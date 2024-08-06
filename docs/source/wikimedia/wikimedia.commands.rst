Wikimedia Management Command
==============================

The "block" command
--------------------

The "block" command ships as part of the wikimedia module for Bitu.
This command allows an operator to block access to a number of Wikimedia 
systems from Bitu, using a management command.

Integrations exists into the following systems:
* Phabricator

Example (blocking user "noname" from Phabricator):


.. code-block:: bash

    $ bitu block -p noname
    Please confirm that you want to block user: noname for the following systems
        * Phabricator
    Confirm with yes/no: y
