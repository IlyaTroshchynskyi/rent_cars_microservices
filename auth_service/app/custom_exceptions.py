class UserNotFoundError(Exception):
    pass


class InvalidOldPasswordError(Exception):
    pass


class BadCredentialsError(Exception):
    pass


class InvalidCurrentPasswordError(Exception):
    pass


class UsernameAlreadyTakenError(Exception):
    pass
