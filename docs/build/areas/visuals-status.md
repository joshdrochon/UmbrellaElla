# visuals status

## Done
- VFX-03, VFX-04, VFX-05: `UUmbrellaVfxSubsystem` (Feedback/Vfx). Bus events -> named effect -> short sphere stand-in at the
  source actor, on the VFX depth layer, no collision. Each family behind its own flag.
  Tests: `UmbrellaElla.Feedback.VfxMapping`, `UmbrellaElla.Feedback.World.VfxStandIn` (PASS, 6/6 Feedback tests).
- BG-05: `UUmbrellaBackdropSubsystem` builds non-colliding stand-in panels at BackgroundFarY/NearY (flag-gated).
  Test: `UmbrellaElla.Feedback.World.BackdropLayers`. Full suite PASS 31/31, module_check 0, manifest_check 0.
- ANIM-06 (stand-in only): `UKeeperPresenterSubsystem` attaches a non-colliding stand-in box to each spawned Keeper, flag-gated.
  Test: `UmbrellaElla.Feedback.World.KeeperStandIn` (Feedback suite PASS 8/8, module_check 0).
- Existing: Ella presenter stand-in + state mapping (ART-03).

## Left
- Flipbook/Niagara art swap for VFX; keeper/enemy/shot presenters; BG-02..04, BG-06 art (looping scroll, clock/water/wind assembly); generated art with
  provenance rows and art_ref_check scores (no keys/art generation run yet); ANIM/ART coverage docs items.
- Art verdicts: none shipped. Generation needs API keys that only the arena shell may source (worker rules), so the
  art_loop could not run. Every piece stays a stand-in/_PH; no art_loop pass record exists for any piece (not attempted).
- Still open: enemy and shot presenters, BG-02..04/06 art, VFX-06..11 (layers, lighting, performance), ANIM/ART coverage items.

## Nov 12 update (after main merge)
- Art generation works without keys: `tools/assetgen.py image --character owl` renders with Blender 5.2.1. One Keeper still
  (`Art/Source/Keeper/Raw/keeper_idle_PH.png`, provenance row added) stays a tracked `_PH` placeholder: no art_loop pass record,
  no blind critic session run, `art_ref_check` has no references assigned to card ANIM-06 in references.json. Nothing shipped under Art/ outside Source/.
- Shots already have a Visual mesh (AUmbrellaProjectile), so a shot stand-in presenter adds nothing.
- Still open: enemy presenter, BG-02..04/06 looping art, VFX-06..11, ANIM/ART coverage, art_loop passes (needs a separate critic session).

## Nov 12 slice 2 (after enemies merge)
Done (full suite PASS 108/108, module_check 0, manifest_check 0):
- BG-02, BG-03, BG-04, BG-06 (+BG-05): `UUmbrellaBackdropSubsystem` now builds five non-colliding looping parallax stand-in layers
  (Sky, FarLand, Base, NearArchitecture, ClockWaterWind), each behind its own flag, scrolled to the camera X (`LoopOffset` wraps
  inside `LoopPeriod`, so it never runs out). Tests: `UmbrellaElla.Feedback.BackdropLoop`, `.World.BackdropLayers`.
- VFX-02, VFX-06..11: effect specs (render layer per effect, readable life, telegraph life follows the event's warning time),
  point-light stand-in for lit effects, concurrent cap + flash gap + `SetReducedFlash` (the settings lane wires the toggle),
  event-frame sync. Tests: `UmbrellaElla.Feedback.VfxRules`, `.World.VfxLayersLightLimits`, `.World.VfxStandIn`.
- ANIM-08, ART-10 (stand-in): `UEnemyPresenterSubsystem` shows a no-collision stand-in on each `AUmbrellaEnemy`, follows its state
  through getters, hides it when defeated/withdrawn, and names the flipbook key per (type, gender, state). Tests:
  `UmbrellaElla.Feedback.EnemyPresenterCoverage`, `.World.EnemyStandIn` (hitbox untouched).
- ANIM-03/ART coverage: `UmbrellaElla.Feedback.PresenterStateCoverage` (every Ella state has a distinct shape and is reachable
  from an event), `.World.ArtSwapKeepsCollision` (state/art changes never move or resize the owner).

Left (nothing more I can do from this lane):
- Real art for every layer, effect and presenter state. All of it is stand-ins. No art_loop pass exists: it needs a separate
  critic session, and the Blender-made stills are far below the key-art bar, so everything stays a tracked `_PH` placeholder.
- Niagara/flipbook swap for VFX and per-state flipbooks (needs passing art).
- Reduced-flash toggle: needs the settings lane to call `UUmbrellaVfxSubsystem::SetReducedFlash`.

## Nov 12 review fixes
- Stale lines above ("Still open: enemy presenter, BG-02..06, VFX-06..11", "Left" in the first sections) are superseded by slice 2:
  enemy presenter, BG-02..06 and VFX-02, VFX-06..11 are built as stand-ins.
- Backdrop subsystem now only exists in Game/PIE worlds (`ShouldCreateSubsystem`), so editor worlds never get panel actors.
- Reduced flash: test `VfxLayersLightLimits` now checks the shrink through the subsystem. The toggle itself needs the settings
  lane: request filed in `docs/build/requests/visuals.md`.
- Not run: Unreal build and tests (no engine in this session).
