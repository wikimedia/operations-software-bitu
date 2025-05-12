.. SPDX-License-Identifier: GPL-3.0-or-later

Permission Request Module
==========================

Bitu provides a module for requesting and approving access to e.g. LDAP groups.
The system is plugable, and allows for other permission backends to be added.

Creating a backend
------------------
Backends can be implemented by using the base class, "permissions.permission.BaseBackend".
You must provide an implementation for all methods in the base class.

Additional permission backends are enabled under the BITU_SUB_SYSTEMS setting, by adding the
new backend class under the "permission" key for a given subsystem.

Example:

.. code-block:: python3

    BITU_SUB_SYSTEMS = {
            'ldapbackend': {
            'manage_ssh_keys': True,
            'permissions': 'ldapbackend.permission.LDAPPermissions',
        ...


Configuration approval rules
----------------------------
Three "validators" are shipped with Bitu:

* manager_approval
* ldap_attribute
* email_domain

For each permission/group that can be requested, you must provide at least one rule for validation.

Manager approval
================
The manager_approval validator take three parameters, the permission request, a list of managers, and a
count, indicating how many managers must approve of the request.





.. automodule:: permissions

.. rubric:: Subpackages and Submodules

.. toctree::
