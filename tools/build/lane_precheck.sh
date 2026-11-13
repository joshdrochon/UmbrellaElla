#!/usr/bin/env bash
# Fast checks a lane must pass before it joins the gate queue (Josh, Nov 12: fail fast in the lane, not in the gate).
# Python only, no Unreal (the 3-job engine cap keeps builds and Unreal tests in the gate):
# merge-with-main dry run, art inventory, pipeline_check, quality no-new-FAIL vs the gate's last main baseline
# (includes the shipped-settings check), and the Python tests the change affects.
# Usage: lane_precheck.sh <area>   prints PRECHECK PASS or PRECHECK FAIL and the problem lines; exit 0/1.
#        lane_precheck.sh <area> --bg   runs in the background (a worker session's commands stop at 10 min) and writes
#        the result to ../logs/precheck-<area>.result: "RUNNING <time>" first, then the PRECHECK line and problems.
#        Poll that file until its first line starts with PRECHECK.
set -u
# Out of background QoS (Nov 13): a worker session runs at background QoS, which pins its children to efficiency cores;
# pipeline_check took ~10 min there vs 15 s at normal QoS. The checks are short; Josh's apps stay at higher priority.
taskpolicy -B -p $$ 2>/dev/null
A="$1"
# The main checkout, wherever this copy lives: the main repo's tools/build or a lane worktree's (Nov 13: the worktree
# copy took the worktree as the repo root and looked for ../UmbrellaElla-areas inside the areas folder).
here="$(cd "$(dirname "$0")" && pwd)"
common="$(git -C "$here" rev-parse --path-format=absolute --git-common-dir 2>/dev/null)"
ROOT="$(dirname "${common:-$here/../../.git}")"; BASE="$(dirname "$ROOT")/UmbrellaElla-areas"; L="$BASE/logs"; WT="$BASE/$A"
if [ "${2:-}" = --bg ]; then
  R="$L/precheck-$A.result"; echo "RUNNING $(date +%H:%M:%S)" > "$R"
  ( "$here/lane_precheck.sh" "$A" > "$R.tmp" 2> "$R.err"; mv "$R.tmp" "$R" ) </dev/null >/dev/null 2>&1 &
  echo "precheck for $A running in the background; poll $R until its first line starts with PRECHECK"; exit 0
fi
cd "$WT" || { echo "PRECHECK FAIL: no worktree $WT"; exit 1; }
out=""; add(){ out="$out
$1"; }
git -C "$ROOT" fetch -q origin
[ -n "$(git status --porcelain --untracked-files=no)" ] && add "uncommitted changes in tracked files (commit or revert)"
if ! git merge-tree --write-tree origin/main HEAD >/dev/null 2>&1; then
  c=$(git merge-tree --write-tree --name-only origin/main HEAD 2>/dev/null | sed -n '2,/^$/p' | grep -v '^$' | grep -v -E '^docs/build/(rule-status\.csv|areas/|requests/)' | head -5 | tr '\n' ' ')
  [ -n "$c" ] && add "merge conflict with main in: $c (merge main and resolve)"
fi
p=$(python3 tools/build/art_inventory.py check 2>&1 | grep -E "FAIL" | head -3); [ -n "$p" ] && add "$p"
p=$(python3 tools/pipeline_check.py 2>&1 | grep -E "^\[" | grep -v agent_play | head -3); [ -n "$p" ] && add "$p"
if [ -f "$L/quality-base.txt" ]; then
  p=$(QUALITY_SPRITE_BASE=origin/main python3 tools/build/quality_gate.py check origin/main "$L/quality-base.txt" 2>&1 | grep -E "new FAIL" | head -5)
  [ -n "$p" ] && add "$p"
fi
# Python tests only on request (PRECHECK_TESTS=1): under load they ran 20-50 min per lane (Nov 13); the gate runs them.
p=""; [ -n "${PRECHECK_TESTS:-}" ] && p=$(python3 tools/affected_tests.py --base origin/main --run 2>&1 | grep -E "^(FAIL|ERROR)" | head -3 2>/dev/null); [ -n "$p" ] && add "$p"
if [ -z "$out" ]; then echo "PRECHECK PASS"; exit 0; fi
echo "PRECHECK FAIL$out"; exit 1
