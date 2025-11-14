"""Authentication domain exceptions."""


class AuthenticationError(Exception):
    """Base authentication error."""
    pass


class InvalidCredentialsError(AuthenticationError):
    """Invalid email or password."""
    pass


class EmailAlreadyExistsError(AuthenticationError):
    """Email already registered."""
    pass


class UserNotFoundError(AuthenticationError):
    """User not found."""
    pass


class InactiveUserError(AuthenticationError):
    """User account is inactive."""
    pass


class InvalidTokenError(AuthenticationError):
    """Invalid or expired token."""
    pass
