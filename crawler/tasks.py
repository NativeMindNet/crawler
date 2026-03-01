"""Celery tasks for parallel crawling."""

import logging
from typing import Dict, Any, Optional, List
from datetime import datetime

from celery import shared_task, chain, group, chord
from celery.exceptions import MaxRetriesExceededError

from crawler.celery_app import app, get_queue_for_priority
from crawler.config_loader import load_platform_config
from crawler.scraper.scraper import Scraper
from crawler.parser.parser import Parser
from crawler.lpm import LocalPersistenceManager
from crawler.webhooks.client import WebhookClient
from crawler.models.task import TaskStatus

logger = logging.getLogger(__name__)


# ============================================================================
# Core Scraping Tasks
# ============================================================================

@app.task(
    bind=True,
    max_retries=3,
    default_retry_delay=30,
    autoretry_for=(Exception,),
    retry_backoff=True,
    retry_backoff_max=300,
)
def scrape_url(
    self,
    url: str,
    platform: str,
    task_id: Optional[str] = None,
    priority: int = 3,
) -> Dict[str, Any]:
    """
    Scrape a single URL.

    Args:
        url: URL to scrape
        platform: Platform name (e.g., 'beacon', 'qpublic')
        task_id: Optional task ID for tracking
        priority: Task priority (1=urgent, 4=low)

    Returns:
        Dict with scraped HTML and metadata
    """
    task_id = task_id or self.request.id
    logger.info(f"[{task_id}] Scraping: {url}")

    try:
        config = load_platform_config(platform)
        scraper = Scraper(config, headless=True)

        content = scraper.fetch_sync(url)

        return {
            "task_id": task_id,
            "url": url,
            "platform": platform,
            "html": content.html,
            "status_code": content.status_code,
            "scraped_at": datetime.utcnow().isoformat(),
            "success": True,
        }

    except Exception as e:
        logger.error(f"[{task_id}] Scrape failed: {e}")
        raise self.retry(exc=e)


@app.task(bind=True)
def parse_html(
    self,
    scrape_result: Dict[str, Any],
) -> Dict[str, Any]:
    """
    Parse scraped HTML content.

    Args:
        scrape_result: Result from scrape_url task

    Returns:
        Dict with parsed data
    """
    task_id = scrape_result.get("task_id", self.request.id)
    platform = scrape_result["platform"]
    html = scrape_result["html"]

    logger.info(f"[{task_id}] Parsing HTML")

    try:
        config = load_platform_config(platform)
        parser = Parser(config)

        result = parser.parse(html)
        result.task_id = task_id

        return {
            "task_id": task_id,
            "url": scrape_result["url"],
            "platform": platform,
            "parsed_data": result.to_dict(),
            "discovered_links": [link.url for link in result.discovered_links],
            "parsed_at": datetime.utcnow().isoformat(),
            "success": True,
        }

    except Exception as e:
        logger.error(f"[{task_id}] Parse failed: {e}")
        return {
            "task_id": task_id,
            "url": scrape_result["url"],
            "platform": platform,
            "success": False,
            "error": str(e),
        }


@app.task(bind=True)
def save_result(
    self,
    parse_result: Dict[str, Any],
    data_dir: str = "/data",
) -> Dict[str, Any]:
    """
    Save parsed result to local persistence.

    Args:
        parse_result: Result from parse_html task
        data_dir: Data directory path

    Returns:
        Dict with save status
    """
    task_id = parse_result.get("task_id", self.request.id)
    platform = parse_result["platform"]

    logger.info(f"[{task_id}] Saving result")

    try:
        lpm = LocalPersistenceManager(data_dir, platform)

        # Save result
        result_path = lpm.save_result_sync(
            task_id,
            platform,
            parse_result.get("parsed_data", {}),
        )

        return {
            "task_id": task_id,
            "platform": platform,
            "result_path": str(result_path),
            "saved_at": datetime.utcnow().isoformat(),
            "success": True,
        }

    except Exception as e:
        logger.error(f"[{task_id}] Save failed: {e}")
        return {
            "task_id": task_id,
            "success": False,
            "error": str(e),
        }


