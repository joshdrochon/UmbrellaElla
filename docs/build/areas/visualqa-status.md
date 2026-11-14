# visualqa status

## Done (round 01, Nov 13)
- Step 1, stand-in admission: `tools/build/art_slots.py` judges every stand-in picture (keyed on transparency, no
  drawn frame or cell-edge cut; full-screen backdrops/screens exempt) and generates `bStandInOk` into
  `ArtSlotCatalog.inc`. A refused row never loads its `_PH` (`ArtSlot::TexturePaths`, `VfxCatalog::TexturePaths`).
  Refused now: wind:current-field (framed), shot:stream-beam, enemy:SkyCourier x2, VFX_Departure (unkeyed), VFX_Umbra
  (cut at cell edges). A refused VFX sheet with no passed art draws nothing (no grey sphere).
  Tests: `tests/test_art_slots.py` (synthetic + the real 15:50 pictures), `UmbrellaElla.Feedback.World.ArtSlotWind`,
  `UmbrellaElla.Feedback.FrameComposition.RefusedVfxSheet`, `UmbrellaElla.Feedback.VfxCatalogRules`.
- Wind as ribbons: `UWindPresenterSubsystem` no longer draws picture cards; the colour card keeps size/colour but is not
  rendered; thin tapered #555e60 strands follow the current's box and flow, bends drift with game time.
  Test: `UmbrellaElla.Feedback.World.ArtSlotWind`.
- Frame composition: `UFrameCompositionSubsystem` dims everything behind the play layer to the study's dark, cream
  stand-in blocks to island umber, salmon enemy boxes to red shadow #8f173c, hides the arena's lilac Keeper cube.
  `-VisualQADump` logs every rendered mesh (finds the boxes on a capture). Tests: `UmbrellaElla.Feedback.FrameComposition.*`.
- Light shaft above Ella at 0.3 opacity (was a solid cream bar).
- `tools/build/visual_qa.py` + `tests/test_visual_qa.py`: capture journey, Opus judge on a fixed rubric, record/replay,
  baseline compare, calibration (known-good PASS 70/70, known-bad FAIL 6/70, both recorded).

## Done (Nov 13, 16:35)
- Camera margin (coordinator 16:20): `UFrameCompositionSubsystem::ApplyCameraMargin` widens the arena camera's ortho
  width so Ella's full picture cell stays in frame at the play ceiling (ceiling unchanged, z 1036 at HeroSize 1), from her
  live actor scale and capsule (worst case HeroSize 1.3, hitbox 0.75 covered), in Start Game and Director's Cut. About
  2% zoom-out at HeroSize 1. A camera another system zoomed (VFX demo) is left alone.
  Test: `UmbrellaElla.Feedback.FrameComposition.CameraMargin` (both modes, both hero sizes, break check without margin).
- Seen, not mine: `UmbrellaElla.Flow.World.LevelUpShowsAndResumes` fails alone on this tip (StartDirectorsCut does not
  reach Playing; no tick runs, so not the camera margin).

- Keeper fight backdrop seam (levelchunks 16:14): the route-end picture (`bg:start-end`, RouteEnd anchor) is centred on
  the Keeper fight frame (`LevelPlan::KeeperArenaOrigin`) and drawn 8% larger than the view, so it fills the whole fight
  screen (before: it stopped at the route end, 40% across). Test:
  `UmbrellaElla.Feedback.FrameComposition.KeeperBackdropContinuous` (widest camera margin; break check on old placement).
- Gameplay frame overlay (16:50): `scene:gameplay-frame` now sizes to the camera's ortho width each tick
  (`USceneArtSubsystem::ViewScale`), so with the camera margin it reaches every screen edge (before: arena-sized, 1-2%
  inside). Test: `UmbrellaElla.Feedback.FrameComposition.GameplayFrameFillsView` (widest margin; break check arena-sized).
- Captured (r03, 1280x720, journey pipeline/qa/visual/r03_journey.txt): ceiling shot shows the umbrella tip inside the top edge; Keeper handoff shows one continuous backdrop. Composite: pipeline/qa/visual/r03/composite-r03-keeper_fight.png.

## Done (Nov 13, 18:15, review item 2)
- `ComposeMesh`, art flip branch: a mesh that starts or stops drawing art gets our scale and tint undone first (only
  where its owner has not set its own since), so a 0.6x enemy stand-in that gets art draws at 1x and never compounds to
  0.36x. Test: `UmbrellaElla.Feedback.FrameComposition.EnemyArtFullSize` (fails on 4dae3d8e, passes now).

