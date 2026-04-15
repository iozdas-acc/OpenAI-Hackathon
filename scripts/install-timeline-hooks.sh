#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

git -C "$ROOT_DIR" config core.hooksPath .githooks
python3 "$ROOT_DIR/scripts/codex_timeline.py" init >/dev/null

echo "Codex timeline hooks installed."
echo "Timeline file: $ROOT_DIR/.codex/timeline.json"
