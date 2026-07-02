"""Atomic JSON persistence for sent vacancy IDs."""

from __future__ import annotations

import json
import os
import tempfile
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from .exceptions import StorageError


class SeenJobStore:
    """Read and atomically update the repository-backed state file."""

    def __init__(self, path: Path) -> None:
        self.path = path
        self._data = self._load()

    def _load(self) -> dict[str, Any]:
        if not self.path.exists():
            return {"version": 1, "jobs": {}}
        try:
            data = json.loads(self.path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as exc:
            raise StorageError(f"Cannot read state file {self.path}: {exc}") from exc
        if not isinstance(data, dict) or data.get("version") != 1 or not isinstance(data.get("jobs"), dict):
            raise StorageError(f"State file {self.path} has an invalid schema")
        return data

    def contains(self, job_id: str) -> bool:
        return job_id in self._data["jobs"]

    def mark_sent(self, job_id: str, title: str) -> None:
        self._data["jobs"][job_id] = {
            "title": title,
            "emailed_at": datetime.now(timezone.utc).isoformat(),
        }
        self._save()

    def _save(self) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        try:
            descriptor, temporary = tempfile.mkstemp(
                prefix=f".{self.path.name}.", dir=self.path.parent, text=True
            )
            with os.fdopen(descriptor, "w", encoding="utf-8") as handle:
                json.dump(self._data, handle, indent=2, sort_keys=True)
                handle.write("\n")
                handle.flush()
                os.fsync(handle.fileno())
            os.replace(temporary, self.path)
        except OSError as exc:
            raise StorageError(f"Cannot update state file {self.path}: {exc}") from exc
