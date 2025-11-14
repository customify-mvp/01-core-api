"""Design request/response schemas."""

from pydantic import BaseModel, Field
from typing import Literal
from datetime import datetime


class DesignDataSchema(BaseModel):
    """Design data (nested in DesignCreateRequest)."""
    
    text: str = Field(min_length=1, max_length=100)
    font: Literal['Bebas-Bold', 'Montserrat-Regular', 'Montserrat-Bold', 
                  'Pacifico-Regular', 'Roboto-Regular']
    color: str = Field(pattern=r'^#[0-9A-Fa-f]{6}$')
    
    model_config = {
        "json_schema_extra": {
            "example": {
                "text": "Hello World",
                "font": "Bebas-Bold",
                "color": "#FF0000"
            }
        }
    }


class DesignCreateRequest(BaseModel):
    """Create design request."""
    
    product_type: Literal['t-shirt', 'mug', 'poster', 'hoodie', 'tote-bag']
    design_data: DesignDataSchema
    use_ai_suggestions: bool = False


class DesignResponse(BaseModel):
    """Design response."""
    
    id: str
    user_id: str
    product_type: str
    design_data: dict
    status: str
    preview_url: str | None
    thumbnail_url: str | None
    created_at: datetime
    updated_at: datetime
    
    model_config = {"from_attributes": True}


class DesignListResponse(BaseModel):
    """Paginated design list response."""
    
    designs: list[DesignResponse]
    total: int
    skip: int
    limit: int
    has_more: bool
