"""
User repository interface (Domain layer).

This is a pure interface with NO implementation.
Defines the contract for user persistence operations.
"""

from abc import ABC, abstractmethod
from typing import Optional
from app.domain.entities.user import User


class IUserRepository(ABC):
    """
    User repository interface.
    
    All implementations MUST provide these methods.
    Domain layer depends on this interface, NOT on implementations.
    """
    
    @abstractmethod
    async def create(self, user: User) -> User:
        """
        Create new user in persistence layer.
        
        Args:
            user: User entity to persist
            
        Returns:
            Created user entity (may include generated fields like timestamps)
            
        Raises:
            Exception: If user with same email already exists
        """
        pass
    
    @abstractmethod
    async def get_by_id(self, user_id: str) -> Optional[User]:
        """
        Get user by ID.
        
        Args:
            user_id: User unique identifier
            
        Returns:
            User entity if found, None otherwise
        """
        pass
    
    @abstractmethod
    async def get_by_email(self, email: str) -> Optional[User]:
        """
        Get user by email address.
        
        Args:
            email: User email address
            
        Returns:
            User entity if found, None otherwise
        """
        pass
    
    @abstractmethod
    async def update(self, user: User) -> User:
        """
        Update existing user.
        
        Args:
            user: User entity with updated fields
            
        Returns:
            Updated user entity
            
        Raises:
            Exception: If user not found
        """
        pass
    
    @abstractmethod
    async def delete(self, user_id: str) -> bool:
        """
        Soft delete user (sets is_deleted=True, is_active=False).
        
        Args:
            user_id: User unique identifier
            
        Returns:
            True if user was deleted, False if not found
        """
        pass
    
    @abstractmethod
    async def exists_email(self, email: str) -> bool:
        """
        Check if email already exists.
        
        Useful for validation before creating new user.
        
        Args:
            email: Email address to check
            
        Returns:
            True if email exists, False otherwise
        """
        pass
