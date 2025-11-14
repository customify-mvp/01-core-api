"""Storage repository interface (Domain layer)."""

from abc import ABC, abstractmethod
from typing import BinaryIO


class IStorageRepository(ABC):
    """
    Storage repository interface.
    
    Defines contract for file storage operations.
    Implementations can use S3, local filesystem, etc.
    """
    
    @abstractmethod
    def upload_design_preview(
        self,
        design_id: str,
        image_data: BinaryIO
    ) -> str:
        """
        Upload design preview image.
        
        Args:
            design_id: Design ID
            image_data: Image file-like object (bytes)
        
        Returns:
            str: Public URL of uploaded image
        
        Raises:
            Exception: If upload fails
        """
        pass
    
    @abstractmethod
    def upload_design_thumbnail(
        self,
        design_id: str,
        image_data: BinaryIO
    ) -> str:
        """
        Upload design thumbnail image (smaller version).
        
        Args:
            design_id: Design ID
            image_data: Thumbnail file-like object (bytes)
        
        Returns:
            str: Public URL of uploaded thumbnail
        
        Raises:
            Exception: If upload fails
        """
        pass
    
    @abstractmethod
    def delete_design_assets(self, design_id: str) -> bool:
        """
        Delete all assets for a design (preview + thumbnail).
        
        Args:
            design_id: Design ID
        
        Returns:
            bool: True if all assets deleted successfully
        """
        pass
