#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "$0")" && pwd)"
DATA_DIR="$ROOT/data"
DEMO_DIR="$ROOT/demo_data"
BACKEND="$ROOT/backend/core_engine3.py"
PORT="${PORT:-18889}"

mkdir -p "$DATA_DIR"

for f in cultivation_save.json realm_progress.json sect_roster.json system_metrics.json cultivation_state.json current_event.json insight_log.jsonl; do
  if [ -f "$DEMO_DIR/$f" ] && [ ! -f "$DATA_DIR/$f" ]; then
    cp "$DEMO_DIR/$f" "$DATA_DIR/$f"
  fi
done

echo "[dragon-lobster] demo data prepared in $DATA_DIR"
echo "[dragon-lobster] starting server at http://0.0.0.0:$PORT"
exec python3 "$BACKEND"
