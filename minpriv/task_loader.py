"""Task loading utility."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from minpriv.schemas import TaskSpec


def load_task(path: str) -> TaskSpec:
    data = json.loads(Path(path).read_text(encoding="utf-8"))
    return TaskSpec.model_validate(data)

def load_task_from_dict(data: dict[str, Any]) -> TaskSpec:
    return TaskSpec.model_validate(data)
