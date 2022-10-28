# Using OpenLDAP container

The container can be configured with a number of environment parameters and load LDIF files on startup.

## Environment variable
LDAP_ROOT: The LDAP ROOT DN, defaults to dc=example,dc=org
LDAP_LOGLEVEL: OpenLDAP loglevel, default 256
LDAP_ADMIN_USERNAME: Administrative username, defaults to "admin"
LDAP_ADMIN_PASSWORD: Password for administrative user, defaults to "adminpassword"

Note that the actual account for administration will be constructed from both LDAP_ROOT and LDAP_ADMIN_USERNAME, meaning that the default login will be "cn=admin,dc=example,dc=org"

## Launching the container

### Without loading data:
Launch empty LDAP directory, with default DN and administrative credentials.

```
docker run -d --name openldap -p 1389:389 docker-registry.wikimedia.org/dev/bullseye-openldap:1.0.0
```

### Load data from ldif files on startup
Assuming that a directory called "ldifs" is available in the current working directory. Files must have the .ldif extention. Files will be loaded in alphabetical order, so consider naming the files containing the top most elements 000_<filename>.ldif, 001_<filename>.ldif.
```
docker run -d --name openldap -p 1388:389 --mount type=bind,source=${pwd}/ldifs,target=/ldifs  docker-registry.wikimedia.org/dev/bullseye-openldap:1.0.0
```