"""Bulk data transformer."""

from typing import Dict, Any, List, Optional
from crawler.models.mapping_profile import MappingProfile


class BulkTransformer:
    """
    Transforms bulk ingestion data according to mapping profile.
    
    Features:
    - Column mapping
    - Value transformations
    - Required field validation
    - Type coercion
    """

    def __init__(self, profile_name: str):
        self.profile_name = profile_name
        self.profile: Optional[MappingProfile] = None
        self._load_profile()

    def _load_profile(self) -> None:
        """Load mapping profile."""
        # In production, this would load from config/database
        # For now, create a default profile
        self.profile = MappingProfile(
            profile_name=self.profile_name,
            source_format="auto",
            mappings={},  # Would be loaded from config
            transformations={},
            required_fields=["parcel_id"],
            idempotent_key=["parcel_id"],
        )

    def transform_batch(self, rows: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Transform a batch of rows.
        
        Args:
            rows: List of row dicts
        
        Returns:
            Transformed rows
        """
        return [self.transform_row(row) for row in rows]

    def transform_row(self, row: Dict[str, Any]) -> Dict[str, Any]:
        """
        Transform a single row.
        
        Args:
            row: Source row dict
        
        Returns:
            Transformed row dict
        """
        if not self.profile:
            return row

        result = {}

        # Apply mappings
        for source_col, target_field in self.profile.mappings.items():
            if source_col in row:
                value = row[source_col]

                # Apply transformation if defined
                transform = self.profile.transformations.get(target_field)
                if transform:
                    value = self._apply_transform(value, transform)

                result[target_field] = value

        # Copy unmapped fields
        for key, value in row.items():
            if key not in self.profile.mappings and key not in result:
                result[key] = value

        return result

    def _apply_transform(self, value: Any, transform: str) -> Any:
        """Apply a transformation to a value."""
        if value is None:
            return value

        # Built-in transforms
        if transform == "uppercase":
            return str(value).upper()
        elif transform == "lowercase":
            return str(value).lower()
        elif transform == "strip":
            return str(value).strip()
        elif transform == "to_string":
            return str(value)
        elif transform == "to_int":
            try:
                return int(value)
            except (ValueError, TypeError):
                return None
        elif transform == "to_float":
            try:
                return float(value)
            except (ValueError, TypeError):
                return None
        elif transform == "to_bool":
            if isinstance(value, bool):
                return value
            return str(value).lower() in ["true", "1", "yes"]

        return value

    def validate(self, row: Dict[str, Any]) -> tuple[bool, List[str]]:
        """
        Validate a row against profile requirements.
        
        Args:
            row: Row dict
        
        Returns:
            Tuple of (is_valid, error messages)
        """
        errors = []

        if not self.profile:
            return True, []

        # Check required fields
        for field in self.profile.required_fields:
            if field not in row or row[field] is None or row[field] == "":
                errors.append(f"Missing required field: {field}")

        return len(errors) == 0, errors

    def set_profile(self, profile: MappingProfile) -> None:
        """Set mapping profile."""
        self.profile = profile
