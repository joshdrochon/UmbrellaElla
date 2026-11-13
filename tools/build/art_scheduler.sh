#!/usr/bin/env bash
# Start/stop the art scheduler (replaces ../UmbrellaElla-areas/art_keepalive.sh). Run from the main checkout.
#   tools/build/art_scheduler.sh start|stop|status|once|plan
set -u
ROOT="$(cd "$(dirname "$0")/../.." && pwd)"; BASE="$(dirname "$ROOT")/UmbrellaElla-areas"
PIDF="$BASE/.art-scheduler.pid"; mkdir -p "$BASE/logs"
alive() { [ -f "$PIDF" ] && kill -0 "$(cat "$PIDF")" 2>/dev/null; }
case "${1:-status}" in
  start)
    alive && { echo "art_scheduler already running pid $(cat "$PIDF")"; exit 0; }
    pkill -f "art_keepalive.sh" 2>/dev/null && echo "stopped old art_keepalive (its running loops stay; the scheduler adopts them)"
    env -u CLAUDECODE -u CLAUDE_CODE_ENTRYPOINT nohup python3 "$ROOT/tools/build/art_scheduler.py" run >>"$BASE/logs/art-scheduler.out" 2>&1 &
    echo $! > "$PIDF"; echo "art_scheduler pid $! log $BASE/logs/art-scheduler.log" ;;
  stop) alive && kill "$(cat "$PIDF")" && rm -f "$PIDF" && echo stopped || echo "not running" ;;
  once) python3 "$ROOT/tools/build/art_scheduler.py" run --once ;;
  plan) python3 "$ROOT/tools/build/art_scheduler.py" plan ;;
  status) alive && echo "running pid $(cat "$PIDF")" || echo "not running"; tail -5 "$BASE/logs/art-scheduler.log" 2>/dev/null ;;
  *) echo "usage: $0 start|stop|status|once|plan"; exit 2 ;;
esac
