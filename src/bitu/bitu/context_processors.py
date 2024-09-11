from django.conf import settings


def bitu(request):
    permission_request_enabled = True if hasattr(settings, 'ACCESS_REQUEST_RULES') and settings.ACCESS_REQUEST_RULES else False
    return {
        'two_factor_auth': settings.ENABLE_2FA,
        'permission_request_enabled': permission_request_enabled}
