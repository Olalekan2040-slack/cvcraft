import json
import threading
import logging

from django.contrib.auth.models import User
from django.contrib.auth.decorators import login_required
from django.db.models import Q
from django.http import JsonResponse
from django.shortcuts import render, get_object_or_404
from django.utils import timezone
from django.views.decorators.http import require_POST

from resumes.models import Resume
from .models import (
    JobListing, UserJobInteraction, JobScrapeLog,
    JobPreference, UserJobTarget,
    LOCATION_CHOICES, LOCATION_KEYWORDS,
)
from .services.ats import calculate_ats_score, score_label, score_css_class
from .services.keywords import extract_keywords

logger = logging.getLogger(__name__)

_FALLBACK_KEYWORDS = [
    'software engineer', 'python developer', 'django developer',
    'full stack developer', 'backend developer', 'javascript developer',
    'react developer', 'vue developer', 'nodejs developer',
    'data analyst', 'data scientist', 'machine learning engineer',
    'web developer', 'frontend developer', 'devops engineer',
]


# ── Per-user keyword extraction ───────────────────────────────────────────────

def _user_keywords(user: User) -> list:
    """
    Build a keyword list tailored to this user's CV.
    Combines job title, skills, technologies, and experience positions.
    Falls back to generic keywords if the user has no resume.
    """
    resume = Resume.objects.filter(user=user).first()
    if not resume:
        return _FALLBACK_KEYWORDS
    data = resume.get_data()
    keywords = extract_keywords(data)
    return keywords if keywords else _FALLBACK_KEYWORDS


# ── Background scraper ────────────────────────────────────────────────────────

def _run_scrape_background(log_id: int, user_id: int | None = None) -> None:
    """
    Scrape job boards and link results to the requesting user.

    If user_id is given:  uses only that user's CV keywords, creates
                          UserJobTarget rows so their feed is personalised.
    If user_id is None:   fallback global scrape (used on first deploy).
    """
    from .services.scraper import scrape_all

    log = JobScrapeLog.objects.get(pk=log_id)
    user = None
    try:
        if user_id:
            user = User.objects.get(pk=user_id)
            keywords = _user_keywords(user)
            logger.info(
                "Per-user scrape for %s using %d keywords: %s…",
                user.username, len(keywords), keywords[:5],
            )
        else:
            # Global fallback — combine all resumes
            kw_set: set = set()
            for resume in Resume.objects.all():
                try:
                    kw_set.update(extract_keywords(resume.get_data()))
                except Exception:
                    pass
            keywords = list(kw_set) if kw_set else _FALLBACK_KEYWORDS
            logger.info("Global scrape with %d keywords", len(keywords))

        raw = scrape_all(keywords)
        new_count = 0
        skip_count = 0
        sources_seen: set = set()

        for item in raw:
            url = (item.get('url') or '').strip()
            if not url:
                skip_count += 1
                continue

            sources_seen.add(item['source_name'])
            listing, created = JobListing.objects.get_or_create(
                url=url,
                defaults={
                    'source_name': item['source_name'],
                    'title':       item['title'],
                    'company':     item.get('company', ''),
                    'location':    item.get('location', ''),
                    'description': item.get('description', ''),
                    'keywords_matched': item.get('keywords_matched', []),
                },
            )
            if created:
                new_count += 1
            else:
                skip_count += 1

            # Link this job to the user who requested the scrape
            if user:
                UserJobTarget.objects.get_or_create(
                    user=user,
                    job=listing,
                    defaults={'matched_keywords': item.get('keywords_matched', [])},
                )

        log.ended_at = timezone.now()
        log.listings_new = new_count
        log.listings_skipped = skip_count
        log.sources_run = len(sources_seen)
        log.status = 'done'
        log.save()
        logger.info(
            "Scrape done [%s]: %d new, %d skipped, %d sources",
            user.username if user else 'global', new_count, skip_count, len(sources_seen),
        )
    except Exception as exc:
        logger.exception("Background scrape failed")
        log.status = 'error'
        log.errors = [str(exc)]
        log.ended_at = timezone.now()
        log.save()


def start_scrape_thread(user: User | None = None) -> 'JobScrapeLog | None':
    """
    Create a JobScrapeLog and start the background scrape thread.
    If a scrape is already running for this user, returns None.
    """
    qs = JobScrapeLog.objects.filter(status='running')
    if user:
        qs = qs.filter(user=user)
    else:
        qs = qs.filter(user__isnull=True)

    if qs.exists():
        return None

    log = JobScrapeLog.objects.create(status='running', user=user)
    t = threading.Thread(
        target=_run_scrape_background,
        args=(log.pk,),
        kwargs={'user_id': user.pk if user else None},
        daemon=True,
    )
    t.start()
    return log


# ── Helpers ───────────────────────────────────────────────────────────────────

def _primary_resume_data(user: User) -> dict:
    resume = Resume.objects.filter(user=user).first()
    return resume.get_data() if resume else {}


def _location_matches(job_location: str, preferred: list) -> bool:
    if not preferred or 'worldwide' in preferred:
        return True
    loc_lower = ' ' + (job_location or '').lower() + ' '
    universal = ['remote', 'worldwide', 'anywhere', 'global', 'international']
    if any(u in loc_lower for u in universal):
        return True
    if not job_location or not job_location.strip():
        return True
    for code in preferred:
        if any(k in loc_lower for k in LOCATION_KEYWORDS.get(code, [])):
            return True
    return False


# ── Views ─────────────────────────────────────────────────────────────────────

