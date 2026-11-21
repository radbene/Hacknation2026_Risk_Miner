"""Effective LLM routing = config/settings.yaml (`llm:`) overridden by the admin's choice stored in the DB.

Precedence: DB `setting['llm.routing']` (PUT /api/settings/llm) > env LLM_MODE > settings.yaml > defaults.
The override may change `mode`, per-task profile order (`tasks`, `default`) and profile fields
(`profiles.<name>`: model, base_url, effort, data_location, max_tokens, extra, or a whole new profile);
secrets are never stored here – a profile only names the env var holding its key (`api_key_env`).

    effective_llm() -> LLMConfig        cached ~5 s per process (each request/worker sees changes quickly)
    save_override(session, {...}, actor) -> LLMConfig     validates, versions the setting, logs a review row
    test_profile("local_bielik")        -> {"ok", "latency_ms", "provider", "model", "data_location", ...}
    data_locations(cfg)                 -> active locations (first profile of every task) for the UI banner
"""

from __future__ import annotations

import datetime as dt
import threading
import time
from typing import Any

from pydantic import BaseModel, ValidationError

from riskminer.core.config import LLMConfig, LLMProfile, get_config, get_env, secret

SETTING_KEY = "llm.routing"
_TTL_S = 5.0
_lock = threading.Lock()
_cache: dict[str, Any] = {"at": 0.0, "override": None}
LOCATION_LABEL = {"local": "lokalnie (nasz serwer)", "eu": "w UE", "non_eu": "poza UE", "none": "bez modelu (reguły)"}


class RoutingError(ValueError):
    pass


def _load_override() -> dict[str, Any] | None:
    now = time.monotonic()
    with _lock:
        if now - _cache["at"] < _TTL_S:
            return _cache["override"]
    val = None
    try:
        from riskminer.core.db import SessionLocal
        from riskminer.models import Setting

        s = SessionLocal()
        try:
            row = s.get(Setting, SETTING_KEY)
            val = dict(row.value) if row and row.value else None
        finally:
            s.close()
    except Exception:  # noqa: BLE001 – no DB → YAML only
        val = None
    with _lock:
        _cache.update(at=now, override=val)
    return val


def invalidate() -> None:
    with _lock:
        _cache["at"] = 0.0


def apply_override(base: LLMConfig, ov: dict[str, Any] | None) -> LLMConfig:
    cfg = base.model_copy(deep=True)
    if not ov:
        return cfg
    for name, fields in (ov.get("profiles") or {}).items():
        cur = cfg.profiles[name].model_dump() if name in cfg.profiles else {}
        cfg.profiles[name] = LLMProfile.model_validate({**cur, **(fields or {})})
    if ov.get("mode"):
        cfg.mode = ov["mode"]
    if ov.get("tasks"):
        cfg.tasks = {**cfg.tasks, **ov["tasks"]}
    if ov.get("default"):
        cfg.default = list(ov["default"])
    return cfg


def effective_llm() -> LLMConfig:
    base = get_config().llm
    ov = _load_override()
    if ov and ov.get("mode") is None and get_env().llm_mode:
        ov = {**ov, "mode": get_env().llm_mode}
    return apply_override(base, ov)


def missing_credentials(p: LLMProfile) -> str | None:
    """Reason a profile cannot be called live right now (None = callable)."""
    if p.provider == "none":
        return None
    if p.provider in ("gemini", "anthropic") and p.extra.get("vertexai"):
        return None if p.extra.get("project") or p.provider == "anthropic" else "brak projektu GCP (extra.project)"
    if p.provider in ("openai", "openai_compatible") and p.base_url and p.data_location == "local":
        return None  # local server, key optional
    if not p.model and p.provider != "anthropic":
        return "brak identyfikatora modelu"
    if p.api_key_env and not secret(p.api_key_env):
        return f"brak klucza API ({p.api_key_env})"
    return None


def data_locations(cfg: LLMConfig) -> list[str]:
    used = {chain[0] for chain in cfg.tasks.values() if chain}
    return sorted({cfg.profiles[n].data_location for n in used if n in cfg.profiles})


