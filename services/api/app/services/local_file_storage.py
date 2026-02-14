"""Local file storage fallback for development without MinIO."""

import logging
import uuid
import os
from pathlib import Path
from typing import Optional

logger = logging.getLogger(__name__)


class LocalFileStorage:
    """Local filesystem storage for development/testing."""

    def __init__(self, base_path: str = "./uploads"):
        """
        Initialize local file storage.

        Args:
            base_path: Base directory for file storage
        """
        self.base_path = Path(base_path)
        self.base_path.mkdir(parents=True, exist_ok=True)
        logger.info(f"Initialized local file storage at: {self.base_path.absolute()}")

    def upload_file(self, user_id: str, file_content: bytes, file_name: str) -> str:
        """
        Save file to local filesystem.

        Args:
            user_id: User ID for folder organization
            file_content: Raw file bytes
            file_name: Original file name

        Returns:
            Local file path

        Raises:
            Exception: If upload fails
        """
        try:
            # Create user directory
            user_dir = self.base_path / "resumes" / str(user_id)
            user_dir.mkdir(parents=True, exist_ok=True)

            # Generate unique file name
            file_extension = file_name.split('.')[-1] if '.' in file_name else 'dat'
            unique_name = f"{uuid.uuid4()}.{file_extension}"
            file_path = user_dir / unique_name

            # Write file
            with open(file_path, 'wb') as f:
                f.write(file_content)

            # Return relative path
            relative_path = f"uploads/resumes/{user_id}/{unique_name}"
            logger.info(f"Saved file locally: {relative_path}")
            return relative_path

        except Exception as e:
            logger.error(f"Local file storage error: {e}")
            raise Exception(f"File upload failed: {str(e)}")

    def delete_file(self, file_path: str) -> bool:
        """
        Delete file from local filesystem.

        Args:
            file_path: Relative file path

        Returns:
            True if successful, False otherwise
        """
        try:
            full_path = self.base_path.parent / file_path
            if full_path.exists():
                full_path.unlink()
                logger.info(f"Deleted file: {file_path}")
                return True
            return False
        except Exception as e:
            logger.error(f"Error deleting file: {e}")
            return False

    def get_file(self, file_path: str) -> Optional[bytes]:
        """
        Read file from local filesystem.

        Args:
            file_path: Relative file path

        Returns:
            File content as bytes, or None if not found
        """
        try:
            full_path = self.base_path.parent / file_path
            if full_path.exists():
                with open(full_path, 'rb') as f:
                    return f.read()
            return None
        except Exception as e:
            logger.error(f"Error reading file: {e}")
            return None
