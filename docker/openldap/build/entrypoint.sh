#!/bin/bash
# SPDX-License-Identifier: GPL-3.0-or-later

TMP_CONF=/tmp/slapd.conf

if [ -z ${LDAP_ROOT} ]; then
    LDAP_ROOT="dc=example,dc=org"
fi

if [ -z ${LDAP_LOGLEVEL} ]; then
    LDAP_LOGLEVEL=256
fi

if [ -z ${LDAP_ADMIN_PASSWORD} ]; then
    LDAP_ADMIN_PASSWORD=adminpassword
fi

if [ -z ${LDAP_ADMIN_USERNAME} ]; then
    LDAP_ADMIN_USERNAME="admin"
fi

export LDAP_ENCRYPTED_ADMIN_PASSWORD="$(echo -n $LDAP_ADMIN_PASSWORD | slappasswd -n -T /dev/stdin)"

cat << EOF > $TMP_CONF
# Schema and objectClass definitions
include         /etc/ldap/schema/core.schema
include         /etc/ldap/schema/cosine.schema
include         /etc/ldap/schema/rfc2307bis.schema
include         /etc/ldap/schema/inetorgperson.schema
include         /etc/ldap/schema/dyngroup.schema
include         /etc/ldap/schema/samba.schema
include		    /etc/ldap/schema/wmf-user.schema
#include         /etc/ldap/schema/ppolicy.schema

pidfile /var/run/slapd/ldap.pid

modulepath  /usr/lib/ldap
moduleload  back_mdb
moduleload  back_monitor
moduleload  memberof
moduleload  syncprov
moduleload  auditlog
moduleload  ppolicy
moduleload  deref
moduleload  unique

database            mdb
suffix              $LDAP_ROOT
directory           /var/lib/ldap/
rootdn              "cn=$LDAP_ADMIN_USERNAME,$LDAP_ROOT"
readonly            false
rootpw              $LDAP_ENCRYPTED_ADMIN_PASSWORD

overlay unique
unique_uri ldap:///?uidNumber?sub?(objectClass=posixaccount)
unique_uri ldap:///?gidNumber?sub?(objectClass=posixgroup)
unique_uri ldap:///?cn?sub?(objectClass=posixaccount)

access to *
        by dn="cn=$LDAP_ADMIN_USERNAME,$LDAP_ROOT" write
        by * break

# The userPassword by default can be changed
# by the entry owning it if they are authenticated.
# Others should not be able to see it, except the
# admin entry below
# These access lines apply to database #1 only
access to attrs=userPassword,shadowLastChange
        by dn="cn=admin,dc=example,dc=org" write
        by anonymous auth
        by self write
        by * none

# Ensure read access to the base for things like
# supportedSASLMechanisms.  Without this you may
# have problems with SASL not knowing what
# mechanisms are available and the like.
# Note that this is covered by the 'access to *'
# ACL below too but if you change that as people
# are wont to do you'll still need this if you
# want SASL (and possible other things) to work
# happily.
access to dn.base="" by * read

# everyone can read everything else not already defined
# in above rules and write self
access to *
        by self write
        by * read

EOF

mv /tmp/slapd.conf /etc/ldap/slapd.conf
bash
slapd -f /etc/ldap/slapd.conf -d $LDAP_LOGLEVEL &
is_alive & sleep 5

for ldif_file in /ldifs/*.ldif; do
    ldapadd -f $ldif_file -x -D cn=$LDAP_ADMIN_USERNAME,$LDAP_ROOT -w $LDAP_ADMIN_PASSWORD
done

kill -9 `cat /var/run/slapd/ldap.pid` && sleep 5
slapd -f /etc/ldap/slapd.conf -d $LDAP_LOGLEVEL

