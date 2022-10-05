from django.contrib.auth.models import AbstractUser
from django.db import models
from django_extensions.db.models import TimeStampedModel


class User(TimeStampedModel, AbstractUser):
    email = models.EmailField(unique=True)
    spotify_id = models.CharField(max_length=100)
    spotify_display_name = models.CharField(max_length=100)
    spotify_avatar_url = models.URLField(null=True)
    spotify_access_token = models.CharField(max_length=100, null=True, blank=True)
    spotify_refresh_token = models.CharField(max_length=100, null=True, blank=True)
