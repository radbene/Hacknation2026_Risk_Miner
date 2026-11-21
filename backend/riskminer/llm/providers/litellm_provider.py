"""Provider 'litellm' – optional extra (`uv sync --extra litellm`, MIT licence) for any other vendor.

    profile: {provider: litellm, model: "mistral/mistral-large-latest", api_key_env: MISTRAL_API_KEY,
              base_url: null, data_location: eu}
"""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel

from riskminer.core.config import LLMProfile
from riskminer.llm.base import LLMError, Usage
from riskminer.llm.providers._common import api_key, schema_hint, strict_schema, text_of


class Provider:
    name = "litellm"

    def complete(self, profile: LLMProfile, *, system: str | None, messages: list[dict[str, Any]],
                 schema: type[BaseModel] | None, max_tokens: int | None = None) -> tuple[str, Usage]:
        try:
            import litellm
        except ImportError as e:
            raise LLMError("litellm nie jest zainstalowany (uv sync --extra litellm)") from e
        sys_parts = [system] if system else []
        kw: dict[str, Any] = {}
        if schema is not None:
            sch, strict = strict_schema(schema)
            kw["response_format"] = {"type": "json_schema",
                                     "json_schema": {"name": schema.__name__[:64], "schema": sch, "strict": strict}}
            sys_parts.append(schema_hint(sch))
        msgs = ([{"role": "system", "content": "\n\n".join(sys_parts)}] if sys_parts else []) + \
            [{"role": m["role"], "content": text_of(m["content"])} for m in messages]
        try:
            resp = litellm.completion(model=profile.model, messages=msgs, max_tokens=max_tokens or profile.max_tokens,
                                      api_key=api_key(profile, required=False), api_base=profile.base_url, **kw)
        except Exception as e:  # noqa: BLE001 – litellm raises many vendor-specific types
            raise LLMError(f"litellm: {type(e).__name__}: {e}") from e
        u = getattr(resp, "usage", None)
        return (resp.choices[0].message.content or "",
                Usage(tokens_in=getattr(u, "prompt_tokens", 0) or 0, tokens_out=getattr(u, "completion_tokens", 0) or 0))

    def embed(self, profile: LLMProfile, texts: list[str]) -> list[list[float]]:
        try:
            import litellm
        except ImportError as e:
            raise LLMError("litellm nie jest zainstalowany") from e
        res = litellm.embedding(model=profile.extra.get("embed_model") or profile.model, input=texts,
                                api_key=api_key(profile, required=False), api_base=profile.base_url)
        return [d["embedding"] for d in res.data]
