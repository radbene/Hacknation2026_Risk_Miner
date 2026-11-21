"""`riskminer demo` – the whole pipeline from a (optionally fresh) DB to the example export and test report.

Steps call the other sessions' CLI commands **by name**; a missing command is skipped with a clear message
(so the demo works at every merge checkpoint). Every step is idempotent (uuid5 ids + upserts), so a
second run must not create duplicates – the demo checks this by comparing row counts with the last run.
"""

from __future__ import annotations

import datetime as dt
import json
import subprocess
import sys
import time
from dataclasses import dataclass, field
from pathlib import Path

import typer

from riskminer.core.config import REPO_ROOT, repo_path

BACKEND = REPO_ROOT / "backend"
FIX = BACKEND / "tests" / "fixtures"
ORGANIZER_XLSX = FIX / "organizer" / "Risk_Miner_dane_projekty.xlsx"
NEW_INVESTMENTS = FIX / "new_investments"
EXPORT_DIR = REPO_ROOT / "exports" / "przyklad"
COUNTS_FILE = REPO_ROOT / "data" / "demo_counts.json"
# Tables whose size must not change on a rerun (logs/audit/jobs legitimately grow).
STABLE_TABLES = ["project", "procedure", "project_procedure", "notice", "contract", "contract_change", "event",
                 "document", "evidence", "data_issue", "analysis", "analysis_item", "alert", "knowledge_table",
                 "entity", "fact"]


@dataclass
class Step:
    label: str
    owner: str
    argv: list[str]  # riskminer sub-command path + args
    optional: bool = False
    extra: list[list[str]] = field(default_factory=list)  # further invocations of the same command


def _click_group():
    from riskminer.cli import app

    return typer.main.get_command(app)


def command_exists(path: list[str]) -> bool:
    import click

    node = _click_group()
    for name in path:
        if not isinstance(node, click.Group) or name not in node.commands:
            return False
        node = node.commands[name]
    return True


def command_path(argv: list[str]) -> list[str]:
    """Leading tokens that name (sub-)commands – stop at the first option or path-like argument."""
    out = []
    for tok in argv:
        if tok.startswith("-") or "/" in tok or "." in tok:
            break
        out.append(tok)
    return out


def run_cli(argv: list[str], echo=typer.echo) -> tuple[int, float]:
    t0 = time.monotonic()
    proc = subprocess.run([sys.executable, "-m", "riskminer.cli", *argv], cwd=BACKEND, text=True,
                          capture_output=True)
    for line in (proc.stdout or "").splitlines()[-25:]:
        echo(f"    {line}")
    if proc.returncode:
        for line in (proc.stderr or "").splitlines()[-15:]:
            echo(f"    ! {line}")
    return proc.returncode, time.monotonic() - t0


def plan(sample: int) -> list[Step]:
    fixtures = sorted(str(p) for p in NEW_INVESTMENTS.glob("*") if p.suffix.lower() in (".txt", ".pdf", ".docx", ".md"))
    analyse = [["analyse", f] for f in fixtures]
    return [
        Step("Wczytanie wiedzy eksperckiej (R01–R15, podsektory, checklisty) do bazy", "S5", ["knowledge", "load"]),
        Step("Konta demonstracyjne", "S5", ["users", "seed"], optional=True),
        Step("Import listy projektów organizatora (xlsx)", "S1", ["import-xlsx", str(ORGANIZER_XLSX)]),
        Step("Wzbogacenie: BZP (lustro) + Biała lista VAT, powiązania", "S1", ["enrich"]),
        Step(f"Zbiór automatyczny z paczki BZP (próbka {sample})", "S1", ["harvest", "--sample", str(sample)],
             optional=True),
        Step("Zdarzenia, zmiany umów, przyczyny z cytatami", "S2", ["extract"]),
        Step("Analiza nowych inwestycji (fixtures)", "S3", analyse[0] if analyse else ["analyse"], extra=analyse[1:]),
        Step("Eksport przykładowy (JSON/CSV)", "S3", ["export", "--out", str(EXPORT_DIR)]),
    ]


def _counts() -> dict[str, int]:
    from riskminer.core.db import SessionLocal
    from riskminer.monitor.report import table_counts

    with SessionLocal() as s:
        return table_counts(s, sorted(set(STABLE_TABLES) | {"op_log", "llm_call", "review", "job"}))


def _fresh_db(echo) -> None:
    from sqlalchemy import text

    from riskminer.core.db import engine

    echo("  ⚠ --fresh: usuwam schemat public i tworzę go od nowa")
    with engine.begin() as c:
        c.execute(text("DROP SCHEMA public CASCADE"))
        c.execute(text("CREATE SCHEMA public"))


def _migrate(echo) -> int:
    proc = subprocess.run([sys.executable, "-m", "alembic", "upgrade", "head"], cwd=BACKEND, text=True,
                          capture_output=True)
    if proc.returncode:
        echo(proc.stderr[-2000:])
    return proc.returncode


def fallback_export(out: Path = EXPORT_DIR) -> list[str]:
    """Generic JSON/CSV dump of the case base (used only when S3's `export` command is missing)."""
    import csv

    from sqlalchemy import select

    from riskminer.core.db import SessionLocal
    from riskminer.core.upsert import row_dict
    from riskminer.models import (
        Analysis,
        AnalysisItem,
        Contract,
        ContractChange,
        Event,
        Evidence,
        Project,
        ProjectProcedure,
    )

    out.mkdir(parents=True, exist_ok=True)
    written = []
    with SessionLocal() as s:
        for name, model in [("projekty", Project), ("powiazania", ProjectProcedure), ("umowy", Contract),
                            ("zmiany_umow", ContractChange), ("zdarzenia", Event), ("analizy", Analysis),
                            ("pozycje_analiz", AnalysisItem), ("dowody", Evidence)]:
            rows = [row_dict(r) for r in s.execute(select(model)).scalars()]
            for r in rows:
                r.pop("embedding", None)
            (out / f"{name}.json").write_text(json.dumps(rows, ensure_ascii=False, indent=1, default=str), "utf-8")
            if rows:
                with (out / f"{name}.csv").open("w", newline="", encoding="utf-8") as f:
                    w = csv.DictWriter(f, fieldnames=list(rows[0]))
                    w.writeheader()
                    for r in rows:
                        w.writerow({k: json.dumps(v, ensure_ascii=False) if isinstance(v, dict | list) else v
                                    for k, v in r.items()})
            written.append(name)
    return written


