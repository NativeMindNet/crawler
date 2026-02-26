"""Worker module for processing task queue."""

import asyncio
import logging
from typing import Optional
from datetime import datetime

from crawler.lpm import LocalPersistenceManager
from crawler.config_loader import PlatformConfig
from crawler.scraper.scraper import Scraper
from crawler.parser.parser import Parser
from crawler.state import StateSerializer, CheckpointState
from crawler.models.task import TaskStatus

logger = logging.getLogger(__name__)


class Worker:
    """
    Worker for processing task queue.
    
    Features:
    - Continuous task processing
    - Checkpoint-based resumability
    - Error handling with retries
    - Progress logging
    """

    def __init__(
        self,
        lpm: LocalPersistenceManager,
        config: PlatformConfig,
        max_retries: int = 3,
        drain_mode: bool = False,
        checkpoint_interval: int = 10,
    ):
        self.lpm = lpm
        self.config = config
        self.max_retries = max_retries
        self.drain_mode = drain_mode
        self.checkpoint_interval = checkpoint_interval

        # State
        self.running = False
        self.processed_count = 0
        self.error_count = 0
        self.current_task_id: Optional[str] = None

        # Components
        self.scraper: Optional[Scraper] = None
        self.parser: Optional[Parser] = None
        self.state_serializer = StateSerializer(f"{lpm.data_dir}/state")

    async def run(self) -> None:
        """Start worker loop."""
        self.running = True
        logger.info(f"Worker started for platform: {self.config.platform}")

        # Initialize scraper and parser
        self.scraper = Scraper(self.config, headless=True)
        self.parser = Parser(self.config)

        try:
            while self.running:
                # Check if we should stop (drain mode)
                if self.drain_mode:
                    depth = await self.lpm.get_queue_depth()
                    if depth == 0:
                        logger.info("Queue drained, stopping")
                        break

                # Get next task
                task = await self.lpm.get_next_task(self.config.platform)

                if task is None:
                    if self.drain_mode:
                        break
                    # Wait before checking again
                    await asyncio.sleep(5)
                    continue

                # Process task
                await self._process_task(task)

                # Create checkpoint periodically
                if self.processed_count % self.checkpoint_interval == 0:
                    await self._create_checkpoint()

        except KeyboardInterrupt:
            logger.info("Worker interrupted")
        finally:
            await self._cleanup()

    async def _process_task(self, task) -> None:
        """Process a single task."""
        self.current_task_id = task.id
        logger.info(f"Processing task: {task.id} ({task.url})")

        try:
            # Mark as processing
            success = await self.lpm.start_task(task.id)
            if not success:
                logger.warning(f"Task {task.id} already being processed")
                return

            # Fetch content
            content = await self.scraper.fetch(task.url)
            logger.debug(f"Fetched {len(content.html)} bytes")

            # Parse content
            result = self.parser.parse(content.html)
            result.task_id = task.id

            # Save result
            result_path = await self.lpm.save_result(
                task.id,
                self.config.platform,
                result.to_dict(),
            )

            # Save raw HTML
            raw_path = self.lpm.get_raw_html_path(task.id, self.config.platform)
            await self.lpm.save_text(content.html, raw_path)

            # Add discovered links to queue
            if result.discovered_links:
                await self.lpm.add_discovered_links(task.id, result.discovered_links)
                logger.debug(f"Added {len(result.discovered_links)} discovered links")

            # Mark complete
            await self.lpm.complete_task(task.id, result_path)
            self.processed_count += 1

            logger.info(f"Task {task.id} completed: {result.parcel_id}")

        except Exception as e:
            logger.error(f"Task {task.id} failed: {e}")
            await self._handle_task_failure(task, e)

    async def _handle_task_failure(self, task, error: Exception) -> None:
        """Handle task failure with retry logic."""
        retry_count = await self.lpm.retry_task(task.id)

        if retry_count <= self.max_retries:
            logger.info(f"Task {task.id} will be retried (attempt {retry_count})")
        else:
            await self.lpm.fail_task(task.id, str(error))
            self.error_count += 1
            logger.error(f"Task {task.id} failed permanently after {retry_count} attempts")

    async def _create_checkpoint(self) -> None:
        """Create checkpoint for resumability."""
        checkpoint = CheckpointState.create(
            checkpoint_id=datetime.utcnow().strftime("%Y%m%d_%H%M%S"),
            task_id=self.current_task_id,
            processed_count=self.processed_count,
            error_count=self.error_count,
            metadata={
                "platform": self.config.platform,
                "drain_mode": self.drain_mode,
            },
        )
        self.state_serializer.save_checkpoint(checkpoint)
        logger.debug(f"Checkpoint created: {checkpoint.checkpoint_id}")

    async def _cleanup(self) -> None:
        """Cleanup resources."""
        self.running = False

        if self.scraper:
            await self.scraper.close()

        # Final checkpoint
        await self._create_checkpoint()

        logger.info(
            f"Worker stopped. Processed: {self.processed_count}, Errors: {self.error_count}"
        )

    def stop(self) -> None:
        """Signal worker to stop."""
        self.running = False
