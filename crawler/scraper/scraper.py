"""Main Scraper class."""

import asyncio
from typing import Optional, List
from datetime import datetime
import logging

from crawler.models.scraped_content import ScrapedContent
from crawler.models.parsed_result import DiscoveredLink, RelationshipType
from crawler.config_loader import PlatformConfig
from crawler.scraper.browser import BrowserManager
from crawler.scraper.anti_bot import AntiBotHandler
from crawler.scraper.retry import RetryConfig, retry_with_backoff
from crawler.scraper.screenshots import ScreenshotManager

logger = logging.getLogger(__name__)


class Scraper:
    """
    Main scraper class for fetching web content.
    
    Features:
    - SeleniumBase browser automation
    - Anti-bot challenge handling
    - Retry with exponential backoff
    - Screenshot capture on error
    - Discovery of related URLs
    """

    def __init__(
        self,
        config: PlatformConfig,
        headless: bool = True,
        timeout: int = 30,
        max_retries: int = 3,
        screenshot_dir: Optional[str] = None,
    ):
        self.config = config
        self.timeout = timeout
        self.max_retries = max_retries

        # Initialize components
        self.browser = BrowserManager(
            headless=headless,
            uc_mode=True,
            timeout=timeout,
        )
        self.anti_bot = AntiBotHandler(self.browser)
        self.screenshot_manager = ScreenshotManager(
            screenshot_dir or "/data/raw/screenshots"
        )

        # Retry config
        self.retry_config = RetryConfig(
            max_retries=max_retries,
            base_delay=1.0,
            max_delay=30.0,
        )

    async def fetch(self, url: str) -> ScrapedContent:
        """
        Fetch URL and return scraped content.
        
        Args:
            url: URL to fetch
        
        Returns:
            ScrapedContent with HTML and metadata
        """
        async def _do_fetch():
            return await asyncio.get_event_loop().run_in_executor(
                None, self._fetch_sync, url
            )

        return await retry_with_backoff(
            _do_fetch,
            config=self.retry_config,
            on_retry=self._on_retry,
        )

    def _fetch_sync(self, url: str) -> ScrapedContent:
        """Synchronous fetch implementation."""
        driver = self.browser.get_driver()
        discovered_urls = []

        try:
            # Navigate to URL
            driver.get(url)

            # Wait for page load
            driver.wait_for_element_present("body", timeout=self.timeout)

            # Check for anti-bot
            html = driver.page_source
            if self.anti_bot.is_blocked(html):
                challenge_info = self.anti_bot.get_challenge_info(html)
                logger.warning(f"Anti-bot detected: {challenge_info}")

                # Attempt to handle
                asyncio.get_event_loop().run_until_complete(
                    self.anti_bot.handle_challenge()
                )

                # Re-fetch after handling
                html = driver.page_source

            # Extract discovered URLs if configured
            discovery_rules = self.config.discovery.get("links", {})
            for rule_name, rule_config in discovery_rules.items():
                selector = rule_config.get("selector")
                attr = rule_config.get("attr", "href")

                if selector:
                    try:
                        elements = driver.find_elements("css selector", selector)
                        for elem in elements:
                            try:
                                link = elem.get_attribute(attr)
                                if link and link.startswith("http"):
                                    discovered_urls.append(link)
                            except Exception:
                                pass
                    except Exception:
                        pass

            # Build result
            content = ScrapedContent(
                html=html,
                url=url,
                discovered_urls=discovered_urls,
                metadata={
                    "title": driver.title,
                    "fetched_at": datetime.utcnow().isoformat(),
                    "platform": self.config.platform,
                },
            )

            return content

        except Exception as e:
            # Capture screenshot on error
            try:
                screenshot = self.browser.take_screenshot()
                if screenshot:
                    self.screenshot_manager.save_screenshot(
                        screenshot,
                        self.config.platform,
                        "error",
                        str(e)[:50],
                    )
            except Exception:
                pass

            raise

    async def fetch_with_discovery(
        self, url: str
    ) -> tuple[ScrapedContent, List[DiscoveredLink]]:
        """
        Fetch URL and extract discovered links.
        
        Returns:
            Tuple of (ScrapedContent, list of DiscoveredLink)
        """
        content = await self.fetch(url)

        # Convert discovered URLs to DiscoveredLink objects
        links = []
        discovery_rules = self.config.discovery.get("links", {})

        for discovered_url in content.discovered_urls:
            # Determine relationship type from rules
            relationship = RelationshipType.UNKNOWN
            priority_delta = 0

            for rule_name, rule_config in discovery_rules.items():
                # Simple heuristic based on rule name
                if "owner" in rule_name.lower():
                    relationship = RelationshipType.OWNER
                    priority_delta = 5
                elif "county" in rule_name.lower():
                    relationship = RelationshipType.COUNTY
                    priority_delta = 3
                elif "parcel" in rule_name.lower():
                    relationship = RelationshipType.PARCEL
                    priority_delta = 2
                elif "neighbor" in rule_name.lower():
                    relationship = RelationshipType.NEIGHBOR
                    priority_delta = 1

            links.append(
                DiscoveredLink(
                    url=discovered_url,
                    relationship_type=relationship,
                    priority_delta=priority_delta,
                )
            )

        return content, links

    async def close(self) -> None:
        """Close browser and cleanup."""
        self.browser.close()

    def _on_retry(self, attempt: int, exception: Exception) -> None:
        """Called on each retry attempt."""
        logger.warning(f"Retry attempt {attempt + 1} due to: {exception}")
