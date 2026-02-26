"""Storage utilities for file operations."""

import hashlib
from pathlib import Path
from typing import Optional, List
import aiofiles


class StorageManager:
    """
    Manages file storage operations.
    
    Handles:
    - File saving with deduplication
    - Directory management
    - File hashing for deduplication
    """

    def __init__(self, base_dir: str):
        self.base_dir = Path(base_dir)

    def get_path(self, *parts: str) -> Path:
        """Get path within base directory."""
        path = self.base_dir / Path(*parts)
        path.parent.mkdir(parents=True, exist_ok=True)
        return path

    async def save_text(
        self, content: str, path: Path, overwrite: bool = True
    ) -> Path:
        """Save text content to file."""
        if not overwrite and path.exists():
            return path

        path.parent.mkdir(parents=True, exist_ok=True)
        async with aiofiles.open(path, "w", encoding="utf-8") as f:
            await f.write(content)

        return path

    async def save_binary(
        self, content: bytes, path: Path, overwrite: bool = True
    ) -> Path:
        """Save binary content to file."""
        if not overwrite and path.exists():
            return path

        path.parent.mkdir(parents=True, exist_ok=True)
        async with aiofiles.open(path, "wb") as f:
            await f.write(content)

        return path

    async def read_text(self, path: Path) -> Optional[str]:
        """Read text content from file."""
        if not path.exists():
            return None

        async with aiofiles.open(path, "r", encoding="utf-8") as f:
            return await f.read()

    async def read_binary(self, path: Path) -> Optional[bytes]:
        """Read binary content from file."""
        if not path.exists():
            return None

        async with aiofiles.open(path, "rb") as f:
            return await f.read()

    def compute_hash(self, content: bytes) -> str:
        """Compute SHA256 hash of content."""
        return hashlib.sha256(content).hexdigest()

    async def save_deduplicated(
        self,
        content: bytes,
        base_path: Path,
        extension: str = ".bin",
    ) -> Path:
        """
        Save file with deduplication based on content hash.
        
        Returns the path where file was/will be saved.
        """
        content_hash = self.compute_hash(content)
        hash_dir = base_path.parent / "by_hash"
        hash_dir.mkdir(parents=True, exist_ok=True)

        hashed_path = hash_dir / f"{content_hash}{extension}"

        if not hashed_path.exists():
            async with aiofiles.open(hashed_path, "wb") as f:
                await f.write(content)

        # Also save to original path (could be symlink in future)
        path.parent.mkdir(parents=True, exist_ok=True)
        async with aiofiles.open(path, "wb") as f:
            await f.write(content)

        return path

    def file_exists(self, path: Path) -> bool:
        """Check if file exists."""
        return path.exists()

    def get_file_size(self, path: Path) -> int:
        """Get file size in bytes."""
        if not path.exists():
            return 0
        return path.stat().st_size

    def list_files(
        self,
        directory: Path,
        pattern: str = "*",
        recursive: bool = False,
    ) -> List[Path]:
        """List files in directory."""
        if not directory.exists():
            return []

        if recursive:
            return list(directory.rglob(pattern))
        return list(directory.glob(pattern))

    def delete_file(self, path: Path) -> bool:
        """Delete file. Returns True if deleted."""
        if path.exists():
            path.unlink()
            return True
        return False

    def get_relative_path(self, path: Path) -> str:
        """Get path relative to base directory."""
        try:
            return str(path.relative_to(self.base_dir))
        except ValueError:
            return str(path)
