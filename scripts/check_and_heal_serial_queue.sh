#!/usr/bin/env bash
set -euo pipefail

cd /root/.openclaw/workspace/pinchbench-skill

CHECK_LOG="/root/.openclaw/workspace/pinchbench-skill/serial-check.log"
QUEUE_SCRIPT="/root/.openclaw/workspace/pinchbench-skill/scripts/run_remaining_models_serial.sh"
GLM_PID_FILE="/root/.openclaw/workspace/pinchbench-skill/glm5.pid"
QUEUE_PID_FILE="/root/.openclaw/workspace/pinchbench-skill/serial-queue.pid"
GLM_CMD='scripts/benchmark.py --model openrouter/z-ai/glm-5-turbo'

log() {
  printf '[%s] %s\n' "$(date '+%F %T')" "$*" >> "$CHECK_LOG"
}

has_glm() {
  pgrep -af "$GLM_CMD" >/dev/null 2>&1
}

has_queue() {
  if [[ -f "$QUEUE_PID_FILE" ]]; then
    local pid
    pid="$(cat "$QUEUE_PID_FILE" 2>/dev/null || true)"
    [[ -n "$pid" ]] && kill -0 "$pid" 2>/dev/null && return 0
  fi
  pgrep -af "run_remaining_models_serial.sh" >/dev/null 2>&1
}

if has_glm; then
  log "OK: glm-5 benchmark is running."
else
  log "WARN: glm-5 benchmark is not running."
fi

if has_queue; then
  log "OK: serial queue is running."
else
  log "HEAL: serial queue missing, relaunching."
  nohup "$QUEUE_SCRIPT" > /tmp/pinchbench-serial-launch.log 2>&1 &
  echo $! > "$QUEUE_PID_FILE"
  sleep 1
  if has_queue; then
    log "HEAL_OK: serial queue relaunched successfully."
  else
    log "HEAL_FAIL: serial queue relaunch failed."
  fi
fi
