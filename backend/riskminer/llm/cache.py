"""File cache for LLM outputs: data/llm_cache/<task>/<hash>.json. Stable reruns + offline replay."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any

from riskminer.core.config import get_config, repo_path


def input_hash(provider: str, model: str | None, prompt_version: str, payload: Any) -> str:
    blob = json.dumps({"p": provider, "m": model, "v": prompt_version, "x": payload}, sort_keys=True,
                      ensure_ascii=False, default=str)
    return hashlib.sha256(blob.encode()).hexdigest()


def _path(task: str, h: str) -> Path:
    return repo_path(get_config().llm.cache_dir) / task / f"{h}.json"


def get(task: str, h: str) -> dict | None:
    p = _path(task, h)
    if p.exists():
        return json.loads(p.read_text(encoding="utf-8"))
    return None


def put(task: str, h: str, record: dict) -> None:
    p = _path(task, h)
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps(record, ensure_ascii=False, indent=1, default=str), encoding="utf-8")
