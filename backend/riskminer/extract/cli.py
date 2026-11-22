"""S2 CLI: `riskminer extract`, `riskminer docs`, `riskminer nik`."""

from __future__ import annotations

import json
from pathlib import Path

import typer


def register(app: typer.Typer) -> None:
    @app.command()
    def extract(project: list[str] = typer.Option(None, help="project code(s); default every deep-tier project"),
                llm: bool = typer.Option(False, help="refine causes with the LLM (quote-gated)")):
        """Rule events from BZP data, causes with quotes, completeness (4 states) + contradictions."""
        from sqlalchemy import select

        from riskminer.core.db import session_scope
        from riskminer.extract.pipeline import extract as run
        from riskminer.models import Project

        with session_scope() as s:
            ids = list(s.execute(select(Project.id).where(Project.code.in_(project))).scalars()) if project else None
            rep = run(s, ids, use_llm=llm)
        typer.echo(f"events {rep['events']} {rep['results']} by type {rep['by_type']}")
        for p in rep["projects"]:
            typer.echo(f"  {p['project']}: {p['events']} events, completeness {p['completeness']:.0%}, issues {p['issues']}")
        if rep["errors"]:
            typer.echo(f"errors: {rep['errors'][:5]}")

    @app.command()
    def docs(path: Path, project: str = typer.Option(None, help="project code"), doc_type: str = typer.Option(None)):
        """Ingest a PDF/DOCX/XLSX/CSV/HTML document (page/paragraph locators, fragments)."""
        from sqlalchemy import select

        from riskminer.core.db import session_scope
        from riskminer.extract.documents import ingest_bytes
        from riskminer.models import Project

        with session_scope() as s:
            pid = s.scalar(select(Project.id).where(Project.code == project)) if project else None
            d = ingest_bytes(s, path.read_bytes(), path.name, project_id=pid, doc_type=doc_type, uploaded_by="cli")
            typer.echo(json.dumps({"id": str(d.id), "doc_type": d.doc_type, "phase": d.phase, "pages": d.pages,
                                   "text_status": d.text_status}, ensure_ascii=False))

    @app.command()
    def ocr(llm: bool = typer.Option(False, help="LLM fragments on the OCR text (quote-gated)")):
        """OCR every stored scan without a text layer (Tesseract), then chunks, fragments and effects."""
        from riskminer.core.db import session_scope
        from riskminer.extract import ocr as engine
        from riskminer.extract.documents import ocr_pending

        if not engine.available():
            typer.echo("OCR unavailable: set `ocr.command` in config/settings.yaml (tesseract or docker image)")
            raise typer.Exit(1)
        with session_scope() as s:
            for row in ocr_pending(s, use_llm=llm):
                typer.echo(json.dumps(row, ensure_ascii=False))

    @app.command()
    def nik(llm: bool = False):
        """Import NIK audit reports (configured URLs) → lessons."""
        from riskminer.core.db import session_scope
        from riskminer.extract.lessons import import_reports

        with session_scope() as s:
            typer.echo(json.dumps(import_reports(s, use_llm=llm), ensure_ascii=False, default=str))
