"""Models package."""

from crawler.models.task import Task, TaskStatus
from crawler.models.scraped_content import ScrapedContent
from crawler.models.parsed_result import ParsedResult, DiscoveredLink
from crawler.models.bulk_job import BulkJob, BulkJobStatus
from crawler.models.ingestion_job import IngestionJob, IngestionJobStatus
from crawler.models.mapping_profile import MappingProfile
from crawler.models.external_links import ExternalLinks

__all__ = [
    "Task",
    "TaskStatus",
    "ScrapedContent",
    "ParsedResult",
    "DiscoveredLink",
    "BulkJob",
    "BulkJobStatus",
    "IngestionJob",
    "IngestionJobStatus",
    "MappingProfile",
    "ExternalLinks",
]
