"""S2 job handlers: extract (events, causes, completeness) and NIK lessons."""

from __future__ import annotations

import uuid

from riskminer.core.jobs import JobContext, job_handler


@job_handler("extract")
def run_extract(ctx: JobContext) -> dict:
    from riskminer.extract.pipeline import extract

    ids = [uuid.UUID(str(x)) for x in ctx.params.get("project_ids") or []] or None
    return extract(ctx.session, ids, use_llm=bool(ctx.params.get("use_llm")), progress=ctx.progress)


@job_handler("nik_lessons")
def run_nik(ctx: JobContext) -> dict:
    from riskminer.extract.lessons import import_reports

    return import_reports(ctx.session, ctx.params.get("urls"), use_llm=bool(ctx.params.get("use_llm")))
