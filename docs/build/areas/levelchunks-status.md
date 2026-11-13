## levelchunks status
Done (branch area/levelchunks, build exit 0, Level/Field/Arena tests PASS, module_check and manifest_check 0 problems):
- HAZ-25..HAZ-36, HAZ-38, HAZ-39: `ChunkLayouts`, `ChunkCatalogueData`, `LevelPlan`; tests `UmbrellaElla.Level.ChunkLayoutsMatchCatalogue` and the other ChunkLayoutTests.
- WIND-03: `UmbrellaElla.Field.World.CurrentTargetsEllaAndMovesHer`.
- CORE-06: `tests/test_levelchunks_core06.py` (package.sh writes asset_manifest=).
Fix after 3935a34: a `-Wshadow` break between `LevelCatalogue.cpp` and `ChunkLayouts.cpp` (`M` alias) is renamed; the build now passes.
Review fixes: retry keeps `max(1, GetCheckpointReached())`; seeds 1001-1003 now run the generator (the fixture short-circuit and
`HasFixtureRoute` are gone; the GDD routes stay illustrative and only seed the fallback layout); `UmbrellaElla.Level.SeedFixtures1001To1003`
now checks each seed's generated route (valid, not fallback, deterministic, authored layouts and bypass valid, retry differs).
PlaytestRun `MeasureFlow28` already counts threats after `StepFollow(KeeperHandoffX(), 1)` (merged from main); no Playtest/smoke run by me.
`EnemySizeFraction` renamed `CheckpointStandFraction`.
Left: nothing in this lane. The `Hazard` folder has no tests of its own.
HAZ-25..HAZ-36 closed: `BuildRouteFrom` on the director; `UmbrellaElla.Level.World.EachVariantSpawnsItsLayout` spawns all 24 variants and checks trap, enemy and per-role current counts against each layout. Build exit 0, Level tests 21/21 PASS. HAZ-06/07 left partial: they are enemies-lane rows (priority algorithm unsettled in the GDD).

## Handoff question (Nov 13, ~11:55): is the route wired into Start Game?
Finding: no, and by design. GDD FLOW-02 (APPROVED_P0): "Start Game provides one basic shot type and goes straight to the
Keeper. Director's Cut follows its story / RPG / full-level route to the same complete fight." So the playthrough's
Start Game -> tutorial -> Keeper is the GDD behaviour, not a gap. `UmbrellaElla.Flow.World.StartGameSkipsRouteAndStartsKeeper`
already pins it. Wiring the route into Start Game would break FLOW-02; I will not do that without a decision.
The route IS wired into Director's Cut: `AUmbrellaPlayerController` -> `AUmbrellaGameMode::BeginRoute(DirectorsCutRouteSeed)`
spawns 9 chunks, Ella at CP0; `AUmbrellaLevelDirector::Tick` raises CheckpointReached CP1..3 and calls
`BeginKeeperFight()` at `LevelPlan::KeeperHandoffX()`. Tests: `Flow.World.DirectorsCutReachesFirstCheckpointWithRoute`,
`Flow.World.RetryOnRoutePlacesAtLastCheckpoint`, `Flow.World.RetryAfterHandoffKeepsEllaInArena`.
Broken Mill: NOT in any flow. Only `PlaytestRun` spawns `ABrokenMillRoom` in a scratch spot. The GDD does not place it
between the route and the Keeper: HAZ-02 calls it "a one-room diagnostic prototype ... not a replacement for the 12-chunk /
24-variant catalogue", FLOW-26 says "do not ... claim its camera/placement qualified". Putting it in the run is a design
call with no GDD rule, so it needs a decision row (added: D-new-mill-in-route, default = keep it out).
Agentplay's journey only drives Start Game, so it never could meet the route. To see the route, a journey must pick
Director's Cut.
Doing now: a Level world test that walks Director's Cut start -> CP1..CP3 -> Keeper handoff in one flow (break-proven).
