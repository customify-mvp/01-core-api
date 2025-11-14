"""Unit tests for Subscription converter."""

import pytest
from datetime import datetime, timezone, timedelta
from app.infrastructure.database.models.subscription_model import SubscriptionModel
from app.infrastructure.database.converters.subscription_converter import to_entity, to_model
from app.domain.entities.subscription import Subscription, PlanType, SubscriptionStatus


@pytest.mark.unit
def test_subscription_converter_to_entity():
    """Test converting SubscriptionModel to Subscription entity."""
    # Arrange
    now = datetime.now(timezone.utc)
    period_end = now + timedelta(days=30)
    
    model = SubscriptionModel(
        id="sub-123",
        user_id="user-456",
        plan="free",
        status="active",
        stripe_customer_id="cus_123",
        stripe_subscription_id="sub_456",
        current_period_start=now,
        current_period_end=period_end,
        designs_this_month=5,
        created_at=now,
        updated_at=now
    )
    
    # Act
    entity = to_entity(model)
    
    # Assert
    assert isinstance(entity, Subscription)
    assert entity.id == "sub-123"
    assert entity.user_id == "user-456"
    assert entity.plan == PlanType.FREE
    assert entity.status == SubscriptionStatus.ACTIVE
    assert entity.stripe_customer_id == "cus_123"
    assert entity.stripe_subscription_id == "sub_456"
    assert entity.designs_this_month == 5
    assert entity.current_period_start == now
    assert entity.current_period_end == period_end


@pytest.mark.unit
def test_subscription_converter_to_entity_professional_plan():
    """Test converting SubscriptionModel with PROFESSIONAL plan."""
    # Arrange
    now = datetime.now(timezone.utc)
    model = SubscriptionModel(
        id="sub-pro",
        user_id="user-pro",
        plan="professional",
        status="active",
        stripe_customer_id=None,
        stripe_subscription_id=None,
        current_period_start=now,
        current_period_end=now + timedelta(days=30),
        designs_this_month=50,
        created_at=now,
        updated_at=now
    )
    
    # Act
    entity = to_entity(model)
    
    # Assert
    assert entity.plan == PlanType.PROFESSIONAL
    assert entity.designs_this_month == 50


@pytest.mark.unit
def test_subscription_converter_to_model_new():
    """Test converting Subscription entity to new SubscriptionModel."""
    # Arrange
    entity = Subscription.create(
        user_id="user-new",
        plan=PlanType.FREE
    )
    
    # Act
    model = to_model(entity)
    
    # Assert
    assert isinstance(model, SubscriptionModel)
    assert model.id == entity.id
    assert model.user_id == "user-new"
    assert model.plan == "free"  # String value
    assert model.status == "active"  # String value
    assert model.designs_this_month == 0


@pytest.mark.unit
def test_subscription_converter_to_model_update_existing():
    """Test updating existing SubscriptionModel from Subscription entity."""
    # Arrange
    entity = Subscription.create(
        user_id="user-update",
        plan=PlanType.STARTER
    )
    entity.designs_this_month = 25
    entity.status = SubscriptionStatus.CANCELED
    
    existing_model = SubscriptionModel()
    existing_model.id = "old-id"
    existing_model.plan = "free"
    existing_model.designs_this_month = 0
    
    # Act
    updated_model = to_model(entity, existing_model)
    
    # Assert
    assert updated_model is existing_model  # Same instance
    assert updated_model.id == entity.id  # Updated
    assert updated_model.plan == "starter"  # Updated
    assert updated_model.status == "canceled"  # Updated
    assert updated_model.designs_this_month == 25  # Updated


@pytest.mark.unit
def test_subscription_converter_roundtrip():
    """Test converting Subscription → Model → Subscription preserves data."""
    # Arrange
    original_entity = Subscription.create(
        user_id="roundtrip-user",
        plan=PlanType.ENTERPRISE
    )
    original_entity.designs_this_month = 100
    
    # Act
    model = to_model(original_entity)
    converted_entity = to_entity(model)
    
    # Assert
    assert converted_entity.id == original_entity.id
    assert converted_entity.user_id == original_entity.user_id
    assert converted_entity.plan == original_entity.plan
    assert converted_entity.status == original_entity.status
    assert converted_entity.designs_this_month == original_entity.designs_this_month
    assert converted_entity.current_period_start == original_entity.current_period_start
    assert converted_entity.current_period_end == original_entity.current_period_end


@pytest.mark.unit
def test_subscription_converter_all_plan_types():
    """Test conversion for all plan types."""
    plan_types = [
        (PlanType.FREE, "free"),
        (PlanType.STARTER, "starter"),
        (PlanType.PROFESSIONAL, "professional"),
        (PlanType.ENTERPRISE, "enterprise")
    ]
    
    for enum_plan, string_plan in plan_types:
        # Entity → Model
        entity = Subscription.create(user_id="user-test", plan=enum_plan)
        model = to_model(entity)
        assert model.plan == string_plan
        
        # Model → Entity
        model.plan = string_plan
        converted = to_entity(model)
        assert converted.plan == enum_plan


@pytest.mark.unit
def test_subscription_converter_all_status_types():
    """Test conversion for all status types."""
    entity = Subscription.create(user_id="user-status", plan=PlanType.FREE)
    
    statuses = [
        (SubscriptionStatus.ACTIVE, "active"),
        (SubscriptionStatus.CANCELED, "canceled"),
        (SubscriptionStatus.PAST_DUE, "past_due"),
        (SubscriptionStatus.TRIALING, "trialing")
    ]
    
    for enum_status, string_status in statuses:
        # Entity → Model
        entity.status = enum_status
        model = to_model(entity)
        assert model.status == string_status
        
        # Model → Entity
        model.status = string_status
        converted = to_entity(model)
        assert converted.status == enum_status
