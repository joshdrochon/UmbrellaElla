#!/usr/bin/env bash
# Before each packaged build (Josh, Nov 12): the full suites that per-merge gates skip, then package and smoke on Mac.
#   1 full Unreal automation suite (tools/ue/test.sh)   2 game-facing Python checks (feel, encounter, manifest,
#     bake_preset defaults, submission_check prejam/assets). The pipeline's own Python suite belongs in the pipeline
#     repos' CI, not here (Josh, Nov 12).
#   3 non-unity build (NONUNITY=1 tools/ue/build.sh)    4 tools/ue/package.sh (Development)
#   5 tools/ue/smoke.sh on the package: SMOKE_OK, input=ok and gamepad=ok (QA-GP), 16:9, debugdraw=0, art/screen checks
#   6 tools/ui_check.py flow-check on the smoke log (UIFLOW)   7 encounter playthrough + encounter critic on the log
# Usage: tools/build/prepackage.sh   (from the main checkout; Xcode first launch must be done:
#        xcodebuild -checkFirstLaunchStatus exits 0). Windows: docs/build/windows-check.md.
set -u
ROOT="$(cd "$(dirname "$0")/../.." && pwd)"; cd "$ROOT"; S="$ROOT/tools/build/ue_slot.sh"; L="$ROOT/Saved/Logs/pipeline"; mkdir -p "$L"
fail=0; t() { T1=$(date +%s); }; s() { echo "[prepackage] $1 ($(( $(date +%s) - T1 )) s)"; }
xcodebuild -checkFirstLaunchStatus || { echo "prepackage: run sudo xcodebuild -runFirstLaunch first"; exit 1; }
[ -z "$(git status --porcelain -- Source Config Content UmbrellaElla.uproject)" ] || { echo "prepackage: commit Source/Config/Content changes first"; exit 1; }
t; "$S" tools/ue/build.sh 2>&1 | tail -1; s build
t; "$S" tools/ue/test.sh 2>&1 | tail -3 | tee "$L/prepackage-tests.txt"; grep -q "^PASS" "$L/prepackage-tests.txt" || fail=1; s "full Unreal tests"
for c in "feel_check.py" "encounter_check.py" "manifest_check.py" "bake_preset.py defaults" "submission_check.py prejam" "submission_check.py assets"; do
  t; python3 tools/$c > "$L/prepackage-py.txt" 2>&1 && s "$c PASS" || { s "$c FAIL"; tail -5 "$L/prepackage-py.txt"; fail=1; }
done
t; NONUNITY=1 "$S" tools/ue/build.sh 2>&1 | tail -1 | tee "$L/prepackage-nonunity.txt"; grep -q "build exit: 0" "$L/prepackage-nonunity.txt" || fail=1; s "non-unity build"
[ $fail = 0 ] || { echo "PREPACKAGE FAIL before packaging"; exit 1; }
t; "$S" tools/ue/package.sh 2>&1 | tail -3 | tee "$L/prepackage-package.txt"; s package
EXE=$(find "$ROOT/Packaged" -maxdepth 4 -name "UmbrellaElla*.app" -type d | head -1)
[ -n "$EXE" ] || { echo "PREPACKAGE FAIL: no packaged app"; exit 1; }
t; "$S" tools/ue/smoke.sh "$EXE" 2>&1 | tee "$L/prepackage-smoke.txt" | tail -4; grep -q "SMOKE_OK" "$L/prepackage-smoke.txt" || fail=1; s "smoke (input, gamepad, 16:9)"
SLOG=$(ls -t "$L"/smoke*.log 2>/dev/null | head -1)
if [ -n "$SLOG" ]; then
  t; python3 tools/ui_check.py flow-check --commit "$(git rev-parse HEAD)" "$SLOG" | tail -2 || fail=1; s "ui flow-check"
  t; ENCOUNTER_LOG="$SLOG" tools/build/critic.sh encounter "$L/prepackage-encounter-critic.txt" || fail=1; s "encounter critic"
fi
[ $fail = 0 ] && echo "PREPACKAGE PASS: $EXE commit $(git rev-parse --short HEAD)" || { echo "PREPACKAGE FAIL"; exit 1; }
