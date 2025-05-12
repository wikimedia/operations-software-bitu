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

### Renew keystore for CAS container
CAS is exposed via https, which means including a certificate. This certificate has a 90 expiration and will routinely need to be updated/regenerated. This can be done using the following command:

```
$ keytool -genkeypair -alias cas -keyalg RSA -keypass changeit -storepass changeit -keystore docker/cas/keystore.jks -dname "CN=cas.example.org,OU=Example,OU=Org,C=US" -storetype PKCS12 -ext "SAN=dns:example.org,dns:localhost,ip:127.0.0.1"
```

## Vue JS environment

The Vue JS applications are stored in the "frontend" subdirectory. The integration into Django is managed by the Django Vite module, which will load the Vue applications either from the Vite development environment, or from "compiled" Javascript files in production, served by the webserver.

Bitu requires each "page" to be its own separate Vue appliction, rather than having one large Vue application. This is done to allow all routing to be handled by Django, as well to avoid dealing with authentication and tokens within the Vue code.


### Running the development server

You can either run the NPM commands manually, or use the supplied Makefile.

To run the development server using NPM do:

```
$ npm ci
$ npm run dev
```

Alternatively run:
```
$ make dev
```

This will fetch the required Javascript packages, and update any packages with security issues and start the Vite development server.

### Building the Vue applications for release
Due to limitation of our build environment and the need to deploy Bitu as a Debian package, the updated and compiled Vue applications must be checked into Git. Running ```make release``` will update and install dependencies, build the application and add them to Git. You must manually handle ```git commit``` and write the appropriote commit message.