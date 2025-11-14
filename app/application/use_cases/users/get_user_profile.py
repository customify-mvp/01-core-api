"""Use case: Get user profile."""

from app.domain.entities.user import User
from app.domain.repositories.user_repository import IUserRepository
from app.domain.exceptions.auth_exceptions import UserNotFoundError


class GetUserProfileUseCase:
    """
    Use case: Get user profile.
    
    Business Rules:
    1. User must exist
    2. Return user entity (includes subscription via relationship)
    """
    
    def __init__(self, user_repo: IUserRepository):
        self.user_repo = user_repo
    
    async def execute(self, user_id: str) -> User:
        """
        Get user profile by ID.
        
        Args:
            user_id: User ID (from JWT)
        
        Returns:
            User entity
        
        Raises:
            UserNotFoundError: User not found
        """
        user = await self.user_repo.get_by_id(user_id)
        
        if user is None:
            raise UserNotFoundError(f"User {user_id} not found")
        
        return user
