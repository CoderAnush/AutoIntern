"""MinIO S3-compatible object storage service."""

import logging
import uuid
from typing import Optional

logger = logging.getLogger(__name__)


class MinIOStorage:
    """MinIO client for file storage."""

    def __init__(self, endpoint: str, access_key: str, secret_key: str, bucket_name: str = "resumes"):
        """
        Initialize MinIO client.

        Args:
            endpoint: MinIO server endpoint (e.g., "localhost:9000")
            access_key: MinIO access key
            secret_key: MinIO secret key
            bucket_name: S3 bucket name for resumes
        """
        try:
            from minio import Minio
            from minio.error import S3Error
        except ImportError:
            raise ImportError("MinIO client not installed. Install with: pip install minio")

        self.minio = Minio(endpoint, access_key=access_key, secret_key=secret_key, secure=False)
        self.bucket_name = bucket_name
        self.S3Error = S3Error

        # Ensure bucket exists
        self._ensure_bucket_exists()

    def _ensure_bucket_exists(self):
        """Create bucket if it doesn't exist."""
        try:
            if not self.minio.bucket_exists(self.bucket_name):
                self.minio.make_bucket(self.bucket_name)
                logger.info(f"Created MinIO bucket: {self.bucket_name}")
        except Exception as e:
            logger.error(f"Error ensuring bucket exists: {e}")
            raise

    def upload_file(self, user_id: str, file_content: bytes, file_name: str) -> str:
        """
        Upload file to MinIO.

        Args:
            user_id: User ID for folder organization
            file_content: Raw file bytes
            file_name: Original file name

        Returns:
            S3 URL of uploaded file

        Raises:
            Exception: If upload fails
        """
        try:
            from io import BytesIO

            # Generate unique object name
            file_extension = file_name.split('.')[-1] if '.' in file_name else 'dat'
            unique_name = f"{uuid.uuid4()}.{file_extension}"
            object_name = f"resumes/{user_id}/{unique_name}"

            # Upload to MinIO
            file_stream = BytesIO(file_content)
            self.minio.put_object(
                self.bucket_name,
                object_name,
                file_stream,
                len(file_content),
                content_type=self._get_content_type(file_extension)
            )

            # Return the S3 URL
            url = f"http://minio:9000/{self.bucket_name}/{object_name}"
            logger.info(f"Uploaded file to MinIO: {object_name}")
            return url

        except self.S3Error as e:
            logger.error(f"MinIO upload error: {e}")
            raise Exception(f"File upload failed: {str(e)}")
        except Exception as e:
            logger.error(f"Unexpected error during upload: {e}")
            raise

    def delete_file(self, object_name: str) -> bool:
        """
        Delete file from MinIO.

        Args:
            object_name: Full object path (e.g., "resumes/user123/file.pdf")

        Returns:
            True if successful, False otherwise
        """
        try:
            self.minio.remove_object(self.bucket_name, object_name)
            logger.info(f"Deleted file from MinIO: {object_name}")
            return True
        except self.S3Error as e:
            logger.error(f"MinIO delete error: {e}")
            return False
        except Exception as e:
            logger.error(f"Unexpected error during delete: {e}")
            return False

    @staticmethod
    def _get_content_type(file_extension: str) -> str:
        """Get MIME type for file extension."""
        content_types = {
            'pdf': 'application/pdf',
            'docx': 'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
            'doc': 'application/msword',
            'txt': 'text/plain',
            'html': 'text/html',
            'json': 'application/json'
        }
        return content_types.get(file_extension.lower(), 'application/octet-stream')
