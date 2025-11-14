"""
Design repository implementation (Infrastructure layer).

Implements IDesignRepository using SQLAlchemy 2.0 async.
"""

from typing import Optional, List, Tuple
from sqlalchemy import select, update, func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.domain.entities.design import Design, DesignStatus
from app.domain.repositories.design_repository import IDesignRepository
from app.infrastructure.database.models.design_model import DesignModel
from app.infrastructure.database.converters import design_converter


class DesignRepositoryImpl(IDesignRepository):
    """
    Design repository implementation using SQLAlchemy.
    
    Handles design persistence, queries, and pagination.
    """
    
    def __init__(self, session: AsyncSession):
        """
        Initialize repository with database session.
        
        Args:
            session: SQLAlchemy async session
        """
        self.session = session
    
    async def create(self, design: Design) -> Design:
        """
        Create new design.
        
        Args:
            design: Design entity to persist
            
        Returns:
            Created design entity
        """
        model = design_converter.to_model(design)
        self.session.add(model)
        await self.session.flush()
        await self.session.refresh(model)
        return design_converter.to_entity(model)
    
    async def get_by_id(self, design_id: str) -> Optional[Design]:
        """
        Get design by ID.
        
        Args:
            design_id: Design unique identifier
            
        Returns:
            Design entity if found, None otherwise
        """
        stmt = select(DesignModel).where(
            DesignModel.id == design_id,
            DesignModel.is_deleted == False  # Exclude soft-deleted designs
        )
        result = await self.session.execute(stmt)
        model = result.scalar_one_or_none()
        return design_converter.to_entity(model) if model else None
    
    async def get_by_user(
        self, 
        user_id: str,
        skip: int = 0,
        limit: int = 100,
        status: Optional[DesignStatus] = None
    ) -> Tuple[List[Design], int]:
        """
        Get user's designs with pagination (optimized, no N+1).
        
        Args:
            user_id: User unique identifier
            skip: Number of records to skip (pagination)
            limit: Maximum number of records to return
            status: Filter by design status (optional)
            
        Returns:
            Tuple of (list of design entities, total count)
        """
        # Build base query with eager loading to prevent N+1
        stmt = (
            select(DesignModel)
            .options(
                selectinload(DesignModel.user),  # Eager load relationships
                # selectinload(DesignModel.orders) if needed
            )
            .where(
                DesignModel.user_id == user_id,
                DesignModel.is_deleted == False
            )
        )
        
        # Add status filter if provided
        if status is not None:
            stmt = stmt.where(DesignModel.status == status.value)
        
        # Add pagination and ordering
        stmt = (
            stmt
            .order_by(DesignModel.created_at.desc())
            .offset(skip)
            .limit(limit)
        )
        
        result = await self.session.execute(stmt)
        models = result.scalars().all()
        
        # Separate count query for performance
        count_stmt = (
            select(func.count(DesignModel.id))
            .where(
                DesignModel.user_id == user_id,
                DesignModel.is_deleted == False
            )
        )
        
        if status is not None:
            count_stmt = count_stmt.where(DesignModel.status == status.value)
        
        count_result = await self.session.execute(count_stmt)
        total = count_result.scalar()
        
        designs = [design_converter.to_entity(model) for model in models]
        
        return designs, total
    
    async def update(self, design: Design) -> Design:
        """
        Update existing design.
        
        Args:
            design: Design entity with updated fields
            
        Returns:
            Updated design entity
            
        Raises:
            ValueError: If design not found
        """
        stmt = select(DesignModel).where(DesignModel.id == design.id)
        result = await self.session.execute(stmt)
        model = result.scalar_one_or_none()
        
        if model is None:
            raise ValueError(f"Design with id {design.id} not found")
        
        # Update model with entity data
        model = design_converter.to_model(design, model)
        await self.session.flush()
        await self.session.refresh(model)
        
        return design_converter.to_entity(model)
    
    async def delete(self, design_id: str) -> bool:
        """
        Soft delete design (sets is_deleted=True).
        
        Args:
            design_id: Design unique identifier
            
        Returns:
            True if design was deleted, False if not found
        """
        stmt = (
            update(DesignModel)
            .where(DesignModel.id == design_id)
            .values(is_deleted=True)
        )
        result = await self.session.execute(stmt)
        await self.session.flush()
        return result.rowcount > 0
    
    async def count_by_user(
        self, 
        user_id: str,
        status: Optional[DesignStatus] = None
    ) -> int:
        """
        Count user's designs.
        
        Useful for subscription quota validation.
        
        Args:
            user_id: User unique identifier
            status: Filter by design status (optional)
            
        Returns:
            Number of designs
        """
        # Build base query
        stmt = select(func.count(DesignModel.id)).where(
            DesignModel.user_id == user_id,
            DesignModel.is_deleted == False
        )
        
        # Add status filter if provided
        if status is not None:
            stmt = stmt.where(DesignModel.status == status.value)
        
        result = await self.session.execute(stmt)
        return result.scalar_one()
