"""Config CLI commands."""

from pathlib import Path

from crawler.config_loader import ConfigLoader
from crawler.config_validator import ConfigValidator


def config_validate_command(
    platform: str,
    config_dir: str,
) -> None:
    """Validate platform configuration."""
    config_path = Path(config_dir) / platform

    if not config_path.exists():
        print(f"✗ Platform directory not found: {config_path}")
        return

    print(f"Validating platform: {platform}")
    print(f"Config path: {config_path}")
    print()

    validator = ConfigValidator(config_path)
    result = validator.validate_all()

    if result.is_valid:
        print("✓ Configuration is valid")
    else:
        print("✗ Configuration has errors:")
        for error in result.errors:
            print(f"  - {error}")

    if result.warnings:
        print("\nWarnings:")
        for warning in result.warnings:
            print(f"  - {warning}")

    # Show info
    if result.info:
        print("\nInfo:")
        for key, value in result.info.items():
            print(f"  {key}: {value}")


def config_list_command(
    config_dir: str,
) -> None:
    """List available platform configurations."""
    config_path = Path(config_dir)

    if not config_path.exists():
        print(f"✗ Config directory not found: {config_path}")
        return

    loader = ConfigLoader(config_dir)
    platforms = loader.list_platforms()

    if not platforms:
        print("No platform configurations found")
        return

    print(f"Available platforms ({len(platforms)}):")
    for platform in platforms:
        config = loader.load(platform)
        manifest = config.manifest if config else {}
        name = manifest.get("name", platform)
        version = manifest.get("version", "unknown")
        print(f"  - {platform} ({name} v{version})")
