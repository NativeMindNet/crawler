"""Worker CLI commands."""

import asyncio
from typing import Optional

from crawler.lpm import LocalPersistenceManager
from crawler.config_loader import ConfigLoader
from crawler.worker import Worker


async def worker_run_command(
    platform: str,
    db_path: str,
    data_dir: str,
    config_dir: str,
    max_retries: int,
) -> None:
    """Start processing the task queue."""
    # Load config
    config_loader = ConfigLoader(config_dir)
    config = config_loader.load(platform)

    if not config:
        print(f"Error: Platform '{platform}' not found in {config_dir}")
        return

    # Initialize LPM
    lpm = LocalPersistenceManager(db_path, data_dir)
    await lpm.initialize()

    # Create and run worker
    worker = Worker(lpm, config, max_retries=max_retries)

    print(f"Starting worker for platform: {platform}")
    print(f"Database: {db_path}")
    print(f"Data dir: {data_dir}")
    print(f"Max retries: {max_retries}")
    print("Press Ctrl+C to stop")
    print()

    try:
        await worker.run()
    except KeyboardInterrupt:
        print("\nStopping worker...")
    finally:
        await lpm.close()


async def worker_resume_command(
    platform: str,
    db_path: str,
    data_dir: str,
    config_dir: str,
) -> None:
    """Resume processing from last checkpoint."""
    # Load config
    config_loader = ConfigLoader(config_dir)
    config = config_loader.load(platform)

    if not config:
        print(f"Error: Platform '{platform}' not found in {config_dir}")
        return

    # Initialize LPM
    lpm = LocalPersistenceManager(db_path, data_dir)
    await lpm.initialize()

    # Load last checkpoint
    from crawler.state import StateSerializer
    serializer = StateSerializer(f"{data_dir}/state")
    checkpoint = serializer.get_latest_checkpoint()

    if checkpoint:
        print(f"Resuming from checkpoint: {checkpoint.checkpoint_id}")
        print(f"  Timestamp: {checkpoint.timestamp}")
        print(f"  Processed: {checkpoint.processed_count}")
        print(f"  Errors: {checkpoint.error_count}")
    else:
        print("No checkpoint found, starting fresh")

    # Create and run worker
    worker = Worker(lpm, config)

    try:
        await worker.run()
    except KeyboardInterrupt:
        print("\nStopping worker...")
    finally:
        await lpm.close()


async def worker_drain_command(
    platform: str,
    db_path: str,
    data_dir: str,
    config_dir: str,
) -> None:
    """Process all pending tasks and exit."""
    # Load config
    config_loader = ConfigLoader(config_dir)
    config = config_loader.load(platform)

    if not config:
        print(f"Error: Platform '{platform}' not found in {config_dir}")
        return

    # Initialize LPM
    lpm = LocalPersistenceManager(db_path, data_dir)
    await lpm.initialize()

    # Get queue depth
    depth = await lpm.get_queue_depth()
    print(f"Pending tasks: {depth}")

    if depth == 0:
        print("No pending tasks to process")
        await lpm.close()
        return

    # Create and run worker
    worker = Worker(lpm, config, drain_mode=True)

    print(f"Draining queue ({depth} tasks)...")

    try:
        await worker.run()
        print("\n✓ Queue drained")
    except KeyboardInterrupt:
        print("\nStopping worker...")
    finally:
        await lpm.close()
