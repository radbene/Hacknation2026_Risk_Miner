# RISK MINER – developer entry points
SHELL := /bin/bash
BE := cd backend &&
UV := uv run

.PHONY: help up down db migrate api worker web dev test test-be test-fe lint openapi knowledge demo fmt report docs prod-test deploy

help:   ## list targets
	@grep -E '^[a-z-]+:.*##' $(MAKEFILE_LIST) | sed 's/:.*##/\t/'

up:     ## start Postgres (pgvector) in docker
	docker compose up -d db
down:
	docker compose down

migrate: up ## apply DB migrations
	$(BE) $(UV) alembic upgrade head

api:    ## run the API on :8040 (reload)
	$(BE) $(UV) uvicorn riskminer.api.main:app --reload --port 8040

worker: ## run the job worker
	$(BE) $(UV) riskminer worker

web:    ## run the frontend on :5180 (proxies /api → :8040)
	cd frontend && npm run dev

openapi: ## regenerate frontend/openapi.json + typed client
	$(BE) $(UV) riskminer openapi --out ../frontend/openapi.json
	cd frontend && npm run gen:api

knowledge: ## regenerate knowledge/wodkan/*.yaml from the expert docx
	$(BE) $(UV) riskminer knowledge import tests/fixtures/organizer/Risk_Miner_material_porady_fazy_dokumenty_ryzyka_ciekawostki.docx tests/fixtures/organizer/Risk_Miner_material_ekspercki_przygotowanie_inw_wodociagowej.docx

test: test-be test-fe ## all tests (must pass before a session reports done)
test-be:
	$(BE) $(UV) pytest -q
test-fe:
	cd frontend && npm run build

lint:
	$(BE) $(UV) ruff check riskminer tests

fmt:
	$(BE) $(UV) ruff check --fix riskminer tests && $(UV) ruff format riskminer tests

demo: migrate ## fresh pipeline: import → enrich → harvest(sample) → extract → analyse → export → report (filled in by S6)
	$(BE) $(UV) riskminer demo

report: ## regenerate docs/raport_z_testu.md from the DB
	$(BE) $(UV) riskminer report

docs: ## regenerate ERD + LICENSES-THIRD-PARTY.md (fails on GPL/AGPL)
	$(BE) $(UV) riskminer docs-gen && $(UV) riskminer licences --check

prod-test: ## full prod stack locally (compose project rmtest, :8088) – does not touch the dev DB
	deploy/local-prod-test.sh up

deploy: ## deploy to a server: make deploy HOST=root@1.2.3.4 [ARGS="--bootstrap --with-data --demo"]
	deploy/deploy.sh $(HOST) $(ARGS)
