#!/usr/bin/env bash
# Full prod-profile stack locally under a separate compose project (does NOT touch the dev DB on 55432).
#   deploy/local-prod-test.sh up | demo | down | logs
set -euo pipefail
cd "$(dirname "$0")/.."
export DOMAIN="${DOMAIN:-:80}" DB_PORT="${DB_PORT:-55499}" HTTP_PORT="${HTTP_PORT:-8088}" HTTPS_PORT="${HTTPS_PORT:-8443}"
DC=(docker compose -p rmtest --profile prod)
case "${1:-up}" in
  up)
    "${DC[@]}" up -d --build
    for i in $(seq 1 60); do curl -fsS "http://localhost:$HTTP_PORT/api/health" >/dev/null 2>&1 && break; sleep 2; done
    curl -fsS "http://localhost:$HTTP_PORT/api/health"; echo
    curl -fsS -o /dev/null -w "web: HTTP %{http_code}\n" "http://localhost:$HTTP_PORT/"
    "${DC[@]}" exec -T api riskminer monitor probe ;;
  demo) "${DC[@]}" exec -T api riskminer demo ;;
  logs) "${DC[@]}" logs --tail 100 ;;
  restart) "${DC[@]}" restart ;;
  down) "${DC[@]}" down ;;
  *) echo "usage: $0 up|demo|logs|restart|down"; exit 2 ;;
esac
