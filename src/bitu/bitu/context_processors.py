from django.conf import settings


def bitu(request):
    return {'two_factor_auth': settings.ENABLE_2FA}
