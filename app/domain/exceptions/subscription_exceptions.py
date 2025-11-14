"""Subscription domain exceptions."""


class SubscriptionError(Exception):
    """Base subscription error."""
    pass


class QuotaExceededError(SubscriptionError):
    """User exceeded design quota for this month."""
    pass


class InactiveSubscriptionError(SubscriptionError):
    """Subscription is not active."""
    pass


class SubscriptionNotFoundError(SubscriptionError):
    """Subscription not found."""
    pass
