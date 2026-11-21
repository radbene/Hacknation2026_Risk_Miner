"""Provider 'openai' – official `openai` SDK; covers OpenAI and ANY OpenAI-compatible endpoint via `base_url`:

    Ollama / vLLM / LM Studio (local Bielik, PLLuM)  base_url: http://localhost:11434/v1     data_location: local
    Azure OpenAI (EU region, v1 API)                 base_url: https://<res>.openai.azure.com/openai/v1/   eu
    Mistral (La Plateforme, EU)                      base_url: https://api.mistral.ai/v1                    eu
    OpenRouter                                       base_url: https://openrouter.ai/api/v1                 non_eu

Structured outputs: `response_format: {type: json_schema, json_schema: {name, schema, strict}}`; `strict` only when
the schema is fully strict (all properties required). Endpoints without json_schema support (older local
servers) can set `extra.json_mode: json_object` (or it falls back automatically after a 400): JSON mode + the schema
in the system prompt; the router then validates with Pydantic and retries once.
"""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel

from riskminer.core.config import LLMProfile
from riskminer.llm.base import LLMError, Usage
from riskminer.llm.providers._common import api_key, schema_hint, strict_schema, text_of


def _client(profile: LLMProfile):
    from openai import OpenAI

    local = bool(profile.base_url) and profile.data_location == "local"
    key = api_key(profile, required=not local) or "local-no-key"
    return OpenAI(api_key=key, base_url=profile.base_url or None,
                  timeout=float(profile.extra.get("timeout_s", 300 if local else 120)), max_retries=1)


def build_request(profile: LLMProfile, *, system: str | None, messages: list[dict[str, Any]],
                  schema: type[BaseModel] | None, max_tokens: int | None, json_mode: str | None = None) -> dict:
    if not profile.model:
        raise LLMError("profil bez identyfikatora modelu (uzupełnij 'model' w ustawieniach)")
    mode = json_mode or profile.extra.get("json_mode") or "json_schema"
    sys_parts = [system] if system else []
    req: dict[str, Any] = {"model": profile.model}
    if schema is not None:
        sch, strict = strict_schema(schema)
        if mode == "json_schema":
            req["response_format"] = {"type": "json_schema", "json_schema": {
                "name": schema.__name__[:64], "schema": sch, "strict": strict}}
            if profile.data_location == "local":  # small local models follow the schema better when they see it
                sys_parts.append(schema_hint(sch))
        else:
            req["response_format"] = {"type": "json_object"}
            sys_parts.append(schema_hint(sch))
    msgs = [{"role": "system", "content": "\n\n".join(sys_parts)}] if sys_parts else []
    msgs += [{"role": m["role"], "content": text_of(m["content"])} for m in messages]
    req["messages"] = msgs
    limit = max_tokens or profile.max_tokens
    if profile.base_url:  # compatible servers understand max_tokens
        req["max_tokens"] = limit
    else:  # api.openai.com: reasoning models need max_completion_tokens
        req["max_completion_tokens"] = limit
        if profile.effort:
            req["reasoning_effort"] = profile.effort
    if "temperature" in profile.extra:
        req["temperature"] = profile.extra["temperature"]
    return req


def parse_response(resp: Any) -> tuple[str, Usage]:
    ch = resp.choices[0]
    if getattr(ch.message, "refusal", None):
        raise LLMError(f"model odmówił odpowiedzi: {ch.message.refusal}")
    if ch.finish_reason == "length":
        raise LLMError("odpowiedź ucięta (limit tokenów)")
    u = resp.usage
    cached = getattr(getattr(u, "prompt_tokens_details", None), "cached_tokens", 0) or 0 if u else 0
    return ch.message.content or "", Usage(tokens_in=(u.prompt_tokens if u else 0) or 0,
                                           tokens_out=(u.completion_tokens if u else 0) or 0, cache_read=cached)


class Provider:
    name = "openai"

    def complete(self, profile: LLMProfile, *, system: str | None, messages: list[dict[str, Any]],
                 schema: type[BaseModel] | None, max_tokens: int | None = None) -> tuple[str, Usage]:
        import openai

        client = _client(profile)
        req = build_request(profile, system=system, messages=messages, schema=schema, max_tokens=max_tokens)
        try:
            try:
                resp = client.chat.completions.create(**req)
            except openai.BadRequestError as e:
                if schema is None or req.get("response_format", {}).get("type") != "json_schema":
                    raise
                # endpoint without json_schema support → JSON mode + schema in prompt
                req = build_request(profile, system=system, messages=messages, schema=schema,
                                    max_tokens=max_tokens, json_mode="json_object")
                try:
                    resp = client.chat.completions.create(**req)
                except openai.BadRequestError:
                    raise e from None
        except openai.AuthenticationError as e:
            raise LLMError("openai: nieprawidłowy klucz API") from e
        except openai.RateLimitError as e:
            raise LLMError("openai: limit zapytań (429)") from e
        except openai.APIStatusError as e:
            raise LLMError(f"openai {e.status_code}: {e.message}") from e
        except openai.APIConnectionError as e:
            raise LLMError(f"openai: błąd połączenia z {profile.base_url or 'api.openai.com'}") from e
        return parse_response(resp)

    def embed(self, profile: LLMProfile, texts: list[str]) -> list[list[float]]:
        import openai

        model = profile.extra.get("embed_model") or profile.model
        try:
            res = _client(profile).embeddings.create(model=model, input=texts)
        except openai.OpenAIError as e:
            raise LLMError(f"openai embeddings: {e}") from e
        return [d.embedding for d in res.data]
