#!/usr/bin/env bash
# Smoke a packaged build: run it with -SmokeQuitAfter=15, then check exit code, SMOKE_OK, fps and the
# SMOKE_BAD log patterns in tools/ue_run.py (any > 0 fails), and fail on any new Saved/Crashes folder.
# Usage: tools/ue/smoke.sh <path to packaged game executable>. Env (all optional):
#   SMOKE_TIMEOUT=120  SMOKE_MAP=L_Graybox (short name the SMOKE_OK map= field must show)  SMOKE_GAME_MAP=/Game/UmbrellaElla/Maps/L_Graybox (full path, passes -SmokeMap=, card 0.6)
#   SMOKE_MIN_FPS=55 (0 = off)  SMOKE_RES=1280x720 SMOKE_WINDOW=windowed|fullscreen (display run; also checks
#   res=, win= and textpx >= SMOKE_MIN_TEXT_PX, default 18)  SMOKE_CRASH_DIRS=dir:dir (extra crash roots)
#   SMOKE_MAX_FRAME_MS=33 (worst_ms limit, 0 = off)  SMOKE_MAX_LOAD_MS=10000 (load_ms limit, 0 = off)  SMOKE_REQUIRE_INPUT=1 (0 = skip input=ok)  SMOKE_REQUIRE_GAMEPAD=1 (0 = skip gamepad=ok)
#   SMOKE_SECTION=S5 (passes -SmokeSection=)  SMOKE_RESTART_CYCLES=5 (passes -SmokeRestartCycles=, checks SMOKE_CYCLE)
#   SMOKE_NO_PLAYER_MAPS (default: pipeline/qa/no-player-maps.txt)  SMOKE_ALIVE_SECONDS=15  SMOKE_MODE=alive: no-log run (alive at 15 s, closed, exit 0); Shipping only if D-new-smoke picks it.
#   SMOKE_MAX_BOOT_S=20 (alive mode: first window within N s, 0 = off)  SMOKE_FORCE_CRASH=1 (passes -SmokeCrash; card 0.6
#   proves crash-check catches it: the run must FAIL with a new crash folder)
#   Every run passes -SmokeShot=<png>: smoke-log runs art_check.py and screen_check.py on that default-build screenshot
#   (either FAIL fails the smoke) and checks view=/aspect= (16:9) and debugdraw=0. SMOKE_FORCE_NO_ASPECT=1 passes
#   -SmokeNoAspectLock, SMOKE_FORCE_DEBUGDRAW=1 passes -SmokeDebugDraw: proof runs that must FAIL (card 0.6)
# SMOKE_OK fields and switches: the smoke hook contract in tools/ue_run.py.
#   SMOKE_ZIP=<gate zip> (the exe is from that zip, unzipped: a passing run appends its LAUNCH record line; launch-record
#   fails when the exe is not a file of that zip, final-10 B H2)
# The commit is checked against the package's BUILD_INFO.txt. The game's SMOKE_EFFECTIVE line (live tuning values and
# flags, compiled-in commit and workbench) is checked by tools/bake_preset.py effective against baked.json and the
# manifest (final-9 B C1).
set -euo pipefail
REPO="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
PY="${PYTHON:-python3}"
EXE="${1:-}"
[ -n "$EXE" ] && [ -x "$EXE" ] || { echo "usage: smoke.sh <packaged game executable>"; exit 2; }
LOGDIR="$REPO/Saved/Logs/pipeline"; mkdir -p "$LOGDIR"
GAMELOG="$LOGDIR/smoke-game-$(date +%Y%m%d-%H%M%S)-$$.log"
OUTLOG="${GAMELOG%.log}-stdout.log"
INFO="$(dirname "$EXE")"; for _ in 1 2 3 4 5; do [ -f "$INFO/BUILD_INFO.txt" ] && break; INFO="$(dirname "$INFO")"; done
[ -f "$INFO/BUILD_INFO.txt" ] || INFO="$(dirname "$EXE")"
CRASH=("$INFO" "$HOME/Library/Application Support/Epic/UmbrellaElla/Saved")   # [VERIFY Mac crash folder on 5.8.4]
if [ -n "${SMOKE_CRASH_DIRS:-}" ]; then IFS=: read -r -a X <<< "$SMOKE_CRASH_DIRS"; CRASH+=("${X[@]}"); fi
SNAP="${GAMELOG%.log}-crashes-before.txt"
"$PY" "$REPO/tools/ue_run.py" crash-list "${CRASH[@]}" --out "$SNAP"
SHOT="${GAMELOG%.log}-shot.png"
ARGS=(-SmokeShot="$SHOT")
# Automated runs never take over the screen or the speakers (Josh, Nov 12): no sound, small window, unless the quiet
# release smoke asks for sound (SMOKE_SOUND=1) or a display run sets SMOKE_RES.
[ "${SMOKE_SOUND:-0}" = "1" ] || ARGS+=(-nosound)
[ -n "${SMOKE_RES:-}" ] || ARGS+=(-windowed -ResX=640 -ResY=360); EXPECT=(--min-fps "${SMOKE_MIN_FPS:-55}" --max-frame-ms "${SMOKE_MAX_FRAME_MS:-33}" --max-load-ms "${SMOKE_MAX_LOAD_MS:-10000}" --shot "$SHOT")
[ -n "${SMOKE_NO_PLAYER_MAPS:-}" ] && EXPECT+=(--no-player-maps "$SMOKE_NO_PLAYER_MAPS")
[ "${SMOKE_REQUIRE_INPUT:-1}" = "0" ] && EXPECT+=(--no-input-check)
[ "${SMOKE_REQUIRE_GAMEPAD:-1}" = "0" ] && EXPECT+=(--no-gamepad-check)
[ -n "${SMOKE_GAME_MAP:-}" ] && ARGS+=(-SmokeMap="$SMOKE_GAME_MAP")
[ "${SMOKE_FORCE_CRASH:-0}" = "1" ] && ARGS+=(-SmokeCrash)   # [VERIFY -SmokeCrash in the card 0.6 hook]
[ "${SMOKE_FORCE_NO_ASPECT:-0}" = "1" ] && ARGS+=(-SmokeNoAspectLock)
[ "${SMOKE_FORCE_DEBUGDRAW:-0}" = "1" ] && ARGS+=(-SmokeDebugDraw)
if [ -n "${SMOKE_SECTION:-}" ]; then ARGS+=(-SmokeSection="$SMOKE_SECTION"); EXPECT+=(--expect-section "$SMOKE_SECTION"); fi
if [ -n "${SMOKE_RESTART_CYCLES:-}" ] && [ "$SMOKE_RESTART_CYCLES" != "0" ]; then
  ARGS+=(-SmokeRestartCycles="$SMOKE_RESTART_CYCLES"); EXPECT+=(--restart-cycles "$SMOKE_RESTART_CYCLES")   # [VERIFY]
