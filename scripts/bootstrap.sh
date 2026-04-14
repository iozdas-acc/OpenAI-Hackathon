#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

echo "Bootstrapping frontend dependencies..."
cd "$ROOT_DIR/apps/web"
npm install

bootstrap_python_service() {
  local service_dir="$1"

  echo "Bootstrapping Python service: $service_dir"
  cd "$service_dir"

  if [[ ! -d .venv ]]; then
    python3 -m venv .venv
  fi

  .venv/bin/pip install -r requirements.txt
}

bootstrap_python_service "$ROOT_DIR/apps/api"
bootstrap_python_service "$ROOT_DIR/services/orchestrator"
bootstrap_python_service "$ROOT_DIR/services/context-graph"

echo
echo "Bootstrap complete."
echo "Next steps:"
echo "  scripts/dev-web.sh"
echo "  scripts/dev-api.sh"
echo "  scripts/dev-orchestrator.sh"
echo "  scripts/dev-context-graph.sh"
echo "  scripts/dev-db.sh"
