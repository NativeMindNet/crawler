"""Tests for discovery engine."""

import pytest
from unittest.mock import AsyncMock, MagicMock

from crawler.discovery import DiscoveryEngine
from crawler.models.parsed_result import DiscoveredLink


@pytest.fixture
def mock_lpm():
    """Create mock Local Persistence Manager."""
    lpm = AsyncMock()
    lpm.add_discovered_links = AsyncMock(return_value=True)
    lpm.add_task = AsyncMock(return_value="new-task-id")
    lpm.get_pending_tasks = AsyncMock(return_value=[])
    lpm.get_unprocessed_links = AsyncMock(return_value=[])
    lpm.mark_link_processed = AsyncMock(return_value=True)
    return lpm


@pytest.fixture
def mock_config():
    """Create mock platform config."""
    config = MagicMock()
    config.platform = "test_platform"
    return config


@pytest.fixture
def discovery_engine(mock_lpm, mock_config):
    """Create discovery engine instance."""
    return DiscoveryEngine(lpm=mock_lpm, config=mock_config)


class TestDiscoveryEngineInit:
    """Tests for DiscoveryEngine initialization."""

    def test_init(self, mock_lpm, mock_config):
        """Test discovery engine initializes correctly."""
        engine = DiscoveryEngine(lpm=mock_lpm, config=mock_config)

        assert engine.lpm == mock_lpm
        assert engine.config == mock_config


class TestProcessDiscoveredLinks:
    """Tests for processing discovered links."""

    @pytest.mark.asyncio
    async def test_process_single_link(self, discovery_engine, mock_lpm):
        """Test processing a single discovered link."""
        link = DiscoveredLink(
            url="https://example.com/property/456",
            link_type="related",
            priority_delta=0,
        )

        count = await discovery_engine.process_discovered_links(
            source_task_id="task-123",
            links=[link],
        )

        assert count == 1
        mock_lpm.add_discovered_links.assert_called_once()
        mock_lpm.add_task.assert_called_once()

    @pytest.mark.asyncio
    async def test_process_multiple_links(self, discovery_engine, mock_lpm):
        """Test processing multiple discovered links."""
        links = [
            DiscoveredLink(url="https://example.com/p/1", link_type="related", priority_delta=0),
            DiscoveredLink(url="https://example.com/p/2", link_type="related", priority_delta=1),
            DiscoveredLink(url="https://example.com/p/3", link_type="related", priority_delta=-1),
        ]

        count = await discovery_engine.process_discovered_links(
            source_task_id="task-123",
            links=links,
        )

        assert count == 3
        assert mock_lpm.add_task.call_count == 3

    @pytest.mark.asyncio
    async def test_skip_duplicate_links(self, discovery_engine, mock_lpm):
        """Test that duplicate links are skipped."""
        # Set up existing task with same URL
        existing_task = MagicMock()
        existing_task.url = "https://example.com/property/456"
        mock_lpm.get_pending_tasks = AsyncMock(return_value=[existing_task])

        link = DiscoveredLink(
            url="https://example.com/property/456",  # Same URL
            link_type="related",
            priority_delta=0,
        )

        count = await discovery_engine.process_discovered_links(
            source_task_id="task-123",
            links=[link],
        )

        assert count == 0
        mock_lpm.add_task.assert_not_called()

    @pytest.mark.asyncio
    async def test_empty_links_list(self, discovery_engine, mock_lpm):
        """Test processing empty links list."""
        count = await discovery_engine.process_discovered_links(
            source_task_id="task-123",
            links=[],
        )

        assert count == 0
        mock_lpm.add_task.assert_not_called()

    @pytest.mark.asyncio
    async def test_priority_adjustment(self, discovery_engine, mock_lpm):
        """Test that priority delta is applied."""
        link = DiscoveredLink(
            url="https://example.com/property/456",
            link_type="high_priority",
            priority_delta=5,
        )

        await discovery_engine.process_discovered_links(
            source_task_id="task-123",
            links=[link],
        )

        # Check that add_task was called with adjusted priority
        call_args = mock_lpm.add_task.call_args
        assert call_args.kwargs.get("priority") == 5


class TestDuplicateDetection:
    """Tests for duplicate link detection."""

    @pytest.mark.asyncio
    async def test_is_duplicate_returns_true(self, discovery_engine, mock_lpm):
        """Test duplicate detection returns true for existing URL."""
        existing_task = MagicMock()
        existing_task.url = "https://example.com/existing"
        mock_lpm.get_pending_tasks = AsyncMock(return_value=[existing_task])

        result = await discovery_engine._is_duplicate("https://example.com/existing")

        assert result is True

    @pytest.mark.asyncio
    async def test_is_duplicate_returns_false(self, discovery_engine, mock_lpm):
        """Test duplicate detection returns false for new URL."""
        mock_lpm.get_pending_tasks = AsyncMock(return_value=[])

        result = await discovery_engine._is_duplicate("https://example.com/new")

        assert result is False


class TestLinkRetrieval:
    """Tests for link retrieval methods."""

    @pytest.mark.asyncio
    async def test_get_unprocessed_links(self, discovery_engine, mock_lpm):
        """Test getting unprocessed links."""
        mock_links = [
            DiscoveredLink(url="https://example.com/1", link_type="related", priority_delta=0),
            DiscoveredLink(url="https://example.com/2", link_type="related", priority_delta=0),
        ]
        mock_lpm.get_unprocessed_links = AsyncMock(return_value=mock_links)

        links = await discovery_engine.get_unprocessed_links()

        assert len(links) == 2
        mock_lpm.get_unprocessed_links.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_unprocessed_links_with_source(self, discovery_engine, mock_lpm):
        """Test getting unprocessed links for specific source."""
        await discovery_engine.get_unprocessed_links(source_task_id="task-123")

        mock_lpm.get_unprocessed_links.assert_called_once_with("task-123")

    @pytest.mark.asyncio
    async def test_mark_link_processed(self, discovery_engine, mock_lpm):
        """Test marking link as processed."""
        await discovery_engine.mark_link_processed("https://example.com/processed")

        mock_lpm.mark_link_processed.assert_called_once_with("https://example.com/processed")
