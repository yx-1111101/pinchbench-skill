#!/usr/bin/env bash
set -euo pipefail

cd /root/.openclaw/workspace/pinchbench-skill

MODELS=(
  "openrouter/google/gemini-3-flash-preview"
  "openrouter/bytedance-seed/seed-2.0-lite"
  "openrouter/anthropic/claude-opus-4.6"
  "openrouter/minimax/minimax-m2.7"
  "openrouter/moonshotai/kimi-k2.5"
)

CURRENT_PID="${1:-285455}"
LOG_FILE="/root/.openclaw/workspace/pinchbench-skill/serial-run.log"
QUEUE_PID_FILE="/root/.openclaw/workspace/pinchbench-skill/serial-queue.pid"

echo $$ > "$QUEUE_PID_FILE"
trap 'rm -f "$QUEUE_PID_FILE"' EXIT

log() {
  printf '[%s] %s\n' "$(date '+%F %T')" "$*" | tee -a "$LOG_FILE"
}

log "Serial queue starting. Waiting for current PID=${CURRENT_PID} to finish before running remaining models."

if kill -0 "$CURRENT_PID" 2>/dev/null; then
  while kill -0 "$CURRENT_PID" 2>/dev/null; do
    sleep 20
  done
  log "Current glm-5 process ${CURRENT_PID} finished."
else
  log "Current PID ${CURRENT_PID} not running, start queue immediately."
fi

for model in "${MODELS[@]}"; do
  log "Starting benchmark for ${model}"
  ./.venv/bin/python scripts/benchmark.py --model "$model" 2>&1 | tee -a "$LOG_FILE"
  log "Finished benchmark for ${model}"
done

log "Serial queue completed."
