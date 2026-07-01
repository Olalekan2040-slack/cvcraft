from django.shortcuts import render, redirect
from resumes.models import TEMPLATE_CHOICES


def landing(request):
    if request.user.is_authenticated:
        return redirect('resumes:dashboard')
    return render(request, 'core/landing.html', {'templates': TEMPLATE_CHOICES})


def pricing(request):
    return render(request, 'core/pricing.html')


def about(request):
    return render(request, 'core/about.html')
