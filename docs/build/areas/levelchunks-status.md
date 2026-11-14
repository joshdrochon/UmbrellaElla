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
- After merging origin/main (5628870f, test launches pass -nosound): gate prefixes 84 tests, 78 PASS, 6 FAIL, all title/credits music
  tests in `Flow.World` ("a music component exists (an audio device is required)"). They need an audio device that `-nosound` removes;
  not caused by this lane (no Flow/audio file changed). Lead: the gate's Flow.World run will hit the same 6 on any merge.

## B8 (route stall at x 11 465, lead order), Nov 13
Verdict: not a soft-lock. agentplay's walker trims to the CP1 stand height + 300 (z ~450). Slot 5 of the Director's Cut route
(seed 1: 01B,02A,03B,04A,06B,07A,10A,08A,12A) is 07A; its low solid spans x 11 482..11 674, z 367..518. Ella's capsule (radius 17)
rests on its face at x 11 464.5. Under it runs the 07A bypass lane (floor to z 367); the same real keys, sinking to z ~200, reach CP2.
- Measured in the game (temporary log, removed): at the stall the motor velocity is +531/+182 but X stays 11 464.5; the character
  movement is in mode 3 (Falling), and a capsule sweep from Ella hits that solid (Actor_21) at 0.1 units. The motor sets MOVE_None in
  BeginPlay, but the game's possession runs ACharacter::Restart (Engine Character.cpp:1388) which sets the default mode, so the
  swept move stops Ella at solids ("Land blocks Ella", UmbrellaLevelDirector.cpp). Move lane: blocking works only through that mode.
- Tests (`LevelRouteWalkerTests.cpp`, the walker's numbers: MoveX held, Hop 0.6 s, DashForward 0.9 s, Shoot while above the trim
  height, heal when hurt; controller given a ULocalPlayer so the movement runs as in the game, PlayerController.cpp:332):
  `UmbrellaElla.Level.World.RealInputWalkerAtZ450StopsAt07ALowSolid` (stops at 11 464.5 +-1, slot 5 = 07A, solid ahead, no CP2 in 60 s);
  `UmbrellaElla.Level.World.RealInputBypassUnder07ASolidReachesCP2At60fps` / `At120fps` (CP2 in 21.7 s / 19.3 s).
  Break-proven: solids without collision -> the stall test FAILS (no solid, CP2 reached); the 07A low solid extended to the floor
  -> both bypass tests FAIL (best x 11 464, CP1). Restored: 3/3 PASS; Level prefix 27/27 PASS. Build exit 0, warnings 0.
- Capture (real game, editor -game 640x360, journey `pipeline/art/proof/levelchunks/b8_walker_stall.txt`): `b8_at_stall.png`,
  route step FAIL at x_best 11 465 (reproduced), shot ella=drawn(320,195). `b8_measure.py` -> B8_CAPTURE_OK: solid's left edge x 326,
  gap 6 px, 17/17 rows (`b8_measure.txt`); negative control (Ella at x 250) FAILS.
- For agentplay: the walker needs to sink under 07A's low solid (e.g. trim height ~200 in slot 5), not an assist. No geometry change made.

## B12 (CP0 -> CP1 walker stall at x 1 903, lead order 17:08), Nov 13
Verdict: a real block for every player since move's B7 ceiling, not the walker. Fixed in this lane.
- Measured (world test, the walker's own numbers and trim, started where agentplay's step began: x 974 at the route ceiling
  z 1 036, game movement mode): Ella stood at x 1 902.9, z ~451 for all 60 s, like agentplay's 40 s at x 1 903. Slot 0 is 01B;
  no route solid there. A capsule sweep 5 units ahead hits `UmbrellaArena_0.RightWall`: the Start Game arena's right wall
  (inner face x 1 920, z -100..1 180) stays at the arena's home width on the route. Before B7 Ella flew over it (z > 1 180;
  the 0ded1480 run crossed high). B7 holds her at z <= 1 036, so nobody can pass over it now; agentplay's late pass at t 44
  was not a route. Not the walker's trim height: no height gets past it.
- Fix: `AUmbrellaLevelDirector::ApplyRouteRightWall` (from `BuildRouteFrom` and `SetArena`, since the game mode sets the arena
  after the build) puts the right wall's inner face at `LevelCatalogue::RouteLength()` via `AUmbrellaArena::SetRightWallInnerX`.
  `MovePlayArea` (the handoff) and `ClearRoute` put it back at the arena edge (`ResetRightWall`). Start Game is unchanged.
- Tests: `UmbrellaElla.Level.World.RealInputWalkerFromCeilingReachesCP1At60fps` / `At120fps` (CP1 in 16.3 s / 14.2 s, past x 1 920,
  wall at the route end, slot 0 = 01B with no solid at x 1 903); `UmbrellaElla.Level.World.RouteRightWallAtRouteEndThenArenaEdge`
  (route end on the route, the moved arena's edge after the handoff, home edge after ClearRoute).
  Break-proven: with the wall not moved (first build: the wall moved only in BuildRouteFrom, before the game mode set the arena)
  both walker tests FAIL at x 1 902.9, block_ahead=RightWall, CP0; with the fix PASS.
  Level+Arena+Flow+Move+Encounter+Field: 145/145 PASS. Build exit 0, warnings 0. module_check, manifest_check 0 problems.
- For agentplay: no walker change needed; `routeassist 1` should now report "not needed".
- Capture (real game, editor -game 640x360 via run_game.sh, journey `pipeline/art/proof/levelchunks/b12_cp0_from_ceiling.txt`, agentplay's
  steps: 8 s untrimmed, 20 s idle at the ceiling, then the trimmed walker): CP1 PASS in 15.4 s from x 951, x_best 5 765, no assist;
  `b12_cp1.png` ella=drawn(320,196). `b12_measure.py` -> B12_CAPTURE_OK (`b12_measure.txt`); negative control on agentplay's 67011eb2
  log -> B12_CAPTURE_FAIL (timeout at 60 s, assist placed).
