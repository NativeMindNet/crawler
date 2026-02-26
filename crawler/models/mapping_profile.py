"""Mapping profile model."""

from dataclasses import dataclass, field
from typing import Dict, List, Any, Optional


@dataclass
class MappingProfile:
    """Represents a mapping profile for bulk ingestion."""
    profile_name: str
    source_format: str
    mappings: Dict[str, str]  # source_col -> target_field
    transformations: Dict[str, Any] = field(default_factory=dict)
    required_fields: List[str] = field(default_factory=list)
    idempotent_key: List[str] = field(default_factory=list)

    def get_target_field(self, source_col: str) -> Optional[str]:
        """Get target field for a source column."""
        return self.mappings.get(source_col)

    def get_transformation(self, field: str) -> Optional[Any]:
        """Get transformation function for a field."""
        return self.transformations.get(field)

    def is_required(self, field: str) -> bool:
        """Check if a field is required."""
        return field in self.required_fields

    def validate(self, data: Dict[str, Any]) -> List[str]:
        """Validate that required fields are present."""
        missing = []
        for field in self.required_fields:
            if field not in data:
                missing.append(field)
        return missing

    def to_dict(self) -> dict:
        """Convert to dictionary."""
        return {
            "profile_name": self.profile_name,
            "source_format": self.source_format,
            "mappings": self.mappings,
            "transformations": self.transformations,
            "required_fields": self.required_fields,
            "idempotent_key": self.idempotent_key,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "MappingProfile":
        """Create from dictionary."""
        return cls(
            profile_name=data["profile_name"],
            source_format=data["source_format"],
            mappings=data["mappings"],
            transformations=data.get("transformations", {}),
            required_fields=data.get("required_fields", []),
            idempotent_key=data.get("idempotent_key", []),
        )
