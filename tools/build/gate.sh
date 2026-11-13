#!/usr/bin/env bash
# Merge gate (Mac). Merges <ref> onto main in the gate worktree (../UmbrellaElla-areas/gate), runs the checks that
# relate to the change, and on PASS updates main and pushes it.   Usage: tools/build/gate.sh <area> [commit]
# Josh, Nov 12: no PR/CI ceremony, every quality check kept, and per-merge checks run only what the change touches
# (tools/build/gate_plan.py). The full Unreal and Python suites run before each package (tools/build/prepackage.sh).
# Steps (each prints a line and its seconds):
#   merge (docs/build conflicts resolve to main's copy; art pass records verify and the gate re-runs the panel) -> build -> targeted automation tests -> module/manifest/feel/
#   encounter checks that apply -> quality_gate.py (art and audio ship only on pass; UI incl. flow-check and story
#   blocking vs main) -> submission_check prejam (+ assets when content changed) -> independent review session
#   (tools/build/review.sh; one round: "changes" holds the merge once, exit 3, then becomes follow-ups) -> critics
#   (story merges: story critic; keeper/enemies: encounter critic once the game writes a run log) -> update main, push.
# Exit 0 = merged, 1 = failed, 3 = held for review changes (send them to the area worker once, then rerun).
set -u
A="${1#area/}"; C="${2:-area/$A}"; ROOT="$(cd "$(dirname "$0")/../.." && pwd)"; BASE="$(dirname "$ROOT")/UmbrellaElla-areas"
G="${GATE_DIR:-$BASE/gate}"; GB="${GATE_BRANCH:-gate}"; L="$BASE/logs"; mkdir -p "$L"; T0=$(date +%s); fail=0
# A head the gate failed or held is never gated again; the lane needs new commits (Josh, Nov 12). Lane verdicts are
# recorded on exit (1 FAIL, 3 HOLD); exits that are not the lane's fault set NORECORD=1 first.
TIP="$(git -C "$ROOT" rev-parse "$C" 2>/dev/null)"; NORECORD=0
# Owner approvals are written only by the build lead on main; a lane that touches them never merges.
if git -C "$ROOT" diff --name-only "origin/main...$C" 2>/dev/null | grep -qx pipeline/art/approvals.json; then NORECORD=1; echo "GATE FAIL: area/$A changes pipeline/art/approvals.json (owner approvals are recorded by the lead on main only)"; exit 1; fi
# A batch must hold lane merges; an empty batch (branch reset to main) never passes (Nov 12: one "passed" and dropped 7 lanes).
if [ "$A" = batch ] && ! git -C "$ROOT" log --format=%s "origin/main..$C" | grep -q " into batch$"; then echo "GATE FAIL: area/batch holds no lane merges"; exit 1; fi
python3 "$ROOT/tools/build/gate_seen.py" check "$L" "$A" "$TIP" || exit 4
trap 'rc=$?; if [ "$NORECORD" = 0 ]; then case $rc in 1) python3 "$ROOT/tools/build/gate_seen.py" record "$L" "$A" "$TIP" FAIL;; 3) python3 "$ROOT/tools/build/gate_seen.py" record "$L" "$A" "$TIP" HOLD;; esac; fi' EXIT
step() { echo "[gate $A] $1 ($(( $(date +%s) - T1 )) s)"; }
# Art lanes wait for the pass-record verifier (Josh, Nov 12): no art-loop pass merges until main can re-verify it.
if [ "$A" != artinventory ] && { git -C "$ROOT" diff --name-only "main...$C" 2>/dev/null | grep -q '^pipeline/art/critic/' || [[ "$A" == art* ]]; }; then
  git -C "$ROOT" cat-file -e main:tools/build/art_pass_verify.py 2>/dev/null || { NORECORD=1; echo "GATE FAIL: area/$A waits for tools/build/art_pass_verify.py on main (pass records must be re-verified)"; exit 1; }
