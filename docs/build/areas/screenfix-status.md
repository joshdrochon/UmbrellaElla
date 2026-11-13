# screenfix status

## Done (commits d87b0e50, bff67883, main merged after)
- Lighting: every placeholder cube, backdrop panel and art slot uses an unlit flat material (`SetFlatUnlit`), plus a fixed-exposure flat post-process on the play camera. No level light needed.
- Draw order: the play camera renders its own view (no auto ortho planes; the frame was centred on world 0,0). Backdrop sits behind gameplay at every camera position.
- Tests: `UmbrellaElla.ScreenFix.*` (gameplay actors in front of every backdrop layer). `tests/test_frame_check.py`.
- Screen check: `tools/frame_check.py` fails on a mostly-black or mostly-flat frame.
- Proof: `pipeline/art/proof/screenfix/mill-after.png` -> `frame_check: PASS black=0.000 flat=0.746`.

## Left
- Nothing. Post-merge: build exit 0, UmbrellaElla.ScreenFix PASS tests=3 failed=0.

## Smoke shot (frames, path, scene switches) - done
- c9f317b4: -SmokeShot after level ready + N rendered frames (-SmokeShotFrames, default 60); relative path resolves against project dir; -SmokeKeeper, -SmokeEnemy=<family> (workbench).
- Build exit 0, warnings 0. `UmbrellaElla.Smoke` PASS tests=12 failed=0.
- Captures under load (load avg ~25-36, 14-16 fps, worst frame ~1 s): `pipeline/art/proof/screenfix/shot-{plain,SmokeKeeper,SmokeEnemy_Roadwarden}.png`, all `frame_check: PASS` (black=0.000). Log: `SMOKE_SHOT frames=60`, `SMOKE_SCENE keeper=1`, `SMOKE_SCENE enemy=Roadwarden spawned=1`.
- Caveat: -SmokeKeeper frame looks the same as plain (owl stand-in and backdrop already show in L_Graybox); fight state is proven by the log line, not the picture. Enemy stand-in (pink cube) is visible.

## Smoke shot ready wait - done
- The shot counts -SmokeShotFrames only on frames where no shader jobs, no streaming textures, no compiling assets, and Ella's pawn is alive on the Playing screen. Any pending item resets the count. Log: `SMOKE_SHOT_READY at_s=`.
- Test `UmbrellaElla.Smoke.ShotWaitsForShadersTexturesAndPlayer`. Build exit 0, `UmbrellaElla.Smoke` PASS tests=13 failed=0.
- Not run: a new loaded capture (artella's -SmokeShotFrames=3000 re-shoot). module_check shows 2 older problems in SmokeHookSubsystem.h (ParseEnemyFamily name, EnemyTypes include), not from this change.

## module_check fixes (Opus escalation) - done
- `ParseEnemyFamily` renamed `HasEnemyFamilyName` (same signature; family through the out parameter), caller and test updated.
- `SmokeHookSubsystem.h` no longer includes `Enemy/EnemyTypes.h`; forward-declares `enum class EEnemyType : uint8;`. The .cpp and SmokeHookTests.cpp include it.
- Build exit 0 (warnings 0). `UmbrellaElla.Smoke+UmbrellaElla.Feedback` PASS tests=48 failed=0. `module_check: 0 problem(s)`.

## Black ready shot (artella request #4) - done (Opus)
- Cause: artella's checkout merged main but never rebuilt. Its editor module is from Nov 12 22:45, older than the
  ready-wait code, so the run used the old 5 s shot (`SMOKE_SHOT at_s=5.0`, no `SMOKE_SHOT_READY` in its log).
  Nothing is wrong with the world render on current code.
- run_game.sh: every run writes its own log `Saved/Logs/runs/run-<UTC>-<pid>.log` (`-abslog`, path printed as
  `run_game: log=`), prints the SMOKE_SHOT/SMOKE_VIEW lines at exit, runs `frame_check` on a `-SmokeShot`, and refuses
  an editor run when any Source file is newer than the module (`run_game: STALE ...`, exit 3; `RUN_STALE_OK=1` skips).
  Test: `tests/test_run_game.py` (fake editor; log kept, black shot fails, stale module refused).
- `SMOKE_VIEW` at the shot: map, view target, camera, Ella and arena-centre pixel and in-frame flags.
  Test `UmbrellaElla.Smoke.ViewPixelInFrame`. L_Graybox has no ground mesh; the arena centre stands in for it.
- Proof: `pipeline/art/proof/screenfix/ready-shot-1280.png` (RUN_RES=1280x720, -SmokeShotFrames=30):
  `SMOKE_VIEW map=L_Graybox view_target=UmbrellaArena_0 ella_px=256,295 ella_in_frame=1 arena_in_frame=1 w=1280 h=720`,
  `frame_check: PASS black=0.001 flat=0.717`.
- Build exit 0, `UmbrellaElla.Smoke+UmbrellaElla.ScreenFix` PASS tests=17, module_check 0, pipeline_check 0.
- Main does not compile as-is: SettingsMenuWidget.cpp include order (UI lane). Built with a local, reverted fix;
  request in `docs/build/requests/screenfix.md`.
- artella must rebuild (`tools/build/ue_slot.sh tools/ue/build.sh`) before its next capture; run_game.sh now says so.
- Affected checks: `UmbrellaElla.Flow` 30/30 success. Python affected set: 212 tests, 5 failures + 1 error, all in
  `test_gdd_check` and `test_area`; the same 6 fail on a clean origin/main checkout, so not from this change.
  `affected_tests.py --base origin/main` itself takes over 10 min to list on this machine.

## Gate review round 1 (Nov 13) - evidence
- Hotfix for SettingsMenuWidget.cpp include order not on origin/main yet (3e4cf07d: line 1 is still the Slate include). Not merged. The measured lines below used a local, reverted include fix.
- Header: commit=7bd5cb8bc2e2177354d2e67d7fa76b3d6cd41ffd engine=5.8.4 config=Development host=mac run=Standalone
- Build: `build exit: 0  mode=unity  commit=7bd5cb8bc2e2177354d2e67d7fa76b3d6cd41ffd  warnings: 0  log: Saved/Logs/pipeline/build-20261113-061232.log` (copy: ../logs/screenfix-build.log)
- Tests (Saved/Logs/pipeline/test-20261113-064452.log): `TEST COMPLETE. EXIT CODE: 0`; UmbrellaElla.Flow all `{Success}` (30/30). Smoke+ScreenFix PASS tests=17 failed=0 (earlier slice, same code).
- run_game.sh (../logs/screenfix-shot.log): `SMOKE_VIEW map=L_Graybox view_target=UmbrellaArena_0 ... ella_in_frame=1 ... arena_in_frame=1 w=1280 h=720`; `frame_check: PASS ... black=0.001 flat=0.717 top_colour=(88, 80, 80)`.
- Python failures seen on clean main (per lead, fixed by the hotfix): test_gdd_check x4, test_area terminal question, story strixon. I did not capture per-test IDs: the re-run of `unittest tests.test_gdd_check tests.test_area` hit the 10 min limit and was killed.
- affected_tests.py slowness filed in docs/build/requests/screenfix.md.
- Left: merge origin/main when the hotfix lands, then re-paste build and test lines.
