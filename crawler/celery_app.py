"""Celery application configuration for parallel task processing."""

import os
from celery import Celery
from kombu import Queue

# Redis URL from environment or default
REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")

# Create Celery app
app = Celery(
    "crawler",
    broker=REDIS_URL,
    backend=REDIS_URL,
    include=["crawler.tasks"],
)

# Celery configuration
app.conf.update(
    # Serialization
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",

    # Timezone
    timezone="UTC",
    enable_utc=True,

    # Task execution
    task_acks_late=True,  # Acknowledge after task completes
    task_reject_on_worker_lost=True,  # Requeue if worker dies
    worker_prefetch_multiplier=1,  # One task at a time per worker

    # Results
    result_expires=3600,  # Results expire in 1 hour

    # Events for Flower monitoring
    worker_send_task_events=True,
    task_send_sent_event=True,

    # Retry policy
    task_default_retry_delay=30,
    task_max_retries=3,

    # Task routing (priority queues)
    task_queues=(
        Queue("urgent", routing_key="urgent"),
        Queue("high", routing_key="high"),
        Queue("default", routing_key="default"),
        Queue("low", routing_key="low"),
    ),
    task_default_queue="default",
    task_default_routing_key="default",

    # Rate limiting (per worker)
    task_annotations={
        "crawler.tasks.scrape_url": {
            "rate_limit": "10/m",  # 10 tasks per minute
        },
    },

    # Concurrency
    worker_concurrency=4,  # Default, can override via CLI
)


def get_celery_app() -> Celery:
    """Get configured Celery application."""
    return app


# Task priority mapping
PRIORITY_QUEUES = {
    1: "urgent",   # User viewing parcel
    2: "high",     # Graph exploration
    3: "default",  # Background refresh
    4: "low",      # Batch crawling
}


def get_queue_for_priority(priority: int) -> str:
    """Map priority level to queue name."""
    return PRIORITY_QUEUES.get(priority, "default")
