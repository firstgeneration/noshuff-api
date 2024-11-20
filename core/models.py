from django.db import models
from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, PermissionsMixin
import uuid
from spotipy import Spotify


class TimestampModelMixin(models.Model):
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True


class UserManager(BaseUserManager):
    def create_user(self, email, password=None, **extra_fields):
        if not email:
            raise ValueError("The Email field must be set")
        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, password=None, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        return self.create_user(email, password, **extra_fields)

class User(AbstractBaseUser, PermissionsMixin, TimestampModelMixin):
    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = []

    objects = UserManager()

    uuid = models.UUIDField(default=uuid.uuid4, editable=False, unique=True, db_index=True)
    is_active = models.BooleanField(default=True)
    email = models.EmailField(unique=True)

    personal_blurb = models.TextField(blank=True, null=True)

    spotify_access_token = models.CharField(max_length=500, null=True, blank=True)
    spotify_access_token_expires_at = models.DateTimeField(blank=True, null=True)
    spotify_refresh_token = models.CharField(max_length=500, null=True, blank=True)
    
    spotify_id = models.CharField(max_length=100)
    spotify_display_name = models.CharField(max_length=100)
    spotify_avatar_url = models.URLField(max_length=2000, null=True, blank=True)
    spotify_country = models.CharField(max_length=100, null=True, blank=True)
    spotify_follower_count = models.IntegerField(null=True, blank=True)
    spotify_account_href = models.URLField(max_length=2000, null=True, blank=True)
    spotify_account_uri = models.CharField(max_length=200, null=True, blank=True)
    spotify_product = models.CharField(max_length=100, null=True, blank=True)

    def __str__(self):
        return self.email

    def get_spotify_client(self):
        return Spotify(auth=self.spotify_access_token)
