from django.db import models
from safedelete.models import SafeDeleteModel

class User(SafeDeleteModel):
    id = models.CharField(max_length=100, primary_key=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    display_name = models.CharField(max_length=100)
    email = models.EmailField()
    avatar_url = models.URLField()
