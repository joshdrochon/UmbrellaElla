# playtest status (area/playtest)

## Done
- Lead item 1: `-SmokeShot=<png>` whole-window screenshot. `SmokeHookSubsystem` now requests the shot with
  bShowUI=true (Slate window, UI and bars), then 1 s later checks the file; if the engine wrote nothing it reads the
  Slate window back itself (`FSlateApplication::TakeScreenshot` + `FImageUtils::SaveImageByExtension`) and logs
  `SMOKE_SHOT_FILE written=<0|1> path_bytes=<n>`.
  Evidence: editor build `build exit: 0`; `UnrealEditor -game -SmokeQuitAfter=12 -SmokeShot=/tmp/pt-shot.png` (Mac,
  windowed 1280x720) logged `SMOKE_SHOT ... w=1280 h=720` and `SMOKE_SHOT_FILE written=1`, PNG with HUD clock and scene.
  NOT run: the packaged Mac build (build lead packages). If `written=0` appears there, the cause is the packaged backbuffer.
  Note: at 5 s the editor-game scene was still loading shaders (fps 1.8), so the frame is dark; not an engine fault.
- `tools/build/playtest_check.py` (checker + tests) for CAM-04, CAM-07, FLOW-25, FLOW-28, HAZ-16 lines (earlier commit).

## Left (blocked)
- The scripted run that writes the PLAYTEST_* lines and the measurements themselves. Needs "Merge area/smoke" on main
  (not there at last check, Nov 12 16:2x) and the Motor/Attack actions the hook says it lacks. CAM-04/07, FLOW-25/28
  also need arena's camera/route data; HAZ-16 needs enemies' Broken Mill. Next: merge main, add the scripted driver in
  `Smoke/` (-SmokePlaytest), emit the lines, run `playtest_check.py` on the log, record values here.

## Scripted run (Nov 12, after Merge area/smoke)
`-SmokePlaytest` (with `-SmokeQuitAfter=20`) runs `Smoke/PlaytestRun.cpp` in the live game: CAM-04 motor profiles in the Broken
Mill lower current at full/min health and trim 0/up/down; CAM-07 decision/reopen heights and the return currents while the
guard lives; FLOW-25 drawn vs usable wind width, camera lead along the route, backdrop coverage; a real-time Broken Mill run
(shoot only on the guard line, no aids); FLOW-28 carry-health and Keeper handoff through the level director.
`-PlaytestLowHealth` starts the HAZ run at half a life. Log: `docs/build/playtest-logs/run-2026-11-12.log`
(Mac editor `-game`, windowed, 4 runs). Check: `python3 tools/build/playtest_check.py <log>`.
Evidence: build exit 0, `UmbrellaElla.Smoke` tests PASS (4), module_check 0 problems.

| Row | Result | Why |
|---|---|---|
| CAM-04 | PASS | 6 profiles inside the envelope derived from Motor tuning (rise/free-fall speed x trim). Wind here is horizontal, so the vertical figure is lift/fall only. |
| CAM-07 | PASS | decision 270 vs reopen 61; both mill currents active while the guard is alive. Heights come from room geometry and Motor tuning, not a played free fall. |
| FLOW-25 | FAIL (real) | Wind actors have only a collision volume: drawn width 0 vs usable 200. Needs a drawn wind field (field/enemies lane). Camera lead and backdrop pass. |
| FLOW-28 | FAIL (real) | Health carries (2 -> 2, no free heal) and the handoff fires, but 4 enemies are still alive at handoff. |
| HAZ-16 | FAIL | One friendly hit (10 dmg) kills the 10 HP guard in about 1 s with no warning shown, so the proxy marks it boring. Two things not run: 1920x1080 (the display clamps the window to 1440x1080) and player words. The GDD's 20 HP comparison is the lever; that is a decision for the designer. |

## Left
- Wind field drawing (FLOW-25), clearing threats before the Keeper handoff (FLOW-28), guard HP vs one-shot (HAZ-16).
- 1920x1080 needs a display or fullscreen path that allows it; packaged-game run not done (build lead packages).

## Reviewer fixes (Nov 12 evening; every run through tools/build/run_game.sh)
- Fixed calibration: `tools/build/playtest_calibration.py` (profile mill_lower_v1) holds frozen ranges for the CAM-04 motor transients; the checker judges against them, not against the run's own numbers.
- Per-tick sampling: HAZ run checks every tick for teleport (`IsTeleportStep`, share 2.5 from a measured worst legit 2.02x at 0.16 s frames) and for both required currents live (`IsCurrentLive`, CAM07 `case=persist`).
- Measured falls: CAM-07 on-time/late/missed are free falls and reopens driven by the motor; FLOW-28 is a route driver calling the level director per tick, then reading threats at the handoff.
- `not_measured=<reason>` on a line makes the row `NOT MEASURED` (fail), never pass. FLOW-25 backdrop coverage uses `IsFrameCovered` per route slot.
- Evidence: build exit 0, `UmbrellaElla.Smoke` PASS (5), `tests.test_playtest_check` 20 OK, module_check 0 problems. Log `docs/build/playtest-logs/run-2026-11-12c.log` (640x360 window, no sound).

| Row | Result | Why |
|---|---|---|
| CAM-04 | FAIL | Real run: Ella never rides (actor-name vs `Ella` id, see requests/playtest.md #1, still on main). With the relay she rides but rises out the top of the band in about 0.5 s, before the far edge. |
| CAM-07 | FAIL real / pass with relay | Same wind bug; with the relay on-time and late reopens are caught with the body above the floor, and both currents stay live every tick. |
| FLOW-25 | FAIL | Drawn wind width 0 vs 200; backdrop covers 0 of 9 route stages in the frame test. |
| FLOW-28 | FAIL | Health carries (2 to 2), handoff fires, framing settles, but 5 enemies alive at handoff. |
| HAZ-16 | FAIL | Guard dies in about 1 s (boring). Not run: 1920x1080 (run_game.sh fixes 640x360) and low-health run in this log. |

## Lead request (levelchunks #2)
- FLOW-28 now calls `StepFollow(KeeperHandoffX(), 1)` once more after the handoff fires, then counts `AUmbrellaEnemy`. `GetThreatsRemaining()` does not exist in this tree or main, so the enemy count stays. Build exit 0. Not re-run in game: the handoff clear is not in this tree; re-run FLOW-28 after levelchunks merges.

## QA-36 run after merging main (Nov 12 19:3x; run_game.sh, 640x360, no sound)
Logs: `docs/build/playtest-logs/run-2026-11-12d.log` (real), `run-2026-11-12e-relay.log` (wind relay, diagnosis only).
Main has no levelchunks route winds and no motor-id fix yet (requests/playtest.md #1 still open), so nothing changed.
| Row | Result | Why |
|---|---|---|
| CAM-04 | FAIL | Ella never rides (id mismatch). With relay she leaves the band by the top before the far edge. |
| CAM-07 | FAIL | Same bug; currents never live (samples_live=0). CAM-07 also waits on levelchunks route currents. |
| FLOW-25 | FAIL | Drawn wind width 0 vs usable 200; backdrop covers 0 of 9 stages. |
| FLOW-28 | FAIL | 5 enemies alive at handoff (health carries 2 to 2). Re-run after levelchunks. |
| HAZ-16 | FAIL | Not run at 1280x720/1920x1080 (run_game.sh fixes 640x360); guard one-shot is a designer call. |
Nothing left to fix inside the playtest lane. Re-run `-SmokePlaytest` after the Motor fix, a drawn wind field and levelchunks merge.
