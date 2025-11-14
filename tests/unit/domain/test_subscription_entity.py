"""Unit tests for Subscription entity."""

import pytest
from datetime import datetime, timezone, timedelta
from app.domain.entities.subscription import Subscription, PlanType, SubscriptionStatus, PLAN_LIMITS


@pytest.mark.unit
def test_subscription_create():
    """Test Subscription.create() factory method."""
    subscription = Subscription.create(
        user_id="user-123",
        plan=PlanType.FREE
    )
    
    assert subscription.id is not None
    assert subscription.user_id == "user-123"
    assert subscription.plan == PlanType.FREE
    assert subscription.status == SubscriptionStatus.ACTIVE
    assert subscription.designs_this_month == 0
    assert subscription.current_period_start is not None
    assert subscription.current_period_end is not None


@pytest.mark.unit
def test_subscription_is_active_true():
    """Test subscription is active after creation."""
    subscription = Subscription.create(
        user_id="user-123",
        plan=PlanType.FREE
    )
    
    assert subscription.status == SubscriptionStatus.ACTIVE


@pytest.mark.unit
def test_subscription_is_active_false_when_canceled():
    """Test subscription status can be changed to canceled."""
    subscription = Subscription.create(
        user_id="user-123",
        plan=PlanType.FREE
    )
    subscription.status = SubscriptionStatus.CANCELED
    
    assert subscription.status == SubscriptionStatus.CANCELED


@pytest.mark.unit
def test_subscription_can_create_design_free_plan_within_quota():
    """Test has_quota() returns True within FREE quota."""
    subscription = Subscription.create(
        user_id="user-123",
        plan=PlanType.FREE
    )
    subscription.designs_this_month = 5  # 5 of 10
    
    assert subscription.has_quota() is True


@pytest.mark.unit
def test_subscription_can_create_design_free_plan_quota_exceeded():
    """Test has_quota() returns False when FREE quota exceeded."""
    subscription = Subscription.create(
        user_id="user-123",
        plan=PlanType.FREE
    )
    subscription.designs_this_month = 10  # 10 of 10
    
    assert subscription.has_quota() is False


@pytest.mark.unit
def test_subscription_can_create_design_professional_plan_within_quota():
    """Test has_quota() returns True within PROFESSIONAL quota."""
    subscription = Subscription.create(
        user_id="user-123",
        plan=PlanType.PROFESSIONAL
    )
    subscription.designs_this_month = 50  # 50 of 1000
    
    assert subscription.has_quota() is True


@pytest.mark.unit
def test_subscription_can_create_design_enterprise_unlimited():
    """Test has_quota() returns True for ENTERPRISE (unlimited)."""
    subscription = Subscription.create(
        user_id="user-123",
        plan=PlanType.ENTERPRISE
    )
    subscription.designs_this_month = 1000  # Unlimited
    
    assert subscription.has_quota() is True


@pytest.mark.unit
def test_subscription_can_create_design_inactive_subscription():
    """Test subscription can be marked inactive."""
    subscription = Subscription.create(
        user_id="user-123",
        plan=PlanType.PROFESSIONAL
    )
    subscription.status = SubscriptionStatus.CANCELED
    
    assert subscription.status == SubscriptionStatus.CANCELED


@pytest.mark.unit
def test_subscription_increment_usage():
    """Test designs_this_month counter can be incremented."""
    subscription = Subscription.create(
        user_id="user-123",
        plan=PlanType.FREE
    )
    
    assert subscription.designs_this_month == 0
    
    subscription.designs_this_month += 1
    assert subscription.designs_this_month == 1
    
    subscription.designs_this_month += 1
    assert subscription.designs_this_month == 2


@pytest.mark.unit
def test_subscription_cancel():
    """Test subscription status can be changed to canceled."""
    subscription = Subscription.create(
        user_id="user-123",
        plan=PlanType.PROFESSIONAL
    )
    
    assert subscription.status == SubscriptionStatus.ACTIVE
    
    subscription.status = SubscriptionStatus.CANCELED
    
    assert subscription.status == SubscriptionStatus.CANCELED


@pytest.mark.unit
def test_subscription_upgrade_plan():
    """Test plan can be upgraded."""
    subscription = Subscription.create(
        user_id="user-123",
        plan=PlanType.FREE
    )
    
    assert subscription.plan == PlanType.FREE
    
    subscription.plan = PlanType.PROFESSIONAL
    
    assert subscription.plan == PlanType.PROFESSIONAL


@pytest.mark.unit
def test_subscription_monthly_limits():
    """Test monthly design limits for each plan."""
    # FREE plan
    assert PLAN_LIMITS[PlanType.FREE] == 10
    
    # STARTER plan
    assert PLAN_LIMITS[PlanType.STARTER] == 100
    
    # PROFESSIONAL plan
    assert PLAN_LIMITS[PlanType.PROFESSIONAL] == 1000
    
    # ENTERPRISE plan
    assert PLAN_LIMITS[PlanType.ENTERPRISE] == -1  # Unlimited
