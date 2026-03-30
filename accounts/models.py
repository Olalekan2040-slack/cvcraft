from django.db import models
from django.contrib.auth.models import User


class Profile(models.Model):
    user = models.OneToOneField(
        User, on_delete=models.CASCADE, related_name='profile')
    avatar = models.ImageField(upload_to='avatars/', null=True, blank=True)
    job_title = models.CharField(max_length=120, blank=True)
    bio = models.TextField(blank=True)
    linkedin_url = models.URLField(blank=True)
    website = models.URLField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f'{self.user.email} profile'

    def get_avatar_url(self):
        if self.avatar:
            return self.avatar.url
        return None