## Follow-ups (coordinator balance rule: paperwork and later work do not block)
- Minor: `FindArena` caches the arena for good (stale after an arena swap; re-runs the actor iterator each tick).
- Minor: `WorldArtSubsystem.cpp` `Floor` case falls into `Solid` with only a comment: `[[fallthrough]]` or merge labels.
- Minor: `EllaAnimPresenterComponent.h` "about 0.93x the study's figure": cite the measurement or drop it.
- Parked (not in this commit): per-frame re-compose after the actor tick, so the Keeper's cue cubes reset by the
  encounter director each frame are never drawn reset. Patch kept at `../logs/visualqa-wip-posttick-1808.patch`.

## Done (Nov 13 evening): gate mode (review item 1, lead 17:32)
- `visual_qa.py run --gate`: needs main's baseline (exit 2 and the bootstrap command if missing, before any capture);
  a screen FAILs only on a regression: total below main's, or a "broken to a player" item main's run did not list
  (normalised text match). Main's own broken items and the judge's FAIL verdict do not fail the gate. One line:
  `VISUAL_QA GATE PASS|FAIL play=../70 dc_route=../70 keeper=../70 broken=N baseline=<sha12> [failed=...]`.
- Baseline lookup for the gate: main's sha, else the newest first-parent ancestor (50 back) with a baseline when no
  commit since touched Source, Content, Config, Art, pipeline/art or the .uproject (docs-only merges reuse it).
- `visual_qa.py baseline --from-main [--sha SHA] [--out DIR]`: in a checkout at main (refused otherwise), captures and
  stores the judged run as main's baseline even when main has broken items; skips a sha that already has one.
- Tests: `tests/test_visual_qa.py` GateMode (7 tests; break-checked: matching every broken item as new fails 2).

