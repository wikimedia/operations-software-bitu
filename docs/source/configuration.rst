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
