"""Provider 'litellm_provider' – Phase 0 stub. Owner: S5 (implement with the official SDK; see llm/base.py Provider)."""

from __future__ import annotations

from riskminer.llm.base import LLMError


class Provider:
    name = "litellm"

    def complete(self, profile, *, system, messages, schema, max_tokens=None):
        raise LLMError("litellm_provider provider not implemented yet (S5)")

    def embed(self, profile, texts):
        raise LLMError("litellm_provider embeddings not implemented yet (S5)")
