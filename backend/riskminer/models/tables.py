"""Full Postgres schema (frozen in Phase 0; later changes = one migration via the main session).

Conventions
- `id` is a uuid5 from natural keys (see riskminer.ids.make_id); upserts use ON CONFLICT (id).
- Review-able rows carry `status` (ReviewStatus) and `method`/`confidence`; everything the system
  generates starts as `proposed`. Rows with status approved/edited/rejected are never overwritten by a
  rerun – the pipeline writes a proposal diff instead (see `proposal` column / review table).
- Every fact/link/event/conclusion points at `evidence` rows (evidence_ids) or carries a `derivation`
  (input evidence ids + formula).
"""

from __future__ import annotations

import datetime as dt
import enum
import uuid
from decimal import Decimal
from typing import Any

from pgvector.sqlalchemy import Vector
from sqlalchemy import (
    BigInteger,
    Boolean,
    Date,
    DateTime,
    Float,
    ForeignKey,
    Index,
    Integer,
    Numeric,
    String,
    Text,
    UniqueConstraint,
    func,
)
from sqlalchemy.dialects.postgresql import JSONB, TSVECTOR, UUID
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column

EMBED_DIM = 384


class Base(DeclarativeBase):
    type_annotation_map = {
        dict[str, Any]: JSONB,
        list[Any]: JSONB,
        uuid.UUID: UUID(as_uuid=True),
    }


class ReviewStatus(str, enum.Enum):
    proposed = "proposed"
    approved = "approved"
    edited = "edited"
    rejected = "rejected"


class Tier(str, enum.Enum):
    deep = "deep"
    auto = "auto"


class TS:
    created_at: Mapped[dt.datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[dt.datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )


class Reviewable:
    status: Mapped[str] = mapped_column(String(16), default=ReviewStatus.proposed.value, index=True)
    method: Mapped[str | None] = mapped_column(String(32))  # rule | llm | expert | import | key | fuzzy ...
    confidence: Mapped[float | None] = mapped_column(Float)
    evidence_ids: Mapped[list[Any]] = mapped_column(JSONB, default=list)
    # pending machine proposal for an already-reviewed row (rerun never overwrites reviewed rows)
    proposal: Mapped[dict[str, Any] | None] = mapped_column(JSONB)
    reviewed_by: Mapped[str | None] = mapped_column(String(64))
    reviewed_at: Mapped[dt.datetime | None] = mapped_column(DateTime(timezone=True))


def pk() -> Mapped[uuid.UUID]:
    return mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)


def fk(target: str, nullable: bool = True, ondelete: str = "SET NULL") -> Mapped[Any]:
    return mapped_column(UUID(as_uuid=True), ForeignKey(target, ondelete=ondelete), nullable=nullable, index=True)


# ---------------------------------------------------------------- sources, raw store, evidence


class Source(TS, Base):
    """A data source (connector or import) with its licence."""

    __tablename__ = "source"
    id: Mapped[uuid.UUID] = pk()
    code: Mapped[str] = mapped_column(String(48), unique=True)  # bzp, bzp_zip, vat_whitelist, nik, xlsx, upload ...
    name: Mapped[str] = mapped_column(String(255))
    base_url: Mapped[str | None] = mapped_column(Text)
    licence: Mapped[str | None] = mapped_column(Text)
    data_location: Mapped[str | None] = mapped_column(String(16))
    notes: Mapped[str | None] = mapped_column(Text)


class RawRecord(TS, Base):
    """Every fetched response / imported file kept as-is (raw store)."""

    __tablename__ = "raw_record"
    __table_args__ = (UniqueConstraint("source_code", "key", "sha256"),)
    id: Mapped[uuid.UUID] = pk()
    source_code: Mapped[str] = mapped_column(String(48), index=True)
    key: Mapped[str] = mapped_column(Text, index=True)  # e.g. notice objectId, query hash, file name
    url: Mapped[str | None] = mapped_column(Text)  # permanent URL if any
    retrieved_from: Mapped[str | None] = mapped_column(Text)  # actual URL fetched (mirror, zip path)
    retrieved_at: Mapped[dt.datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    sha256: Mapped[str] = mapped_column(String(64))
    content_type: Mapped[str | None] = mapped_column(String(128))
    payload: Mapped[dict[str, Any] | None] = mapped_column(JSONB)  # JSON body
    blob_path: Mapped[str | None] = mapped_column(Text)  # binary body on disk (raw_store_dir)
    op_log_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True))


