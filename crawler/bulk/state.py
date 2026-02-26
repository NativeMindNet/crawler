"""Ingestion state manager for resumability."""

import json
import pickle
from pathlib import Path
from typing import Dict, Any, Optional
import msgpack


class IngestionStateManager:
    """
    Manages state for bulk ingestion jobs.
    
    Supports multiple serialization formats:
    - JSON: Human-readable, portable
    - MessagePack: Compact binary
    - Pickle: Python-specific, complex objects
    """

    def __init__(self, state_dir: str):
        self.state_dir = Path(state_dir) / "bulk"
        self.state_dir.mkdir(parents=True, exist_ok=True)

    def get_state_path(self, job_id: str, format: str = "json") -> Path:
        """Get path for state file."""
        return self.state_dir / f"{job_id}_state.{format}"

    def save_state(
        self,
        job_id: str,
        state: Dict[str, Any],
        format: str = "json",
    ) -> str:
        """Save ingestion state."""
        path = self.get_state_path(job_id, format)

        if format == "json":
            with open(path, "w") as f:
                json.dump(state, f, indent=2, default=str)
        elif format == "msgpack":
            with open(path, "wb") as f:
                msgpack.pack(state, f)
        elif format == "pickle":
            with open(path, "wb") as f:
                pickle.dump(state, f)
        else:
            raise ValueError(f"Unknown format: {format}")

        return str(path)

    def load_state(
        self,
        job_id: str,
        format: str = "json",
    ) -> Optional[Dict[str, Any]]:
        """Load ingestion state."""
        path = self.get_state_path(job_id, format)

        if not path.exists():
            return None

        try:
            if format == "json":
                with open(path, "r") as f:
                    return json.load(f)
            elif format == "msgpack":
                with open(path, "rb") as f:
                    return msgpack.unpack(f)
            elif format == "pickle":
                with open(path, "rb") as f:
                    return pickle.load(f)
        except Exception as e:
            return None

        return None

    def save_checkpoint(
        self,
        job_id: str,
        processed_count: int,
        error_count: int,
        last_processed_id: Optional[str] = None,
        metadata: Optional[Dict] = None,
    ) -> str:
        """Save a checkpoint."""
        state = {
            "job_id": job_id,
            "processed_count": processed_count,
            "error_count": error_count,
            "last_processed_id": last_processed_id,
            "metadata": metadata or {},
        }
        return self.save_state(job_id, state)

    def delete_state(self, job_id: str) -> bool:
        """Delete state files for a job."""
        deleted = 0
        for format in ["json", "msgpack", "pickle"]:
            path = self.get_state_path(job_id, format)
            if path.exists():
                path.unlink()
                deleted += 1
        return deleted > 0

    def list_states(self) -> list:
        """List all state files."""
        return list(self.state_dir.glob("*_state.*"))
