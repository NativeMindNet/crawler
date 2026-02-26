"""Discovery engine for ripple effect."""

import logging
from typing import List, Optional

from crawler.lpm import LocalPersistenceManager
from crawler.config_loader import PlatformConfig
from crawler.models.parsed_result import DiscoveredLink

logger = logging.getLogger(__name__)


class DiscoveryEngine:
    """
    Processes discovered links and adds them to the queue.
    
    Features:
    - Automatic link discovery from parsed results
    - Priority adjustment based on relationship type
    - Duplicate prevention
    """

    def __init__(
        self,
        lpm: LocalPersistenceManager,
        config: PlatformConfig,
    ):
        self.lpm = lpm
        self.config = config

    async def process_discovered_links(
        self,
        source_task_id: str,
        links: List[DiscoveredLink],
    ) -> int:
        """
        Process discovered links and add to queue.
        
        Args:
            source_task_id: ID of task that discovered the links
            links: List of discovered links
        
        Returns:
            Count of links added to queue
        """
        added = 0

        for link in links:
            # Check if already processed or in queue
            is_duplicate = await self._is_duplicate(link.url)
            if is_duplicate:
                logger.debug(f"Skipping duplicate link: {link.url}")
                continue

            # Add to discovered links table
            await self.lpm.add_discovered_links(source_task_id, [link])

            # Add as new task with adjusted priority
            base_priority = 0  # Could come from config
            priority = base_priority + link.priority_delta

            await self.lpm.add_task(
                url=link.url,
                platform=self.config.platform,
                priority=priority,
            )

            added += 1
            logger.debug(f"Added discovered link: {link.url} (priority: {priority})")

        return added

    async def _is_duplicate(self, url: str) -> bool:
        """Check if URL is already in queue or processed."""
        # Check pending tasks
        pending = await self.lpm.get_pending_tasks(limit=1000)
        for task in pending:
            if task.url == url:
                return True

        # TODO: Check processed results (would need index)
        return False

    async def get_unprocessed_links(
        self,
        source_task_id: Optional[str] = None,
    ) -> List[DiscoveredLink]:
        """Get unprocessed discovered links."""
        return await self.lpm.get_unprocessed_links(source_task_id)

    async def mark_link_processed(self, url: str) -> None:
        """Mark a link as processed."""
        await self.lpm.mark_link_processed(url)
