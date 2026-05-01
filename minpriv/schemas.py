"""Pydantic schemas for tasks, workspace, traces, and scores."""

from __future__ import annotations

from datetime import datetime, timezone
from enum import Enum
from typing import Any

from pydantic import BaseModel


class Permission(Enum):
    READER = "READER"
    WRITER = "WRITER"
    WRITER_ONLY = "WRITER_ONLY"
    OWNER = "OWNER"


class AccessJudgment(str, Enum):
    REQUIRED = "required"
    JUSTIFIED_DISCOVERY = "justified_discovery"
    TRUE_OVERREACH = "true_overreach"


class PermissionJudgment(str, Enum):
    MINIMUM_SUFFICIENT = "minimum_sufficient"
    TOOL_FORCED = "tool_forced"
    AGENT_ESCALATED = "agent_escalated"


class EventKind(str, Enum):
    FILE_READ = "file_read"
    FILE_WRITE = "file_write"
    FILE_SHARE = "file_share"
    FILE_DELETE = "file_delete"
    FILE_LIST = "file_list"
    SUBAGENT_CREATE = "subagent_create"


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


class AllowedDiscovery(BaseModel):
    max_list_calls: int = 1
    max_confirmation_reads: int = 1
    allowed_search_scope: list[str] = ["/"]


class GoldMinAccessSet(BaseModel):
    file_access: dict[str, list[str]] = {}  # file_id -> list of allowed tools
    global_tools: list[str] = []           # tools not targeting a specific file (e.g., list_files)
    permission_floor: dict[str, Permission] = {}
    allowed_discovery: AllowedDiscovery = AllowedDiscovery()

    @property
    def all_required_files(self) -> set[str]:
        return set(self.file_access.keys())

    @property
    def all_required_tools(self) -> set[str]:
        tools = set(self.global_tools)
        for tlist in self.file_access.values():
            tools.update(tlist)
        return tools


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
            self.timestamp = datetime.now(timezone.utc).isoformat()


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


class ScoredEvent(BaseModel):
    step_index: int
    tool_name: str
    event_kind: EventKind
    target_file_id: str | None = None
    access_judgment: AccessJudgment
    permission_judgment: PermissionJudgment | None = None
    rationale: str


class ScoreResult(BaseModel):
    task_id: str
    model: str
    prompt_mode: str
    run_id: str
    success: bool
    
    # Strict metrics (original)
    strict_orr: int
    strict_eac: int
    strict_pfa: int
    
    # Refined metrics
    refined_orr: int
    refined_eac: int
    tool_adjusted_pfa: int
    
    # Diagnostics
    discovery_count: int
    true_overreach_count: int
    tool_forced_count: int
    
    step_count: int
    unique_files_touched: int
    unique_tools_used: int
    scored_events: list[ScoredEvent] = []

    @property
    def orr(self) -> int:
        return self.strict_orr

    @property
    def eac(self) -> int:
        return self.strict_eac

    @property
    def pfa(self) -> int:
        return self.strict_pfa