fi
cd "$ROOT"; git fetch -q origin
[ -d "$G" ] || git worktree add -q "$G" -B "$GB" main
mkdir -p "$G/Saved/Config/MacEditor"; cp -n "$ROOT/Saved/Config/MacEditor/GameUserSettings.ini" "$G/Saved/Config/MacEditor/" 2>/dev/null
cd "$G"; git reset -q --hard main; git clean -qfd; MAIN=$(git rev-parse HEAD)   # untracked leftovers from a killed run must not reach the checks
# The baseline depends only on main, so it is computed once per main SHA and reused (Nov 12: ~10 min per gate run).
T1=$(date +%s); QB="$L/quality-base-$MAIN.txt"
if [ -s "$QB" ]; then cp "$QB" "$L/quality-base.txt"; step "baseline (cached for $(git rev-parse --short HEAD))"
else python3 tools/build/quality_gate.py baseline "$QB.tmp" 2>/dev/null && mv "$QB.tmp" "$QB"; cp "$QB" "$L/quality-base.txt" 2>/dev/null; step "baseline"; fi
T1=$(date +%s)
if ! git -c core.hooksPath=/dev/null merge -q --no-ff -m "Merge area/$A ($(git rev-parse --short "$C")) into main" "$C" 2>/dev/null; then
  if git diff --name-only --diff-filter=U | grep -qx docs/build/rule-status.csv; then python3 tools/build/rule_status_merge.py || true; fi
  # The inventory CSV is generated: a conflict there is resolved by regenerating it from the merged tree.
  if git diff --name-only --diff-filter=U | grep -qx docs/build/art-inventory.csv; then git checkout --ours docs/build/art-inventory.csv && python3 tools/build/art_inventory.py write >/dev/null 2>&1; git add docs/build/art-inventory.csv; fi
  bad=$(git diff --name-only --diff-filter=U | grep -v -E '^docs/build/(areas/[a-z]+\.md|worker-rules\.md|areas\.py)$')
  if [ -n "$bad" ]; then echo "GATE FAIL: merge conflict in: $bad"; git merge --abort; exit 1; fi
  git diff --name-only --diff-filter=U | xargs git checkout --ours -- && git add -A docs/build && git -c core.hooksPath=/dev/null commit -q --no-edit
fi
git merge-base --is-ancestor "$TIP" HEAD || { NORECORD=1; echo "GATE FAIL: the merge of area/$A did not happen (git refused it; see the merge output above)"; exit 1; }
step "merge $(git rev-parse --short HEAD)"
# Branches that each kept a row for the same take merge into duplicates; collapse them to the row the critic record backs.
if python3 tools/build/provenance_dedupe.py | grep -q "rows -> 1"; then
  git add pipeline/art/provenance.csv && git -c core.hooksPath=/dev/null commit -q -m "Gate: collapse duplicate provenance rows from the merge of area/$A"
  step "provenance rows deduplicated"
fi
eval "$(python3 tools/build/gate_plan.py "$MAIN" HEAD)"
export CRITIC_CONTEXT=full   # Josh, Nov 13: critics run with full context
export UE_SLOT_GATE=1   # the gate always gets its reserved engine slot
SLOT="$ROOT/tools/build/ue_slot.sh"; EV="$L/gate-$A-evidence.txt"; : > "$EV"
chk() { local name="$1"; shift; T1=$(date +%s); out=$("$@" 2>&1); rc=$?; echo "$out" | tail -3 >> "$EV"
  if [ $rc -eq 0 ]; then step "$name PASS"; else step "$name FAIL"; echo "$out" | tail -15; fail=1; fi; }
# Rows turning built must have their proving tests run here (clause_check, Nov 13): add them to this merge's tests.
CLAUSE_TESTS=$(python3 tools/build/clause_check.py tests "$MAIN" 2>/dev/null)
CT_UE=$(echo "$CLAUSE_TESTS" | sed -n 's/^UE //p' | paste -sd+ -); CT_PY=$(echo "$CLAUSE_TESTS" | sed -n 's/^PY //p')
if [ -n "$CT_UE" ]; then SRC=1; TESTS="${TESTS:+$TESTS+}$CT_UE"; fi
for f in $CT_PY; do chk "clause py ${f##*/}" python3 -m unittest "$(echo "${f%.py}" | tr / .)"; done
if [ "$SRC" = 1 ]; then
  T1=$(date +%s); b=$("$SLOT" tools/ue/build.sh 2>&1 | tail -1); echo "$b" >> "$EV"
  # exit 6 = another UnrealBuildTool held UBT's machine-wide mutex (Nov 13, twice): wait for it, retry once.
  if echo "$b" | grep -q "build exit: 6"; then
    step "build exit 6 (another UBT running): waiting, then one retry"
    while pgrep -f "UnrealBuildTool.dll" >/dev/null; do sleep 5; done
    b=$("$SLOT" tools/ue/build.sh 2>&1 | tail -1); echo "retry: $b" >> "$EV"
  fi
  if echo "$b" | grep -q "build exit: 0"; then step "build PASS"; else step "build FAIL: $b"; fail=1; fi
  if [ $fail = 0 ]; then
    T1=$(date +%s); t=$(TEST_FILTER="$TESTS" "$SLOT" tools/ue/test.sh 2>&1 | tail -6); echo "$t" >> "$EV"
    if echo "$t" | grep -q "^PASS"; then step "tests PASS ($TESTS): $(echo "$t" | grep '^PASS' | cut -c1-40)"; else step "tests FAIL ($TESTS)"; echo "$t"; fail=1; echo "$t" | grep -q "report missing or unreadable" && NORECORD=1; fi   # no report = the run never finished (load), not the lane
  fi
