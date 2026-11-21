"""S1 job handlers: enrich (BZP → procedures → links) and harvest (auto tier from the snapshot)."""

from __future__ import annotations

import datetime as dt
import uuid

from riskminer.core.jobs import JobContext, job_handler


def _date(v):
    return dt.date.fromisoformat(v) if v else None


@job_handler("enrich")
def run_enrich(ctx: JobContext) -> dict:
    from riskminer.connectors.pipeline import enrich

    ids = [uuid.UUID(str(x)) for x in ctx.params.get("project_ids") or []] or None
    sources = ctx.params.get("sources") or []
    source = ctx.params.get("source") or ("offline" if sources == ["bzp_zip"] else "auto")
    rep = enrich(ctx.session, project_ids=ids, source=source, date_to=_date(ctx.params.get("as_of")),
                 progress=ctx.progress, job_id=ctx.job_id, actor=ctx.params.get("actor") or "system")
    rep["per_nip"] = rep["per_nip"][:50]
    return rep


@job_handler("harvest")
def run_harvest(ctx: JobContext) -> dict:
    from riskminer.connectors.bzp_zip import harvest

    return harvest(limit=ctx.params.get("limit"), date_from=_date(ctx.params.get("date_from")),
                   date_to=_date(ctx.params.get("date_to")), progress=ctx.progress, job_id=ctx.job_id)
