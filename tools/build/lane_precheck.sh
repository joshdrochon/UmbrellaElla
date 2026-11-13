#!/usr/bin/env bash
# Fast checks a lane must pass before it joins the gate queue (Josh, Nov 12: fail fast in the lane, not in the gate).
# Python only, no Unreal (the 3-job engine cap keeps builds and Unreal tests in the gate):
# merge-with-main dry run, art inventory, pipeline_check, quality no-new-FAIL vs the gate's last main baseline
# (includes the shipped-settings check), and the Python tests the change affects.
# Usage: lane_precheck.sh <area>   prints PRECHECK PASS or PRECHECK FAIL and the problem lines; exit 0/1.
set -u
A="$1"; ROOT="$(cd "$(dirname "$0")/../.." && pwd)"; BASE="$(dirname "$ROOT")/UmbrellaElla-areas"; L="$BASE/logs"; WT="$BASE/$A"
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
  p=$(python3 tools/build/quality_gate.py check origin/main "$L/quality-base.txt" 2>&1 | grep -E "new FAIL" | head -5)
  [ -n "$p" ] && add "$p"
fi
p=""; [ -z "${PRECHECK_FAST:-}" ] && p=$(python3 tools/affected_tests.py --base origin/main --run 2>&1 | grep -E "^(FAIL|ERROR)" | head -3 2>/dev/null); [ -n "$p" ] && add "$p"
if [ -z "$out" ]; then echo "PRECHECK PASS"; exit 0; fi
echo "PRECHECK FAIL$out"; exit 1
