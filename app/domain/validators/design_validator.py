"""
Design validators using Strategy Pattern.

Product-specific validation logic separated by product type.
Easily extensible for new product types.
"""

from typing import Protocol
import re


class DesignValidator(Protocol):
    """
    Protocol (interface) for design validators.
    
    Each product type can have its own validator implementation
    with specific rules and constraints.
    """
    
    def validate(self, design_data: dict, product_type: str) -> None:
        """
        Validate design data for a specific product type.
        
        Args:
            design_data: Design configuration (text, font, color, etc.)
            product_type: Product type (t-shirt, mug, etc.)
        
        Raises:
            ValueError: If validation fails with descriptive message
        """
        ...


class TShirtValidator:
    """
    Validator for t-shirt designs.
    
    T-shirts have limited print area, so text length is constrained.
    Position is important for proper placement.
    """
    
    MAX_TEXT_LENGTH = 50  # T-shirts have less space
    
    def validate(self, design_data: dict, product_type: str) -> None:
        """Validate t-shirt design data."""
        # Required fields
        required = ['text', 'font', 'color']
        for field in required:
            if field not in design_data:
                raise ValueError(f"Missing required field for t-shirt: {field}")
        
        # Text validation
        text = design_data.get('text', '')
        if not text or not text.strip():
            raise ValueError("Text cannot be empty")
        
        if len(text) > self.MAX_TEXT_LENGTH:
            raise ValueError(
                f"Text too long for t-shirt. "
                f"Maximum {self.MAX_TEXT_LENGTH} characters, got {len(text)}"
            )
        
        # Color validation
        self._validate_color(design_data.get('color'))
        
        # Font validation
        self._validate_font(design_data.get('font'))
        
        # Font size validation (if provided)
        if 'fontSize' in design_data:
            self._validate_font_size(design_data['fontSize'], min_size=12, max_size=72)
    
    def _validate_color(self, color: str) -> None:
        """Validate hex color format."""
        if not color:
            raise ValueError("Color is required")
        
        if not color.startswith('#') or len(color) != 7:
            raise ValueError(f"Invalid color format (expected #RRGGBB): {color}")
        
        if not re.match(r'^#[0-9A-Fa-f]{6}$', color):
            raise ValueError(f"Invalid hex color: {color}")
    
    def _validate_font(self, font: str) -> None:
        """Validate font name."""
        allowed_fonts = [
            'Bebas-Bold',
            'Montserrat-Regular',
            'Montserrat-Bold',
            'Pacifico-Regular',
            'Roboto-Regular',
        ]
        
        if not font:
            raise ValueError("Font is required")
        
        if font not in allowed_fonts:
            raise ValueError(
                f"Invalid font: {font}. "
                f"Allowed fonts: {', '.join(allowed_fonts)}"
            )
    
    def _validate_font_size(self, font_size: int, min_size: int, max_size: int) -> None:
        """Validate font size range."""
        if not isinstance(font_size, (int, float)):
            raise ValueError(f"fontSize must be a number, got {type(font_size).__name__}")
        
        if font_size < min_size or font_size > max_size:
            raise ValueError(
                f"fontSize must be between {min_size} and {max_size}, "
                f"got {font_size}"
            )


class MugValidator:
    """
    Validator for mug designs.
    
    Mugs have wrap-around design area, allowing longer text.
    """
    
    MAX_TEXT_LENGTH = 100  # Mugs can have more text
    
    def validate(self, design_data: dict, product_type: str) -> None:
        """Validate mug design data."""
        # Required fields (mugs don't need position)
        required = ['text', 'font', 'color']
        for field in required:
            if field not in design_data:
                raise ValueError(f"Missing required field for mug: {field}")
        
        # Text validation
        text = design_data.get('text', '')
        if not text or not text.strip():
            raise ValueError("Text cannot be empty")
        
        if len(text) > self.MAX_TEXT_LENGTH:
            raise ValueError(
                f"Text too long for mug. "
                f"Maximum {self.MAX_TEXT_LENGTH} characters, got {len(text)}"
            )
        
        # Reuse t-shirt validators for common fields
        t_shirt_validator = TShirtValidator()
        t_shirt_validator._validate_color(design_data.get('color'))
        t_shirt_validator._validate_font(design_data.get('font'))
        
        # Font size validation (mugs can have larger text)
        if 'fontSize' in design_data:
            t_shirt_validator._validate_font_size(
                design_data['fontSize'],
                min_size=8,
                max_size=144
            )


class PosterValidator:
    """
    Validator for poster designs.
    
    Posters have large print area, very flexible.
    """
    
    MAX_TEXT_LENGTH = 200  # Posters can have lots of text
    
    def validate(self, design_data: dict, product_type: str) -> None:
        """Validate poster design data."""
        required = ['text', 'font', 'color']
        for field in required:
            if field not in design_data:
                raise ValueError(f"Missing required field for poster: {field}")
        
        # Text validation
        text = design_data.get('text', '')
        if not text or not text.strip():
            raise ValueError("Text cannot be empty")
        
        if len(text) > self.MAX_TEXT_LENGTH:
            raise ValueError(
                f"Text too long for poster. "
                f"Maximum {self.MAX_TEXT_LENGTH} characters, got {len(text)}"
            )
        
        # Reuse t-shirt validators
        t_shirt_validator = TShirtValidator()
        t_shirt_validator._validate_color(design_data.get('color'))
        t_shirt_validator._validate_font(design_data.get('font'))
        
        if 'fontSize' in design_data:
            t_shirt_validator._validate_font_size(
                design_data['fontSize'],
                min_size=8,
                max_size=200  # Posters can have very large text
            )


# ============================================================
# Validator Registry (Factory Pattern)
# ============================================================

VALIDATORS: dict[str, DesignValidator] = {
    't-shirt': TShirtValidator(),
    'mug': MugValidator(),
    'poster': PosterValidator(),
    'hoodie': TShirtValidator(),  # Reuse t-shirt rules
    'tote-bag': TShirtValidator(),  # Reuse t-shirt rules
}


def get_validator(product_type: str) -> DesignValidator:
    """
    Get appropriate validator for product type.
    
    Args:
        product_type: Product type (t-shirt, mug, poster, etc.)
    
    Returns:
        DesignValidator: Validator instance for that product type
    
    Raises:
        ValueError: If product type is unknown
    
    Examples:
        >>> validator = get_validator('t-shirt')
        >>> validator.validate({'text': 'Hello', 'font': 'Bebas-Bold', 'color': '#FF0000'}, 't-shirt')
    """
    validator = VALIDATORS.get(product_type)
    
    if validator is None:
        valid_types = ', '.join(VALIDATORS.keys())
        raise ValueError(
            f"Unknown product type: {product_type}. "
            f"Valid types: {valid_types}"
        )
    
    return validator


def register_validator(product_type: str, validator: DesignValidator) -> None:
    """
    Register a custom validator for a product type.
    
    Useful for extending the system with new product types
    without modifying core code.
    
    Args:
        product_type: Product type identifier
        validator: Validator instance implementing DesignValidator protocol
    
    Examples:
        >>> class CanvasValidator:
        ...     def validate(self, design_data, product_type):
        ...         # Custom validation logic
        ...         pass
        >>> 
        >>> register_validator('canvas', CanvasValidator())
    """
    VALIDATORS[product_type] = validator
