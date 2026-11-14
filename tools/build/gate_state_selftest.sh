#!/usr/bin/env bash
# Gate self-test (Josh, Nov 13): plant a progress save like the one a visual_qa capture leaves, run the gate's clean_state,
# then the Unreal test that the leftover broke; it must pass. Break check: without clean_state the same test must fail
# (proves the test still sees saves). Usage: tools/build/gate_state_selftest.sh [<worktree, default ../UmbrellaElla-areas/gate>] [--no-break]
# Run it only while no gate run is active. Exit 0 = PASS.
ROOT="$(cd "$(dirname "$0")/../.." && pwd)"; W="${1:-$(dirname "$ROOT")/UmbrellaElla-areas/gate}"; L="$(dirname "$ROOT")/UmbrellaElla-areas/logs"
. "$ROOT/tools/build/gate_clean_state.sh"
SAV="${GATE_SELFTEST_SAVE:-$(ls -t "$L"/gate-savegames-*/UmbrellaEllaProgress.sav 2>/dev/null | head -1)}"
[ -f "$SAV" ] || { echo "SELFTEST ERROR: no planted save found (GATE_SELFTEST_SAVE)"; exit 2; }
T=UmbrellaElla.Flow.World.LevelUpShowsAndResumes; cd "$W" || exit 2
plant(){ mkdir -p Saved/SaveGames; cp "$SAV" Saved/SaveGames/UmbrellaEllaProgress.sav; cp "$SAV" Saved/SaveGames/UmbrellaEllaProgress_Backup.sav; }
run(){ TEST_FILTER="$T" UE_SLOT_GATE=1 "$ROOT/tools/build/ue_slot.sh" tools/ue/test.sh 2>&1 | grep -E "^(PASS|FAIL)" | tail -1; }
rc=0
if [ "${2:-}" != --no-break ]; then
  plant; r=$(run); clean_state "$W"
  case "$r" in FAIL*) echo "ok   break check: planted save without clean_state -> $r";; *) echo "WARN break check: planted save did not fail the test ($r)";; esac
fi
plant; clean_state "$W"; [ -e Saved/SaveGames ] && { echo "FAIL clean_state left Saved/SaveGames"; rc=1; }
r=$(run); clean_state "$W"
case "$r" in PASS*) echo "ok   planted save + clean_state -> $r";; *) echo "FAIL planted save + clean_state -> $r"; rc=1;; esac
[ $rc = 0 ] && echo "SELFTEST PASS" || echo "SELFTEST FAIL"; exit $rc
