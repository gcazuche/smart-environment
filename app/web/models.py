"""Only local operational metadata. Business records remain in Supabase with RLS."""

from django.db import models


class LoginAttempt(models.Model):
    key = models.CharField(max_length=64, primary_key=True)
    attempts = models.PositiveIntegerField(default=0)
    expires_at = models.FloatField()
