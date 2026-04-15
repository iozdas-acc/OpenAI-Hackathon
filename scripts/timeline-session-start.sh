#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

python3 "$ROOT_DIR/scripts/codex_timeline.py" init >/dev/null
python3 "$ROOT_DIR/scripts/codex_timeline.py" start "$@"
