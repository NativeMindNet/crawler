"""Test configuration and fixtures."""

import pytest
from pathlib import Path


@pytest.fixture
def sample_html() -> str:
    """Sample HTML for testing."""
    return """
    <html>
    <body>
        <div id="parcel_id">12345-67890</div>
        <div id="owner">John Doe</div>
        <div class="address">123 Main St</div>
    </body>
    </html>
    """


@pytest.fixture
def sample_config() -> dict:
    """Sample platform configuration."""
    return {
        "platform": "test",
        "selectors": {
            "parcel_id": {"selector": "#parcel_id", "type": "css"},
            "owner": {"selector": "#owner", "type": "css"},
        },
        "mapping": {
            "fields": {
                "parcel_id": {"source": "parcel_id"},
                "owner_name": {"source": "owner"},
            }
        },
        "discovery": {},
        "business_rules": {},
    }


@pytest.fixture
def temp_db(tmp_path: Path) -> str:
    """Create temporary database path."""
    return str(tmp_path / "test.db")
