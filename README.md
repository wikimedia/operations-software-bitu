# Bitu IDM

## Setup development environment
To work on the Bitu project you will frequently need an LDAP installation. A preconfigured Docker instance, based on a custom OpenLDAP can be started using docker-compose by running:

```
$ docker-compose up -d
```

This will start a container running OpenLDAP, with a number of test users and groups loaded. The LDAP can be administered with the "cn=admin,dc=example,dc=org" account, using the password: "adminpassword".