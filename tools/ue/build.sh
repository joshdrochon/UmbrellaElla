#!/usr/bin/env bash
# Compile the editor target on Mac. Fails on compile errors; prints the warning count. NONUNITY=1 = strict build.
source "$(dirname "$0")/common.sh"
LOG="$LOGDIR/build-$STAMP.log"
EXTRA=()
[ "${NONUNITY:-0}" = "1" ] && EXTRA=(-DisableUnity -NoPCH -NoSharedPCH)
rc=0
"${UE_RUN[@]}" run --timeout "$UE_TIMEOUT" --log "$LOG" -- \
  "$UE_ROOT/Engine/Build/BatchFiles/Mac/Build.sh" UmbrellaEllaEditor Mac Development \
  -Project="$PROJECT" -WaitMutex ${EXTRA[@]+"${EXTRA[@]}"} || rc=$?
MODE=unity; [ "${NONUNITY:-0}" = "1" ] && MODE=nonunity
# One summary line; tools/check_pr.py reads exactly `build exit: <rc>  mode=<unity|nonunity>  commit=<sha>` (dry run A H3).
# The commit ties the line to the PR head (final-7 B H7).
COMMIT="$(git -C "$REPO" rev-parse HEAD 2>/dev/null || echo unknown)"
echo "build exit: $rc  mode=$MODE  commit=$COMMIT  warnings: $(grep -c ' warning:' "$LOG" || true)  log: $LOG"
exit "$rc"
