import threading
import logging

from django.shortcuts import render, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from django.db.models import Q
from django.utils import timezone

import json

from resumes.models import Resume
from .models import JobListing, UserJobInteraction, JobScrapeLog, JobPreference, LOCATION_CHOICES, LOCATION_KEYWORDS
from .services.ats import calculate_ats_score, score_label, score_css_class
from .services.keywords import extract_keywords

logger = logging.getLogger(__name__)

_FALLBACK_KEYWORDS = [
    'software engineer', 'python developer', 'django developer',
    'full stack developer', 'backend developer', 'javascript developer',
    'react developer', 'vue developer', 'nodejs developer',
    'data analyst', 'data scientist', 'machine learning engineer',
    'web developer', 'frontend developer', 'devops engineer',
    'product manager', 'ux designer', 'ui designer',
]


def _run_scrape_background(log_id):
    """Run scrape_all in a background thread and update the log when done."""
    from .services.scraper import scrape_all

    log = JobScrapeLog.objects.get(pk=log_id)
    try:
        kw_set = set()
        for resume in Resume.objects.all():
            try:
                kw_set.update(extract_keywords(resume.get_data()))
            except Exception:
                pass
        keywords = list(kw_set) if kw_set else _FALLBACK_KEYWORDS

        raw = scrape_all(keywords)
        new_count = 0
        skip_count = 0
        sources_seen = set()

        for item in raw:
            url = (item.get('url') or '').strip()
            if not url:
                skip_count += 1
                continue
            sources_seen.add(item['source_name'])
            _, created = JobListing.objects.get_or_create(
                url=url,
                defaults={
                    'source_name': item['source_name'],
                    'title': item['title'],
                    'company': item.get('company', ''),
                    'location': item.get('location', ''),
                    'description': item.get('description', ''),
                    'keywords_matched': item.get('keywords_matched', []),
                },
            )
            if created:
                new_count += 1
            else:
                skip_count += 1

        log.ended_at = timezone.now()
        log.listings_new = new_count
        log.listings_skipped = skip_count
        log.sources_run = len(sources_seen)
        log.status = 'done'
        log.save()
        logger.info("Background scrape done: %d new, %d skipped", new_count, skip_count)
    except Exception as exc:
        logger.exception("Background scrape failed")
        log.status = 'error'
        log.errors = [str(exc)]
        log.ended_at = timezone.now()
        log.save()


def start_scrape_thread():
    """Create a running log entry and kick off _run_scrape_background."""
    if JobScrapeLog.objects.filter(status='running').exists():
        return None
    log = JobScrapeLog.objects.create(status='running')
    t = threading.Thread(target=_run_scrape_background, args=(log.pk,), daemon=True)
    t.start()
    return log


def _primary_resume_data(user):
    resume = Resume.objects.filter(user=user).first()
    return resume.get_data() if resume else {}


def _location_matches(job_location: str, preferred: list) -> bool:
    """
    Return True if the job should be shown given the user's location preferences.
    Jobs tagged Remote/Worldwide always pass. Empty preference = show all.
    """
    if not preferred or 'worldwide' in preferred:
        return True

    loc_lower = (' ' + (job_location or '').lower() + ' ')

    # Always show remote/worldwide jobs regardless of filter
    universal = ['remote', 'worldwide', 'anywhere', 'global', 'international']
    if any(u in loc_lower for u in universal):
        return True
    # Empty location → assume worldwide
    if not job_location or not job_location.strip():
        return True

    # Check preferred countries
    for code in preferred:
        keywords = LOCATION_KEYWORDS.get(code, [])
        if any(k in loc_lower for k in keywords):
            return True
    return False


@login_required
def feed(request):
    resume_data = _primary_resume_data(request.user)
    keywords = extract_keywords(resume_data)
    tab = request.GET.get('tab', 'all')
    q = request.GET.get('q', '').strip()

    # Load or create user location preferences
    pref, _ = JobPreference.objects.get_or_create(user=request.user)
    preferred_locations = pref.preferred_locations or []

    dismissed_ids = set(
        UserJobInteraction.objects.filter(
            user=request.user, status=UserJobInteraction.STATUS_DISMISSED
        ).values_list('job_id', flat=True)
    )
    saved_map = {
        i.job_id: i
        for i in UserJobInteraction.objects.filter(
            user=request.user, status=UserJobInteraction.STATUS_SAVED
        )
    }

    if tab == 'saved':
        qs = JobListing.objects.filter(id__in=saved_map.keys(), is_active=True)
    else:
        qs = JobListing.objects.filter(is_active=True).exclude(id__in=dismissed_ids)

    if q:
        qs = qs.filter(
            Q(title__icontains=q) | Q(company__icontains=q) |
            Q(location__icontains=q) | Q(description__icontains=q)
        )

    jobs = list(qs.order_by('-scraped_at')[:500])

    # Apply location filter
    if preferred_locations and 'worldwide' not in preferred_locations:
        jobs = [j for j in jobs if _location_matches(j.location, preferred_locations)]

    # Cap after location filter
    jobs = jobs[:200]

    cards = []
    for job in jobs:
        score, breakdown = calculate_ats_score(
            job.title, job.description, resume_data
        )
        cards.append({
            'job': job,
            'score': score,
            'label': score_label(score),
            'css': score_css_class(score),
            'breakdown': breakdown,
            'snippet': job.description_snippet(),
            'is_saved': job.id in saved_map,
            'stack_fit': breakdown.get('stack', {}).get('fit', 'unknown'),
            'job_langs': breakdown.get('stack', {}).get('job_langs', []),
        })

    cards.sort(key=lambda c: c['score'], reverse=True)

    last_scrape = JobScrapeLog.objects.filter(status='done').order_by('-ended_at').first()
    total_jobs = JobListing.objects.filter(is_active=True).count()

    return render(request, 'jobs/feed.html', {
        'cards': cards,
        'tab': tab,
        'q': q,
        'keywords': keywords[:12],
        'has_resume': bool(resume_data.get('personal', {}).get('full_name')),
        'total_jobs': total_jobs,
        'saved_count': len(saved_map),
        'last_scrape': last_scrape,
        'preferred_locations': preferred_locations,
        'location_choices': LOCATION_CHOICES,
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
            user=request.user,
            job=job,
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
    """Save user's preferred job locations."""
    try:
        body = json.loads(request.body)
        locations = body.get('preferred_locations', [])
        # Validate: only allow known codes
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
    """Kick off a background scrape if none is already running."""
    if JobScrapeLog.objects.filter(status='running').exists():
        return JsonResponse({'status': 'already_running'})
    log = start_scrape_thread()
    if log:
        return JsonResponse({'status': 'started'})
    return JsonResponse({'status': 'already_running'})


@login_required
def scrape_status(request):
    """Poll endpoint: returns current scrape progress and job count."""
    running = JobScrapeLog.objects.filter(status='running').exists()
    total = JobListing.objects.filter(is_active=True).count()
    last = JobScrapeLog.objects.filter(status='done').order_by('-ended_at').first()
    return JsonResponse({
        'running': running,
        'total_jobs': total,
        'last_scrape': last.ended_at.isoformat() if last and last.ended_at else None,
    })
