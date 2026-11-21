"""S6 CLI: `monitor …`, `demo`, `report`, `snapshot …`, `licences`, `docs-gen`."""

from __future__ import annotations

import datetime as dt
import json
import sys
from pathlib import Path

import typer

from riskminer.core.config import REPO_ROOT

monitor_app = typer.Typer(help="Monitorowanie niezakończonych inwestycji (obserwowane postępowania, as_of)")
snapshot_app = typer.Typer(help="Złoty zrzut bazy (reset piaskownicy)")


@monitor_app.command("run")
def monitor_run(as_of: str = typer.Option(None, help="RRRR-MM-DD: odtworzenie – udawaj, że dziś jest ta data"),
                no_reanalyse: bool = typer.Option(False, help="nie zlecaj ponownej analizy"),
                offline: bool = typer.Option(False, help="tryb live bez zapytań do BZP (tylko kontrole)")):
    """One monitoring pass (live, or replay with --as-of)."""
    from riskminer.core.db import SessionLocal
    from riskminer.monitor.watch import run_monitor

    with SessionLocal() as s:
        rep = run_monitor(s, as_of=dt.date.fromisoformat(as_of) if as_of else None, reanalyse=not no_reanalyse,
                          live=False if offline else None, user="cli")
    typer.echo(json.dumps(rep, ensure_ascii=False, indent=1, default=str))


@monitor_app.command("watch")
def monitor_watch(project: list[str] = typer.Option(None, help="kod projektu, np. RM-2026-020"),
                  ocid: list[str] = typer.Option(None), auto: bool = typer.Option(False, help="wszystkie niezakończone"),
                  off: bool = typer.Option(False, help="przestań obserwować")):
    """Mark procedures as watched (by project code, OCID, or --auto)."""
    from sqlalchemy import select

    from riskminer.core.db import SessionLocal
    from riskminer.models import Procedure, Project
    from riskminer.monitor.watch import auto_watch_unfinished, set_watch

    with SessionLocal() as s:
        n = 0
        if auto:
            n += auto_watch_unfinished(s)
        pids = list(s.execute(select(Project.id).where(Project.code.in_(project or []))).scalars()) if project else []
        prids = list(s.execute(select(Procedure.id).where(Procedure.ocid.in_(ocid or []))).scalars()) if ocid else []
        if pids or prids:
            n += set_watch(s, procedure_ids=prids, project_ids=pids, watched=not off)
        s.commit()
        total = s.execute(select(Procedure.id).where(Procedure.watched.is_(True))).all()
    typer.echo(f"zmieniono: {n}, obserwowane razem: {len(total)}")


@monitor_app.command("worker")
def monitor_worker(poll: float = 1.0, interval_min: int = typer.Option(None, help="co ile minut (domyślnie env MONITOR_INTERVAL_MIN=360)")):
    """Job worker + APScheduler monitoring tick (used by the docker `worker` service)."""
    from riskminer.core.jobs import worker_loop
    from riskminer.monitor.scheduler import start_scheduler

    start_scheduler(interval_min)
    worker_loop(poll_s=poll)


@monitor_app.command("probe")
def monitor_probe():
    """Check outbound access to the BZP mirror and the official API (custom User-Agent)."""
    from riskminer.monitor.feed import probe

    ok = True
    for url in ("https://bzp.cytr.us/mo-board/api/v1/notice", "https://ezamowienia.gov.pl/mo-board/api/v1/notice"):
        r = probe(url)
        ok &= r.get("status") == 200
        typer.echo(json.dumps(r, ensure_ascii=False))
    raise typer.Exit(0 if ok else 1)


@snapshot_app.command("save")
def snapshot_save(directory: str = "data/snapshots/golden"):
    from riskminer.monitor import snapshot

    m = snapshot.save(directory)
    typer.echo(f"zapisano {sum(m['counts'].values())} wierszy → {directory}")


@snapshot_app.command("restore")
def snapshot_restore(directory: str = "data/snapshots/golden", yes: bool = typer.Option(False, "--yes")):
    from riskminer.monitor import snapshot

    if not yes:
        typer.confirm("To nadpisze całą bazę zrzutem. Kontynuować?", abort=True)
    m = snapshot.restore(directory)
    typer.echo(f"odtworzono zrzut z {m['created_at']}")


def demo(fresh: bool = typer.Option(False, help="usuń schemat i zacznij od pustej bazy"),
         sample: int = typer.Option(500, help="liczba postępowań z paczki BZP (poziom auto)"),
         as_of: str = typer.Option(None, help="data dla monitoringu (domyślnie dziś)"),
         no_snapshot: bool = typer.Option(False, help="nie zapisuj złotego zrzutu")):
    """Full pipeline: migrate → knowledge → import → enrich → harvest → extract → analyse → export → report."""
    from riskminer.monitor.demo import run_demo

    rep = run_demo(fresh=fresh, sample=sample, as_of=as_of, snapshot=not no_snapshot)
    raise typer.Exit(1 if rep.get("failed") else 0)


def report(out: str = "docs/raport_z_testu.md"):
    """Generate the test report (links vs gold, organizer data errors, analyses, op_log, LLM)."""
    from riskminer.core.db import SessionLocal
    from riskminer.monitor.report import write_report

    with SessionLocal() as s:
        path, summary = write_report(s, out)
    typer.echo(f"wrote {path}: {json.dumps(summary.get('linking'), default=str)}")


def licences(out: Path = typer.Option(REPO_ROOT / "LICENSES-THIRD-PARTY.md"),
             check: bool = typer.Option(False, help="błąd, gdy jest zależność GPL/AGPL"),
             json_out: Path = typer.Option(None, help="także SBOM w JSON")):
    """Write LICENSES-THIRD-PARTY.md (data sources, Python + npm deps, models)."""
    from riskminer.monitor.licences import as_dicts, inventory, render_markdown

    items = inventory()
    out.write_text(render_markdown(items), encoding="utf-8")
    if json_out:
        json_out.write_text(json.dumps(as_dicts(items), ensure_ascii=False, indent=1), encoding="utf-8")
    bad = [i for i in items if i.verdict == "forbidden"]
    typer.echo(f"wrote {out}: {len(items)} pozycji, GPL/AGPL: {len(bad)}")
    for i in bad:
        typer.echo(f"  ✗ {i.ecosystem} {i.name} {i.version}: {i.licence}", err=True)
    if check and bad:
        raise typer.Exit(1)


def docs_gen():
    """Regenerate docs/erd.md (mermaid ERD from models/tables.py)."""
    from riskminer.monitor.docs_gen import erd_mermaid

    p = REPO_ROOT / "docs" / "erd.md"
    p.write_text("# ERD – schemat bazy (wygenerowany)\n\n"
                 "Generowany z `backend/riskminer/models/tables.py`: `uv run riskminer docs-gen`.\n\n"
                 "## Widok skrócony (klucze i relacje)\n\n```mermaid\n" + erd_mermaid(compact=True) + "\n```\n\n"
                 "## Pełny schemat\n\n```mermaid\n" + erd_mermaid() + "\n```\n", encoding="utf-8")
    typer.echo(f"wrote {p}")


def register(app: typer.Typer) -> None:
    app.add_typer(monitor_app, name="monitor")
    app.add_typer(snapshot_app, name="snapshot")
    app.command("demo")(demo)
    app.command("report")(report)
    app.command("licences")(licences)
    app.command("docs-gen")(docs_gen)


if __name__ == "__main__":  # pragma: no cover
    sys.exit(0)
