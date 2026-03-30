from django.contrib import admin
from django.utils import timezone
from datetime import timedelta
from .models import Subscription


def grant_pro(modeladmin, request, queryset):
    queryset.update(plan='pro_monthly', status='active',
                    current_period_end=timezone.now() + timedelta(days=36500))


grant_pro.short_description = 'Grant Pro (lifetime) to selected users'


def revoke_pro(modeladmin, request, queryset):
    queryset.update(plan='free', status='active', current_period_end=None)


revoke_pro.short_description = 'Revoke Pro → revert to Free'


@admin.register(Subscription)
class SubscriptionAdmin(admin.ModelAdmin):
    list_display = ('user', 'plan', 'status', 'is_active_display',
                    'current_period_end', 'updated_at')
    list_filter = ('plan', 'status')
    search_fields = ('user__username', 'user__email')
    list_editable = ('plan', 'status')
    actions = [grant_pro, revoke_pro]
    readonly_fields = ('created_at', 'updated_at')

    @admin.display(boolean=True, description='Active?')
    def is_active_display(self, obj):
        return obj.is_active
