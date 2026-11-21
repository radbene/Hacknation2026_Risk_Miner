"""S5 CLI: `riskminer knowledge load`, `riskminer users …`, `riskminer reset-demo`, `riskminer llm …`."""

from __future__ import annotations

import typer


def _knowledge_group(app: typer.Typer) -> typer.Typer:
    for g in app.registered_groups:
        if g.name == "knowledge" and g.typer_instance is not None:
            return g.typer_instance
    k = typer.Typer(help="Wiedza ekspercka")
    app.add_typer(k, name="knowledge")
    return k


def register(app: typer.Typer) -> None:
    knowledge = _knowledge_group(app)

    @knowledge.command("load")
    def knowledge_load(sector: str = typer.Option(None, help="sector code (default: every folder in knowledge/)"),
                       actor: str = "import"):
        """Load knowledge/<sector>/*.yaml (+ extra/) into versioned DB tables; seeds risk_category, clause."""
        from riskminer.core.db import session_scope
        from riskminer.knowledge import store

        sectors = [sector] if sector else store.sectors_on_disk()
        with session_scope() as s:
            for sec in sectors:
                rep = store.load_sector(s, sec, actor=actor)
                typer.echo(f"[{sec}] new versions: {', '.join(rep['written']) or '—'}; "
                           f"unchanged: {len(rep['unchanged'])}")

    users = typer.Typer(help="Użytkownicy demonstracyjni i role")
    app.add_typer(users, name="users")

    @users.command("seed")
    def users_seed():
        """Create/refresh demo users admin / ekspert / analityk / gosc (password: env DEMO_PASSWORD)."""
        from riskminer.core.db import session_scope
        from riskminer.review import auth

        with session_scope() as s:
            for u in auth.seed_users(s):
                typer.echo(f"{u.username:10s} {u.role}")

    @users.command("list")
    def users_list():
        from sqlalchemy import select

        from riskminer.core.db import session_scope
        from riskminer.models import User

        with session_scope() as s:
            for u in s.execute(select(User).order_by(User.username)).scalars():
                typer.echo(f"{u.username:10s} {u.role:8s} {'aktywny' if u.active else 'nieaktywny'}")

    @app.command("reset-demo")
    def reset_demo(snapshot: bool = typer.Option(False, help="save the CURRENT DB as the golden snapshot instead"),
                   force: bool = typer.Option(False, help="terminate other connections to the source DB")):
        """Restore the juror sandbox from the golden DB (or, with --snapshot, create the golden DB)."""
        from riskminer.review import sandbox

        msg = sandbox.snapshot(force=force) if snapshot else sandbox.restore()
        typer.echo(msg)

    llm = typer.Typer(help="Modele językowe: test połączenia, zużycie")
    app.add_typer(llm, name="llm")

    @llm.command("test")
    def llm_test(profile: str, model: str = typer.Option(None, help="override the profile's model id")):
        """One tiny structured call through the given profile (live, bypasses the cache)."""
        from riskminer.llm.routing import test_profile

        typer.echo(test_profile(profile, model=model))

    @llm.command("usage")
    def llm_usage():
        from riskminer.core.db import session_scope
        from riskminer.llm.usage import usage_summary

        with session_scope() as s:
            for r in usage_summary(s):
                typer.echo(f"{r['task']:18s} {r['provider']:9s} {r['model'] or '':28s} calls={r['calls']} "
                           f"cached={r['cached']} err={r['errors']} ${r['cost_usd']:.4f}")
