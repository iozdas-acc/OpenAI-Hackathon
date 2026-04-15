#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT_DIR/apps/api"

if [[ ! -f .venv/bin/activate ]]; then
  echo "Missing apps/api/.venv. Run scripts/bootstrap.sh first."
  exit 1
fi

source .venv/bin/activate

if [[ -f "$ROOT_DIR/.env" ]]; then
  uvicorn main:app --reload --port 8000 --env-file "$ROOT_DIR/.env"
else
  uvicorn main:app --reload --port 8000
fi
