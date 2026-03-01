"""Application settings and mode configuration."""

import os
from enum import Enum
from typing import Optional
from dataclasses import dataclass, field
from pathlib import Path


class WorkerMode(str, Enum):
    """Worker execution mode."""
    ASYNC = "async"    # Lightweight async loop (default)
    CELERY = "celery"  # Celery distributed processing


@dataclass
class Settings:
    """
    Application settings loaded from environment.

    Environment Variables:
        MODE: Worker mode (async or celery)
        PLATFORM: Platform name (e.g., beacon, qpublic)
        CONFIG_DIR: Path to platform config directory
        DATA_DIR: Path to data storage directory
        REDIS_URL: Redis connection URL (for Celery mode)
        WEBHOOK_URL: Webhook endpoint URL
        WEBHOOK_SECRET: HMAC secret for webhooks
        LOG_LEVEL: Logging level (DEBUG, INFO, WARNING, ERROR)
        API_HOST: API server host
        API_PORT: API server port
        CELERY_CONCURRENCY: Number of Celery worker processes
    """

    # Mode
    mode: WorkerMode = WorkerMode.ASYNC

    # Platform
    platform: str = "default"
    config_dir: Path = Path("/config")
    data_dir: Path = Path("/data")

    # Redis (Celery mode)
    redis_url: str = "redis://localhost:6379/0"

    # Webhooks
    webhook_url: Optional[str] = None
    webhook_secret: Optional[str] = None

    # Logging
    log_level: str = "INFO"

    # API
    api_host: str = "0.0.0.0"
    api_port: int = 8000

    # Celery
    celery_concurrency: int = 4

    @classmethod
    def from_env(cls) -> "Settings":
        """Load settings from environment variables."""
        mode_str = os.getenv("MODE", "async").lower()
        mode = WorkerMode.CELERY if mode_str == "celery" else WorkerMode.ASYNC

        return cls(
            mode=mode,
            platform=os.getenv("PLATFORM", "default"),
            config_dir=Path(os.getenv("CONFIG_DIR", "/config")),
            data_dir=Path(os.getenv("DATA_DIR", "/data")),
            redis_url=os.getenv("REDIS_URL", "redis://localhost:6379/0"),
            webhook_url=os.getenv("WEBHOOK_URL"),
            webhook_secret=os.getenv("WEBHOOK_SECRET"),
            log_level=os.getenv("LOG_LEVEL", "INFO").upper(),
            api_host=os.getenv("API_HOST", "0.0.0.0"),
            api_port=int(os.getenv("API_PORT", "8000")),
            celery_concurrency=int(os.getenv("CELERY_CONCURRENCY", "4")),
        )

    @property
    def is_celery_mode(self) -> bool:
        """Check if running in Celery mode."""
        return self.mode == WorkerMode.CELERY

    @property
    def is_async_mode(self) -> bool:
        """Check if running in async mode."""
        return self.mode == WorkerMode.ASYNC

    def get_config_path(self) -> Path:
        """Get platform config path."""
        # If config_dir contains platform name, use directly
        # Otherwise, append platform subdirectory
        if (self.config_dir / "selectors.json").exists():
            return self.config_dir
        return self.config_dir / self.platform

    def to_dict(self) -> dict:
        """Convert to dictionary."""
        return {
            "mode": self.mode.value,
            "platform": self.platform,
            "config_dir": str(self.config_dir),
            "data_dir": str(self.data_dir),
            "redis_url": self.redis_url if self.is_celery_mode else None,
            "webhook_url": self.webhook_url,
            "log_level": self.log_level,
            "api_host": self.api_host,
            "api_port": self.api_port,
            "celery_concurrency": self.celery_concurrency if self.is_celery_mode else None,
        }


# Global settings instance
_settings: Optional[Settings] = None


def get_settings() -> Settings:
    """Get application settings (cached)."""
    global _settings
    if _settings is None:
        _settings = Settings.from_env()
    return _settings


def reload_settings() -> Settings:
    """Reload settings from environment."""
    global _settings
    _settings = Settings.from_env()
    return _settings


# Helper function for config loading
def load_platform_config(platform: Optional[str] = None):
    """
    Load platform configuration.

    Args:
        platform: Platform name (uses settings.platform if not provided)

    Returns:
        PlatformConfig
    """
    from crawler.config_loader import ConfigLoader

    settings = get_settings()
    platform = platform or settings.platform

    # Determine config directory
    config_dir = settings.config_dir
    if not (config_dir / "selectors.json").exists():
        # Config dir is parent of platform directories
        loader = ConfigLoader(str(config_dir))
        return loader.load(platform)
    else:
        # Config dir IS the platform config
        loader = ConfigLoader(str(config_dir.parent))
        return loader.load(config_dir.name)
