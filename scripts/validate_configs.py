#!/usr/bin/env python3
"""Validate platform configuration files."""

import json
import sys
from pathlib import Path
from typing import Dict, List, Tuple, Any

# Required config files per platform
REQUIRED_FILES = [
    "selectors.json",
    "mapping.json",
    "manifest.json",
]

OPTIONAL_FILES = [
    "discovery.json",
    "business_rules.json",
    "schedule.json",
    "counties.json",
]

# Schema definitions
MANIFEST_REQUIRED_KEYS = ["platform", "version"]
SELECTORS_REQUIRED_KEYS = ["default"]
MAPPING_REQUIRED_KEYS = ["default"]


class ConfigValidator:
    """Validates platform configuration files."""

    def __init__(self, config_dir: Path):
        self.config_dir = Path(config_dir)
        self.errors: List[str] = []
        self.warnings: List[str] = []

    def validate_all(self) -> Tuple[int, int]:
        """
        Validate all platforms in config directory.

        Returns:
            Tuple of (error_count, warning_count)
        """
        platforms_dir = self.config_dir / "platforms"

        if not platforms_dir.exists():
            self.errors.append(f"Platforms directory not found: {platforms_dir}")
            return len(self.errors), len(self.warnings)

        platforms = [d for d in platforms_dir.iterdir() if d.is_dir()]

        if not platforms:
            self.warnings.append("No platform directories found")
            return len(self.errors), len(self.warnings)

        print(f"Validating {len(platforms)} platforms...")

        for platform_dir in platforms:
            self._validate_platform(platform_dir)

        return len(self.errors), len(self.warnings)

    def _validate_platform(self, platform_dir: Path) -> None:
        """Validate a single platform's configuration."""
        platform = platform_dir.name
        print(f"\n  [{platform}]")

        # Check required files
        for filename in REQUIRED_FILES:
            filepath = platform_dir / filename
            if not filepath.exists():
                self.errors.append(f"{platform}: Missing required file {filename}")
                print(f"    ERROR: Missing {filename}")
            else:
                self._validate_file(platform, filepath)

        # Check optional files (warn if invalid but present)
        for filename in OPTIONAL_FILES:
            filepath = platform_dir / filename
            if filepath.exists():
                self._validate_file(platform, filepath)

    def _validate_file(self, platform: str, filepath: Path) -> None:
        """Validate a single config file."""
        filename = filepath.name

        # Try to parse JSON
        try:
            with open(filepath, "r") as f:
                data = json.load(f)
        except json.JSONDecodeError as e:
            self.errors.append(f"{platform}/{filename}: Invalid JSON - {e}")
            print(f"    ERROR: {filename} - Invalid JSON")
            return

        # Validate schema based on file type
        if filename == "manifest.json":
            self._validate_manifest(platform, data)
        elif filename == "selectors.json":
            self._validate_selectors(platform, data)
        elif filename == "mapping.json":
            self._validate_mapping(platform, data)
        elif filename == "discovery.json":
            self._validate_discovery(platform, data)
        elif filename == "business_rules.json":
            self._validate_business_rules(platform, data)
        elif filename == "schedule.json":
            self._validate_schedule(platform, data)

        print(f"    OK: {filename}")

    def _validate_manifest(self, platform: str, data: Dict[str, Any]) -> None:
        """Validate manifest.json schema."""
        for key in MANIFEST_REQUIRED_KEYS:
            if key not in data:
                self.errors.append(f"{platform}/manifest.json: Missing required key '{key}'")

        if "platform" in data and data["platform"] != platform:
            self.warnings.append(
                f"{platform}/manifest.json: platform value '{data['platform']}' "
                f"doesn't match directory name '{platform}'"
            )

    def _validate_selectors(self, platform: str, data: Dict[str, Any]) -> None:
        """Validate selectors.json schema."""
        for key in SELECTORS_REQUIRED_KEYS:
            if key not in data:
                self.errors.append(f"{platform}/selectors.json: Missing required key '{key}'")

        if "default" in data:
            default = data["default"]
            if not isinstance(default, dict):
                self.errors.append(f"{platform}/selectors.json: 'default' must be an object")
            elif not default:
                self.warnings.append(f"{platform}/selectors.json: 'default' is empty")

    def _validate_mapping(self, platform: str, data: Dict[str, Any]) -> None:
        """Validate mapping.json schema."""
        for key in MAPPING_REQUIRED_KEYS:
            if key not in data:
                self.errors.append(f"{platform}/mapping.json: Missing required key '{key}'")

    def _validate_discovery(self, platform: str, data: Dict[str, Any]) -> None:
        """Validate discovery.json schema."""
        # Discovery config is optional, just check it's a valid object
        if not isinstance(data, dict):
            self.errors.append(f"{platform}/discovery.json: Must be an object")

    def _validate_business_rules(self, platform: str, data: Dict[str, Any]) -> None:
        """Validate business_rules.json schema."""
        if not isinstance(data, dict):
            self.errors.append(f"{platform}/business_rules.json: Must be an object")

    def _validate_schedule(self, platform: str, data: Dict[str, Any]) -> None:
        """Validate schedule.json schema."""
        if not isinstance(data, dict):
            self.errors.append(f"{platform}/schedule.json: Must be an object")

    def print_summary(self) -> None:
        """Print validation summary."""
        print("\n" + "=" * 50)
        print("VALIDATION SUMMARY")
        print("=" * 50)

        if self.errors:
            print(f"\nERRORS ({len(self.errors)}):")
            for error in self.errors:
                print(f"  - {error}")

        if self.warnings:
            print(f"\nWARNINGS ({len(self.warnings)}):")
            for warning in self.warnings:
                print(f"  - {warning}")

        if not self.errors and not self.warnings:
            print("\nAll configurations valid!")

        print()


def main():
    """Main entry point."""
    # Determine config directory
    if len(sys.argv) > 1:
        config_dir = Path(sys.argv[1])
    else:
        # Default to config/ relative to this script's parent
        script_dir = Path(__file__).parent.parent
        config_dir = script_dir / "config"

    print(f"Config directory: {config_dir}")

    validator = ConfigValidator(config_dir)
    errors, warnings = validator.validate_all()
    validator.print_summary()

    # Exit with error code if there were errors
    sys.exit(1 if errors > 0 else 0)


if __name__ == "__main__":
    main()
