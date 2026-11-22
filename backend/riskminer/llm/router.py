"""complete(task, messages, schema) → LLMResult, with per-task fallback chain, cache, validation, logging."""

from __future__ import annotations

import contextlib
import contextvars
import json
import logging
import re
import time
from typing import Any

from pydantic import BaseModel, ValidationError

from riskminer.core.config import LLMProfile
from riskminer.llm import cache
from riskminer.llm.base import LLMError, LLMResult, Usage, estimate_cost
from riskminer.llm.routing import effective_llm, missing_credentials
from riskminer.llm.safety import UNTRUSTED_SYSTEM_RULE

log = logging.getLogger("riskminer.llm")


def _provider(name: str):
    if name == "none":
        from riskminer.llm.providers.none import NoneProvider
        return NoneProvider()
    if name == "anthropic":
        from riskminer.llm.providers.anthropic import Provider
    elif name in ("openai", "openai_compatible"):
        from riskminer.llm.providers.openai_compat import Provider
    elif name == "gemini":
        from riskminer.llm.providers.gemini import Provider
    elif name == "litellm":
        from riskminer.llm.providers.litellm_provider import Provider
    else:
        raise LLMError(f"unknown provider {name}")
    return Provider()


def _strip_fences(text: str) -> str:
    m = re.search(r"```(?:json)?\s*(.*?)```", text, re.S)
    return (m.group(1) if m else text).strip()


def _parse(raw: str, schema: type[BaseModel] | None) -> BaseModel | None:
    if schema is None:
        return None
    return schema.model_validate(json.loads(_strip_fences(raw)))


def _log_call(**kw: Any) -> None:
    try:
        from riskminer.core.db import SessionLocal
        from riskminer.models import LLMCall

        s = SessionLocal()
        try:
            s.add(LLMCall(**kw))
            s.commit()
        finally:
            s.close()
    except Exception:  # noqa: BLE001 – logging must never break a pipeline
        log.warning("could not log llm_call", exc_info=True)


# Model chosen by the user for the current request (e.g. one analysis). Set via `use_profile(...)`.
_preferred: contextvars.ContextVar[str | None] = contextvars.ContextVar("riskminer_llm_preferred", default=None)


@contextlib.contextmanager
def use_profile(name: str | None):
    """Within this block every `complete()` tries the user's chosen profile first, then the expert's order.
    `name="rules"` means no model at all (deterministic rules only); None/'' keeps the expert's order."""
    token = _preferred.set(name or None)
    try:
        yield
    finally:
        _preferred.reset(token)


def chain_for(task: str) -> list[tuple[str, LLMProfile]]:
    cfg = effective_llm()
    names = list(cfg.tasks.get(task) or cfg.default)
    pref = _preferred.get()
    if pref == "rules":
        names = ["rules"]
    elif pref and pref in cfg.profiles:
        names = [pref] + [n for n in names if n != pref]
    return [(n, cfg.profiles[n]) for n in names if n in cfg.profiles]


