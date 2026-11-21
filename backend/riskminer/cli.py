"""riskminer CLI. Each Phase 1 session adds its own sub-commands in its own module (see `_register`)."""

from __future__ import annotations

import contextlib
from pathlib import Path

import typer

from riskminer.core.config import get_config, repo_path

app = typer.Typer(no_args_is_help=True, help="RISK MINER – baza doświadczeń inwestycji publicznych")
knowledge_app = typer.Typer(help="Wiedza ekspercka (katalog R01–R15, podsektory, checklisty …)")
app.add_typer(knowledge_app, name="knowledge")


@knowledge_app.command("import")
def knowledge_import(files: list[Path], sector: str = typer.Option(None, help="sector code (default from config)")):
    """Generate knowledge/<sector>/*.yaml from expert docx files."""
    from riskminer.knowledge.docx_import import import_docx

    sector = sector or get_config().sector
    out = repo_path(get_config().knowledge_dir) / sector
    counts = import_docx(files, out, sector)
    for k, v in counts.items():
        typer.echo(f"{k:20s} {v:4d}  → {out / (k + '.yaml')}")


@app.command()
def worker(once: bool = False, poll: float = 1.0):
    """Run the background job worker (DB queue)."""
    from riskminer.core.jobs import worker_loop

    worker_loop(poll_s=poll, once=once)


@app.command()
def openapi(out: Path = Path("../frontend/openapi.json")):
    """Dump the OpenAPI contract (frontend client is generated from it)."""
    import json

    from riskminer.api.main import app as api

    out.write_text(json.dumps(api.openapi(), ensure_ascii=False, indent=1), encoding="utf-8")
    typer.echo(f"wrote {out}")


def _register() -> None:
    """Sub-command modules owned by Phase 1 sessions (one line each)."""
    for mod in (
        "riskminer.connectors.cli",   # S1: import-xlsx, enrich, harvest, gold
        "riskminer.extract.cli",      # S2: extract, docs
        "riskminer.analysis.cli",     # S3: analyse, export
        "riskminer.review.cli",       # S5: users, knowledge load, reset-demo
        "riskminer.monitor.cli",      # S6: monitor, demo, report
    ):
        with contextlib.suppress(ModuleNotFoundError):
            m = __import__(mod, fromlist=["register"])
            m.register(app)


_register()

if __name__ == "__main__":
    app()
