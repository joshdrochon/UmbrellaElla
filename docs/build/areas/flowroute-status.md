# flowroute status
Done (build exit 0, UmbrellaElla.* PASS 225/225, module_check 0, manifest_check 0), after merging main with area/level:
- Director's Cut start spawns `AUmbrellaLevelDirector`, `BuildRoute(Flow.DirectorsCutRouteSeed)`, places Ella at checkpoint 1; the director hands off to `BeginKeeperFight` at the route end. If the route cannot be built, falls back to the Keeper fight. Start Game unchanged.
- Retry in Director's Cut puts Ella at the last checkpoint reached (`PlaceAtLastCheckpoint`).
- Progression widgets were already wired (XP ring in Director's Cut only; purchase screen at run start). Widgets use `AddToViewport` on the local controller.
Tests: `UmbrellaElla.Flow.World.DirectorsCutReachesFirstCheckpointWithRoute`, `.StartGameSkipsRouteAndStartsKeeper` (plus existing Flow tests).
Left: purchase screen at refuges mid-route (FLOW-29) is not shown; only at run start. Keeper fight start after handoff is not covered by a world test (Level tests cover the handoff call).

## Review round 1 (changes) — done
- `AUmbrellaGameMode::PlaceAtLastCheckpoint` is a no-op after the Keeper handoff (`HasHandedOff()`); the encounter's own retry checkpoint places Ella.
- Refuge purchase screen (FLOW-29, FLOW-42): in Director's Cut, reaching a new refuge (CP2, CP3; CP1 was served at run start) opens the purchase screen with context `SafeRefuge` when `ShouldOfferPurchase()`; Done/Back/Pause leaves via `LeaveRefuge` to the neutral wait, then play resumes. Once per refuge, never after handoff. New commands `EnterRefuge`, `LeaveRefuge`.
- Tests (UmbrellaElla.* PASS 238/238, build exit 0, module_check 0, manifest_check 0): `Flow.World.RetryOnRoutePlacesAtLastCheckpoint`, `Flow.World.RetryAfterHandoffKeepsEllaInArena`, `Flow.World.RefugeOffersPurchaseScreen`.
- Not done: the fallback-to-Keeper path with level flags off has no test; route-retry health carry stays with the Health lane (`CheckpointRetried` is a Keeper-phase event).
