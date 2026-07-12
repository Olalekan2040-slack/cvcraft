from django.shortcuts import render, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from django.db.models import Q

from resumes.models import Resume
from .models import JobListing, UserJobInteraction, JobScrapeLog
from .services.ats import calculate_ats_score, score_label, score_css_class
from .services.keywords import extract_keywords


def _primary_resume_data(user):
    resume = Resume.objects.filter(user=user).first()
    return resume.get_data() if resume else {}


@login_required
def feed(request):
    resume_data = _primary_resume_data(request.user)
    keywords = extract_keywords(resume_data)
    tab = request.GET.get('tab', 'all')
    q = request.GET.get('q', '').strip()

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

    jobs = list(qs.order_by('-scraped_at')[:200])

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
        })

    cards.sort(key=lambda c: c['score'], reverse=True)

    last_scrape = JobScrapeLog.objects.filter(status='done').first()
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
