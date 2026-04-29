"""Trace logging utilities."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from minpriv.schemas import TraceEvent, TraceEventType


def _read_jsonl(path: Path) -> list[TraceEvent]:
    events: list[TraceEvent] = []
    for line in path.read_text(encoding="utf-8").strip().splitlines():
        if line:
            events.append(TraceEvent.model_validate_json(line))
    return events


class TraceLogger:
    def __init__(self, run_id: str, task_id: str, out_dir: Path):
        self.run_id = run_id
        self.task_id = task_id
        self.out_dir = out_dir
        self.out_dir.mkdir(parents=True, exist_ok=True)
        self._fh = None

    def _path(self) -> Path:
        return self.out_dir / f"{self.run_id}.jsonl"

    def _file(self):
        if self._fh is None:
            self._fh = open(self._path(), "a", encoding="utf-8")
        return self._fh

    def log(self, event_type: TraceEventType, step_index: int, payload: dict[str, Any]) -> None:
        event = TraceEvent(
            event_type=event_type,
            run_id=self.run_id,
            task_id=self.task_id,
            step_index=step_index,
            payload=payload,
        )
        self._file().write(event.model_dump_json() + "\n")
        self._file().flush()

    def close(self) -> None:
        if self._fh:
            self._fh.close()
            self._fh = None

    def read_events(self) -> list[TraceEvent]:
        self.close()
        if self._path().exists():
            return _read_jsonl(self._path())
        return []
