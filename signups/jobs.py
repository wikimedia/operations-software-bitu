# SPDX-License-Identifier: GPL-3.0-or-later
import base64
from django_rq import job
from django.urls import reverse


@job('notification')
def send_activation_email(signup):
    token = signup.generate_activation_token()
    sid = base64.b64encode(bytes(signup.pk.hex, 'utf8'))
    url = reverse('signups:activate', kwargs={'token': token, 'uidb64': sid.decode(encoding='utf8')})
    print(url)
