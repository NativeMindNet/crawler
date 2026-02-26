"""State serialization utilities."""

import json
from pathlib import Path
from typing import Any, Optional
from dataclasses import dataclass, asdict
from datetime import datetime


@dataclass
class CheckpointState:
    """Represents a checkpoint state for resumability."""
    checkpoint_id: str
    timestamp: str
    task_id: Optional[str]
    job_id: Optional[str]
    processed_count: int
    error_count: int
    metadata: dict

    @classmethod
    def create(
        cls,
        checkpoint_id: str,
        task_id: Optional[str] = None,
        job_id: Optional[str] = None,
        processed_count: int = 0,
        error_count: int = 0,
        metadata: Optional[dict] = None,
    ) -> "CheckpointState":
        """Create a new checkpoint."""
        return cls(
            checkpoint_id=checkpoint_id,
            timestamp=datetime.utcnow().isoformat(),
            task_id=task_id,
            job_id=job_id,
            processed_count=processed_count,
            error_count=error_count,
            metadata=metadata or {},
        )


class StateSerializer:
    """
    Handles state serialization in multiple formats.
    
    Supported formats:
    - JSON: Human-readable, portable
    - MessagePack: Compact binary, fast
    - Pickle: Python-specific, supports complex objects
    """

    def __init__(self, state_dir: str):
        self.state_dir = Path(state_dir)
        self.state_dir.mkdir(parents=True, exist_ok=True)

    def get_path(self, name: str, format: str) -> Path:
        """Get state file path."""
        return self.state_dir / f"{name}.{format}"

    def save_json(self, name: str, data: Any) -> Path:
        """Save state as JSON."""
        path = self.get_path(name, "json")
        with open(path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, default=str, ensure_ascii=False)
        return path

    def load_json(self, name: str) -> Optional[Any]:
        """Load state from JSON."""
        path = self.get_path(name, "json")
        if not path.exists():
            return None

        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)

    def save_msgpack(self, name: str, data: Any) -> Path:
        """Save state as MessagePack."""
        import msgpack

        path = self.get_path(name, "msgpack")
        with open(path, "wb") as f:
            msgpack.pack(data, f)
        return path

    def load_msgpack(self, name: str) -> Optional[Any]:
        """Load state from MessagePack."""
        import msgpack

        path = self.get_path(name, "msgpack")
        if not path.exists():
            return None

        with open(path, "rb") as f:
            return msgpack.unpack(f)

    def save_pickle(self, name: str, data: Any) -> Path:
        """Save state as Pickle."""
        import pickle

        path = self.get_path(name, "pickle")
        with open(path, "wb") as f:
            pickle.dump(data, f)
        return path

    def load_pickle(self, name: str) -> Optional[Any]:
        """Load state from Pickle."""
        import pickle

        path = self.get_path(name, "pickle")
        if not path.exists():
            return None

        with open(path, "rb") as f:
            return pickle.load(f)

    def save_checkpoint(self, checkpoint: CheckpointState) -> Path:
        """Save checkpoint state."""
        return self.save_json(f"checkpoint_{checkpoint.checkpoint_id}", asdict(checkpoint))

    def load_checkpoint(self, checkpoint_id: str) -> Optional[CheckpointState]:
        """Load checkpoint state."""
        data = self.load_json(f"checkpoint_{checkpoint_id}")
        if data is None:
            return None

        return CheckpointState(**data)

    def get_latest_checkpoint(self, prefix: str = "checkpoint_") -> Optional[CheckpointState]:
        """Get the most recent checkpoint."""
        checkpoints = []
        for path in self.state_dir.glob(f"{prefix}*.json"):
            try:
                data = json.loads(path.read_text(encoding="utf-8"))
                checkpoints.append(CheckpointState(**data))
            except (json.JSONDecodeError, KeyError):
                continue

        if not checkpoints:
            return None

        # Sort by timestamp descending
        checkpoints.sort(key=lambda c: c.timestamp, reverse=True)
        return checkpoints[0]

    def delete_checkpoint(self, checkpoint_id: str) -> bool:
        """Delete a checkpoint."""
        path = self.get_path(f"checkpoint_{checkpoint_id}", "json")
        if path.exists():
            path.unlink()
            return True
        return False

    def cleanup_old_checkpoints(self, keep_count: int = 5) -> int:
        """
        Remove old checkpoints, keeping only the most recent ones.
        
        Returns count of deleted checkpoints.
        """
        checkpoints = []
        for path in self.state_dir.glob("checkpoint_*.json"):
            try:
                data = json.loads(path.read_text(encoding="utf-8"))
                checkpoints.append((path, data.get("timestamp", "")))
            except (json.JSONDecodeError, KeyError):
                checkpoints.append((path, ""))

        if len(checkpoints) <= keep_count:
            return 0

        # Sort by timestamp descending
        checkpoints.sort(key=lambda c: c[1], reverse=True)

        # Delete old ones
        deleted = 0
        for path, _ in checkpoints[keep_count:]:
            path.unlink()
            deleted += 1

        return deleted
