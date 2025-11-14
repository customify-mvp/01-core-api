"""AWS S3 client for file storage."""

import boto3
from botocore.exceptions import ClientError
from typing import Optional, BinaryIO
import logging
from app.config import settings

logger = logging.getLogger(__name__)


class S3Client:
    """
    AWS S3 client wrapper.
    
    Handles file uploads, downloads, and URL generation for S3 storage.
    Thread-safe singleton for use in Celery workers.
    """
    
    def __init__(self):
        """Initialize S3 client with credentials from settings."""
        self.s3 = boto3.client(
            's3',
            region_name=settings.AWS_REGION,
            aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
            aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
        )
        self.bucket = settings.S3_BUCKET_NAME
        logger.info(f"Initialized S3 client for bucket: {self.bucket}")
    
    def upload_file(
        self,
        file_data: BinaryIO,
        key: str,
        content_type: str = "image/png",
        metadata: Optional[dict] = None
    ) -> str:
        """
        Upload file to S3.
        
        Args:
            file_data: File-like object (bytes)
            key: S3 object key (path/to/file.png)
            content_type: MIME type (default: image/png)
            metadata: Optional metadata dict (stored as S3 object metadata)
        
        Returns:
            str: Public URL of uploaded file
        
        Raises:
            Exception: If upload fails
        
        Example:
            >>> with open('image.png', 'rb') as f:
            >>>     url = s3_client.upload_file(f, 'designs/123/preview.png')
        """
        try:
            extra_args = {
                'ContentType': content_type,
            }
            
            # Add metadata if provided
            if metadata:
                extra_args['Metadata'] = metadata
            
            # Make public if configured
            if settings.S3_PUBLIC_BUCKET:
                extra_args['ACL'] = 'public-read'
            
            # Upload file
            self.s3.upload_fileobj(
                file_data,
                self.bucket,
                key,
                ExtraArgs=extra_args
            )
            
            # Generate URL
            url = self._get_public_url(key)
            
            logger.info(f"Uploaded file to S3: {key}")
            return url
        
        except ClientError as e:
            error_code = e.response.get('Error', {}).get('Code', 'Unknown')
            logger.error(f"Failed to upload file to S3: {error_code} - {e}")
            raise Exception(f"S3 upload failed: {error_code}")
        except Exception as e:
            logger.error(f"Unexpected error uploading to S3: {e}", exc_info=True)
            raise
    
    def upload_from_path(
        self,
        file_path: str,
        key: str,
        content_type: str = "image/png"
    ) -> str:
        """
        Upload file from local path to S3.
        
        Args:
            file_path: Local file path
            key: S3 object key
            content_type: MIME type
        
        Returns:
            str: Public URL of uploaded file
        
        Example:
            >>> url = s3_client.upload_from_path('./temp/image.png', 'designs/123/preview.png')
        """
        with open(file_path, 'rb') as f:
            return self.upload_file(f, key, content_type)
    
    def delete_file(self, key: str) -> bool:
        """
        Delete file from S3.
        
        Args:
            key: S3 object key
        
        Returns:
            bool: True if deleted successfully, False otherwise
        
        Example:
            >>> s3_client.delete_file('designs/123/preview.png')
        """
        try:
            self.s3.delete_object(Bucket=self.bucket, Key=key)
            logger.info(f"Deleted file from S3: {key}")
            return True
        except ClientError as e:
            error_code = e.response.get('Error', {}).get('Code', 'Unknown')
            logger.error(f"Failed to delete file from S3: {error_code} - {e}")
            return False
        except Exception as e:
            logger.error(f"Unexpected error deleting from S3: {e}")
            return False
    
    def get_signed_url(
        self,
        key: str,
        expiration: int = 3600
    ) -> str:
        """
        Generate pre-signed URL for private files.
        
        Use this for private buckets where direct URLs don't work.
        
        Args:
            key: S3 object key
            expiration: URL expiration in seconds (default: 1 hour)
        
        Returns:
            str: Pre-signed URL valid for specified duration
        
        Raises:
            ClientError: If URL generation fails
        
        Example:
            >>> url = s3_client.get_signed_url('private/file.pdf', expiration=300)
        """
        try:
            url = self.s3.generate_presigned_url(
                'get_object',
                Params={'Bucket': self.bucket, 'Key': key},
                ExpiresIn=expiration
            )
            logger.debug(f"Generated signed URL for {key} (expires in {expiration}s)")
            return url
        except ClientError as e:
            logger.error(f"Failed to generate signed URL: {e}")
            raise
    
    def _get_public_url(self, key: str) -> str:
        """
        Get public URL for object.
        
        Uses CloudFront if configured, otherwise S3 direct URL.
        
        Args:
            key: S3 object key
        
        Returns:
            str: Public URL
        """
        return f"{settings.s3_base_url}/{key}"
    
    def file_exists(self, key: str) -> bool:
        """
        Check if file exists in S3.
        
        Args:
            key: S3 object key
        
        Returns:
            bool: True if file exists, False otherwise
        
        Example:
            >>> if s3_client.file_exists('designs/123/preview.png'):
            >>>     print('File exists!')
        """
        try:
            self.s3.head_object(Bucket=self.bucket, Key=key)
            return True
        except ClientError as e:
            if e.response.get('Error', {}).get('Code') == '404':
                return False
            logger.error(f"Error checking file existence: {e}")
            return False


# Singleton instance
# Import this in workers/tasks to avoid re-creating client
s3_client = S3Client()
