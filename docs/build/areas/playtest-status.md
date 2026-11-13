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
