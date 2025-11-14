"""Unit tests for User converter."""

import pytest
from datetime import datetime, timezone
from app.infrastructure.database.models.user_model import UserModel
from app.infrastructure.database.converters.user_converter import to_entity, to_model
from app.domain.entities.user import User


@pytest.mark.unit
def test_user_converter_to_entity():
    """Test converting UserModel to User entity."""
    # Arrange
    now = datetime.now(timezone.utc)
    model = UserModel(
        id="user-123",
        email="test@test.com",
        password_hash="hashed_password",
        full_name="Test User",
        avatar_url="https://example.com/avatar.png",
        is_active=True,
        is_verified=False,
        is_deleted=False,
        created_at=now,
        updated_at=now,
        last_login=None
    )
    
    # Act
    entity = to_entity(model)
    
    # Assert
    assert isinstance(entity, User)
    assert entity.id == "user-123"
    assert entity.email == "test@test.com"
    assert entity.password_hash == "hashed_password"
    assert entity.full_name == "Test User"
    assert entity.avatar_url == "https://example.com/avatar.png"
    assert entity.is_active is True
    assert entity.is_verified is False
    assert entity.is_deleted is False
    assert entity.created_at == now
    assert entity.updated_at == now
    assert entity.last_login is None


@pytest.mark.unit
def test_user_converter_to_model_new():
    """Test converting User entity to new UserModel."""
    # Arrange
    entity = User.create(
        email="new@test.com",
        password_hash="hashed",
        full_name="New User"
    )
    
    # Act
    model = to_model(entity)
    
    # Assert
    assert isinstance(model, UserModel)
    assert model.id == entity.id
    assert model.email == "new@test.com"
    assert model.password_hash == "hashed"
    assert model.full_name == "New User"
    assert model.is_active is True
    assert model.is_verified is False
    assert model.is_deleted is False
    assert model.created_at == entity.created_at
    assert model.updated_at == entity.updated_at


@pytest.mark.unit
def test_user_converter_to_model_update_existing():
    """Test updating existing UserModel from User entity."""
    # Arrange
    entity = User.create(
        email="update@test.com",
        password_hash="hash",
        full_name="Original Name"
    )
    
    existing_model = UserModel()
    existing_model.id = "old-id"
    existing_model.email = "old@test.com"
    
    # Act
    updated_model = to_model(entity, existing_model)
    
    # Assert
    assert updated_model is existing_model  # Same instance
    assert updated_model.id == entity.id  # Updated
    assert updated_model.email == "update@test.com"  # Updated
    assert updated_model.full_name == "Original Name"


@pytest.mark.unit
def test_user_converter_roundtrip():
    """Test converting User → Model → User preserves data."""
    # Arrange
    original_entity = User.create(
        email="roundtrip@test.com",
        password_hash="hash123",
        full_name="Roundtrip User"
    )
    
    # Act
    model = to_model(original_entity)
    converted_entity = to_entity(model)
    
    # Assert
    assert converted_entity.id == original_entity.id
    assert converted_entity.email == original_entity.email
    assert converted_entity.password_hash == original_entity.password_hash
    assert converted_entity.full_name == original_entity.full_name
    assert converted_entity.is_active == original_entity.is_active
    assert converted_entity.is_verified == original_entity.is_verified
    assert converted_entity.is_deleted == original_entity.is_deleted
