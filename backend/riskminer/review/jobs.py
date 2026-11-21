"""S5 job handlers: knowledge load (all sectors or one)."""

from __future__ import annotations

from riskminer.core.jobs import JobContext, job_handler


@job_handler("knowledge_load")
def run_knowledge_load(ctx: JobContext) -> dict:
    from riskminer.knowledge import store

    sectors = [ctx.params["sector"]] if ctx.params.get("sector") else store.sectors_on_disk()
    out = {}
    for i, s in enumerate(sectors):
        out[s] = store.load_sector(ctx.session, s, actor=ctx.params.get("actor") or "import")
        ctx.session.commit()
        ctx.progress((i + 1) / len(sectors), f"wiedza: {s}")
    return {"sectors": {s: {"written": r["written"], "unchanged": r["unchanged"]} for s, r in out.items()}}


@job_handler("llm_test")
def run_llm_test(ctx: JobContext) -> dict:
    """'Testuj połączenie' from the LLM routing screen."""
    from riskminer.llm.routing import test_profile

    return test_profile(ctx.params["profile"], model=ctx.params.get("model"))