@app.task(bind=True)
def send_webhook(
    self,
    result: Dict[str, Any],
    webhook_url: Optional[str] = None,
    webhook_secret: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Send webhook notification.

    Args:
        result: Task result to send
        webhook_url: Webhook endpoint URL
        webhook_secret: HMAC secret for signing

    Returns:
        Dict with webhook status
    """
    import os
    webhook_url = webhook_url or os.getenv("WEBHOOK_URL")

    if not webhook_url:
        logger.debug("No webhook URL configured, skipping")
        return {"sent": False, "reason": "no_url"}

    task_id = result.get("task_id", self.request.id)
    logger.info(f"[{task_id}] Sending webhook")

    try:
        webhook_secret = webhook_secret or os.getenv("WEBHOOK_SECRET")
        client = WebhookClient(webhook_url, webhook_secret)

        success = client.send_sync(result)

        return {
            "task_id": task_id,
            "sent": success,
            "webhook_url": webhook_url,
        }

    except Exception as e:
        logger.error(f"[{task_id}] Webhook failed: {e}")
        return {"sent": False, "error": str(e)}


# ============================================================================
# Composite Tasks (Chains)
# ============================================================================

@app.task(bind=True)
def scrape_and_parse(
    self,
    url: str,
    platform: str,
    task_id: Optional[str] = None,
    priority: int = 3,
    save: bool = True,
    notify: bool = True,
) -> str:
    """
    Full pipeline: scrape → parse → save → webhook.

    Returns the task chain ID.
    """
    task_id = task_id or self.request.id
    queue = get_queue_for_priority(priority)

    # Build task chain
    workflow = chain(
        scrape_url.s(url, platform, task_id, priority).set(queue=queue),
        parse_html.s(),
    )

    if save:
        workflow = workflow | save_result.s()

    if notify:
        workflow = workflow | send_webhook.s()

    # Execute chain
    result = workflow.apply_async()

    return result.id


@app.task(bind=True)
def batch_scrape(
    self,
    urls: List[str],
    platform: str,
    priority: int = 3,
    save: bool = True,
) -> Dict[str, Any]:
    """
    Scrape multiple URLs in parallel.

    Args:
        urls: List of URLs to scrape
        platform: Platform name
        priority: Task priority
        save: Whether to save results

    Returns:
        Dict with batch status
    """
    queue = get_queue_for_priority(priority)

    # Create group of scrape+parse chains
    tasks = group(
        chain(
            scrape_url.s(url, platform, priority=priority).set(queue=queue),
            parse_html.s(),
            save_result.s() if save else None,
        )
        for url in urls
    )

    # Execute batch
    result = tasks.apply_async()

    return {
        "batch_id": self.request.id,
        "task_count": len(urls),
        "platform": platform,
        "group_id": result.id,
    }


# ============================================================================
# Discovery Tasks
# ============================================================================

@app.task(bind=True)
def process_discovered_links(
    self,
    parse_result: Dict[str, Any],
    max_depth: int = 2,
    current_depth: int = 0,
) -> Dict[str, Any]:
    """
    Process discovered links and queue them for scraping.

    Args:
        parse_result: Result containing discovered_links
        max_depth: Maximum crawl depth
        current_depth: Current depth level

    Returns:
        Dict with queued task info
    """
    if current_depth >= max_depth:
        return {"queued": 0, "reason": "max_depth_reached"}

    discovered = parse_result.get("discovered_links", [])
    if not discovered:
        return {"queued": 0, "reason": "no_links"}

    platform = parse_result["platform"]
    queued = 0

    for url in discovered:
        # Queue with lower priority (ripple effect)
        scrape_and_parse.apply_async(
            args=[url, platform],
            kwargs={
                "priority": 4,  # Low priority for discovered
                "save": True,
                "notify": False,
            },
            queue="low",
        )
        queued += 1

    return {
        "queued": queued,
        "depth": current_depth + 1,
        "platform": platform,
    }


# ============================================================================
# Bulk Tasks
# ============================================================================

@app.task(bind=True)
def bulk_import_urls(
    self,
    urls: List[str],
    platform: str,
    batch_size: int = 50,
    priority: int = 4,
) -> Dict[str, Any]:
    """
    Import bulk URLs for scraping.

    Args:
        urls: List of URLs
        platform: Platform name
        batch_size: URLs per batch
        priority: Task priority

    Returns:
        Dict with import status
    """
    total = len(urls)
    batches = [urls[i:i + batch_size] for i in range(0, total, batch_size)]

    for batch in batches:
        batch_scrape.apply_async(
            args=[batch, platform],
            kwargs={"priority": priority, "save": True},
            queue=get_queue_for_priority(priority),
        )

    return {
        "job_id": self.request.id,
        "total_urls": total,
        "batches": len(batches),
        "batch_size": batch_size,
        "platform": platform,
    }


# ============================================================================
# Utility Tasks
# ============================================================================

@app.task
def health_check() -> Dict[str, Any]:
    """Simple health check task."""
    return {
        "status": "ok",
        "timestamp": datetime.utcnow().isoformat(),
        "worker": "celery",
    }
