import json
import uuid
from django.db import models
from django.contrib.auth.models import User
from django.urls import reverse


TEMPLATE_CHOICES = [
    ('classic', 'Classic Professional'),
    ('modern', 'Modern Minimalist'),
    ('executive', 'Executive'),
    ('creative', 'Creative'),
    ('student', 'Student / Entry Level'),
    ('technical', 'Technical / Developer'),
    ('elegant', 'Elegant'),
    ('bold', 'Bold Impact'),
    ('clean', 'Clean ATS'),
    ('timeline', 'Timeline'),
]

DEFAULT_RESUME_DATA = {
    "personal": {
        "full_name": "",
        "job_title": "",
        "email": "",
        "phone": "",
        "location": "",
        "website": "",
        "linkedin": "",
        "summary": ""
    },
    "experience": [],
    "education": [],
    "skills": [],
    "certifications": [],
    "projects": [],
    "languages": [],
    "custom_sections": []
}


class Resume(models.Model):
    user = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name='resumes')
    title = models.CharField(max_length=200, default='My Resume')
    template_slug = models.CharField(
        max_length=50, choices=TEMPLATE_CHOICES, default='modern')
    data = models.JSONField(default=dict)
    custom_css = models.TextField(blank=True)
    is_public = models.BooleanField(default=False)
    public_token = models.UUIDField(
        default=uuid.uuid4, unique=True, editable=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    # Customization
    accent_color = models.CharField(max_length=7, default='#C9A84C')
    font_family = models.CharField(max_length=60, default='Inter')

    class Meta:
        ordering = ['-updated_at']

    def __str__(self):
        return f'{self.title} ({self.user.email})'

    def get_absolute_url(self):
        return reverse('resumes:builder', kwargs={'pk': self.pk})

    def get_public_url(self):
        return reverse('resumes:public_view', kwargs={'token': self.public_token})

    def get_data(self):
        if not self.data:
            return DEFAULT_RESUME_DATA.copy()
        # Merge with defaults to add any missing keys
        merged = DEFAULT_RESUME_DATA.copy()
        merged.update(self.data)
        return merged

    @property
    def personal(self):
        return self.get_data().get('personal', {})

    @property
    def full_name(self):
        return self.personal.get('full_name', self.title)


class ExportLog(models.Model):
    FORMAT_CHOICES = [('pdf', 'PDF'), ('docx', 'DOCX'), ('json', 'JSON')]
    user = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name='exports')
    resume = models.ForeignKey(
        Resume, on_delete=models.CASCADE, related_name='exports')
    format = models.CharField(max_length=10, choices=FORMAT_CHOICES)
    exported_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-exported_at']

    def __str__(self):
        return f'{self.user.email} - {self.format} - {self.exported_at}'