def run_demo(*, fresh: bool = False, sample: int = 500, as_of: str | None = None, snapshot: bool = True,
             echo=typer.echo) -> dict:
    t_start = time.monotonic()
    report: dict = {"started_at": dt.datetime.now(dt.UTC).isoformat(), "steps": []}
    echo("RISK MINER – demo: pełny przebieg potoku\n")
    if fresh:
        _fresh_db(echo)
    echo("▶ Migracje bazy (alembic upgrade head)")
    if _migrate(echo):
        raise typer.Exit(1)
    before = _counts()

    for st in plan(sample):
        path = command_path(st.argv)
        if not path or not command_exists(path):
            msg = f"⏭  {st.label}: polecenie `riskminer {' '.join(path)}` ({st.owner}) jeszcze niedostępne – pomijam"
            echo(msg)
            report["steps"].append({"step": st.label, "owner": st.owner, "status": "skipped"})
            continue
        echo(f"▶ {st.label}  [riskminer {' '.join(st.argv)}]")
        rc, secs = run_cli(st.argv, echo)
        for more in st.extra:
            echo(f"  ▶ riskminer {' '.join(more)}")
            rc2, s2 = run_cli(more, echo)
            rc, secs = rc or rc2, secs + s2
        status = "ok" if rc == 0 else ("failed-optional" if st.optional else "failed")
        echo(f"  {'✓' if rc == 0 else '✗'} {status} ({secs:.1f} s)")
        report["steps"].append({"step": st.label, "owner": st.owner, "status": status, "seconds": round(secs, 1)})

    if not command_exists(["export"]):
        echo("▶ Eksport przykładowy (zapasowy eksport S6, bo brak `riskminer export`)")
        names = fallback_export()
        report["steps"].append({"step": "Eksport przykładowy (zapasowy)", "owner": "S6", "status": "ok",
                                "files": names})

    from riskminer.core.db import SessionLocal
    from riskminer.monitor.report import write_report
    from riskminer.monitor.watch import auto_watch_unfinished, run_monitor

    with SessionLocal() as s:
        echo("▶ Monitoring: obserwacja niezakończonych + odtworzenie as_of")
        n = auto_watch_unfinished(s)
        s.commit()
        mon = run_monitor(s, as_of=dt.date.fromisoformat(as_of) if as_of else dt.date.today(), reanalyse=False)
        echo(f"  ✓ obserwowane: {mon['watched']} (nowe: {n}), alerty utworzone: {mon['alerts_created']}")
        report["steps"].append({"step": "Monitoring", "owner": "S6", "status": "ok", "watched": mon["watched"],
                                "alerts_created": mon["alerts_created"]})
        echo("▶ Raport z testu → docs/raport_z_testu.md")
        path, summ = write_report(s)
        report["steps"].append({"step": "Raport z testu", "owner": "S6", "status": "ok", "path": str(path),
                                "linking": summ.get("linking")})

    after = _counts()
    prev = json.loads(COUNTS_FILE.read_text()) if COUNTS_FILE.exists() else None
    report["counts"] = after
    report["added_this_run"] = {k: after[k] - before.get(k, 0) for k in after if after[k] != before.get(k, 0)}
    dup = {k: after[k] - prev["counts"][k] for k in STABLE_TABLES
           if prev and k in prev.get("counts", {}) and after.get(k, 0) > prev["counts"][k]} if prev else {}
    if prev and not fresh:
        report["idempotent"] = not dup
        echo("✓ Powtórny przebieg nie utworzył duplikatów" if not dup
             else f"⚠ Przyrost rekordów względem poprzedniego przebiegu (sprawdź duplikaty): {dup}")
    COUNTS_FILE.parent.mkdir(parents=True, exist_ok=True)
    COUNTS_FILE.write_text(json.dumps({"at": report["started_at"], "counts": after}, indent=1))

    if snapshot:
        from riskminer.monitor import snapshot as snap

        m = snap.save()
        echo(f"▶ Złoty zrzut bazy → {snap.DEFAULT_DIR} ({sum(m['counts'].values())} wierszy)")
    EXPORT_DIR.mkdir(parents=True, exist_ok=True)
    report["seconds"] = round(time.monotonic() - t_start, 1)
    (EXPORT_DIR / "demo_run.json").write_text(json.dumps(report, ensure_ascii=False, indent=1), "utf-8")
    echo("\nLiczba rekordów: " + ", ".join(f"{k}={v}" for k, v in after.items() if v))
    skipped = [s["step"] for s in report["steps"] if s["status"] == "skipped"]
    failed = [s["step"] for s in report["steps"] if s["status"] == "failed"]
    if skipped:
        echo(f"Pominięte (brak poleceń): {len(skipped)}")
    if failed:
        echo(f"Nieudane kroki: {failed}")
    echo(f"Gotowe w {report['seconds']} s. Raport: docs/raport_z_testu.md · eksport: exports/przyklad/")
    report["failed"] = failed
    return report


__all__ = ["run_demo", "command_exists", "fallback_export", "repo_path"]
