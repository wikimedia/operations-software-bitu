import bituldap

# Validators take a permission request and kwargs, kwargs being the configuration from
# the settings file. Validators return two booleans, approved and processed.
#
# If "processed" is True the approved value will contain a valid approval status for
# the request (True/False). If processed is not True, the request cannot currently be
# validated, e.g. no managers have approved the requests yet. In this case the approval
# MUST NOT be trusted to contain a valid status and the validator should not be included
# in the evaluation of the request.

def manager_approval(permission_request, **kwargs) -> tuple[bool, bool]:
    # This could be managed by a "unique_together" on a database level, but that also
    # limits testability.
    # 1) Get all rejections, logs with the approved field set to false, created by
    #    managers of this permission.
    # 2) Count the number of rejections, any number of rejections, greater than zero
    #    will be considered a rejection of the entire request.
    rejections = permission_request.log_set.filter(
        created_by__username__in=kwargs['managers'], approved=False
        ).count()

    if rejections:
        return False, True

    # Request is not rejected, check if it is approved:
    # 1) Get all approvals, logs with the approved field set to true.
    # 2) Get all the usernames of approvers.
    # 3) Convert list of usernames to a set, to filter out duplicated (the same manager
    #    approved the request multiple times).
    approvals = set(
        permission_request.log_set.filter(
            created_by__username__in=kwargs['managers'], approved=True
        ).values_list('created_by__username', flat=True))

    # The request must be approved by at least the number of managers specified in the configuration.
    approved = len(approvals) == kwargs['count']
    if approved:
        return approved, True

    # The request was not rejected, but also does not have enough approvals to accept.
    # Return "not approved", but also not "processed".
    return False, False


def ldap_attribute(permission_request, **kwargs) -> tuple[bool, bool]:
    entry = bituldap.get_user(permission_request.user.get_username())
    if not entry:
        return False, True

    # Limit the operators we allow to avoid rules with uses "upper" which will always return True, or
    # equivalent.
    valid_operators = ['__contains__', '__eq__', 'isalnum', 'isalpha', 'isascii', 'isdecimal',
                       'isdigit', 'isidentifier', 'islower', 'isnumeric', 'isprintable', 'isspace',
                       'istitle', 'isupper', 'startswith', 'endswith']

    if kwargs['operator'] not in valid_operators:
        return False, True

    attr = entry.entry_attributes_as_dict[kwargs['attribute']][0]
    operator = getattr(attr, kwargs['operator'])
    return operator(kwargs['value']), True


def email_domain(permission_request, **kwargs):
    # Get email address from LDAP, to avoid sync errors.
    # This can also be implemented using ldap_attribute, but here we
    # ensure that the @ is included.
    entry = bituldap.get_user(permission_request.user.get_username())
    return entry.mail.__str__().endswith(f'@{kwargs["domain"]}'), True