class Evidence(TS, Base):
    """Where a fact comes from: source + permanent URL + locator + verbatim quote (or a derivation)."""

    __tablename__ = "evidence"
    id: Mapped[uuid.UUID] = pk()
    source_code: Mapped[str] = mapped_column(String(48), index=True)
    kind: Mapped[str] = mapped_column(String(32))  # notice_section | pdf_page | docx_paragraph | xlsx_cell | api_field | url | derivation | expert
    url: Mapped[str | None] = mapped_column(Text)  # permanent (ezamowienia.gov.pl ...)
    retrieved_from: Mapped[str | None] = mapped_column(Text)
    retrieved_at: Mapped[dt.datetime | None] = mapped_column(DateTime(timezone=True))
    # {section, label, part_no, page, paragraph, sheet, row, column, start, end, field}
    locator: Mapped[dict[str, Any]] = mapped_column(JSONB, default=dict)
    quote: Mapped[str | None] = mapped_column(Text)
    quote_verified: Mapped[bool | None] = mapped_column(Boolean)
    notice_id: Mapped[uuid.UUID | None] = fk("notice.id")
    document_id: Mapped[uuid.UUID | None] = fk("document.id")
    chunk_id: Mapped[uuid.UUID | None] = fk("chunk.id")
    raw_record_id: Mapped[uuid.UUID | None] = fk("raw_record.id")
    import_sha256: Mapped[str | None] = mapped_column(String(64))
    # for calculations: {"inputs": [evidence ids], "formula": "...", "values": {...}}
    derivation: Mapped[dict[str, Any] | None] = mapped_column(JSONB)
    created_by: Mapped[str | None] = mapped_column(String(64))


# ---------------------------------------------------------------- entities, projects, procedures


class Entity(TS, Base):
    __tablename__ = "entity"
    id: Mapped[uuid.UUID] = pk()
    name: Mapped[str] = mapped_column(Text)
    nip: Mapped[str | None] = mapped_column(String(10), index=True)
    regon: Mapped[str | None] = mapped_column(String(14), index=True)
    krs: Mapped[str | None] = mapped_column(String(10))
    role: Mapped[str | None] = mapped_column(String(32))  # beneficiary | buyer | contractor
    entity_type: Mapped[str | None] = mapped_column(Text)
    city: Mapped[str | None] = mapped_column(Text)
    province: Mapped[str | None] = mapped_column(String(8))
    country: Mapped[str | None] = mapped_column(String(4))
    verified_by: Mapped[list[Any]] = mapped_column(JSONB, default=list)  # ["BZP","VAT","KRS"]
    vat_status: Mapped[str | None] = mapped_column(String(32))
    natural_person_flag: Mapped[bool] = mapped_column(Boolean, default=False)
    aliases: Mapped[list[Any]] = mapped_column(JSONB, default=list)
    evidence_ids: Mapped[list[Any]] = mapped_column(JSONB, default=list)


class Project(TS, Reviewable, Base):
    __tablename__ = "project"
    id: Mapped[uuid.UUID] = pk()
    code: Mapped[str] = mapped_column(String(32), unique=True)  # RM-2026-001, or AUTO-<ocid-short>
    title: Mapped[str] = mapped_column(Text)
    description: Mapped[str | None] = mapped_column(Text)
    beneficiary_id: Mapped[uuid.UUID | None] = fk("entity.id")
    country: Mapped[str | None] = mapped_column(String(32))
    teryt: Mapped[str | None] = mapped_column(String(8))
    voivodeship: Mapped[str | None] = mapped_column(String(64))
    city: Mapped[str | None] = mapped_column(Text)
    sector: Mapped[str] = mapped_column(String(32), default="wodkan")
    subsector_main: Mapped[str | None] = mapped_column(String(64))
    subsector_extra: Mapped[list[Any]] = mapped_column(JSONB, default=list)
    work_type: Mapped[str | None] = mapped_column(String(64))  # budowa | przebudowa | rozbudowa | modernizacja
    formula: Mapped[str | None] = mapped_column(String(64))  # tradycyjna | zaprojektuj i wybuduj
    order_type: Mapped[str | None] = mapped_column(String(64))
    legal_regime: Mapped[str | None] = mapped_column(Text)
    currency: Mapped[str | None] = mapped_column(String(8))
    project_status: Mapped[str | None] = mapped_column(String(64))  # Zakończone ...
    funding: Mapped[str | None] = mapped_column(Text)  # KPO B3.1.1, PROW, ...
    project_value: Mapped[Decimal | None] = mapped_column(Numeric(16, 2))
    grant_value: Mapped[Decimal | None] = mapped_column(Numeric(16, 2))
    public_id_type: Mapped[str | None] = mapped_column(String(64))  # Ogłoszenie BZP | Projekt KPO
    public_id_value: Mapped[str | None] = mapped_column(String(128), index=True)
    record_scope: Mapped[str | None] = mapped_column(String(64))  # całe postępowanie | część N
    part_no: Mapped[int | None] = mapped_column(Integer)
    record_source: Mapped[str | None] = mapped_column(Text)
    record_date: Mapped[dt.date | None] = mapped_column(Date)
    record_version: Mapped[str | None] = mapped_column(String(16))
    annotation: Mapped[str | None] = mapped_column(Text)
    tier: Mapped[str] = mapped_column(String(8), default=Tier.deep.value, index=True)
    features: Mapped[dict[str, Any]] = mapped_column(JSONB, default=dict)  # km, rlm, connections... (+evidence)
    import_row: Mapped[dict[str, Any] | None] = mapped_column(JSONB)  # raw xlsx row
    exemplary: Mapped[bool] = mapped_column(Boolean, default=False)


