"""
User domain entity (pure business logic).

NO framework dependencies - pure Python only.
"""

from dataclasses import dataclass
from datetime import datetime
from typing import Optional


@dataclass
class User:
    """
    User domain entity representing a merchant/application user.
    
    This is pure business logic with NO external dependencies.
    NO SQLAlchemy, NO Pydantic, NO FastAPI.
    """
    
    id: str
    email: str
    password_hash: str
    full_name: str
    avatar_url: Optional[str]
    is_active: bool
    is_verified: bool
    is_deleted: bool
    created_at: datetime
    updated_at: datetime
    last_login: Optional[datetime]
    
    @staticmethod
    def create(
        email: str,
        password_hash: str,
        full_name: str
    ) -> "User":
        """
        Factory method to create a new user.
        
        Args:
            email: User's email address (will be normalized to lowercase)
            password_hash: Already hashed password (use passlib)
            full_name: User's full name
            
        Returns:
            New User instance with defaults
        """
        from uuid import uuid4
        
        now = datetime.utcnow()
        
        return User(
            id=str(uuid4()),
            email=email.lower().strip(),  # Normalize email
            password_hash=password_hash,
            full_name=full_name.strip(),
            avatar_url=None,
            is_active=True,
            is_verified=False,  # Email verification required
            is_deleted=False,
            created_at=now,
            updated_at=now,
            last_login=None
        )
    
    def mark_login(self) -> None:
        """
        Mark user as logged in.
        
        Updates last_login and updated_at timestamps.
        """
        now = datetime.utcnow()
        self.last_login = now
        self.updated_at = now
    
    def update_profile(
        self,
        full_name: Optional[str] = None,
        avatar_url: Optional[str] = None
    ) -> None:
        """
        Update user profile information.
        
        Args:
            full_name: New full name (if provided)
            avatar_url: New avatar URL (if provided)
        """
        if full_name is not None:
            self.full_name = full_name.strip()
        
        if avatar_url is not None:
            self.avatar_url = avatar_url.strip() if avatar_url else None
        
        self.updated_at = datetime.utcnow()
    
    def verify_email(self) -> None:
        """
        Mark user's email as verified.
        
        Raises:
            ValueError: If user is already verified
        """
        if self.is_verified:
            raise ValueError("User email is already verified")
        
        self.is_verified = True
        self.updated_at = datetime.utcnow()
    
    def deactivate(self) -> None:
        """
        Deactivate user account (soft delete).
        
        Sets is_deleted and is_active to False.
        """
        self.is_deleted = True
        self.is_active = False
        self.updated_at = datetime.utcnow()
    
    def reactivate(self) -> None:
        """
        Reactivate a previously deactivated account.
        
        Raises:
            ValueError: If user was not deactivated
        """
        if not self.is_deleted:
            raise ValueError("User is not deactivated")
        
        self.is_deleted = False
        self.is_active = True
        self.updated_at = datetime.utcnow()
    
    def validate_can_login(self) -> None:
        """
        Validate that user can log in.
        
        Raises:
            ValueError: If user cannot log in (deleted, inactive, or not verified)
        """
        if self.is_deleted:
            raise ValueError("User account has been deleted")
        
        if not self.is_active:
            raise ValueError("User account is inactive")
        
        if not self.is_verified:
            raise ValueError("Email verification required")
