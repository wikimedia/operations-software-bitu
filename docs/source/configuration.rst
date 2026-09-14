.. SPDX-License-Identifier: GPL-3.0-or-later

Configuration
================================

The general feature set of the Bitu identity manager is configured
using the Django settings file. All configurable behaviour and module
loading is centralized under the BITU_SUB_SYSTEMS variable, though
modules are free to utilize their own separate settings.

The BITU_SUB_SYSTEMS must be a dictionary, where each key is the name
of an available module.

For Bitu to determining if a module can provide certain features the
module must exist as a key in the BITU_SUB_SYSTEMS dictionary. Installed
which are not listed in BITU_SUB_SYSTEMS will be ignored.

Single sign-out
--------------------------------

Signing out of Bitu also terminates the session at the OpenID Connect
provider, so that pressing the single sign-on button afterwards asks for
credentials again rather than restoring the previous session.

This happens whenever the current session was established through the
OpenID Connect backend and an end session endpoint is known. The endpoint
is taken from ``SOCIAL_AUTH_OIDC_END_SESSION_URL`` when set, and is
otherwise derived from ``SOCIAL_AUTH_OIDC_OIDC_ENDPOINT`` by appending
``/logout``, which is where Apereo CAS exposes it. With neither setting
present, or for sessions that were not established through the provider,
sign-out only clears the local Django session.

Note that the provider must accept the address Bitu sends as
``post_logout_redirect_uri`` for the user to be returned to Bitu; Apereo
CAS requires ``cas.logout.follow-service-redirects`` to be enabled for
that redirect to be followed.

As an alternative, or in addition, ``SOCIAL_AUTH_OIDC_PROMPT`` may be set
to ``login`` to make the provider re-authenticate the user on every
sign-in. This requires social-auth-core 4.7.0 or newer.
