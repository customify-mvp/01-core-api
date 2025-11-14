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
    2. Password must be hashed
    3. Auto-create free subscription
    4. User starts unverified
    """
    
    def __init__(
        self,
        user_repo: IUserRepository,
        subscription_repo: ISubscriptionRepository,
    ):
        self.user_repo = user_repo
        self.subscription_repo = subscription_repo
    
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
        """
        # 1. Check email not exists
        if await self.user_repo.exists_email(email):
            raise EmailAlreadyExistsError(f"Email {email} already registered")
        
        # 2. Hash password
        password_hash = hash_password(password)
        
        # 3. Create user entity
        user = User.create(
            email=email,
            password_hash=password_hash,
            full_name=full_name
        )
        
        # 4. Persist user
        created_user = await self.user_repo.create(user)
        
        # 5. Create free subscription
        subscription = Subscription.create(
            user_id=created_user.id,
            plan=PlanType.FREE,
        )
        await self.subscription_repo.create(subscription)
        
        return created_user
