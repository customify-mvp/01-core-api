"""
User converter - Convert between UserModel (SQLAlchemy) and User entity (Domain).

This keeps the domain layer clean from ORM dependencies.
"""

from app.domain.entities.user import User
from app.infrastructure.database.models.user_model import UserModel


def to_entity(model: UserModel) -> User:
    """
    Convert UserModel (SQLAlchemy) to User entity (Domain).
    
    Args:
        model: SQLAlchemy UserModel instance
        
    Returns:
        Domain User entity
        
    Example:
        >>> model = await session.get(UserModel, user_id)
        >>> user = user_converter.to_entity(model)
        >>> user.email
        'test@example.com'
    """
    return User(
        id=model.id,
        email=model.email,
        password_hash=model.password_hash,
        full_name=model.full_name,
        avatar_url=model.avatar_url,
        is_active=model.is_active,
        is_verified=model.is_verified,
        is_deleted=model.is_deleted,
        created_at=model.created_at,
        updated_at=model.updated_at,
        last_login=model.last_login,
    )


def to_model(entity: User, model: UserModel = None) -> UserModel:
    """
    Convert User entity (Domain) to UserModel (SQLAlchemy).
    
    If model is provided (update scenario), updates existing model.
    If not provided (create scenario), creates new model instance.
    
    Args:
        entity: Domain User entity
        model: Existing UserModel to update (optional)
        
    Returns:
        SQLAlchemy UserModel instance
        
    Example:
        # Create new
        >>> user = User.create(...)
        >>> model = user_converter.to_model(user)
        >>> session.add(model)
        
        # Update existing
        >>> user.full_name = "New Name"
        >>> model = user_converter.to_model(user, existing_model)
        >>> await session.flush()
    """
    if model is None:
        model = UserModel()
    
    model.id = entity.id
    model.email = entity.email
    model.password_hash = entity.password_hash
    model.full_name = entity.full_name
    model.avatar_url = entity.avatar_url
    model.is_active = entity.is_active
    model.is_verified = entity.is_verified
    model.is_deleted = entity.is_deleted
    model.created_at = entity.created_at
    model.updated_at = entity.updated_at
    model.last_login = entity.last_login
    
    return model
