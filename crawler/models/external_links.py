"""External links model."""

from dataclasses import dataclass, field
from typing import Optional, Dict


@dataclass
class ExternalLinks:
    """Represents external mapping links for a location."""
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    address: Optional[str] = None
    google_maps: Optional[str] = None
    google_street_view: Optional[str] = None
    google_satellite: Optional[str] = None
    bing_maps: Optional[str] = None
    apple_maps: Optional[str] = None

    def __post_init__(self):
        """Generate links if coordinates are available."""
        if self.latitude and self.longitude:
            self._generate_links()

    def _generate_links(self) -> None:
        """Generate external map links from coordinates."""
        lat = self.latitude
        lon = self.longitude

        self.google_maps = f"https://www.google.com/maps?q={lat},{lon}"
        self.google_street_view = f"https://www.google.com/maps/@?api=1&map_action=pano&viewpoint={lat},{lon}"
        self.google_satellite = f"https://www.google.com/maps?q={lat},{lon}&t=k"
        self.bing_maps = f"https://www.bing.com/maps?cp={lat}~{lon}&lvl=17"
        self.apple_maps = f"https://maps.apple.com/?ll={lat},{lon}"

    def to_dict(self) -> Dict[str, Optional[str]]:
        """Convert to dictionary."""
        return {
            "latitude": str(self.latitude) if self.latitude else None,
            "longitude": str(self.longitude) if self.longitude else None,
            "address": self.address,
            "google_maps": self.google_maps,
            "google_street_view": self.google_street_view,
            "google_satellite": self.google_satellite,
            "bing_maps": self.bing_maps,
            "apple_maps": self.apple_maps,
        }

    @classmethod
    def from_coords(cls, latitude: float, longitude: float, address: Optional[str] = None) -> "ExternalLinks":
        """Create ExternalLinks from coordinates."""
        return cls(latitude=latitude, longitude=longitude, address=address)

    @classmethod
    def from_dict(cls, data: dict) -> "ExternalLinks":
        """Create from dictionary."""
        return cls(
            latitude=float(data["latitude"]) if data.get("latitude") else None,
            longitude=float(data["longitude"]) if data.get("longitude") else None,
            address=data.get("address"),
            google_maps=data.get("google_maps"),
            google_street_view=data.get("google_street_view"),
            google_satellite=data.get("google_satellite"),
            bing_maps=data.get("bing_maps"),
            apple_maps=data.get("apple_maps"),
        )
