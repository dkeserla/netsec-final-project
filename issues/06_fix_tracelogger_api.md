# Issue: Fix TraceLogger-return API for in-memory scoring

## Objective
Eliminate the need for the CLI to re-read trace JSONL from disk immediately after `runner.execute()` finishes.

## Problem
Currently `AgentRunner.execute()` returns a `TraceLogger`, but `score_run()` expects `list[TraceEvent]`. The caller must:
1. Know the trace file path from the logger internals
2. Call `load_trace(path)` to read it back from disk

This is awkward and brittle. The runner should either:
- Return the list of events directly (in addition to logging to disk), or
- Expose a helper on `TraceLogger` to read back its own events

## Proposed Solutions (choose one)

### Option A: Return events alongside logger
Change `AgentRunner.execute()` signature or return type:
```python
def execute(self, task: TaskSpec) -> tuple[TraceLogger, list[TraceEvent]]:
    ...
```
This lets `cli.py` call `score_run(events, task, ...)` without file I/O.

### Option B: Add `read_events()` to `TraceLogger`
Add a method on `TraceLogger`:
```python
def read_events(self) -> list[TraceEvent]:
    self.close()
    return load_trace(str(self._path()))
```
This keeps the runner return type simple while still allowing in-memory scoring.

## Acceptance Criteria
- The CLI (or any caller) can run a task and score it without manually constructing a file path
- All existing trace JSONL writes still happen

## Files to Modify
- `minpriv/traces.py` (add `read_events()` or similar)
- `minpriv/runner.py` (if Option A is chosen)
