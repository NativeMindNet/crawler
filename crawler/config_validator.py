"""Configuration validator for platform configs."""

import json
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple
from dataclasses import dataclass


@dataclass
class ValidationResult:
    """Result of configuration validation."""
    is_valid: bool
    platform: str
    errors: List[str]
    warnings: List[str]
    info: Dict[str, Any]

    @classmethod
    def success(
        cls,
        platform: str,
        info: Optional[Dict[str, Any]] = None,
        warnings: Optional[List[str]] = None,
    ) -> "ValidationResult":
        """Create a success result."""
        return cls(
            is_valid=True,
            platform=platform,
            errors=[],
            warnings=warnings or [],
            info=info or {},
        )

    @classmethod
    def failure(
        cls,
        platform: str,
        errors: List[str],
        warnings: Optional[List[str]] = None,
    ) -> "ValidationResult":
        """Create a failure result."""
        return cls(
            is_valid=False,
            platform=platform,
            errors=errors,
            warnings=warnings or [],
            info={},
        )


class ConfigValidator:
    """
    Validates platform configuration files.
    
    Validates:
    - File existence
    - JSON syntax
    - Required fields
    - Schema structure
    - Cross-file references
    """

    # Required selector fields
    SELECTOR_REQUIRED_FIELDS = ["selector", "type"]

    # Valid selector types
    VALID_SELECTOR_TYPES = ["css", "xpath", "regex"]

    # Valid attribute types for selectors
    VALID_ATTR_TYPES = ["text", "html", "href", "src", "data-*", "class", "id"]

    def __init__(self, config_path: Path):
        self.config_path = config_path
        self.platform = config_path.name

    def validate_all(self) -> ValidationResult:
        """Validate all configuration files."""
        all_errors = []
        all_warnings = []
        info = {}

        # Validate each config file
        selectors_result = self.validate_selectors()
        if not selectors_result.is_valid:
            all_errors.extend(selectors_result.errors)
        all_warnings.extend(selectors_result.warnings)
        info["selectors"] = selectors_result.info

        mapping_result = self.validate_mapping()
        if not mapping_result.is_valid:
            all_errors.extend(mapping_result.errors)
        all_warnings.extend(mapping_result.warnings)
        info["mapping"] = mapping_result.info

        discovery_result = self.validate_discovery()
        if not discovery_result.is_valid:
            all_errors.extend(discovery_result.errors)
        all_warnings.extend(discovery_result.warnings)
        info["discovery"] = discovery_result.info

        business_rules_result = self.validate_business_rules()
        if not business_rules_result.is_valid:
            all_errors.extend(business_rules_result.errors)
        all_warnings.extend(business_rules_result.warnings)
        info["business_rules"] = business_rules_result.info

        # Check cross-file references
        cross_refs_result = self.validate_cross_references()
        all_warnings.extend(cross_refs_result.warnings)

        is_valid = len(all_errors) == 0

        if is_valid:
            return ValidationResult.success(self.platform, info, all_warnings)
        else:
            return ValidationResult.failure(self.platform, all_errors, all_warnings)

    def validate_selectors(self) -> ValidationResult:
        """Validate selectors.json."""
        path = self.config_path / "selectors.json"
        errors = []
        warnings = []
        info = {"count": 0}

        if not path.exists():
            return ValidationResult.failure(
                self.platform,
                ["selectors.json not found"],
            )

        data = self._load_json(path)
        if data is None:
            return ValidationResult.failure(
                self.platform,
                ["selectors.json is not valid JSON"],
            )

        # Check structure
        if "selectors" not in data:
            errors.append("Missing 'selectors' object")
        else:
            selectors = data["selectors"]
            info["count"] = len(selectors)

            for name, selector in selectors.items():
                if not isinstance(selector, dict):
                    errors.append(f"Selector '{name}' must be an object")
                    continue

                # Check required fields
                for field in self.SELECTOR_REQUIRED_FIELDS:
                    if field not in selector:
                        errors.append(f"Selector '{name}' missing required field: {field}")

                # Validate type
                selector_type = selector.get("type")
                if selector_type and selector_type not in self.VALID_SELECTOR_TYPES:
                    errors.append(
                        f"Selector '{name}' has invalid type '{selector_type}'. "
                        f"Valid types: {self.VALID_SELECTOR_TYPES}"
                    )

                # Validate attr if present
                attr = selector.get("attr")
                if attr and attr not in self.VALID_ATTR_TYPES and not attr.startswith("data-"):
                    warnings.append(
                        f"Selector '{name}' has unusual attr '{attr}'"
                    )

                # Check for index with regex
                if selector.get("type") == "regex" and "index" not in selector:
                    warnings.append(
                        f"Selector '{name}' uses regex but has no 'index' field"
                    )

        # Check for discovery section (optional in selectors.json)
        if "discovery" in data:
            info["has_discovery"] = True

        if errors:
            return ValidationResult.failure(self.platform, errors, warnings)
        return ValidationResult.success(self.platform, info, warnings)

    def validate_mapping(self) -> ValidationResult:
        """Validate mapping.json."""
        path = self.config_path / "mapping.json"
        errors = []
        warnings = []
        info = {"fields": 0}

        if not path.exists():
            # mapping.json is optional
            return ValidationResult.success(self.platform, info)

        data = self._load_json(path)
        if data is None:
            errors.append("mapping.json is not valid JSON")
            return ValidationResult.failure(self.platform, errors)

        # Check structure
        if "fields" not in data:
            errors.append("Missing 'fields' object")
        else:
            fields = data["fields"]
            info["fields"] = len(fields)

            for name, mapping in fields.items():
                if not isinstance(mapping, dict):
                    errors.append(f"Mapping field '{name}' must be an object")
                    continue

                # Must have either 'source' or 'const'
                if "source" not in mapping and "const" not in mapping:
                    errors.append(
                        f"Mapping field '{name}' must have 'source' or 'const'"
                    )

                # Check transform if present
                transform = mapping.get("transform")
                if transform and not isinstance(transform, str):
                    warnings.append(
                        f"Mapping field '{name}' has non-string transform"
                    )

        # Check required array
        required = data.get("required", [])
        if required and not isinstance(required, list):
            errors.append("'required' must be an array")

        info["required_fields"] = len(required)

        if errors:
            return ValidationResult.failure(self.platform, errors, warnings)
        return ValidationResult.success(self.platform, info, warnings)

    def validate_discovery(self) -> ValidationResult:
        """Validate discovery.json."""
        path = self.config_path / "discovery.json"
        errors = []
        warnings = []
        info = {"rules": 0}

        if not path.exists():
            # discovery.json is optional
            return ValidationResult.success(self.platform, info)

        data = self._load_json(path)
        if data is None:
            errors.append("discovery.json is not valid JSON")
            return ValidationResult.failure(self.platform, errors)

        # Check structure
        if "rules" not in data and "links" not in data:
            warnings.append(
                "discovery.json has no 'rules' or 'links' object"
            )
        else:
            rules = data.get("rules", data.get("links", {}))
            info["rules"] = len(rules)

        if errors:
            return ValidationResult.failure(self.platform, errors, warnings)
        return ValidationResult.success(self.platform, info, warnings)

    def validate_business_rules(self) -> ValidationResult:
        """Validate business_rules.json."""
        path = self.config_path / "business_rules.json"
        errors = []
        warnings = []
        info = {"rules": 0}

        if not path.exists():
            # business_rules.json is optional
            return ValidationResult.success(self.platform, info)

        data = self._load_json(path)
        if data is None:
            errors.append("business_rules.json is not valid JSON")
            return ValidationResult.failure(self.platform, errors)

        # Count rules
        for key in ["validations", "transforms", "constraints"]:
            if key in data:
                value = data[key]
                count = len(value) if isinstance(value, (dict, list)) else 1
                info[f"{key}_count"] = count

        info["rules"] = sum(v for k, v in info.items() if k.endswith("_count"))

        if errors:
            return ValidationResult.failure(self.platform, errors, warnings)
        return ValidationResult.success(self.platform, info, warnings)

    def validate_cross_references(self) -> ValidationResult:
        """Validate cross-file references."""
        warnings = []

        # Load selectors and mapping
        selectors_path = self.config_path / "selectors.json"
        mapping_path = self.config_path / "mapping.json"

        if not selectors_path.exists() or not mapping_path.exists():
            return ValidationResult.success(self.platform, warnings=warnings)

        selectors_data = self._load_json(selectors_path)
        mapping_data = self._load_json(mapping_path)

        if not selectors_data or not mapping_data:
            return ValidationResult.success(self.platform, warnings=warnings)

        # Check if mapping sources reference selector names
        selectors = selectors_data.get("selectors", {})
        mapping_fields = mapping_data.get("fields", {})

        for field_name, mapping in mapping_fields.items():
            source = mapping.get("source")
            if source and source not in selectors:
                warnings.append(
                    f"Mapping field '{field_name}' references unknown selector '{source}'"
                )

        return ValidationResult.success(self.platform, warnings=warnings)

    def _load_json(self, path: Path) -> Optional[Dict[str, Any]]:
        """Load JSON file."""
        if not path.exists():
            return None

        try:
            with open(path, "r", encoding="utf-8") as f:
                return json.load(f)
        except (json.JSONDecodeError, IOError):
            return None


def validate_config(config_path: str) -> ValidationResult:
    """Convenience function to validate a platform config."""
    validator = ConfigValidator(Path(config_path))
    return validator.validate_all()