fi
[ "$MODULE" = 1 ] && chk module_check python3 tools/module_check.py
[ "$MANIFEST" = 1 ] && chk manifest_check python3 tools/manifest_check.py
[ "$FEEL" = 1 ] && chk feel_check python3 tools/feel_check.py
[ "$ENCOUNTER" = 1 ] && chk encounter_check python3 tools/encounter_check.py
chk quality_gate python3 tools/build/quality_gate.py check "$MAIN" "$L/quality-base.txt"
chk art_pass_verify python3 tools/build/art_pass_verify.py check --base "$MAIN"
chk clause_check python3 tools/build/clause_check.py "$MAIN"   # a row may become built only with every GDD clause proven (Nov 13)
if [ $fail = 0 ]; then
  # The proof the panel really ran (Josh, Nov 12): every piece whose pass record is new in this merge is judged again by
  # fresh blind critic sessions on the same packets; the gate's panel must pass it too, or the merge fails.
  for pc in $(python3 tools/build/art_pass_verify.py newly-passed "$MAIN"); do
    T1=$(date +%s); out=$(python3 tools/art_loop.py gate-rerun --piece "$pc" 2>&1); rc=$?; echo "$out" | tail -2 >> "$EV"
    if [ $rc -eq 0 ]; then step "art panel re-run $pc PASS"; else step "art panel re-run $pc FAIL"; echo "$out" | tail -6; fail=1; fi
  done
fi
chk prejam python3 tools/submission_check.py prejam
[ "$ASSETS" = 1 ] && chk assets python3 tools/submission_check.py assets
if [ $fail = 0 ] && [ "$AUDIO" = 1 ]; then
  # Audio critic (Josh, Nov 12): a piece the blind critic fails ships as a tracked placeholder (provenance origin
  # "placeholder: ..."), recorded in a gate commit; it never blocks the merge.
  T1=$(date +%s)
  ids=$(git diff --name-only "$MAIN" HEAD -- Audio/Source | sed -n 's#^Audio/Source/\([^/]*\)/.*\.wav$#\1#p' | sort -u | paste -sd, -)
  if [ -n "$ids" ]; then
    "$ROOT/tools/build/critic.sh" audio "$L/audio-critic-$A.txt" "$ids" "GATE-$A-$(git rev-parse --short HEAD)" >/dev/null
    failed=$(sed -n 's/^AUDIO_CRITIC: FAIL piece=\([^ ]*\) gap=\(.*\)/\1\t\2/p' "$L/audio-critic-$A.txt")
    if [ -n "$failed" ]; then
      python3 - "$failed" <<'P'
import csv, sys
fails = dict(l.split("\t", 1) for l in sys.argv[1].splitlines() if "\t" in l)
rows = list(csv.reader(open("pipeline/art/provenance.csv")))
for r in rows[1:]:
    if r and r[0].startswith("Audio/Source/") and r[0].split("/")[2] in fails and not r[2].startswith("placeholder:"):
        r[2] = "placeholder: audio critic fail (" + fails[r[0].split("/")[2]][:120] + ")"
csv.writer(open("pipeline/art/provenance.csv", "w", newline=""), lineterminator="\n").writerows(rows)
P
      git add pipeline/art/provenance.csv && git -c core.hooksPath=/dev/null commit -q -m "Gate: audio critic failed $(echo "$failed" | cut -f1 | paste -sd, -); tracked as placeholders"
    fi
    step "audio critic: $(grep -c PASS "$L/audio-critic-$A.txt") pass, $(grep -c FAIL "$L/audio-critic-$A.txt") placeholder"
  fi
