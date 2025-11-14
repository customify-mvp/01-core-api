"""Local file storage for development (mock S3)."""

import os
from pathlib import Path
from typing import BinaryIO
import logging
from app.domain.repositories.storage_repository import IStorageRepository

logger = logging.getLogger(__name__)


class LocalStorageRepository(IStorageRepository):
    """
    Local filesystem storage (for development).
    
    Mimics S3 behavior but stores files locally.
    Use this when USE_LOCAL_STORAGE=True (development mode).
    """
    
    def __init__(self, base_path: str = "./storage"):
        """
        Initialize local storage with base directory.
        
        Args:
            base_path: Root directory for file storage (default: ./storage)
        """
        self.base_path = Path(base_path)
        self.base_path.mkdir(exist_ok=True)
        logger.info(f"Initialized local storage at: {self.base_path.absolute()}")
    
    def upload_design_preview(
        self,
        design_id: str,
        image_data: BinaryIO
    ) -> str:
        """
        Save preview to local filesystem.
        
        Path: {base_path}/designs/{design_id}/preview.png
        
        Args:
            design_id: Design ID
            image_data: Image file-like object
        
        Returns:
            str: Mock URL for local file
        """
        # Create design directory
        design_path = self.base_path / "designs" / design_id
        design_path.mkdir(parents=True, exist_ok=True)
        
        # Save file
        file_path = design_path / "preview.png"
        with open(file_path, 'wb') as f:
            f.write(image_data.read())
        
        # Return mock URL (static file serving)
        url = f"http://localhost:8000/static/designs/{design_id}/preview.png"
        logger.info(f"Saved preview locally: {file_path}")
        
        return url
    
    def upload_design_thumbnail(
        self,
        design_id: str,
        image_data: BinaryIO
    ) -> str:
        """
        Save thumbnail to local filesystem.
        
        Path: {base_path}/designs/{design_id}/thumbnail.png
        
        Args:
            design_id: Design ID
            image_data: Thumbnail file-like object
        
        Returns:
            str: Mock URL for local file
        """
        # Create design directory
        design_path = self.base_path / "designs" / design_id
        design_path.mkdir(parents=True, exist_ok=True)
        
        # Save file
        file_path = design_path / "thumbnail.png"
        with open(file_path, 'wb') as f:
            f.write(image_data.read())
        
        # Return mock URL
        url = f"http://localhost:8000/static/designs/{design_id}/thumbnail.png"
        logger.info(f"Saved thumbnail locally: {file_path}")
        
        return url
    
    def delete_design_assets(self, design_id: str) -> bool:
        """
        Delete local files for a design.
        
        Args:
            design_id: Design ID
        
        Returns:
            bool: True if all files deleted successfully
        """
        design_path = self.base_path / "designs" / design_id
        
        if not design_path.exists():
            logger.warning(f"Design directory not found: {design_path}")
            return False
        
        try:
            # Delete all files in design directory
            deleted_count = 0
            for file in design_path.glob("*"):
                file.unlink()
                deleted_count += 1
            
            # Remove directory
            design_path.rmdir()
            
            logger.info(f"Deleted {deleted_count} files for design: {design_id}")
            return True
        
        except Exception as e:
            logger.error(f"Failed to delete local assets for design {design_id}: {e}")
            return False
