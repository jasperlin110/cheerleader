from django.db import models
from django.utils import timezone as tz


class User(models.Model):
    name = models.CharField(max_length=100)
    email = models.EmailField(unique=True)
    phone_number = models.CharField(max_length=50, blank=True)
    timezone = models.CharField(max_length=100, blank=True)
    created_at = models.DateTimeField(default=tz.now)
    updated_at = models.DateTimeField(default=tz.now)
