from typing import Optional


class AppException(Exception):
    """
    Base exception for the entire application.
    Domain and service layers should raise only these.
    """

    status_code: int = 400
    error_code: str = "APP_ERROR"
    message: str = "Something went wrong"

    def __init__(
        self,
        message: Optional[str] = None,
        *,
        status_code: Optional[int] = None,
        error_code: Optional[str] = None,
    ) -> None:
        if message is not None:
            self.message = message
        if status_code is not None:
            self.status_code = status_code
        if error_code is not None:
            self.error_code = error_code
        super().__init__(self.message)


# ---- Auth / Security ----

class AuthenticationError(AppException):
    status_code = 401
    error_code = "AUTHENTICATION_FAILED"
    message = "Authentication failed"

class InvalidCredentials(AuthenticationError):
    error_code = "INVALID_CREDENTIALS"
    message = "Invalid email or password"

class AuthorizationError(AppException):
    status_code = 403
    error_code = "FORBIDDEN"
    message = "You do not have permission to perform this action"

# ---- Common ----

class ResourceNotFound(AppException):
    status_code = 404
    error_code = "NOT_FOUND"
    message = "Resource not found"

class ResourceConflict(AppException):
    status_code = 409
    error_code = "RESOURCE_CONFLICT"
    message = "Resource with given attributes already exists"
