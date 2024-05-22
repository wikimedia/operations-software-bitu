# Bitu IDM

## Setup development environment
Bitu ships with a docker-compose files, which can start up a full development environment for you.
Included in this environment is:

* A database server (MariaDB)
* A Redis server (Used by the queuing system)
* An LDAP server for working on LDAP integration
* A containerized version of Bitu.

For development work, you do not need the Bitu container, all the container started by docker-compose will expose the required ports for you to start working in your local development environment.

To build the Bitu docker image you'll need Blubber a Buildkit extension by Wikimedia Foundation, see: https://doc.wikimedia.org/releng/blubber/

To start the environment run:

```
$ docker-compose up -d
```

### Blubber on macOS
Currently Blubber is not distributed for ARM, and Apple M-series chips, so you will need to build it manually.

```
$ git clone https://gitlab.wikimedia.org/repos/releng/blubber.git
$ cd blubber
$ make blubber-buildkit-docker
```

This will build a local docker image which can be used as part of the Buildkit pipeline. To use this image edit the .pipeline/blubber.yaml and change the syntax line to:

```
# syntax = localhost/blubber-buildkit
```

### Default users
The docker environment contains a number of default users, which can be used to debug.

For authenticating with Bitu, via Django-LDAP-Auth, use the username: 'admin', password: 'admin'.
This is a LDAP backed Django superuser, which can also access the Django admin interface.

The OpenLDAP container is accessible on openldap.local.wmftest.net, port: 1389, using the username: 'cn=admin,dc=example,dc=org' and password: 'adminpassword'.

MariaDB can be accessed on db.local.wmftest.net, port 3306, using either the username: "idm", password: "secret", which will grant you access to the idm database, backing the Bitu environment. For root access to MariaDB please use username: 'root', password: 'password'