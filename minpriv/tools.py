"""Tool definitions and schema generation."""

from __future__ import annotations

import json
from typing import Any

from minpriv.schemas import Permission
from minpriv.workspace import Workspace


TOOL_SCHEMAS: dict[str, dict[str, Any]] = {
    "list_files": {
        "type": "function",
        "function": {
            "name": "list_files",
            "description": "List files in the workspace. Optionally filter by folder or query.",
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {"type": "string", "description": "Substring to match against file names."},
                    "folder": {"type": "string", "description": "Folder path prefix to filter by."},
                },
            },
        },
    },
    "read_file": {
        "type": "function",
        "function": {
            "name": "read_file",
            "description": "Read the content of a file by file_id.",
            "parameters": {
                "type": "object",
                "properties": {
                    "file_id": {"type": "string"},
                },
                "required": ["file_id"],
            },
        },
    },
    "write_file": {
        "type": "function",
        "function": {
            "name": "write_file",
            "description": "Overwrite the content of a file by file_id.",
            "parameters": {
                "type": "object",
                "properties": {
                    "file_id": {"type": "string"},
                    "content_patch": {"type": "string"},
                },
                "required": ["file_id", "content_patch"],
            },
        },
    },
    "create_file": {
        "type": "function",
        "function": {
            "name": "create_file",
            "description": "Create a new file in the workspace.",
            "parameters": {
                "type": "object",
                "properties": {
                    "parent_folder_id": {"type": "string"},
                    "name": {"type": "string"},
                    "content": {"type": "string"},
                },
                "required": ["name", "content"],
            },
        },
    },
    "share_file": {
        "type": "function",
        "function": {
            "name": "share_file",
            "description": "Share a file with a principal at a given role.",
            "parameters": {
                "type": "object",
                "properties": {
                    "file_id": {"type": "string"},
                    "principal": {"type": "string"},
                    "role": {"type": "string", "enum": ["READER", "WRITER", "OWNER"]},
                },
                "required": ["file_id", "principal", "role"],
            },
        },
    },
    "delete_file": {
        "type": "function",
        "function": {
            "name": "delete_file",
            "description": "Delete a file by file_id.",
            "parameters": {
                "type": "object",
                "properties": {
                    "file_id": {"type": "string"},
                },
                "required": ["file_id"],
            },
        },
    },
}


class ToolRegistry:
    def __init__(self, workspace: Workspace):
        self.workspace = workspace

    def dispatch(self, tool_name: str, arguments: dict[str, Any]) -> str:
        method = getattr(self, f"_{tool_name}", None)
        if method is None:
            return json.dumps({"error": f"Unknown tool {tool_name}"})
        return method(**arguments)

    def _list_files(self, query: str | None = None, folder: str | None = None) -> str:
        result = self.workspace.list_files(query=query, folder=folder)
        return json.dumps({"files": result})

    def _read_file(self, file_id: str) -> str:
        return self.workspace.read_file(file_id)

    def _write_file(self, file_id: str, content_patch: str) -> str:
        return self.workspace.write_file(file_id, content_patch)

    def _create_file(self, name: str, content: str, parent_folder_id: str | None = None) -> str:
        return self.workspace.create_file(parent_folder_id, name, content)

    def _share_file(self, file_id: str, principal: str, role: str) -> str:
        return self.workspace.share_file(file_id, principal, role)

    def _delete_file(self, file_id: str) -> str:
        return self.workspace.delete_file(file_id)

    def effective_permission(self, tool_name: str, arguments: dict[str, Any]) -> Permission | None:
        if tool_name in ("list_files", "read_file"):
            return Permission.READER
        if tool_name in ("write_file", "create_file", "share_file"):
            return Permission.WRITER
        if tool_name == "delete_file":
            return Permission.OWNER
        return None

    def target_file_ids(self, tool_name: str, arguments: dict[str, Any]) -> list[str]:
        if tool_name in ("read_file", "write_file", "share_file", "delete_file"):
            fid = arguments.get("file_id")
            return [fid] if fid else []
        if tool_name == "create_file":
            return []
        if tool_name == "list_files":
            return []
        return []


def build_tool_schema(available: list[str]) -> list[dict[str, Any]]:
    return [TOOL_SCHEMAS[name] for name in available if name in TOOL_SCHEMAS]
