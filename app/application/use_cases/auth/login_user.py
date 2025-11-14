"""Use case: Login user."""

from typing import Tuple
from app.domain.entities.user import User
from app.domain.repositories.user_repository import IUserRepository
from app.domain.exceptions.auth_exceptions import (
    InvalidCredentialsError,
    InactiveUserError,
)
from app.shared.services.password_service import verify_password
from app.shared.services.jwt_service import create_access_token


class LoginUserUseCase:
    """
    Use case: Login user.
    
    Business Rules:
    1. Verify email exists
    2. Verify password correct
    3. User must be active
    4. Update last_login timestamp
    5. Generate JWT token
    """
    
    def __init__(self, user_repo: IUserRepository):
        self.user_repo = user_repo
    
    async def execute(self, email: str, password: str) -> Tuple[User, str]:
        """
        Login user.
        
        Args:
            email: User email
            password: Plain password
        
        Returns:
            Tuple of (User entity, JWT access token)
        
        Raises:
            InvalidCredentialsError: Invalid email or password
            InactiveUserError: User account is inactive
        """
        # 1. Normalize email
        email = email.lower().strip()
        
        # 2. Get user by email
        user = await self.user_repo.get_by_email(email)
        if user is None:
            raise InvalidCredentialsError("Invalid email or password")
        
        # 3. Verify password
        if not verify_password(password, user.password_hash):
            raise InvalidCredentialsError("Invalid email or password")
        
        # 4. Check user is active
        if not user.is_active or user.is_deleted:
            raise InactiveUserError("User account is inactive")
        
        # 5. Update last_login
        user.mark_login()
        await self.user_repo.update(user)
        
        # 6. Generate JWT token
        access_token = create_access_token(user.id)
        
        return user, access_token
