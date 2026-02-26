"""Parsed result and discovered link models."""

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any
from enum import Enum


class RelationshipType(str, Enum):
    """Types of discovered link relationships."""
    OWNER = "owner"
    COUNTY = "county"
    PARCEL = "parcel"
    NEIGHBOR = "neighbor"
    RELATED = "related"
    UNKNOWN = "unknown"


@dataclass
class DiscoveredLink:
    """Represents a link discovered during parsing."""
    url: str
    relationship_type: RelationshipType = RelationshipType.UNKNOWN
    priority_delta: int = 0
    source_task_id: Optional[str] = None

    def to_dict(self) -> dict:
        """Convert to dictionary."""
        return {
            "url": self.url,
            "relationship_type": self.relationship_type.value,
            "priority_delta": self.priority_delta,
            "source_task_id": self.source_task_id,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "DiscoveredLink":
        """Create from dictionary."""
        return cls(
            url=data["url"],
            relationship_type=RelationshipType(data.get("relationship_type", "unknown")),
            priority_delta=data.get("priority_delta", 0),
            source_task_id=data.get("source_task_id"),
        )


@dataclass
class ParsedResult:
    """Represents parsed and structured data from scraped content."""
    task_id: str
    platform: str
    parcel_id: str
    data: Dict[str, Any]
    image_urls: List[str] = field(default_factory=list)
    external_links: Dict[str, str] = field(default_factory=dict)
    discovered_links: List[DiscoveredLink] = field(default_factory=list)

    def add_image(self, url: str) -> None:
        """Add an image URL."""
        if url not in self.image_urls:
            self.image_urls.append(url)

    def add_external_link(self, name: str, url: str) -> None:
        """Add an external mapping link."""
        self.external_links[name] = url

    def add_discovered_link(self, link: DiscoveredLink) -> None:
        """Add a discovered link."""
        self.discovered_links.append(link)

    def to_dict(self) -> dict:
        """Convert to dictionary."""
        return {
            "task_id": self.task_id,
            "platform": self.platform,
            "parcel_id": self.parcel_id,
            "data": self.data,
            "image_urls": self.image_urls,
            "external_links": self.external_links,
            "discovered_links": [link.to_dict() for link in self.discovered_links],
        }

    @classmethod
    def from_dict(cls, data: dict) -> "ParsedResult":
        """Create from dictionary."""
        result = cls(
            task_id=data["task_id"],
            platform=data["platform"],
            parcel_id=data["parcel_id"],
            data=data["data"],
            image_urls=data.get("image_urls", []),
            external_links=data.get("external_links", {}),
        )
        for link_data in data.get("discovered_links", []):
            result.discovered_links.append(DiscoveredLink.from_dict(link_data))
        return result
