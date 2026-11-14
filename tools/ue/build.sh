#!/usr/bin/env bash
# Compile the editor target on Mac. Fails on compile errors; prints the warning count. NONUNITY=1 = strict build.
source "$(dirname "$0")/common.sh"
LOG="$LOGDIR/build-$STAMP.log"
EXTRA=()
[ "${NONUNITY:-0}" = "1" ] && EXTRA=(-DisableUnity -NoPCH -NoSharedPCH)
# -NoHotReload: write the base module names (libUnrealEditor-UmbrellaElla.dylib). Without it UBT switches to hot-reload
# names (-NNNN.dylib) whenever ANY full editor of this engine is open, on any checkout: the editor touches
# Engine/Intermediate/EditorRuns/<pid> (Developer/HotReload/Private/HotReload.cpp, CreateFileThatIndicatesEditorRunIfNeeded)
# and UBT matches only the editor executable path, not the project (Programs/UnrealBuildTool/System/HotReload.cs,
# ShouldDoHotReloadFromIDE; -NoHotReload = HotReloadMode.Disabled in Configuration/Descriptors/TargetDescriptor.cs).
# Disabled mode also deletes the earlier suffixed files listed in HotReloadState.json. Our runs start a fresh editor
# process, so they never need a hot reload. UE_HOT_RELOAD=1 keeps UBT's default (building for an editor open on this
# checkout).
[ "${UE_HOT_RELOAD:-0}" = "1" ] || EXTRA+=(-NoHotReload)
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
