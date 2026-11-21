#!/usr/bin/env bash
# RISK MINER – deploy to a single Ubuntu host (Hetzner CX32/CPX31, DE/FI) with docker compose.
#
#   deploy/deploy.sh root@1.2.3.4                 # rsync the working tree, build, start, smoke test
#   deploy/deploy.sh root@1.2.3.4 --bootstrap     # first time: install docker + firewall, then deploy
#   deploy/deploy.sh root@1.2.3.4 --with-data     # also upload data/ (BZP zip, raw store, LLM replay cache)
#   deploy/deploy.sh root@1.2.3.4 --demo          # after start: run `riskminer demo` inside the api container
#
# Env: REMOTE_DIR (default /opt/riskminer), DOMAIN (default <ip>.sslip.io), SSH_OPTS.
set -euo pipefail

HOST="${1:?usage: deploy/deploy.sh user@host [--bootstrap] [--with-data] [--demo]}"; shift || true
BOOTSTRAP=0; WITH_DATA=0; DEMO=0
for a in "$@"; do
  case "$a" in
    --bootstrap) BOOTSTRAP=1 ;;
    --with-data) WITH_DATA=1 ;;
    --demo) DEMO=1 ;;
    *) echo "unknown option $a" >&2; exit 2 ;;
  esac
done
REMOTE_DIR="${REMOTE_DIR:-/opt/riskminer}"
SSH_OPTS="${SSH_OPTS:-}"
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
IP="$(ssh $SSH_OPTS "$HOST" "curl -4fsS https://ifconfig.me || hostname -I | cut -d' ' -f1")"
DOMAIN="${DOMAIN:-${IP}.sslip.io}"
say() { printf '\n\033[1m▶ %s\033[0m\n' "$*"; }

if [[ $BOOTSTRAP == 1 ]]; then
  say "Bootstrap $HOST (docker, ufw)"
  ssh $SSH_OPTS "$HOST" 'bash -s' < "$ROOT/deploy/bootstrap.sh"
fi

say "Sync code → $HOST:$REMOTE_DIR"
ssh $SSH_OPTS "$HOST" "mkdir -p $REMOTE_DIR/data $REMOTE_DIR/exports $REMOTE_DIR/config"
rsync -az --delete -e "ssh $SSH_OPTS" \
  --exclude .git --exclude '.venv' --exclude node_modules --exclude 'frontend/dist' \
  --exclude '__pycache__' --exclude '.pytest_cache' --exclude '.ruff_cache' \
  --exclude 'data/' --exclude 'exports/' --exclude '.env' --exclude 'config/settings.yaml' \
  "$ROOT/" "$HOST:$REMOTE_DIR/"
if [[ $WITH_DATA == 1 ]]; then
  say "Upload data/ (zip, raw store, LLM cache)"
  rsync -az --info=progress2 -e "ssh $SSH_OPTS" "$ROOT/data/" "$HOST:$REMOTE_DIR/data/"
fi

say "Server .env / settings (created once, never overwritten)"
ssh $SSH_OPTS "$HOST" "cd $REMOTE_DIR && \
  if [ ! -f .env ]; then cp .env.example .env && \
    sed -i \"s/^POSTGRES_PASSWORD=.*/POSTGRES_PASSWORD=\$(openssl rand -hex 16)/; s/^SECRET_KEY=.*/SECRET_KEY=\$(openssl rand -hex 32)/; s/^LLM_MODE=.*/LLM_MODE=cache/\" .env && \
    echo '  created .env – add API keys: ssh $HOST nano $REMOTE_DIR/.env'; fi && \
  sed -i '/^DOMAIN=/d; /^CORS_ORIGINS=/d' .env && echo 'DOMAIN=$DOMAIN' >> .env && echo 'CORS_ORIGINS=https://$DOMAIN' >> .env && \
  [ -f config/settings.yaml ] || cp config/settings.example.yaml config/settings.yaml"

say "Build + start (docker compose --profile prod)"
ssh $SSH_OPTS "$HOST" "cd $REMOTE_DIR && docker compose --profile prod up -d --build --remove-orphans && docker compose ps"

say "Smoke test https://$DOMAIN"
for i in $(seq 1 40); do
  if curl -fsS "https://$DOMAIN/api/health" >/dev/null 2>&1; then break; fi
  sleep 3
done
curl -fsS "https://$DOMAIN/api/health" && echo
curl -fsS -o /dev/null -w "web: HTTP %{http_code}\n" "https://$DOMAIN/"
ssh $SSH_OPTS "$HOST" "cd $REMOTE_DIR && docker compose exec -T api riskminer monitor probe" || echo "⚠ outbound BZP probe failed"

if [[ $DEMO == 1 ]]; then
  say "riskminer demo (inside api container)"
  ssh $SSH_OPTS "$HOST" "cd $REMOTE_DIR && docker compose exec -T api riskminer demo"
fi
say "Live: https://$DOMAIN   (API docs: https://$DOMAIN/api/docs)"
