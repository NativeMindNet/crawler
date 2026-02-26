"""Webhook client for sending notifications."""

import logging
from typing import Optional, Dict, Any
import httpx

from crawler.webhooks.models import WebhookPayload
from crawler.webhooks.signer import WebhookSigner

logger = logging.getLogger(__name__)


class WebhookClient:
    """
    Client for sending webhook notifications.
    
    Features:
    - HMAC signature for security
    - Retry with backoff
    - Timeout handling
    - Error logging
    """

    def __init__(
        self,
        webhook_url: Optional[str] = None,
        secret: Optional[str] = None,
        timeout: float = 10.0,
        max_retries: int = 3,
    ):
        self.webhook_url = webhook_url
        self.signer = WebhookSigner(secret) if secret else None
        self.timeout = timeout
        self.max_retries = max_retries

    async def send(self, payload: WebhookPayload) -> bool:
        """
        Send webhook payload.
        
        Args:
            payload: Payload to send
        
        Returns:
            True if sent successfully
        """
        if not self.webhook_url:
            logger.debug("No webhook URL configured, skipping send")
            return False

        return await self._send_with_retry(payload)

    async def _send_with_retry(self, payload: WebhookPayload) -> bool:
        """Send with retry logic."""
        last_error = None

        for attempt in range(self.max_retries):
            try:
                success = await self._send_once(payload)
                if success:
                    return True
            except Exception as e:
                last_error = e
                logger.warning(f"Webhook attempt {attempt + 1} failed: {e}")

            # Wait before retry (exponential backoff)
            if attempt < self.max_retries - 1:
                import asyncio
                delay = 2 ** attempt
                await asyncio.sleep(delay)

        logger.error(f"Webhook failed after {self.max_retries} attempts: {last_error}")
        return False

    async def _send_once(self, payload: WebhookPayload) -> bool:
        """Send webhook once."""
        async with httpx.AsyncClient() as client:
            # Prepare payload
            data = payload.to_dict()

            # Prepare headers
            headers = {
                "Content-Type": "application/json",
                "X-Webhook-Event": payload.event.value,
            }

            # Add signature if configured
            if self.signer:
                signature = self.signer.sign(data)
                headers["X-Webhook-Signature"] = signature

            try:
                response = await client.post(
                    self.webhook_url,
                    json=data,
                    headers=headers,
                    timeout=self.timeout,
                )

                if response.status_code >= 400:
                    logger.warning(f"Webhook returned {response.status_code}")
                    return False

                logger.info(f"Webhook sent successfully: {payload.event.value}")
                return True

            except httpx.TimeoutException:
                logger.warning("Webhook request timed out")
                return False
            except httpx.ConnectError:
                logger.warning("Webhook connection failed")
                return False

    async def send_task_completed(
        self,
        task_id: str,
        result: Dict[str, Any],
        raw_paths: Dict[str, str],
        platform: str,
    ) -> bool:
        """Send task completed notification."""
        payload = WebhookPayload.task_completed(
            task_id=task_id,
            platform=platform,
            result=result,
            raw_paths=raw_paths,
        )
        return await self.send(payload)

    async def send_task_failed(
        self,
        task_id: str,
        error: str,
        platform: str,
    ) -> bool:
        """Send task failed notification."""
        payload = WebhookPayload.task_failed(
            task_id=task_id,
            platform=platform,
            error=error,
        )
        return await self.send(payload)

    async def send_bulk_completed(
        self,
        job_id: str,
        stats: Dict[str, Any],
        platform: str,
    ) -> bool:
        """Send bulk completed notification."""
        payload = WebhookPayload.bulk_completed(
            job_id=job_id,
            platform=platform,
            stats=stats,
        )
        return await self.send(payload)
