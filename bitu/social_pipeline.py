# SPDX-License-Identifier: GPL-3.0-or-later
# Pipeline for Python Social Auth.
# Allow social_auth to extra the CAS LDAP groups, and
# create the missing Django groups and add the user to
# these group.
#
# Note that we're not reusing the groups feature from
# the standard social_auth pipelines, as this doesn't
# understand the CAS handling of LDAP groups, nor
# does it know how to deal with an LDAP dn.
import logging

from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group

logger = logging.getLogger('social')

def add_user_to_groups(strategy, details, backend, user=None, *args, **kwargs):
    logger.debug(f'strategy: {strategy}, details: {details}, backend: {backend}, user: {user}, args: {args}, kwargs: {kwargs}')
    if not user:
        return

    # Convert the user object to a real Django User object.
    User = get_user_model()
    user = User.objects.get(username=user.username)
    groups = kwargs.get('response', {}).get('groups', [])

    for group in groups:
        # Get the CN of the group to use as name.
        group_name = group.split(',')[0]
        if group_name.startswith('cn='):
            group_name = group_name[3:]

        g, created = Group.objects.get_or_create(name=group_name)
        if created:
            logger.info(f'backend: {backend}, group created: {group_name}')

        logger.info(f'backend: {backend}, user:{user.normalize_username}')
        user.groups.add(g)
