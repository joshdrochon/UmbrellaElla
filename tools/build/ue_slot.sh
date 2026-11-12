#!/usr/bin/env bash
# Run an Unreal command (build.sh, test.sh, package.sh, smoke.sh) only when one of UE_SLOTS (default 2) engine slots is free.
# Mac-only helper for parallel area workers on one machine: they share one engine and 10 cores. A slot whose holder PID
# died is reclaimed. Usage: tools/build/ue_slot.sh tools/ue/build.sh   (Windows: run the .ps1 scripts directly, no slots)
set -u
SLOTS="${UE_SLOTS:-2}"; DIR="${UE_SLOT_DIR:-/tmp/umbrellaella-ue-slots}"; mkdir -p "$DIR"
while :; do
  for i in $(seq 1 "$SLOTS"); do
    s="$DIR/slot$i"
    if mkdir "$s" 2>/dev/null; then
      echo "$$ $(pwd)" > "$s/owner"; trap 'rm -rf "$s"' EXIT INT TERM
      echo "ue_slot: slot $i taken by $$ for: $*" >&2
      "$@"; rc=$?; exit $rc
    fi
    pid=$(cut -d' ' -f1 "$s/owner" 2>/dev/null || echo "")
    if [ -n "$pid" ] && ! kill -0 "$pid" 2>/dev/null; then rm -rf "$s"; fi
  done
  sleep 20
done