@login_required
def feed(request):
    resume_data = _primary_resume_data(request.user)
    keywords = extract_keywords(resume_data)
    has_resume = bool(resume_data.get('personal', {}).get('full_name'))
    tab = request.GET.get('tab', 'all')
    q   = request.GET.get('q', '').strip()

    pref, _ = JobPreference.objects.get_or_create(user=request.user)
    preferred_locations = pref.preferred_locations or []

    dismissed_ids = set(
        UserJobInteraction.objects.filter(
            user=request.user, status=UserJobInteraction.STATUS_DISMISSED,
        ).values_list('job_id', flat=True)
    )
    saved_map = {
        i.job_id: i
        for i in UserJobInteraction.objects.filter(
            user=request.user, status=UserJobInteraction.STATUS_SAVED,
        )
    }

    # ── Only show jobs scraped FOR this user ──────────────────────────────────
    if tab == 'saved':
        qs = JobListing.objects.filter(id__in=saved_map.keys(), is_active=True)
    else:
        qs = (
            JobListing.objects
            .filter(user_targets__user=request.user, is_active=True)
            .exclude(id__in=dismissed_ids)
            .distinct()
        )

    if q:
        qs = qs.filter(
            Q(title__icontains=q) | Q(company__icontains=q) |
            Q(location__icontains=q) | Q(description__icontains=q)
        )

    jobs = list(qs.order_by('-scraped_at')[:500])

    # Location filter
    if preferred_locations and 'worldwide' not in preferred_locations:
        jobs = [j for j in jobs if _location_matches(j.location, preferred_locations)]

    jobs = jobs[:200]

    # ── Auto-trigger a per-user scrape if this user has no jobs yet ───────────
    user_job_count = UserJobTarget.objects.filter(user=request.user).count()
    user_scrape_running = JobScrapeLog.objects.filter(
        status='running', user=request.user,
    ).exists()

    if has_resume and user_job_count == 0 and not user_scrape_running and tab != 'saved':
        log = start_scrape_thread(user=request.user)
        if log:
            user_scrape_running = True

    cards = []
    for job in jobs:
        score, breakdown = calculate_ats_score(job.title, job.description, resume_data)
        cards.append({
            'job':        job,
            'score':      score,
            'label':      score_label(score),
            'css':        score_css_class(score),
            'breakdown':  breakdown,
            'snippet':    job.description_snippet(),
            'is_saved':   job.id in saved_map,
            'stack_fit':  breakdown.get('stack', {}).get('fit', 'unknown'),
            'job_langs':  breakdown.get('stack', {}).get('job_langs', []),
        })

    cards.sort(key=lambda c: c['score'], reverse=True)

    last_scrape = (
        JobScrapeLog.objects
        .filter(status='done', user=request.user)
        .order_by('-ended_at')
        .first()
    )

    return render(request, 'jobs/feed.html', {
        'cards':               cards,
        'tab':                 tab,
        'q':                   q,
        'keywords':            keywords[:12],
        'has_resume':          has_resume,
        'total_jobs':          user_job_count,
        'saved_count':         len(saved_map),
        'last_scrape':         last_scrape,
        'preferred_locations': preferred_locations,
        'location_choices':    LOCATION_CHOICES,
        'scrape_running':      user_scrape_running,
    })


@login_required
@require_POST
def toggle_save(request, job_id):
    job = get_object_or_404(JobListing, pk=job_id, is_active=True)
    inter = UserJobInteraction.objects.filter(user=request.user, job=job).first()

    if inter and inter.status == UserJobInteraction.STATUS_SAVED:
        inter.delete()
        return JsonResponse({'saved': False})

    if inter:
        inter.status = UserJobInteraction.STATUS_SAVED
        inter.save(update_fields=['status'])
    else:
        resume_data = _primary_resume_data(request.user)
        score, _ = calculate_ats_score(job.title, job.description, resume_data)
        UserJobInteraction.objects.create(
            user=request.user, job=job,
            status=UserJobInteraction.STATUS_SAVED,
            ats_score=score,
        )
    return JsonResponse({'saved': True})


@login_required
@require_POST
def dismiss_job(request, job_id):
    job = get_object_or_404(JobListing, pk=job_id)
    UserJobInteraction.objects.update_or_create(
        user=request.user, job=job,
        defaults={'status': UserJobInteraction.STATUS_DISMISSED},
    )
    return JsonResponse({'dismissed': True})


@login_required
@require_POST
def save_preferences(request):
    try:
        body = json.loads(request.body)
        locations = body.get('preferred_locations', [])
        valid_codes = {code for code, _ in LOCATION_CHOICES}
        locations = [loc for loc in locations if loc in valid_codes]
        pref, _ = JobPreference.objects.get_or_create(user=request.user)
        pref.preferred_locations = locations
        pref.save()
        return JsonResponse({'ok': True, 'saved': locations})
    except Exception as exc:
        return JsonResponse({'ok': False, 'error': str(exc)}, status=400)


@login_required
@require_POST
def trigger_scrape(request):
    """Kick off a per-user background scrape."""
    if JobScrapeLog.objects.filter(status='running', user=request.user).exists():
        return JsonResponse({'status': 'already_running'})
    log = start_scrape_thread(user=request.user)
    if log:
        return JsonResponse({'status': 'started'})
    return JsonResponse({'status': 'already_running'})


@login_required
def scrape_status(request):
    """Poll endpoint — returns this user's scrape progress and job count."""
    running   = JobScrapeLog.objects.filter(status='running', user=request.user).exists()
    total     = UserJobTarget.objects.filter(user=request.user).count()
    last      = (
        JobScrapeLog.objects
        .filter(status='done', user=request.user)
        .order_by('-ended_at')
        .first()
    )
    return JsonResponse({
        'running':    running,
        'total_jobs': total,
        'last_scrape': last.ended_at.isoformat() if last and last.ended_at else None,
    })
