#!/usr/bin/env bash
# Run an Unreal command (build.sh, test.sh, package.sh, smoke.sh, run_game.sh) only when an engine slot is free.
# Mac helper for parallel area workers on one machine. Slots adapt to memory (Josh, Nov 12):
#   used < 36 GB -> 4 at once, < 44 GB -> 3, otherwise 2; at or above 56 GB no new Unreal command starts.
# Memory source: the line in ${UE_MEMWATCH:-~/.umbrella-ella-memwatch} ("used=31.9GB/64.0GB ..."), if it is fresh
# (under 3 min old), else vm_stat. UE_SLOTS=<n> forces a fixed count. A slot whose holder PID died is reclaimed.
# UE_SLOT_EXCLUSIVE=1 waits for every slot to be free and holds them all (packaging).
# Usage: tools/build/ue_slot.sh tools/ue/build.sh      (Windows: run the .ps1 scripts directly, no slots)
set -u
DIR="${UE_SLOT_DIR:-/tmp/umbrellaella-ue-slots}"; MW="${UE_MEMWATCH:-$HOME/.umbrella-ella-memwatch}"; mkdir -p "$DIR"
used_gb() {
  if [ -f "$MW" ] && [ $(( $(date +%s) - $(stat -L -f %m "$MW") )) -lt 180 ]; then
    sed -n 's/.*used=\([0-9.]*\)GB.*/\1/p' "$MW" | head -1; return
  fi
  vm_stat | awk -v ps="$(pagesize)" '/Pages active/{a=$3}/Pages wired/{w=$4}/occupied by compressor/{c=$5}
    END{printf "%.1f", (a+w+c)*ps/1073741824}'
}
allowed() {
  [ -n "${UE_SLOTS:-}" ] && { echo "$UE_SLOTS"; return; }
  # Josh, Nov 12 late: at most 3 Unreal-heavy jobs machine-wide; workers share 2, the gate's reserved slot is the 3rd.
  awk -v u="$(used_gb)" 'BEGIN{ if (u+0 >= 56) print 0; else if (u+0 < 44) print 2; else print 1 }'
}
held() {
  n=0
  for s in "$DIR"/slot*; do
    [ -d "$s" ] || continue
    pid=$(cut -d' ' -f1 "$s/owner" 2>/dev/null || echo "")
    if [ -n "$pid" ] && kill -0 "$pid" 2>/dev/null; then n=$((n + 1)); else rm -rf "$s"; fi
  done
  echo $n
}
while :; do
  if mkdir "$DIR/.mutex" 2>/dev/null; then
    max=$(allowed); have=$(held)
    if [ -n "${UE_SLOT_EXCLUSIVE:-}" ]; then
      # Packaging: UAT's own UBT calls fail on UBT's machine-wide mutex while any other build runs, so wait until no
      # slot is held, then hold enough slots that nobody else starts.
      # Reserve first (every caller counts these, so nobody new starts), then wait for the others to finish.
      if [ ! -d "$DIR/slot$$-x1" ]; then
        for i in 1 2 3 4 5 6; do mkdir "$DIR/slot$$-x$i"; echo "$$ $(pwd)" > "$DIR/slot$$-x$i/owner"; done
        trap 'rm -rf "$DIR"/slot$$-x*' EXIT INT TERM
        echo "ue_slot: exclusive reserved by $$, waiting for $have running" >&2
      fi
      if [ $(( have - 6 )) -le 0 ] && [ "$have" -ge 6 ]; then
        rmdir "$DIR/.mutex"
        echo "ue_slot: exclusive for $$: $*" >&2
        "$@"; exit $?
      fi
    # The merge gate gets one reserved slot above the cap (Nov 12: a gate test run starved for 43 min behind art loops).
    elif [ "$have" -lt "$max" ] || { [ -n "${UE_SLOT_GATE:-}" ] && [ "$max" -gt 0 ] && [ ! -d "$DIR/gate-held" ] && [ "$have" -lt $((max + 1)) ]; }; then
      [ -n "${UE_SLOT_GATE:-}" ] && { mkdir -p "$DIR/gate-held"; trap 'rm -rf "$DIR/gate-held"' EXIT; }
      s="$DIR/slot$$"; mkdir "$s"; echo "$$ $(pwd)" > "$s/owner"; rmdir "$DIR/.mutex"
      trap 'rm -rf "$s" "$DIR/gate-held"' EXIT INT TERM
      echo "ue_slot: slot taken by $$ ($((have + 1))/$max, used $(used_gb) GB) for: $*" >&2
      export UE_SLOT_HELD=1
      # One UBT build at a time machine-wide (parallel UBT runs fail with exit 6); the gate's build goes first.
      case "$1" in *build.sh)
        [ -n "${UE_SLOT_GATE:-}" ] && touch "$DIR/gate-wants-build"
        until { [ -n "${UE_SLOT_GATE:-}" ] || [ ! -f "$DIR/gate-wants-build" ]; } && mkdir "$DIR/build.lock" 2>/dev/null; do
          o=$(cat "$DIR/build.lock/owner" 2>/dev/null); [ -n "$o" ] && ! kill -0 "$o" 2>/dev/null && rm -rf "$DIR/build.lock"; sleep 5; done
        echo $$ > "$DIR/build.lock/owner"; rm -f "$DIR/gate-wants-build" 2>/dev/null
        trap 'rm -rf "$s" "$DIR/gate-held" "$DIR/build.lock"' EXIT INT TERM;;
      esac
      # Any editor or game launch builds first under the build lock when the module is older than the source
      # (Nov 13: an editor started by an import script auto-compiled outside the lock and broke the gate's build, exit 6).
      case "$1" in *build.sh) ;; *)
        dylib="$(pwd)/Binaries/Mac/libUnrealEditor-UmbrellaElla.dylib"
        if [ -d Source ] && { [ ! -f "$dylib" ] || [ -n "$(find Source -newer "$dylib" -name '*.[ch]*' -print -quit 2>/dev/null)" ]; }; then
          until mkdir "$DIR/build.lock" 2>/dev/null; do
            o=$(cat "$DIR/build.lock/owner" 2>/dev/null); [ -n "$o" ] && ! kill -0 "$o" 2>/dev/null && rm -rf "$DIR/build.lock"; sleep 5; done
          echo $$ > "$DIR/build.lock/owner"; trap 'rm -rf "$s" "$DIR/gate-held" "$DIR/build.lock"' EXIT INT TERM
          echo "ue_slot: module older than Source; building first under the build lock" >&2
          tools/ue/build.sh >&2; rm -rf "$DIR/build.lock"; trap 'rm -rf "$s" "$DIR/gate-held"' EXIT INT TERM
        fi;;
      esac
      "$@"; exit $?
    fi
    rmdir "$DIR/.mutex"
  else
    # A mutex older than a minute belongs to a killed process.
    [ $(( $(date +%s) - $(stat -f %m "$DIR/.mutex" 2>/dev/null || date +%s) )) -gt 60 ] && rmdir "$DIR/.mutex" 2>/dev/null
  fi
  sleep 15
done
