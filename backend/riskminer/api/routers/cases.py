"""Case base (owner: S1 acquisition & linking). Projects, procedures, notices, contracts, timeline, graph."""

from __future__ import annotations

import uuid

from fastapi import APIRouter

from riskminer.api.deps import DB, USER, CurrentUser, Session, not_implemented
from riskminer.schemas.cases import (
    ContractOut,
    EntityOut,
    GraphOut,
    NoticeDetail,
    NoticeOut,
    ProcedureOut,
    ProjectDetail,
    ProjectListItem,
    ProjectPatch,
    TimelineOut,
)
from riskminer.schemas.common import Page

router = APIRouter(tags=["cases"])
OWNER = "S1"


@router.get("/projects", response_model=Page[ProjectListItem])
def list_projects(q: str | None = None, tier: str | None = "deep", status: str | None = None,
                  subsector: str | None = None, link_status: str | None = None,
                  offset: int = 0, limit: int = 50, db: Session = DB):
    raise not_implemented(OWNER)


@router.get("/projects/{project_id}", response_model=ProjectDetail)
def get_project(project_id: uuid.UUID, db: Session = DB):
    raise not_implemented(OWNER)


@router.patch("/projects/{project_id}", response_model=ProjectDetail)
def patch_project(project_id: uuid.UUID, body: ProjectPatch, db: Session = DB, user: CurrentUser = USER):
    raise not_implemented(OWNER)


@router.get("/projects/{project_id}/timeline", response_model=TimelineOut)
def project_timeline(project_id: uuid.UUID, db: Session = DB):
    raise not_implemented(OWNER)


@router.get("/projects/{project_id}/graph", response_model=GraphOut)
def project_graph(project_id: uuid.UUID, db: Session = DB):
    raise not_implemented(OWNER)


@router.get("/projects/{project_id}/procedures", response_model=list[ProcedureOut])
def project_procedures(project_id: uuid.UUID, db: Session = DB):
    raise not_implemented(OWNER)


@router.get("/projects/{project_id}/contracts", response_model=list[ContractOut])
def project_contracts(project_id: uuid.UUID, db: Session = DB):
    raise not_implemented(OWNER)


@router.get("/projects/{project_id}/notices", response_model=list[NoticeOut])
def project_notices(project_id: uuid.UUID, db: Session = DB):
    raise not_implemented(OWNER)


@router.get("/procedures", response_model=Page[ProcedureOut])
def list_procedures(q: str | None = None, nip: str | None = None, tier: str | None = None,
                    offset: int = 0, limit: int = 50, db: Session = DB):
    raise not_implemented(OWNER)


@router.get("/procedures/{procedure_id}", response_model=ProcedureOut)
def get_procedure(procedure_id: uuid.UUID, db: Session = DB):
    raise not_implemented(OWNER)


@router.get("/notices/{notice_id}", response_model=NoticeDetail)
def get_notice(notice_id: uuid.UUID, db: Session = DB):
    raise not_implemented(OWNER)


@router.get("/entities/{entity_id}", response_model=EntityOut)
def get_entity(entity_id: uuid.UUID, db: Session = DB):
    raise not_implemented(OWNER)
