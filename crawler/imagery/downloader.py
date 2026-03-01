"""Image downloader with retry and validation."""

import asyncio
import hashlib
import logging
from dataclasses import dataclass
from pathlib import Path
from typing import List, Optional, Tuple
from urllib.parse import urlparse

import httpx

logger = logging.getLogger(__name__)


@dataclass
class DownloadResult:
    """Result of an image download."""

    url: str
    success: bool
    local_path: Optional[Path] = None
    filename: Optional[str] = None
    content_type: Optional[str] = None
    size_bytes: int = 0
    error: Optional[str] = None
    checksum: Optional[str] = None


class ImageDownloader:
    """
    Downloads images with retry logic and validation.

    Features:
    - Concurrent downloads
    - Content-type validation
    - Size limits
    - Checksum generation
    - Retry with backoff
    """

    VALID_CONTENT_TYPES = [
        "image/jpeg",
        "image/png",
        "image/gif",
        "image/webp",
        "image/svg+xml",
    ]

    EXTENSION_MAP = {
        "image/jpeg": ".jpg",
        "image/png": ".png",
        "image/gif": ".gif",
        "image/webp": ".webp",
        "image/svg+xml": ".svg",
    }

    def __init__(
        self,
        output_dir: Path,
        max_concurrent: int = 5,
        max_size_mb: float = 10.0,
        timeout: float = 30.0,
        max_retries: int = 3,
    ):
        self.output_dir = Path(output_dir)
        self.max_concurrent = max_concurrent
        self.max_size_bytes = int(max_size_mb * 1024 * 1024)
        self.timeout = timeout
        self.max_retries = max_retries
        self._semaphore = asyncio.Semaphore(max_concurrent)

    async def download_all(
        self,
        urls: List[str],
        prefix: str = "",
    ) -> List[DownloadResult]:
        """
        Download multiple images concurrently.

        Args:
            urls: List of image URLs
            prefix: Prefix for output filenames

        Returns:
            List of download results
        """
        self.output_dir.mkdir(parents=True, exist_ok=True)

        tasks = [
            self._download_with_semaphore(url, prefix, idx)
            for idx, url in enumerate(urls)
        ]

        return await asyncio.gather(*tasks)

    async def _download_with_semaphore(
        self,
        url: str,
        prefix: str,
        index: int,
    ) -> DownloadResult:
        """Download with concurrency limit."""
        async with self._semaphore:
            return await self.download_single(url, prefix, index)

    async def download_single(
        self,
        url: str,
        prefix: str = "",
        index: int = 0,
    ) -> DownloadResult:
        """
        Download a single image with retry.

        Args:
            url: Image URL
            prefix: Filename prefix
            index: Image index for naming

        Returns:
            Download result
        """
        last_error = None

        for attempt in range(self.max_retries):
            try:
                return await self._do_download(url, prefix, index)
            except httpx.TimeoutException as e:
                last_error = f"Timeout: {e}"
                logger.warning(f"Timeout downloading {url}, attempt {attempt + 1}")
            except httpx.HTTPStatusError as e:
                last_error = f"HTTP {e.response.status_code}"
                if e.response.status_code in (404, 403, 401):
                    # Don't retry client errors
                    break
                logger.warning(f"HTTP error {url}, attempt {attempt + 1}: {e}")
            except Exception as e:
                last_error = str(e)
                logger.warning(f"Error downloading {url}, attempt {attempt + 1}: {e}")

            if attempt < self.max_retries - 1:
                await asyncio.sleep(2 ** attempt)  # Exponential backoff

        return DownloadResult(
            url=url,
            success=False,
            error=last_error,
        )

    async def _do_download(
        self,
        url: str,
        prefix: str,
        index: int,
    ) -> DownloadResult:
        """Perform the actual download."""
        async with httpx.AsyncClient(timeout=self.timeout, follow_redirects=True) as client:
            response = await client.get(url)
            response.raise_for_status()

            content_type = response.headers.get("content-type", "").split(";")[0].strip()

            # Validate content type
            if content_type not in self.VALID_CONTENT_TYPES:
                return DownloadResult(
                    url=url,
                    success=False,
                    error=f"Invalid content type: {content_type}",
                )

            content = response.content

            # Check size
            if len(content) > self.max_size_bytes:
                return DownloadResult(
                    url=url,
                    success=False,
                    error=f"Image too large: {len(content)} bytes",
                )

            # Generate filename
            extension = self.EXTENSION_MAP.get(content_type, ".jpg")
            filename = f"{prefix}_{index:03d}{extension}" if prefix else f"image_{index:03d}{extension}"
            local_path = self.output_dir / filename

            # Calculate checksum
            checksum = hashlib.md5(content).hexdigest()

            # Save file
            local_path.write_bytes(content)

            logger.debug(f"Downloaded {url} -> {local_path}")

            return DownloadResult(
                url=url,
                success=True,
                local_path=local_path,
                filename=filename,
                content_type=content_type,
                size_bytes=len(content),
                checksum=checksum,
            )

    def get_filename_from_url(self, url: str) -> str:
        """Extract filename from URL."""
        parsed = urlparse(url)
        path = parsed.path
        if path:
            return Path(path).name
        return "image"

    async def validate_url(self, url: str) -> Tuple[bool, Optional[str]]:
        """
        Validate image URL without downloading.

        Returns:
            Tuple of (is_valid, content_type or error)
        """
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.head(url, follow_redirects=True)
                response.raise_for_status()

                content_type = response.headers.get("content-type", "").split(";")[0].strip()

                if content_type in self.VALID_CONTENT_TYPES:
                    return True, content_type
                else:
                    return False, f"Invalid content type: {content_type}"

        except Exception as e:
            return False, str(e)
