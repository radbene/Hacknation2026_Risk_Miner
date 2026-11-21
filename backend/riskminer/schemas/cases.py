"""Case base: projects, procedures, notices, contracts, changes, links, timeline, graph."""

from __future__ import annotations

import datetime as dt
import uuid
from typing import Any, Literal

from pydantic import BaseModel, Field

from riskminer.schemas.common import ORM, ReviewFields


class EntityOut(ORM):
    id: uuid.UUID
    name: str
    nip: str | None = None
    regon: str | None = None
    krs: str | None = None
    role: str | None = None
    city: str | None = None
    province: str | None = None
    verified_by: list[str] = Field(default_factory=list)
    vat_status: str | None = None
    natural_person_flag: bool = False


class ProjectListItem(ReviewFields):
    id: uuid.UUID
    code: str
    title: str
    beneficiary_name: str | None = None
    beneficiary_nip: str | None = None
    voivodeship: str | None = None
    teryt: str | None = None
    subsector_main: str | None = None
    subsector_extra: list[str] = Field(default_factory=list)
    public_id_type: str | None = None
    public_id_value: str | None = None
    record_scope: str | None = None
    part_no: int | None = None
    project_status: str | None = None
    tier: Literal["deep", "auto"] = "deep"
    link_status: Literal["linked", "uncertain", "unlinked", "rejected"] = "unlinked"
    n_procedures: int = 0
    n_events: int = 0
    n_issues: int = 0
    n_pending_review: int = 0
    completeness: float | None = None  # 0..1


class ProjectDetail(ProjectListItem):
    description: str | None = None
    city: str | None = None
    work_type: str | None = None
    formula: str | None = None
    funding: str | None = None
    project_value: float | None = None
    grant_value: float | None = None
    annotation: str | None = None
    features: dict[str, Any] = Field(default_factory=dict)
    beneficiary: EntityOut | None = None
    import_row: dict[str, Any] | None = None
    exemplary: bool = False


class ProjectPatch(BaseModel):
    """Expert edit of any input field; every change is audited."""

    changes: dict[str, Any]
    comment: str | None = None


class SectionOut(BaseModel):
    section: str
    label: str
    value: str
    offset: int | None = None
    part_no: int | None = None


class NoticeOut(ORM):
    id: uuid.UUID
    object_id: str
    notice_number: str
    notice_type: str
    ocid: str | None = None
    procedure_id: uuid.UUID | None = None
    published_at: dt.datetime | None = None
    title: str | None = None
    org_name: str | None = None
    org_nip: str | None = None
    url: str | None = None
    pdf_url: str | None = None
    retrieved_from: str | None = None
    retrieved_at: dt.datetime | None = None
    contractors: list[dict[str, Any]] = Field(default_factory=list)
    xrefs: list[dict[str, Any]] = Field(default_factory=list)
    parsed: dict[str, Any] = Field(default_factory=dict)


class NoticeDetail(NoticeOut):
    canonical_text: str | None = None
    sections: list[SectionOut] = Field(default_factory=list)


class ProcedureOut(ORM):
    id: uuid.UUID
    ocid: str | None = None
    bzp_number: str | None = None
    title: str | None = None
    cpv_main: str | None = None
    cpv_extra: list[str] = Field(default_factory=list)
    mode: str | None = None
    buyer_nip: str | None = None
    est_value_net: float | None = None
    budget_gross: float | None = None
    planned_period_text: str | None = None
    planned_days: int | None = None
    parts: int | None = None
    eu_funded: bool | None = None
    eu_project_ref: str | None = None
    offers_count: int | None = None
    cancelled: bool | None = None
    cancel_basis: str | None = None
    first_published_at: dt.datetime | None = None
    subsector_main: str | None = None
    tier: str = "auto"
    related_procedure_ids: list[uuid.UUID] = Field(default_factory=list)
    evidence_ids: list[uuid.UUID] = Field(default_factory=list)


