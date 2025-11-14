"""
HashedPassword value object with validation.

Pure domain logic - no framework dependencies.
"""

from dataclasses import dataclass


@dataclass(frozen=True)
class HashedPassword:
    """
    Hashed password value object with validation.
    
    Immutable (frozen=True) to ensure security.
    Stores only hashed passwords, never plaintext.
    
    Examples:
        >>> hashed = HashedPassword("$2b$12$...")  # bcrypt hash
        >>> str(hashed)
        '$2b$12$...'
        >>> HashedPassword("123")  # Raises ValueError (too short)
    """
    
    value: str
    
    def __post_init__(self):
        """Validate hash format on creation."""
        if not self._is_valid_hash(self.value):
            raise ValueError("Invalid password hash format")
    
    @staticmethod
    def _is_valid_hash(hash_value: str) -> bool:
        """
        Validate password hash format.
        
        Requirements:
        - Must be a string
        - Minimum length 20 chars (bcrypt hashes are 60+ chars)
        - Should start with hash algorithm identifier
        
        Args:
            hash_value: Hash string to validate
        
        Returns:
            bool: True if valid hash format, False otherwise
        """
        if not hash_value or not isinstance(hash_value, str):
            return False
        
        # Minimum length check (bcrypt: 60, argon2: 90+)
        if len(hash_value) < 20:
            return False
        
        # Check for common hash algorithm prefixes
        valid_prefixes = (
            '$2a$',  # bcrypt (old)
            '$2b$',  # bcrypt (current)
            '$2y$',  # bcrypt (PHP)
            '$argon2',  # argon2
            'pbkdf2:',  # PBKDF2
            '$scrypt$',  # scrypt
        )
        
        # Allow any hash that looks valid (starts with prefix)
        has_valid_prefix = any(
            hash_value.startswith(prefix) for prefix in valid_prefixes
        )
        
        # If no recognized prefix, just check length (permissive)
        return has_valid_prefix or len(hash_value) >= 60
    
    def __str__(self) -> str:
        """String representation (the hash value)."""
        return self.value
    
    def __repr__(self) -> str:
        """Developer-friendly representation (masked)."""
        # Don't expose full hash in repr
        preview = self.value[:12] + '...' if len(self.value) > 12 else self.value
        return f"HashedPassword('{preview}')"
    
    def masked(self) -> str:
        """
        Return masked hash for logging (security).
        
        Examples:
            $2b$12$abc123... -> $2b$12$***...
        """
        if len(self.value) <= 10:
            return '***'
        
        # Show algorithm and cost, hide the actual hash
        parts = self.value.split('$')
        if len(parts) >= 3:
            return f"${parts[1]}${parts[2]}$***"
        
        return self.value[:10] + '***'
    
    @property
    def algorithm(self) -> str:
        """
        Extract hash algorithm from hash string.
        
        Returns:
            str: Algorithm name (bcrypt, argon2, etc.)
        """
        if self.value.startswith('$2'):
            return 'bcrypt'
        elif self.value.startswith('$argon2'):
            return 'argon2'
        elif self.value.startswith('pbkdf2:'):
            return 'pbkdf2'
        elif self.value.startswith('$scrypt$'):
            return 'scrypt'
        else:
            return 'unknown'
