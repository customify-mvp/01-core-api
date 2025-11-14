"""Repository dependencies for FastAPI."""

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.infrastructure.database.session import get_db_session
from app.infrastructure.database.repositories.user_repo_impl import UserRepositoryImpl
from app.infrastructure.database.repositories.subscription_repo_impl import SubscriptionRepositoryImpl
from app.infrastructure.database.repositories.design_repo_impl import DesignRepositoryImpl
from app.domain.repositories.user_repository import IUserRepository
from app.domain.repositories.subscription_repository import ISubscriptionRepository
from app.domain.repositories.design_repository import IDesignRepository


async def get_user_repository(
    session: AsyncSession = Depends(get_db_session)
) -> IUserRepository:
    """
    Dependency: User repository.
    
    Returns:
        User repository instance
    """
    return UserRepositoryImpl(session)


async def get_subscription_repository(
    session: AsyncSession = Depends(get_db_session)
) -> ISubscriptionRepository:
    """
    Dependency: Subscription repository.
    
    Returns:
        Subscription repository instance
    """
    return SubscriptionRepositoryImpl(session)


async def get_design_repository(
    session: AsyncSession = Depends(get_db_session)
) -> IDesignRepository:
    """
    Dependency: Design repository.
    
    Returns:
        Design repository instance
    """
    return DesignRepositoryImpl(session)
