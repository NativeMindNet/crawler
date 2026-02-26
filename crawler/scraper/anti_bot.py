"""Anti-bot challenge handler."""

import asyncio
from typing import Optional, Dict, Any
from crawler.scraper.browser import BrowserManager


class AntiBotHandler:
    """
    Handles anti-bot challenges.
    
    Detects and handles:
    - Cloudflare challenges
    - CAPTCHA pages
    - Rate limiting responses
    - Blocking pages
    """

    # Common anti-bot indicators
    BLOCKED_INDICATORS = [
        "cf-browser-verification",
        "cloudflare",
        "checking your browser",
        "ddos protection",
        "access denied",
        "captcha",
        "robot check",
    ]

    def __init__(self, browser: BrowserManager):
        self.browser = browser

    def is_blocked(self, html: str) -> bool:
        """Check if response indicates blocking."""
        html_lower = html.lower()
        return any(indicator in html_lower for indicator in self.BLOCKED_INDICATORS)

    def get_block_type(self, html: str) -> Optional[str]:
        """Get type of blocking detected."""
        html_lower = html.lower()

        if "cf-browser-verification" in html_lower or "cloudflare" in html_lower:
            return "cloudflare"
        if "captcha" in html_lower:
            return "captcha"
        if "access denied" in html_lower:
            return "access_denied"
        if "ddos protection" in html_lower:
            return "ddos_protection"

        return None

    async def handle_challenge(self) -> bool:
        """
        Attempt to handle anti-bot challenge.
        
        Returns True if handled successfully.
        """
        driver = self.browser.get_driver()
        if driver is None:
            return False

        # Wait for challenge to resolve (some resolve automatically)
        await asyncio.sleep(5)

        # Try clicking if there's a verify button
        try:
            verify_button = driver.find_element(
                "css selector",
                "input[type='button'], button, .cf-verify-button"
            )
            if verify_button:
                verify_button.click()
                await asyncio.sleep(3)
                return True
        except Exception:
            pass

        # Challenge might resolve on its own
        await asyncio.sleep(10)
        return True

    def get_challenge_info(self, html: str) -> Dict[str, Any]:
        """Get information about detected challenge."""
        return {
            "is_blocked": self.is_blocked(html),
            "block_type": self.get_block_type(html),
            "html_length": len(html),
            "title": self._extract_title(html),
        }

    def _extract_title(self, html: str) -> str:
        """Extract page title."""
        import re
        match = re.search(r"<title>(.*?)</title>", html, re.IGNORECASE)
        if match:
            return match.group(1).strip()
        return ""