class Procedure(TS, Base):
    __tablename__ = "procedure"
    id: Mapped[uuid.UUID] = pk()
    ocid: Mapped[str | None] = mapped_column(String(80), unique=True)  # tenderId
    bzp_number: Mapped[str | None] = mapped_column(String(32), index=True)  # 2023/BZP 00110672 (no /01)
    title: Mapped[str | None] = mapped_column(Text)
    cpv_main: Mapped[str | None] = mapped_column(String(16), index=True)
    cpv_extra: Mapped[list[Any]] = mapped_column(JSONB, default=list)
    mode: Mapped[str | None] = mapped_column(Text)
    order_type: Mapped[str | None] = mapped_column(String(32))
    buyer_id: Mapped[uuid.UUID | None] = fk("entity.id")
    buyer_nip: Mapped[str | None] = mapped_column(String(10), index=True)
    est_value_net: Mapped[Decimal | None] = mapped_column(Numeric(16, 2))
    budget_gross: Mapped[Decimal | None] = mapped_column(Numeric(16, 2))  # kwota na sfinansowanie (TenderResult)
    planned_period_text: Mapped[str | None] = mapped_column(Text)
    planned_days: Mapped[int | None] = mapped_column(Integer)
    parts: Mapped[int | None] = mapped_column(Integer)
    eu_funded: Mapped[bool | None] = mapped_column(Boolean)
    eu_project_ref: Mapped[str | None] = mapped_column(Text)
    platform_url: Mapped[str | None] = mapped_column(Text)
    ted_refs: Mapped[list[Any]] = mapped_column(JSONB, default=list)
    related_procedure_ids: Mapped[list[Any]] = mapped_column(JSONB, default=list)  # cancelled / repeated siblings
    first_published_at: Mapped[dt.datetime | None] = mapped_column(DateTime(timezone=True))
    offers_count: Mapped[int | None] = mapped_column(Integer)
    cancelled: Mapped[bool | None] = mapped_column(Boolean)
    cancel_basis: Mapped[str | None] = mapped_column(Text)
    sector: Mapped[str | None] = mapped_column(String(32))
    subsector_main: Mapped[str | None] = mapped_column(String(64))
    tier: Mapped[str] = mapped_column(String(8), default=Tier.auto.value, index=True)
    watched: Mapped[bool] = mapped_column(Boolean, default=False)
    meta: Mapped[dict[str, Any]] = mapped_column(JSONB, default=dict)
    evidence_ids: Mapped[list[Any]] = mapped_column(JSONB, default=list)


class ProjectProcedure(TS, Reviewable, Base):
    """Link project → procedure (optionally a lot). `components` explains the score with evidence."""

    __tablename__ = "project_procedure"
    __table_args__ = (UniqueConstraint("project_id", "procedure_id", "part_no"),)
    id: Mapped[uuid.UUID] = pk()
    project_id: Mapped[uuid.UUID] = fk("project.id", nullable=False, ondelete="CASCADE")
    procedure_id: Mapped[uuid.UUID] = fk("procedure.id", nullable=False, ondelete="CASCADE")
    part_no: Mapped[int | None] = mapped_column(Integer)
    # method: kpo_ref | notice_no | ocid | xref | fuzzy | expert
    # components: [{name, score, weight, detail, evidence_id}]
    components: Mapped[list[Any]] = mapped_column(JSONB, default=list)
    alternatives: Mapped[list[Any]] = mapped_column(JSONB, default=list)  # decoys / other candidates with scores
    is_override: Mapped[bool] = mapped_column(Boolean, default=False)  # expert relink, survives rebuilds
    rank: Mapped[int] = mapped_column(Integer, default=1)


