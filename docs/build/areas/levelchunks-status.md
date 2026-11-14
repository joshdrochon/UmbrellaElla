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
Done: `UmbrellaElla.Level.World.DirectorsCutWalksRouteToKeeper` walks Director's Cut start -> CP1..CP3 -> short of the
handoff -> over it -> Keeper fight active, route threats cleared, CP events once each in order. Build exit 0, test PASS;
break-proven (handoff line moved +100000: FAIL 'handed off', 'route threats cleared'), restored. The Keeper fight also
raises CheckpointReached for its phases (detail `wings`, source KeeperOfTime); the test counts the director's events only.
Lead: to see the route in the real game, the journey needs Director's Cut (title menu item 2), not Start Game.

## B5 + B6 (Director's Cut camera, lead order post-handoff leftover 1), Nov 13
- B6: `LevelPlan::CheckpointStandLocation(0)` now stands in slot 0 (x 240), not at `RefugeStartX(0)` (x -720: no floor there and
  left of the camera clamp). There is no refuge before slot 0.
- B5: at the handoff `AUmbrellaLevelDirector::StepFollow` moves the arena with `AUmbrellaArena::MovePlayArea(LevelPlan::KeeperArenaOrigin())`
  before `BeginKeeperFight()`: the arena origin is the handoff X less `PlayerStartXFraction` of its width, so Ella stands at the same
  fraction as in Start Game, and bounds, fixed camera, backgrounds and the Keeper anchor move with it. The route scroll stops after the
  handoff; `ClearRoute` puts the arena home. Start Game never builds a route, so its arena stays at the origin. No Encounter change needed
  (`SpawnKeeper` already reads the arena's current anchor).
- Tests: `UmbrellaElla.Level.World.DirectorsCutFramesEllaAndKeeper` (Ella in the camera frame at route start, mid route, and Ella + Keeper
  in frame after the handoff; camera holds; arena home after ClearRoute). Break-proven: with both fixes removed it FAILS
  ('route start: Ella in the camera frame', 'arena at the route end', 'fight: Keeper in the camera frame'), restored PASS.
  `UmbrellaElla.Level.World.StartGameKeepsArenaAndKeeperFrame` pins Start Game's arena at the origin. Level+Arena+Flow+Encounter: 70/70 PASS.
- Capture: `pipeline/art/proof/levelchunks/` (journey `b5b6_directors_cut.txt`, windowed 640x360 via run_game.sh): route start ella=drawn(80,111);
  Keeper fight ella=drawn(128,263) keeper=drawn(480,145). `b5b6_measure.txt` has the lines. The journey runs without -SmokeQuitAfter:
  with it the smoke hook starts Start Game itself and the title click fails (first try, logged).
- Seen, not in this grant: in the fight frame the route background ends at the route end (screen x 256), so the left 40 % shows the route
  backdrop and the rest the arena backdrop. B7 (no ceiling on the route) and B8 (stall at x 11 465) are still open.
