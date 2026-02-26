"""Main Parser class."""

import logging
from typing import Dict, Any, List, Optional

from crawler.models.parsed_result import ParsedResult, DiscoveredLink, RelationshipType
from crawler.config_loader import PlatformConfig
from crawler.parser.selector_engine import SelectorEngine
from crawler.parser.transformer import MappingTransformer
from crawler.parser.validator import DataValidator
from crawler.parser.image_extractor import ImageExtractor
from crawler.parser.external_links import ExternalLinkGenerator

logger = logging.getLogger(__name__)


class Parser:
    """
    Main parser class for extracting structured data from HTML.
    
    Features:
    - Config-driven selectors (CSS/XPath)
    - Data transformation via mapping
    - Validation against business rules
    - Image extraction
    - External link generation
    - Discovery of related URLs
    """

    def __init__(self, config: PlatformConfig):
        self.config = config
        self.selector_engine = SelectorEngine()
        self.transformer = MappingTransformer()
        self.validator = DataValidator()
        self.image_extractor = ImageExtractor()
        self.external_link_generator = ExternalLinkGenerator()

    def parse(self, html: str) -> ParsedResult:
        """
        Parse HTML and extract structured data.
        
        Args:
            html: HTML content to parse
        
        Returns:
            ParsedResult with extracted data
        """
        # Load HTML into selector engine
        self.selector_engine.load(html)

        # Extract raw values using selectors
        raw_data = self._extract_raw_values()

        # Transform data according to mapping
        transformed_data = self.transformer.transform(raw_data, self.config.mapping)

        # Validate against business rules
        is_valid, errors = self.validator.validate(
            transformed_data,
            self.config.business_rules,
        )

        if not is_valid:
            logger.warning(f"Validation errors: {errors}")

        # Extract parcel ID (primary identifier)
        parcel_id = self._get_parcel_id(transformed_data)

        # Build result
        result = ParsedResult(
            task_id="",  # Will be set by caller
            platform=self.config.platform,
            parcel_id=parcel_id,
            data=transformed_data,
        )

        # Extract images
        image_urls = self.image_extractor.extract(html, self.config)
        for url in image_urls:
            result.add_image(url)

        # Generate external links if coordinates available
        self._add_external_links(result, transformed_data)

        # Extract discovered links
        self._add_discovered_links(result, html)

        return result

    def _extract_raw_values(self) -> Dict[str, Any]:
        """Extract raw values using selectors."""
        raw_data = {}

        selectors = self.config.selectors.get("selectors", {})
        for name, selector_config in selectors.items():
            try:
                value = self.selector_engine.extract(selector_config)
                if value:
                    raw_data[name] = value
            except Exception as e:
                logger.debug(f"Failed to extract {name}: {e}")

        return raw_data

    def _get_parcel_id(self, data: Dict[str, Any]) -> str:
        """Get parcel ID from parsed data."""
        # Try common field names
        for field in ["parcel_id", "parcel", "apn", "account", "id"]:
            if field in data and data[field]:
                return str(data[field])

        # Try to find any field with parcel-like value
        for key, value in data.items():
            if value and isinstance(value, str):
                # Check if looks like parcel ID
                if len(value) >= 6 and any(c.isdigit() for c in value):
                    return str(value)

        return "unknown"

    def _add_external_links(
        self,
        result: ParsedResult,
        data: Dict[str, Any],
    ) -> None:
        """Add external mapping links if coordinates available."""
        # Try to get coordinates from data
        latitude = None
        longitude = None

        for field in ["latitude", "lat", "y"]:
            if field in data:
                try:
                    latitude = float(data[field])
                    break
                except (ValueError, TypeError):
                    pass

        for field in ["longitude", "lon", "lng", "x"]:
            if field in data:
                try:
                    longitude = float(data[field])
                    break
                except (ValueError, TypeError):
                    pass

        if latitude and longitude:
            links = self.external_link_generator.generate(latitude, longitude)
            for name, url in links.items():
                result.add_external_link(name, url)

    def _add_discovered_links(
        self,
        result: ParsedResult,
        html: str,
    ) -> None:
        """Add discovered links from page."""
        discovery_config = self.config.discovery.get("links", {})

        for rule_name, rule_config in discovery_config.items():
            selector = rule_config.get("selector")
            attr = rule_config.get("attr", "href")

            if not selector:
                continue

            # Determine relationship type
            relationship = self._get_relationship_type(rule_name)
            priority_delta = self._get_priority_delta(rule_name)

            # Extract links
            links = self.selector_engine.extract_all({
                "selector": selector,
                "type": "css",
                "attr": attr,
            })

            for url in links:
                if url and url.startswith("http"):
                    result.add_discovered_link(
                        DiscoveredLink(
                            url=url,
                            relationship_type=relationship,
                            priority_delta=priority_delta,
                        )
                    )

    def _get_relationship_type(self, rule_name: str) -> RelationshipType:
        """Get relationship type from rule name."""
        name_lower = rule_name.lower()

        if "owner" in name_lower:
            return RelationshipType.OWNER
        if "county" in name_lower:
            return RelationshipType.COUNTY
        if "parcel" in name_lower:
            return RelationshipType.PARCEL
        if "neighbor" in name_lower:
            return RelationshipType.NEIGHBOR

        return RelationshipType.UNKNOWN

    def _get_priority_delta(self, rule_name: str) -> int:
        """Get priority delta from rule name."""
        name_lower = rule_name.lower()

        if "owner" in name_lower:
            return 5
        if "county" in name_lower:
            return 3
        if "parcel" in name_lower:
            return 2
        if "neighbor" in name_lower:
            return 1

        return 0
