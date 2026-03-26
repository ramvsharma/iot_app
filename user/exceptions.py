class IotAppException(Exception):
    """Base class for all exceptions in the IoT application."""

    def __init__(self, message="An error occurred in the application."):
        self.message = message
        super().__init__(self.message)


class MissingTokenException(IotAppException):
    """Raised when the token is missing in the request headers."""

    def __init__(self, message="Token does not present."):
        self.message = message
        super().__init__(self.message)


class InvalidTokenException(IotAppException):
    """Raised when the token is missing in the request headers."""

    def __init__(self, message="Token is invalid."):
        self.message = message
        super().__init__(self.message)
