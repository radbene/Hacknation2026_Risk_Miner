"""Documents: upload / URL fetch, chunks, search, file (owner: S2)."""

from __future__ import annotations

import uuid

from fastapi import APIRouter, File, Form, UploadFile

from riskminer.api.deps import DB, USER, CurrentUser, Session, not_implemented
from riskminer.schemas.documents import ChunkOut, DocumentFromUrlIn, DocumentOut, SearchHit

router = APIRouter(tags=["documents"])
OWNER = "S2"


@router.post("/documents", response_model=DocumentOut)
async def upload_document(file: UploadFile = File(...), project_id: uuid.UUID | None = Form(None),
                          analysis_id: uuid.UUID | None = Form(None), doc_type: str | None = Form(None),
                          db: Session = DB, user: CurrentUser = USER):
    raise not_implemented(OWNER)


@router.post("/documents/from-url", response_model=DocumentOut)
def document_from_url(body: DocumentFromUrlIn, db: Session = DB, user: CurrentUser = USER):
    raise not_implemented(OWNER)


@router.get("/documents", response_model=list[DocumentOut])
def list_documents(project_id: uuid.UUID | None = None, analysis_id: uuid.UUID | None = None, db: Session = DB):
    raise not_implemented(OWNER)


@router.get("/documents/{document_id}", response_model=DocumentOut)
def get_document(document_id: uuid.UUID, db: Session = DB):
    raise not_implemented(OWNER)


@router.get("/documents/{document_id}/chunks", response_model=list[ChunkOut])
def document_chunks(document_id: uuid.UUID, db: Session = DB):
    raise not_implemented(OWNER)


@router.get("/documents/{document_id}/file")
def document_file(document_id: uuid.UUID, db: Session = DB):
    """Original file (PDF.js viewer loads this)."""
    raise not_implemented(OWNER)


@router.get("/search", response_model=list[SearchHit])
def search_chunks(q: str, project_id: uuid.UUID | None = None, limit: int = 20, db: Session = DB):
    raise not_implemented(OWNER)