class Notice(TS, Base):
    __tablename__ = "notice"
    id: Mapped[uuid.UUID] = pk()
    object_id: Mapped[str] = mapped_column(String(64), unique=True)
    notice_number: Mapped[str] = mapped_column(String(32), index=True)  # 2023/BZP 00396503/01
    bzp_number: Mapped[str | None] = mapped_column(String(32), index=True)
    notice_type: Mapped[str] = mapped_column(String(40), index=True)
    procedure_id: Mapped[uuid.UUID | None] = fk("procedure.id")
    ocid: Mapped[str | None] = mapped_column(String(80), index=True)
    published_at: Mapped[dt.datetime | None] = mapped_column(DateTime(timezone=True), index=True)
    title: Mapped[str | None] = mapped_column(Text)
    org_name: Mapped[str | None] = mapped_column(Text)
    org_nip: Mapped[str | None] = mapped_column(String(10), index=True)
    org_city: Mapped[str | None] = mapped_column(Text)
    org_province: Mapped[str | None] = mapped_column(String(8))
    cpv: Mapped[str | None] = mapped_column(Text)
    order_type: Mapped[str | None] = mapped_column(String(32))
    below_eu: Mapped[bool | None] = mapped_column(Boolean)
    contractors: Mapped[list[Any]] = mapped_column(JSONB, default=list)
    url: Mapped[str | None] = mapped_column(Text)  # permanent notice-details page
    pdf_url: Mapped[str | None] = mapped_column(Text)
    retrieved_from: Mapped[str | None] = mapped_column(Text)
    retrieved_at: Mapped[dt.datetime | None] = mapped_column(DateTime(timezone=True))
    raw_record_id: Mapped[uuid.UUID | None] = fk("raw_record.id")
    canonical_text: Mapped[str | None] = mapped_column(Text)
    # [{section, label, value, offset, part_no}] – offsets into canonical_text
    sections: Mapped[list[Any]] = mapped_column(JSONB, default=list)
    xrefs: Mapped[list[Any]] = mapped_column(JSONB, default=list)  # [{section, notice_number, kind}]
    parsed: Mapped[dict[str, Any]] = mapped_column(JSONB, default=dict)  # type-specific parsed fields
    parser_version: Mapped[str | None] = mapped_column(String(16))
    tier: Mapped[str] = mapped_column(String(8), default=Tier.auto.value, index=True)


class Contract(TS, Reviewable, Base):
    __tablename__ = "contract"
    __table_args__ = (UniqueConstraint("procedure_id", "part_no", "contractor_id"),)
    id: Mapped[uuid.UUID] = pk()
    procedure_id: Mapped[uuid.UUID] = fk("procedure.id", nullable=False, ondelete="CASCADE")
    part_no: Mapped[int | None] = mapped_column(Integer)
    contractor_id: Mapped[uuid.UUID | None] = fk("entity.id")
    result_notice_id: Mapped[uuid.UUID | None] = fk("notice.id")
    performing_notice_id: Mapped[uuid.UUID | None] = fk("notice.id")
    signed_at: Mapped[dt.date | None] = mapped_column(Date)
    value_gross: Mapped[Decimal | None] = mapped_column(Numeric(16, 2))
    value_net: Mapped[Decimal | None] = mapped_column(Numeric(16, 2))
    offers_count: Mapped[int | None] = mapped_column(Integer)
    lowest_offer: Mapped[Decimal | None] = mapped_column(Numeric(16, 2))
    highest_offer: Mapped[Decimal | None] = mapped_column(Numeric(16, 2))
    planned_end: Mapped[dt.date | None] = mapped_column(Date)
    planned_days: Mapped[int | None] = mapped_column(Integer)
    actual_end: Mapped[dt.date | None] = mapped_column(Date)
    paid_gross: Mapped[Decimal | None] = mapped_column(Numeric(16, 2))
    on_time: Mapped[bool | None] = mapped_column(Boolean)
    performed: Mapped[bool | None] = mapped_column(Boolean)
    proper: Mapped[bool | None] = mapped_column(Boolean)
    n_changes: Mapped[int | None] = mapped_column(Integer)
    terms_source: Mapped[str | None] = mapped_column(String(64))  # umowa | PPU | SWU | ogłoszenie
    meta: Mapped[dict[str, Any]] = mapped_column(JSONB, default=dict)


class ContractChange(TS, Reviewable, Base):
    __tablename__ = "contract_change"
    __table_args__ = (UniqueConstraint("contract_id", "notice_id", "change_no"),)
    id: Mapped[uuid.UUID] = pk()
    contract_id: Mapped[uuid.UUID | None] = fk("contract.id", ondelete="CASCADE")
    procedure_id: Mapped[uuid.UUID | None] = fk("procedure.id", ondelete="CASCADE")
    notice_id: Mapped[uuid.UUID | None] = fk("notice.id")
    change_no: Mapped[int] = mapped_column(Integer, default=1)
    change_date: Mapped[dt.date | None] = mapped_column(Date)
    legal_basis: Mapped[str | None] = mapped_column(Text)
    legal_basis_code: Mapped[str | None] = mapped_column(String(32))  # 455.1.1 | 455.1.4 | 455.2 ...
    reason: Mapped[str | None] = mapped_column(Text)  # verbatim
    description: Mapped[str | None] = mapped_column(Text)  # verbatim
    change_kind: Mapped[list[Any]] = mapped_column(JSONB, default=list)  # termin | wynagrodzenie | zakres | wykonawca
    value_delta: Mapped[Decimal | None] = mapped_column(Numeric(16, 2))
    new_value: Mapped[Decimal | None] = mapped_column(Numeric(16, 2))
    new_end: Mapped[dt.date | None] = mapped_column(Date)


