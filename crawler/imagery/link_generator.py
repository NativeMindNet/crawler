"""External map link generator."""

import logging
from typing import Optional
from urllib.parse import quote_plus

from crawler.models.external_links import ExternalLinks

logger = logging.getLogger(__name__)


class LinkGenerator:
    """
    Generates external mapping links for properties.

    Supports:
    - Google Maps (standard, street view, satellite)
    - Bing Maps
    - Apple Maps
    - Zillow
    - Redfin
    """

    # Zoom levels for different map providers
    DEFAULT_ZOOM = 17
    STREET_VIEW_ZOOM = 18

    def generate(
        self,
        latitude: Optional[float] = None,
        longitude: Optional[float] = None,
        address: Optional[str] = None,
    ) -> ExternalLinks:
        """
        Generate external links from coordinates or address.

        Args:
            latitude: Property latitude
            longitude: Property longitude
            address: Property address (fallback if no coordinates)

        Returns:
            ExternalLinks object with all generated links
        """
        if latitude is not None and longitude is not None:
            return self._generate_from_coords(latitude, longitude, address)
        elif address:
            return self._generate_from_address(address)
        else:
            logger.warning("No coordinates or address provided for link generation")
            return ExternalLinks()

    def _generate_from_coords(
        self,
        lat: float,
        lon: float,
        address: Optional[str] = None,
    ) -> ExternalLinks:
        """Generate links from coordinates."""
        return ExternalLinks(
            latitude=lat,
            longitude=lon,
            address=address,
            google_maps=self._google_maps_coords(lat, lon),
            google_street_view=self._google_street_view(lat, lon),
            google_satellite=self._google_satellite(lat, lon),
            bing_maps=self._bing_maps_coords(lat, lon),
            apple_maps=self._apple_maps_coords(lat, lon),
        )

    def _generate_from_address(self, address: str) -> ExternalLinks:
        """Generate links from address (search-based)."""
        encoded = quote_plus(address)
        return ExternalLinks(
            address=address,
            google_maps=f"https://www.google.com/maps/search/{encoded}",
            google_street_view=None,  # Can't do street view without coords
            google_satellite=f"https://www.google.com/maps/search/{encoded}?t=k",
            bing_maps=f"https://www.bing.com/maps?q={encoded}",
            apple_maps=f"https://maps.apple.com/?q={encoded}",
        )

    def _google_maps_coords(self, lat: float, lon: float) -> str:
        """Generate Google Maps link."""
        return f"https://www.google.com/maps?q={lat},{lon}&z={self.DEFAULT_ZOOM}"

    def _google_street_view(self, lat: float, lon: float) -> str:
        """Generate Google Street View link."""
        return (
            f"https://www.google.com/maps/@?api=1&map_action=pano"
            f"&viewpoint={lat},{lon}&heading=0&pitch=0&fov=90"
        )

    def _google_satellite(self, lat: float, lon: float) -> str:
        """Generate Google Maps satellite view link."""
        return f"https://www.google.com/maps?q={lat},{lon}&t=k&z={self.DEFAULT_ZOOM}"

    def _bing_maps_coords(self, lat: float, lon: float) -> str:
        """Generate Bing Maps link."""
        return f"https://www.bing.com/maps?cp={lat}~{lon}&lvl={self.DEFAULT_ZOOM}"

    def _apple_maps_coords(self, lat: float, lon: float) -> str:
        """Generate Apple Maps link."""
        return f"https://maps.apple.com/?ll={lat},{lon}&z={self.DEFAULT_ZOOM}"

    def generate_zillow_link(self, address: str) -> str:
        """Generate Zillow search link."""
        encoded = quote_plus(address)
        return f"https://www.zillow.com/homes/{encoded}_rb/"

    def generate_redfin_link(self, address: str) -> str:
        """Generate Redfin search link."""
        encoded = quote_plus(address)
        return f"https://www.redfin.com/search?q={encoded}"

    def generate_static_map_url(
        self,
        lat: float,
        lon: float,
        width: int = 600,
        height: int = 400,
        zoom: int = 17,
        api_key: Optional[str] = None,
    ) -> Optional[str]:
        """
        Generate Google Static Maps API URL.

        Note: Requires API key to actually fetch the image.
        """
        if not api_key:
            logger.debug("No API key provided for static map")
            return None

        return (
            f"https://maps.googleapis.com/maps/api/staticmap"
            f"?center={lat},{lon}"
            f"&zoom={zoom}"
            f"&size={width}x{height}"
            f"&maptype=satellite"
            f"&key={api_key}"
        )
