#!/usr/bin/env bash
# Run a command on a quiet machine (release smoke, Josh Nov 12): pause every area worker and its Unreal, build and
# Blender children with SIGSTOP, wait until the 1-minute load average is under QUIET_LOAD (default 4, max 180 s),
# run the command, then resume everything (also on exit or interrupt). The fps bar itself never changes.
# Usage: tools/build/quiet.sh tools/ue/smoke.sh <exe>
set -u
LOAD="${QUIET_LOAD:-4}"; PIDS=""
for w in $(pgrep -f "claude -p You are the '.*' area worker"); do
  PIDS="$PIDS $w $(pgrep -P "$w" | tr '\n' ' ')"
done
PIDS="$PIDS $(pgrep -f 'UnrealEditor|UnrealBuildTool|ShaderCompileWorker|Blender' | tr '\n' ' ')"
resume() { [ -n "${PIDS// }" ] && kill -CONT $PIDS 2>/dev/null; }
trap resume EXIT INT TERM
[ -n "${PIDS// }" ] && kill -STOP $PIDS 2>/dev/null
echo "quiet: paused $(echo $PIDS | wc -w | tr -d ' ') process(es)" >&2
for i in $(seq 1 36); do
  l=$(sysctl -n vm.loadavg | awk '{print $2}')
  awk -v l="$l" -v m="$LOAD" 'BEGIN{exit !(l < m)}' && break
  sleep 5
done
echo "quiet: load average $(sysctl -n vm.loadavg | awk '{print $2}') when the command starts" >&2
"$@"