class Fact(TS, Reviewable, Base):
    """Any atomic fact (value with unit) about any subject, with evidence or derivation."""

    __tablename__ = "fact"
    id: Mapped[uuid.UUID] = pk()
    subject_type: Mapped[str] = mapped_column(String(32), index=True)  # project | procedure | contract | analysis
    subject_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), index=True)
    fact_type: Mapped[str] = mapped_column(String(64), index=True)  # length_km, rlm, value, delay_days ...
    value_num: Mapped[float | None] = mapped_column(Float)
    value_text: Mapped[str | None] = mapped_column(Text)
    value_date: Mapped[dt.date | None] = mapped_column(Date)
    unit: Mapped[str | None] = mapped_column(String(32))
    vat_basis: Mapped[str] = mapped_column(String(8), default="unknown")  # net | gross | unknown
    derivation: Mapped[dict[str, Any] | None] = mapped_column(JSONB)


# ---------------------------------------------------------------- documents


class Document(TS, Reviewable, Base):
    __tablename__ = "document"
    id: Mapped[uuid.UUID] = pk()
    project_id: Mapped[uuid.UUID | None] = fk("project.id", ondelete="CASCADE")
    procedure_id: Mapped[uuid.UUID | None] = fk("procedure.id")
    analysis_id: Mapped[uuid.UUID | None] = fk("analysis.id", ondelete="CASCADE")
    doc_type: Mapped[str | None] = mapped_column(String(64))  # SWZ | PFU | PPU | OPZ | aneks | NIK | ...
    phase: Mapped[str | None] = mapped_column(String(64))
    title: Mapped[str | None] = mapped_column(Text)
    url: Mapped[str | None] = mapped_column(Text)
    file_path: Mapped[str | None] = mapped_column(Text)
    file_name: Mapped[str | None] = mapped_column(Text)
    mime: Mapped[str | None] = mapped_column(String(128))
    sha256: Mapped[str | None] = mapped_column(String(64), index=True)
    version: Mapped[int] = mapped_column(Integer, default=1)
    pages: Mapped[int | None] = mapped_column(Integer)
    source_code: Mapped[str | None] = mapped_column(String(48))
    retrieved_at: Mapped[dt.datetime | None] = mapped_column(DateTime(timezone=True))
    uploaded_by: Mapped[str | None] = mapped_column(String(64))
    text_status: Mapped[str | None] = mapped_column(String(32))  # ok | no_text_layer | error
    meta: Mapped[dict[str, Any]] = mapped_column(JSONB, default=dict)


class Chunk(TS, Base):
    __tablename__ = "chunk"
    __table_args__ = (Index("ix_chunk_tsv", "tsv", postgresql_using="gin"),)
    id: Mapped[uuid.UUID] = pk()
    document_id: Mapped[uuid.UUID | None] = fk("document.id", ondelete="CASCADE")
    notice_id: Mapped[uuid.UUID | None] = fk("notice.id", ondelete="CASCADE")
    ord: Mapped[int] = mapped_column(Integer, default=0)
    page: Mapped[int | None] = mapped_column(Integer)
    paragraph: Mapped[int | None] = mapped_column(Integer)
    section: Mapped[str | None] = mapped_column(String(32))
    start: Mapped[int | None] = mapped_column(Integer)
    end: Mapped[int | None] = mapped_column(Integer)
    locator: Mapped[dict[str, Any]] = mapped_column(JSONB, default=dict)
    text: Mapped[str] = mapped_column(Text)
    tsv: Mapped[Any] = mapped_column(TSVECTOR, nullable=True)
    embedding: Mapped[Any] = mapped_column(Vector(EMBED_DIM), nullable=True)


# ---------------------------------------------------------------- knowledge


class RiskCategory(TS, Reviewable, Base):
    __tablename__ = "risk_category"
    __table_args__ = (UniqueConstraint("sector", "code"),)
    id: Mapped[uuid.UUID] = pk()
    sector: Mapped[str] = mapped_column(String(32), default="wodkan")
    code: Mapped[str] = mapped_column(String(16))  # R01..R15, or P-xxx for proposed
    name: Mapped[str] = mapped_column(Text)
    effects: Mapped[str | None] = mapped_column(Text)
    description: Mapped[str | None] = mapped_column(Text)
    keywords: Mapped[list[Any]] = mapped_column(JSONB, default=list)
    parent_code: Mapped[str | None] = mapped_column(String(16))
    version: Mapped[int] = mapped_column(Integer, default=1)


