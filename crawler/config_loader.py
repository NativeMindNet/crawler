"""Configuration loader for platform-specific settings."""

import json
from pathlib import Path
from typing import Dict, Any, Optional, List
from dataclasses import dataclass, field
from datetime import datetime


@dataclass
class PlatformConfig:
    """Represents a complete platform configuration."""
    platform: str
    selectors: Dict[str, Any] = field(default_factory=dict)
    mapping: Dict[str, Any] = field(default_factory=dict)
    discovery: Dict[str, Any] = field(default_factory=dict)
    business_rules: Dict[str, Any] = field(default_factory=dict)
    schedule: Optional[Dict[str, Any]] = None
    manifest: Dict[str, Any] = field(default_factory=dict)
    config_path: Optional[Path] = None
    loaded_at: Optional[datetime] = None

    def get_selector(self, name: str) -> Optional[Dict[str, Any]]:
        """Get a selector by name."""
        return self.selectors.get(name)

    def get_mapping(self, name: str) -> Optional[Dict[str, Any]]:
        """Get a mapping by name."""
        return self.mapping.get(name)

    def get_discovery_rule(self, name: str) -> Optional[Dict[str, Any]]:
        """Get a discovery rule by name."""
        return self.discovery.get(name)

    def get_business_rule(self, name: str) -> Optional[Dict[str, Any]]:
        """Get a business rule by name."""
        return self.business_rules.get(name)

    @property
    def selector_names(self) -> List[str]:
        """Get list of selector names."""
        return list(self.selectors.keys())

    @property
    def is_valid(self) -> bool:
        """Check if config has minimum required fields."""
        return bool(self.platform and self.selectors)


class ConfigLoader:
    """
    Loads and manages platform configurations.
    
    Configuration directory structure:
        config_dir/
            {platform}/
                selectors.json
                mapping.json
                discovery.json
                business_rules.json
                schedule.json (optional)
                manifest.json
    """

    def __init__(self, config_dir: str):
        self.config_dir = Path(config_dir)
        self._cache: Dict[str, PlatformConfig] = {}

    def list_platforms(self) -> List[str]:
        """List available platform configurations."""
        if not self.config_dir.exists():
            return []

        platforms = []
        for item in self.config_dir.iterdir():
            if item.is_dir():
                manifest = item / "manifest.json"
                selectors = item / "selectors.json"
                # At minimum, need selectors.json
                if selectors.exists():
                    platforms.append(item.name)

        return sorted(platforms)

    def load(self, platform: str, use_cache: bool = True) -> Optional[PlatformConfig]:
        """
        Load platform configuration.
        
        Args:
            platform: Platform name (directory name)
            use_cache: Use cached config if available
        
        Returns:
            PlatformConfig or None if not found
        """
        # Check cache
        if use_cache and platform in self._cache:
            return self._cache[platform]

        platform_dir = self.config_dir / platform
        if not platform_dir.exists():
            return None

        config = PlatformConfig(
            platform=platform,
            config_path=platform_dir,
            loaded_at=datetime.utcnow(),
        )

        # Load each config file
        config.selectors = self._load_json_file(platform_dir / "selectors.json") or {}
        config.mapping = self._load_json_file(platform_dir / "mapping.json") or {}
        config.discovery = self._load_json_file(platform_dir / "discovery.json") or {}
        config.business_rules = self._load_json_file(platform_dir / "business_rules.json") or {}
        config.schedule = self._load_json_file(platform_dir / "schedule.json")
        config.manifest = self._load_json_file(platform_dir / "manifest.json") or {}

        # Cache it
        self._cache[platform] = config

        return config

    def reload(self, platform: str) -> Optional[PlatformConfig]:
        """Reload platform configuration (bypass cache)."""
        return self.load(platform, use_cache=False)

    def clear_cache(self) -> None:
        """Clear configuration cache."""
        self._cache.clear()

    def _load_json_file(self, path: Path) -> Optional[Dict[str, Any]]:
        """Load a JSON file."""
        if not path.exists():
            return None

        try:
            with open(path, "r", encoding="utf-8") as f:
                return json.load(f)
        except (json.JSONDecodeError, IOError) as e:
            return None

    def validate_config(self, platform: str) -> tuple[bool, List[str]]:
        """
        Validate a platform configuration.
        
        Returns:
            Tuple of (is_valid, list of error messages)
        """
        errors = []
        config = self.load(platform)

        if config is None:
            return False, [f"Platform '{platform}' not found"]

        # Check required files
        required_files = ["selectors.json"]
        for file in required_files:
            if not (config.config_path / file).exists():
                errors.append(f"Missing required file: {file}")

        # Validate selectors structure
        if config.selectors:
            for name, selector in config.selectors.items():
                if not isinstance(selector, dict):
                    errors.append(f"Selector '{name}' must be an object")
                    continue
                if "selector" not in selector:
                    errors.append(f"Selector '{name}' missing 'selector' field")
                if "type" not in selector:
                    errors.append(f"Selector '{name}' missing 'type' field")

        # Validate mapping structure
        if config.mapping:
            fields = config.mapping.get("fields", {})
            if not isinstance(fields, dict):
                errors.append("Mapping 'fields' must be an object")

        return len(errors) == 0, errors


def load_config(config_dir: str, platform: str) -> Optional[PlatformConfig]:
    """Convenience function to load a platform config."""
    loader = ConfigLoader(config_dir)
    return loader.load(platform)


def list_configs(config_dir: str) -> List[str]:
    """Convenience function to list available platforms."""
    loader = ConfigLoader(config_dir)
    return loader.list_platforms()
