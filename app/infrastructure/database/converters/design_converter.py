"""
Design converter - Convert between DesignModel and Design entity.

Handles JSONB design_data field and enum types.
"""

from app.domain.entities.design import Design, DesignStatus
from app.infrastructure.database.models.design_model import DesignModel


def to_entity(model: DesignModel) -> Design:
    """
    Convert DesignModel (SQLAlchemy) to Design entity (Domain).
    
    Args:
        model: SQLAlchemy DesignModel instance
        
    Returns:
        Domain Design entity
        
    Note:
        design_data is stored as JSONB in PostgreSQL,
        SQLAlchemy automatically converts to/from Python dict.
    """
    return Design(
        id=model.id,
        user_id=model.user_id,
        product_type=model.product_type,
        design_data=model.design_data,  # JSONB -> dict (automatic)
        status=DesignStatus(model.status),  # Convert string to enum
        preview_url=model.preview_url,
        thumbnail_url=model.thumbnail_url,
        is_deleted=model.is_deleted,
        created_at=model.created_at,
        updated_at=model.updated_at,
    )


def to_model(entity: Design, model: DesignModel = None) -> DesignModel:
    """
    Convert Design entity (Domain) to DesignModel (SQLAlchemy).
    
    Args:
        entity: Domain Design entity
        model: Existing DesignModel to update (optional)
        
    Returns:
        SQLAlchemy DesignModel instance
        
    Note:
        design_data dict is automatically converted to JSONB by SQLAlchemy.
    """
    if model is None:
        model = DesignModel()
    
    model.id = entity.id
    model.user_id = entity.user_id
    model.product_type = entity.product_type
    model.design_data = entity.design_data  # dict -> JSONB (automatic)
    model.status = entity.status.value  # Convert enum to string
    model.preview_url = entity.preview_url
    model.thumbnail_url = entity.thumbnail_url
    model.is_deleted = entity.is_deleted
    model.created_at = entity.created_at
    model.updated_at = entity.updated_at
    
    return model
