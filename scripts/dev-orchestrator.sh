#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT_DIR/services/orchestrator"

if [[ ! -f .venv/bin/activate ]]; then
  echo "Missing services/orchestrator/.venv. Run scripts/bootstrap.sh first."
  exit 1
fi

source .venv/bin/activate
python main.py
