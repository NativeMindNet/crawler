"""Browser manager for SeleniumBase."""

from typing import Optional
from seleniumbase import Driver


class BrowserManager:
    """
    Manages SeleniumBase browser instances.
    
    Features:
    - Headless mode with sbvirtualdisplay
    - UC mode for anti-bot bypass
    - Screenshot capability
    - Resource management
    """

    def __init__(
        self,
        headless: bool = True,
        uc_mode: bool = True,
        browser: str = "chrome",
        timeout: int = 30,
    ):
        self.headless = headless
        self.uc_mode = uc_mode
        self.browser = browser
        self.timeout = timeout
        self._driver: Optional[Driver] = None

    def get_driver(self) -> Driver:
        """Get or create browser driver."""
        if self._driver is None:
            self._driver = Driver(
                headless=self.headless,
                uc=self.uc_mode,
                browser=self.browser,
                timeout=self.timeout,
                # Anti-detection settings
                disable_cookies=True,
                disable_js=True,
                # Performance
                enable_cdp_events=True,
            )
        return self._driver

    def close(self) -> None:
        """Close browser."""
        if self._driver:
            try:
                self._driver.quit()
            except Exception:
                pass
            self._driver = None

    def take_screenshot(self) -> Optional[bytes]:
        """Take a screenshot."""
        if self._driver is None:
            return None

        try:
            return self._driver.get_screenshot_as_png()
        except Exception:
            return None

    @property
    def driver(self) -> Optional[Driver]:
        """Get current driver."""
        return self._driver

    def __enter__(self) -> "BrowserManager":
        """Context manager entry."""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        """Context manager exit."""
        self.close()
