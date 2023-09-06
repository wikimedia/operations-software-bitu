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


def create_test_users():
    user = b.new_user('test1')
    user.cn = 'Test1'
    user.sn = 'test1'
    user.uidNumber = 1000
    user.gidNumber = 1000
    user.homeDirectory = '/home/test1'
    user.entry_commit_changes()

    user = b.new_user('test2')
    user.cn = 'Test2'
    user.sn = 'test2'
    user.uidNumber = 2000
    user.gidNumber = 2000
    user.homeDirectory = '/home/test2'
    user.entry_commit_changes()

    user = b.new_user('test3')
    user.cn = 'Test3'
    user.sn = 'test3'
    user.uidNumber = 3000
    user.gidNumber = 3000
    user.homeDirectory = '/home/test3'
    user.entry_commit_changes()