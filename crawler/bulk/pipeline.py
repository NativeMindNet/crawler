"""Bulk ingestion pipeline."""

import asyncio
import logging
from pathlib import Path
from typing import Optional, Dict, Any
import uuid

from crawler.lpm import LocalPersistenceManager
from crawler.bulk.readers.base import SourceReader
from crawler.bulk.readers.csv_reader import CSVReader
from crawler.bulk.readers.excel_reader import ExcelReader
from crawler.bulk.readers.json_reader import JSONReader
from crawler.bulk.transformer import BulkTransformer
from crawler.bulk.state import IngestionStateManager
from crawler.bulk.upsert import UpsertHandler

logger = logging.getLogger(__name__)


class BulkIngestionPipeline:
    """
    Pipeline for bulk data ingestion.
    
    Features:
    - Multi-format support (CSV, Excel, JSON)
    - Streaming for large files
    - Resumable ingestion
    - Progress tracking
    - Error handling
    """

    def __init__(self, lpm: LocalPersistenceManager, platform: str):
        self.lpm = lpm
        self.platform = platform
        self.state_manager = IngestionStateManager(lpm.data_dir)

    async def ingest(
        self,
        file_path: str,
        profile_name: str,
        batch_size: int = 100,
    ) -> str:
        """
        Start bulk ingestion.
        
        Args:
            file_path: Path to source file
            profile_name: Mapping profile name
            batch_size: Rows per batch
        
        Returns:
            Job ID
        """
        job_id = str(uuid.uuid4())
        logger.info(f"Starting bulk ingestion: {job_id}")

        # Create job record
        await self.lpm.create_bulk_job(file_path, profile_name, job_id=job_id)

        try:
            # Get reader for file type
            reader = self._get_reader(file_path)
            total_rows = reader.get_row_count()

            logger.info(f"Source: {total_rows} rows")

            # Update job with total
            job = await self.lpm.get_bulk_job(job_id)
            job.total_rows = total_rows
            await self.lpm.bulk_job_repo.update(job)

            # Create transformer
            transformer = BulkTransformer(profile_name)

            # Process batches
            processed = 0
            errors = 0

            for batch in reader.read_rows(batch_size):
                try:
                    # Transform batch
                    transformed = transformer.transform_batch(batch)

                    # Upsert each row
                    for row in transformed:
                        try:
                            await self._upsert_row(row)
                            processed += 1
                        except Exception as e:
                            logger.error(f"Upsert failed: {e}")
                            errors += 1

                    # Update progress
                    await self.lpm.update_bulk_progress(job_id, processed, errors)

                except Exception as e:
                    logger.error(f"Batch processing failed: {e}")
                    errors += len(batch)
                    await self.lpm.update_bulk_progress(job_id, processed, errors)

            # Complete job
            await self.lpm.complete_bulk_job(job_id)
            logger.info(f"Bulk ingestion complete: {processed} rows, {errors} errors")

        except Exception as e:
            logger.error(f"Bulk ingestion failed: {e}")
            await self.lpm.fail_bulk_job(job_id)
            raise

        return job_id

    def _get_reader(self, file_path: str) -> SourceReader:
        """Get appropriate reader for file type."""
        path = Path(file_path)
        ext = path.suffix.lower()

        if ext == ".csv":
            return CSVReader(file_path)
        elif ext in [".xlsx", ".xls"]:
            return ExcelReader(file_path)
        elif ext in [".json", ".jsonl"]:
            return JSONReader(file_path)
        else:
            # Try CSV as default
            return CSVReader(file_path)

    async def _upsert_row(self, row: Dict[str, Any]) -> None:
        """Upsert a single row to database."""
        # This would insert into a parcels/properties table
        # For now, just save as JSON result
        parcel_id = row.get("parcel_id", str(uuid.uuid4()))
        task_id = f"bulk_{parcel_id}"

        await self.lpm.save_result(task_id, self.platform, row)

    async def resume(self, job_id: str) -> str:
        """Resume interrupted ingestion job."""
        job = await self.lpm.get_bulk_job(job_id)

        if not job:
            raise ValueError(f"Job not found: {job_id}")

        if job.status.value == "completed":
            logger.info(f"Job {job_id} already completed")
            return job_id

        # Load state
        state = await self.state_manager.load_state(job_id)
        if state:
            logger.info(f"Resuming from state: {state}")

        # Re-run ingestion (would be smarter in production)
        return await self.ingest(job.source_file, job.profile_id)

    async def get_status(self, job_id: str) -> Optional[Dict[str, Any]]:
        """Get job status and progress."""
        job = await self.lpm.get_bulk_job(job_id)

        if not job:
            return None

        return job.to_dict()
