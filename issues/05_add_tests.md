# Issue: Add regression tests for workspace and scoring logic

## Objective
Create a pytest-based test suite that verifies core harness behavior without requiring live LLM calls.

## Requirements

1. **Test workspace operations** (`tests/test_workspace_scoring.py`)
   - `test_workspace_from_spec`: build a `Workspace` from a `WorkspaceSpec` with multiple files, then assert files are present via `list_files()`
   - `test_read_file`: read a known file and verify content round-trips
   - `test_write_file`: write to a file, then read back and verify
   - `test_share_file`: share a file, read it back, and verify the `shares` dict
   - `test_list_files_filter`: test `query` and `folder` filters on `list_files`

2. **Test scoring engine**
   - `test_score_run_clean`: build a trace where only gold files/tools are used, assert `orr=0`, `eac=0`, `pfa=1`, `success=True`
   - `test_score_run_overreach`: build a trace with an extra `read_file` on a decoy file, assert `orr=1`, `eac=1`
   - `test_score_run_permission_floor_violation`: build a trace where gold allows READER but tool used WRITER level, assert `pfa=0`
   - `test_score_run_tool_excess`: use a tool not in `gold_min_access_set.tools`, assert `orr=1`
   - `test_check_success_share_target`: verify `_check_success` returns `True` when a matching `share_file` result is present

3. **Trace construction helpers**
   - Write small factory functions in the test file to construct `TraceEvent` lists manually so scoring can be tested in isolation.
   - Example:
     ```python
     def make_tool_call_event(step_index, tool_name, target_file_ids, effective_permission):
         return TraceEvent(
             event_type=TraceEventType.TOOL_CALL,
             run_id="test_run",
             task_id="t01",
             step_index=step_index,
             payload={...}
         )
     ```

## Acceptance Criteria
- All tests pass with `pytest tests/`
- No live LLM API calls are made during test execution
- Tests cover the three primary metrics: ORR, EAC, PFA

## Files to Create
- `tests/__init__.py`
- `tests/test_workspace_scoring.py`
