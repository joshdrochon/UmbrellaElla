#!/usr/bin/env bash
# Batch gate (Nov 12, throughput): take up to GATE_BATCH (default 8) queued lanes that merge cleanly together
# (overlapping files are fine when git merges them), merge them onto main in ../UmbrellaElla-areas/batch, and run the normal gate once on that combined branch (every check,
# targeted tests for the union, one review of the combined diff). PASS merges all of them; FAIL or HOLD puts each lane
# back at the front of the queue to be gated alone (a batch verdict is not recorded against any lane).
# Usage: gate_batch.sh <lane> [<lane>...]   prints the lanes it gated as a batch, or "single <lane>" when <2 qualify.
set -u
ROOT="$(cd "$(dirname "$0")/../.." && pwd)"; BASE="$(dirname "$ROOT")/UmbrellaElla-areas"; L="$BASE/logs"; W="$BASE/batch"
SHARED='^docs/build/(rule-status\.csv|areas/[a-z0-9]+(-status)?\.md|requests/[a-z0-9]+\.md)$'
git -C "$ROOT" fetch -q origin
[ -d "$W" ] || git -C "$ROOT" worktree add -q "$W" -B area/batch origin/main
cd "$W" && git reset -q --hard origin/main && git clean -qfd
picked=(); seen=""
for a in "$@"; do
  tip=$(git rev-parse "area/$a" 2>/dev/null) || continue
  grep -qx "$a" "$L/gate-never" 2>/dev/null && continue   # stopped or stale lanes the lead listed
  python3 "$ROOT/tools/build/gate_seen.py" check "$L" "$a" "$tip" >/dev/null || continue
  # Fast pre-check in the lane's worktree (inventory, pipeline_check, quality vs main): a lane that would fail is left out
  # of the batch and told why, instead of failing the whole batch (Nov 13: 8-lane batches failing on one doc path).
  if [ -d "$BASE/$a" ] && ! pc=$(PRECHECK_FAST=1 "$ROOT/tools/build/lane_precheck.sh" "$a" 2>&1); then
    echo "$(date +%H:%M) precheck $a: $(echo "$pc" | sed -n '2,4p' | tr '\n' ' ' | cut -c1-300)" >> "$L/precheck.log"
    python3 "$ROOT/tools/build/gate_seen.py" record "$L" "$a" "$tip" FAIL >/dev/null; continue
  fi
  files=""
  if git -c core.hooksPath=/dev/null merge -q --no-ff -m "Merge area/$a ($(git rev-parse --short "area/$a")) into batch" "area/$a" 2>/dev/null; then
    picked+=("$a"); seen="$seen
$files"
  else
    # a rule-status-only conflict is resolved row by row, anything else drops the lane from the batch
    u=$(git diff --name-only --diff-filter=U)
    echo "$u" | grep -qx docs/build/rule-status.csv && python3 "$ROOT/tools/build/rule_status_merge.py" >/dev/null
    echo "$u" | grep -qx docs/build/art-inventory.csv && { git checkout --ours docs/build/art-inventory.csv && python3 tools/build/art_inventory.py write >/dev/null 2>&1; git add docs/build/art-inventory.csv; }
    if [ -z "$(git diff --name-only --diff-filter=U)" ]; then
      git -c core.hooksPath=/dev/null commit -q --no-edit && { picked+=("$a"); seen="$seen
$files"; }
    else git merge --abort; fi
  fi
  [ ${#picked[@]} -ge "${GATE_BATCH:-8}" ] && break
done
if [ ${#picked[@]} -lt 2 ]; then git reset -q --hard origin/main; echo "single"; exit 0; fi
echo "batch ${picked[*]}"
