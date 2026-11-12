# Enemies status

Build 0 errors; full suite PASS (34 tests); `module_check` 0 problems; `manifest_check` 0 problems.
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
- HAZ-16 human acceptance and HAZ-18 art evidence are human/art gates. HAZ-14/15 runtime sweeps with the real Motor and wind need the integrated build and a human run; only the rule parts are proven here.
- HAZ-41 floating-ground containment is not in this area's Rule IDs; not built.

## Open / limits
- Needs from Core: tuning member, `EnemyKilled` event, working projectile service (see `docs/build/requests/enemies.md`). Until then enemies read `FEnemyTuning()` defaults and broadcast `BossPartDestroyed` Detail=Enemy.
- Bellows push is a rule value (`FTrapRules::BellowsPush`); the Motor does not read it yet. Mill wind volumes are not spawned (Field lane owns `AWindCurrent`); `SelectWind` is the rule.
- Gust length/speed, blade count, tooth size are not in the GDD; prototype starts in `FTrapTuning`.
- Hit detection by the projectile service is untested end to end (service is a stub on this branch).
