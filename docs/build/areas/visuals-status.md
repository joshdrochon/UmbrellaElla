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
