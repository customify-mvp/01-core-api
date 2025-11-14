"""
Design domain entity (pure business logic).

NO framework dependencies - pure Python only.
"""

from dataclasses import dataclass
from datetime import datetime
from typing import Optional
from enum import Enum
import re


class DesignStatus(Enum):
    """Design status values."""
    DRAFT = "draft"
    RENDERING = "rendering"
    PUBLISHED = "published"
    FAILED = "failed"


class ProductType(Enum):
    """Supported product types."""
    T_SHIRT = "t-shirt"
    MUG = "mug"
    POSTER = "poster"
    HOODIE = "hoodie"
    TOTE_BAG = "tote-bag"


@dataclass
class Design:
    """
    Design domain entity representing a user-created design.
    
    This is pure business logic with NO external dependencies.
    NO SQLAlchemy, NO Pydantic, NO FastAPI.
    """
    
    id: str
    user_id: str
    product_type: str
    design_data: dict
    status: DesignStatus
    preview_url: Optional[str]
    thumbnail_url: Optional[str]
    is_deleted: bool
    created_at: datetime
    updated_at: datetime
    
    @staticmethod
    def create(
        user_id: str,
        product_type: str,
        design_data: dict
    ) -> "Design":
        """
        Factory method to create a new design.
        
        Args:
            user_id: User ID who owns this design
            product_type: Type of product (t-shirt, mug, etc.)
            design_data: Design configuration (text, font, color, etc.)
            
        Returns:
            New Design instance with defaults
            
        Raises:
            ValueError: If product_type or design_data is invalid
        """
        from uuid import uuid4
        
        # Validate product type
        valid_types = [pt.value for pt in ProductType]
        if product_type not in valid_types:
            raise ValueError(
                f"Invalid product_type: {product_type}. "
                f"Must be one of: {', '.join(valid_types)}"
            )
        
        # Validate design_data has required fields
        required_fields = ["text", "font", "color"]
        missing = [field for field in required_fields if field not in design_data]
        if missing:
            raise ValueError(f"Missing required fields in design_data: {', '.join(missing)}")
        
        now = datetime.utcnow()
        
        design = Design(
            id=str(uuid4()),
            user_id=user_id,
            product_type=product_type,
            design_data=design_data,
            status=DesignStatus.DRAFT,
            preview_url=None,
            thumbnail_url=None,
            is_deleted=False,
            created_at=now,
            updated_at=now
        )
        
        # Validate the design
        design.validate()
        
        return design
    
    def validate(self) -> None:
        """
        Validate design business rules.
        
        Raises:
            ValueError: If any validation rule fails
        """
        # Rule 1: Check required fields exist
        required_fields = ['text', 'font', 'color']
        for field in required_fields:
            if field not in self.design_data:
                raise ValueError(f"Missing required field: {field}")
        
        # Rule 2: Text validation
        text = self.design_data.get("text", "")
        
        # Text must not be empty
        if not text or not text.strip():
            raise ValueError("Text cannot be empty")
        
        # Text must not exceed 100 characters
        if len(text) > 100:
            raise ValueError(f"Text too long (max 100 chars): {len(text)}")
        
        # Rule 3: Color validation - must be valid hex format (#RRGGBB)
        color = self.design_data.get("color", "")
        if not color.startswith('#') or len(color) != 7:
            raise ValueError(f"Invalid color format (expected #RRGGBB): {color}")
        
        # Verify it's valid hex
        if not re.match(r'^#[0-9A-Fa-f]{6}$', color):
            raise ValueError(f"Invalid hex color: {color}")
        
        # Rule 4: Font validation - must be in allowed list
        allowed_fonts = [
            'Bebas-Bold', 
            'Montserrat-Regular', 
            'Montserrat-Bold',
            'Pacifico-Regular', 
            'Roboto-Regular'
        ]
        font = self.design_data.get("font", "")
        
        if not font or not font.strip():
            raise ValueError("Font cannot be empty")
        
        if font not in allowed_fonts:
            raise ValueError(
                f"Invalid font: {font}. Allowed fonts: {', '.join(allowed_fonts)}"
            )
        
        # Rule 5: If fontSize provided, must be between 8 and 144
        if "fontSize" in self.design_data:
            font_size = self.design_data["fontSize"]
            if not isinstance(font_size, (int, float)):
                raise ValueError(f"fontSize must be a number, got {type(font_size).__name__}")
            if font_size < 8 or font_size > 144:
                raise ValueError(f"fontSize must be between 8 and 144, got {font_size}")
    
    def mark_rendering(self) -> None:
        """
        Mark design as being rendered.
        
        Raises:
            ValueError: If design is not in DRAFT status
        """
        if self.status != DesignStatus.DRAFT:
            raise ValueError(
                f"Can only render DRAFT designs. Current status: {self.status.value}"
            )
        
        self.status = DesignStatus.RENDERING
        self.updated_at = datetime.utcnow()
    
    def mark_published(self, preview_url: str, thumbnail_url: Optional[str] = None) -> None:
        """
        Mark design as published with preview URLs.
        
        Args:
            preview_url: URL to full preview image
            thumbnail_url: URL to thumbnail (optional)
            
        Raises:
            ValueError: If design is not in RENDERING status
        """
        if self.status != DesignStatus.RENDERING:
            raise ValueError(
                f"Can only publish RENDERING designs. Current status: {self.status.value}"
            )
        
        if not preview_url or not preview_url.strip():
            raise ValueError("preview_url cannot be empty")
        
        self.status = DesignStatus.PUBLISHED
        self.preview_url = preview_url
        self.thumbnail_url = thumbnail_url
        self.updated_at = datetime.utcnow()
    
    def mark_failed(self, error_message: Optional[str] = None) -> None:
        """
        Mark design rendering as failed.
        
        Args:
            error_message: Optional error message (stored in design_data)
            
        Raises:
            ValueError: If design is not in RENDERING status
        """
        if self.status != DesignStatus.RENDERING:
            raise ValueError(
                f"Can only mark RENDERING designs as failed. Current status: {self.status.value}"
            )
        
        self.status = DesignStatus.FAILED
        
        if error_message:
            self.design_data["error_message"] = error_message
        
        self.updated_at = datetime.utcnow()
    
    def update_data(self, new_design_data: dict) -> None:
        """
        Update design data (only allowed for DRAFT or FAILED designs).
        
        Args:
            new_design_data: New design configuration
            
        Raises:
            ValueError: If design is RENDERING or PUBLISHED, or validation fails
        """
        if self.status in [DesignStatus.RENDERING, DesignStatus.PUBLISHED]:
            raise ValueError(
                f"Cannot update {self.status.value} designs. "
                f"Only DRAFT or FAILED designs can be updated."
            )
        
        # Validate required fields
        required_fields = ["text", "font", "color"]
        missing = [field for field in required_fields if field not in new_design_data]
        if missing:
            raise ValueError(f"Missing required fields: {', '.join(missing)}")
        
        # Update data and validate
        old_data = self.design_data
        self.design_data = new_design_data
        
        try:
            self.validate()
        except ValueError as e:
            # Rollback on validation failure
            self.design_data = old_data
            raise e
        
        # Reset to DRAFT if was FAILED
        if self.status == DesignStatus.FAILED:
            self.status = DesignStatus.DRAFT
            self.preview_url = None
            self.thumbnail_url = None
        
        self.updated_at = datetime.utcnow()
    
    def soft_delete(self) -> None:
        """
        Soft delete the design.
        
        Sets is_deleted to True.
        """
        self.is_deleted = True
        self.updated_at = datetime.utcnow()
    
    def restore(self) -> None:
        """
        Restore a soft-deleted design.
        
        Raises:
            ValueError: If design is not deleted
        """
        if not self.is_deleted:
            raise ValueError("Design is not deleted")
        
        self.is_deleted = False
        self.updated_at = datetime.utcnow()
