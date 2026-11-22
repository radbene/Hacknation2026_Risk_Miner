from __future__ import annotations

import datetime as dt
import uuid
from typing import Any

from pydantic import BaseModel, Field

from riskminer.schemas.common import ORM


class OpLogOut(ORM):
    id: uuid.UUID
    job_id: uuid.UUID | None = None
    connector: str
    operation: str
    url: str | None = None
    params: dict[str, Any] = Field(default_factory=dict)
    status_code: int | None = None
    n_results: int | None = None
    duration_ms: int | None = None
    error: str | None = None
    at: dt.datetime


class ConnectorHealth(BaseModel):
    code: str
    name: str
    enabled: bool
    base_url: str | None = None
    ok: bool | None = None
    last_ok_at: dt.datetime | None = None
    last_error: str | None = None
    licence: str | None = None
    tier: str = "P0"
    status: str = "działa"  # działa | zaprojektowane


class LLMUsageRow(BaseModel):
    task: str
    provider: str
    model: str | None = None
    data_location: str | None = None
    calls: int
    cached: int
    errors: int
    tokens_in: int
    tokens_out: int
    cost_usd: float


class LLMProfileOut(BaseModel):
    name: str
    display_name: str | None = None
    provider: str
    model: str
    base_url: str | None = None
    data_location: str
    has_key: bool
    effort: str | None = None
    available: bool = True  # can be called live now (key/model/endpoint configured)
    unavailable_reason: str | None = None
    max_tokens: int | None = None
    price_known: bool = False
    added_by: str | None = None  # set for models a user (not an expert) added for their own analyses


class LLMRoutingOut(BaseModel):
    mode: str
    profiles: list[LLMProfileOut]
    tasks: dict[str, list[str]]
    active_data_locations: list[str]  # for the banner
    default: list[str] = Field(default_factory=list)
    data_location_labels: dict[str, str] = Field(default_factory=dict)  # local → "lokalnie (nasz serwer)" ...
    task_locations: dict[str, str] = Field(default_factory=dict)  # task → data location of its first profile
    overridden: bool = False  # routing changed in the UI (DB) vs settings.yaml
    data_processing_note: str | None = None
    version: int | None = None
    updated_by: str | None = None


class LLMRoutingIn(BaseModel):
    mode: str | None = None
    tasks: dict[str, list[str]] | None = None
    default: list[str] | None = None
    # profile field overrides or new profiles (no secrets: only api_key_env names the variable)
    profiles: dict[str, dict[str, Any]] | None = None
    # API keys pasted in the UI, per profile: write-only, stored on the server, never returned
    api_keys: dict[str, str] | None = None
    comment: str | None = None


class UserModelIn(BaseModel):
    display_name: str
    provider: str = "openai_compatible"
    model: str
    base_url: str | None = None
    api_key: str | None = None  # write-only: stored on the server, never returned
    data_location: str | None = None  # ignored: the server infers it from provider + address (infer_data_location)


class LLMTestIn(BaseModel):
    profile: str
    model: str | None = None


class SandboxStatus(BaseModel):
    database: str
    golden: str
    golden_exists: bool
    golden_size_mb: float | None = None
    golden_created_at: str | None = None
    demo_mode: bool


class LicenceOut(BaseModel):
    name: str
    kind: str  # data | library | model
    licence: str
    url: str | None = None
    notes: str | None = None


class DashboardOut(BaseModel):
    counts: dict[str, int]  # projects, procedures, notices, contracts, events, pending_review, analyses ...
    last_jobs: list[dict[str, Any]] = Field(default_factory=list)
    alerts: list[dict[str, Any]] = Field(default_factory=list)
    data_locations: list[str] = Field(default_factory=list)
    tiers: dict[str, int] = Field(default_factory=dict)


class QualityMetrics(BaseModel):
    gold_set: str
    computed_at: dt.datetime
    linking: dict[str, Any]  # precision, recall, f1, per-level
    events: dict[str, Any] = Field(default_factory=dict)
    quotes: dict[str, Any] = Field(default_factory=dict)
    details: list[dict[str, Any]] = Field(default_factory=list)


class AlertOut(ORM):
    id: uuid.UUID
    project_id: uuid.UUID | None = None
    procedure_id: uuid.UUID | None = None
    notice_id: uuid.UUID | None = None
    kind: str
    severity: str
    message: str
    payload: dict[str, Any] = Field(default_factory=dict)
    read: bool = False
    created_at: dt.datetime


class WatchIn(BaseModel):
    procedure_ids: list[uuid.UUID] | None = None
    project_ids: list[uuid.UUID] | None = None
    watched: bool = True


class MonitorRunIn(BaseModel):
    as_of: dt.date | None = None  # replay: pretend today is as_of


class UserOut(ORM):
    id: uuid.UUID
    username: str
    display_name: str
    role: str


class LoginIn(BaseModel):
    username: str
    password: str


class TokenOut(BaseModel):
    token: str
    user: UserOut
