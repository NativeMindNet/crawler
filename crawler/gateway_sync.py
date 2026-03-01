"""Gateway synchronization for external task coordination."""

import asyncio
import logging
from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional, Dict, Any, List

import httpx

from crawler.lpm import LocalPersistenceManager
from crawler.config_loader import PlatformConfig
from crawler.webhooks.signer import WebhookSigner

logger = logging.getLogger(__name__)


@dataclass
class GatewayTask:
    """Task received from gateway."""

    id: str
    url: str
    platform: str
    priority: int = 0
    metadata: Dict[str, Any] = field(default_factory=dict)
    created_at: Optional[datetime] = None

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "GatewayTask":
        """Create from dictionary."""
        return cls(
            id=data["id"],
            url=data["url"],
            platform=data["platform"],
            priority=data.get("priority", 0),
            metadata=data.get("metadata", {}),
            created_at=datetime.fromisoformat(data["created_at"])
            if data.get("created_at")
            else None,
        )


@dataclass
class SyncStats:
    """Statistics from sync operation."""

    tasks_fetched: int = 0
    tasks_added: int = 0
    results_pushed: int = 0
    errors: int = 0
    last_sync: Optional[datetime] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "tasks_fetched": self.tasks_fetched,
            "tasks_added": self.tasks_added,
            "results_pushed": self.results_pushed,
            "errors": self.errors,
            "last_sync": self.last_sync.isoformat() if self.last_sync else None,
        }


class GatewaySync:
    """
    Synchronizes tasks and results with external gateway.

    Features:
    - Fetch tasks from gateway
    - Push completed results
    - HMAC authentication
    - Batch operations
    - Retry logic
    """

    def __init__(
        self,
        gateway_url: str,
        api_key: str,
        lpm: LocalPersistenceManager,
        config: PlatformConfig,
        secret: Optional[str] = None,
        sync_interval: int = 60,
        batch_size: int = 50,
    ):
        self.gateway_url = gateway_url.rstrip("/")
        self.api_key = api_key
        self.lpm = lpm
        self.config = config
        self.signer = WebhookSigner(secret) if secret else None
        self.sync_interval = sync_interval
        self.batch_size = batch_size

        self.stats = SyncStats()
        self.running = False

    async def start(self) -> None:
        """Start continuous sync loop."""
        self.running = True
        logger.info(f"Gateway sync started: {self.gateway_url}")

        while self.running:
            try:
                await self.sync()
            except Exception as e:
                logger.error(f"Sync error: {e}")
                self.stats.errors += 1

            await asyncio.sleep(self.sync_interval)

    def stop(self) -> None:
        """Stop sync loop."""
        self.running = False
        logger.info("Gateway sync stopped")

    async def sync(self) -> SyncStats:
        """
        Perform full sync: fetch tasks and push results.

        Returns:
            Sync statistics
        """
        logger.debug("Starting sync cycle")

        # Fetch new tasks
        await self._fetch_tasks()

        # Push completed results
        await self._push_results()

        self.stats.last_sync = datetime.utcnow()
        logger.debug(f"Sync complete: {self.stats.to_dict()}")

        return self.stats

    async def _fetch_tasks(self) -> None:
        """Fetch tasks from gateway."""
        try:
            tasks = await self._request_tasks()
            self.stats.tasks_fetched += len(tasks)

            for task in tasks:
                await self._add_task_to_queue(task)
                self.stats.tasks_added += 1

        except Exception as e:
            logger.error(f"Error fetching tasks: {e}")
            self.stats.errors += 1

    async def _request_tasks(self) -> List[GatewayTask]:
        """Request tasks from gateway API."""
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{self.gateway_url}/tasks",
                params={
                    "platform": self.config.platform,
                    "limit": self.batch_size,
                },
                headers=self._auth_headers(),
                timeout=30.0,
            )
            response.raise_for_status()

            data = response.json()
            return [GatewayTask.from_dict(t) for t in data.get("tasks", [])]

    async def _add_task_to_queue(self, task: GatewayTask) -> None:
        """Add gateway task to local queue."""
        await self.lpm.add_task(
            url=task.url,
            platform=task.platform,
            priority=task.priority,
            task_id=task.id,  # Use gateway's task ID
        )
        logger.debug(f"Added task from gateway: {task.id}")

    async def _push_results(self) -> None:
        """Push completed results to gateway."""
        try:
            results = await self._get_unpushed_results()

            for result in results:
                success = await self._push_single_result(result)
                if success:
                    await self._mark_result_pushed(result["task_id"])
                    self.stats.results_pushed += 1

        except Exception as e:
            logger.error(f"Error pushing results: {e}")
            self.stats.errors += 1

    async def _get_unpushed_results(self) -> List[Dict[str, Any]]:
        """Get results that haven't been pushed to gateway."""
        # This would query LPM for completed tasks not yet synced
        # Implementation depends on LPM schema
        return []

    async def _push_single_result(self, result: Dict[str, Any]) -> bool:
        """Push a single result to gateway."""
        async with httpx.AsyncClient() as client:
            try:
                response = await client.post(
                    f"{self.gateway_url}/results",
                    json=result,
                    headers=self._auth_headers(),
                    timeout=30.0,
                )
                response.raise_for_status()
                return True

            except httpx.HTTPStatusError as e:
                logger.warning(f"Failed to push result: {e}")
                return False

    async def _mark_result_pushed(self, task_id: str) -> None:
        """Mark result as pushed to gateway."""
        # Would update LPM to mark as synced
        pass

    def _auth_headers(self) -> Dict[str, str]:
        """Generate authentication headers."""
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
            "X-Platform": self.config.platform,
        }

        if self.signer:
            timestamp = datetime.utcnow().isoformat()
            headers["X-Timestamp"] = timestamp
            # Sign the timestamp for request authenticity
            headers["X-Signature"] = self.signer.sign({"timestamp": timestamp})

        return headers

    async def health_check(self) -> bool:
        """Check gateway connectivity."""
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    f"{self.gateway_url}/health",
                    headers=self._auth_headers(),
                    timeout=10.0,
                )
                return response.status_code == 200
        except Exception as e:
            logger.warning(f"Gateway health check failed: {e}")
            return False

    async def register_crawler(self) -> bool:
        """Register this crawler instance with gateway."""
        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{self.gateway_url}/crawlers/register",
                    json={
                        "platform": self.config.platform,
                        "capabilities": {
                            "scrape": True,
                            "parse": True,
                            "bulk": True,
                        },
                    },
                    headers=self._auth_headers(),
                    timeout=30.0,
                )
                response.raise_for_status()
                logger.info("Crawler registered with gateway")
                return True

        except Exception as e:
            logger.error(f"Failed to register with gateway: {e}")
            return False

    async def heartbeat(self) -> bool:
        """Send heartbeat to gateway."""
        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{self.gateway_url}/crawlers/heartbeat",
                    json={
                        "platform": self.config.platform,
                        "stats": self.stats.to_dict(),
                        "queue_depth": await self.lpm.get_queue_depth(),
                    },
                    headers=self._auth_headers(),
                    timeout=10.0,
                )
                return response.status_code == 200

        except Exception as e:
            logger.warning(f"Heartbeat failed: {e}")
            return False
