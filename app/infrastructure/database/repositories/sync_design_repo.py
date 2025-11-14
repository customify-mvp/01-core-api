"""
Sync Design repository for Celery workers.

Simplified sync version for task operations.
"""

from typing import Optional
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.domain.entities.design import Design
from app.infrastructure.database.models.design_model import DesignModel
from app.infrastructure.database.converters import design_converter


class SyncDesignRepository:
    """
    Sync design repository for Celery tasks.
    
    Provides basic CRUD operations with sync SQLAlchemy.
    """
    
    def __init__(self, session: Session):
        """
        Initialize repository with sync session.
        
        Args:
            session: SQLAlchemy sync session
        """
        self.session = session
    
    def get_by_id(self, design_id: str) -> Optional[Design]:
        """
        Get design by ID.
        
        Args:
            design_id: Design unique identifier
            
        Returns:
            Design entity if found, None otherwise
        """
        stmt = select(DesignModel).where(
            DesignModel.id == design_id,
            DesignModel.is_deleted == False
        )
        result = self.session.execute(stmt)
        model = result.scalar_one_or_none()
        return design_converter.to_entity(model) if model else None
    
    def update(self, design: Design) -> Design:
        """
        Update existing design.
        
        Args:
            design: Design entity with updated data
            
        Returns:
            Updated design entity
        """
        # Get existing model
        stmt = select(DesignModel).where(DesignModel.id == design.id)
        result = self.session.execute(stmt)
        model = result.scalar_one_or_none()
        
        if not model:
            raise ValueError(f"Design {design.id} not found")
        
        # Update model with entity data
        model.status = design.status.value
        model.preview_url = design.preview_url
        model.thumbnail_url = design.thumbnail_url
        model.design_data = design.design_data
        model.updated_at = design.updated_at
        
        self.session.flush()
        self.session.refresh(model)
        
        return design_converter.to_entity(model)
