"""Mapping transformer for data transformation."""

from typing import Dict, Any, Optional, Callable, List
import re
from datetime import datetime


class MappingTransformer:
    """
    Transforms extracted data according to mapping configuration.
    
    Built-in transformations:
    - clean_parcel_id: Remove special chars, standardize format
    - normalize_name: Clean and format property owner name
    - to_decimal: Convert to decimal number
    - to_integer: Convert to integer
    - to_date: Parse date string
    - uppercase/lowercase: Case transformations
    - trim: Remove whitespace
    - concat: Concatenate fields
    - split: Split string
    """

    def __init__(self):
        self.transforms: Dict[str, Callable] = {
            "clean_parcel_id": self.clean_parcel_id,
            "normalize_name": self.normalize_name,
            "to_decimal": self.to_decimal,
            "to_integer": self.to_integer,
            "to_date": self.to_date,
            "uppercase": self.uppercase,
            "lowercase": self.lowercase,
            "trim": self.trim,
            "concat": self.concat,
            "split": self.split,
            "default_if_empty": self.default_if_empty,
            "regex_extract": self.regex_extract,
        }

    def transform(
        self,
        data: Dict[str, Any],
        mapping_config: Dict[str, Any],
    ) -> Dict[str, Any]:
        """
        Transform data according to mapping configuration.
        
        Args:
            data: Raw extracted data
            mapping_config: Mapping configuration with fields and transforms
        
        Returns:
            Transformed data
        """
        result = {}
        fields = mapping_config.get("fields", {})

        for field_name, field_config in fields.items():
            if not isinstance(field_config, dict):
                continue

            # Get source value
            source = field_config.get("source")
            value = data.get(source) if source else None

            # Handle const values
            if value is None and "const" in field_config:
                value = field_config["const"]

            # Apply transformation
            transform_name = field_config.get("transform")
            if transform_name and value is not None:
                transform_fn = self.transforms.get(transform_name)
                if transform_fn:
                    value = transform_fn(value, field_config)
                else:
                    # Try to call as method on value
                    value = self._apply_transform(value, transform_name, field_config)

            # Handle default
            if value is None or value == "":
                value = field_config.get("default")

            result[field_name] = value

        return result

    def _apply_transform(
        self,
        value: Any,
        transform_name: str,
        config: Dict[str, Any],
    ) -> Any:
        """Apply a transform by name."""
        # Handle method calls on strings
        if isinstance(value, str):
            if transform_name == "strip":
                return value.strip()
            if transform_name == "upper":
                return value.upper()
            if transform_name == "lower":
                return value.lower()
            if transform_name == "title":
                return value.title()

        return value

    # === Built-in Transform Methods ===

    def clean_parcel_id(self, value: str, config: Dict) -> str:
        """Clean and standardize parcel ID."""
        if not value:
            return value

        # Remove common prefixes/suffixes
        value = re.sub(r"^(APN|PARCEL|ID)[:\s]*", "", value, flags=re.IGNORECASE)

        # Remove special characters except dashes
        value = re.sub(r"[^\w\-]", "", value)

        # Normalize dashes
        value = value.replace("_", "-")

        return value.strip().upper()

    def normalize_name(self, value: str, config: Dict) -> str:
        """Normalize property owner name."""
        if not value:
            return value

        # Remove common suffixes
        value = re.sub(
            r"\s+(LLC|L\.L\.C\.|INC|CORP|CO|TRUST|TRUSTEE)\.?$",
            "",
            value,
            flags=re.IGNORECASE,
        )

        # Clean up multiple spaces
        value = re.sub(r"\s+", " ", value)

        # Title case
        value = value.title()

        return value.strip()

    def to_decimal(self, value: str, config: Dict) -> Optional[float]:
        """Convert to decimal number."""
        if not value:
            return None

        # Remove currency symbols and commas
        value = re.sub(r"[$,]", "", str(value))

        try:
            return float(value)
        except ValueError:
            return None

    def to_integer(self, value: str, config: Dict) -> Optional[int]:
        """Convert to integer."""
        if not value:
            return None

        # Remove non-numeric chars except minus
        value = re.sub(r"[^\d\-]", "", str(value))

        try:
            return int(value)
        except ValueError:
            return None

    def to_date(self, value: str, config: Dict) -> Optional[str]:
        """Convert to ISO date string."""
        if not value:
            return None

        date_format = config.get("format", "%Y-%m-%d")

        try:
            dt = datetime.strptime(value, date_format)
            return dt.isoformat()
        except ValueError:
            return value

    def uppercase(self, value: str, config: Dict) -> str:
        """Convert to uppercase."""
        return value.upper() if value else value

    def lowercase(self, value: str, config: Dict) -> str:
        """Convert to lowercase."""
        return value.lower() if value else value

    def trim(self, value: str, config: Dict) -> str:
        """Trim whitespace."""
        return value.strip() if value else value

    def concat(self, value: str, config: Dict) -> str:
        """Concatenate with other values."""
        parts = [value] if value else []
        with_values = config.get("with", [])

        if isinstance(with_values, list):
            parts.extend(with_values)
        elif isinstance(with_values, str):
            parts.append(with_values)

        separator = config.get("separator", " ")
        return separator.join(str(p) for p in parts)

    def split(self, value: str, config: Dict) -> List[str]:
        """Split string by delimiter."""
        if not value:
            return []

        delimiter = config.get("delimiter", ",")
        return value.split(delimiter)

    def default_if_empty(self, value: str, config: Dict) -> Any:
        """Return default if value is empty."""
        if not value or value == "":
            return config.get("default")
        return value

    def regex_extract(self, value: str, config: Dict) -> Optional[str]:
        """Extract using regex pattern."""
        if not value:
            return None

        pattern = config.get("pattern")
        if not pattern:
            return value

        match = re.search(pattern, value)
        if match:
            return match.group(1) if match.groups() else match.group(0)

        return value
