"""Path B – new-investment analysis."""

from __future__ import annotations

import datetime as dt
import uuid
from typing import Any, Literal

from pydantic import BaseModel, Field

from riskminer.schemas.common import BlockLabel, ReviewFields


class FeatureValue(BaseModel):
    value: Any = None
    unit: str | None = None
    source: Literal["user", "regex", "llm", "document", "default"] = "user"
    quote: str | None = None
    evidence_id: uuid.UUID | None = None
    confidence: float | None = None


class Features(BaseModel):
    """Editable feature form. Values carry their source; `vat_basis` must be asked (net/gross)."""

    subsector_main: FeatureValue | None = None
    subsector_extra: FeatureValue | None = None
    work_type: FeatureValue | None = None
    formula: FeatureValue | None = None
    length_km: FeatureValue | None = None
    connections: FeatureValue | None = None
    pump_stations: FeatureValue | None = None
    rlm: FeatureValue | None = None
    capacity_m3d: FeatureValue | None = None
    value: FeatureValue | None = None
    vat_basis: FeatureValue | None = None  # net | gross | unknown
    duration_months: FeatureValue | None = None
    start_date: FeatureValue | None = None
    voivodeship: FeatureValue | None = None
    location: FeatureValue | None = None
    funding: FeatureValue | None = None
    cues: dict[str, FeatureValue] = Field(default_factory=dict)  # land, permits, environment, operator ...
    extra: dict[str, FeatureValue] = Field(default_factory=dict)


class FeatureExtractIn(BaseModel):
    text: str | None = None
    document_ids: list[uuid.UUID] = Field(default_factory=list)
    llm_profile: str | None = None  # user's model choice (profile name, "rules" = no model, None = expert's order)


class FeatureExtractOut(BaseModel):
    features: Features
    missing: list[str] = Field(default_factory=list)
    questions: list[str] = Field(default_factory=list)  # e.g. "Czy kwota jest netto czy brutto?"
    model_label: str | None = None


class AnalysisCreateIn(BaseModel):
    title: str
    text: str | None = None
    document_ids: list[uuid.UUID] = Field(default_factory=list)
    features: Features | None = None  # confirmed features; if None they are extracted
    params: dict[str, Any] = Field(default_factory=dict)  # weights, k, tiers, as_of
    project_id: uuid.UUID | None = None


class NeighbourPayload(BaseModel):
    project_id: uuid.UUID
    project_code: str
    title: str
    score: float
    breakdown: list[dict[str, Any]]  # [{component, similarity, weight, contribution, detail}]
    shared_terms: list[str] = Field(default_factory=list)
    differences: list[str] = Field(default_factory=list)
    missing: list[str] = Field(default_factory=list)
    tier: str = "deep"
    outcome: dict[str, Any] = Field(default_factory=dict)  # delay_days, paid_ratio, n_changes, cancelled


class RangePayload(BaseModel):
    metric: str  # p_late | delay_days | paid_ratio | p_change | share_cancelled | offer_vs_estimate
    n: int
    period: str | None = None
    p50: float | None = None
    p80: float | None = None
    p95: float | None = None
    estimate: float | None = None
    ci_low: float | None = None
    ci_high: float | None = None
    fallback_level: str  # neighbours | subsector | wodkan | works
    case_ids: list[uuid.UUID] = Field(default_factory=list)
    formula: str | None = None


class AnalysisItemOut(ReviewFields):
    id: uuid.UUID
    analysis_id: uuid.UUID
    kind: Literal["neighbour", "range", "assessment", "flag", "action", "clause", "lesson", "checklist"]
    ord: int = 0
    label: BlockLabel
    title: str | None = None
    payload: dict[str, Any] = Field(default_factory=dict)
    ref_project_id: uuid.UUID | None = None
    risk_codes: list[str] = Field(default_factory=list)
    excluded: bool = False


class AnalysisOut(ReviewFields):
    id: uuid.UUID
    title: str
    input_text: str | None = None
    features: dict[str, Any] = Field(default_factory=dict)
    params: dict[str, Any] = Field(default_factory=dict)
    summary: dict[str, Any] = Field(default_factory=dict)
    excluded_project_ids: list[uuid.UUID] = Field(default_factory=list)
    llm_profile: str | None = None
    created_by: str | None = None
    created_at: dt.datetime | None = None
    version: int = 1
    items: list[AnalysisItemOut] = Field(default_factory=list)


class AnalysisListItem(BaseModel):
    id: uuid.UUID
    title: str
    status: str
    created_at: dt.datetime | None = None
    created_by: str | None = None
    subsector_main: str | None = None
    n_neighbours: int = 0
    n_flags: int = 0


class AnalysisItemPatch(BaseModel):
    status: Literal["approved", "rejected", "edited", "proposed"] | None = None
    excluded: bool | None = None  # for neighbours: exclude + recompute
    payload: dict[str, Any] | None = None
    comment: str | None = None
