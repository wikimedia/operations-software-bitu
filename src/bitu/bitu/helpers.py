def capitalize_first(username: str) -> str:
    # Do not be tempted to replace this function with capitalize or title.
    # These methods do not do the same thing. Capitalize will ensure
    # that the the first letter is upper-case, and the remaining is
    # lower-case, mangling "John Doe" into "John doe". The reverse is the
    # true for "title", "john doe" will be returned as "John Doe" and while
    # that may be what the user intended, we cannot be sure, nor may it be
    # applicable in all languages.
    if not username:
        return username

    if len(username) == 1:
        return username.upper()

    return username[0].upper() + username[1:]