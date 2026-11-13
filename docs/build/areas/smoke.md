# Packaged smoke passes (G1 blocker). Branch area/smoke. Read docs/build/worker-rules.md first.
The first Mac Development package exists (main 5ae3718, built in /Users/joanmiguel/Desktop/Developer/UmbrellaElla-areas/
package). Two problems, both yours:
1. `tools/ue/package.sh` archives `Packaged/Mac/UmbrellaElla.app` WITHOUT `Contents/UE` (no paks: the game fails with
   "Failed to open descriptor file" and an ICU assertion). The staged app `Saved/StagedBuilds/Mac/UmbrellaElla.app` has
   the paks and runs. Find why the archive step drops Contents/UE on Mac 5.8.4 and fix package.sh (and package.ps1 only
   if the same logic applies on Windows), so `Packaged/Mac/UmbrellaElla.app` runs on its own.
2. Smoking the staged app (`tools/ue/smoke.sh .../Saved/StagedBuilds/Mac/UmbrellaElla.app/Contents/MacOS/UmbrellaElla`)
   runs and quits with exit 0 but prints no `SMOKE_OK` / `SMOKE_EFFECTIVE` and no LogUmbrellaElla lines, and -abslog
   writes no file. Make the smoke hook (`Source/UmbrellaElla/Private/Smoke/**`) work in a packaged Development build per
   the contract in `python3 tools/ue_run.py --help` (SMOKE_EFFECTIVE at=start/end, SMOKE_OK with view/aspect/debugdraw/
   fps/commit/workbench, input=ok and gamepad=ok, -SmokeQuitAfter), and make the game log reach the file smoke.sh reads.
Package with `UE_SLOT_EXCLUSIVE=1 tools/build/ue_slot.sh tools/ue/package.sh` in YOUR worktree (it needs a clean tree:
commit first), smoke with `tools/build/ue_slot.sh tools/ue/smoke.sh <exe inside the .app>`.
Lane: Source/UmbrellaElla/{Public,Private}/Smoke/**, Private/Tests/Smoke/**, tools/ue/package.sh, tools/ue/smoke.sh,
tools/ue/package.ps1, tools/ue/smoke.ps1 (only if needed). Done: package + smoke PASS (SMOKE_OK line), build and tests pass.
