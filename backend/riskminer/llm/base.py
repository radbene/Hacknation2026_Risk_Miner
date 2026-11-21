"""Vendor-independent LLM interface.

    from riskminer.llm import complete
    res = complete("causes", messages=[{"role": "user", "content": "..."}], schema=CauseOut, system="...")
    res.data      # validated CauseOut instance (or None when provider == none)
    res.provider, res.model, res.cost, res.cached, res.data_location

Task routing (config llm.tasks.<task>) gives an ordered list of profiles; the router tries them in order
and the last one is normally `rules` (provider `none`) → callers MUST handle `res.data is None` with their
deterministic fallback. Every call is logged to `llm_call` with cost; outputs are cached by
(provider, model, prompt_version, input hash) so reruns are stable (modes: live | cache | replay).
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Protocol

from pydantic import BaseModel

from riskminer.core.config import LLMProfile


@dataclass
class Usage:
    tokens_in: int = 0
    tokens_out: int = 0
    cache_read: int = 0
    cache_write: int = 0


@dataclass
class LLMResult:
    data: BaseModel | None
    raw_text: str | None = None
    usage: Usage = field(default_factory=Usage)
    cost: float = 0.0
    provider: str = "none"
    model: str | None = None
    profile: str | None = None
    data_location: str = "none"
    latency_ms: int = 0
    cached: bool = False
    attempts: list[dict[str, Any]] = field(default_factory=list)  # failed profiles before this one

    @property
    def label(self) -> str:
        """Shown in UI next to [Wniosek modelu]."""
        return "reguły" if self.provider == "none" else f"{self.provider}/{self.model}"


class LLMError(RuntimeError):
    pass


class Provider(Protocol):
    name: str

    def complete(self, profile: LLMProfile, *, system: str | None, messages: list[dict[str, Any]],
                 schema: type[BaseModel] | None, max_tokens: int | None = None) -> tuple[str, Usage]:
        """Return (raw JSON/text, usage). Raise LLMError on failure."""
        ...

    def embed(self, profile: LLMProfile, texts: list[str]) -> list[list[float]]:
        ...


# USD per 1M tokens (input, output), first-party list prices (Claude: claude-api skill, cached 2026-11-03).
# Update when models change; unknown models → cost 0 and flagged "brak cennika" on the usage page.
# Local models (Ollama/vLLM) cost 0 by definition (data_location local).
PRICES: dict[str, tuple[float, float]] = {
    "claude-opus-5-5": (4.0, 20.0),
    "claude-opus-5": (5.0, 25.0),
    "claude-sonnet-5-5": (2.0, 10.0),
    "claude-haiku-5-5": (0.10, 0.50),
    "claude-fable-5-2": (8.0, 40.0),
}
CACHE_READ_FACTOR = 0.1   # Anthropic cache read ≈ 0.1× input price
CACHE_WRITE_FACTOR = 1.25  # 5-minute cache write ≈ 1.25× input price


def price_known(model: str | None) -> bool:
    return (model or "") in PRICES


def estimate_cost(model: str | None, usage: Usage) -> float:
    p = PRICES.get(model or "")
    if not p:
        return 0.0
    inp = usage.tokens_in + usage.cache_read * CACHE_READ_FACTOR + usage.cache_write * CACHE_WRITE_FACTOR
    return (inp * p[0] + usage.tokens_out * p[1]) / 1_000_000
