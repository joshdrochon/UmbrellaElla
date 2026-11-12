#!/usr/bin/env bash
# One gate at a time from a queue (the gate checkout is shared). Usage:
#   tools/build/gate_runner.sh add <area> [<area>...]   append to the queue (../UmbrellaElla-areas/logs/gate-queue)
#   tools/build/gate_runner.sh run                      process the queue until empty (one runner only; lock dir)
ROOT="$(cd "$(dirname "$0")/../.." && pwd)"; L="$(dirname "$ROOT")/UmbrellaElla-areas/logs"; Q="$L/gate-queue"; mkdir -p "$L"; touch "$Q"
if [ "${1:-}" = add ]; then shift; for a in "$@"; do grep -qx "$a" "$Q" || echo "$a" >> "$Q"; done; cat "$Q"; exit 0; fi
mkdir "$L/gate-runner.lock" 2>/dev/null || { echo "a runner is already running"; exit 0; }
trap 'rmdir "$L/gate-runner.lock"' EXIT
while a=$(head -1 "$Q") && [ -n "$a" ]; do
  sed -i '' '1d' "$Q"
  "$ROOT/tools/build/gate.sh" "$a" > "$L/gate-$a.log" 2>&1; rc=$?
  echo "$(date +%H:%M) $a rc=$rc: $(grep -E '^GATE' "$L/gate-$a.log" | tail -1)"
done
