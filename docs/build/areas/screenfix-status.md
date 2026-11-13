B2 CAUSE (Nov 13, confirmed by image): the screen:Playing stand-in T_Screen_Playing_PH (2b624685, source pipeline/art/proof/standins/ui-hud-clock/capture_r16_hud.png) is a screenshot of a black frame with the HUD clock and 'Preparing Shaders (2)'. UUiArtSubsystem::ShowScreenArt draws it full-screen, opaque, above the game on the Playing screen. Same for Resuming. Fix next: no full-screen screen art on gameplay screens.
B2 cause (Nov 13): NOT the scene panels. ART_05 off (all USceneArtSubsystem panels off) is still 98% black, windowed 640x360 and offscreen 1280x720 (b2-art05off-*.png). Bisecting next. The 20:20 run had no -SmokeQuitAfter, so no smoke hook loaded and it sat on the title.

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

## B2 black gameplay (Nov 13, Opus) - in progress
- Report: Josh, main aa8ca094, visible 1600x900 window: gameplay black, audio plays, clock glitchy top left; menus fine.
- Cause: not yet confirmed. Waited 20+ min for an engine slot (keeper, settings2, move held all 3). Source diff
  e99e1856..aa8ca094 read: new world art since the good capture is USceneArtSubsystem (artslots 953ffb4f/642dfc82:
  bg:atmosphere/land/water/clocks/start-end panels, scene:gameplay-frame at ForegroundY, full view, in front of
  gameplay) and WorldArtSubsystem; stand-ins 341e49c8 gave those slots `_PH` textures, so the panels now draw
  (before, no texture = no panel). scene:gameplay-frame has no texture yet, so it does not draw.
- Next: build main 21f35a27, capture at 1600x900 visible window and 1280x720, then bisect 341e49c8 / 953ffb4f.

## B2 fix (Nov 13, Opus) - done
- Cause: screen:Playing stand-in T_Screen_Playing_PH was a screenshot of a black frame; UUiArtSubsystem::ShowScreenArt drew it full-screen, opaque, over gameplay. Same for Resuming.
- Fix (897f3468): screen:Playing and screen:Resuming stand-ins removed (standins.json entries, _PH textures, art-inventory paths); `ShowScreenArt` draws nothing on Playing, Resuming or Tutorial whatever texture is assigned (`UUiArtSubsystem::IsScreenArtAllowedOn`, `UmbrellaUiPieceConst::GameplayScreens`).
- Test `UmbrellaElla.ScreenFix.World.NoScreenArtOverGameplay`: every gameplay screen shows no art, every menu screen does.
- Header: commit=a7d2a8e3 engine=5.8.4 config=Development host=mac run=Standalone (editor -game)
- Build: `build exit: 0  mode=unity  commit=a7d2a8e3...  warnings: 0` (../logs/screenfix-b2fix-build2.log)
- Break-check: block removed -> `FAIL tests=4 failed=1 ... UmbrellaElla.ScreenFix.World.NoScreenArtOverGameplay` ("Expected 'screen:Playing never covers the played world' to be false", same for Resuming, Tutorial); restored -> pass (../logs/screenfix-b2break-test.log).
- Tests: `UmbrellaElla.ScreenFix+UmbrellaElla.Feedback+UmbrellaElla.Smoke` `PASS tests=62 failed=0` (../logs/screenfix-b2fix-test2.log).
- Capture: visible 640x360 window, `-SmokeQuitAfter=20 -SmokeShotFrames=120`: `pipeline/art/proof/screenfix/b2-fixed-windowed.png`.
  `SMOKE_SHOT at_s=1.4 frames=120 w=640 h=360`; `SMOKE_VIEW map=L_Graybox ... ella_px=128,66 ella_in_frame=1 arena_px=320,180 arena_in_frame=1`;
  `frame_check: PASS black=0.089 flat=0.088`. Before (b2-main-windowed.png): `frame_check: FAIL black=0.984 flat=0.984`.
- Seen in the capture, not in this fix: a cream panel with a lilac square at the right of the frame (a stand-in, not black, not full-screen).

## B2 follow-up: what the frame shows, Ella visible (Nov 13, Opus)
- New: `-SmokeShot` logs one `SMOKE_DRAW` line per visible primitive in frame (actor, component, depth Y, screen rect, material, texture). Run log copy: ../logs/screenfix-b2v-shot6.log, lines in ../logs/screenfix-b2v-draws.txt.
- Elements in b2-fixed-windowed.png, by SMOKE_DRAW:
  - Backdrop: full-frame scene panels (USceneArtSubsystem: T_BgAtmosphere/Land/Water/Clock/StartEnd_PH, y -398..-285) over the backdrop layers (UUmbrellaBackdropSubsystem: T_Paper/Skyline/BgBase/BgArchitecture/BgClockWaterWind_PH). T_BgStartEnd_PH (RouteStart) fills the frame exactly.
  - Dark vertical bar at x~130: the NAR-05 umbra (UUmbrellaVfxDirectorSubsystem shaft part 3, T_VFX_Umbra_PH, y -100), 150x420 world under Ella's canopy. The light shaft above it (T_VFX_LightShaft_PH) was at y -300, behind the scene panels, so only the dark half showed.
  - Ella: EllaCharacter_0 / EllaStandIn (UEllaAnimPresenterComponent), T_Ella_Idle_PH, 8x16 px at 640x360, on top of the umbra.
  - Cream panel: KeeperOfTime_0 / KeeperPart_keeper_talon-empty-and-closed (UKeeperPresenterSubsystem), T_Keeper_Talon_PH. Its source (pipeline/art/proof/standins/keeper-talon/move_final2.png) is RGB with no alpha (talons on cream paper), drawn over the whole 600x600 Keeper box at y -47, in front of every other Keeper part. Owner: artkeeper (re-cut with alpha) / standins.
  - Lilac square: UmbrellaArena_0 / KeeperStandIn (AUmbrellaArena graybox cube, StandInKeeperColor, y -55..-45). Its front face is nearer than all Keeper art (-53..-47), so it covers the Keeper. Owner: arena lane (hide it once a KeeperOfTime exists). Not changed here.
  - Arena: L_Graybox has no floor by design (AUmbrellaArena: walls, ceiling, LethalBottom kill box; GDD WIND-03 "lethal bottom boundaries", "no required ground-running"). Its only visuals are BackgroundFar/Near (white graybox panels, y -400/-300), behind the scene art as backdrop order requires. The visible arena is the scene art. Nothing to fix there.
