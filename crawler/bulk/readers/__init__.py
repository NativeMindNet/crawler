"""Bulk readers package."""

from crawler.bulk.readers.base import SourceReader
from crawler.bulk.readers.csv_reader import CSVReader
from crawler.bulk.readers.excel_reader import ExcelReader
from crawler.bulk.readers.json_reader import JSONReader

__all__ = [
    "SourceReader",
    "CSVReader",
    "ExcelReader",
    "JSONReader",
]
