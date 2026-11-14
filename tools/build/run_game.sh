#!/usr/bin/env bash
# The one way an automated run starts the game (editor -game or a packaged exe): never fullscreen, never with sound,
# never with crash-reporter windows (Josh, Nov 12: playtest runs took over his screen with buzzing audio).
# Usage: tools/build/run_game.sh [--packaged <exe>] [extra game args...]   (editor -game on this checkout by default)
# Every run keeps its own game log: Saved/Logs/runs/run-<UTC stamp>-<pid>.log (printed as `run_game: log=`), because
# the Mac editor's default log is one shared, rotating file for every worktree. With -SmokeShot=<png> the run ends
# with `run_game: frame_check ...` on that shot, so a black or flat capture is caught where it is made.
# Editor runs refuse a stale module (any Source file newer than the editor dylib): the game would run old code
# (screenfix, Nov 13: a merged checkout without a rebuild ran the old 5 s shot and captured a black frame).
# RUN_STALE_OK=1 skips that check.
set -u
# Every game launch (playtests, screenshots) takes an engine slot like a build (Josh: at most 3 Unreal-heavy jobs).
[ -z "${UE_SLOT_HELD:-}" ] && exec "$(cd "$(dirname "$0")" && pwd)/ue_slot.sh" "$0" "$@"
ROOT="$(cd "$(dirname "$0")/../.." && pwd)"; UE_ROOT="${UE_ROOT:-/Users/Shared/Epic Games/UE_5.8}"
SAFE=(-nosound -windowed -ResX=640 -ResY=360 -unattended -nocrashreports -nosplash)
# RUN_RES=WxH: a larger capture (e.g. 1280x720, 1920x1080) renders offscreen, so no window takes over the screen.
if [ -n "${RUN_RES:-}" ]; then SAFE=(-nosound -RenderOffscreen -ForceRes -ResX="${RUN_RES%x*}" -ResY="${RUN_RES#*x}" -unattended -nocrashreports -nosplash); fi
# Offscreen captures render as fast as the GPU allows and lagged Josh's mouse (Nov 13): cap them at RUN_MAXFPS (default
# 30; 0 = uncapped). visual_qa scores at 30 fps match the uncapped ones within judge noise (visualqa status, item 3).
if [ -n "${RUN_RES:-}" ] && [ "${RUN_MAXFPS:-30}" != "0" ]; then SAFE+=("-ini:Engine:[ConsoleVariables]:t.MaxFPS=${RUN_MAXFPS:-30}"); fi
LOG_DIR="$ROOT/Saved/Logs/runs"; mkdir -p "$LOG_DIR"
LOG="$LOG_DIR/run-$(date -u +%Y%m%d-%H%M%S)-$$.log"
SHOT=""
for a in "$@"; do case "$a" in -SmokeShot=*) SHOT="${a#-SmokeShot=}";; esac; done
if [ -n "$SHOT" ] && [ "${SHOT#/}" = "$SHOT" ]; then SHOT="$ROOT/$SHOT"; fi   # the game resolves it against the project dir

if [ "${1:-}" = "--packaged" ]; then
  EXE="$2"; shift 2; CMD=("$EXE" "${SAFE[@]}" -abslog="$LOG" "$@")
else
  DYLIB="$ROOT/Binaries/Mac/libUnrealEditor-UmbrellaElla.dylib"
  if [ -z "${RUN_STALE_OK:-}" ]; then
    if [ ! -f "$DYLIB" ]; then echo "run_game: STALE no module at Binaries/Mac; run tools/build/ue_slot.sh tools/ue/build.sh first"; exit 3; fi
    NEWER="$(find "$ROOT/Source" -type f \( -name '*.cpp' -o -name '*.h' -o -name '*.cs' \) -newer "$DYLIB" 2>/dev/null | head -1)"
    if [ -n "$NEWER" ]; then
      echo "run_game: STALE ${NEWER#$ROOT/} is newer than the editor module; run tools/build/ue_slot.sh tools/ue/build.sh first (RUN_STALE_OK=1 skips)"
      exit 3
    fi
  fi
  CMD=("$UE_ROOT/Engine/Binaries/Mac/UnrealEditor.app/Contents/MacOS/UnrealEditor" "$ROOT/UmbrellaElla.uproject" -game "${SAFE[@]}" -abslog="$LOG" "$@")
fi
echo "run_game: log=$LOG"
[ -n "$SHOT" ] && rm -f "$SHOT"   # an old shot must never pass for this run's
"${CMD[@]}"; RC=$?
echo "run_game: exit=$RC log=$LOG"
grep -E "SMOKE_SHOT|SMOKE_VIEW" "$LOG" 2>/dev/null | sed 's/^.*LogUmbrellaElla: \(Display: \)\{0,1\}/run_game: /'
if [ -n "$SHOT" ]; then
  if [ -f "$SHOT" ]; then echo "run_game: $(python3 "$ROOT/tools/frame_check.py" "$SHOT")"; else echo "run_game: frame_check: FAIL no shot at $SHOT"; fi
fi
exit $RC