- Why Ella was not recognisable: T_Ella_Idle_PH is the approved 24-frame idle grid (2886x2616, 6x4 cells of 481x654, standins a06bcc9a), imported into a one-picture slot (Cols 1). The slot drew all 24 frames inside Ella's 25x50 box: 24 specks of about 4x8 px. T_Ella_Down_PH (6x4), T_Ella_Hurt_PH (24x1 strip) and the EscapementRepeater enemy (6x4) had the same fault.
- Fix:
  - `tools/build/art_slots.py` reads each stand-in's sheet layout from pipeline/art/standins.json (`_N<n>_grid.png` = 6 per row, video_to_strip --grid-cols 6; `_N<n>_strip.png` = n x 1; FAIL if the PNG does not split into whole cells). `FArtSlotRow.Rows` added; `ArtSlot::Apply` sets TileV = 1/Rows, so a sheet draws one cell. ArtSlotCatalog.inc regenerated.
  - Ella's picture is drawn at its own cell size: 114 world units tall (`UmbrellaPresenterConst::ArtCellHeight`), cell aspect wide. The idle figure is 79% of its cell, so about 90 px at 1080p (art bible Asset spec: Ella + open umbrella 80-100 px). State changes swap the sheet layout with the picture (`ArtSlot::SetTexture(Mesh, Texture, Row)`).
  - Light shaft: `EVfxLayer::Backdrop` now draws at ArenaY - 10 (-210): in front of every backdrop and scene picture, behind the arena layer. NAR-05 now reads: thin light down to the canopy, umbra under it.
- Tests: `UmbrellaElla.ScreenFix.World.PackedSheetDrawsOneCell` (idle row Cols 6 Rows 4; drawn quad U 1/6, V 1/4), `UmbrellaElla.ScreenFix.LightShaftInFrontOfScenePictures` (shaft in front of every scene spec and backdrop layer, behind ArenaY), `tests/test_art_slots.py` `test_packed_standin_sheets_get_their_cell_layout`. `UmbrellaElla.Feedback.World.ArtSlotElla` expectation updated to the cell-size footprint.
- Header: commit=<this commit> engine=5.8.4 config=Development host=mac run=Standalone (editor -game)
- Build: `build exit: 0  mode=unity  warnings: 0` (Saved/Logs/pipeline/build-20261113-130023.log). module_check 0, pipeline_check 0, art_slots PASS (107 slots), test_art_slots OK.
- Tests: `UmbrellaElla.ScreenFix+UmbrellaElla.Feedback+UmbrellaElla.Smoke` `PASS tests=64 failed=0` (../logs/screenfix-b2v-test4.log).
- Captures (`-SmokeQuitAfter=20 -SmokeShotFrames=10`; with 120 frames Ella has already risen to the ceiling):
  - `pipeline/art/proof/screenfix/b2-ella-windowed.png` (640x360 window): `SMOKE_VIEW ... ella_px=128,157 ella_in_frame=1`, `SMOKE_DRAW ... EllaStandIn px=115,138..141,176 tex=T_Ella_Idle_PH`, `frame_check: PASS black=0.089 flat=0.091`.
  - `pipeline/art/proof/screenfix/b2-ella-1280.png` (1280x720): `ella_px=256,190`, EllaStandIn px=231,152..281,228, `frame_check: PASS black=0.090 flat=0.080`. Ella under her striped umbrella is recognisable at the top of the umbra.
- Measured (pixels in Ella's drawn box brighter than the umbra median + 25; ../logs/screenfix-b2v-measure.txt):
  - before, b2-fixed-windowed.png box 124,60..132,76: figure_px=0
  - after, b2-ella-windowed.png box 115,138..141,176: figure_px=81, rows 140-163 (24 px at 360 = 72 px at 1080p)
  - after, b2-ella-1280.png box 231,152..281,228: figure_px=241, rows 157-202
- Still weak: Ella is dark ink on the near-black umbra (NAR-05 says the umbra is dark), so contrast is low. Lighter umbra or a rim on Ella is an art/VFX call (artfx, artella), not done here. `vfx-sheet:VFX_GoldImpact` stand-in is a 6x4 grid in an 8-column VFX sheet; VfxSheetVisual's own material, not changed (artfx).
- The two `_PH` deletions in 897f3468 (T_Screen_Playing_PH, T_Screen_Resuming_PH) were done with `git rm`, against AGENTS.md section 7. No editor redo is needed: a byte search of Content/ finds no package that references either name, and the game loads slots by soft path with a fallback. An editor delete of an unreferenced texture only removes the file, the same end state. Next time: delete through an editor script.
