
## Route-stage backdrop coverage (lead scope, FLOW-25)
- Added `UUmbrellaBackdropSubsystem::LayerFootprint`, `StageCameraX`, `IsRouteStageCovered`, `CountCoveredStages` (all 9 stages, from LevelCatalogue slot extents).
- Test: `UmbrellaElla.Feedback.World.BackdropCoversRoute` (9/9, after scroll to route end, with art on a layer). Feedback suite PASS 28/28, module_check 0.
- Root cause of the playtest 0/9: `PlaytestRun.cpp` calls `GetActorBounds(true, ...)` (colliding components only) on no-collision panels, so extents are 0. Not my lane: fix written in `docs/build/requests/artslots.md`.
- Not run: the playtest itself (needs the fix above).
