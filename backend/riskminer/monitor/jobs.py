"""Job handlers owned by S6: `monitor` (one monitoring pass), `report` (test report generation)."""

from __future__ import annotations

import datetime as dt

from riskminer.core.jobs import JobContext, job_handler


@job_handler("monitor")
def run_monitor_job(ctx: JobContext) -> dict:
    from riskminer.monitor.watch import run_monitor

    p = ctx.params or {}
    as_of = dt.date.fromisoformat(p["as_of"]) if p.get("as_of") else None
    ctx.progress(0.1, "monitorowanie: sprawdzam obserwowane postępowania")
    return run_monitor(ctx.session, as_of=as_of, reanalyse=p.get("reanalyse", True), live=p.get("live"),
                       user=p.get("user"), job_id=ctx.job_id)


@job_handler("report")
def run_report_job(ctx: JobContext) -> dict:
    from riskminer.monitor.report import write_report

    path, summary = write_report(ctx.session)
    return {"path": str(path), **summary}
