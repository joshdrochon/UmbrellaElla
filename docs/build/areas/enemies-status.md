# Enemies status

Build 0 errors; `TEST_FILTER=UmbrellaElla.BrokenMill` PASS (11 tests, including the two World tests); full-suite count not re-measured here; `module_check` 0 problems; `manifest_check` 0 problems.
All code is in `Source/UmbrellaElla/{Public,Private}/{Enemy,Trap,BrokenMill}` with tests in `Private/Tests/{Enemy,Trap,BrokenMill}`.

## Done (rule -> test)
- COM-12 gender variants, mechanics identical -> `Enemy.World.GenderChangesNoMechanics`
- COM-13 red/yellow shots on every type -> `Enemy.World.FiresConfiguredColour`, `Enemy.ShotIsStraightAtCapturedTarget`
- COM-14/15/16 Roadwarden, Floodstrider, Sky Courier numbers and cycle -> `Enemy.ProfilesMatchGdd`, `Enemy.BrainCycle`, `Enemy.PatrolStaysInSpan`, `Enemy.World.DiesAtZeroHp`
- COM-17 courier 8 slots, withdraw, retry restore, duplicate callbacks -> `Enemy.CourierPacketLifecycle`, `Enemy.World.CourierWithdrawsAndRetryRestores`
- COM-18 fixed-right firing window, kills optional (withdrawal, no XP) -> `Enemy.FiringWindowIsFixedRight`
- FLOW-46 seeded 2:1 colour assignment with reserved early yellows -> `Enemy.ColorRatioTwoRedToOneYellow`
- HAZ-19..22 air mill (full disk), shutter, bellows, roof teeth, one hit per protection window -> `Trap.*`, `Trap.World.EachTrapHurtsOnContact`
- HAZ-23 pressure contract (9 violations) -> `Trap.PressureContract`
- HAZ-02..15 Broken Mill room geometry, activation, one shot per pass, winds, window/emission/impact arithmetic, guard cancel/abort/pause, shot log -> `BrokenMill.*`
- HAZ-17 pool gate as a rule function -> `BrokenMill.ShotLogAndPoolGate`

## Not code, not done
- HAZ-16 human acceptance and HAZ-18 art evidence are human/art gates. A human run of the room is still HAZ-16; the automated HAZ-14/15 checks are below.
- HAZ-41 floating-ground containment is not in this area's Rule IDs; not built.

## Open / limits
- Core request log: `docs/build/requests/enemies.md`. Enemies broadcast `BossPartDestroyed` Detail=Enemy.
- Bellows push is a rule value (`FTrapRules::BellowsPush`); the Motor does not read it yet. `ABrokenMillRoom::BuildRoom` now calls `BuildWinds`, which spawns the real `AWindCurrent` bands (upper reset left, lower onward right, `FBrokenMillTuning::WindSpeed` 300 prototype).
- Gust length/speed, blade count, tooth size are not in the GDD; prototype starts in `FTrapTuning`.

## Fixenemies pass (HAZ-14, HAZ-15 integrated checks)
- Real `AEllaCharacter` + Motor + room + real `AWindCurrent` in a transient world:
  `BrokenMill.World.GuardChecksWithRealElla` (pause freezes the clock then one shot; passing behind cancels, no bullet; pass-behind cancel is position-driven (SetActorLocation; no dash chain reaches the muzzle inside the 1.1 s warning); the abort is driven by real Motor dashes back out of range, no bullet),
  `BrokenMill.World.WindCarriesEllaPastOneShotPerPass` (current carries Ella right, one warning and one shot, no warning while passing behind, rearm and second warning on a fresh pass).
- Room fixes: pause is read from the world (`bPaused` was never set), assist/exit now set the no-warning phase, guard events are counted (`GetEventCount`).
- Found, not fixable in this lane: `AWindCurrent` overlap events carry the pawn's actor name as `TargetId`; the Motor only accepts `Ella`. In play no wind moves Ella. Request with the exact diff: `docs/build/requests/enemies.md`. The test broadcasts the event with `TargetId = Ella` as a workaround.
- Not covered: the free-rise case (Ella rising 120/s leaves the region before release) is real motion, not tested as a pass; reset-wind sweeps by a human run (HAZ-16).
