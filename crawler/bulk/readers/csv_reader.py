"""CSV source reader."""

import csv
from pathlib import Path
from typing import Iterator, Dict, Any, List

from crawler.bulk.readers.base import SourceReader


class CSVReader(SourceReader):
    """
    Reader for CSV files.
    
    Features:
    - Streaming for large files
    - Custom delimiter support
    - Encoding handling
    """

    def __init__(
        self,
        file_path: str,
        delimiter: str = ",",
        encoding: str = "utf-8",
        has_header: bool = True,
    ):
        super().__init__(file_path)
        self.delimiter = delimiter
        self.encoding = encoding
        self.has_header = has_header
        self._column_count = 0

    def get_row_count(self) -> int:
        """Count rows in CSV."""
        count = 0
        with open(self.file_path, "r", encoding=self.encoding) as f:
            reader = csv.reader(f, delimiter=self.delimiter)
            if self.has_header:
                next(reader, None)
            for _ in reader:
                count += 1
        return count

    def read_rows(self, batch_size: int = 100) -> Iterator[Dict[str, Any]]:
        """Read rows from CSV."""
        with open(self.file_path, "r", encoding=self.encoding) as f:
            reader = csv.DictReader(f, delimiter=self.delimiter)
            batch = []

            for row in reader:
                batch.append(row)
                if len(batch) >= batch_size:
                    yield from batch
                    batch = []

            if batch:
                yield from batch

    def get_columns(self) -> List[str]:
        """Get column names from CSV header."""
        with open(self.file_path, "r", encoding=self.encoding) as f:
            reader = csv.reader(f, delimiter=self.delimiter)
            header = next(reader)
            return header

    def validate(self) -> tuple[bool, list]:
        """Validate CSV file."""
        errors = []

        try:
            # Check file exists
            if not self.file_path.exists():
                errors.append("File not found")
                return False, errors

            # Check can read header
            columns = self.get_columns()
            if not columns:
                errors.append("CSV file is empty or has no header")

            # Check can read first data row
            rows = list(self.read_rows(batch_size=1))
            if not rows:
                errors.append("CSV file has no data rows")

            # Check consistent column count
            self._column_count = len(columns)
            for i, row in enumerate(self.read_rows(batch_size=10)):
                if len(row) != self._column_count:
                    errors.append(f"Row {i + 1} has inconsistent column count")
                    break

        except Exception as e:
            errors.append(f"Failed to read CSV: {e}")

        return len(errors) == 0, errors
