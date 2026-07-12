from django.db import models
from django.contrib.auth.models import User


LOCATION_CHOICES = [
    ('worldwide', 'Worldwide / Remote'),
    ('usa',       'United States'),
    ('uk',        'United Kingdom'),
    ('canada',    'Canada'),
    ('australia', 'Australia'),
    ('germany',   'Germany'),
    ('netherlands','Netherlands'),
    ('france',    'France'),
    ('spain',     'Spain'),
    ('nigeria',   'Nigeria'),
    ('india',     'India'),
    ('south_africa','South Africa'),
    ('ghana',     'Ghana'),
    ('kenya',     'Kenya'),
    ('brazil',    'Brazil'),
    ('singapore', 'Singapore'),
    ('uae',       'UAE / Dubai'),
    ('europe',    'Europe'),
]

# Keywords that appear in job location strings for each country code
LOCATION_KEYWORDS: dict[str, list[str]] = {
    'worldwide':   ['worldwide', 'anywhere', 'global', 'international'],
    'usa':         ['usa', ' us ', 'united states', 'america', 'u.s.', 'new york', 'san francisco', 'seattle', 'austin'],
    'uk':          ['uk', 'united kingdom', 'britain', 'england', 'london', 'u.k.'],
    'canada':      ['canada', 'toronto', 'vancouver', 'montreal', 'calgary'],
    'australia':   ['australia', 'sydney', 'melbourne', 'brisbane'],
    'germany':     ['germany', 'berlin', 'munich', 'hamburg', 'deutschland'],
    'netherlands': ['netherlands', 'amsterdam', 'holland'],
    'france':      ['france', 'paris'],
    'spain':       ['spain', 'madrid', 'barcelona'],
    'nigeria':     ['nigeria', 'lagos', 'abuja'],
    'india':       ['india', 'bangalore', 'bengaluru', 'mumbai', 'delhi', 'hyderabad'],
    'south_africa':['south africa', 'johannesburg', 'cape town', 'durban'],
    'ghana':       ['ghana', 'accra'],
    'kenya':       ['kenya', 'nairobi'],
    'brazil':      ['brazil', 'brasil', 'são paulo', 'rio de janeiro'],
    'singapore':   ['singapore'],
    'uae':         ['uae', 'dubai', 'abu dhabi', 'emirates'],
    'europe':      ['europe', 'european', ' eu ', 'emea'],
}


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


class JobPreference(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='job_preference')
    preferred_locations = models.JSONField(default=list)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        locs = ', '.join(self.preferred_locations) or 'worldwide'
        return f"{self.user.username} prefers: {locs}"


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
