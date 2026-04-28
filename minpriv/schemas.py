"""Pydantic schemas for tasks, workspace, traces, and scores."""

from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import Any

from pydantic import BaseModel


class Permission(Enum):
    READER = "READER"
    WRITER = "WRITER"
    OWNER = "OWNER"


class FileSpec(BaseModel):
    file_id: str
    name: str
    path: str
    content: str
    mime_type: str = "text/plain"
    permission: Permission = Permission.WRITER
    owner: str = "agent"
    metadata: dict[str, Any] | None = None
    shares: dict[str, Permission] = {}


class WorkspaceSpec(BaseModel):
    files: list[FileSpec] = []


class GoldMinAccessSet(BaseModel):
    files: list[str] = []
    tools: list[str] = []
    permission_floor: dict[str, Permission] = {}


class SuccessCheck(BaseModel):
    check_type: str = "custom"
    params: dict[str, Any] = {}


class TaskSpec(BaseModel):
    task_id: str
    scope_type: str  # well_scoped | ambiguous
    instruction_mode: str  # none | explicit_least_privilege
    goal_prompt: str
    available_tools: list[str] = []
    workspace: WorkspaceSpec
    gold_min_access_set: GoldMinAccessSet
    success_check: SuccessCheck


class TraceEventType(str, Enum):
    MODEL_TURN_START = "model_turn_start"
    TOOL_CALL = "tool_call"
    TOOL_RESULT = "tool_result"
    FINAL_RESPONSE = "final_response"
    SUBAGENT_SPAWN = "subagent_spawn"
    RUN_END = "run_end"


class TraceEvent(BaseModel):
    event_type: TraceEventType
    run_id: str
    task_id: str
    step_index: int
    timestamp: str = ""
    payload: dict[str, Any] = {}

    def model_post_init(self, __context: Any) -> None:
        if not self.timestamp:
            self.timestamp = datetime.utcnow().isoformat()


class ToolCallPayload(BaseModel):
    tool_name: str
    arguments: dict[str, Any]
    target_file_ids: list[str] = []
    effective_permission_used: Permission | None = None
    model_name: str = ""


class ToolResultPayload(BaseModel):
    tool_name: str
    arguments: dict[str, Any]
    result: str
    error: str | None = None


class FinalResponsePayload(BaseModel):
    content: str
    model_name: str = ""


class RunEndPayload(BaseModel):
    reason: str  # success | max_steps | error
    final_step_index: int


class ScoreResult(BaseModel):
    task_id: str
    model: str
    prompt_mode: str
    run_id: str
    success: bool
    orr: int
    eac: int
    pfa: int
    step_count: int
    unique_files_touched: int
    unique_tools_used: int
