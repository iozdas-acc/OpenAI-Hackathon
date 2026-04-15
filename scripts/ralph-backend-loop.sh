#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
LOG_DIR="$ROOT_DIR/reports/ralph-backend"
SCRIPT="$ROOT_DIR/scripts/ralph_backend_loop.py"

MODE="foreground"
ARGS=()

while [[ $# -gt 0 ]]; do
  case "$1" in
    --background)
      MODE="background"
      shift
      ;;
    --foreground)
      MODE="foreground"
      shift
      ;;
    *)
      ARGS+=("$1")
      shift
      ;;
  esac
done

mkdir -p "$LOG_DIR"

if [[ "$MODE" == "background" ]]; then
  nohup python3 "$SCRIPT" "${ARGS[@]}" >"$LOG_DIR/loop.log" 2>&1 &
  echo "Ralph backend loop started in background."
  echo "PID: $!"
  echo "Log: reports/ralph-backend/loop.log"
  exit 0
fi

exec python3 "$SCRIPT" "${ARGS[@]}"
