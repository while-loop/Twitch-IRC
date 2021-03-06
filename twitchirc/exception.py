class IRCException(Exception):
    def __init__(self, value):
        self.value = value

    def __str__(self):
        return self.value


class IllegalArgumentError(ValueError):
    pass


class AuthenticationError(IRCException):
    pass


class APIError(Exception):
    """
        This exception gets raised whenever a non-200 status code was returned by the Twitch API.
    """

    def __init__(self, value):
        self.value = value

    def __str__(self):
        return self.value
