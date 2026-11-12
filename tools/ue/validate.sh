#!/usr/bin/env bash
# Asset and data validation on Mac: runs the DataValidation commandlet on the project, fails on any error,
# and prints `validate: errors=N warnings=M` for the daily record. [VERIFY -run=DataValidation and its
# log lines on 5.8.4; the DataValidation plugin must be enabled, Technical Director's call]
source "$(dirname "$0")/common.sh"
LOG="$LOGDIR/validate-$STAMP-$$.log"
rc=0
"${UE_RUN[@]}" run --timeout "$UE_TIMEOUT" --log "$LOG" -- \
  "$UE_ROOT/Engine/Binaries/Mac/UnrealEditor.app/Contents/MacOS/UnrealEditor" "$PROJECT" \
  -run=DataValidation -unattended -nopause -nosplash -NullRHI -nocrashreports -stdout >/dev/null || rc=$?
if [ "$rc" = "124" ]; then echo "FAIL: validation timed out after ${UE_TIMEOUT}s; log: $LOG"; exit 124; fi
err="$(grep -cE "\bError:" "$LOG" || true)"
warn="$(grep -cE "\bWarning:" "$LOG" || true)"
echo "validate: errors=$err warnings=$warn  log: $LOG  exit: $rc"
[ "$rc" = "0" ] && [ "$err" = "0" ] || { echo "FAIL: data validation"; exit 1; }
