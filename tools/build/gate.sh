#!/usr/bin/env bash
# Merge gate (Mac). Merges <ref> onto main in a separate gate worktree, runs the gates, and on PASS fast-forwards
# main and pushes it. Usage: tools/build/gate.sh area/<name> [commit]   (commit defaults to the branch tip)
# Gates: build exit 0, test.sh PASS, module_check 0, manifest_check 0, feel_check 0, encounter_check 0.
# The diff review is separate (see HANDOFF.md). Log: ../UmbrellaElla-areas/logs/gate-<name>.log
set -u
REF="$1"; C="${2:-$1}"; ROOT="$(cd "$(dirname "$0")/../.." && pwd)"; BASE="$(dirname "$ROOT")/UmbrellaElla-areas"; G="$BASE/gate"
cd "$ROOT"; git fetch -q origin
if [ ! -d "$G" ]; then git worktree add -q "$G" -B gate main; fi
mkdir -p "$G/Saved/Config/MacEditor"; cp -n "$ROOT/Saved/Config/MacEditor/GameUserSettings.ini" "$G/Saved/Config/MacEditor/" 2>/dev/null
cd "$G"; git reset -q --hard main
git -c core.hooksPath=/dev/null merge -q --no-ff -m "Merge $REF ($(git rev-parse --short "$C")) into main" "$C" || { echo "GATE FAIL: merge conflict"; git merge --abort; exit 1; }
fail=0
"$ROOT/tools/build/ue_slot.sh" tools/ue/build.sh 2>&1 | tail -1 | tee /dev/stderr | grep -q "build exit: 0" || fail=1
[ $fail = 0 ] && { "$ROOT/tools/build/ue_slot.sh" tools/ue/test.sh 2>&1 | tail -4 | tee /dev/stderr | grep -q "^PASS" || fail=1; }
for t in module_check manifest_check feel_check encounter_check; do python3 tools/$t.py 2>&1 | tail -1 | tee /dev/stderr | grep -q " 0 problem" || fail=1; done
if [ $fail = 0 ]; then
  cd "$ROOT"
  if ! git merge -q --ff-only gate 2>/dev/null; then
    # main moved during the gate. Merge anyway only if the new main commits touch no game files.
    base=$(git merge-base main gate)
    if git diff --name-only "$base" main | grep -q -E '^(Source|Config|Content|Plugins)/|\.uproject$'; then
      echo "GATE FAIL: main moved with game-file changes during the gate; rerun"; exit 1
    fi
    git -c core.hooksPath=/dev/null merge -q --no-edit -m "Merge gate result for $REF" gate || { git merge --abort; echo "GATE FAIL: merge"; exit 1; }
  fi
  git push -q origin main && echo "GATE PASS: main $(git rev-parse --short HEAD) pushed"
else echo "GATE FAIL: $REF $(git -C "$G" rev-parse --short HEAD) (main unchanged)"; exit 1; fi
