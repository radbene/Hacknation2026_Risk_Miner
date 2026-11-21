# RISK MINER

Inteligentna baza doświadczeń inwestycji publicznych – pilotaż: gospodarka wodno-ściekowa.
HackNation 2026, zadanie Ministerstwa Funduszy i Polityki Regionalnej.

> README in progress – final version (criteria table, disclosure) is prepared at submission.

## Quick start
```bash
cp .env.example .env
make up migrate      # Postgres + schema
make api             # API on :8040  (docs: http://localhost:8040/api/docs)
make web             # UI on :5180
make test
```

See `docs/plan.md` (plan), `docs/status.md` (what works vs designed), `CLAUDE.md` (dev rules).

## Licence
Apache-2.0 (see `LICENSE`). Third-party licences: `LICENSES-THIRD-PARTY.md`.