fi
if [ $fail = 0 ] && [ "$STORY" = 1 ]; then chk story_critic "$ROOT/tools/build/critic.sh" story "$L/critic-$A.txt"; fi
if [ $fail = 0 ] && [ "$ENCOUNTER" = 1 ]; then chk encounter_critic "$ROOT/tools/build/critic.sh" encounter "$L/critic-$A.txt"; fi
if [ $fail = 1 ]; then echo "GATE FAIL: area/$A $(git rev-parse --short HEAD) (main unchanged, $(( $(date +%s) - T0 )) s)"; exit 1; fi
if [ "$A" = batch ]; then
  # Batch (Josh, Nov 12): one independent review per lane on that lane's own diff, in parallel; any lane asking for
  # changes in its first round holds the batch, and that lane's tip is recorded so it needs new commits.
  T1=$(date +%s); LANES=$(git log --format=%s "$MAIN..HEAD" | sed -n 's/^Merge area\/\([a-z0-9]*\) .* into batch$/\1/p')
  for b in $LANES; do REVIEW_RANGE="$MAIN...area/$b" "$ROOT/tools/build/review.sh" "$b" "$EV" "$L/review-$b.txt" & done; wait
  held=""; for b in $LANES; do
    grep -q "VERDICT: approve" "$L/review-$b.txt" && { echo 0 > "$L/review-$b.round"; continue; }
    nb=$(cat "$L/review-$b.round" 2>/dev/null || echo 0)
    if [ "$nb" = 0 ]; then echo 1 > "$L/review-$b.round"; held="$held $b"
      python3 "$ROOT/tools/build/gate_seen.py" record "$L" "$b" "$(git -C "$ROOT" rev-parse "area/$b")" HOLD
    else echo "review changes for $b after the one round: follow-ups in $L/review-$b.txt"; fi
  done
  step "review per lane:$(for b in $LANES; do grep -q 'VERDICT: approve' "$L/review-$b.txt" && echo -n " $b=approve" || echo -n " $b=changes"; done)"
  [ -n "$held" ] && { NORECORD=1; echo "GATE HOLD: review asks for changes in:$held (send $L/review-<lane>.txt to each)"; exit 3; }
  rv=0; ROUND="$L/review-batch.round"; n=1
else
T1=$(date +%s); "$ROOT/tools/build/review.sh" "$A" "$EV" "$L/review-$A.txt"; rv=$?; step "review $( [ $rv = 0 ] && echo approve || echo changes/none )"
ROUND="$L/review-$A.round"; n=$(cat "$ROUND" 2>/dev/null || echo 0)
fi
if [ $rv != 0 ] && [ "$n" = 0 ]; then
  echo 1 > "$ROUND"; echo "GATE HOLD: review asks for changes; send $L/review-$A.txt to the $A worker once, then rerun"; exit 3
fi
[ $rv != 0 ] && echo "review changes after the one round: merge goes ahead; add $L/review-$A.txt items to HANDOFF follow-ups"
echo 0 > "$ROUND"
# Dry run (GATE_NOPUSH=1, with GATE_DIR/GATE_BRANCH for a separate checkout): every check ran; main is not touched.
if [ -n "${GATE_NOPUSH:-}" ]; then echo "GATE DRY PASS: area/$A $(git rev-parse --short HEAD) (main untouched, $(( $(date +%s) - T0 )) s)"; exit 0; fi
cd "$ROOT"
if ! git merge -q --ff-only "$GB" 2>/dev/null; then
  base=$(git merge-base main "$GB")
  if git diff --name-only "$base" main | grep -q -E '^(Source|Config|Content|Plugins)/|\.uproject$'; then
    NORECORD=1; echo "GATE FAIL: main moved with game-file changes during the gate; rerun"; exit 1
  fi
  git -c core.hooksPath=/dev/null merge -q --no-edit -m "Merge gate result for area/$A" "$GB" || { git merge --abort; echo "GATE FAIL: merge"; exit 1; }
fi
git push -q origin main 2>/dev/null || { git fetch -q origin && git -c core.hooksPath=/dev/null merge -q --no-edit origin/main && git push -q origin main; } || { echo "GATE FAIL: push"; exit 1; }
echo "GATE PASS: main $(git rev-parse --short HEAD) pushed ($(( $(date +%s) - T0 )) s)"
