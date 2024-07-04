import json
import urllib

import mwclient

from django.conf import settings


def validate(username, totp):
    parts = urllib.parse.urlparse(settings.MEDIAWIKI['host'])

    site = mwclient.Site(
        parts.netloc,
        consumer_token=settings.MEDIAWIKI['consumer_token'],
        consumer_secret=settings.MEDIAWIKI['consumer_secret'],
        access_token=settings.MEDIAWIKI['access_token'],
        access_secret=settings.MEDIAWIKI['access_secret'],
        clients_useragent=settings.MEDIAWIKI['user_agent'],
        scheme=parts.scheme,
        force_login=True,
    )

    token = site.get_token("csrf", force=True)
    result = site.api(
        "oathvalidate",
        formatversion=2,
        user=username,
        data=json.dumps({"token": totp}),
        token=token,
    )
    return result['oathvalidate']['enabled'], result['oathvalidate']['valid']
