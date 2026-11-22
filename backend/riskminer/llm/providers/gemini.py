"""Provider 'gemini' – official `google-genai` SDK: Gemini API (AI Studio, key) or Vertex AI (EU location).

    gemini:            api_key_env: GEMINI_API_KEY                                          data_location: non_eu
    gemini_vertex_eu:  extra: {vertexai: true, project: <gcp>, location: europe-west4}      data_location: eu
                       (auth: Application Default Credentials, `gcloud auth application-default login`)

Structured output: `response_mime_type: application/json` + `response_json_schema`.
"""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel

from riskminer.core.config import LLMProfile
from riskminer.llm.base import LLMError, Usage
from riskminer.llm.providers._common import api_key, strict_schema, text_of


def _http_options(profile: LLMProfile):
    """Bounded wait: without a timeout the SDK can hang for minutes on an overloaded model (seen live: >5 min
    on 'Odczytaj cechy'). The caller then falls back to the next profile / rules."""
    from google.genai import types

    timeout_s = float(profile.extra.get("timeout_s") or 90)
    return types.HttpOptions(timeout=int(min(timeout_s, 120) * 1000),
                             retry_options=types.HttpRetryOptions(attempts=2))


def _client(profile: LLMProfile):
    from google import genai

    if profile.extra.get("vertexai"):
        return genai.Client(vertexai=True, project=profile.extra.get("project") or None,
                            location=profile.extra.get("location") or "europe-west4", http_options=_http_options(profile))
    return genai.Client(api_key=api_key(profile), http_options=_http_options(profile))


def build_request(profile: LLMProfile, *, system: str | None, messages: list[dict[str, Any]],
                  schema: type[BaseModel] | None, max_tokens: int | None) -> dict[str, Any]:
    from google.genai import types

    if not profile.model:
        raise LLMError("profil bez identyfikatora modelu (uzupełnij 'model' w ustawieniach)")
    cfg: dict[str, Any] = {"max_output_tokens": max_tokens or profile.max_tokens}
    if system:
        cfg["system_instruction"] = system
    if schema is not None:
        sch = strict_schema(schema)[0]
        _drop_additional(sch)
        cfg["response_mime_type"] = "application/json"
        cfg["response_json_schema"] = sch
    contents = [types.Content(role="model" if m["role"] == "assistant" else "user",
                              parts=[types.Part(text=text_of(m["content"]))])
                for m in messages if m.get("role") in ("user", "assistant")]
    return {"model": profile.model, "contents": contents, "config": types.GenerateContentConfig(**cfg)}


def _drop_additional(node: Any) -> None:
    """Older Gemini schema validation rejects additionalProperties=false on nested objects; keep it simple."""
    if isinstance(node, dict):
        node.pop("additionalProperties", None)
        for v in node.values():
            _drop_additional(v)
    elif isinstance(node, list):
        for v in node:
            _drop_additional(v)


def parse_response(resp: Any) -> tuple[str, Usage]:
    text = resp.text
    if not text:
        reason = None
        if getattr(resp, "candidates", None):
            reason = getattr(resp.candidates[0], "finish_reason", None)
        raise LLMError(f"gemini: pusta odpowiedź (finish_reason={reason})")
    um = resp.usage_metadata
    return text, Usage(tokens_in=getattr(um, "prompt_token_count", 0) or 0,
                       tokens_out=(getattr(um, "candidates_token_count", 0) or 0)
                       + (getattr(um, "thoughts_token_count", 0) or 0),
                       cache_read=getattr(um, "cached_content_token_count", 0) or 0)


class Provider:
    name = "gemini"

    def complete(self, profile: LLMProfile, *, system: str | None, messages: list[dict[str, Any]],
                 schema: type[BaseModel] | None, max_tokens: int | None = None) -> tuple[str, Usage]:
        from google.genai import errors

        req = build_request(profile, system=system, messages=messages, schema=schema, max_tokens=max_tokens)
        client = _client(profile)  # keep a reference: a temporary Client is closed before the request is sent
        try:
            resp = client.models.generate_content(**req)
        except errors.APIError as e:
            raise LLMError(f"gemini {getattr(e, 'code', '')}: {getattr(e, 'message', e)}") from e
        return parse_response(resp)

    def embed(self, profile: LLMProfile, texts: list[str]) -> list[list[float]]:
        from google.genai import errors

        model = profile.extra.get("embed_model") or "gemini-embedding-001"
        client = _client(profile)
        try:
            res = client.models.embed_content(model=model, contents=texts)
        except errors.APIError as e:
            raise LLMError(f"gemini embeddings: {e}") from e
        return [list(e.values) for e in res.embeddings]
