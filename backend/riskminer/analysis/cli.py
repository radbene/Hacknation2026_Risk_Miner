"""S3 CLI: `riskminer analyse <file>`, `riskminer classify`, `riskminer export`."""

from __future__ import annotations

from pathlib import Path

import typer


def register(app: typer.Typer) -> None:
    @app.command()
    def analyse(path: Path, title: str = typer.Option(None), llm: bool = typer.Option(False, help="LLM features + summary")):
        """Path B: analyse a new-investment description (.txt/.md/.pdf/.docx) → analysis record."""
        from riskminer.analysis.run import create
        from riskminer.core.db import session_scope

        with session_scope() as s:
            text, doc_ids = None, []
            if path.suffix.lower() in (".txt", ".md"):
                text = path.read_text(encoding="utf-8")
            else:
                from riskminer.extract.documents import ingest_bytes

                d = ingest_bytes(s, path.read_bytes(), path.name, uploaded_by="cli", fragments=False)
                doc_ids = [d.id]
            name = title or path.stem.replace("_", " ")
            from sqlalchemy import select

            from riskminer.analysis.run import compute
            from riskminer.models import Analysis

            a = s.execute(select(Analysis).where(Analysis.title == name, Analysis.input_text == text,
                                                 Analysis.created_by == "cli")).scalars().first() if text else None
            if a is not None:  # idempotent rerun (make demo): recompute, expert decisions on items survive
                a.params = {**(a.params or {}), "use_llm": llm}
                compute(s, a, "cli")
            else:
                a = create(s, title=name, text=text, features=None, document_ids=doc_ids, actor="cli", use_llm=llm)
            sm = a.summary
            typer.echo(f"{a.id}  {a.title}: cases {sm.get('n_cases')} {sm.get('cases_by_tier')}, neighbours "
                       f"{sm.get('n_neighbours')}, P(late) {(sm.get('p_late') or {}).get('estimate')}, flags {sm.get('n_flags')} "
                       f"{sm.get('risk_codes')}")

    @app.command()
    def classify(all: bool = typer.Option(False, "--all", help="reclassify every project (not only missing)"),
                 tier: str = typer.Option(None)):
        """Subsector / work type / scale features for case-base projects (rules)."""
        from riskminer.analysis.classify import classify as run
        from riskminer.core.db import session_scope

        with session_scope() as s:
            typer.echo(run(s, tier=tier, only_missing=not all, progress=lambda p, m: typer.echo(f"  {m}")))

    @app.command()
    def export(out: Path = Path("../exports/przyklad")):
        """Example export: deep-tier records, links.csv, every analysis (JSON/CSV/DOCX)."""
        from riskminer.core.db import session_scope
        from riskminer.export.records import bundle

        with session_scope() as s:
            data = bundle(s, out)
        typer.echo(f"{out} ({len(data) // 1024} KB zip)")
