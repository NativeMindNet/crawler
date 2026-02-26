"""Image extractor for property photos."""

import re
from typing import List, Dict, Any
from bs4 import BeautifulSoup

from crawler.config_loader import PlatformConfig


class ImageExtractor:
    """
    Extracts property images from HTML.
    
    Features:
    - Filter out icons/logos
    - Handle common image patterns
    - Platform-specific extraction rules
    """

    # Patterns to exclude (icons, logos, etc.)
    EXCLUDE_PATTERNS = [
        r"icon",
        r"logo",
        r"spinner",
        r"loader",
        r"avatar",
        r"thumb",
        r"pixel",
        r"analytics",
        r"tracking",
        r"doubleclick",
        r"googletagmanager",
    ]

    # Common image extensions
    IMAGE_EXTENSIONS = [".jpg", ".jpeg", ".png", ".gif", ".webp", ".svg"]

    # Minimum image dimensions (heuristic)
    MIN_WIDTH = 200
    MIN_HEIGHT = 200

    def __init__(self):
        self.exclude_regex = re.compile(
            "|".join(self.EXCLUDE_PATTERNS),
            re.IGNORECASE,
        )

    def extract(
        self,
        html: str,
        config: PlatformConfig,
    ) -> List[str]:
        """
        Extract image URLs from HTML.
        
        Args:
            html: HTML content
            config: Platform configuration
        
        Returns:
            List of image URLs
        """
        soup = BeautifulSoup(html, "lxml")
        images = []

        # Check for platform-specific extraction rules
        image_config = config.mapping.get("images", {})
        if image_config:
            images.extend(self._extract_by_config(soup, image_config))

        # Also extract common image patterns
        images.extend(self._extract_img_tags(soup))
        images.extend(self._extract_background_images(soup))
        images.extend(self._extract_from_style(soup))

        # Filter and deduplicate
        return self._filter_images(images)

    def _extract_by_config(
        self,
        soup: BeautifulSoup,
        config: Dict[str, Any],
    ) -> List[str]:
        """Extract images using configuration."""
        images = []

        selector = config.get("selector")
        attr = config.get("attr", "src")

        if selector:
            elements = soup.select(selector)
            for elem in elements:
                value = elem.get(attr)
                if value:
                    images.append(value)

        return images

    def _extract_img_tags(self, soup: BeautifulSoup) -> List[str]:
        """Extract from img tags."""
        images = []

        for img in soup.find_all("img"):
            src = img.get("src")
            if src:
                images.append(self._resolve_url(src))

            # Also check srcset
            srcset = img.get("srcset")
            if srcset:
                images.extend(self._parse_srcset(srcset))

        return images

    def _extract_background_images(self, soup: BeautifulSoup) -> List[str]:
        """Extract from background-image styles."""
        images = []

        for elem in soup.find_all(style=True):
            style = elem.get("style", "")
            match = re.search(r"background-image:\s*url\(['\"]?([^'\")]+)['\"]?\)", style)
            if match:
                images.append(self._resolve_url(match.group(1)))

        return images

    def _extract_from_style(self, soup: BeautifulSoup) -> List[str]:
        """Extract from style blocks."""
        images = []

        for style in soup.find_all("style"):
            if style.string:
                matches = re.findall(r"url\(['\"]?([^'\")]+)['\"]?\)", style.string)
                for match in matches:
                    images.append(self._resolve_url(match))

        return images

    def _resolve_url(self, url: str) -> str:
        """Resolve relative URL."""
        if url.startswith("//"):
            return "https:" + url
        if url.startswith("http"):
            return url
        if url.startswith("/"):
            # Absolute path - keep as is for now
            return url
        return url

    def _parse_srcset(self, srcset: str) -> List[str]:
        """Parse srcset attribute."""
        urls = []
        for item in srcset.split(","):
            parts = item.strip().split()
            if parts:
                urls.append(self._resolve_url(parts[0]))
        return urls

    def _filter_images(self, images: List[str]) -> List[str]:
        """Filter out unwanted images and deduplicate."""
        filtered = []
        seen = set()

        for url in images:
            # Normalize URL
            url = url.strip()
            if not url:
                continue

            # Skip data URLs
            if url.startswith("data:"):
                continue

            # Skip if matches exclude patterns
            if self.exclude_regex.search(url):
                continue

            # Skip if no image extension (heuristic)
            has_extension = any(
                url.lower().split("?")[0].endswith(ext)
                for ext in self.IMAGE_EXTENSIONS
            )
            if not has_extension:
                continue

            # Deduplicate
            if url in seen:
                continue
            seen.add(url)

            filtered.append(url)

        return filtered
