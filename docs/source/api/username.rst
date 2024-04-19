.. SPDX-License-Identifier: GPL-3.0-or-later

Username validation API
=======================
For systems that either want to complement user creation alongside Bitu,
or want to do prevalidation before sending a user to Bitu, an API for
validating the desired future username is provided.

This API is exposed as ``/signup/api/username`` and accepts one required
parameter (username), and one optional (uid).

The validators are applied to the API the same as Bitu applies them to
its own signup. These can be defined in the settings, using the
``SIGNUP_USERNAME_VALIDATORS`` and ``SIGNUP_UID_VALIDATORS`` options.
These are normal Django validators and can be augmented with either
Django provided or custom validators as required.

**Input parameters**

* username: username to validate (required)
* uid: desired shell account username (optional)

**Returns**

HTTP status code 201, if the username is valid along with

* username: Provided input username.
* uid: Either provided input uid, or a uid derived from the username, if not provided.
* sanitized: A version of the username which can be used by MediaWiki.

HTTP 400 Bad request of invalid input.

* username: Array of validation errors.
* uid: Array of validation errors, if uid was provided.

Example query, using Curl:

.. code-block:: bash

    $ curl -X POST http://127.0.0.1:8000/signup/api/username/ \                                                       12:26:59
        -H 'Authorization: Token 9944b09199c62bcf9418ad846dd0e4bbdfc6ee4b' \
        -H 'Content-Type: application/json' \
        --data '{"username":"Holger Drachmann", "uid":"hd"}'


