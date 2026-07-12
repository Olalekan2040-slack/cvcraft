from django.shortcuts import render, redirect
from django.http import JsonResponse
from resumes.models import TEMPLATE_CHOICES


def landing(request):
    return render(request, 'core/landing.html', {'templates': TEMPLATE_CHOICES})


def pricing(request):
    return render(request, 'core/pricing.html')


def about(request):
    return render(request, 'core/about.html')


def ping(request):
    return JsonResponse({'ok': True})
