from django.contrib import admin
from .models import Resume, ExportLog


@admin.register(Resume)
class ResumeAdmin(admin.ModelAdmin):
    list_display = ['title', 'user',
                    'template_slug', 'is_public', 'updated_at']
    list_filter = ['template_slug', 'is_public']
    search_fields = ['title', 'user__email']
    readonly_fields = ['public_token', 'created_at', 'updated_at']


@admin.register(ExportLog)
class ExportLogAdmin(admin.ModelAdmin):
    list_display = ['user', 'resume', 'format', 'exported_at']
    list_filter = ['format']
