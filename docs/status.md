# Status (działa / zaprojektowane / problemy)

Updated by each session; merged by the main session at checkpoints.

## Phase 0 – foundation (main session, 21.11 ~16:15)
**Działa**
- Repo scaffold, docker compose (db/api/worker/web/caddy), Makefile, CI, `.env.example`, `config/settings.example.yaml`.
- Full Postgres schema (30 tables) + migration 0001 (pgvector, pg_trgm, unaccent).
- API contract: 70 endpoints (Pydantic schemas + router stubs returning 501 until implemented); `/api/settings/llm`, `/api/evidence`, `/api/jobs` implemented.
- Shared infra: uuid5 ids, NIP/REGON/BZP/KPO validators, `upsert_reviewable` (expert data never overwritten), evidence helpers, op_log, DB job queue + worker.
- LLM layer: `complete(task, messages, schema)` with per-task fallback chain, cache (live/cache/replay), repair retry, llm_call log, `wrap_untrusted`, PII strip; provider `none`. Other providers: stubs (S5).
- Knowledge import: `riskminer knowledge import <docx>` → 11 YAML tables (R01–R15, 6 subsectors, 8 phases, 25 doc types, event→source, art. 455, porady, 9-point checklist …) + team drafts in `extra/`.
- Frontend scaffold: layout with 5 navigation areas (Polish), typed client from OpenAPI, 501→mock fallback, data-location banner.
- Fixtures: 988 real notices of the 20 beneficiaries (from the organizer zip); prep notices/gold/holdout reason sets.

**Open (user)**: HackTribe task selection (by 20:00) · mentor questions (`docs/pytania_do_mentorow.md`) · API keys in `.env` · host (Hetzner) · GitHub repo (no `gh` CLI on this machine).

## S1 Acquisition & linking
## S2 Extraction & documents
## S3 Analysis
## S4 Frontend
## S5 Expert, knowledge, LLM
## S6 Ops & deliverables