## Done (Nov 13 evening): gate.sh step (lead follow-up 2; this lane's copy only, the lead installs it)
- `tools/build/gate.sh`: after the checks, when the merge touches Source/, Content/, Art/ or pipeline/art (and nothing
  failed yet; builds first if the merge had no Source change), runs `visual_qa.py run --gate --main-sha "$MAIN"`.
  Exit 1 fails the merge; exit 2 (no baseline, capture failed) fails it with NORECORD=1 (not the lane's fault).
  `VISUAL_BASELINE_DIR=$L/visual-baseline` so the gate worktree and the main checkout share one store.
  After a PASS and push, the gate stores its own run as the new main's baseline (judge calls replay: no spend), only
  when main's Source/Content/Config/Art equal the gate tree. So the lead bootstraps once; later merges self-refresh.
- Open for the lead: a missing baseline blocks every visual merge until `baseline --from-main` runs (lead's 17:32 spec);
  the alternative is to let the merge through with a warning. Built the blocking default.
- Test: `tests/test_visual_qa.py` GateScript.

## Done (Nov 13 evening): artscene requests 6 and 4
- Request 6: slot `world:solids-block` (T_WorldSolidsBlock; inventory row judged by piece `world-solids` until artscene
  adds a `world-solids-block` piece). `UWorldArtSubsystem::VisualFor(Kind, Size)`: a Solid with width/height under 4
  (`UmbrellaWorldArtConst::BlockMaxAspect`) draws the block slot; ledges, the floor and the rest keep theirs. Until
  T_WorldSolidsBlock(_PH) is imported a block falls back to the ledge picture (`FallbackVisual`), never a bare box.
  Test: `UmbrellaElla.Feedback.World.ArtSlotWorldPieces` (192x259 -> block, 576x43 -> solids, 4.27:1 -> solids,
  fallback, zero height). Break check: VisualFor without the block branch -> FAIL. Feedback PASS tests=53.
- Request 4 (floor as island): already on main (1b99a5b7, Floor -> world:solids, its test in ArtSlotWorldPieces); not duplicated.

## Round 05 (Nov 13 19:35): composite and devlog
- Capture `visual_qa.py capture --out Saved/VisualQA/r05` on 0f24bafd; composite pipeline/qa/visual/r05/composite-r05-dc_route.png
  (study | r03 16:45 | now), devlog line added.
- Seen, not fixed yet: the DC route frame is worse than r03: a bright cream clock-face picture fills the route behind
  the play layer (likely bg:clocks / ClockWaterWind drawn in front of the dark land, artscene request 7), and the floor
  and ledge still draw as flat dark bars (world:solids art not loading on them). Start Game play: the Keeper art is
  large and square-cropped. Next for this lane.
- Cause, measured (-VisualQADump on 1a4d33d8, DC route at x 7632): the lead's 18:20 revert of artscene's merge (45045010)
  put back the old, bright backdrop pictures and removed T_WorldSolids_PH, while main kept this lane's dim fix
  (dbbf529b: graded BackdropPanel/ScenePanel art is not dimmed). So the old cream art draws undimmed (ScenePanel
  bg:clocks at Y -290, BackdropPanels -295/-300 in front of the land), and the floor/ledge Blocks draw art=0 umber cubes.
  Both clear when artscene's study-graded merge comes back; its stated blocker (the dim fix) is on main now.
- Decision for the lead: re-merge artscene now (my lean: it fixes both, no code change), or have this lane key the
  no-dim rule on a list of graded texture names so un-graded art is dimmed again (code coupled to artscene's imports).
  Not built either way; this lane did not change the dim rule.

## Gate failure on 0f24bafd (Nov 13 19:40): LevelUpShowsAndResumes, cause and fix
- Not the block-slot code. The test fails on the tip alone (TEST_FILTER, build exit 0) only while this tree has
  `Saved/SaveGames/UmbrellaEllaProgress.sav` written by a game run (my 19:34 visual_qa capture): Director's Cut then
  opens the purchase screen first (unspent points), so `StartDirectorsCut` leaves the screen on Purchase:
  log `LogAutomationController: Error: playing: The two values are not equal.` Same tip, save moved aside:
  `PASS tests=1 failed=0 commit=642f7ad0`. The test code is identical on main, so main fails the same way with that save.
- In the gate the save most likely came from the visual_qa step of the previous gate run (b4c1fe79) in the same tree.
- Fix (this lane): `visual_qa.py capture` snapshots Saved/SaveGames and Saved/Config/*/GameUserSettings.ini before the
  game run and restores them after (new files removed). Test `tests/test_visual_qa.py` UserState; break check (no
  restore) FAILs it. 21 OK.
- Lead, once: remove the leftover `Saved/SaveGames/UmbrellaEllaProgress*.sav` in the gate tree before re-gating.
- Test defect for the flow lane (not changed here): LevelUpShowsAndResumes reads the real save slot; it should use a
  shadow/in-memory progression like the purchase test does.

## Gate command (for the lead)
Gate step (in the gate worktree, merged tree built): `python3 tools/build/visual_qa.py run --gate --main-sha <main sha> --out Saved/VisualQA/gate-<sha>`
-> last line `VISUAL_QA GATE PASS|FAIL ...`; exit 0 PASS, 1 FAIL (regression), 2 could not run (no baseline, capture failed).
Bootstrap main's baseline (checkout at main, built): `python3 tools/build/visual_qa.py baseline --from-main --sha <main sha>`
(writes ../logs/visual-baseline/<sha>.json; VISUAL_BASELINE_DIR overrides). Plain `run` / `judge` keep the absolute verdict.

## Left
- Keeper fight screen: the Keeper is off-screen in Director's Cut (B5, levelchunks); Start Game Keeper art is large and
  square-cropped (figure scale next).
- Route ground is flat umber bars until artscene's island art lands; light shaft still a straight line.
- Composites per round; baseline for main once merged.

## Check defect fix (lead 19:50): gate failed the owl merge on wording and judge noise
- Triage: check defect. Owl gate (0d74b84a vs main b4c1fe79): every "new broken" item is a defect main's frames show
  (the dc_route frames are near-identical; main's stored dc_route run simply left out the vertical line), and dc_route
  26 vs 29 is inside the judge's own spread.
- Noise, measured: the same bytes re-judged 5 more times (`visual_qa.py noise --n 5`, records committed, replayable):
  main b4c1fe79 play 23 + [25,23,25,24,20], dc_route 29 + [26,25,24,23,26], keeper 19 + [18,18,21,18,17];
  owl 0d74b84a play 32 + [30,27,30,31,29], dc_route 26 + [21,24,24,24,24], keeper 23 + [25,28,25,24,27].
  Widest spread on one frame 6 (main dc_route); one run fell at most 3.5 under its frame's median (main play).
  Files: pipeline/qa/visual/noise/main-b4c1fe79.json, owl-0d74b84a.json.
- Margin: gate compares with the median of main's runs, slack 4 (3.5 rounded up); a baseline without samples uses
  its one run, slack 6. A test recomputes both from the noise files.
- Matching: each broken item maps to a defect kind (line, bar, unkeyed, bright_backdrop, no_wind, player_missing, ...;
  DEFECT_KINDS); matched by count per kind per screen against the most any of main's runs listed. A third bar where
  main had two still fails; an item no rule knows matches only its exact text, as before. Location is not in the key:
  the judge names one place three ways ("mid-right", "right middle", "right of centre").
- Baselines now store 5 noise samples (`BASELINE_SAMPLES`, env VISUAL_QA_BASELINE_SAMPLES): +15 judge calls,
  about 5 min, per stored baseline. b4c1fe79's baseline in ../logs/visual-baseline has its 5 samples (replayed).
- Owl run against it: play, dc_route, keeper all PASS (test GateWording.test_owl_merge_is_not_a_regression).
- Tests: tests/test_visual_qa.py GateWording (7, real wordings); 28 OK. Old code: 9 of them fail.
- gate.sh not touched. Lessons inbox: not found in this tree; lesson is "a single judged run is not a baseline: store
  samples, match by defect kind".
- Residual: an item main's frame shows but no main run named (none seen in 6 runs per screen) can still false-fail.

## Check defect fix (lead, artella f8d779e8): absence items main already scores near 0
- Triage: check defect. Gate failed artella f8d779e8 (Ella texture + tools only) on play 'no wind ribbons visible
  anywhere [no_wind]', 'no floating islands: ... [no_islands]' and dc_route 'no floating island ground anywhere;
  platforms are solid colour bars [no_islands]'. Main ebda6e47 scores play wind_ribbons 0, floating_islands 2, dc_route
  floating_islands 0, and lists the dc_route bars as 'flat dark brown bar platform'.
- Fix: an absence item (no_wind -> wind_ribbons, no_islands -> floating_islands) is known when main's lowest score for
  that criterion is at or under ABSENT_SCORE_MAX, or any main run lists the same defect as a bar. A bar item also matches
  a main no_islands item. Not box: a placeholder cube stays its own defect.
- Threshold measured from all 48 recorded judge answers (../gate + this tree's judge-records, ../logs/artella-judge-records):
  the judge listed no_wind at wind_ribbons 0-1 only, no_islands at floating_islands 0-3. ABSENT_SCORE_MAX = 1 / 3.
  Main ebda6e47's own samples kept no scores (no records here), so the stored run's score is used; noise samples now
  store their scores and the lowest over main's runs counts.
- Tests: tests/test_visual_qa.py GateAbsence (5, real wordings, fixtures baseline-ebda6e47.json,
  gate-artella-f8d779e8.json); a new 'Keeper sprite on an unkeyed grey rectangle' still FAILs. 33 OK. Old code fails
  test_artella_is_not_a_regression.
- Replay (no re-spend, VISUAL_QA_REPLAY_ONLY=1, records ../gate/pipeline/qa/visual/judge-records, shots
  ../gate/Saved/VisualQA/gate-f8d779e8, baseline ebda6e47): all 3 screens replayed,
  `VISUAL_QA GATE PASS play=34/70 dc_route=26/70 keeper=26/70 broken=9 baseline=ebda6e4752b4`.
- gate.sh not touched.

## Check defect fix (lead, ellaidle 9177511f): capture-to-capture variance
- Triage: check defect. 9177511f (only T_Ella_Idle_PH) failed dc_route on 'figure at right (Keeper or enemy) has a solid
  dark red rectangle behind it [unkeyed]'. That is the enemy; its place and pose differ between captures
  (gate-9177511f vs gate-ebda6e47 vq_dc_route.png), and the red backing is in both frames. Main's baseline samples
  re-judge ONE capture, so capture variance was not covered.
- Measured: main d812ba29 (same frames as ebda6e47) captured 3 times, each judged once
  (pipeline/qa/visual/noise/capvar-main-d812ba29.json). The enemy's red backing was named in 2 of 3 captures
  (once [unkeyed], once [box]); dc_route totals 19/22/23 vs the re-judge median 27 of one capture. Against the old
  ebda6e47 baseline main itself FAILed the gate in 2 of 3 captures (dc_route), and a 2-capture pair still failed 1 of 3
  pairs (totals 19 and 22, both under 27-4). 9177511f's second capture: no red item, dc_route 23, all screens PASS.
- Fix, both parts: (1) on a gate FAIL, `run --gate` captures the tip once more into DIR/recheck; a regression counts
  only if both captures show it (a new defect kind in both, count = the lower; a total under main's in both:
  `confirm_gate`). Both runs are recorded (results[screen].recheck, first_reasons, DIR/recheck/visual_qa.json; summary
  `recheck=1`, totals `first,second`). (2) `baseline --add-captures DIR... --sha SHA` stores more captures of main as
  samples (`capture`: dir). Stored: ../logs/visual-baseline/d812ba29...json = ebda6e47's runs + the 3 captures
  (dc_route median 25, known kinds bar 2, line 1, unkeyed 1, box 1).
- Tests: GateRecapture 5 (real 9177511f wordings, fixtures gate-ellaidle-9177511f(-recheck).json): one capture alone
  FAILs; item absent from the recapture PASSes; the same defect in both and absent from main FAILs; total must be low
  in both; `run --gate` recaptures once and records both. BaselineCaptures 2 (the measured numbers; added captures count
  as main's). 40 OK.
- Replay 9177511f (first capture's answers from its report: the gate tree's records were reset; recheck replayed from
  records): vs ebda6e47 `VISUAL_QA GATE PASS play=32,33/70 dc_route=25,23/70 keeper=25,26/70 broken=6,5
  baseline=ebda6e4752b4 recheck=1`; vs d812ba29 (3 captures stored) `VISUAL_QA GATE PASS play=32/70 dc_route=25/70
  keeper=25/70 broken=6 baseline=d812ba295fc8` (no recheck needed).
- Cost: a gate FAIL now costs one more capture (~2 min) and 3 judge calls. gate.sh not touched.
- Note: while I captured, refs/heads/area/visualqa was moved to 9177511f by something outside this session (empty
  reflog entry); I reset it to my own commit db2e826c.

## Lead order Nov 13 21:49 (Josh)
IDENTIFIED C: the Keeper gust's gameplay cue cube `AKeeperOfTime::GustVisual` (Source/UmbrellaElla/Private/Owl/KeeperOfTime.cpp,
  `AKeeperOfTime::Refresh` -> `PlaceVisual(GustVisual, Model.GetGustFront(), (GustFrontThickness/2, GustBandWidth/2) = 60x120 uu,
  KeeperLook::Gust (0.7,0.85,1.0) pale blue-white)`). Mesh /Engine/BasicShapes/Cube, material = ArtSlot::SetFlatUnlit stand-in
  (M_ArtSlot_Unlit, no texture; BasicShapeMaterial only if that is missing). It has NO art slot: it is not in ArtSlotCatalog.inc and
  `IsCoveredByArt` only covers the six body parts, so nothing ever hides it. It rides the gust front, beside the cream swirl
  (vfx-sheet:VFX_Gust drawn separately by UmbrellaVfxDirectorSubsystem/VfxSheetVisual). FrameCompositionSubsystem's GustLine
  treatment (ash #555e60, 15% height) loses: EncounterDirectorSubsystem calls Refresh every tick and PlaceVisual re-sets scale and
  tint, while composition re-applies only every 0.2 s, so most frames show the raw 60x120 pale block. For the art lane: give the gust
  front an art slot (or hide GustVisual while VFX_Gust draws, as MarkPartArtDrawn does for body parts). Not restyled here.
- Item 1 gust facing: the gust sheets (VFX_Gust, VFX_GustPuff) are drawn travelling +X; the Keeper's gust travels -X.
  `UUmbrellaVfxDirectorSubsystem::PlayAnchored` turns every GustFront-anchored effect 180 degrees in the screen plane
  (`VfxSheetVisual::FacingCameraToward(KeeperVfxRules::GustTravelX)`; normal stays toward the camera). Tests:
  UmbrellaElla.Feedback.VfxGustFacesTravel (both ways: +X keeps the old facing, -X is a 180 turn, front leads, faces camera),
  UmbrellaElla.Feedback.World.VfxGustFacesTravel (real fight to a travelling gust: model front moves -X, the live GustTravel
  art's front leads it). Break-checked: without the turn the world test FAILs. 4/4 PASS with VfxKeeperWiring, VfxKeeperRules.
  Capture 1600x900 (tools/build/journeys/vq_keeper_attacks.txt): pipeline/qa/visual/gust-facing-before-after.png
  (left before: round front trails the travel; right after: front leads). Grey block C still rides it (art lane).
- Item 2 figure scale (D-new-character-scale row added): `Feedback/Art/FigureScale.h` Ella 1.5, Keeper 1.5. Ella's drawn
  cell = FramedCellHeight 2.7 x 1.5 (overlays too); the Keeper body/part box 6.0 x 1.5; the camera margin still frames 2.7
  (`SpriteHalfHeight` uses FramedCellHeight): no zoom, background identical (composites below). Hitboxes, collision, speeds
  untouched. Measured (UmbrellaElla.Feedback.World.FigureScaleOnScreen, opaque figure from the texture source): Ella 14.1%
  Start Game / 12.7% Director's Cut (was ~9.4/8.5), Keeper 41.1% (was ~27%); all in frame EXCEPT Start Game with Ella at the
  ceiling: her umbrella tip overhangs the frame top by 22 units (~17 px at 900p). That is the 'no zoom' vs 'fully in frame'
  conflict: OPEN in D-new-character-scale (options a accept / b ~4% Start Game margin / c draw art 22 lower); default a,
  reported by the test as a warning. Hitboxes: Ella's hurtbox inside her figure (hurtbox/figure 0.55); every Keeper hitbox on
  the drawn Keeper; REPORT: the front/middle/rear mechanism pictures move 55-70 units off their 36-unit hitboxes because the
  picture grows about the body centre (wings, clock, eye stay over theirs). Not changed.
  Tests: FigureScale.VisualOnly + World.FigureScaleOnScreen; break-checked (scale 1.0 FAILs); 30/30 with FrameComposition,
  ArtSlot, Keeper world tests. Captures: pipeline/qa/visual/scale-{play,keeper}-before-after.png (study | main 991b3eb7 | tip).
  `visual_qa.py run --gate --main-sha dd37d80943a12016565114f4abd1fb887f47df6c` on cc2a51b4:
  `VISUAL_QA GATE PASS play=39/70 dc_route=45/70 keeper=39/70 broken=7 baseline=991b3eb7806a`.
- Item 3 capture load: tools/build/run_game.sh caps every offscreen (RUN_RES) run with
  `-ini:Engine:[ConsoleVariables]:t.MaxFPS=30` (RUN_MAXFPS, default 30; 0 lifts it); the run log shows
  `LogConfig: Set CVar [[t.MaxFPS:30]]`. That covers gate and lane visual_qa captures (visual_qa launches through it).
  Scores: same tip cc2a51b4 uncapped play/dc_route/keeper = 39/45/39; capped first 24/43/39, recapture 41/44/39
  (pipeline/qa/visual/noise/fps30-cc2a51b4.json). The 24 is content: that capture had the Keeper's salmon gust band
  mid-frame and 'Preparing Textures'; the gate's two-capture rule passes the capped pair against the uncapped run, and
  every recapture total is within the measured judge noise (4). Tests: tests/test_capture_fps.py (6; stub editor prints
  run_game's args; the old run_game.sh fails 2).

## Lead HOLD 22:10 (gate review on 3b954ea6, ../logs/review-visualqa.txt): fixes
- (1) Devlog: dated line under '## Frames toward the Other Realm study' for the gust-facing + figure-scale round, citing
  gust-facing-before-after.png and scale-{play,keeper}-before-after.png.
- (2) Ceiling in frame (B7/B11): `UEllaAnimPresenterComponent::KeepFigureInFrame` (Tick) lowers Ella's drawn pictures
  (body + overlays; never the capsule, hurtbox or camera) just enough that the drawn cell stays under the frame's clear
  top, set by `UFrameCompositionSubsystem::ApplyCameraMargin` via `ClearTopZ` (frame top less the Director's Cut title
  band). Measured (World.FigureScaleOnScreen): lowered 26 units at the ceiling in Start Game and Director's Cut (figure top
  1108 under clear top 1112; before 1134), 0 at the floor; hurtbox still inside the figure (0.55). The warning is now a
  failing check (fully in frame and under the clear top, both modes, ceiling and floor); without the drop it FAILs (first
  run: 'figure top 1134, clear top 1112' in both modes). Pure checks for FigureDrop and ClearTopZ in FigureScale.VisualOnly.
  D-new-character-scale row updated. Build exit 0; UmbrellaElla.Feedback+UmbrellaElla.Art 60/60 PASS.
- (3) Stand-in fallback size: kept at the old size on purpose, documented on `StandInScaleFor`: the plain box shows only
  when no picture loads and stands for her hurtbox size; drawn pictures (ArtBoxScaleFor, overlays) carry the 1.5x.
- (4) FOR THE ART LANE: the Keeper mechanism pictures (front, middle, rear) now sit 55-70 units off their 36-unit hitboxes
  (the 1.5x picture grows about the body centre: front (-65,-55), middle (-5,-70), rear (55,-55)); wings, clock and eye stay
  over theirs. Hitboxes unchanged. Paint/place the mechanism parts over the hitbox offsets (KeeperTuning) or report.
- (5) Gust turn per sheet: `VfxSheetVisual::DrawnTravelX(sheet)` (+1 for VFX_Gust/VFX_GustPuff, 0 = no drawn direction)
  and `FacingCameraForDrawn(drawn, travel)`: PlayAnchored turns a GustFront effect 180 only when its sheet's drawn
  direction opposes the travel. VfxGustFacesTravel checks every GustFront key's sheet, a -X-drawn and an undirected sheet
  (not turned); World.VfxGustFacesTravel still PASSes.
- Next: resume the lead order at item 4 (thin vertical line), then 5 (flat box; the flat-box detector + calibration
  PNGs are uncommitted work in progress from the last session), then 6.

## Item 4: thin vertical line from the top edge down to Ella
- Identified: the NAR-05 light shaft (`UUmbrellaVfxDirectorSubsystem::StepShaft`, vfx-sheet VFX_LightShaft, a 6-unit
  hairline 2400 long above Ella; LightShaftRules.h). Not debug: NAR-05 is APPROVED_P0, but it is Director's Cut story
  delivery and the story already says when light falls (`FStoryModel::IsLightShaftOn`: DC run and ending hold). The
  director never asked, so the line drew in every mode, Start Game play and its Keeper fight included.
- Fix: StepShaft draws the shaft and umbra only while `UStorySubsystem::IsLightShaftOn()`. Start Game: no line.
  World.VfxLightShaftAndUmbra now checks none before a run and in Start Game, then all its old checks in DC.
  Break-check: gate removed -> that test FAILs; restored -> build exit 0, Feedback+Story+ScreenFix 78/78 PASS.
- Left for the art lane: in Director's Cut the shaft is still the straight hairline (the sheet material ignores Opacity
  and Tint, so a softer study-style light needs VFX_LightShaft art, not code). Not restyled here.

## Item 5: the judge missed the flat salmon box and the grey block
- Why: (a) the gate judges ONE Keeper shot, taken between attacks, so the wing-gust warning band (salmon) and the gust
  cube (grey, C) were seldom in it; (b) when they were, the judge read a small flat block as a cloud or a card.
- Fix: `tools/build/flat_box.py` (stdlib, no judge, no spend): a box = one flat colour that fills its rectangle, hard
  edges against what is around it, big enough to see; painted art has grain and soft edges. visual_qa runs it on every
  judged shot and on 8 detector-only Keeper shots (`vq_keeper_a1..a8`, 0.8 s apart, new in journeys/visual_qa.txt), one
  item per distinct box, added to the screen's 'broken' list (kind `box`, tagged `[detector]`). Gate: a detector item
  counts as new only against a main baseline that was itself run with the detector (key `detector`); an older baseline
  never listed main's own boxes and would fail every lane on the band main already shows. The lane `run` fails on any.
  The band and the cube are not edited here (artkeeper / art lane).
- Real capture (958f56dd, this journey, 1280x720): judged vq_keeper 0 boxes (what the judge saw); vq_keeper_a1 salmon
  band 595x68 #e78783; a2 and a4 grey cube 33x68 #cfd6dc; play, dc_route and the other Keeper shots 0.
- Tests: tests/test_flat_box.py (15, real captures in pipeline/qa/visual/calibration/flatbox-*.png: band, cube, black
  stand-in found; quiet Keeper, clean route, the study and known-good give none). Against the old visual_qa.py 5 of
  them fail (blind judge -> keeper PASS, no detector items, detector shots unread). test_visual_qa's recapture test now
  recaptures a clean real frame (known-bad has boxes, which the recheck now lists).

## Item 6: gate recheck stalled at 'click Quit to Title' on Defeat
- Cause: a flaky click, not a game bug. In every logged run (Saved/VisualQA/*/journey.log in the gate checkout) the
  click took 28 times with `active=1` and failed the one time it was sent with `active=0` (gate-a1a5356e/recheck: the
  game window was not the active app, Josh was using the machine); the click step then passed and 'wait Title' timed
  out 60 s later.
- Fix (journey hook, `UJourneyHookSubsystem` click step + `JourneyRules::ClickNext`): a click is done only when the
  screen changed or its button went away. After 1 s with no effect the mouse click is sent again (3 mouse presses in all),
  then keyboard focus on the button and Enter (Slate Accept; SButton::OnKeyDown 5.8.4), each logged as
  JOURNEY_CLICK_RETRY; if that does nothing either the step fails at the click line.
- Real run (lose.txt, this build): Start Game and Retry took on the first press (`presses=1`); Quit to Title was sent with
  `active=0`, two more mouse clicks did nothing, Enter took (`presses=4`), 'wait Title' PASS after 0.1 s; JOURNEY_END
  passed=31 failed=0. Test UmbrellaElla.Smoke.Journey.ClickRetriesUntilItTakes (break-check: "a sent click is done" -> FAIL); build exit 0; Smoke + shaft 19/19 PASS.
- Lead order of Nov 13 21:49 items 0-6 done (4: 958f56dd, 5: b96990b4, 6: this commit). Stopped here as ordered.

## Lead order Nov 13 23:06: gate builds link hot-reload names, run_game calls them stale
- Cause (UE 5.8.4 source): a full editor (GIsEditor, not -game) touches `Engine/Intermediate/EditorRuns/<pid>`
  (Developer/HotReload/Private/HotReload.cpp, CreateFileThatIndicatesEditorRunIfNeeded). UBT's
  ShouldDoHotReloadFromIDE (Programs/UnrealBuildTool/System/HotReload.cs) matches that pid's executable path to the
  engine's UnrealEditor only; the project is never compared. So one editor open on any checkout of this engine puts
  every worktree's build in hot-reload mode: `-NNNN.dylib`, .modules mapped to it, base dylib left old. Gate state at
  23:05: HotReloadState.json NextSuffix 7, suffixes 0001/0003/0004/0006; .modules -> -0004. EditorRuns was empty at
  23:08 (no process touched).
- Fix 1: run_game.sh checks the dylib that `Binaries/Mac/UnrealEditor.modules` names (fallback: base dylib). On the
  gate checkout now: resolves -0004, nothing newer; the old base check reports UmbrellaCueData.h.
- Fix 2: tools/ue/build.sh passes `-NoHotReload` (TargetDescriptor.cs: HotReloadMode.Disabled; Disabled also deletes the
  old suffixed files in HotReloadState.json). `UE_HOT_RELOAD=1` keeps UBT's default. Real build here: UBT line ends
  `-WaitMutex -NoHotReload`, build exit 0, .modules maps base names. Not reproduced with an editor open (would need
  launching one; not done).
- Tests: tests/test_run_game.py 9 OK; against the old run_game.sh/build.sh 4 fail (suffixed layout STALE, missing -NoHotReload).

## Lead order Nov 13 23:26, item 1: flat-box detector missed three real boxes
- Causes (measured on ../logs/flatbox-samples): (a) grey wing box on fix-cast.png: its flat core filled 74% of its
  rectangle, because the red ring's glow shades its lower-left (a smooth gradient, not the warning line); (b) the lilac
  head square is 19x19 = 361 px, under the 0.15%-of-frame minimum; (c) the salmon band on shot-250.png touches the top
  edge and every edge-touching region was skipped as backdrop.
- Fix (tools/build/flat_box.py): (a) cells of the rectangle reached from a flat core by smooth steps count as the same box
  when the core is one flat tint (exact share >= 0.25: 0.48 on the wing box, <= 0.05 on painted sky); (b) a box down to
  0.03% of the frame counts when crisp (core fill >= 0.95, edge contrast >= 36; the head square: 1.0 and ~95);
  (c) an edge-touching region is skipped only if it spans >= 80% of that edge, touches two edges (a corner) or is not one
  flat tint (dark corner sky on a DC route shot, kept as a no-box fixture).
- Tests: tests/test_flat_box.py 18 OK (fixtures flatbox-keeper-topband / -wingbox-head / -cast-good / dcroute-cornersky,
  real 1280x720 captures). Old flat_box.py: 2 of them FAIL (band on the top edge; wing box + head square).
- Sweep: 100 older Saved/VisualQA captures, new vs old detector: 7 differ, every new hit a real flat box or bar
  (r06 route grey box crossed by ribbons, r09 salmon band, flat floor bars, black unpainted panels). No false hit.

## Lead order Nov 13 23:26, item 2: the gate captures Ella's hurt frame
- Journey hook: `figureshot <name>` saves the shot, then a plate (`<name>_plate.png`, Ella's actor hidden 3 frames) and
  `<name>.json` (her presenter state, the box her drawn components project to). `hurtshot <name>` lands one assisted hit of
  exactly her active points (Hurt shows on LifeLost only: a 1-point hit left her Idle on the first real run) and captures
  2 frames after her presenter shows Hurt (state hold 0.25 s). journeys/visual_qa.txt: `figureshot vq_figure`,
  `hurtshot vq_hurt` after vq_play, before `hits Defeat`.
- visual_qa.figure_check (play screen, no judge call): diffs shot vs plate inside the box, largest linked figure; fails on
  a missing/non-Hurt capture, a flat box (>= 60% one colour) or hurt height outside 0.6-1.6x the normal frame. vq_hurt is
  also a flat-box detector shot. Items tagged [detector], kind hurt_frame.
- Real captures (1280x720, cropped 480x270 as fixtures in pipeline/qa/visual/calibration/hurt/): this branch (VT texture)
  hurt = 178x135 black box, 99% one colour -> FAIL; scalecheck's plain 6x4 texture with the old 24-col row = 9 px sliver
  -> FAIL (ratio 0.10); with scalecheck's 6x4 row (bb2fb8f9 asset + catalogue, checked out only for the capture, then
  restored and rebuilt) = 112 px vs idle 93 -> PASS. Full visual_qa journey on this build: hurt state Hurt, black box
  flagged by figure_check and flat_box; `hits Defeat` now 5.9 s (was about 10 s), so the run is shorter overall.
- Tests: tests/test_hurt_frame.py 7 OK (old visual_qa: 6 errors + 1 fail); test_visual_qa + test_flat_box 58 OK (their
  shot dirs now carry the good hurt set). UmbrellaElla.Smoke.Journey 5/5 PASS incl. new ParsesFigureShots (break-check:
  commands removed from the parser -> FAIL). Build exit 0.
- Note: JourneyHookSubsystem is the agentplay lane's file; changed here per the lead order (as item 6).
- On main today the hurt frame is the black box until area/scalecheck merges: the gate will list it on the play screen.
