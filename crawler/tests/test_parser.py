"""Tests for parser."""

import pytest
from crawler.parser.parser import Parser
from crawler.config_loader import PlatformConfig


@pytest.mark.asyncio
def test_parser_extract(sample_html: str, sample_config: dict):
    """Test basic parsing."""
    config = PlatformConfig(
        platform="test",
        selectors=sample_config["selectors"],
        mapping=sample_config["mapping"],
    )

    parser = Parser(config)
    result = parser.parse(sample_html)

    assert result.parcel_id == "12345-67890"
    assert result.data.get("parcel_id") == "12345-67890"
    assert result.data.get("owner_name") == "John Doe"


def test_selector_engine(sample_html: str):
    """Test selector engine."""
    from crawler.parser.selector_engine import SelectorEngine

    engine = SelectorEngine(sample_html)

    # Test CSS selector
    value = engine.extract({"selector": "#parcel_id", "type": "css"})
    assert value == "12345-67890"

    # Test with attr
    engine2 = SelectorEngine('<a href="https://example.com">Link</a>')
    value = engine2.extract({"selector": "a", "type": "css", "attr": "href"})
    assert value == "https://example.com"


def test_transformer():
    """Test mapping transformer."""
    from crawler.parser.transformer import MappingTransformer

    transformer = MappingTransformer()

    # Test clean_parcel_id
    result = transformer.clean_parcel_id("APN: 123-456", {})
    assert result == "123-456"

    # Test to_decimal
    result = transformer.to_decimal("$1,234.56", {})
    assert result == 1234.56

    # Test normalize_name
    result = transformer.normalize_name("JOHN DOE LLC", {})
    assert "John" in result and "Doe" in result
