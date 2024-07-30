import uuid

from django.contrib.auth import get_user_model
from django.db import models
from django.utils.translation import gettext_lazy as _


User = get_user_model()


class Permission(object):
    def __init__(self, **kwargs) -> None:
        attributes = ['key', 'name', 'source', 'source_display', 'owner', 'description', 'state', 'user']
        self.__dict__.update(
            (k, v) for k, v in kwargs.items() if k in attributes
        )

    @property
    def description_display(self):
        if self.description:
            return self.description
        elif self.name:
            return self.name.__str__().capitalize()
        return self.key

    @property
    def state_display(self):
        for status in PermissionRequest.REQUEST_STATUS:
            if status[0] == self.state:
                return status[1]
        return _('Uknown')

    @property
    def request(self):
        return PermissionRequest.objects.filter(user=self.user, system=self.source, key=self.key).first()


class PermissionRequest(models.Model):
    APPROVED = 'AP'
    CANCELLED = 'CN'
    PENDING = 'PN'
    SYNCRONIZED = 'SY'
    REJECTED = 'RJ'
    REQUEST_STATUS = [
        (APPROVED, _('Approved')),
        (CANCELLED, _('Cancelled')),
        (PENDING, _('Pending')),
        (SYNCRONIZED, _('Existing Permission')),
        (REJECTED, _('Rejected')),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    created = models.DateTimeField(auto_now_add=True)
    updated = models.DateTimeField(auto_now=True)
    key = models.CharField(max_length=150)
    system = models.CharField(max_length=150)
    user = models.ForeignKey(User, on_delete=models.PROTECT, related_name="permission_requests")
    status = models.CharField(max_length=2, choices=REQUEST_STATUS, default=PENDING)
    comment = models.TextField(help_text=_('Please provide a reasoning for this request'))
    ticket = models.CharField(max_length=256, blank=True, default='', help_text=_('Phabricator ticket, if available.'))

    @property
    def permission(self):
        from .permission import permission_set
        return permission_set.get_permission(self.system, self.key)


class Log(models.Model):
    created = models.DateTimeField(auto_now_add=True)
    approved = models.BooleanField(default=False)
    created_by = models.ForeignKey(User, on_delete=models.PROTECT)
    request = models.ForeignKey(PermissionRequest, on_delete=models.CASCADE)
    comment = models.TextField()
