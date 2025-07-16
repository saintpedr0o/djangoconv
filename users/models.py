from django.db import models
from django.contrib.auth.models import User
from .api.utils import generate_api_key


class UserAPIKey(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name="api_key")
    key = models.CharField(max_length=48, unique=True, editable=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def regenerate_key(self):
        self.key = generate_api_key()
        self.save()
