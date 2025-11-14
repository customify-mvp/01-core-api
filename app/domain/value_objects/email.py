"""
Email value object with validation.

Pure domain logic - no framework dependencies.
"""

from dataclasses import dataclass
import re


@dataclass(frozen=True)
class Email:
    """
    Email value object with built-in validation.
    
    Immutable (frozen=True) to ensure data integrity.
    
    Examples:
        >>> email = Email("user@example.com")
        >>> str(email)
        'user@example.com'
        >>> Email("invalid")  # Raises ValueError
    """
    
    value: str
    
    def __post_init__(self):
        """Validate email format on creation."""
        if not self._is_valid(self.value):
            raise ValueError(f"Invalid email format: {self.value}")
    
    @staticmethod
    def _is_valid(email: str) -> bool:
        """
        Validate email format using regex.
        
        Pattern requirements:
        - Local part: alphanumeric + ._%+-
        - @ symbol
        - Domain: alphanumeric + .- 
        - TLD: 2+ letters
        
        Args:
            email: Email string to validate
        
        Returns:
            bool: True if valid format, False otherwise
        """
        if not email or not isinstance(email, str):
            return False
        
        # Basic email regex (RFC 5322 simplified)
        pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        
        # Check length constraints
        if len(email) > 254:  # RFC 5321
            return False
        
        return bool(re.match(pattern, email))
    
    def __str__(self) -> str:
        """String representation (just the email value)."""
        return self.value
    
    def __repr__(self) -> str:
        """Developer-friendly representation."""
        return f"Email('{self.value}')"
    
    @property
    def local_part(self) -> str:
        """Get local part of email (before @)."""
        return self.value.split('@')[0]
    
    @property
    def domain(self) -> str:
        """Get domain part of email (after @)."""
        return self.value.split('@')[1]
    
    def masked(self) -> str:
        """
        Return masked email for display (privacy).
        
        Examples:
            user@example.com -> u***@example.com
            john.doe@company.io -> j*******@company.io
        """
        local = self.local_part
        domain = self.domain
        
        if len(local) <= 1:
            masked_local = local
        else:
            masked_local = local[0] + '*' * (len(local) - 1)
        
        return f"{masked_local}@{domain}"