fi
# SMOKE_EXPECT_RES=WxH: check res= without passing -ResX/-ResY (the settings step: a garbage ini falls back to 1080p)
[ -n "${SMOKE_EXPECT_RES:-}" ] && [ -z "${SMOKE_RES:-}" ] && EXPECT+=(--expect-res "$SMOKE_EXPECT_RES")
if [ -n "${SMOKE_RES:-}" ]; then
  W="${SMOKE_WINDOW:-windowed}"
  ARGS+=(-ResX="${SMOKE_RES%x*}" -ResY="${SMOKE_RES#*x}" "-$W")   # [VERIFY -ResX/-ResY/-windowed/-fullscreen]
  EXPECT+=(--expect-res "$SMOKE_RES" --expect-win "$W" --min-text-px "${SMOKE_MIN_TEXT_PX:-18}")
fi
rc=0
if [ "${SMOKE_MODE:-}" = "alive" ]; then
  "$PY" "$REPO/tools/ue_run.py" alive --seconds "${SMOKE_ALIVE_SECONDS:-15}" --max-boot-s "${SMOKE_MAX_BOOT_S:-0}" --log "$OUTLOG" -- "$EXE" -unattended -nocrashreports ${ARGS[@]+"${ARGS[@]}"} || rc=$?
else
  "$PY" "$REPO/tools/ue_run.py" run --timeout "${SMOKE_TIMEOUT:-120}" --log "$OUTLOG" -- \
    "$EXE" -SmokeQuitAfter=15 -log -abslog="$GAMELOG" -stdout -FullStdOutLogOutput -unattended -nocrashreports ${ARGS[@]+"${ARGS[@]}"} >/dev/null || rc=$?   # 5.8.4 Mac packaged: Log-verbosity lines (LogUmbrellaElla) reach stdout only with -stdout -FullStdOutLogOutput, and -abslog writes no file, so $OUTLOG is the game log
  LOGS=("$OUTLOG"); [ -f "$GAMELOG" ] && LOGS+=("$GAMELOG")
  echo "smoke logs: ${LOGS[*]}"
  if [ -f "$INFO/BUILD_INFO.txt" ]; then EXPECT+=(--expect-commit "$(sed -n 's/^commit=//p' "$INFO/BUILD_INFO.txt")"); fi
  WBI="$([ -f "$INFO/BUILD_INFO.txt" ] && sed -n 's/^workbench=//p' "$INFO/BUILD_INFO.txt" || true)"
  [ -n "$WBI" ] && EXPECT+=(--expect-workbench "$WBI")   # workbench=0: no workbench line may appear (D-new-workbench-debug)
  [ -n "${SMOKE_MAP:-}" ] && EXPECT+=(--expect-map "$SMOKE_MAP")
  r2=0; "$PY" "$REPO/tools/ue_run.py" --root "$REPO" smoke-log "${LOGS[@]}" --exit-code "$rc" "${EXPECT[@]}" || r2=$?; rc=$r2
  r3=0; "$PY" "$REPO/tools/bake_preset.py" --root "$REPO" effective "${LOGS[@]}" || r3=$?; [ "$r3" = "0" ] || rc=1
fi
cr=0; "$PY" "$REPO/tools/ue_run.py" crash-check --before "$SNAP" "${CRASH[@]}" || cr=$?
[ "$rc" = "0" ] && [ "$cr" = "0" ] || exit 1
if [ -n "${SMOKE_ZIP:-}" ] && [ "${SMOKE_MODE:-}" != "alive" ]; then
  "$PY" "$REPO/tools/ue_run.py" --root "$REPO" launch-record --zip "$SMOKE_ZIP" --exe "$EXE" "${LOGS[@]}" || exit 1
fi
