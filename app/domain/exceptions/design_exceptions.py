"""Design domain exceptions."""


class DesignError(Exception):
    """Base design error."""
    pass


class DesignNotFoundError(DesignError):
    """Design not found."""
    pass


class UnauthorizedDesignAccessError(DesignError):
    """User doesn't own this design."""
    pass


class InvalidDesignDataError(DesignError):
    """Invalid design data."""
    pass
