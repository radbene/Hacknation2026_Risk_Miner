"""Golden DB snapshot (pure SQL COPY, no pg_dump needed) – used by S5's sandbox reset.

    save(dir)     – every table → <table>.csv + manifest.json (alembic revision, counts)
    restore(dir)  – TRUNCATE all tables, COPY back in FK order (same schema revision required)
"""

from __future__ import annotations

import datetime as dt
import gzip
import json
from pathlib import Path

from sqlalchemy import text

from riskminer.core.config import repo_path
from riskminer.core.db import engine
from riskminer.models import Base

DEFAULT_DIR = "data/snapshots/golden"


def _tables() -> list[str]:
    return [t.name for t in Base.metadata.sorted_tables]


def _revision(conn) -> str | None:
    try:
        return conn.execute(text("SELECT version_num FROM alembic_version")).scalar()
    except Exception:  # noqa: BLE001
        return None


def save(directory: str | Path = DEFAULT_DIR) -> dict:
    d = repo_path(str(directory))
    d.mkdir(parents=True, exist_ok=True)
    counts: dict[str, int] = {}
    raw = engine.raw_connection()
    try:
        cur = raw.cursor()
        for t in _tables():
            with gzip.open(d / f"{t}.csv.gz", "wb") as f, cur.copy(f'COPY "{t}" TO STDOUT WITH (FORMAT csv, HEADER true)') as cp:
                for chunk in cp:
                    f.write(bytes(chunk))
            cur.execute(f'SELECT count(*) FROM "{t}"')
            counts[t] = cur.fetchone()[0]
        with engine.connect() as c:
            rev = _revision(c)
    finally:
        raw.close()
    manifest = {"created_at": dt.datetime.now(dt.UTC).isoformat(), "alembic_revision": rev, "counts": counts}
    (d / "manifest.json").write_text(json.dumps(manifest, indent=1), encoding="utf-8")
    return manifest


def restore(directory: str | Path = DEFAULT_DIR) -> dict:
    d = repo_path(str(directory))
    manifest = json.loads((d / "manifest.json").read_text(encoding="utf-8"))
    tables = _tables()
    raw = engine.raw_connection()
    try:
        cur = raw.cursor()
        rev = cur.execute("SELECT version_num FROM alembic_version").fetchone()
        if manifest.get("alembic_revision") and rev and rev[0] != manifest["alembic_revision"]:
            raise RuntimeError(f"snapshot revision {manifest['alembic_revision']} != DB revision {rev[0]}")
        cur.execute("TRUNCATE " + ", ".join(f'"{t}"' for t in tables) + " CASCADE")
        for t in tables:
            p = d / f"{t}.csv.gz"
            if not p.exists():
                continue
            with gzip.open(p, "rb") as f:
                header = f.readline().decode("utf-8").strip()
                cols = ",".join(f'"{c}"' for c in header.split(","))
                with cur.copy(f'COPY "{t}" ({cols}) FROM STDIN WITH (FORMAT csv)') as cp:
                    while chunk := f.read(1 << 20):
                        cp.write(chunk)
        raw.commit()
    except Exception:
        raw.rollback()
        raise
    finally:
        raw.close()
    return manifest
