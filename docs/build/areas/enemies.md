# Area: enemies (Director's Cut regular enemies, the Broken Mill room and traps)

Branch `area/enemies`. Read `docs/build/worker-rules.md` first. Added Nov 12 14:10 (Josh: 8 workers).

## Rule IDs (all Director's Cut, G2)
COM-12 .. COM-18 (male/female variants, dual-colour red/yellow shots, Roadwarden three types, Floodstrider, Sky Courier,
courier packet lifecycle, kills optional with firing windows), HAZ-02 .. HAZ-23 (the Broken Mill Roadwarden one-room
test and its checks, trap baseline: air mill, timed shutter, hostile bellows, roof bridge teeth, the pressure contract),
FLOW-46 (procedural placement shot colour).

## GDD sections
5 "Director's Cut full level": "Broken Mill Roadwarden: proposed one-room test", "Trap catalogue and pressure budget",
"Enemy roles and proposed combat baselines"; 8 "Production state coverage" and the enemy prompt sections (for the
state names art will need; art itself is the arena area's).

## File lane (only these)
- `Source/UmbrellaElla/{Public,Private}/Enemy/**`, `Trap/**`, `BrokenMill/**`
- `Source/UmbrellaElla/Private/Tests/Enemy/**`, `Private/Tests/Trap/**`, `Private/Tests/BrokenMill/**`
- `Content/UmbrellaElla/Enemy/**`, `docs/build/areas/enemies-status.md`, `docs/build/requests/enemies.md`

## What to build
- An enemy base (state UENUM, hittable via `IUmbrellaShotReceiver`, HP from your tuning, fires through
  `AUmbrellaProjectile::Fire` with EnemyRed/EnemyYellow) and the three enemy families with their behaviours from the GDD.
  Kills broadcast an event the progression area can read (use the bus: `BossTargetHit`/`ProjectileContact` for hits; for a
  kill, broadcast `XPAwarded` only if the GDD gives you the XP value, else write a request for a `EnemyKilled` event in
  `docs/build/requests/enemies.md` and broadcast `BossPartDestroyed` with Detail=`Enemy` meanwhile).
- Traps (HAZ-19..22) as actors that damage via shots or a hazard overlap on `UmbrellaCollision::Hazard`, with the
  pressure contract (HAZ-23) as a rule function plus tests.
- The Broken Mill room (HAZ-02..18) as a self-contained actor/room that can be spawned from code into a test world.
- Placement uses a seeded `FRandomStream` (never unseeded random). Placeholder visuals from engine primitives.

## Done
Worker-rules DoD, plus rule tests for each enemy's behaviour and the pressure contract, and world tests: each enemy
spawns, takes damage from a PlayerBlast and dies at 0 HP, fires the right colour, each trap hurts Ella on contact.