def complete(task: str, messages: list[dict[str, Any]], schema: type[BaseModel] | None = None, *,
             system: str | None = None, prompt_version: str = "v1", untrusted: bool = True,
             max_tokens: int | None = None, profiles: list[str] | None = None) -> LLMResult:
    cfg = effective_llm()
    chain = [(n, cfg.profiles[n]) for n in profiles if n in cfg.profiles] if profiles else chain_for(task)
    sys_prompt = "\n\n".join(x for x in (system, UNTRUSTED_SYSTEM_RULE if untrusted else None) if x)
    attempts: list[dict[str, Any]] = []
    schema_json = schema.model_json_schema() if schema else None

    for name, prof in chain:
        if prof.provider == "none":
            return LLMResult(data=None, provider="none", profile=name, data_location="none", attempts=attempts)
        h = cache.input_hash("openai" if prof.provider == "openai_compatible" else prof.provider, prof.model, prompt_version,
                             {"system": sys_prompt, "messages": messages, "schema": schema_json})
        if cfg.mode in ("cache", "replay"):
            hit = cache.get(task, h)
            if hit is not None:
                try:
                    data = _parse(hit["raw"], schema)
                    _log_call(task=task, profile=name, provider=prof.provider, model=prof.model,
                              data_location=prof.data_location, prompt_version=prompt_version, input_hash=h,
                              cached=True, tokens_in=0, tokens_out=0, cost_usd=0.0, latency_ms=0)
                    return LLMResult(data=data, raw_text=hit["raw"], provider=prof.provider, display_name=prof.display_name, model=prof.model,
                                     profile=name, data_location=prof.data_location, cached=True, attempts=attempts)
                except (ValidationError, ValueError):
                    pass
            if cfg.mode == "replay":
                attempts.append({"profile": name, "error": "replay: no cached output"})
                continue
        missing = missing_credentials(prof)
        if missing:  # no key → skip quickly (cached outputs above are still served offline)
            attempts.append({"profile": name, "error": missing})
            continue
        t0 = time.monotonic()
        try:
            provider = _provider(prof.provider)
            raw, usage = provider.complete(prof, system=sys_prompt, messages=messages, schema=schema,
                                           max_tokens=max_tokens or prof.max_tokens)
            try:
                data = _parse(raw, schema)
            except (ValidationError, ValueError) as e:  # one repair retry
                repair = messages + [{"role": "assistant", "content": raw},
                                     {"role": "user", "content": f"Odpowiedź nie przeszła walidacji schematu: {e}. "
                                      "Zwróć wyłącznie poprawny JSON zgodny ze schematem."}]
                raw, usage2 = provider.complete(prof, system=sys_prompt, messages=repair, schema=schema,
                                                max_tokens=max_tokens or prof.max_tokens)
                usage = Usage(usage.tokens_in + usage2.tokens_in, usage.tokens_out + usage2.tokens_out,
                              usage.cache_read + usage2.cache_read, usage.cache_write + usage2.cache_write)
                data = _parse(raw, schema)
            ms = int((time.monotonic() - t0) * 1000)
            cost = estimate_cost(prof.model, usage)
            cache.put(task, h, {"raw": raw, "provider": prof.provider, "model": prof.model, "task": task,
                                "prompt_version": prompt_version})
            _log_call(task=task, profile=name, provider=prof.provider, model=prof.model,
                      data_location=prof.data_location, prompt_version=prompt_version, input_hash=h, cached=False,
                      tokens_in=usage.tokens_in, tokens_out=usage.tokens_out, cost_usd=cost, latency_ms=ms)
            return LLMResult(data=data, raw_text=raw, usage=usage, cost=cost, provider=prof.provider, display_name=prof.display_name,
                             model=prof.model, profile=name, data_location=prof.data_location, latency_ms=ms,
                             attempts=attempts)
        except Exception as e:  # noqa: BLE001 – fall through to the next profile
            ms = int((time.monotonic() - t0) * 1000)
            attempts.append({"profile": name, "error": f"{type(e).__name__}: {e}"[:500]})
            _log_call(task=task, profile=name, provider=prof.provider, model=prof.model,
                      data_location=prof.data_location, prompt_version=prompt_version, input_hash=h, cached=False,
                      ok=False, error=str(e)[:2000], latency_ms=ms)
            log.warning("llm task %s profile %s failed: %s", task, name, e)
    return LLMResult(data=None, provider="none", profile=None, data_location="none", attempts=attempts)


def embed(texts: list[str], task: str = "embeddings") -> list[list[float]] | None:
    """Embeddings: local sentence-transformers by default (S3/S5 implement in analysis/embeddings.py)."""
    try:
        from riskminer.analysis.embeddings import embed_local
        return embed_local(texts)
    except Exception:  # noqa: BLE001
        return None
