"""Imagery service - coordinates image extraction, downloading, and analysis."""

import logging
from dataclasses import dataclass, field
from pathlib import Path
from typing import List, Optional, Dict, Any

from crawler.config_loader import PlatformConfig
from crawler.parser.image_extractor import ImageExtractor
from crawler.models.external_links import ExternalLinks
from crawler.imagery.link_generator import LinkGenerator
from crawler.imagery.downloader import ImageDownloader, DownloadResult
from crawler.imagery.analyzer import ImageAnalyzer, AnalysisResult

logger = logging.getLogger(__name__)


@dataclass
class ImageryResult:
    """Complete imagery processing result."""

    task_id: str
    external_links: Optional[ExternalLinks] = None
    extracted_urls: List[str] = field(default_factory=list)
    downloaded: List[DownloadResult] = field(default_factory=list)
    analysis: List[AnalysisResult] = field(default_factory=list)
    errors: List[str] = field(default_factory=list)

    @property
    def success_count(self) -> int:
        """Count of successfully downloaded images."""
        return sum(1 for d in self.downloaded if d.success)

    @property
    def failed_count(self) -> int:
        """Count of failed downloads."""
        return sum(1 for d in self.downloaded if not d.success)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "task_id": self.task_id,
            "external_links": self.external_links.to_dict() if self.external_links else None,
            "extracted_urls": self.extracted_urls,
            "downloaded": [
                {
                    "url": d.url,
                    "success": d.success,
                    "filename": d.filename,
                    "size_bytes": d.size_bytes,
                    "checksum": d.checksum,
                    "error": d.error,
                }
                for d in self.downloaded
            ],
            "analysis": [a.to_dict() for a in self.analysis],
            "success_count": self.success_count,
            "failed_count": self.failed_count,
            "errors": self.errors,
        }


class ImageryService:
    """
    Coordinates imagery operations for property data.

    Features:
    - Extract image URLs from HTML
    - Generate external map links
    - Download property images
    - Analyze images (YOLOv8 placeholder)
    """

    def __init__(
        self,
        output_dir: Path,
        config: Optional[PlatformConfig] = None,
        download_images: bool = True,
        analyze_images: bool = False,
        max_images: int = 20,
    ):
        self.output_dir = Path(output_dir)
        self.config = config
        self.download_images = download_images
        self.analyze_images = analyze_images
        self.max_images = max_images

        self.extractor = ImageExtractor()
        self.link_generator = LinkGenerator()
        self.downloader = ImageDownloader(output_dir / "images")
        self.analyzer = ImageAnalyzer()

    async def process(
        self,
        task_id: str,
        html: str,
        latitude: Optional[float] = None,
        longitude: Optional[float] = None,
        address: Optional[str] = None,
    ) -> ImageryResult:
        """
        Process imagery for a task.

        Args:
            task_id: Unique task identifier
            html: HTML content to extract images from
            latitude: Property latitude
            longitude: Property longitude
            address: Property address

        Returns:
            Complete imagery result
        """
        result = ImageryResult(task_id=task_id)

        # Generate external links
        try:
            result.external_links = self.link_generator.generate(
                latitude=latitude,
                longitude=longitude,
                address=address,
            )
        except Exception as e:
            logger.error(f"Error generating external links: {e}")
            result.errors.append(f"Link generation failed: {e}")

        # Extract image URLs from HTML
        try:
            if self.config:
                result.extracted_urls = self.extractor.extract(html, self.config)
            else:
                # Basic extraction without config
                result.extracted_urls = self._basic_extract(html)

            # Limit images
            result.extracted_urls = result.extracted_urls[: self.max_images]
            logger.info(f"Extracted {len(result.extracted_urls)} image URLs")

        except Exception as e:
            logger.error(f"Error extracting images: {e}")
            result.errors.append(f"Image extraction failed: {e}")

        # Download images
        if self.download_images and result.extracted_urls:
            try:
                task_dir = self.output_dir / "images" / task_id
                self.downloader.output_dir = task_dir

                result.downloaded = await self.downloader.download_all(
                    urls=result.extracted_urls,
                    prefix=task_id,
                )

                logger.info(
                    f"Downloaded {result.success_count}/{len(result.downloaded)} images"
                )

            except Exception as e:
                logger.error(f"Error downloading images: {e}")
                result.errors.append(f"Image download failed: {e}")

        # Analyze images
        if self.analyze_images and result.downloaded:
            try:
                successful_downloads = [d for d in result.downloaded if d.success and d.local_path]
                for download in successful_downloads:
                    analysis = await self.analyzer.analyze(download.local_path)
                    result.analysis.append(analysis)

            except Exception as e:
                logger.error(f"Error analyzing images: {e}")
                result.errors.append(f"Image analysis failed: {e}")

        return result

    def _basic_extract(self, html: str) -> List[str]:
        """Basic image extraction without platform config."""
        from bs4 import BeautifulSoup
        import re

        soup = BeautifulSoup(html, "lxml")
        images = []

        # Extract from img tags
        for img in soup.find_all("img"):
            src = img.get("src")
            if src and not src.startswith("data:"):
                images.append(src)

        # Filter out obvious non-property images
        filtered = []
        exclude = re.compile(r"(icon|logo|spinner|avatar|banner|ad)", re.I)

        for url in images:
            if not exclude.search(url):
                filtered.append(url)

        return filtered

    async def download_single(
        self,
        url: str,
        task_id: str,
    ) -> DownloadResult:
        """Download a single image."""
        task_dir = self.output_dir / "images" / task_id
        self.downloader.output_dir = task_dir
        return await self.downloader.download_single(url, prefix=task_id)

    def generate_links_only(
        self,
        latitude: Optional[float] = None,
        longitude: Optional[float] = None,
        address: Optional[str] = None,
    ) -> ExternalLinks:
        """Generate external links without processing HTML."""
        return self.link_generator.generate(
            latitude=latitude,
            longitude=longitude,
            address=address,
        )
