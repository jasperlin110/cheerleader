from django.db import models
from django.utils import timezone


class ChatSession(models.Model):
    session_key = models.CharField(max_length=40, unique=True)
    user = models.ForeignKey("users.User", null=True, blank=True, on_delete=models.SET_NULL)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    messages = models.JSONField(default=list)
    meeting_scheduled = models.BooleanField(default=False)
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(default=timezone.now)
