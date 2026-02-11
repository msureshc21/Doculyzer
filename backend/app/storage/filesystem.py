"""
Local filesystem storage abstraction.

This module provides a clean interface for file operations,
allowing easy migration to cloud storage in the future.
"""
import os
from pathlib import Path
from typing import Optional, BinaryIO
from app.core.config import settings


class FileStorage:
    """
    Local filesystem storage implementation.
    
    Provides abstraction for file storage operations,
    making it easy to swap implementations later.
    """
    
    def __init__(self, base_path: Optional[str] = None):
        """
        Initialize file storage.
        
        Args:
            base_path: Base directory for file storage. Defaults to settings.UPLOAD_DIR
        """
        self.base_path = Path(base_path or settings.UPLOAD_DIR)
        self.base_path.mkdir(parents=True, exist_ok=True)
    
    def save(self, file_content: bytes, file_path: str) -> str:
        """
        Save file content to storage.
        
        Args:
            file_content: Binary file content
            file_path: Relative path within storage directory
            
        Returns:
            str: Full path to saved file
        """
        full_path = self.base_path / file_path
        full_path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(full_path, "wb") as f:
            f.write(file_content)
        
        return str(full_path)
    
    def read(self, file_path: str) -> bytes:
        """
        Read file content from storage.
        
        Args:
            file_path: Relative path within storage directory
            
        Returns:
            bytes: File content
            
        Raises:
            FileNotFoundError: If file doesn't exist
        """
        full_path = self.base_path / file_path
        if not full_path.exists():
            raise FileNotFoundError(f"File not found: {file_path}")
        
        with open(full_path, "rb") as f:
            return f.read()
    
    def delete(self, file_path: str) -> bool:
        """
        Delete file from storage.
        
        Args:
            file_path: Relative path within storage directory
            
        Returns:
            bool: True if file was deleted, False if it didn't exist
        """
        full_path = self.base_path / file_path
        if full_path.exists():
            full_path.unlink()
            return True
        return False
    
    def exists(self, file_path: str) -> bool:
        """
        Check if file exists in storage.
        
        Args:
            file_path: Relative path within storage directory
            
        Returns:
            bool: True if file exists
        """
        return (self.base_path / file_path).exists()


# Global storage instance
storage = FileStorage()

