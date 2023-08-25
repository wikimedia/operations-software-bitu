import bituldap as b

from ldap3 import Server, Connection, MOCK_SYNC
from ldap3.protocol.schemas.slapd24 import slapd_2_4_schema, slapd_2_4_dsa_info

def connect():
    username = 'cn=admin,dc=example,dc=org'
    password = 'adminpassword'

    users = b.types.LdapQueryOptions(
        'ou=people,dc=example,dc=org',
        ['inetOrgPerson'], ['posixAccount'])

    groups = b.types.LdapQueryOptions(
        'ou=groups,dc=example,dc=org',
        ['groupOfNames'], ['posixGroup'])

    server = Server.from_definition('mock_server', slapd_2_4_dsa_info, slapd_2_4_schema)
    b.singleton.shared_configuration = b.types.Configuration(
        servers=[server],
        username=username,
        password=password,
        read_only=False,
        users=users,
        groups=groups)

    connection = Connection(server=server, user=username, password=password,
                             client_strategy=MOCK_SYNC)
    connection.strategy.add_entry(username, {'userPassword': password, 'sn': 'admin'})
    connection.strategy.entries_from_json('ldapbackend/tests/data/entries.json')
    return connection.bind(), connection


def setup():
    _, connection = connect()
    b.singleton.shared_connection = connection