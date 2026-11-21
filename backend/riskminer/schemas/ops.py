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
    provider: str
    model: str
    base_url: str | None = None
    data_location: str
    has_key: bool
    effort: str | None = None


class LLMRoutingOut(BaseModel):
    mode: str
    profiles: list[LLMProfileOut]
    tasks: dict[str, list[str]]
    active_data_locations: list[str]  # for the banner


class LLMRoutingIn(BaseModel):
    mode: str | None = None
    tasks: dict[str, list[str]] | None = None


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
