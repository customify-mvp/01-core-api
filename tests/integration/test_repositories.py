import pytest
from sqlalchemy.ext.asyncio import AsyncSession
from app.domain.entities.user import User
from app.infrastructure.database.repositories.user_repo_impl import UserRepositoryImpl
from app.shared.services.password_service import hash_password


@pytest.mark.asyncio
async def test_user_repository_create(db_session: AsyncSession):
    """Test creating user through repository."""
    repo = UserRepositoryImpl(db_session)
    
    # Create entity
    user = User.create(
        email="test_repo@test.com",
        password_hash=hash_password("Test1234"),
        full_name="Test Repo User"
    )
    
    # Persist
    created_user = await repo.create(user)
    
    # Assert
    assert created_user.id is not None
    assert created_user.email == "test_repo@test.com"
    print(f"✅ Created user: {created_user.id}")


@pytest.mark.asyncio
async def test_user_repository_get_by_email(db_session: AsyncSession):
    """Test getting user by email."""
    repo = UserRepositoryImpl(db_session)
    
    # Create first
    user = User.create(
        email="find_me@test.com",
        password_hash=hash_password("Test1234"),
        full_name="Find Me"
    )
    await repo.create(user)
    
    # Find by email
    found_user = await repo.get_by_email("find_me@test.com")
    
    # Assert
    assert found_user is not None
    assert found_user.email == "find_me@test.com"
    print(f"✅ Found user: {found_user.full_name}")


@pytest.mark.asyncio
async def test_user_repository_update(db_session: AsyncSession):
    """Test updating user."""
    repo = UserRepositoryImpl(db_session)
    
    # Create
    user = User.create(
        email="update_me@test.com",
        password_hash=hash_password("Test1234"),
        full_name="Original Name"
    )
    created_user = await repo.create(user)
    
    # Update
    created_user.update_profile(full_name="Updated Name")
    updated_user = await repo.update(created_user)
    
    # Assert
    assert updated_user.full_name == "Updated Name"
    print(f"✅ Updated user: {updated_user.full_name}")


@pytest.mark.asyncio
async def test_user_repository_exists_email(db_session: AsyncSession):
    """Test checking if email exists."""
    repo = UserRepositoryImpl(db_session)
    
    # Create
    user = User.create(
        email="exists@test.com",
        password_hash=hash_password("Test1234"),
        full_name="Exists User"
    )
    await repo.create(user)
    
    # Check exists
    exists = await repo.exists_email("exists@test.com")
    not_exists = await repo.exists_email("notexists@test.com")
    
    # Assert
    assert exists is True
    assert not_exists is False
    print("✅ exists_email() working")