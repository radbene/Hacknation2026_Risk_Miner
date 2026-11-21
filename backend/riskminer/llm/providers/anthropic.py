"""Provider 'anthropic' – Phase 0 stub. Owner: S5 (implement with the official SDK; see llm/base.py Provider)."""

from __future__ import annotations

from riskminer.llm.base import LLMError


class Provider:
    name = "anthropic"

    def complete(self, profile, *, system, messages, schema, max_tokens=None):
        raise LLMError("anthropic provider not implemented yet (S5)")

    def embed(self, profile, texts):
        raise LLMError("anthropic embeddings not implemented yet (S5)")
