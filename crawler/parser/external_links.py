"""External link generator for mapping services."""

from typing import Dict, Optional


class ExternalLinkGenerator:
    """
    Generates external mapping links for properties.
    
    Supported services:
    - Google Maps
    - Google Street View
    - Google Satellite
    - Bing Maps
    - Apple Maps
    """

    def generate(
        self,
        latitude: float,
        longitude: float,
        address: Optional[str] = None,
    ) -> Dict[str, str]:
        """
        Generate all external mapping links.
        
        Args:
            latitude: Property latitude
            longitude: Property longitude
            address: Optional street address
        
        Returns:
            Dict of service name -> URL
        """
        links = {}

        # Google Maps
        links["google_maps"] = (
            f"https://www.google.com/maps?q={latitude},{longitude}"
        )

        # Google Street View
        links["google_street_view"] = (
            f"https://www.google.com/maps/@?api=1&map_action=pano"
            f"&viewpoint={latitude},{longitude}"
        )

        # Google Satellite
        links["google_satellite"] = (
            f"https://www.google.com/maps?q={latitude},{longitude}&t=k"
        )

        # Bing Maps
        links["bing_maps"] = (
            f"https://www.bing.com/maps?cp={latitude}~{longitude}&lvl=17"
        )

        # Apple Maps
        links["apple_maps"] = (
            f"https://maps.apple.com/?ll={latitude},{longitude}"
        )

        # If address provided, add address-based links
        if address:
            encoded_address = address.replace(" ", "+").replace(",", "")
            links["google_maps_address"] = (
                f"https://www.google.com/maps/search/{encoded_address}"
            )

        return links

    def generate_google_maps(
        self,
        latitude: float,
        longitude: float,
    ) -> str:
        """Generate Google Maps link."""
        return f"https://www.google.com/maps?q={latitude},{longitude}"

    def generate_street_view(
        self,
        latitude: float,
        longitude: float,
    ) -> str:
        """Generate Google Street View link."""
        return (
            f"https://www.google.com/maps/@?api=1&map_action=pano"
            f"&viewpoint={latitude},{longitude}"
        )

    def generate_satellite(
        self,
        latitude: float,
        longitude: float,
    ) -> str:
        """Generate Google Satellite link."""
        return f"https://www.google.com/maps?q={latitude},{longitude}&t=k"

    def generate_bing_maps(
        self,
        latitude: float,
        longitude: float,
    ) -> str:
        """Generate Bing Maps link."""
        return f"https://www.bing.com/maps?cp={latitude}~{longitude}&lvl=17"

    def generate_apple_maps(
        self,
        latitude: float,
        longitude: float,
    ) -> str:
        """Generate Apple Maps link."""
        return f"https://maps.apple.com/?ll={latitude},{longitude}"
