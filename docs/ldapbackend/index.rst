.. SPDX-License-Identifier: GPL-3.0-or-later

LDAPBackend
===========

Configuration
-------------
The ldapbackend provides a number of configuration options. These are
primarily used during the signup process.

Note that the ldapbackend assumes that the following schemas are
loaded in the LDAP server:

* inetorgperson.schema (Provided by OpenLDAP)
* rfc2307bis.schema (Distributed with Bitu in the folder: docker/build/schemas)

The ldapbackend utilizes the Bitu-LDAP library, which itself is a wrapper around
ldap3 (https://ldap3.readthedocs.io/), to communicate with LDAP servers. You must
configure Bitu-LDAP before you can use the ldapbackend. Details on configuration
can be found here: https://gerrit.wikimedia.org/r/admin/repos/operations/software/bitu-ldap,general.

Note that Bitu is restricted by Bitu-LDAP and can only act users and groups in
the DNs (distinguished name) configured for Bitu-LDAP. Object outside the configured
DNs will not be visible in Bitu. In the following configuration example, the system
is restricted to the users under "ou=people,dc=example,dc=org" and group under the
"ou=groups,dc=example,dc=org" DN.

.. code-block:: python3

   BITU_LDAP = {
    'uri': 'ldap://openldap.local.wmftest.net:1389',
    'username': 'cn=admin,dc=example,dc=org',
    'password': 'adminpassword',
    'readonly': False,
    'connection_timeout': 5,
    'users': {
        'dn': 'ou=people,dc=example,dc=org',
        'object_classes': ['inetOrgPerson'],
        'auxiliary_classes': ['posixAccount', 'wikimediaPerson'],
    },
    'groups': {
      'dn': 'ou=groups,dc=example,dc=org'
    }
   }

Available options are:

* default_gid (int): Default group ID to assign to new users.
* default_groups (List[str]): Groups to assign membership to on creation.
* password_hash: Function to use to hash passwords.
* password_hash_method: Option for password_hash, the type of hash to apply
  to the provided password.

Example:

.. code-block:: python3

   BITU_SUB_SYSTEMS = {
      'ldapbackend': {
        'default_gid': 2000,
        'password_hash': 'ldapbackend.helpers.hash_password',
        'password_hash_method': HASHED_SALTED_SHA,
        'default_groups': ['staff',]
      }
   }

.. automodule:: ldapbackend

.. rubric:: Subpackages and Submodules

.. toctree::

   ldapbackend.helpers
   ldapbackend.validators