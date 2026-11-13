#!/usr/bin/env bash
# One gate at a time from a queue (the gate checkout is shared). Usage:
#   tools/build/gate_runner.sh add <area> [<area>...]   append to the queue (../UmbrellaElla-areas/logs/gate-queue)
#   tools/build/gate_runner.sh run                      process the queue until empty (one runner only; lock dir)
ROOT="$(cd "$(dirname "$0")/../.." && pwd)"; L="$(dirname "$ROOT")/UmbrellaElla-areas/logs"; Q="$L/gate-queue"; mkdir -p "$L"; touch "$Q"
if [ "${1:-}" = add ]; then shift; for a in "$@"; do grep -qx "$a" "$Q" || echo "$a" >> "$Q"; done; cat "$Q"
  # Adding always makes sure a runner is draining the queue (Nov 12: the runner exited on an empty queue and later adds sat).
  [ -d "$L/gate-runner.lock" ] || nohup "$0" run >> "$L/gate-runner.out" 2>&1 &
  exit 0; fi
mkdir "$L/gate-runner.lock" 2>/dev/null || { echo "a runner is already running"; exit 0; }
trap 'rmdir "$L/gate-runner.lock"' EXIT
SOLO="$L/gate-solo"; touch "$SOLO"
while a=$(head -1 "$Q") && [ -n "$a" ]; do
  # Batch non-overlapping lanes into one gate run (Nov 12 throughput); a lane that failed in a batch is then gated alone.
  if ! grep -qx "$a" "$SOLO" && [ "${GATE_BATCH:-4}" -gt 1 ]; then
    out=$("$ROOT/tools/build/gate_batch.sh" $(grep -v -x -F -f "$SOLO" "$Q" | head -8) 2>>"$L/gate-batch.err" | tail -1)
    if [ "${out%% *}" = batch ]; then
      lanes="${out#batch }"; for x in $lanes; do sed -i '' "/^$x\$/d" "$Q"; done
      echo 0 > "$L/review-batch.round"
      "$ROOT/tools/build/gate.sh" batch area/batch > "$L/gate-batch.log" 2>&1; rc=$?
      echo "$(date +%H:%M) batch [$lanes] rc=$rc: $(grep -E '^GATE' "$L/gate-batch.log" | tail -1)"
      if [ $rc != 0 ]; then { printf '%s\n' $lanes; cat "$Q"; } > "$Q.new" && mv "$Q.new" "$Q"; printf '%s\n' $lanes >> "$SOLO"; fi
      continue
    fi
  fi
  sed -i '' '1d' "$Q"; sed -i '' "/^$a\$/d" "$SOLO"
  "$ROOT/tools/build/gate.sh" "$a" > "$L/gate-$a.log" 2>&1; rc=$?
  echo "$(date +%H:%M) $a rc=$rc: $(grep -E '^GATE' "$L/gate-$a.log" | tail -1)"
done