class ContractChangeOut(ReviewFields):
    id: uuid.UUID
    contract_id: uuid.UUID | None = None
    notice_id: uuid.UUID | None = None
    change_no: int = 1
    change_date: dt.date | None = None
    legal_basis: str | None = None
    legal_basis_code: str | None = None
    reason: str | None = None
    description: str | None = None
    change_kind: list[str] = Field(default_factory=list)
    value_delta: float | None = None
    new_value: float | None = None
    new_end: dt.date | None = None


class ContractOut(ReviewFields):
    id: uuid.UUID
    procedure_id: uuid.UUID
    part_no: int | None = None
    contractor: EntityOut | None = None
    signed_at: dt.date | None = None
    value_gross: float | None = None
    value_net: float | None = None
    offers_count: int | None = None
    planned_end: dt.date | None = None
    planned_days: int | None = None
    actual_end: dt.date | None = None
    paid_gross: float | None = None
    on_time: bool | None = None
    performed: bool | None = None
    proper: bool | None = None
    n_changes: int | None = None
    terms_source: str | None = None
    changes: list[ContractChangeOut] = Field(default_factory=list)


class LinkComponent(BaseModel):
    name: str  # kpo_ref | notice_no | nip | ocid | xref | title | cpv | date | value | location | lot
    score: float
    weight: float | None = None
    detail: str | None = None
    evidence_id: uuid.UUID | None = None


class LinkCandidate(BaseModel):
    procedure_id: uuid.UUID | None = None
    ocid: str | None = None
    bzp_number: str | None = None
    title: str | None = None
    score: float
    components: list[LinkComponent] = Field(default_factory=list)
    why_not: str | None = None


class LinkOut(ReviewFields):
    id: uuid.UUID
    project_id: uuid.UUID
    project_code: str | None = None
    procedure_id: uuid.UUID
    ocid: str | None = None
    bzp_number: str | None = None
    procedure_title: str | None = None
    part_no: int | None = None
    components: list[LinkComponent] = Field(default_factory=list)
    alternatives: list[LinkCandidate] = Field(default_factory=list)
    is_override: bool = False
    rank: int = 1


class ProjectRelinkIn(BaseModel):
    """Pick a candidate, or give an OCID / notice number (triggers a fetch)."""

    procedure_id: uuid.UUID | None = None
    ocid: str | None = None
    notice_number: str | None = None
    part_no: int | None = None
    comment: str | None = None


class TimelineItem(BaseModel):
    date: dt.date | None = None
    kind: Literal["budget", "estimate", "published", "offers", "contract", "change", "planned_end",
                  "actual_end", "paid", "cancelled", "notice", "event", "other"]
    label: str
    value: float | None = None
    planned: bool = False
    notice_id: uuid.UUID | None = None
    evidence_ids: list[uuid.UUID] = Field(default_factory=list)


class TimelineOut(BaseModel):
    project_id: uuid.UUID
    items: list[TimelineItem]
    planned_vs_actual: dict[str, Any] = Field(default_factory=dict)  # {planned_end, actual_end, delay_days, value, paid ...}


class GraphNode(BaseModel):
    id: str
    type: Literal["project", "entity", "procedure", "notice", "contract", "change", "event", "document", "source"]
    label: str
    data: dict[str, Any] = Field(default_factory=dict)


class GraphEdge(BaseModel):
    source: str
    target: str
    label: str | None = None
    method: str | None = None
    confidence: float | None = None
    status: str | None = None


class GraphOut(BaseModel):
    nodes: list[GraphNode]
    edges: list[GraphEdge]


class ImportReport(BaseModel):
    file: str
    sha256: str
    rows: int
    created: int
    updated: int
    unchanged: int
    issues: list[dict[str, Any]] = Field(default_factory=list)


class EnrichIn(BaseModel):
    project_ids: list[uuid.UUID] | None = None  # None = all deep-tier projects
    sources: list[str] | None = None  # None = all enabled connectors
    as_of: dt.date | None = None


class HarvestIn(BaseModel):
    source: Literal["bzp_zip", "bzp"] = "bzp_zip"
    date_from: dt.date | None = None
    date_to: dt.date | None = None
    limit: int | None = None
