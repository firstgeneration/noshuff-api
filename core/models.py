from django.db import models
from django.contrib.auth.models import AbstractUser


class TimestampModelMixin(models.Model):
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True


class User(AbstractUser, TimestampModelMixin):
    email = models.EmailField(unique=True)
    spotify_id = models.CharField(max_length=100)
    spotify_display_name = models.CharField(max_length=100)
    avatar_url = models.URLField(null=True, blank=True)
    spotify_access_token = models.CharField(max_length=100, null=True, blank=True)
    spotify_refresh_token = models.CharField(max_length=100, null=True, blank=True)
