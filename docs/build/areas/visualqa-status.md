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
- Review item 3: a composite per screen under `pipeline/qa/visual/` for this round, and a dated line in
  `pipeline/submission/devlog.md` under "## Frames toward the Other Realm study"; `composed-01.png`.
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
