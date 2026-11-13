#!/usr/bin/env bash
# Package a Mac build (Win64 must be packaged on Windows with package.ps1). SHIPPING=1 for Shipping.
# Default: the submission target UmbrellaElla, workbench compiled out (D-new-workbench-debug); workbench-check must pass.
# --workbench (or WORKBENCH=1): the tester target UmbrellaEllaWorkbench, never submitted (BuildCookRun -target= [VERIFY on 5.8.4]). Not with SHIPPING=1.
# Refuses a dirty git tree unless --allow-dirty (or ALLOW_DIRTY=1). build-info writes BUILD_INFO.txt into the package
# and copies pipeline/submission/README.txt and LICENSE.txt next to it.
source "$(dirname "$0")/common.sh"
ALLOW=(); WB="${WORKBENCH:-0}"
[ "${ALLOW_DIRTY:-0}" = "1" ] && ALLOW=(--allow-dirty)
for a in "$@"; do case "$a" in --allow-dirty) ALLOW=(--allow-dirty) ;; --workbench) WB=1 ;; *) echo "unknown option: $a"; exit 2 ;; esac; done
if [ "$WB" = "1" ] && [ "${SHIPPING:-0}" = "1" ]; then echo "FAIL: --workbench with SHIPPING=1; the workbench is dev-only"; exit 2; fi
"${UE_RUN[@]}" clean-tree ${ALLOW[@]+"${ALLOW[@]}"} || exit 1
# The commit is stamped at build start and compiled in (UmbrellaElla.Target.cs reads UMBRELLAELLA_BUILD_COMMIT into the
# game, which logs it in SMOKE_EFFECTIVE); BUILD_INFO gets the same value, never HEAD after the build (final-9 B H5).
COMMIT="$(git -C "$REPO" rev-parse HEAD 2>/dev/null || echo unknown)"
DIRTY=no; [ -n "$(git -C "$REPO" status --porcelain 2>/dev/null)" ] && DIRTY=yes
export UMBRELLAELLA_BUILD_COMMIT="$COMMIT"
TARGET=UmbrellaElla
if [ "$WB" = "1" ]; then TARGET=UmbrellaEllaWorkbench; else "${UE_RUN[@]}" workbench-check || exit 1; fi
CFG=Development; EXTRA=()
[ "${SHIPPING:-0}" = "1" ] && CFG=Shipping && EXTRA=(-nodebuginfo)
LOG="$LOGDIR/package-$STAMP-$$.log"   # one log per run: the error and warning counts read it
# The tester package goes to its own folder, and each run starts from an empty one, so BUILD_INFO and the exe always
# belong to this run and a zip never holds two targets (final-7 dry run A M7).
OUT="$REPO/Packaged"; [ "$WB" = "1" ] && OUT="$REPO/Packaged-Workbench"
rm -rf "$OUT"
rc=0
"${UE_RUN[@]}" run --timeout "$UE_TIMEOUT" --log "$LOG" -- \
  "$UE_ROOT/Engine/Build/BatchFiles/RunUAT.sh" BuildCookRun -project="$PROJECT" -target="$TARGET" -noP4 -platform=Mac \
  -clientconfig=$CFG -build -cook -stage -pak -iostore -archive -archivedirectory="$OUT" \
  -unattended -utf8output -nocrashreports -AdditionalCookerOptions=-nocrashreports -UbtArgs=-WaitMutex ${EXTRA[@]+"${EXTRA[@]}"} || rc=$?
# UAT's Mac archive step copies Binaries/Mac/<Target>.app (the build output: no Contents/UE, so no paks and no engine
# config) into the archive. The staged app Saved/StagedBuilds/Mac/<Target>.app is the complete one (Xcode "Stage" mode
# syncs the staged data into Contents/UE and signs it). Replace the archived app with it; ditto keeps signature and modes.
STAGED_APP="$REPO/Saved/StagedBuilds/Mac/$TARGET.app"
if [ "$rc" = "0" ] && [ -d "$STAGED_APP/Contents/UE" ]; then
  rm -rf "$OUT/Mac/$TARGET.app" && mkdir -p "$OUT/Mac" && ditto "$STAGED_APP" "$OUT/Mac/$TARGET.app" || rc=1
elif [ "$rc" = "0" ]; then echo "FAIL: staged app $STAGED_APP has no Contents/UE"; rc=1; fi
[ "$rc" = "0" ] && [ -d "$OUT/Mac/$TARGET.app/Contents/UE" ] && echo "archive app has Contents/UE: ok"
if grep -E "^(Error:|.*LogCook: Error)" "$LOG" >/dev/null; then echo "FAIL: errors in cook log $LOG"; exit 1; fi
echo "cook warnings: $(grep -cE "^Warning:|LogCook: Warning" "$LOG" || true)"   # daily fails if it rises [VERIFY pattern on 5.8.4]
NOW="$(git -C "$REPO" rev-parse HEAD 2>/dev/null || echo unknown)"
if [ "$NOW" != "$COMMIT" ]; then echo "FAIL: HEAD moved from $COMMIT to $NOW during packaging; the binary is $COMMIT's. Package again."; rc=1; fi
if [ "$DIRTY" = "no" ] && [ -n "$(git -C "$REPO" status --porcelain 2>/dev/null)" ]; then echo "FAIL: the tree changed during packaging. Package again."; rc=1; fi
if [ "$rc" = "0" ]; then "${UE_RUN[@]}" build-info --out "$OUT" --config "$CFG" --target "$TARGET" --workbench "$WB" --commit "$COMMIT" || rc=$?; fi
# One summary line; tools/check_pr.py reads exactly `package exit: <rc>  commit=<sha>  dirty=<yes|no>` (final-7 B H7, M8)
# and platform= (a card that asks for package.ps1 needs platform=Win64; final-9 A H5).
echo "package exit: $rc  commit=$COMMIT  dirty=$DIRTY  target=$TARGET  platform=Mac  log: $LOG"
exit "$rc"
