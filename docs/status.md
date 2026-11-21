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
**Działa**
- Stos produkcyjny docker compose (db, api z `alembic upgrade head`, worker z APScheduler, web, Caddy z auto-HTTPS); healthchecki; porty konfigurowalne (test lokalny `deploy/local-prod-test.sh`, projekt `rmtest`, :8088); dane trwałe w `pgdata`, `data/`, `exports/`.
- Skrypty wdrożenia na Hetzner: `deploy/deploy.sh user@host [--bootstrap --with-data --demo]` (docker, ufw, `.env` z losowymi sekretami, `<ip>.sslip.io`, test dymny), `make deploy`.
- Router `ops`: dashboard (liczby wg tabel i poziomów, ostatnie zadania, alerty, miejsca przetwarzania), dziennik zapytań z filtrami, stan konektorów (działa/zaprojektowane), zużycie LLM, licencje, alerty (+ oznacz jako przeczytany), obserwacja i uruchomienie monitoringu; `/quality` wywołuje `riskminer.link.quality` (S1), bez niego 501.
- Monitoring: obserwowane postępowania, przebieg live (okno dni z lustra BZP, filtr OCID po stronie klienta) i odtworzenie `as_of` z bazy; alerty nowe ogłoszenie / przekroczony termin / jakość danych („Zakończone” bez ogłoszenia o wykonaniu); zlecenie `reanalyze` (S2), jeśli zarejestrowane; alerty idempotentne (uuid5).
- `riskminer demo` (kroki pozostałych sesji wywoływane po nazwie i pomijane, gdy ich brak; kontrola duplikatów względem poprzedniego przebiegu; zapasowy eksport; raport; złoty zrzut), `riskminer report` → `docs/raport_z_testu.md`, `riskminer snapshot save|restore` (COPY, bez pg_dump – do resetu piaskownicy S5), `riskminer licences --check` (0 GPL/AGPL; psycopg LGPL opisany), `riskminer docs-gen` (ERD mermaid z `tables.py`), `riskminer monitor probe` (dostęp do lustra i ezamowienia.gov.pl: HTTP 200 z własnym UA, sprawdzone z hosta).
- Dokumenty: `uruchomienie.md`, `architektura.md`, `erd.md`, `zrodla_i_dopasowanie.md`, szkielet `opis_rozwiazania.md`, `prezentacja_plan.md`, `wideo_scenariusz.md`, README wg szablonu hn-zgloszenie, `LICENSES-THIRD-PARTY.md`.
- CI: job `docker` (build obrazów backend/web, walidacja compose) + sprawdzenie licencji.

**Zaprojektowane**
- Ponowna analiza jako diff (zależy od S2 `reanalyze`); metryki `/quality` od S1.
- Wpisanie liczb z raportu do README / opisu przy zamrożeniu (pola `{{…}}`).

**Znane problemy**
- Test pełnego stosu prod w dockerze nie został ukończony: dysk główny hosta zapełnił się podczas budowania (21.11 ~17:40); czeka na zwolnienie miejsca.
- `riskminer demo` uruchomione na pustej bazie S6 – kroki S1–S5 pominięte, bo ich polecenia nie są jeszcze scalone.
