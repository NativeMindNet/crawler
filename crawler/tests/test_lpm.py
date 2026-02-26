"""Tests for LPM."""

import pytest
from crawler.lpm import LocalPersistenceManager


@pytest.mark.asyncio
async def test_lpm_add_task(temp_db: str, tmp_path):
    """Test adding a task."""
    lpm = LocalPersistenceManager(temp_db, str(tmp_path))
    await lpm.initialize()

    try:
        task_id = await lpm.add_task(
            url="https://example.com",
            platform="test",
            priority=5,
        )

        task = await lpm.get_task(task_id)
        assert task is not None
        assert task.url == "https://example.com"
        assert task.platform == "test"
        assert task.priority == 5
        assert task.status.value == "pending"
    finally:
        await lpm.close()


@pytest.mark.asyncio
async def test_lpm_get_next_task(temp_db: str, tmp_path):
    """Test getting next pending task."""
    lpm = LocalPersistenceManager(temp_db, str(tmp_path))
    await lpm.initialize()

    try:
        # Add tasks with different priorities
        await lpm.add_task("https://low.com", "test", priority=1)
        await lpm.add_task("https://high.com", "test", priority=10)
        await lpm.add_task("https://med.com", "test", priority=5)

        # Should get highest priority first
        task = await lpm.get_next_task()
        assert task.url == "https://high.com"
    finally:
        await lpm.close()


@pytest.mark.asyncio
async def test_lpm_complete_task(temp_db: str, tmp_path):
    """Test completing a task."""
    lpm = LocalPersistenceManager(temp_db, str(tmp_path))
    await lpm.initialize()

    try:
        task_id = await lpm.add_task("https://example.com", "test")

        await lpm.complete_task(task_id, "/results/test.json")

        task = await lpm.get_task(task_id)
        assert task.status.value == "completed"
        assert task.result_path == "/results/test.json"
    finally:
        await lpm.close()
