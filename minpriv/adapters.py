"""Model adapter layer."""

from __future__ import annotations

import json
import os
from typing import Any, Protocol

from litellm import completion


class ModelAdapter(Protocol):
    def run_turn(
        self,
        messages: list[dict[str, Any]],
        tools: list[dict[str, Any]],
        model_name: str,
    ) -> dict[str, Any]:
        ...


class LiteLLMAdapter:
    """Adapter using LiteLLM for multi-provider support."""

    def run_turn(
        self,
        messages: list[dict[str, Any]],
        tools: list[dict[str, Any]],
        model_name: str,
    ) -> dict[str, Any]:
        # LiteLLM expects tools in OpenAI-compatible schema
        kwargs: dict[str, Any] = {
            "model": model_name,
            "messages": messages,
            "max_tokens": 1024,
        }
        if tools:
            kwargs["tools"] = tools
            kwargs["tool_choice"] = "auto"

        response = completion(**kwargs)
        choice = response.choices[0]
        msg = choice.message
        content = msg.content or ""

        tool_calls = []
        if hasattr(msg, "tool_calls") and msg.tool_calls:
            for tc in msg.tool_calls:
                tool_calls.append({
                    "id": tc.id,
                    "type": tc.type,
                    "function": {
                        "name": tc.function.name,
                        "arguments": tc.function.arguments,
                    },
                })
        return {
            "content": content,
            "tool_calls": tool_calls,
        }
