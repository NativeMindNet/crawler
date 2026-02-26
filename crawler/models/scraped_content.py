"""Scraped content model."""

from dataclasses import dataclass, field
from typing import Optional, List, Dict, Any


@dataclass
class ScrapedContent:
    """Represents content scraped from a URL."""
    html: str
    url: str
    screenshot: Optional[bytes] = None
    discovered_urls: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)

    def add_discovered_url(self, url: str) -> None:
        """Add a discovered URL."""
        if url not in self.discovered_urls:
            self.discovered_urls.append(url)

    def set_metadata(self, key: str, value: Any) -> None:
        """Set metadata field."""
        self.metadata[key] = value

    @property
    def size(self) -> int:
        """Get HTML size in bytes."""
        return len(self.html.encode('utf-8'))
