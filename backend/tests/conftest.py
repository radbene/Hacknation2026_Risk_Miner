from __future__ import annotations

import json
import lzma
from pathlib import Path

import pytest

FIX = Path(__file__).parent / "fixtures"


@pytest.fixture(scope="session")
def fixtures_dir() -> Path:
    return FIX


@pytest.fixture(scope="session")
def notices22() -> list[dict]:
    """All BZP notices (4 types) of the 20 beneficiaries of the 22 organizer projects, from the organizer zip."""
    with lzma.open(FIX / "projects22" / "notices_by_nip.jsonl.xz", "rt", encoding="utf-8") as f:
        return [json.loads(line) for line in f]


@pytest.fixture(scope="session")
def db_available() -> bool:
    try:
        from sqlalchemy import text

        from riskminer.core.db import engine

        with engine.connect() as c:
            c.execute(text("SELECT 1"))
        return True
    except Exception:
        return False


@pytest.fixture
def db(db_available):
    if not db_available:
        pytest.skip("no database")
    from riskminer.core.db import SessionLocal

    s = SessionLocal()
    try:
        yield s
    finally:
        s.rollback()
        s.close()


import sys as _sys  # noqa: E402

_sys.path.insert(0, str(Path(__file__).parent))  # test helpers (bzp_rows)
