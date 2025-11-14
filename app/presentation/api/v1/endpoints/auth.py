"""Authentication endpoints."""

from fastapi import APIRouter, Depends, status

from app.presentation.schemas.auth_schema import (
    RegisterRequest,
    LoginRequest,
    UserResponse,
    LoginResponse,
)
from app.presentation.dependencies.repositories import (
    get_user_repository,
    get_subscription_repository,
)
from app.presentation.dependencies.auth import get_current_user
from app.application.use_cases.auth.register_user import RegisterUserUseCase
from app.application.use_cases.auth.login_user import LoginUserUseCase
from app.domain.repositories.user_repository import IUserRepository
from app.domain.repositories.subscription_repository import ISubscriptionRepository
from app.domain.entities.user import User


router = APIRouter(prefix="/auth", tags=["Authentication"])


@router.post(
    "/register",
    response_model=UserResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Register new user",
    description="Register new user account with email and password. Auto-creates free subscription."
)
async def register(
    request: RegisterRequest,
    user_repo: IUserRepository = Depends(get_user_repository),
    subscription_repo: ISubscriptionRepository = Depends(get_subscription_repository),
):
    """
    Register new user.
    
    - Creates user account
    - Validates password strength (min 8 chars, letter + number)
    - Normalizes email (lowercase, trimmed)
    - Auto-creates free subscription
    - User starts unverified
    
    Returns:
        UserResponse: Created user (without password)
    
    Raises:
        409: Email already exists
        400: Invalid password or validation error
    """
    use_case = RegisterUserUseCase(user_repo, subscription_repo)
    user = await use_case.execute(
        email=request.email,
        password=request.password,
        full_name=request.full_name
    )
    return UserResponse.model_validate(user)


@router.post(
    "/login",
    response_model=LoginResponse,
    summary="Login user",
    description="Authenticate user with email and password. Returns JWT access token."
)
async def login(
    request: LoginRequest,
    user_repo: IUserRepository = Depends(get_user_repository),
):
    """
    Login user.
    
    - Validates credentials
    - Normalizes email (case-insensitive)
    - Checks user is active
    - Updates last_login timestamp
    - Returns JWT token (7-day expiration)
    
    Returns:
        LoginResponse: Access token and user data
    
    Raises:
        401: Invalid credentials
        403: User account is inactive
    """
    use_case = LoginUserUseCase(user_repo)
    user, access_token = await use_case.execute(
        email=request.email,
        password=request.password
    )
    
    return LoginResponse(
        access_token=access_token,
        user=UserResponse.model_validate(user)
    )


@router.get(
    "/me",
    response_model=UserResponse,
    summary="Get current user profile",
    description="Get authenticated user's profile information."
)
async def get_me(
    current_user: User = Depends(get_current_user)
):
    """
    Get current authenticated user profile.
    
    Requires:
        Authorization header with Bearer token
    
    Returns:
        UserResponse: Current user data
    
    Raises:
        401: Invalid or expired token
        403: User account is inactive
    """
    return UserResponse.model_validate(current_user)
