from __future__ import annotations

import logging

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from riskminer.api.routers import (
    analyses,
    cases,
    common,
    documents,
    events,
    exports,
    imports,
    knowledge,
    links,
    ops,
    review,
    settings,
)
from riskminer.core.config import get_env

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s")

app = FastAPI(
    title="RISK MINER API",
    version="0.1.0",
    description="Inteligentna baza doświadczeń inwestycji publicznych (wodociągi i kanalizacja). HackNation 2026 / MFiPR.",
    openapi_url="/api/openapi.json",
    docs_url="/api/docs",
)
app.add_middleware(
    CORSMiddleware,
    allow_origins=[o.strip() for o in get_env().cors_origins.split(",") if o.strip()],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

for r in (common, cases, imports, links, events, documents, analyses, exports, review, knowledge, settings, ops):
    app.include_router(r.router, prefix="/api")
