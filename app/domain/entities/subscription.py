"""
Subscription domain entity (pure business logic).

NO framework dependencies - pure Python only.
"""

from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from enum import Enum
from typing import Optional


class PlanType(Enum):
    """Subscription plan types."""

    FREE = "free"
    STARTER = "starter"
    PROFESSIONAL = "professional"
    ENTERPRISE = "enterprise"


class SubscriptionStatus(Enum):
    """Subscription status values."""

    ACTIVE = "active"
    CANCELED = "canceled"
    PAST_DUE = "past_due"
    TRIALING = "trialing"


# Plan limits (designs per month)
PLAN_LIMITS = {
    PlanType.FREE: 10,
    PlanType.STARTER: 100,
    PlanType.PROFESSIONAL: 1000,
    PlanType.ENTERPRISE: -1,  # Unlimited
}


@dataclass
class Subscription:
    """
    Subscription domain entity representing a user's subscription plan.

    This is pure business logic with NO external dependencies.
    NO SQLAlchemy, NO Pydantic, NO FastAPI.
    """

    id: str
    user_id: str
    plan: PlanType
    status: SubscriptionStatus
    stripe_customer_id: Optional[str]
    stripe_subscription_id: Optional[str]
    designs_this_month: int
    current_period_start: Optional[datetime]
    current_period_end: Optional[datetime]
    created_at: datetime
    updated_at: datetime

    @staticmethod
    def create(user_id: str, plan: PlanType = PlanType.FREE) -> "Subscription":
        """
        Factory method to create a new subscription.

        Args:
            user_id: User ID this subscription belongs to
            plan: Subscription plan type (default: FREE)

        Returns:
            New Subscription instance with defaults
        """
        from uuid import uuid4

        now = datetime.now(UTC)
        period_end = now + timedelta(days=30)  # 30-day billing period

        return Subscription(
            id=str(uuid4()),
            user_id=user_id,
            plan=plan,
            status=SubscriptionStatus.ACTIVE,
            stripe_customer_id=None,
            stripe_subscription_id=None,
            designs_this_month=0,
            current_period_start=now,
            current_period_end=period_end,
            created_at=now,
            updated_at=now,
        )

    def has_quota(self) -> bool:
        """
        Check if user has remaining design quota for this month.

        Returns:
            True if user can create more designs, False otherwise
        """
        limit = PLAN_LIMITS[self.plan]

        # Unlimited plans (enterprise)
        if limit == -1:
            return True

        return self.designs_this_month < limit

    def is_active(self) -> bool:
        """
        Check if subscription is active.

        Returns:
            True if subscription status is ACTIVE, False otherwise
        """
        return self.status == SubscriptionStatus.ACTIVE

    def get_remaining_quota(self) -> int:
        """
        Get remaining design quota for this month.

        Returns:
            Number of designs remaining (-1 for unlimited)
        """
        limit = PLAN_LIMITS[self.plan]

        # Unlimited plans
        if limit == -1:
            return -1

        remaining = limit - self.designs_this_month
        return max(0, remaining)

    def increment_usage(self) -> None:
        """
        Increment the designs_this_month counter.

        Raises:
            ValueError: If no quota remaining
        """
        if not self.has_quota():
            raise ValueError(
                f"Design quota exceeded for {self.plan.value} plan "
                f"({self.designs_this_month}/{PLAN_LIMITS[self.plan]})"
            )

        self.designs_this_month += 1
        self.updated_at = datetime.now(UTC)

    def reset_monthly_usage(self) -> None:
        """
        Reset monthly usage counter (called at billing period renewal).

        Also updates the billing period dates.
        """
        now = datetime.now(UTC)

        self.designs_this_month = 0
        self.current_period_start = now
        self.current_period_end = now + timedelta(days=30)
        self.updated_at = now

    def upgrade_plan(self, new_plan: PlanType) -> None:
        """
        Upgrade subscription to a higher plan.

        Args:
            new_plan: New plan type

        Raises:
            ValueError: If trying to downgrade or same plan
        """
        plan_order = [PlanType.FREE, PlanType.STARTER, PlanType.PROFESSIONAL, PlanType.ENTERPRISE]

        current_idx = plan_order.index(self.plan)
        new_idx = plan_order.index(new_plan)

        if new_idx <= current_idx:
            raise ValueError(f"Cannot upgrade from {self.plan.value} to {new_plan.value}")

        self.plan = new_plan
        self.updated_at = datetime.now(UTC)

    def downgrade_plan(self, new_plan: PlanType) -> None:
        """
        Downgrade subscription to a lower plan.

        Args:
            new_plan: New plan type

        Raises:
            ValueError: If trying to upgrade or same plan
        """
        plan_order = [PlanType.FREE, PlanType.STARTER, PlanType.PROFESSIONAL, PlanType.ENTERPRISE]

        current_idx = plan_order.index(self.plan)
        new_idx = plan_order.index(new_plan)

        if new_idx >= current_idx:
            raise ValueError(f"Cannot downgrade from {self.plan.value} to {new_plan.value}")

        self.plan = new_plan
        self.updated_at = datetime.now(UTC)

    def cancel(self) -> None:
        """
        Cancel subscription.

        Sets status to CANCELED but doesn't immediately revoke access.
        """
        if self.status == SubscriptionStatus.CANCELED:
            raise ValueError("Subscription is already canceled")

        self.status = SubscriptionStatus.CANCELED
        self.updated_at = datetime.now(UTC)

    def reactivate(self) -> None:
        """
        Reactivate a canceled subscription.

        Raises:
            ValueError: If subscription is not canceled
        """
        if self.status != SubscriptionStatus.CANCELED:
            raise ValueError("Can only reactivate canceled subscriptions")

        self.status = SubscriptionStatus.ACTIVE
        self.updated_at = datetime.now(UTC)

    def is_active(self) -> bool:
        """
        Check if subscription is currently active.

        Returns:
            True if subscription is active
        """
        return self.status == SubscriptionStatus.ACTIVE

    def validate_can_create_design(self) -> None:
        """
        Validate that user can create a new design.

        Raises:
            ValueError: If subscription is not active or no quota
        """
        if not self.is_active():
            raise ValueError(f"Subscription is {self.status.value}, must be active")

        if not self.has_quota():
            raise ValueError(
                f"Design quota exceeded for {self.plan.value} plan "
                f"({self.designs_this_month}/{PLAN_LIMITS[self.plan]})"
            )
