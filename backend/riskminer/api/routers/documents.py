"""Documents: upload / URL fetch, chunks, search, file (owner: S2)."""

from __future__ import annotations

import uuid
from pathlib import Path

from fastapi import APIRouter, File, Form, HTTPException, UploadFile
from fastapi.responses import FileResponse, RedirectResponse
from sqlalchemy import select

from riskminer.api.deps import DB, USER, CurrentUser, Session
from riskminer.models import Chunk, Document
from riskminer.schemas.documents import ChunkOut, DocumentFromUrlIn, DocumentOut, SearchHit

router = APIRouter(tags=["documents"])
OWNER = "S2"
MAX_UPLOAD = 60 * 1024 * 1024


def _doc_or_404(db: Session, document_id: uuid.UUID) -> Document:
    d = db.get(Document, document_id)
    if not d:
        raise HTTPException(404, "Nie znaleziono dokumentu")
    return d


@router.post("/documents", response_model=DocumentOut)
async def upload_document(file: UploadFile = File(...), project_id: uuid.UUID | None = Form(None),
                          analysis_id: uuid.UUID | None = Form(None), doc_type: str | None = Form(None),
                          db: Session = DB, user: CurrentUser = USER):
    from riskminer.extract.documents import ingest_bytes

    data = await file.read()
    if not data:
        raise HTTPException(400, "Pusty plik")
    if len(data) > MAX_UPLOAD:
        raise HTTPException(413, "Plik za duży (limit 60 MB)")
    try:
        doc = ingest_bytes(db, data, file.filename or "dokument", mime=file.content_type, project_id=project_id,
                           analysis_id=analysis_id, doc_type=doc_type, uploaded_by=user.username)
    except ValueError as e:
        db.rollback()
        raise HTTPException(400, f"Nie udało się odczytać dokumentu: {e}") from e
    db.commit()
    return doc


@router.post("/documents/from-url", response_model=DocumentOut)
def document_from_url(body: DocumentFromUrlIn, db: Session = DB, user: CurrentUser = USER):
    from riskminer.extract.documents import fetch_url

    if not body.url.lower().startswith(("http://", "https://")):
        raise HTTPException(400, "Adres musi zaczynać się od http(s)://")
    try:
        doc = fetch_url(db, body.url, project_id=body.project_id, analysis_id=body.analysis_id, doc_type=body.doc_type,
                        uploaded_by=user.username)
    except Exception as e:  # noqa: BLE001 – network / parse error → 502 with the reason
        db.rollback()
        raise HTTPException(502, f"Nie udało się pobrać dokumentu: {type(e).__name__}: {e}"[:300]) from e
    db.commit()
    return doc


@router.get("/documents", response_model=list[DocumentOut])
def list_documents(project_id: uuid.UUID | None = None, analysis_id: uuid.UUID | None = None, db: Session = DB):
    q = select(Document)
    if project_id:
        q = q.where(Document.project_id == project_id)
    if analysis_id:
        q = q.where(Document.analysis_id == analysis_id)
    return db.execute(q.order_by(Document.created_at.desc()).limit(500)).scalars().all()


@router.get("/documents/{document_id}", response_model=DocumentOut)
def get_document(document_id: uuid.UUID, db: Session = DB):
    return _doc_or_404(db, document_id)


@router.get("/documents/{document_id}/chunks", response_model=list[ChunkOut])
def document_chunks(document_id: uuid.UUID, db: Session = DB):
    _doc_or_404(db, document_id)
    return db.execute(select(Chunk).where(Chunk.document_id == document_id).order_by(Chunk.ord)).scalars().all()


@router.get("/documents/{document_id}/file")
def document_file(document_id: uuid.UUID, db: Session = DB):
    """Original file (PDF.js viewer loads this)."""
    d = _doc_or_404(db, document_id)
    if d.file_path and Path(d.file_path).exists():
        return FileResponse(d.file_path, media_type=d.mime or "application/octet-stream",
                            filename=d.file_name or Path(d.file_path).name, content_disposition_type="inline")
    if d.url:
        return RedirectResponse(d.url)
    raise HTTPException(404, "Plik nie jest dostępny")


@router.get("/search", response_model=list[SearchHit])
def search_chunks(q: str, project_id: uuid.UUID | None = None, limit: int = 20, db: Session = DB):
    from riskminer.extract.documents import search

    if not q.strip():
        return []
    return [SearchHit(chunk=ChunkOut.model_validate(c), score=s, highlight=h) for c, s, h in search(db, q, project_id, limit)
            if c is not None]
