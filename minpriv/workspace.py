"""In-memory workspace simulator."""

from __future__ import annotations

import json
from typing import Any

from minpriv.schemas import FileSpec, Permission, WorkspaceSpec


class FileNode:
    """Represents a single file or folder in the simulated Drive."""

    def __init__(self, spec: FileSpec):
        self.file_id = spec.file_id
        self.name = spec.name
        self.path = spec.path
        self.content = spec.content
        self.mime_type = spec.mime_type
        self.permission = spec.permission
        self.owner = spec.owner
        self.metadata = spec.metadata or {}
        self.shares = dict(spec.shares)

    def to_dict(self) -> dict[str, Any]:
        return {
            "file_id": self.file_id,
            "name": self.name,
            "path": self.path,
            "content": self.content,
            "mime_type": self.mime_type,
            "permission": self.permission.value,
            "owner": self.owner,
            "metadata": self.metadata,
            "shares": {k: v.value for k, v in self.shares.items()},
        }


class Workspace:
    """In-memory Drive-like workspace."""

    def __init__(self, files: dict[str, FileNode] | None = None):
        self._files: dict[str, FileNode] = files or {}

    @classmethod
    def from_spec(cls, spec: WorkspaceSpec) -> Workspace:
        files = {f.file_id: FileNode(f) for f in spec.files}
        return cls(files)

    # --- read ops ---

    def list_files(self, query: str | None = None, folder: str | None = None) -> list[dict[str, Any]]:
        results = []
        for f in self._files.values():
            match = True
            if folder and not f.path.startswith(folder):
                match = False
            if query and query.lower() not in f.name.lower():
                match = False
            if match:
                results.append(f.to_dict())
        return results

    def read_file(self, file_id: str) -> str:
        node = self._files.get(file_id)
        if not node:
            return json.dumps({"error": f"file_id '{file_id}' not found"})
        
        if node.permission in (Permission.READER, Permission.WRITER, Permission.OWNER):
            return json.dumps(node.to_dict())
        return json.dumps({"error": "Permission denied: Insufficient read access."})

    # --- write ops ---

    def write_file(self, file_id: str, content_patch: str) -> str:
        node = self._files.get(file_id)
        if not node:
            return json.dumps({"error": f"file_id '{file_id}' not found"})
        
        if node.permission in (Permission.WRITER, Permission.WRITER_ONLY, Permission.OWNER):
            node.content = content_patch
            return json.dumps({"status": "ok", "file_id": file_id})
        return json.dumps({"error": "Permission denied: Insufficient write access."})

    def create_file(self, parent_folder_id: str | None, name: str, content: str) -> str:
        new_id = f"auto_{name}_{len(self._files)}"
        spec = FileSpec(
            file_id=new_id,
            name=name,
            path=f"/{name}" if parent_folder_id is None else f"/{parent_folder_id}/{name}",
            content=content,
        )
        self._files[new_id] = FileNode(spec)
        return json.dumps({"status": "ok", "file_id": new_id})

    def delete_file(self, file_id: str) -> str:
        if file_id not in self._files:
            return json.dumps({"error": f"file_id '{file_id}' not found"})
        del self._files[file_id]
        return json.dumps({"status": "ok", "deleted": file_id})

    # --- sharing ---

    def share_file(self, file_id: str, principal: str, role: str) -> str:
        node = self._files.get(file_id)
        if not node:
            return json.dumps({"error": f"file_id '{file_id}' not found"})
        try:
            perm = Permission(role.upper())
        except ValueError:
            return json.dumps({"error": f"invalid role '{role}'"})
        node.shares[principal] = perm
        return json.dumps({"status": "ok", "file_id": file_id, "shared_with": principal, "role": role})

    # --- inspection ---

    def to_spec(self) -> WorkspaceSpec:
        return WorkspaceSpec(
            files=[
                FileSpec(
                    file_id=n.file_id,
                    name=n.name,
                    path=n.path,
                    content=n.content,
                    mime_type=n.mime_type,
                    permission=n.permission,
                    owner=n.owner,
                    metadata=n.metadata,
                    shares=n.shares,
                )
                for n in self._files.values()
            ]
        )

    def get_file(self, file_id: str) -> FileNode | None:
        return self._files.get(file_id)
