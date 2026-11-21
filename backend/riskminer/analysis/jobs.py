"""S3 job handlers: analyse a description (path B) and classify the case base."""

from __future__ import annotations

from riskminer.core.jobs import JobContext, job_handler


@job_handler("analyse")
def run_analyse(ctx: JobContext) -> dict:
    from riskminer.analysis.run import create

    a = create(ctx.session, title=ctx.params.get("title") or "Analiza", text=ctx.params.get("text"),
               features=ctx.params.get("features"), params=ctx.params.get("params"),
               actor=ctx.params.get("actor") or "system")
    ctx.session.commit()
    return {"analysis_id": str(a.id), **{k: a.summary.get(k) for k in ("n_neighbours", "n_flags", "risk_codes")}}


@job_handler("classify")
def run_classify(ctx: JobContext) -> dict:
    from riskminer.analysis.classify import classify

    return classify(ctx.session, tier=ctx.params.get("tier"), only_missing=not ctx.params.get("all"), progress=ctx.progress)