def validate_override(ov: dict[str, Any], base: LLMConfig | None = None) -> LLMConfig:
    base = base or get_config().llm
    if ov.get("mode") not in (None, "live", "cache", "replay"):
        raise RoutingError("tryb musi być: live, cache albo replay")
    for name, fields in (ov.get("profiles") or {}).items():
        if fields and any(k.lower().endswith(("key", "token", "secret")) and k != "api_key_env" for k in fields):
            raise RoutingError("klucze API nie są zapisywane w ustawieniach – podaj nazwę zmiennej (api_key_env)")
        if name not in base.profiles and not (fields or {}).get("provider"):
            raise RoutingError(f"nowy profil {name}: podaj provider")
    try:
        cfg = apply_override(base, ov)
    except ValidationError as e:
        raise RoutingError(f"niepoprawny profil: {e.errors()[0].get('msg')}") from e
    for task, chain in {**(ov.get("tasks") or {}), "default": ov.get("default") or []}.items():
        unknown = [n for n in chain if n not in cfg.profiles]
        if unknown:
            raise RoutingError(f"zadanie {task}: nieznane profile {unknown}")
    return cfg


def save_override(session, ov: dict[str, Any], actor: str | None, comment: str | None = None) -> LLMConfig:
    """Merge `ov` into the stored override (new version) and log it in the review trail."""
    from riskminer.ids import make_id
    from riskminer.models import Review, Setting

    row = session.get(Setting, SETTING_KEY)
    prev = dict(row.value) if row and row.value else {}
    merged = {**prev}
    for k in ("mode", "default"):
        if ov.get(k) is not None:
            merged[k] = ov[k]
    if ov.get("tasks"):
        merged["tasks"] = {**(prev.get("tasks") or {}), **ov["tasks"]}
    if ov.get("profiles"):
        merged["profiles"] = {**(prev.get("profiles") or {}), **ov["profiles"]}
    cfg = validate_override(merged)
    if row is None:
        row = Setting(key=SETTING_KEY, value=merged, version=1, updated_by=actor)
        session.add(row)
    else:
        row.value, row.version, row.updated_by = merged, (row.version or 1) + 1, actor
    session.add(Review(object_type="setting", object_id=make_id("setting", SETTING_KEY), action="edit",
                       before=prev or None, after=merged, reviewer=actor, comment=comment or "Zmiana routingu LLM",
                       at=dt.datetime.now(dt.UTC)))
    session.flush()
    invalidate()
    return cfg


def reset_override(session, actor: str | None) -> None:
    from riskminer.models import Setting

    row = session.get(Setting, SETTING_KEY)
    if row is not None:
        save_override(session, {}, actor, "Przywrócono ustawienia z pliku")
        row.value = {}
    invalidate()


class _Ping(BaseModel):
    ok: bool
    odpowiedz: str


def test_profile(name: str, model: str | None = None) -> dict[str, Any]:
    """One tiny live structured call through a profile (bypasses the cache), logged in llm_call."""
    from riskminer.llm.base import estimate_cost
    from riskminer.llm.router import _log_call, _parse, _provider

    cfg = effective_llm()
    if name not in cfg.profiles:
        raise RoutingError(f"nieznany profil {name}")
    prof = cfg.profiles[name]
    if model:
        prof = prof.model_copy(update={"model": model})
    out: dict[str, Any] = {"profile": name, "provider": prof.provider, "model": prof.model,
                           "data_location": prof.data_location, "ok": False}
    if prof.provider == "none":
        return {**out, "ok": True, "message": "profil reguł – nie wywołuje modelu"}
    missing = missing_credentials(prof)
    if missing:
        return {**out, "error": missing}
    t0 = time.monotonic()
    try:
        raw, usage = _provider(prof.provider).complete(
            prof, system="Jesteś testem połączenia. Odpowiadasz krótko po polsku.",
            messages=[{"role": "user", "content": "Potwierdź działanie: ustaw ok=true i odpowiedz jednym zdaniem."}],
            schema=_Ping, max_tokens=min(prof.max_tokens, 2000))
        data = _parse(raw, _Ping)
        ms = int((time.monotonic() - t0) * 1000)
        cost = estimate_cost(prof.model, usage)
        _log_call(task="llm_test", profile=name, provider=prof.provider, model=prof.model,
                  data_location=prof.data_location, prompt_version="test", cached=False,
                  tokens_in=usage.tokens_in, tokens_out=usage.tokens_out, cost_usd=cost, latency_ms=ms)
        return {**out, "ok": bool(data and data.ok), "latency_ms": ms, "tokens_in": usage.tokens_in,
                "tokens_out": usage.tokens_out, "cost_usd": cost, "sample": data.odpowiedz if data else raw[:200]}
    except Exception as e:  # noqa: BLE001
        ms = int((time.monotonic() - t0) * 1000)
        _log_call(task="llm_test", profile=name, provider=prof.provider, model=prof.model,
                  data_location=prof.data_location, prompt_version="test", cached=False, ok=False,
                  error=str(e)[:2000], latency_ms=ms)
        return {**out, "latency_ms": ms, "error": f"{type(e).__name__}: {e}"[:500]}
