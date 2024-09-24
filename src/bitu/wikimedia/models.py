from django.db import models


class UserBlockEventLog(models.Model):
    created_at = models.DateTimeField(auto_now_add=True)
    created_by = models.CharField(max_length=256)
    username = models.CharField(max_length=256)
    action = models.CharField(max_length=256)
    comment = models.TextField()