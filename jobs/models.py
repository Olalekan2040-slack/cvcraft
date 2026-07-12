from django.db import models
from django.contrib.auth.models import User


class JobListing(models.Model):
    source_name = models.CharField(max_length=100)
    title = models.CharField(max_length=500)
    company = models.CharField(max_length=300, blank=True)
    location = models.CharField(max_length=300, blank=True)
    url = models.URLField(max_length=2000, unique=True)
    description = models.TextField(blank=True)
    keywords_matched = models.JSONField(default=list)
    scraped_at = models.DateTimeField(auto_now_add=True)
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ['-scraped_at']
        indexes = [
            models.Index(fields=['scraped_at']),
            models.Index(fields=['is_active', 'scraped_at']),
        ]

    def __str__(self):
        return f"{self.title} @ {self.company}"

    def description_snippet(self, length=220):
        import re
        clean = re.sub(r'<[^>]+>', ' ', self.description)
        clean = re.sub(r'\s+', ' ', clean).strip()
        return clean[:length] + ('…' if len(clean) > length else '')


class UserJobInteraction(models.Model):
    STATUS_SAVED = 'saved'
    STATUS_DISMISSED = 'dismissed'
    STATUS_CHOICES = [
        (STATUS_SAVED, 'Saved'),
        (STATUS_DISMISSED, 'Dismissed'),
    ]
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='job_interactions')
    job = models.ForeignKey(JobListing, on_delete=models.CASCADE, related_name='interactions')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES)
    ats_score = models.SmallIntegerField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('user', 'job')

    def __str__(self):
        return f"{self.user.username} — {self.job.title} [{self.status}]"


class JobScrapeLog(models.Model):
    started_at = models.DateTimeField(auto_now_add=True)
    ended_at = models.DateTimeField(null=True, blank=True)
    sources_run = models.IntegerField(default=0)
    listings_new = models.IntegerField(default=0)
    listings_skipped = models.IntegerField(default=0)
    errors = models.JSONField(default=list)
    status = models.CharField(max_length=20, default='running')

    class Meta:
        ordering = ['-started_at']

    def __str__(self):
        return f"Scrape {self.started_at:%Y-%m-%d %H:%M} — {self.status}"
