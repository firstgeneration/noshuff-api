from django.contrib.auth.models import AbstractUser
from django.db import models
from django_extensions.db.models import TimeStampedModel
import uuid


class User(TimeStampedModel, AbstractUser):
    uuid = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)
    spotify_email = models.EmailField(unique=True, null=True, blank=True)
    spotify_id = models.CharField(max_length=255, unique=True)
    spotify_display_name = models.CharField(max_length=255)
    spotify_avatar_url = models.URLField(max_length=2000, null=True, blank=True)
    spotify_access_token = models.CharField(max_length=255, null=True, blank=True)
    spotify_refresh_token = models.CharField(max_length=255, null=True, blank=True)
    spotify_scope = models.CharField(max_length=255, null=True, blank=True)
