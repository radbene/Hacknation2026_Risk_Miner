"""Juror sandbox: "Przywróć stan demo" restores the app DB from a golden copy (Postgres `CREATE DATABASE … TEMPLATE`).

How S6 produces the golden snapshot (once the demo data is final):

    make demo                                   # fills the app DB (import → enrich → extract → analyse …)
    docker compose stop api worker              # TEMPLATE needs no other connections to the source DB
    cd backend && uv run riskminer reset-demo --snapshot          # (--force terminates leftover connections)
    docker compose start api worker

This creates `<db>_golden` (override with env GOLDEN_DB) inside the same Postgres – no files, no /tmp; the copy
costs about the size of the app DB on the Postgres volume. A portable backup for the server is a compressed
dump kept under /home (never /tmp):  pg_dump -Fc -d <db>_golden -f /home/<user>/riskminer_golden.dump

Restore (POST /api/admin/reset-demo, admin; or `riskminer reset-demo`):
    CREATE DATABASE <db>_restore TEMPLATE <db>_golden      # copy while the app keeps running
    terminate connections to <db>; ALTER DATABASE <db> RENAME TO <db>_old; ALTER … <db>_restore RENAME TO <db>
    DROP DATABASE <db>_old
The app's connection pool reconnects on the next request (pool_pre_ping). The DB role needs CREATEDB.
"""

from __future__ import annotations

import datetime as dt
import os
import re

from sqlalchemy import create_engine, text
from sqlalchemy.engine import URL, make_url

_NAME = re.compile(r"^[a-z_][a-z0-9_]{0,62}$")


class SandboxError(RuntimeError):
    pass


def _url() -> URL:
    from riskminer.core.config import get_env

    return make_url(get_env().database_url)


def names(url: URL | None = None) -> tuple[str, str]:
    url = url or _url()
    db = url.database
    golden = os.environ.get("GOLDEN_DB") or f"{db}_golden"
    for n in (db, golden):
        if not _NAME.match(n or ""):
            raise SandboxError(f"niedozwolona nazwa bazy: {n!r}")
    return db, golden


def _admin_engine(url: URL):
    return create_engine(url.set(database="postgres"), isolation_level="AUTOCOMMIT", pool_pre_ping=True)


def _exists(c, name: str) -> bool:
    return c.execute(text("SELECT 1 FROM pg_database WHERE datname=:n"), {"n": name}).first() is not None


def _connections(c, name: str) -> int:
    return c.execute(text("SELECT count(*) FROM pg_stat_activity WHERE datname=:n AND pid<>pg_backend_pid()"),
                     {"n": name}).scalar_one()


def _terminate(c, name: str) -> None:
    c.execute(text("SELECT pg_terminate_backend(pid) FROM pg_stat_activity WHERE datname=:n "
                   "AND pid<>pg_backend_pid()"), {"n": name})


def _dispose_app_pool() -> None:
    try:
        from riskminer.core.db import engine

        engine.dispose()
    except Exception:  # noqa: BLE001
        pass


def status(url: URL | None = None) -> dict:
    url = url or _url()
    db, golden = names(url)
    eng = _admin_engine(url)
    try:
        with eng.connect() as c:
            ok = _exists(c, golden)
            size = c.execute(text("SELECT pg_database_size(:n)"), {"n": golden}).scalar_one() if ok else None
            created = None
            if ok:
                created = c.execute(text("SELECT shobj_description(oid, 'pg_database') FROM pg_database "
                                         "WHERE datname=:n"), {"n": golden}).scalar_one()
    finally:
        eng.dispose()
    return {"database": db, "golden": golden, "golden_exists": ok,
            "golden_size_mb": round(size / 1e6, 1) if size else None, "golden_created_at": created}


def snapshot(force: bool = False, url: URL | None = None) -> str:
    """Copy the current DB to the golden DB (replacing an older golden copy)."""
    url = url or _url()
    db, golden = names(url)
    _dispose_app_pool()
    eng = _admin_engine(url)
    try:
        with eng.connect() as c:
            n = _connections(c, db)
            if n and not force:
                raise SandboxError(f"{n} innych połączeń z bazą {db} – zatrzymaj api/worker albo użyj --force")
            if force:
                _terminate(c, db)
            if _exists(c, golden):
                _terminate(c, golden)
                c.execute(text(f'DROP DATABASE "{golden}"'))
            c.execute(text(f'CREATE DATABASE "{golden}" TEMPLATE "{db}"'))
            stamp = dt.datetime.now(dt.UTC).isoformat(timespec="seconds")
            c.execute(text(f"COMMENT ON DATABASE \"{golden}\" IS '{stamp}'"))
    finally:
        eng.dispose()
    return f"Zapisano stan wzorcowy: {db} → {golden} ({stamp})"


def restore(url: URL | None = None) -> str:
    """Replace the app DB with a fresh copy of the golden DB."""
    url = url or _url()
    db, golden = names(url)
    tmp, old = f"{db}_restore", f"{db}_old"
    eng = _admin_engine(url)
    try:
        with eng.connect() as c:
            if not _exists(c, golden):
                raise SandboxError(f"brak bazy wzorcowej {golden} – najpierw `riskminer reset-demo --snapshot`")
            for leftover in (tmp, old):
                if _exists(c, leftover):
                    _terminate(c, leftover)
                    c.execute(text(f'DROP DATABASE "{leftover}"'))
            _terminate(c, golden)
            c.execute(text(f'CREATE DATABASE "{tmp}" TEMPLATE "{golden}"'))
            _dispose_app_pool()
            _terminate(c, db)
            c.execute(text(f'ALTER DATABASE "{db}" RENAME TO "{old}"'))
            c.execute(text(f'ALTER DATABASE "{tmp}" RENAME TO "{db}"'))
            _terminate(c, old)
            c.execute(text(f'DROP DATABASE "{old}"'))
    finally:
        eng.dispose()
    return f"Przywrócono stan demo z {golden}"
