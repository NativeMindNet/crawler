"""Base class for source readers."""

from abc import ABC, abstractmethod
from pathlib import Path
from typing import Iterator, Dict, Any, Optional


class SourceReader(ABC):
    """
    Abstract base class for bulk ingestion source readers.
    
    Implementations:
    - CSVReader
    - ExcelReader
    - GISReader (Shapefile/GeoJSON)
    - JSONReader
    """

    def __init__(self, file_path: str):
        self.file_path = Path(file_path)
        if not self.file_path.exists():
            raise FileNotFoundError(f"Source file not found: {file_path}")

    @abstractmethod
    def get_row_count(self) -> int:
        """Get total row count (excluding header)."""
        pass

    @abstractmethod
    def read_rows(self, batch_size: int = 100) -> Iterator[Dict[str, Any]]:
        """
        Read rows from source file.
        
        Args:
            batch_size: Number of rows to read at a time
        
        Yields:
            Dict representing each row
        """
        pass

    @abstractmethod
    def get_columns(self) -> list:
        """Get column names from source."""
        pass

    def validate(self) -> tuple[bool, list]:
        """
        Validate source file.
        
        Returns:
            Tuple of (is_valid, list of errors)
        """
        errors = []

        try:
            # Try to read first row
            rows = list(self.read_rows(batch_size=1))
            if not rows:
                errors.append("Source file is empty")
        except Exception as e:
            errors.append(f"Failed to read source: {e}")

        return len(errors) == 0, errors

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        pass
