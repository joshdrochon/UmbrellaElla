
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
