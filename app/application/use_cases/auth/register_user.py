"""Use case: Register new user."""

from app.domain.entities.user import User
from app.domain.entities.subscription import Subscription, PlanType, SubscriptionStatus
from app.domain.repositories.user_repository import IUserRepository
from app.domain.repositories.subscription_repository import ISubscriptionRepository
from app.domain.exceptions.auth_exceptions import EmailAlreadyExistsError
from app.shared.services.password_service import hash_password


class RegisterUserUseCase:
    """
    Use case: Register new user.
    
    Business Rules:
    1. Email must be unique
    2. Password must meet strength requirements
    3. Password must be hashed
    4. Auto-create free subscription
    5. User starts unverified
    """
    
    def __init__(
        self,
        user_repo: IUserRepository,
        subscription_repo: ISubscriptionRepository,
    ):
        self.user_repo = user_repo
        self.subscription_repo = subscription_repo
    
    def _validate_password(self, password: str) -> None:
        """
        Validate password strength.
        
        Rules:
        - Min 8 characters
        - Max 100 characters
        - At least one letter
        - At least one number
        
        Args:
            password: Plain password to validate
        
        Raises:
            ValueError: If password doesn't meet requirements
        """
        if len(password) < 8:
            raise ValueError("Password must be at least 8 characters")
        
        if len(password) > 100:
            raise ValueError("Password must be less than 100 characters")
        
        if not any(c.isalpha() for c in password):
            raise ValueError("Password must contain at least one letter")
        
        if not any(c.isdigit() for c in password):
            raise ValueError("Password must contain at least one number")
    
    async def execute(self, email: str, password: str, full_name: str) -> User:
        """
        Register new user.
        
        Args:
            email: User email
            password: Plain password (will be hashed)
            full_name: User full name
        
        Returns:
            Created user entity
        
        Raises:
            EmailAlreadyExistsError: If email already registered
            ValueError: If password doesn't meet requirements
        """
        # 1. Validate password strength
        self._validate_password(password)
        
        # 2. Normalize email
        email = email.lower().strip()
        
        # 3. Check email not exists
        if await self.user_repo.exists_email(email):
            raise EmailAlreadyExistsError(f"Email {email} already registered")
        
        # 4. Hash password
        password_hash = hash_password(password)
        
        # 5. Create user entity
        user = User.create(
            email=email,
            password_hash=password_hash,
            full_name=full_name
        )
        
        # 6. Persist user
        created_user = await self.user_repo.create(user)
        
        # 7. Create free subscription
        subscription = Subscription.create(
            user_id=created_user.id,
            plan=PlanType.FREE,
        )
        await self.subscription_repo.create(subscription)
        
        return created_user
