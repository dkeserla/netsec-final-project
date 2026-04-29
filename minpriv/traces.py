"""Trace logging utilities."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from minpriv.schemas import TraceEvent, TraceEventType


def load_trace(path: Path | str) -> list[TraceEvent]:
    events: list[TraceEvent] = []
    p = Path(path)
    if not p.exists():
        return []
    for line in p.read_text(encoding="utf-8").strip().splitlines():
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
        self._events: list[TraceEvent] = []

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
        self._events.append(event)
        self._file().write(event.model_dump_json() + "\n")
        self._file().flush()

    def close(self) -> None:
        if self._fh:
            self._fh.close()
            self._fh = None

    def read_events(self) -> list[TraceEvent]:
        if self._events:
            return list(self._events)
        return load_trace(self._path())
