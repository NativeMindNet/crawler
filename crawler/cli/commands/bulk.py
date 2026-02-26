"""Bulk CLI commands."""

from pathlib import Path

from crawler.lpm import LocalPersistenceManager
from crawler.bulk.pipeline import BulkIngestionPipeline


async def bulk_ingest_command(
    file: Path,
    profile: str,
    platform: str,
) -> None:
    """Start bulk ingestion."""
    import os

    db_path = os.environ.get("DB_PATH", "/data/state/crawler.db")
    data_dir = os.environ.get("DATA_DIR", "/data")

    if not file.exists():
        print(f"Error: File not found: {file}")
        return

    # Initialize LPM
    lpm = LocalPersistenceManager(db_path, data_dir)
    await lpm.initialize()

    try:
        # Create pipeline
        pipeline = BulkIngestionPipeline(lpm, platform)

        # Start ingestion
        print(f"Starting bulk ingestion...")
        print(f"  File: {file}")
        print(f"  Profile: {profile}")
        print(f"  Platform: {platform}")

        job_id = await pipeline.ingest(str(file), profile)
        print(f"\n✓ Ingestion started: {job_id}")

    finally:
        await lpm.close()


async def bulk_status_command(
    job_id: str,
    db_path: str,
) -> None:
    """Get bulk job status."""
    lpm = LocalPersistenceManager(db_path, "/data")
    await lpm.initialize()

    try:
        job = await lpm.get_bulk_job(job_id)

        if not job:
            print(f"✗ Job not found: {job_id}")
            return

        print(f"Job: {job_id}")
        print(f"  Status: {job.status.value}")
        print(f"  Source: {job.source_file}")
        print(f"  Profile: {job.profile_id}")
        print(f"  Progress: {job.processed_rows}/{job.total_rows} ({job.progress_percent:.1f}%)")
        print(f"  Errors: {job.error_rows}")
        if job.completed_at:
            print(f"  Completed: {job.completed_at}")
    finally:
        await lpm.close()
