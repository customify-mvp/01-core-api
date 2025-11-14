"""Unit tests for User entity."""

import pytest
from datetime import datetime
from app.domain.entities.user import User


@pytest.mark.unit
def test_user_create():
    """Test User.create() factory method."""
    user = User.create(
        email="test@test.com",
        password_hash="hashed_password",
        full_name="Test User"
    )
    
    assert user.id is not None
    assert user.email == "test@test.com"
    assert user.password_hash == "hashed_password"
    assert user.full_name == "Test User"
    assert user.is_active is True
    assert user.is_verified is False
    assert user.is_deleted is False
    assert user.last_login is None
    assert user.created_at is not None
    assert user.updated_at is not None


@pytest.mark.unit
def test_user_mark_login():
    """Test User.mark_login() updates last_login."""
    user = User.create(
        email="test@test.com",
        password_hash="hash",
        full_name="Test"
    )
    
    assert user.last_login is None
    
    user.mark_login()
    
    assert user.last_login is not None
    assert isinstance(user.last_login, datetime)


@pytest.mark.unit
def test_user_update_profile():
    """Test User.update_profile() updates fields."""
    user = User.create(
        email="test@test.com",
        password_hash="hash",
        full_name="Test User"
    )
    
    assert user.full_name == "Test User"
    assert user.avatar_url is None
    
    user.update_profile(
        full_name="Updated Name",
        avatar_url="https://example.com/avatar.png"
    )
    
    assert user.full_name == "Updated Name"
    assert user.avatar_url == "https://example.com/avatar.png"


@pytest.mark.unit
def test_user_deactivate():
    """Test User.deactivate() marks user as inactive."""
    user = User.create(
        email="test@test.com",
        password_hash="hash",
        full_name="Test"
    )
    
    assert user.is_active is True
    assert user.is_deleted is False
    
    user.deactivate()
    
    assert user.is_active is False
    assert user.is_deleted is True


@pytest.mark.unit
def test_user_verify():
    """Test User.verify_email() marks user as verified."""
    user = User.create(
        email="test@test.com",
        password_hash="hash",
        full_name="Test"
    )
    
    assert user.is_verified is False
    
    user.verify_email()
    
    assert user.is_verified is True


@pytest.mark.unit
def test_user_created_at_is_set():
    """Test User.created_at is set on creation."""
    user = User.create(
        email="test@test.com",
        password_hash="hash",
        full_name="Test"
    )
    
    assert user.created_at is not None
    assert isinstance(user.created_at, datetime)
