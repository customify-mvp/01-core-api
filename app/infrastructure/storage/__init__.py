"""Storage module - Factory for storage repositories."""

from app.config import settings
from app.domain.repositories.storage_repository import IStorageRepository
from app.infrastructure.storage.local_storage import LocalStorageRepository
from app.infrastructure.storage.storage_repo_impl import StorageRepositoryImpl


def get_storage_repository() -> IStorageRepository:
    """
    Get storage repository instance.
    
    Returns local storage for development (USE_LOCAL_STORAGE=True)
    or S3 storage for production (USE_LOCAL_STORAGE=False).
    
    Returns:
        IStorageRepository: Storage repository instance
    
    Example:
        >>> storage = get_storage_repository()
        >>> url = storage.upload_design_preview(design_id, image_data)
    """
    if settings.USE_LOCAL_STORAGE:
        return LocalStorageRepository()
    return StorageRepositoryImpl()


__all__ = [
    "get_storage_repository",
    "IStorageRepository",
    "LocalStorageRepository",
    "StorageRepositoryImpl",
]
