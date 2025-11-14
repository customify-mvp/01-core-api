"""Design endpoints."""

from fastapi import APIRouter, Depends, Query, status

from app.presentation.schemas.design_schema import (
    DesignCreateRequest,
    DesignResponse,
    DesignListResponse,
)
from app.presentation.dependencies.repositories import (
    get_design_repository,
    get_subscription_repository,
)
from app.presentation.dependencies.auth import get_current_user
from app.application.use_cases.designs.create_design import CreateDesignUseCase
from app.domain.repositories.design_repository import IDesignRepository
from app.domain.repositories.subscription_repository import ISubscriptionRepository
from app.domain.entities.user import User
from app.domain.exceptions.design_exceptions import (
    DesignNotFoundError,
    UnauthorizedDesignAccessError,
)


router = APIRouter(prefix="/designs", tags=["Designs"])


@router.post(
    "",
    response_model=DesignResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create new design",
    description="Create a new product design with text customization."
)
async def create_design(
    request: DesignCreateRequest,
    current_user: User = Depends(get_current_user),
    design_repo: IDesignRepository = Depends(get_design_repository),
    subscription_repo: ISubscriptionRepository = Depends(get_subscription_repository),
):
    """
    Create new design.
    
    - Validates subscription is active
    - Checks monthly quota not exceeded
    - Validates design data (font whitelist, hex color)
    - Increments usage counter
    - Queues render job (TODO)
    
    Requires:
        Authorization header with Bearer token
    
    Returns:
        DesignResponse: Created design
    
    Raises:
        400: Invalid design data
        402: Quota exceeded (upgrade plan)
        403: Subscription inactive
        401: Invalid/expired token
    """
    use_case = CreateDesignUseCase(design_repo, subscription_repo)
    design = await use_case.execute(
        user_id=current_user.id,
        product_type=request.product_type,
        design_data=request.design_data.model_dump(),
        use_ai_suggestions=request.use_ai_suggestions
    )
    return DesignResponse.model_validate(design)


@router.get(
    "",
    response_model=DesignListResponse,
    summary="List user designs",
    description="Get paginated list of user's designs."
)
async def list_designs(
    skip: int = Query(0, ge=0, description="Number of designs to skip"),
    limit: int = Query(20, ge=1, le=100, description="Max number of designs to return"),
    current_user: User = Depends(get_current_user),
    design_repo: IDesignRepository = Depends(get_design_repository),
):
    """
    List user's designs with pagination.
    
    - Returns only user's own designs
    - Excludes deleted designs
    - Ordered by created_at DESC (newest first)
    - Supports pagination
    
    Requires:
        Authorization header with Bearer token
    
    Returns:
        DesignListResponse: Paginated design list
    
    Raises:
        401: Invalid/expired token
    """
    # Get designs (without filters param)
    designs = await design_repo.get_by_user(
        user_id=current_user.id,
        skip=skip,
        limit=limit
    )
    
    # Get total count
    total = await design_repo.count_by_user(current_user.id)
    
    return DesignListResponse(
        designs=[DesignResponse.model_validate(d) for d in designs],
        total=total,
        skip=skip,
        limit=limit,
        has_more=(skip + limit) < total
    )


@router.get(
    "/{design_id}",
    response_model=DesignResponse,
    summary="Get design by ID",
    description="Get a specific design by its ID."
)
async def get_design(
    design_id: str,
    current_user: User = Depends(get_current_user),
    design_repo: IDesignRepository = Depends(get_design_repository),
):
    """
    Get design by ID.
    
    - Verifies design exists
    - Verifies ownership (only owner can access)
    
    Requires:
        Authorization header with Bearer token
    
    Returns:
        DesignResponse: Design data
    
    Raises:
        404: Design not found
        403: Not the design owner
        401: Invalid/expired token
    """
    design = await design_repo.get_by_id(design_id)
    
    if design is None:
        raise DesignNotFoundError(f"Design {design_id} not found")
    
    if design.user_id != current_user.id:
        raise UnauthorizedDesignAccessError(f"Design {design_id} does not belong to you")
    
    return DesignResponse.model_validate(design)