class Lesson(TS, Reviewable, Base):
    """case → cause → signal → effect → recommendation."""

    __tablename__ = "lesson"
    id: Mapped[uuid.UUID] = pk()
    sector: Mapped[str] = mapped_column(String(32), default="wodkan")
    project_id: Mapped[uuid.UUID | None] = fk("project.id", ondelete="CASCADE")
    document_id: Mapped[uuid.UUID | None] = fk("document.id")
    source_kind: Mapped[str | None] = mapped_column(String(32))  # case | NIK | KIO | expert
    title: Mapped[str | None] = mapped_column(Text)
    cause: Mapped[str | None] = mapped_column(Text)
    signal: Mapped[str | None] = mapped_column(Text)
    effect: Mapped[str | None] = mapped_column(Text)
    recommendation: Mapped[str | None] = mapped_column(Text)
    risk_codes: Mapped[list[Any]] = mapped_column(JSONB, default=list)
    subsectors: Mapped[list[Any]] = mapped_column(JSONB, default=list)


class Clause(TS, Reviewable, Base):
    __tablename__ = "clause"
    id: Mapped[uuid.UUID] = pk()
    sector: Mapped[str] = mapped_column(String(32), default="wodkan")
    code: Mapped[str | None] = mapped_column(String(32), index=True)
    risk_code: Mapped[str | None] = mapped_column(String(16), index=True)
    title: Mapped[str | None] = mapped_column(Text)
    trigger: Mapped[str | None] = mapped_column(Text)
    legal_basis: Mapped[str | None] = mapped_column(Text)  # e.g. art. 455 ust. 1 pkt 1 Pzp
    text: Mapped[str] = mapped_column(Text)
    version: Mapped[int] = mapped_column(Integer, default=1)


class KnowledgeTable(TS, Base):
    """Versioned expert table (catalog, rules, checklists, weights, thresholds, routing ...).

    The row with the highest `version` per (sector, name) is current; old versions are kept.
    """

    __tablename__ = "knowledge_table"
    __table_args__ = (UniqueConstraint("sector", "name", "version"),)
    id: Mapped[uuid.UUID] = pk()
    sector: Mapped[str] = mapped_column(String(32), default="wodkan")
    name: Mapped[str] = mapped_column(String(64))  # risks, subsectors, phases, checklist, porady, art455, weights ...
    version: Mapped[int] = mapped_column(Integer, default=1)
    title: Mapped[str | None] = mapped_column(Text)
    columns: Mapped[list[Any]] = mapped_column(JSONB, default=list)  # [{key, label, type}]
    rows: Mapped[list[Any]] = mapped_column(JSONB, default=list)
    source_file: Mapped[str | None] = mapped_column(Text)
    source_sha256: Mapped[str | None] = mapped_column(String(64))
    edited_by: Mapped[str | None] = mapped_column(String(64))
    comment: Mapped[str | None] = mapped_column(Text)


class Rule(TS, Base):
    __tablename__ = "rule"
    __table_args__ = (UniqueConstraint("sector", "kind", "key", "version"),)
    id: Mapped[uuid.UUID] = pk()
    sector: Mapped[str] = mapped_column(String(32), default="wodkan")
    kind: Mapped[str] = mapped_column(String(32))  # event_rule | cause_pattern | blacklist | link_override | flag
    key: Mapped[str] = mapped_column(String(128))
    version: Mapped[int] = mapped_column(Integer, default=1)
    body: Mapped[dict[str, Any]] = mapped_column(JSONB, default=dict)
    active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_by: Mapped[str | None] = mapped_column(String(64))


class Setting(TS, Base):
    __tablename__ = "setting"
    key: Mapped[str] = mapped_column(String(128), primary_key=True)
    value: Mapped[dict[str, Any]] = mapped_column(JSONB, default=dict)
    version: Mapped[int] = mapped_column(Integer, default=1)
    updated_by: Mapped[str | None] = mapped_column(String(64))


class SectorProfile(TS, Base):
    __tablename__ = "sector_profile"
    id: Mapped[uuid.UUID] = pk()
    code: Mapped[str] = mapped_column(String(32), unique=True)  # wodkan | drogi
    name: Mapped[str] = mapped_column(Text)
    knowledge_path: Mapped[str] = mapped_column(Text)
    cpv_prefixes: Mapped[list[Any]] = mapped_column(JSONB, default=list)
    active: Mapped[bool] = mapped_column(Boolean, default=True)


# ---------------------------------------------------------------- events, issues, review


