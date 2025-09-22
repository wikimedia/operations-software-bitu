from django.db import models


class UserBlockEventLog(models.Model):
    created_at = models.DateTimeField(auto_now_add=True)
    created_by = models.CharField(max_length=256)
    username = models.CharField(max_length=256)
    action = models.CharField(max_length=256)
    comment = models.TextField()
    unset_email = models.BooleanField(default=False)
    parent = models.ForeignKey('self', null=True, blank=True, on_delete=models.CASCADE)

    def get_display_action(self):
        if self.action == "block_user":
            return "Blocked"
        elif self.action == "unblock_user":
            return "Unblocked"
        else:
            return self.action

    def __str__(self):
        return f'({self.pk}) [ {self.created_by} ] {self.action} - {self.comment}'