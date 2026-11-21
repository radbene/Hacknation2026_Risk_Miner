"""Helpers shared by providers: strict JSON schema, message normalisation, API key lookup."""

from __future__ import annotations

import copy
import json
from typing import Any

from pydantic import BaseModel

from riskminer.core.config import LLMProfile, secret
from riskminer.llm.base import LLMError


def api_key(profile: LLMProfile, required: bool = True) -> str | None:
    key = secret(profile.api_key_env)
    if required and not key:
        raise LLMError(f"brak klucza API: zmienna {profile.api_key_env or '(nie ustawiono api_key_env)'}")
    return key


def strict_schema(schema: type[BaseModel] | dict[str, Any]) -> tuple[dict[str, Any], bool]:
    """Pydantic JSON schema → structured-output schema.

    Sets `additionalProperties: false` on every object and drops keywords most providers reject
    (`default`, `title`). Returns (schema, fully_strict): fully_strict is True when every property is
    required (OpenAI `strict: true` demands it)."""
    s = copy.deepcopy(schema.model_json_schema() if isinstance(schema, type) else schema)
    strict = True

    def walk(node: Any) -> None:
        nonlocal strict
        if isinstance(node, dict):
            node.pop("title", None)
            node.pop("default", None)
            if node.get("type") == "object" or "properties" in node:
                node.setdefault("additionalProperties", False)
                props = node.get("properties") or {}
                if set(props) - set(node.get("required") or []):
                    strict = False
            for v in node.values():
                walk(v)
        elif isinstance(node, list):
            for v in node:
                walk(v)

    walk(s)
    return s, strict


def schema_hint(schema_json: dict[str, Any]) -> str:
    """Instruction appended to the system prompt for providers/models without native structured output."""
    return ("Odpowiedz WYŁĄCZNIE jednym obiektem JSON zgodnym z tym schematem JSON (bez komentarzy i bez "
            "bloków kodu):\n" + json.dumps(schema_json, ensure_ascii=False))


def text_of(content: Any) -> str:
    """Message content may be a string or a list of {type: text, text} blocks."""
    if isinstance(content, str):
        return content
    if isinstance(content, list):
        return "\n".join(b.get("text", "") if isinstance(b, dict) else str(b) for b in content)
    return str(content)
