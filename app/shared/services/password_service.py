"""
Password hashing and verification service.

This service handles all password-related operations to keep
domain entities clean and framework-independent.

Uses passlib with bcrypt for secure password hashing.
"""

from passlib.context import CryptContext

# Configure password context
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def hash_password(password: str) -> str:
    """
    Hash a plain password using bcrypt.
    
    Args:
        password: Plain text password
        
    Returns:
        Hashed password string
        
    Example:
        >>> hashed = hash_password("MySecurePassword123")
        >>> hashed.startswith("$2b$")
        True
    """
    return pwd_context.hash(password)


def verify_password(plain_password: str, password_hash: str) -> bool:
    """
    Verify a plain password against a hashed password.
    
    Args:
        plain_password: Plain text password to verify
        password_hash: Previously hashed password
        
    Returns:
        True if password matches, False otherwise
        
    Example:
        >>> hashed = hash_password("MyPassword123")
        >>> verify_password("MyPassword123", hashed)
        True
        >>> verify_password("WrongPassword", hashed)
        False
    """
    return pwd_context.verify(plain_password, password_hash)


def needs_rehash(password_hash: str) -> bool:
    """
    Check if a password hash needs to be rehashed.
    
    Useful when upgrading bcrypt cost factor or changing algorithms.
    
    Args:
        password_hash: Previously hashed password
        
    Returns:
        True if hash should be updated, False otherwise
    """
    return pwd_context.needs_update(password_hash)
