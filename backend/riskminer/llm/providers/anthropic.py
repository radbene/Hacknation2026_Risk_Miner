"""Provider 'anthropic' – official `anthropic` SDK (Claude API, or Vertex AI with `extra.vertexai`).

- Structured output via `output_config.format` (JSON schema); effort set explicitly (`output_config.effort`).
- Thinking: not sent – current models run adaptive thinking by default; no `temperature` (rejected by current models).
- Refusals: on the Claude API, beta `server-side-fallback-2026-07-01` + `fallbacks: "default"` for models that
  support it (not on Vertex). A final `stop_reason == "refusal"` raises LLMError → router tries the next profile.
- Prompt caching: the (long, stable) system prompt – risk catalog, rules, few-shot examples – is sent as a
  text block with `cache_control: ephemeral`; volatile input stays in `messages` after the breakpoint.
- Data location: first-party API = non_eu; Vertex with `extra.region` europe-* / "eu" = eu.
"""

from __future__ import annotations

import json
from typing import Any

from pydantic import BaseModel

from riskminer.core.config import LLMProfile
from riskminer.llm.base import LLMError, Usage
from riskminer.llm.providers._common import api_key, strict_schema, text_of

DEFAULT_MODEL = "claude-opus-5-5"
FALLBACK_BETA = "server-side-fallback-2026-07-01"
# models that accept server-side `fallbacks` (Haiku has none)
FALLBACK_MODELS = ("claude-opus-5-5", "claude-opus-5", "claude-sonnet-5-5", "claude-fable-5-1", "claude-fable-5-2")
DEFAULT_EFFORT = "medium"


def _client(profile: LLMProfile):
    import anthropic

    timeout = float(profile.extra.get("timeout_s", 300))
    if profile.extra.get("vertexai"):
        from anthropic import AnthropicVertex

        return AnthropicVertex(project_id=profile.extra.get("project") or None,
                               region=profile.extra.get("region") or profile.extra.get("location") or "europe-west1",
                               timeout=timeout, max_retries=2), True
    return anthropic.Anthropic(api_key=api_key(profile), base_url=profile.base_url or None, timeout=timeout,
                               max_retries=2), False


def build_request(profile: LLMProfile, *, system: str | None, messages: list[dict[str, Any]],
                  schema: type[BaseModel] | None, max_tokens: int | None, vertex: bool = False) -> dict[str, Any]:
    """Request kwargs (separated for replay tests)."""
    model = profile.model or DEFAULT_MODEL
    req: dict[str, Any] = {
        "model": model,
        "max_tokens": max_tokens or profile.max_tokens or 16000,
        "messages": [{"role": m["role"], "content": text_of(m["content"])} for m in messages
                     if m.get("role") in ("user", "assistant")],
    }
    if system:
        req["system"] = [{"type": "text", "text": system, "cache_control": {"type": "ephemeral"}}]
    output_config: dict[str, Any] = {"effort": profile.effort or DEFAULT_EFFORT}
    if schema is not None:
        output_config["format"] = {"type": "json_schema", "schema": strict_schema(schema)[0]}
    req["output_config"] = output_config
    if not vertex and model in FALLBACK_MODELS and profile.extra.get("fallbacks", True):
        req["betas"] = [FALLBACK_BETA]
        req["fallbacks"] = "default"
    return req


def parse_response(resp: Any) -> tuple[str, Usage]:
    if resp.stop_reason == "refusal":
        cat = getattr(getattr(resp, "stop_details", None), "category", None)
        raise LLMError(f"model odmówił odpowiedzi (refusal, kategoria: {cat})")
    if resp.stop_reason == "max_tokens":
        raise LLMError("odpowiedź ucięta (max_tokens) – zwiększ max_tokens w profilu")
    text = "".join(b.text for b in resp.content if getattr(b, "type", None) == "text")
    u = resp.usage
    cache_read = getattr(u, "cache_read_input_tokens", 0) or 0
    cache_write = getattr(u, "cache_creation_input_tokens", 0) or 0
    usage = Usage(tokens_in=(u.input_tokens or 0), tokens_out=u.output_tokens or 0,
                  cache_read=cache_read, cache_write=cache_write)
    return text, usage


class Provider:
    name = "anthropic"

    def complete(self, profile: LLMProfile, *, system: str | None, messages: list[dict[str, Any]],
                 schema: type[BaseModel] | None, max_tokens: int | None = None) -> tuple[str, Usage]:
        import anthropic

        client, vertex = _client(profile)
        req = build_request(profile, system=system, messages=messages, schema=schema, max_tokens=max_tokens,
                            vertex=vertex)
        try:
            if "betas" in req:
                resp = client.beta.messages.create(**req)
            else:
                resp = client.messages.create(**req)
        except anthropic.BadRequestError as e:
            raise LLMError(f"anthropic 400: {e.message}") from e
        except anthropic.AuthenticationError as e:
            raise LLMError("anthropic: nieprawidłowy klucz API") from e
        except anthropic.RateLimitError as e:
            raise LLMError("anthropic: limit zapytań (429)") from e
        except anthropic.APIStatusError as e:
            raise LLMError(f"anthropic {e.status_code}: {e.message}") from e
        except anthropic.APIConnectionError as e:
            raise LLMError(f"anthropic: błąd połączenia: {e}") from e
        text, usage = parse_response(resp)
        if schema is not None:
            json.loads(text)  # structured output guarantees JSON; fail loudly if not
        return text, usage

    def embed(self, profile: LLMProfile, texts: list[str]) -> list[list[float]]:
        raise LLMError("Anthropic nie udostępnia embeddingów – używamy lokalnego modelu sentence-transformers")
