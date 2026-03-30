from django.shortcuts import render


def landing(request):
    if request.user.is_authenticated:
        from django.shortcuts import redirect
        return redirect('resumes:dashboard')
    return render(request, 'core/landing.html')


def pricing(request):
    return render(request, 'core/pricing.html')


def about(request):
    return render(request, 'core/about.html')
