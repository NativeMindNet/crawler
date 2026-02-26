"""Bulk ingestion module."""

from crawler.bulk.pipeline import BulkIngestionPipeline
from crawler.bulk.transformer import BulkTransformer
from crawler.bulk.state import IngestionStateManager
from crawler.bulk.upsert import UpsertHandler
from crawler.bulk.readers.base import SourceReader
from crawler.bulk.readers.csv_reader import CSVReader
from crawler.bulk.readers.excel_reader import ExcelReader
from crawler.bulk.readers.json_reader import JSONReader

__all__ = [
    "BulkIngestionPipeline",
    "BulkTransformer",
    "IngestionStateManager",
    "UpsertHandler",
    "SourceReader",
    "CSVReader",
    "ExcelReader",
    "JSONReader",
]
