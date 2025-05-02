from django.conf import settings


def bitu(request):
    permission_request_enabled = True if hasattr(settings, 'ACCESS_REQUEST_RULES') and settings.ACCESS_REQUEST_RULES else False
    return {
        'two_factor_auth': settings.ENABLE_2FA,
        'permission_request_enabled': permission_request_enabled}


def permissions(request):
    if not request.user.is_authenticated or \
        not hasattr(settings, 'ACCESS_REQUEST_RULES') or \
        not settings.ACCESS_REQUEST_RULES:
        return {
        'pending_permissions': 0,
        'managed_permissions': False
    }

    count = 0
    if hasattr(settings, 'ACCESS_REQUEST_RULES') and settings.ACCESS_REQUEST_RULES:
        from permissions.permission import permission_set
        count = permission_set.get_pending(request.user).count()

    return {
        'pending_permissions': count,
        'managed_permissions': request.user.permission_manager
    }
