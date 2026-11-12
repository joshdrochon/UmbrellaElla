# flowroute status
Done (build exit 0, UmbrellaElla.* PASS 225/225, module_check 0, manifest_check 0), after merging main with area/level:
- Director's Cut start spawns `AUmbrellaLevelDirector`, `BuildRoute(Flow.DirectorsCutRouteSeed)`, places Ella at checkpoint 1; the director hands off to `BeginKeeperFight` at the route end. If the route cannot be built, falls back to the Keeper fight. Start Game unchanged.
- Retry in Director's Cut puts Ella at the last checkpoint reached (`PlaceAtLastCheckpoint`).
- Progression widgets were already wired (XP ring in Director's Cut only; purchase screen at run start). Widgets use `AddToViewport` on the local controller.
Tests: `UmbrellaElla.Flow.World.DirectorsCutReachesFirstCheckpointWithRoute`, `.StartGameSkipsRouteAndStartsKeeper` (plus existing Flow tests).
Left: purchase screen at refuges mid-route (FLOW-29) is not shown; only at run start. Keeper fight start after handoff is not covered by a world test (Level tests cover the handoff call).
