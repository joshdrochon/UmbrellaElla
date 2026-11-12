#!/usr/bin/env bash
# Run UmbrellaElla automation tests headless on Mac, then check the report (not the exit code).
# Extra arguments go to check_automation_report.py: --bootstrap (card 0.3 only), --require NAME...,
# --test-map pipeline/qa/test-map.md (daily build), --max-rule-seconds S. BASELINE=<n> sets --baseline.
# TEST_FILTER=<full test name> runs one test alone (gate isolation check in qa-build.md).
# Tests that write files write under Saved/UmbrellaEllaTests and delete them. Leftovers from a crashed run are
# removed before the run; any file left there after the run fails it. Save slots (Saved/SaveGames) and
# Saved/Config/*/GameUserSettings.ini are hashed before the run; any change after it fails (state-check).
source "$(dirname "$0")/common.sh"
REPORT="$REPO/Saved/Automation"
LOG="$LOGDIR/test-$STAMP.log"
rm -rf "$REPORT"
SCRATCH="$REPO/Saved/UmbrellaEllaTests"
if [ -d "$SCRATCH" ]; then echo "reset: removed $(find "$SCRATCH" -type f | wc -l | tr -d " ") leftover file(s) in $SCRATCH"; rm -rf "$SCRATCH"; fi
STATE="$LOGDIR/test-$STAMP-$$-state-before.txt"
"${UE_RUN[@]}" state-list --out "$STATE"   # [VERIFY the editor itself leaves GameUserSettings.ini alone on 5.8.4]
rc=0
"${UE_RUN[@]}" run --timeout "$UE_TIMEOUT" --log "$LOG" -- \
  "$UE_ROOT/Engine/Binaries/Mac/UnrealEditor.app/Contents/MacOS/UnrealEditor" "$PROJECT" \
  -ExecCmds="Automation RunTests ${TEST_FILTER:-UmbrellaElla};Quit" -TestExit="Automation Test Queue Empty" \
  -ReportExportPath="$REPORT" -unattended -nopause -nosplash -NullRHI -nocrashreports -stdout >/dev/null || rc=$?
if [ "$rc" = "124" ]; then echo "FAIL: editor timed out after ${UE_TIMEOUT}s; log: $LOG"; exit 124; fi
# The (world) marks of the test map always count, so a world test is the same test here, in the daily and in the map
# (final-10 A H4); --test-map (the daily) also requires the merged rows' tests.
WMAP="$REPO/pipeline/qa/test-map.md"; WARGS=(); [ -f "$WMAP" ] && WARGS=(--world-map "$WMAP")
rc=0; "$PY" "$REPO/tools/check_automation_report.py" "$REPORT/index.json" ${BASELINE:+--baseline "$BASELINE"} ${WARGS[@]+"${WARGS[@]}"} "$@" || rc=$?
left="$( [ -d "$SCRATCH" ] && find "$SCRATCH" -type f || true)"
if [ -n "$left" ]; then echo "FAIL: tests left file(s) in $SCRATCH (each test deletes what it writes):"; echo "$left" | head -20; exit 1; fi
"${UE_RUN[@]}" state-check --before "$STATE" || exit 1
exit "$rc"
