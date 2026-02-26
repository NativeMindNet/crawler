"""Configuration routes."""

from fastapi import APIRouter, HTTPException, Query
from typing import List

from crawler.api.schemas import PlatformConfigResponse, ConfigListResponse

router = APIRouter()


@router.get("", response_model=ConfigListResponse)
async def list_configs():
    """List available platform configurations."""
    from fastapi import Request
    request = Request.scope.get("request")
    config_loader = request.app.state.config_loader if request else None

    if not config_loader:
        raise HTTPException(status_code=500, detail="Config loader not initialized")

    platforms = config_loader.list_platforms()
    configs = []

    for platform in platforms:
        config = config_loader.load(platform)
        if config:
            configs.append(
                PlatformConfigResponse(
                    platform=platform,
                    name=config.manifest.get("name", platform),
                    version=config.manifest.get("version", "unknown"),
                    is_valid=config.is_valid,
                    selectors_count=len(config.selectors),
                    has_mapping=bool(config.mapping),
                    has_discovery=bool(config.discovery),
                )
            )

    return ConfigListResponse(
        platforms=configs,
        total=len(configs),
    )


@router.get("/{platform}", response_model=PlatformConfigResponse)
async def get_config(platform: str):
    """Get platform configuration."""
    from fastapi import Request
    request = Request.scope.get("request")
    config_loader = request.app.state.config_loader if request else None

    if not config_loader:
        raise HTTPException(status_code=500, detail="Config loader not initialized")

    config = config_loader.load(platform)
    if not config:
        raise HTTPException(status_code=404, detail="Platform not found")

    return PlatformConfigResponse(
        platform=platform,
        name=config.manifest.get("name", platform),
        version=config.manifest.get("version", "unknown"),
        is_valid=config.is_valid,
        selectors_count=len(config.selectors),
        has_mapping=bool(config.mapping),
        has_discovery=bool(config.discovery),
    )


@router.post("/{platform}/validate")
async def validate_config(platform: str):
    """Validate platform configuration."""
    from fastapi import Request
    from crawler.config_validator import ConfigValidator
    from pathlib import Path

    request = Request.scope.get("request")
    config_dir = request.app.state.config_dir if request else "/config"

    config_path = Path(config_dir) / platform
    if not config_path.exists():
        raise HTTPException(status_code=404, detail="Platform not found")

    validator = ConfigValidator(config_path)
    result = validator.validate_all()

    return {
        "platform": platform,
        "is_valid": result.is_valid,
        "errors": result.errors,
        "warnings": result.warnings,
        "info": result.info,
    }
