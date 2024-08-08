import bituldap


def manager_approval(permission_request, **kwargs) -> bool:
    # This could be managed by a "unique_together" on a database level, but that also
    # limits testability.
    # 1) Get all approvals, logs with the approved field set to true.
    # 2) Get all the usernames of approvers.
    # 3) Convert list of usernames to a set, to filter out duplicated (the same manager
    #    approved the request multiple times).
    approvals = set(
        permission_request.log_set.filter(
            created_by__username__in=kwargs['managers'], approved=True
        ).values_list('created_by__username', flat=True))
    return len(approvals) == kwargs['count']


def ldap_attribute(permission_request, **kwargs) -> bool:
    entry = bituldap.get_user(permission_request.user.get_username())
    if not entry:
        return False

    # Limit the operators we allow to avoid rules with uses "upper" which will always return True, or
    # equivalent.
    valid_operators = ['__contains__', '__eq__', 'isalnum', 'isalpha', 'isascii', 'isdecimal',
                       'isdigit', 'isidentifier', 'islower', 'isnumeric', 'isprintable', 'isspace',
                       'istitle', 'isupper', 'startswith', 'endswith']

    if kwargs['operator'] not in valid_operators:
        return False

    attr = entry.entry_attributes_as_dict[kwargs['attribute']][0]
    operator = getattr(attr, kwargs['operator'])
    return operator(kwargs['value'])


def email_domain(permission_request, **kwargs):
    # Get email address from LDAP, to avoid sync errors.
    # This can also be implemented using ldap_attribute, but here we
    # ensure that the @ is included.
    entry = bituldap.get_user(permission_request.user.get_username())
    return entry.mail.__str__().endswith(f'@{kwargs["domain"]}')
