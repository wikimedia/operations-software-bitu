# SPDX-License-Identifier: GPL-3.0-or-later

import uuid

import structlog

from django.conf import settings
from django.contrib.auth import get_user_model
from django.db import models
from django.utils.translation import gettext_lazy as _
from django.utils.module_loading import import_string


audit = structlog.getLogger('audit')
User = get_user_model()


class PermissionValidationError(Exception):
    pass


class Permission(object):
    def __init__(self, **kwargs) -> None:
        attributes = ['key', 'name', 'source', 'source_display', 'owner', 'description', 'state', 'user']
        self.__dict__.update(
            (k, v) for k, v in kwargs.items() if k in attributes
        )

    @property
    def configured(self) -> bool:
        """Check if configuration for this permissions is available in
        the settings file.

        Returns:
            bool: Configured, True/False
        """
        if not hasattr(settings, 'ACCESS_REQUEST_RULES'):
            return False

        if self.source not in settings.ACCESS_REQUEST_RULES:
            return False

        if self.key not in settings.ACCESS_REQUEST_RULES[self.source]:
            return False

        return True

    def run_validators(self, user) -> bool:
        if not self.configured:
            return False
        rules = [
            rule for rule in settings.ACCESS_REQUEST_RULES[
                self.source][self.key] if rule.get('prevalidate', False)]

        request = PermissionRequest()
        request.user = user
        for rule in rules:
            m = import_string(rule['module'])
            approved, processed = m(request, **rule)
            if not approved:
                return False
        return True

    def __eq__(self, other):
        if self.source == other.source and self.key == other.key:
            return True
        return False

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
        return _('Unknown')

    @property
    def request(self):
        return PermissionRequest.objects.filter(user=self.user,
                                                system=self.source,
                                                key=self.key).order_by('-created').first()


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
        (SYNCRONIZED, _('Enabled')),
        (REJECTED, _('Rejected')),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    created = models.DateTimeField(auto_now_add=True)
    updated = models.DateTimeField(auto_now=True)
    key = models.CharField(max_length=150)
    system = models.CharField(max_length=150)
    user = models.ForeignKey(User, on_delete=models.PROTECT, related_name="permission_requests")
    status = models.CharField(max_length=2, choices=REQUEST_STATUS, default=PENDING)
    comment = models.TextField(blank=False, help_text=_('Please provide a reasoning for this access request'))
    ticket = models.CharField(max_length=256,
                              blank=True,
                              default='',
                              help_text=_(
                                  'Phabricator task with access request, alternatively provide reasoning below'))

    @property
    def permission(self):
        from .permission import permission_set
        return permission_set.get_permission(self.system, self.key)

    @property
    def rules(self):
        return getattr(settings, 'ACCESS_REQUEST_RULES', {}).get(self.system, {}).get(self.key, [])

    def validate(self):
        process_count = 0
        for rule in self.rules:
            validator = import_string(rule['module'])
            approved, processed = validator(self, **rule)
            if not processed:
                continue

            process_count += 1

            if not approved:
                # All validation checks must parse
                self.status = self.REJECTED
                self.save()
                return False
            audit.info('validation',
                       id=self.id, user=self.user.get_username(),
                       status=self.get_status_display, rule=rule['module'], validation='success')

        # At this point all validator checks have parsed, or zero was given.
        # Do not approve requests validated by zero rules.
        result = True if len(self.rules) > 0 and len(self.rules) == process_count else False
        if result:
            self.status = self.APPROVED
            self.save()
            audit.info('request',
                       id=self.id, user=self.user.get_username(),
                       status=self.get_status_display(), success=result)

            if self.permission:
                self.grant()

    def grant(self):
        if self.status != self.APPROVED:
            return

        from .permission import permission_set
        backend = permission_set._backends[self.system]
        backend.grant(self.user, self.permission)

    def list_approvals(self):
        return self.log_set.filter(approved=True).order_by("-created")

    def __str__(self):
        return f"({self.id}) - {self.get_status_display() } - {self.system}|{self.key}; requested on: {self.created} by {self.user.get_username()}"



class Log(models.Model):
    created = models.DateTimeField(auto_now_add=True)
    approved = models.BooleanField(default=False)
    created_by = models.ForeignKey(User, on_delete=models.PROTECT)
    request = models.ForeignKey(PermissionRequest, on_delete=models.CASCADE)
    comment = models.TextField()
