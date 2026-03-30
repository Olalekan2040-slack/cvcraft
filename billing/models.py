from django.db import models
from django.contrib.auth.models import User
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.utils import timezone


class Subscription(models.Model):
    PLAN_CHOICES = [
        ('free', 'Free'),
        ('pro_monthly', 'Pro Monthly'),
        ('pro_yearly', 'Pro Yearly'),
    ]
    STATUS_CHOICES = [
        ('active', 'Active'),
        ('canceled', 'Canceled'),
        ('past_due', 'Past Due'),
        ('trialing', 'Trialing'),
    ]

    user = models.OneToOneField(
        User, on_delete=models.CASCADE, related_name='subscription')
    plan = models.CharField(
        max_length=20, choices=PLAN_CHOICES, default='free')
    status = models.CharField(
        max_length=20, choices=STATUS_CHOICES, default='active')
    stripe_customer_id = models.CharField(max_length=100, blank=True)
    stripe_subscription_id = models.CharField(max_length=100, blank=True)
    current_period_end = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f'{self.user.email} - {self.plan} ({self.status})'

    @property
    def is_active(self):
        return self.plan != 'free' and self.status in ('active', 'trialing')

    @property
    def is_pro(self):
        return self.is_active


@receiver(post_save, sender=User)
def create_subscription(sender, instance, created, **kwargs):
    if created:
        Subscription.objects.get_or_create(user=instance)
