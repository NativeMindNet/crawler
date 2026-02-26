"""Upsert handler for idempotent data insertion."""

from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime


class UpsertHandler:
    """
    Handles idempotent upsert operations.
    
    Features:
    - Duplicate detection
    - Conflict resolution
    - Batch upsert
    """

    def __init__(self, idempotent_key: List[str]):
        """
        Initialize upsert handler.
        
        Args:
            idempotent_key: Fields that uniquely identify a record
        """
        self.idempotent_key = idempotent_key

    def compute_key(self, row: Dict[str, Any]) -> str:
        """
        Compute unique key for a row.
        
        Args:
            row: Row dict
        
        Returns:
            Unique key string
        """
        key_parts = []
        for field in self.idempotent_key:
            value = row.get(field, "")
            key_parts.append(str(value))

        return "|".join(key_parts)

    def upsert(
        self,
        existing: Dict[str, Any],
        new: Dict[str, Any],
        strategy: str = "replace",
    ) -> Dict[str, Any]:
        """
        Perform upsert operation.
        
        Args:
            existing: Existing record (or empty dict)
            new: New record
            strategy: "replace" or "merge"
        
        Returns:
            Resulting record
        """
        if not existing:
            return new.copy()

        if strategy == "replace":
            return new.copy()

        elif strategy == "merge":
            result = existing.copy()
            result.update(new)
            return result

        else:
            raise ValueError(f"Unknown strategy: {strategy}")

    def validate_key(self, row: Dict[str, Any]) -> Tuple[bool, Optional[str]]:
        """
        Validate that idempotent key fields are present.
        
        Args:
            row: Row dict
        
        Returns:
            Tuple of (is_valid, error message)
        """
        missing = []
        for field in self.idempotent_key:
            if field not in row or row[field] is None or row[field] == "":
                missing.append(field)

        if missing:
            return False, f"Missing idempotent key fields: {missing}"

        return True, None

    def batch_upsert(
        self,
        existing_records: Dict[str, Dict[str, Any]],
        new_records: List[Dict[str, Any]],
        strategy: str = "replace",
    ) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
        """
        Batch upsert operation.
        
        Args:
            existing_records: Dict of key -> existing record
            new_records: List of new records
            strategy: Upsert strategy
        
        Returns:
            Tuple of (inserted, updated) lists
        """
        inserted = []
        updated = []

        for new_row in new_records:
            key = self.compute_key(new_row)
            existing = existing_records.get(key)

            result = self.upsert(existing, new_row, strategy)

            if existing:
                updated.append(result)
            else:
                inserted.append(result)

        return inserted, updated

    def detect_duplicates(
        self,
        records: List[Dict[str, Any]],
    ) -> Dict[str, List[Dict[str, Any]]]:
        """
        Detect duplicates within a list of records.
        
        Args:
            records: List of records
        
        Returns:
            Dict of key -> list of duplicate records
        """
        by_key = {}

        for record in records:
            key = self.compute_key(record)
            if key not in by_key:
                by_key[key] = []
            by_key[key].append(record)

        # Return only keys with duplicates
        return {k: v for k, v in by_key.items() if len(v) > 1}
