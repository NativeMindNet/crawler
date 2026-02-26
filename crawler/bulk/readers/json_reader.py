"""JSON/JSONL source reader."""

import json
from pathlib import Path
from typing import Iterator, Dict, Any, List, Union

from crawler.bulk.readers.base import SourceReader


class JSONReader(SourceReader):
    """
    Reader for JSON and JSONL files.
    
    Supports:
    - JSON array: [{...}, {...}]
    - JSONL: One JSON object per line
    - Nested JSON with flattening
    """

    def __init__(
        self,
        file_path: str,
        format: str = "auto",
        flatten: bool = False,
    ):
        super().__init__(file_path)
        self.format = format  # "json", "jsonl", "auto"
        self.flatten = flatten
        self._detected_format: str = ""
        self._row_count: int = 0

    def _detect_format(self) -> str:
        """Detect JSON format by reading file."""
        if self.format != "auto":
            return self.format

        with open(self.file_path, "r") as f:
            first_line = f.readline().strip()

            if first_line.startswith("{"):
                self._detected_format = "jsonl"
            elif first_line.startswith("["):
                self._detected_format = "json"
            else:
                # Try to parse as JSON
                try:
                    json.loads(first_line)
                    self._detected_format = "jsonl"
                except:
                    self._detected_format = "json"

        return self._detected_format

    def get_row_count(self) -> int:
        """Count rows in JSON file."""
        if self._row_count > 0:
            return self._row_count

        fmt = self._detect_format()

        if fmt == "jsonl":
            with open(self.file_path, "r") as f:
                self._row_count = sum(1 for _ in f)
        else:
            # JSON array
            data = self._load_json()
            if isinstance(data, list):
                self._row_count = len(data)
            else:
                self._row_count = 1

        return self._row_count

    def _load_json(self) -> Union[Dict, List]:
        """Load entire JSON file."""
        with open(self.file_path, "r") as f:
            return json.load(f)

    def read_rows(self, batch_size: int = 100) -> Iterator[Dict[str, Any]]:
        """Read rows from JSON."""
        fmt = self._detect_format()

        if fmt == "jsonl":
            yield from self._read_jsonl(batch_size)
        else:
            yield from self._read_json_array(batch_size)

    def _read_jsonl(self, batch_size: int) -> Iterator[Dict[str, Any]]:
        """Read JSONL file."""
        batch = []

        with open(self.file_path, "r") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue

                try:
                    obj = json.loads(line)
                    if self.flatten:
                        obj = self._flatten_dict(obj)
                    batch.append(obj)

                    if len(batch) >= batch_size:
                        yield from batch
                        batch = []

                except json.JSONDecodeError:
                    continue

        if batch:
            yield from batch

    def _read_json_array(self, batch_size: int) -> Iterator[Dict[str, Any]]:
        """Read JSON array file."""
        data = self._load_json()

        if not isinstance(data, list):
            data = [data]

        batch = []
        for item in data:
            if self.flatten and isinstance(item, dict):
                item = self._flatten_dict(item)
            batch.append(item)

            if len(batch) >= batch_size:
                yield from batch
                batch = []

        if batch:
            yield from batch

    def _flatten_dict(self, d: Dict, parent_key: str = "", sep: str = ".") -> Dict:
        """Flatten nested dictionary."""
        items = []
        for k, v in d.items():
            new_key = f"{parent_key}{sep}{k}" if parent_key else k
            if isinstance(v, dict):
                items.extend(self._flatten_dict(v, new_key, sep).items())
            else:
                items.append((new_key, v))
        return dict(items)

    def get_columns(self) -> List[str]:
        """Get column names from first row."""
        rows = list(self.read_rows(batch_size=1))
        if rows:
            return list(rows[0].keys())
        return []

    def validate(self) -> tuple[bool, list]:
        """Validate JSON file."""
        errors = []

        try:
            # Check can parse
            fmt = self._detect_format()

            if fmt == "jsonl":
                # Validate first line
                with open(self.file_path, "r") as f:
                    first_line = f.readline()
                    json.loads(first_line)
            else:
                # Validate entire file
                self._load_json()

            # Check has data
            if self.get_row_count() == 0:
                errors.append("JSON file has no data")

        except json.JSONDecodeError as e:
            errors.append(f"Invalid JSON: {e}")
        except Exception as e:
            errors.append(f"Failed to read JSON: {e}")

        return len(errors) == 0, errors
