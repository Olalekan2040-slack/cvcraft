from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.conf import settings
from .models import Subscription


@login_required
def pricing(request):
    subscription = getattr(request.user, 'subscription', None)
    return render(request, 'billing/pricing.html', {
        'subscription': subscription,
        'stripe_public_key': settings.STRIPE_PUBLIC_KEY,
    })


@login_required
def checkout(request, plan):
    if plan not in ('pro_monthly', 'pro_yearly'):
        return redirect('billing:pricing')

    if not settings.STRIPE_SECRET_KEY:
        messages.info(request, 'Stripe is not configured yet. Coming soon!')
        return redirect('billing:pricing')

    # TODO: Create Stripe checkout session
    messages.info(request, 'Stripe checkout integration coming soon!')
    return redirect('billing:pricing')


@login_required
def manage_subscription(request):
    subscription = getattr(request.user, 'subscription', None)
    return render(request, 'billing/manage.html', {'subscription': subscription})


@login_required
def cancel_subscription(request):
    subscription = getattr(request.user, 'subscription', None)
    if subscription and subscription.is_active:
        # TODO: Cancel via Stripe API
        subscription.status = 'canceled'
        subscription.save()
        messages.success(
            request, 'Subscription canceled. You can continue using Pro until period end.')
    return redirect('billing:manage')
