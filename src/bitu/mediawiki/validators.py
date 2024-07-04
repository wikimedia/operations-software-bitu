from . import mediawiki


def TOTPValidator(username, totp):
    return mediawiki.validate(username, totp)
