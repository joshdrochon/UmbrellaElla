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
GRP="$L/gate-groups"; touch "$GRP"
# Batches (Josh, Nov 12): up to 8 queued lanes that merge cleanly together are gated in one run (one build and test
# run, a review per lane). A failed batch is bisected: its two halves go to gate-groups and are gated next, down to
# single lanes, so the bad lane is found without re-gating every lane alone. A held batch records only the lanes whose
# review asked for changes; the rest go back to the queue.
gate_group() {   # $@ = lanes; gates them as one batch (or a single lane) and handles the verdict
  if [ $# = 1 ]; then
    "$ROOT/tools/build/gate.sh" "$1" > "$L/gate-$1.log" 2>&1; rc=$?
    echo "$(date +%H:%M) $1 rc=$rc: $(grep -E '^GATE' "$L/gate-$1.log" | tail -1)"; return
  fi
  out=$("$ROOT/tools/build/gate_batch.sh" "$@" 2>>"$L/gate-batch.err" | tail -1)
  if [ "${out%% *}" != batch ]; then for x in "$@"; do echo "$x" >> "$GRP"; done; return; fi
  lanes="${out#batch }"; for x in "$@"; do case " $lanes " in *" $x "*) ;; *) echo "$x" >> "$Q";; esac; done
  echo 0 > "$L/review-batch.round"
  "$ROOT/tools/build/gate.sh" batch area/batch > "$L/gate-batch.log" 2>&1; rc=$?
  echo "$(date +%H:%M) batch [$lanes] rc=$rc: $(grep -E '^GATE' "$L/gate-batch.log" | tail -1)"
  if [ $rc = 3 ]; then   # held: lanes whose review approved go back to the queue; held lanes wait for their worker
    held=$(grep -E '^GATE HOLD' "$L/gate-batch.log" | sed 's/.*in://; s/(send.*//')
    for x in $lanes; do case " $held " in *" $x "*) ;; *) echo "$x" >> "$Q";; esac; done
  elif [ $rc != 0 ]; then
    set -- $lanes; n=$#; h=$(( (n + 1) / 2 )); first="${*:1:$h}"; second="${*:$((h+1))}"
    echo "$first" >> "$GRP"; [ -n "$second" ] && echo "$second" >> "$GRP"
    echo "$(date +%H:%M) bisect: [$first] then [$second]"
  fi
}
while :; do
  if g=$(head -1 "$GRP") && [ -n "$g" ]; then sed -i '' '1d' "$GRP"; gate_group $g; continue; fi
  a=$(head -1 "$Q"); [ -z "$a" ] && break
  lanes=$(head -16 "$Q" | tr '\n' ' '); for x in $lanes; do sed -i '' "/^$x\$/d" "$Q"; done
  if [ "${GATE_BATCH:-8}" -gt 1 ]; then gate_group $lanes; else for x in $lanes; do echo "$x" >> "$Q"; done; sed -i '' '1d' "$Q"; gate_group "$a"; fi
done
