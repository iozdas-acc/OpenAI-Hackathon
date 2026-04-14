#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT_DIR/apps/web"

if [[ ! -d node_modules ]]; then
  echo "Missing apps/web/node_modules. Run scripts/bootstrap.sh first."
  exit 1
fi

npm run dev
