"""Settings: config/settings.yaml (expert/admin-editable) + environment (.env).

Precedence: env vars > settings.yaml > defaults. Secrets (API keys) only ever
come from env; settings.yaml names the env var (`api_key_env`).
"""

from __future__ import annotations

import os
from functools import lru_cache
from pathlib import Path
from typing import Any, Literal

import yaml
from pydantic import BaseModel, Field
from pydantic_settings import BaseSettings, SettingsConfigDict

REPO_ROOT = Path(__file__).resolve().parents[3]

DataLocation = Literal["local", "eu", "non_eu", "none"]


class LLMProfile(BaseModel):
    # openai_compatible = any server speaking the OpenAI chat API (Ollama, vLLM, LM Studio – e.g. local Bielik)
    provider: Literal["anthropic", "openai", "openai_compatible", "gemini", "litellm", "none"]
    display_name: str | None = None  # shown in the UI instead of provider/model
    model: str = ""
    base_url: str | None = None
    api_key_env: str | None = None
    data_location: DataLocation = "non_eu"
    max_tokens: int = 4096
    effort: str | None = None  # anthropic: low|medium|high ; openai: reasoning_effort
    extra: dict[str, Any] = Field(default_factory=dict)


class LLMConfig(BaseModel):
    mode: Literal["live", "cache", "replay"] = "cache"
    cache_dir: str = "data/llm_cache"
    profiles: dict[str, LLMProfile] = Field(default_factory=lambda: {"rules": LLMProfile(provider="none", data_location="none")})
    tasks: dict[str, list[str]] = Field(default_factory=dict)
    default: list[str] = Field(default_factory=lambda: ["rules"])


class ConnectorConfig(BaseModel):
    enabled: bool = True
    base_url: str | None = None
    min_interval_s: float = 0.0
    timeout_s: float = 60.0
    extra: dict[str, Any] = Field(default_factory=dict)


class AppConfig(BaseModel):
    sector: str = "wodkan"
    knowledge_dir: str = "knowledge"
    raw_store_dir: str = "data/raw"
    upload_dir: str = "data/uploads"
    user_agent: str = "riskminer-hacknation/0.1 (+https://github.com/hacknation-2026-solutions/risk-miner)"
    licence: str = "Apache-2.0"
    data_processing_note: str = ""
    connectors: dict[str, ConnectorConfig] = Field(default_factory=dict)
    llm: LLMConfig = Field(default_factory=LLMConfig)
    embeddings_model: str = "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"
    embeddings_dim: int = 384


class Env(BaseSettings):
    model_config = SettingsConfigDict(env_file=str(REPO_ROOT / ".env"), extra="ignore")

    database_url: str = "postgresql+psycopg://riskminer:riskminer@localhost:55432/riskminer"
    settings_file: str = str(REPO_ROOT / "config" / "settings.yaml")
    llm_mode: str | None = None  # overrides llm.mode
    secret_key: str = "dev-only-change-me"
    demo_mode: bool = True
    cors_origins: str = "http://localhost:5173"


def _load_yaml(path: Path) -> dict:
    if not path.exists():
        example = path.with_name("settings.example.yaml")
        path = example if example.exists() else path
    if not path.exists():
        return {}
    return yaml.safe_load(path.read_text(encoding="utf-8")) or {}


@lru_cache
def get_env() -> Env:
    return Env()


@lru_cache
def get_config() -> AppConfig:
    env = get_env()
    cfg = AppConfig.model_validate(_load_yaml(repo_path(env.settings_file)))
    if env.llm_mode:
        cfg.llm.mode = env.llm_mode  # type: ignore[assignment]
    return cfg


def repo_path(rel: str) -> Path:
    p = Path(rel)
    return p if p.is_absolute() else REPO_ROOT / p


def secret(name: str | None) -> str | None:
    """API key by env-var name: process environment first, then the repo `.env` (read on every call, so a key
    an admin adds to `.env` works for a newly added model without a restart or a code change)."""
    if not name:
        return None
    if name.startswith("db:"):  # key a user typed for a model they added – stored server-side, never sent back
        return _db_secret(name[3:])
    if os.environ.get(name):
        return os.environ[name]
    from dotenv import dotenv_values

    return dotenv_values(REPO_ROOT / ".env").get(name) or None


USER_KEYS_SETTING = "llm.user_keys"


def _db_secret(profile: str) -> str | None:
    try:
        from riskminer.core.db import SessionLocal
        from riskminer.models import Setting

        with SessionLocal() as s:
            row = s.get(Setting, USER_KEYS_SETTING)
            return ((row.value or {}).get(profile) or None) if row else None
    except Exception:  # noqa: BLE001
        return None
