"""Storage repository implementation using AWS S3."""

from typing import BinaryIO
import logging
from app.domain.repositories.storage_repository import IStorageRepository
from app.infrastructure.storage.s3_client import s3_client

logger = logging.getLogger(__name__)


class StorageRepositoryImpl(IStorageRepository):
    """
    S3 storage repository implementation.
    
    Implements IStorageRepository interface using AWS S3.
    Uses s3_client singleton for all operations.
    """
    
    def upload_design_preview(
        self,
        design_id: str,
        image_data: BinaryIO
    ) -> str:
        """
        Upload design preview to S3.
        
        File path: designs/{design_id}/preview.png
        
        Args:
            design_id: Design ID
            image_data: Image file-like object
        
        Returns:
            str: Public URL of uploaded preview
        """
        key = f"designs/{design_id}/preview.png"
        
        try:
            url = s3_client.upload_file(
                file_data=image_data,
                key=key,
                content_type="image/png",
                metadata={
                    "design_id": design_id,
                    "type": "preview"
                }
            )
            logger.info(f"Uploaded design preview: {design_id}")
            return url
        
        except Exception as e:
            logger.error(f"Failed to upload preview for design {design_id}: {e}")
            raise
    
    def upload_design_thumbnail(
        self,
        design_id: str,
        image_data: BinaryIO
    ) -> str:
        """
        Upload design thumbnail to S3.
        
        File path: designs/{design_id}/thumbnail.png
        
        Args:
            design_id: Design ID
            image_data: Thumbnail file-like object
        
        Returns:
            str: Public URL of uploaded thumbnail
        """
        key = f"designs/{design_id}/thumbnail.png"
        
        try:
            url = s3_client.upload_file(
                file_data=image_data,
                key=key,
                content_type="image/png",
                metadata={
                    "design_id": design_id,
                    "type": "thumbnail"
                }
            )
            logger.info(f"Uploaded design thumbnail: {design_id}")
            return url
        
        except Exception as e:
            logger.error(f"Failed to upload thumbnail for design {design_id}: {e}")
            raise
    
    def delete_design_assets(self, design_id: str) -> bool:
        """
        Delete all S3 assets for a design.
        
        Deletes:
        - designs/{design_id}/preview.png
        - designs/{design_id}/thumbnail.png
        
        Args:
            design_id: Design ID
        
        Returns:
            bool: True if all assets deleted successfully
        """
        try:
            preview_key = f"designs/{design_id}/preview.png"
            thumbnail_key = f"designs/{design_id}/thumbnail.png"
            
            preview_deleted = s3_client.delete_file(preview_key)
            thumbnail_deleted = s3_client.delete_file(thumbnail_key)
            
            if preview_deleted and thumbnail_deleted:
                logger.info(f"Deleted all assets for design: {design_id}")
                return True
            else:
                logger.warning(
                    f"Partial deletion for design {design_id}: "
                    f"preview={preview_deleted}, thumbnail={thumbnail_deleted}"
                )
                return False
        
        except Exception as e:
            logger.error(f"Failed to delete assets for design {design_id}: {e}")
            return False
