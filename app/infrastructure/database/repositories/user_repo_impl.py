"""
User repository implementation (Infrastructure layer).

Implements IUserRepository using SQLAlchemy 2.0 async.
"""

from typing import Optional
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.domain.entities.user import User
from app.domain.repositories.user_repository import IUserRepository
from app.infrastructure.database.models.user_model import UserModel
from app.infrastructure.database.converters import user_converter


class UserRepositoryImpl(IUserRepository):
    """
    User repository implementation using SQLAlchemy.
    
    This class bridges the domain layer (User entity) with
    the infrastructure layer (UserModel ORM).
    """
    
    def __init__(self, session: AsyncSession):
        """
        Initialize repository with database session.
        
        Args:
            session: SQLAlchemy async session
        """
        self.session = session
    
    async def create(self, user: User) -> User:
        """
        Create new user in database.
        
        Args:
            user: User entity to persist
            
        Returns:
            Created user entity with database-generated fields
            
        Raises:
            IntegrityError: If email already exists
        """
        model = user_converter.to_model(user)
        self.session.add(model)
        await self.session.flush()
        await self.session.refresh(model)
        return user_converter.to_entity(model)
    
    async def get_by_id(self, user_id: str) -> Optional[User]:
        """
        Get user by ID.
        
        Args:
            user_id: User unique identifier
            
        Returns:
            User entity if found, None otherwise
        """
        stmt = select(UserModel).where(
            UserModel.id == user_id,
            UserModel.is_deleted == False  # Exclude soft-deleted users
        )
        result = await self.session.execute(stmt)
        model = result.scalar_one_or_none()
        return user_converter.to_entity(model) if model else None
    
    async def get_by_email(self, email: str) -> Optional[User]:
        """
        Get user by email address.
        
        Args:
            email: User email address
            
        Returns:
            User entity if found, None otherwise
        """
        stmt = select(UserModel).where(
            UserModel.email == email,
            UserModel.is_deleted == False  # Exclude soft-deleted users
        )
        result = await self.session.execute(stmt)
        model = result.scalar_one_or_none()
        return user_converter.to_entity(model) if model else None
    
    async def update(self, user: User) -> User:
        """
        Update existing user.
        
        Args:
            user: User entity with updated fields
            
        Returns:
            Updated user entity
            
        Raises:
            NoResultFound: If user not found
        """
        stmt = select(UserModel).where(UserModel.id == user.id)
        result = await self.session.execute(stmt)
        model = result.scalar_one()  # Raises NoResultFound if not exists
        
        # Update model with entity data
        model = user_converter.to_model(user, model)
        await self.session.flush()
        await self.session.refresh(model)
        
        return user_converter.to_entity(model)
    
    async def delete(self, user_id: str) -> bool:
        """
        Soft delete user (sets is_deleted=True, is_active=False).
        
        Args:
            user_id: User unique identifier
            
        Returns:
            True if user was deleted, False if not found
        """
        stmt = (
            update(UserModel)
            .where(UserModel.id == user_id)
            .values(is_deleted=True, is_active=False)
        )
        result = await self.session.execute(stmt)
        await self.session.flush()
        return result.rowcount > 0
    
    async def exists_email(self, email: str) -> bool:
        """
        Check if email already exists.
        
        Args:
            email: Email address to check
            
        Returns:
            True if email exists, False otherwise
        """
        stmt = select(UserModel.id).where(
            UserModel.email == email,
            UserModel.is_deleted == False  # Exclude soft-deleted users
        )
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none() is not None
