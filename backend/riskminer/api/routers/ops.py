"""Dashboard, op log, connector health, LLM usage, licences, quality, monitoring (owner: S6)."""

from __future__ import annotations

import uuid

from fastapi import APIRouter

from riskminer.api.deps import DB, USER, CurrentUser, Session, not_implemented
from riskminer.schemas.common import Message, Page
from riskminer.schemas.ops import (
    AlertOut,
    ConnectorHealth,
    DashboardOut,
    LicenceOut,
    LLMUsageRow,
    MonitorRunIn,
    OpLogOut,
    QualityMetrics,
    WatchIn,
)

router = APIRouter(tags=["ops"])
OWNER = "S6"


@router.get("/dashboard", response_model=DashboardOut)
def dashboard(db: Session = DB):
    raise not_implemented(OWNER)


@router.get("/ops/log", response_model=Page[OpLogOut])
def op_log(connector: str | None = None, job_id: uuid.UUID | None = None, offset: int = 0, limit: int = 100,
           db: Session = DB):
    raise not_implemented(OWNER)


@router.get("/ops/connectors", response_model=list[ConnectorHealth])
def connectors(db: Session = DB):
    raise not_implemented(OWNER)


@router.get("/ops/llm-usage", response_model=list[LLMUsageRow])
def llm_usage(db: Session = DB):
    raise not_implemented(OWNER)


@router.get("/ops/licences", response_model=list[LicenceOut])
def licences():
    raise not_implemented(OWNER)


@router.get("/quality", response_model=QualityMetrics)
def quality(db: Session = DB):
    """Gold-set metrics (precision/recall of linking etc.). Computation lives in S1's link module."""
    raise not_implemented(OWNER)


@router.get("/alerts", response_model=list[AlertOut])
def alerts(unread_only: bool = False, db: Session = DB):
    raise not_implemented(OWNER)


@router.post("/monitor/watch", response_model=Message)
def watch(body: WatchIn, db: Session = DB, user: CurrentUser = USER):
    raise not_implemented(OWNER)


@router.post("/monitor/run", response_model=Message)
def monitor_run(body: MonitorRunIn, db: Session = DB, user: CurrentUser = USER):
    raise not_implemented(OWNER)