class Event(TS, Reviewable, Base):
    __tablename__ = "event"
    id: Mapped[uuid.UUID] = pk()
    project_id: Mapped[uuid.UUID | None] = fk("project.id", ondelete="CASCADE")
    procedure_id: Mapped[uuid.UUID | None] = fk("procedure.id", ondelete="CASCADE")
    contract_id: Mapped[uuid.UUID | None] = fk("contract.id", ondelete="CASCADE")
    change_id: Mapped[uuid.UUID | None] = fk("contract_change.id", ondelete="CASCADE")
    notice_id: Mapped[uuid.UUID | None] = fk("notice.id")
    document_id: Mapped[uuid.UUID | None] = fk("document.id", ondelete="CASCADE")
    # late | paid_above_value | change_deadline | change_value | change_scope | change_contractor |
    # not_performed | terminated | improper | cancelled | repeated | single_offer | offers_above_budget |
    # kio_appeal | doc_fragment
    event_type: Mapped[str] = mapped_column(String(40), index=True)
    event_date: Mapped[dt.date | None] = mapped_column(Date)
    risk_codes: Mapped[list[Any]] = mapped_column(JSONB, default=list)
    title: Mapped[str | None] = mapped_column(Text)
    cause: Mapped[str | None] = mapped_column(Text)
    signal: Mapped[str | None] = mapped_column(Text)  # doc fragments: warunek/sygnał
    effect: Mapped[str | None] = mapped_column(Text)
    effect_days: Mapped[float | None] = mapped_column(Float)
    effect_pln: Mapped[Decimal | None] = mapped_column(Numeric(16, 2))
    effect_pct: Mapped[float | None] = mapped_column(Float)
    mitigation: Mapped[str | None] = mapped_column(Text)
    mitigation_effect: Mapped[str | None] = mapped_column(String(32))  # skuteczne | częściowo | nieskuteczne | brak danych
    mitigation_rule: Mapped[str | None] = mapped_column(Text)
    quote: Mapped[str | None] = mapped_column(Text)
    model_label: Mapped[str | None] = mapped_column(String(128))  # provider/model when method=llm
    exemplary: Mapped[bool] = mapped_column(Boolean, default=False)
    tier: Mapped[str] = mapped_column(String(8), default=Tier.deep.value, index=True)


class DataIssue(TS, Reviewable, Base):
    """Braki danych / sprzeczności / validation problems (expert's 4 states)."""

    __tablename__ = "data_issue"
    id: Mapped[uuid.UUID] = pk()
    project_id: Mapped[uuid.UUID | None] = fk("project.id", ondelete="CASCADE")
    procedure_id: Mapped[uuid.UUID | None] = fk("procedure.id", ondelete="CASCADE")
    analysis_id: Mapped[uuid.UUID | None] = fk("analysis.id", ondelete="CASCADE")
    kind: Mapped[str] = mapped_column(String(32))  # missing | contradiction | validation | organizer_error
    field: Mapped[str | None] = mapped_column(String(128))
    # 4 states: potwierdzone | częściowe | brak | sprzeczne
    state: Mapped[str | None] = mapped_column(String(32))
    message: Mapped[str] = mapped_column(Text)
    what_to_add: Mapped[str | None] = mapped_column(Text)
    impact: Mapped[str | None] = mapped_column(Text)  # how the gap limits the analysis


class Review(Base):
    """Append-only audit trail of every human/system change."""

    __tablename__ = "review"
    id: Mapped[uuid.UUID] = pk()
    object_type: Mapped[str] = mapped_column(String(40), index=True)
    object_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), index=True)
    action: Mapped[str] = mapped_column(String(32))  # create | accept | edit | reject | relink | exemplary | bulk_confirm | rerun_proposal
    before: Mapped[dict[str, Any] | None] = mapped_column(JSONB)
    after: Mapped[dict[str, Any] | None] = mapped_column(JSONB)
    comment: Mapped[str | None] = mapped_column(Text)
    reviewer: Mapped[str | None] = mapped_column(String(64))
    at: Mapped[dt.datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), index=True)


# ---------------------------------------------------------------- analysis (path B)


class Analysis(TS, Reviewable, Base):
    __tablename__ = "analysis"
    id: Mapped[uuid.UUID] = pk()
    title: Mapped[str] = mapped_column(Text)
    input_text: Mapped[str | None] = mapped_column(Text)
    features: Mapped[dict[str, Any]] = mapped_column(JSONB, default=dict)  # confirmed features (+source per field)
    params: Mapped[dict[str, Any]] = mapped_column(JSONB, default=dict)  # weights, k, tiers, as_of
    summary: Mapped[dict[str, Any]] = mapped_column(JSONB, default=dict)
    excluded_project_ids: Mapped[list[Any]] = mapped_column(JSONB, default=list)
    llm_profile: Mapped[str | None] = mapped_column(String(64))
    created_by: Mapped[str | None] = mapped_column(String(64))
    project_id: Mapped[uuid.UUID | None] = fk("project.id")  # when analysing an existing/unfinished project
    version: Mapped[int] = mapped_column(Integer, default=1)


