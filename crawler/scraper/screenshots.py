"""Screenshot capture on error."""

from pathlib import Path
from typing import Optional
from datetime import datetime


class ScreenshotManager:
    """
    Manages screenshot capture and storage.
    
    Features:
    - Automatic naming with timestamps
    - Organized by platform and error type
    - Memory-efficient storage
    """

    def __init__(self, base_dir: str):
        self.base_dir = Path(base_dir)
        self.base_dir.mkdir(parents=True, exist_ok=True)

    def get_screenshot_path(
        self,
        platform: str,
        task_id: str,
        error_type: Optional[str] = None,
    ) -> Path:
        """Get path for screenshot."""
        platform_dir = self.base_dir / platform
        platform_dir.mkdir(parents=True, exist_ok=True)

        timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
        suffix = f"_{error_type}" if error_type else ""
        filename = f"{task_id}_{timestamp}{suffix}.png"

        return platform_dir / filename

    def save_screenshot(
        self,
        screenshot: bytes,
        platform: str,
        task_id: str,
        error_type: Optional[str] = None,
    ) -> Path:
        """Save screenshot to file."""
        path = self.get_screenshot_path(platform, task_id, error_type)
        path.parent.mkdir(parents=True, exist_ok=True)

        with open(path, "wb") as f:
            f.write(screenshot)

        return path

    def save_screenshot_from_driver(
        self,
        driver,
        platform: str,
        task_id: str,
        error_type: Optional[str] = None,
    ) -> Optional[Path]:
        """Capture and save screenshot from Selenium driver."""
        try:
            screenshot = driver.get_screenshot_as_png()
            return self.save_screenshot(screenshot, platform, task_id, error_type)
        except Exception as e:
            print(f"Failed to capture screenshot: {e}")
            return None

    def list_screenshots(
        self,
        platform: Optional[str] = None,
        task_id: Optional[str] = None,
    ) -> list:
        """List screenshots."""
        if platform:
            platform_dir = self.base_dir / platform
            if not platform_dir.exists():
                return []

            if task_id:
                return list(platform_dir.glob(f"{task_id}*.png"))
            return list(platform_dir.glob("*.png"))

        # All screenshots
        screenshots = []
        for platform_dir in self.base_dir.iterdir():
            if platform_dir.is_dir():
                screenshots.extend(platform_dir.glob("*.png"))
        return screenshots

    def delete_old_screenshots(self, days: int = 7) -> int:
        """Delete screenshots older than specified days."""
        import time

        cutoff = time.time() - (days * 24 * 60 * 60)
        deleted = 0

        for screenshot in self.list_screenshots():
            if screenshot.stat().st_mtime < cutoff:
                try:
                    screenshot.unlink()
                    deleted += 1
                except Exception:
                    pass

        return deleted
