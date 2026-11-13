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
