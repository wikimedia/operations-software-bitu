.. SPDX-License-Identifier: GPL-3.0-or-later

Development
===========

This section of the documentation guides you in configuring a
development environment, allowing you to work on Bitu locally.

Depending on the modules you need, docker may or may not be
required.

Getting the code
----------------
You can download the latest version of the Bitu code from the
Wikimedia Git repository:

.. code-block:: bash

   git clone "https://gerrit.wikimedia.org/r/operations/software/bitu"


Setting up a virtualenv
-----------------------
The recommended way of installing the dependencies for Bitu is by
using pip and a virtualenv.

.. code-block:: bash

   python3 -venv .venv
   source .venv/bin/activate
   pip install -r requirements-dev.txt




