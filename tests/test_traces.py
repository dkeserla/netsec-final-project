"""Tests for TraceLogger."""

import json
import tempfile
from pathlib import Path

from minpriv.schemas import TraceEvent, TraceEventType
from minpriv.traces import TraceLogger


def test_read_events_round_trip() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        logger = TraceLogger(run_id="test_rt", task_id="t01", out_dir=Path(tmp))

        logger.log(TraceEventType.MODEL_TURN_START, 1, {"model_name": "gpt-4"})
        logger.log(TraceEventType.TOOL_CALL, 1, {"tool_name": "read_file", "arguments": {"file_id": "f1"}})
        logger.log(TraceEventType.TOOL_RESULT, 1, {"tool_name": "read_file", "result": "ok"})
        logger.log(TraceEventType.FINAL_RESPONSE, 2, {"content": "done"})
        logger.log(TraceEventType.RUN_END, 2, {"reason": "success"})

        events = logger.read_events()

        assert len(events) == 5
        assert events[0].event_type == TraceEventType.MODEL_TURN_START
        assert events[0].step_index == 1
        assert events[0].run_id == "test_rt"
        assert events[0].task_id == "t01"
        assert events[1].event_type == TraceEventType.TOOL_CALL
        assert events[3].event_type == TraceEventType.FINAL_RESPONSE
        assert events[4].event_type == TraceEventType.RUN_END


def test_read_events_empty() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        logger = TraceLogger(run_id="test_empty", task_id="t01", out_dir=Path(tmp))
        events = logger.read_events()
        assert events == []


def test_read_events_closes_file_handle() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        logger = TraceLogger(run_id="test_close", task_id="t01", out_dir=Path(tmp))
        logger.log(TraceEventType.MODEL_TURN_START, 1, {})
        logger.read_events()
        assert logger._fh is None


def test_jsonl_file_persists_after_read() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        logger = TraceLogger(run_id="test_persist", task_id="t01", out_dir=Path(tmp))
        logger.log(TraceEventType.MODEL_TURN_START, 1, {"model_name": "gpt-4"})
        logger.read_events()

        trace_path = Path(tmp) / "test_persist.jsonl"
        assert trace_path.exists()
        lines = trace_path.read_text(encoding="utf-8").strip().splitlines()
        assert len(lines) == 1
        parsed = json.loads(lines[0])
        assert parsed["event_type"] == "model_turn_start"
        assert parsed["run_id"] == "test_persist"


def test_read_events_rejects_no_extra_args() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        logger = TraceLogger(run_id="test_noargs", task_id="t01", out_dir=Path(tmp))
        logger.log(TraceEventType.RUN_END, 1, {"reason": "success"})
        events = logger.read_events()
        assert len(events) == 1
        assert events[0].payload["reason"] == "success"


def test_logged_events_match_read_events() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        logger = TraceLogger(run_id="test_match", task_id="t01", out_dir=Path(tmp))

        logger.log(TraceEventType.MODEL_TURN_START, 1, {"model_name": "m"})
        logger.log(TraceEventType.TOOL_CALL, 1, {"tool_name": "t1"})

        events = logger.read_events()

        assert len(events) == 2
        assert events[0].step_index == events[1].step_index == 1
        assert events[0].run_id == events[1].run_id == "test_match"
        assert events[0].task_id == events[1].task_id == "t01"
