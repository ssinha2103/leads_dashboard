#!/usr/bin/env bash
set -euo pipefail

ROOT_DEFAULT="data/USA Database Business Leads"

have() { command -v "$1" &>/dev/null; }

# Detect Docker Compose v2 or legacy
if docker compose version &>/dev/null; then
  COMPOSE=(docker compose)
elif have docker-compose; then
  COMPOSE=(docker-compose)
else
  echo "Docker Compose is required (install Docker Desktop or docker-compose)." >&2
  exit 1
fi

usage() {
  cat <<USAGE
Usage: scripts/run.sh <command> [options]

Commands:
  up               Build and start the stack (attached)
  up-d             Build and start detached
  down             Stop the stack
  build            Rebuild images
  logs             Tail logs
  ps               Show service status
  migrate          Run Django migrations
  ingest [--root PATH] [--glob GLOB] [--limit N]
                   Ingest (CSV+XLSX). Defaults: root="$ROOT_DEFAULT", glob="all"
  ingest-gdrive --url URL [--glob GLOB] [--keep] [--out-dir DIR]
                   Download from Google Drive and ingest. Defaults: glob="all"
  superuser        Create a Django superuser

Examples:
  scripts/run.sh up
  scripts/run.sh ingest --root "data/USA Database Business Leads"
USAGE
}

cmd=${1:-}
shift || true

case "$cmd" in
  up)
    "${COMPOSE[@]}" up --build
    ;;
  up-d)
    "${COMPOSE[@]}" up --build -d
    ;;
  down)
    "${COMPOSE[@]}" down
    ;;
  build)
    "${COMPOSE[@]}" build --no-cache
    ;;
  logs)
    "${COMPOSE[@]}" logs -f
    ;;
  ps)
    "${COMPOSE[@]}" ps
    ;;
  migrate)
    "${COMPOSE[@]}" up -d
    "${COMPOSE[@]}" exec web python manage.py makemigrations --noinput
    "${COMPOSE[@]}" exec web python manage.py migrate --noinput
    ;;
  ingest)
    ROOT="$ROOT_DEFAULT"; GLOB='**/*.csv'; LIMIT=''
    while [[ $# -gt 0 ]]; do
      case "$1" in
        --root) ROOT="$2"; shift 2 ;;
        --glob) GLOB="$2"; shift 2 ;;
        --limit) LIMIT="$2"; shift 2 ;;
        *) echo "Unknown option: $1"; usage; exit 1 ;;
      esac
    done
    "${COMPOSE[@]}" up -d
    ARGS=(--root "$ROOT" --glob "$GLOB")
    if [[ -n "$LIMIT" ]]; then ARGS+=(--limit "$LIMIT"); fi
    "${COMPOSE[@]}" exec web python manage.py ingest_local "${ARGS[@]}"
    ;;
  ingest-gdrive)
    URL=''; GLOB='all'; KEEP=0; OUT_DIR='data'
    while [[ $# -gt 0 ]]; do
      case "$1" in
        --url) URL="$2"; shift 2 ;;
        --glob) GLOB="$2"; shift 2 ;;
        --keep) KEEP=1; shift 1 ;;
        --out-dir) OUT_DIR="$2"; shift 2 ;;
        *) echo "Unknown option: $1"; usage; exit 1 ;;
      esac
    done
    if [[ -z "$URL" ]]; then echo "--url is required"; usage; exit 1; fi
    "${COMPOSE[@]}" up -d
    ARGS=(--url "$URL" --glob "$GLOB" --out-dir "$OUT_DIR")
    if [[ "$KEEP" -eq 1 ]]; then ARGS+=(--no-cleanup); fi
    "${COMPOSE[@]}" exec web python manage.py ingest_gdrive "${ARGS[@]}"
    ;;
  superuser)
    "${COMPOSE[@]}" up -d
    "${COMPOSE[@]}" exec web python manage.py createsuperuser
    ;;
  *)
    usage
    ;;
esac
