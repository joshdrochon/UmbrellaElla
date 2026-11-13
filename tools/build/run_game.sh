#!/usr/bin/env bash
# The one way an automated run starts the game (editor -game or a packaged exe): never fullscreen, never with sound,
# never with crash-reporter windows (Josh, Nov 12: playtest runs took over his screen with buzzing audio).
# Usage: tools/build/run_game.sh [--packaged <exe>] [extra game args...]   (editor -game on this checkout by default)
set -u
ROOT="$(cd "$(dirname "$0")/../.." && pwd)"; UE_ROOT="${UE_ROOT:-/Users/Shared/Epic Games/UE_5.8}"
SAFE=(-nosound -windowed -ResX=640 -ResY=360 -unattended -nocrashreports -nosplash)
if [ "${1:-}" = "--packaged" ]; then EXE="$2"; shift 2; exec "$EXE" "${SAFE[@]}" "$@"; fi
exec "$UE_ROOT/Engine/Binaries/Mac/UnrealEditor.app/Contents/MacOS/UnrealEditor" "$ROOT/UmbrellaElla.uproject" -game "${SAFE[@]}" "$@"
