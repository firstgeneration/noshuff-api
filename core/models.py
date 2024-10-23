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
    spotify_avatar_url = models.URLField(max_length=2000, null=True, blank=True)
    spotify_access_token = models.CharField(max_length=500, null=True, blank=True)
    spotify_access_token_expires_at = models.DateTimeField(blank=True, null=True)
    spotify_refresh_token = models.CharField(max_length=500, null=True, blank=True)
    spotify_country = models.CharField(max_length=100, null=True, blank=True)
    spotify_follower_count = models.IntegerField(null=True, blank=True)
    spotify_account_href = models.URLField(max_length=2000, null=True, blank=True)
    spotify_account_uri = models.CharField(max_length=200, null=True, blank=True)
    spotify_product = models.CharField(max_length=100, null=True, blank=True)
