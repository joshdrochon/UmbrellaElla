
## Route-stage backdrop coverage (lead scope, FLOW-25)
- Added `UUmbrellaBackdropSubsystem::LayerFootprint`, `StageCameraX`, `IsRouteStageCovered`, `CountCoveredStages` (all 9 stages, from LevelCatalogue slot extents).
- Test: `UmbrellaElla.Feedback.World.BackdropCoversRoute` (9/9, after scroll to route end, with art on a layer). Feedback suite PASS 28/28, module_check 0.
- Root cause of the playtest 0/9: `PlaytestRun.cpp` calls `GetActorBounds(true, ...)` (colliding components only) on no-collision panels, so extents are 0. Not my lane: fix written in `docs/build/requests/artslots.md`.
- Not run: the playtest itself (needs the fix above).

## Review round 1 fixes (Nov 12)
Rule IDs: ART-05..ART-10, ANIM-02..ANIM-08, BG-02..BG-06, VFX-02/03, FLOW-25 (brief: docs/build/areas/artslots.md, now committed).
- Flipbook loader: passed `FB_Ella_<Name>` first, `_PH` second (like textures). Test `ArtSlotEllaFlipbookPaths` updated.
- Ella art: a state with its own art draws even when Idle has none (`TextureForState` falls back to any loaded state; `ApplyState` calls `DrawArt`). Test added in `World.ArtSlotElla`.
- Dropped the stale `/Art/Slots/` skip in `art_inventory.py`; `import_art_candidate.py` now says vfx-material rows are materials with nothing to import.
- Honest gap: vfx-sheet rows show frame 0 only. `ArtSlot.cpp` sets `Frame` to 0 and no frame driver exists yet.
- Run: `TEST_FILTER=UmbrellaElla.Feedback` PASS tests=29 failed=0 (includes all ArtSlot* tests); `python3 -m unittest tests.test_art_slots` OK (5); `art_slots.py check` PASS (100 slots); `module_check` 0 problems; build exit 0.
- Left: vfx-sheet frame driver; Roadwarden variants map to one slot (see docs/build/requests/artslots.md); Apply caching.

## Follow-ups (Nov 12, session 2)
Run: build exit 0; `TEST_FILTER=UmbrellaElla.Feedback` PASS tests=32 failed=0; art_slots check PASS; module_check 0; manifest_check 0; `tests.test_art_slots` OK.
1. Shot slots (ANIM-05, VFX-04): new `UShotPresenterSubsystem` draws shot:gold / shot:red / shot:yellow on projectiles (Projectile/ is a Core contract, so it swaps the sphere on the first tick instead of editing it). Bolt hit: `UUmbrellaVfxSubsystem::ShowImpactArt` draws shot:red-impact on ShotImpact. Test `World.ArtSlotShots`. Not drawn yet: shot:stream-beam (no consumer).
2. Sheet frames (VFX-02/03): the effect director already drove frames (`StepLive`, artfx); my "no frame driver" note was wrong. Added `World.ArtSlotSheetFrames`, which reads the sheet material's Frame and shows it advancing. No VFX sheet sidecar exists: columns come from the catalogue row (8 cells, one row).
3. Wind (FLOW-25): new `UWindPresenterSubsystem` (outside Field/, which is another lane): wind:current-field replaces the colour card, wind:decor-lines and the vfx-sheet:VFX_Gust sheet are overlays that exist only when their asset does; the picture is re-applied after the current refreshes its card. The card stays as fallback. Test `World.ArtSlotWind` fails if a wind slot asset exists and the wind does not draw it. No T_WindZone/T_WindLines asset exists yet; the _PH gust sheet draws today.
Left: 4 Roadwarden variant slots, 5 loader caching, 6 UI slots.

## Session 3 (Nov 12): UI screen slots
Rule IDs: ART-08, ART-05 (screen:* slots), FLOW-25 context.
- New `UUiArtSubsystem` (Feedback/Ui/): draws `screen:<Screen>` as a click-through full-frame overlay above the flow menus when the asset exists; menus stay the fallback. One lookup per screen change (loader cache).
- Test `UmbrellaElla.Feedback.World.ArtSlotUiScreens` (a row and asset per screen, click-through, swap, clear).
- Run: build exit 0; `TEST_FILTER=UmbrellaElla.Feedback` PASS tests=35 failed=0; art_slots check PASS (100); `tests.test_art_slots` OK; module_check 0.
- Not run: in-game capture (no T_Screen_* asset exists yet).
- Left: nothing in the brief.

## Session 4 (Nov 13): Feedback+Field world test fix
- Main merge (6c04ed2f) run: only `UmbrellaElla.Feedback.World.ArtSlotKeeperEnemy` failed (ArtSlotWind and CurrentDrawsItsUsableWidth passed; already fixed on main).
- Cause: the test, not the slot code. `T_Keeper_Owl_PH` now exists, so the keeper stand-in draws it on spawn and a later `ShowArt` is correctly refused. The test assumed no asset.
- Fix: the test finds the `KeeperStandIn` mesh; if it already has art, only the "second picture is refused" check runs.
- Run: build exit 0; `TEST_FILTER=UmbrellaElla.Feedback+UmbrellaElla.Field` PASS tests=39 failed=0.

## Session 5 (Nov 13): consumers for the 40 unconsumed slots, by art priority
Rule IDs: ART-05, ANIM-05, ANIM-06, BG-02..BG-06 (scene), FLOW-25 (frame).
- Scene backgrounds + frame (`USceneArtSubsystem`, Feedback/Background): bg:atmosphere, bg:land, bg:water, bg:clocks, bg:start-end (two panels: route start and end), scene:gameplay-frame. A panel exists only when its asset exists (the stand-in backdrop stays the fallback). Backdrop-sized panels scroll with the backdrop's parallax; frame and start/end are one camera view big. Test `World.ArtSlotScene`.
- shot:stream-beam: `UShotPresenterSubsystem::ShowBeamArt`, re-sized every tick. Test `World.ArtSlotBeam`. The beam rescales its cube after the swap; fix in `docs/build/requests/artslots.md` (request 3).
- Keeper parts: wings, mechanism front/middle/rear, clock cover, talon draw as layers over the body when their asset exists. Test `World.ArtSlotKeeperParts`.
- Slot rules for the ui:* rows (T_UI_ClockFace, Grain, Ground, HeadPaused, HeadSettings, Panel, TitleLockup); ui:font is a font, no slot. `art_slots.py check` was failing on main for these rows; it passes now (107 slots).
- Fixed `PresenterStandIn` (T_Ella_Idle_PH now exists, so Ella draws art; the stand-in checks run only without it).
- Run: build exit 0; `TEST_FILTER=UmbrellaElla.Feedback` PASS tests=38 failed=0; `tests.test_art_slots` OK; module_check 0.
- Not run: in-game capture (no Scene/Shots/Keeper part asset exists yet; the panels are untested with real art). Unsure of the art aspect: backdrop-sized panels are 4800x2400 like bg-layer panels.
- Still no consumer (need another lane or a design call): ella:free-fall/hop-cartwheel-dash/mode-transition/condition/living-critical (need Motor/Health state events), umbrella:prop/repair (no prop in Ella's shell), keeper:part-masks-7-6-4-0 and living-departure (need part-health and departure events), menu-backdrop:Clocks/Drift (SFlowBackground is in UI/Menus, another lane), ui:* pieces (HUD/menu widgets in the UI lane), world:* (level geometry), vfx-material rows (materials, nothing to import).
