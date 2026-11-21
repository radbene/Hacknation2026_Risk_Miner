from __future__ import annotations

from riskminer.llm.base import LLMError


class NoneProvider:
    """Rules only: never calls a model. The router returns data=None and callers use deterministic fallbacks."""

    name = "none"

    def complete(self, profile, *, system, messages, schema, max_tokens=None):
        raise LLMError("provider none – rules only")

    def embed(self, profile, texts):
        raise LLMError("provider none – no embeddings")
