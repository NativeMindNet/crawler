"""Selector engine for CSS/XPath extraction."""

from typing import Optional, List, Dict, Any
from bs4 import BeautifulSoup, Tag
import re


class SelectorEngine:
    """
    Extracts data from HTML using CSS or XPath selectors.
    
    Supported selector types:
    - CSS selectors
    - XPath (converted to CSS where possible)
    - Regular expressions
    """

    def __init__(self, html: Optional[str] = None):
        self.soup: Optional[BeautifulSoup] = None
        if html:
            self.load(html)

    def load(self, html: str) -> None:
        """Load HTML content."""
        self.soup = BeautifulSoup(html, "lxml")

    def extract(
        self,
        selector_config: Dict[str, Any],
    ) -> Optional[str]:
        """
        Extract value using selector configuration.
        
        Args:
            selector_config: Dict with selector, type, attr, index, etc.
        
        Returns:
            Extracted value or None
        """
        if self.soup is None:
            raise ValueError("No HTML loaded. Call load() first.")

        selector = selector_config.get("selector")
        selector_type = selector_config.get("type", "css")
        attr = selector_config.get("attr")
        index = selector_config.get("index", 0)

        if not selector:
            return None

        # Find elements based on selector type
        elements = self._find_elements(selector, selector_type)

        if not elements:
            return None

        # Get specific element by index
        if index < 0:
            index = len(elements) + index
        if index < 0 or index >= len(elements):
            return None

        element = elements[index]
        return self._extract_value(element, attr)

    def extract_all(
        self,
        selector_config: Dict[str, Any],
    ) -> List[str]:
        """
        Extract all matching values.
        
        Returns:
            List of extracted values
        """
        if self.soup is None:
            raise ValueError("No HTML loaded. Call load() first.")

        selector = selector_config.get("selector")
        selector_type = selector_config.get("type", "css")
        attr = selector_config.get("attr")

        if not selector:
            return []

        elements = self._find_elements(selector, selector_type)
        return [self._extract_value(elem, attr) for elem in elements]

    def _find_elements(
        self,
        selector: str,
        selector_type: str,
    ) -> List[Tag]:
        """Find elements using selector."""
        if selector_type == "css":
            try:
                return self.soup.select(selector)
            except Exception:
                return []

        elif selector_type == "xpath":
            # Convert XPath to CSS where possible, otherwise use lxml
            return self._xpath_select(selector)

        elif selector_type == "regex":
            return self._regex_select(selector)

        else:
            # Default to CSS
            try:
                return self.soup.select(selector)
            except Exception:
                return []

    def _xpath_select(self, xpath: str) -> List[Tag]:
        """Handle XPath selectors."""
        # Simple XPath to CSS conversions
        if xpath.startswith("//") and "[@id=" in xpath:
            # //div[@id="foo"] -> #foo
            match = re.search(r'\[@id="([^"]+)"\]', xpath)
            if match:
                return self.soup.select(f"#{match.group(1)}")

        if xpath.startswith("//") and "[@class=" in xpath:
            # //div[@class="foo"] -> .foo
            match = re.search(r'\[@class="([^"]+)"\]', xpath)
            if match:
                return self.soup.select(f".{match.group(1)}")

        # For complex XPath, fall back to finding by tag
        tag_match = re.search(r"//(\w+)", xpath)
        if tag_match:
            return self.soup.find_all(tag_match.group(1))

        return []

    def _regex_select(self, pattern: str) -> List[Tag]:
        """Find elements using regex on HTML."""
        if self.soup is None:
            return []

        # Search for pattern in HTML
        matches = re.findall(pattern, str(self.soup), re.IGNORECASE | re.MULTILINE)

        # Create fake tags from matches
        result = []
        for match in matches:
            if isinstance(match, tuple):
                match = match[0]
            tag = Tag(name="span", string=match)
            result.append(tag)

        return result

    def _extract_value(self, element: Tag, attr: Optional[str]) -> str:
        """Extract value from element."""
        if attr is None:
            # Get text content
            return element.get_text(strip=True)

        if attr == "text":
            return element.get_text(strip=True)

        if attr == "html":
            return str(element)

        if attr == "href":
            href = element.get("href")
            return href or ""

        if attr == "src":
            src = element.get("src")
            return src or ""

        if attr.startswith("data-"):
            return element.get(attr, "")

        # Generic attribute
        return element.get(attr, "")

    def clear(self) -> None:
        """Clear loaded HTML."""
        self.soup = None
