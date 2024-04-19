.. SPDX-License-Identifier: GPL-3.0-or-later

REST API
===========
A number of APIs are available to external systems, either as a means
of integrating with Bitu, or to access certain features or datasets.

These APIs are exposed as HTTP endpoints and require authentication.
Each API can be accessed using an authenticated user, with the correct
set of permissions. Permissions are managed using Djangos built in
permission model.

One example of an API is the username validation API. It is available
at the ``/signup/api/username/`` endpoint.


.. rubric:: Available APIs

.. toctree::

       username


Authentication
---------------------
Systems integrating with Bitu are expected to use token authentication.

For clients to authenticate, the token key should be included in the
Authorization HTTP header. The key should be prefixed by the string
literal "Token", with whitespace separating the two strings.

For example:

.. code-block:: bash

    Authorization: Token 9944b09199c62bcf9418ad846dd0e4bbdfc6ee4b

Using Curl:

.. code-block:: bash

    curl -X GET http://127.0.0.1:8000/api/example/ -H 'Authorization: Token 9944b09199c62bcf9418ad846dd0e4bbdfc6ee4b'

