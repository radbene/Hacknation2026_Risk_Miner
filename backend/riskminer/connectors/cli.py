"""S1 CLI: `riskminer import-xlsx`, `enrich`, `harvest`, `gold`, `links-csv`."""

from __future__ import annotations

import datetime as dt
import json
from pathlib import Path

import typer


def _dump(obj) -> None:
    typer.echo(json.dumps(obj, ensure_ascii=False, indent=1, default=str))


def register(app: typer.Typer) -> None:
    @app.command("import-xlsx")
    def import_xlsx(path: Path, profile: str = "organizer"):
        """Import the project list (organizer xlsx profile) with per-cell evidence and validation issues."""
        from riskminer.connectors.xlsx_import import import_path
        from riskminer.core.db import session_scope

        with session_scope() as s:
            rep = import_path(s, path, profile=profile, actor="cli")
        _dump({k: v for k, v in rep.items() if k != "issues"} | {"issues": len(rep.get("issues", []))})

    @app.command()
    def enrich(source: str = typer.Option("auto", help="live | offline | auto (live, snapshot fallback)"),
               project: list[str] = typer.Option(None, help="project code(s); default all deep-tier"),
               date_to: str = typer.Option(None, help="YYYY-MM-DD (as_of replay)")):
        """BZP notices of every beneficiary → procedures → links (idempotent)."""
        from sqlalchemy import select

        from riskminer.connectors.pipeline import enrich as run
        from riskminer.core.db import session_scope
        from riskminer.models import Project

        with session_scope() as s:
            ids = list(s.execute(select(Project.id).where(Project.code.in_(project))).scalars()) if project else None
            rep = run(s, project_ids=ids, source=source, date_to=dt.date.fromisoformat(date_to) if date_to else None,
                      progress=lambda p, m: typer.echo(f"  [{p:4.0%}] {m}"), actor="cli")
        typer.echo(f"notices {rep['notices']} (new {rep['inserted']}, updated {rep['updated']}, unchanged "
                   f"{rep['unchanged']}), procedures {rep['procedures']}, requests {rep['requests']}, "
                   f"offline NIPs {len(rep['offline_nips'])}, {rep['seconds']} s")
        typer.echo(f"links: {rep['link_summary']}")
        for x in rep["links"]:
            typer.echo(f"  {x['project']}: {x['status']:9} {x['method'] or '-':9} {x['confidence'] or '':<5} {x['procedure'] or ''}")

    @app.command()
    def harvest(sample: int = typer.Option(None, help="stop after N notices (dev/demo)"),
                date_from: str = typer.Option(None), date_to: str = typer.Option(None)):
        """Auto tier: wod-kan procedures from the organizer BZP snapshot (streamed, never unpacked)."""
        from riskminer.connectors.bzp_zip import harvest as run

        rep = run(limit=sample, date_from=dt.date.fromisoformat(date_from) if date_from else None,
                  date_to=dt.date.fromisoformat(date_to) if date_to else None,
                  progress=lambda p, m: typer.echo(f"  {m}"))
        _dump(rep)

    @app.command()
    def gold():
        """Link precision/recall vs the hand-verified gold set."""
        from riskminer.core.db import session_scope
        from riskminer.link.quality import evaluate

        with session_scope() as s:
            q = evaluate(s)
        _dump({k: v for k, v in q.items() if not isinstance(v, list) or len(v) < 30})

    @app.command("links-csv")
    def links_csv(out: Path = Path("../exports/links.csv")):
        """Write links.csv (method, confidence, components with evidence, status)."""
        from riskminer.connectors.pipeline import links_csv as build
        from riskminer.core.db import session_scope

        with session_scope() as s:
            text = build(s)
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(text, encoding="utf-8")
        typer.echo(f"{out} ({text.count(chr(10)) - 1} rows)")
