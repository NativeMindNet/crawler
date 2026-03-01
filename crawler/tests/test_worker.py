"""Tests for worker module."""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from pathlib import Path

from crawler.worker import Worker
from crawler.models.task import Task, TaskStatus


@pytest.fixture
def mock_lpm():
    """Create mock Local Persistence Manager."""
    lpm = AsyncMock()
    lpm.data_dir = "/tmp/test_data"
    lpm.get_queue_depth = AsyncMock(return_value=5)
    lpm.get_next_task = AsyncMock(return_value=None)
    lpm.start_task = AsyncMock(return_value=True)
    lpm.complete_task = AsyncMock(return_value=True)
    lpm.retry_task = AsyncMock(return_value=1)
    lpm.fail_task = AsyncMock(return_value=True)
    lpm.save_result = AsyncMock(return_value="/tmp/result.json")
    lpm.save_text = AsyncMock(return_value=True)
    lpm.get_raw_html_path = MagicMock(return_value="/tmp/raw.html")
    lpm.add_discovered_links = AsyncMock(return_value=True)
    return lpm


@pytest.fixture
def mock_config():
    """Create mock platform config."""
    config = MagicMock()
    config.platform = "test_platform"
    config.selectors = {}
    config.mapping = {}
    return config


@pytest.fixture
def worker(mock_lpm, mock_config):
    """Create worker instance."""
    return Worker(
        lpm=mock_lpm,
        config=mock_config,
        max_retries=3,
        drain_mode=True,
        checkpoint_interval=5,
    )


class TestWorkerInit:
    """Tests for Worker initialization."""

    def test_init_with_defaults(self, mock_lpm, mock_config):
        """Test worker initializes with correct defaults."""
        worker = Worker(lpm=mock_lpm, config=mock_config)

        assert worker.max_retries == 3
        assert worker.drain_mode is False
        assert worker.checkpoint_interval == 10
        assert worker.running is False
        assert worker.processed_count == 0
        assert worker.error_count == 0

    def test_init_with_custom_values(self, mock_lpm, mock_config):
        """Test worker with custom configuration."""
        worker = Worker(
            lpm=mock_lpm,
            config=mock_config,
            max_retries=5,
            drain_mode=True,
            checkpoint_interval=20,
        )

        assert worker.max_retries == 5
        assert worker.drain_mode is True
        assert worker.checkpoint_interval == 20


class TestWorkerTaskProcessing:
    """Tests for task processing."""

    @pytest.mark.asyncio
    async def test_process_task_success(self, worker, mock_lpm):
        """Test successful task processing."""
        task = MagicMock()
        task.id = "test-task-123"
        task.url = "https://example.com/property/123"

        mock_content = MagicMock()
        mock_content.html = "<html><body>Test</body></html>"

        mock_result = MagicMock()
        mock_result.task_id = task.id
        mock_result.parcel_id = "PARCEL-123"
        mock_result.discovered_links = []
        mock_result.to_dict = MagicMock(return_value={"parcel_id": "PARCEL-123"})

        with patch.object(worker, 'scraper') as mock_scraper, \
             patch.object(worker, 'parser') as mock_parser:

            mock_scraper.fetch = AsyncMock(return_value=mock_content)
            mock_parser.parse = MagicMock(return_value=mock_result)

            await worker._process_task(task)

        mock_lpm.start_task.assert_called_once_with(task.id)
        mock_lpm.complete_task.assert_called_once()
        assert worker.processed_count == 1

    @pytest.mark.asyncio
    async def test_process_task_already_processing(self, worker, mock_lpm):
        """Test task that's already being processed."""
        task = MagicMock()
        task.id = "test-task-123"
        task.url = "https://example.com/property/123"

        mock_lpm.start_task = AsyncMock(return_value=False)

        await worker._process_task(task)

        mock_lpm.complete_task.assert_not_called()
        assert worker.processed_count == 0

    @pytest.mark.asyncio
    async def test_process_task_with_discovered_links(self, worker, mock_lpm):
        """Test task that discovers new links."""
        task = MagicMock()
        task.id = "test-task-123"
        task.url = "https://example.com/property/123"

        mock_content = MagicMock()
        mock_content.html = "<html><body>Test</body></html>"

        mock_link = MagicMock()
        mock_link.url = "https://example.com/property/456"

        mock_result = MagicMock()
        mock_result.task_id = task.id
        mock_result.parcel_id = "PARCEL-123"
        mock_result.discovered_links = [mock_link]
        mock_result.to_dict = MagicMock(return_value={"parcel_id": "PARCEL-123"})

        with patch.object(worker, 'scraper') as mock_scraper, \
             patch.object(worker, 'parser') as mock_parser:

            mock_scraper.fetch = AsyncMock(return_value=mock_content)
            mock_parser.parse = MagicMock(return_value=mock_result)

            await worker._process_task(task)

        mock_lpm.add_discovered_links.assert_called_once_with(task.id, [mock_link])


class TestWorkerFailureHandling:
    """Tests for failure handling."""

    @pytest.mark.asyncio
    async def test_handle_task_failure_with_retry(self, worker, mock_lpm):
        """Test task failure triggers retry."""
        task = MagicMock()
        task.id = "test-task-123"
        error = Exception("Network error")

        mock_lpm.retry_task = AsyncMock(return_value=1)

        await worker._handle_task_failure(task, error)

        mock_lpm.retry_task.assert_called_once_with(task.id)
        mock_lpm.fail_task.assert_not_called()

    @pytest.mark.asyncio
    async def test_handle_task_failure_max_retries(self, worker, mock_lpm):
        """Test task fails permanently after max retries."""
        task = MagicMock()
        task.id = "test-task-123"
        error = Exception("Network error")

        mock_lpm.retry_task = AsyncMock(return_value=4)  # Exceeds max_retries=3

        await worker._handle_task_failure(task, error)

        mock_lpm.fail_task.assert_called_once_with(task.id, "Network error")
        assert worker.error_count == 1


class TestWorkerLifecycle:
    """Tests for worker lifecycle."""

    def test_stop_sets_running_false(self, worker):
        """Test stop method sets running to False."""
        worker.running = True
        worker.stop()
        assert worker.running is False

    @pytest.mark.asyncio
    async def test_cleanup_creates_checkpoint(self, worker):
        """Test cleanup creates final checkpoint."""
        worker.scraper = AsyncMock()
        worker.scraper.close = AsyncMock()

        with patch.object(worker, '_create_checkpoint', new_callable=AsyncMock) as mock_checkpoint:
            await worker._cleanup()

        mock_checkpoint.assert_called_once()
        assert worker.running is False

    @pytest.mark.asyncio
    async def test_run_drain_mode_empty_queue(self, worker, mock_lpm):
        """Test worker stops when queue is empty in drain mode."""
        mock_lpm.get_queue_depth = AsyncMock(return_value=0)
        mock_lpm.get_next_task = AsyncMock(return_value=None)

        with patch.object(worker, '_cleanup', new_callable=AsyncMock):
            await worker.run()

        assert worker.running is False