class AnalysisItem(TS, Reviewable, Base):
    __tablename__ = "analysis_item"
    id: Mapped[uuid.UUID] = pk()
    analysis_id: Mapped[uuid.UUID] = fk("analysis.id", nullable=False, ondelete="CASCADE")
    kind: Mapped[str] = mapped_column(String(32), index=True)  # neighbour | range | assessment | flag | action | clause | lesson
    ord: Mapped[int] = mapped_column(Integer, default=0)
    label: Mapped[str] = mapped_column(String(32))  # dane_zrodlowe | obliczenia | wniosek_modelu
    title: Mapped[str | None] = mapped_column(Text)
    payload: Mapped[dict[str, Any]] = mapped_column(JSONB, default=dict)
    ref_project_id: Mapped[uuid.UUID | None] = fk("project.id")
    risk_codes: Mapped[list[Any]] = mapped_column(JSONB, default=list)
    excluded: Mapped[bool] = mapped_column(Boolean, default=False)


# ---------------------------------------------------------------- ops


class Alert(TS, Base):
    __tablename__ = "alert"
    id: Mapped[uuid.UUID] = pk()
    project_id: Mapped[uuid.UUID | None] = fk("project.id", ondelete="CASCADE")
    procedure_id: Mapped[uuid.UUID | None] = fk("procedure.id", ondelete="CASCADE")
    notice_id: Mapped[uuid.UUID | None] = fk("notice.id")
    kind: Mapped[str] = mapped_column(String(32))  # new_notice | deadline_passed | data_quality | reanalysis
    severity: Mapped[str] = mapped_column(String(16), default="info")
    message: Mapped[str] = mapped_column(Text)
    payload: Mapped[dict[str, Any]] = mapped_column(JSONB, default=dict)
    read: Mapped[bool] = mapped_column(Boolean, default=False)


class Job(TS, Base):
    __tablename__ = "job"
    id: Mapped[uuid.UUID] = pk()
    kind: Mapped[str] = mapped_column(String(48), index=True)  # import | enrich | harvest | extract | analyse | export | monitor
    params: Mapped[dict[str, Any]] = mapped_column(JSONB, default=dict)
    state: Mapped[str] = mapped_column(String(16), default="queued", index=True)  # queued | running | done | failed
    progress: Mapped[float] = mapped_column(Float, default=0.0)
    message: Mapped[str | None] = mapped_column(Text)
    result: Mapped[dict[str, Any] | None] = mapped_column(JSONB)  # run report
    error: Mapped[str | None] = mapped_column(Text)
    attempts: Mapped[int] = mapped_column(Integer, default=0)
    started_at: Mapped[dt.datetime | None] = mapped_column(DateTime(timezone=True))
    finished_at: Mapped[dt.datetime | None] = mapped_column(DateTime(timezone=True))
    created_by: Mapped[str | None] = mapped_column(String(64))


class OpLog(Base):
    __tablename__ = "op_log"
    id: Mapped[uuid.UUID] = pk()
    job_id: Mapped[uuid.UUID | None] = fk("job.id", ondelete="SET NULL")
    connector: Mapped[str] = mapped_column(String(48), index=True)
    operation: Mapped[str] = mapped_column(String(64))
    url: Mapped[str | None] = mapped_column(Text)
    params: Mapped[dict[str, Any]] = mapped_column(JSONB, default=dict)
    status_code: Mapped[int | None] = mapped_column(Integer)
    n_results: Mapped[int | None] = mapped_column(Integer)
    duration_ms: Mapped[int | None] = mapped_column(Integer)
    bytes: Mapped[int | None] = mapped_column(BigInteger)
    error: Mapped[str | None] = mapped_column(Text)
    at: Mapped[dt.datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), index=True)


class LLMCall(Base):
    __tablename__ = "llm_call"
    id: Mapped[uuid.UUID] = pk()
    task: Mapped[str] = mapped_column(String(48), index=True)
    profile: Mapped[str | None] = mapped_column(String(64))
    provider: Mapped[str] = mapped_column(String(32))
    model: Mapped[str | None] = mapped_column(String(128))
    data_location: Mapped[str | None] = mapped_column(String(16))
    prompt_version: Mapped[str | None] = mapped_column(String(32))
    input_hash: Mapped[str | None] = mapped_column(String(64), index=True)
    cached: Mapped[bool] = mapped_column(Boolean, default=False)
    ok: Mapped[bool] = mapped_column(Boolean, default=True)
    error: Mapped[str | None] = mapped_column(Text)
    tokens_in: Mapped[int | None] = mapped_column(Integer)
    tokens_out: Mapped[int | None] = mapped_column(Integer)
    cost_usd: Mapped[float | None] = mapped_column(Float)
    latency_ms: Mapped[int | None] = mapped_column(Integer)
    job_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True))
    at: Mapped[dt.datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), index=True)


class User(TS, Base):
    __tablename__ = "app_user"
    id: Mapped[uuid.UUID] = pk()
    username: Mapped[str] = mapped_column(String(64), unique=True)
    display_name: Mapped[str] = mapped_column(Text)
    role: Mapped[str] = mapped_column(String(16), default="expert")  # admin | expert | analyst | viewer
    password_hash: Mapped[str | None] = mapped_column(Text)
    active: Mapped[bool] = mapped_column(Boolean, default=True)
