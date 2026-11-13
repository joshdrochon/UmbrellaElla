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
