# Area: keeper (the Keeper of Time fight)

Branch `area/keeper`. Read `docs/build/worker-rules.md` first.

## Rule IDs
G1 first: OWL-06 .. OWL-35 (all 30), FLOW-09 (retry at the current phase checkpoint, 3 lives, full health).
Later: none (regular enemies moved to the `enemies` area, Nov 12 14:10). After G1, harden the fight: every
attack and effect from the contract, tuning from encounter data, and the QA scenarios for the Keeper.

## GDD sections
5 (Levels and encounters: Attack allocation by phase, Encounter record, Keeper numerical baseline, Attack and effect
tuning, Uncertainties and acceptance, Complete Keeper attack contract and every subsection). Data: `pipeline/level/encounter.json` + `encounter.md`; gate
`python3 tools/encounter_check.py` (0 problems; `--wiring` once your code reads the data, see `--help`).

## File lane (only these)
- `Source/UmbrellaElla/{Public,Private}/Owl/**`, `Encounter/**`
- `Source/UmbrellaElla/Private/Tests/Keeper/**`
- `pipeline/level/**`, `Content/UmbrellaElla/Keeper/**`, `docs/build/areas/keeper-status.md`, `docs/build/requests/keeper.md`

## What to build
- Encounter Director (`UEncounterDirectorSubsystem`, stubbed): the encounter state UENUM (READY, ACTIVE,
  ENDING_SUCCESS, ENDING_FAILURE, RESTARTING, PAUSED), phases and checkpoints, the scheduler, retry at the phase
  checkpoint (FLOW-09) when Health broadcasts LifeLost/PlayerDefeated, the win on the final clock hit (OWL-35) with the
  living departure; broadcast PhaseStarted, CheckpointReached, CheckpointRetried, BossPartDestroyed, EncounterCompleted.
  `BeginKeeperFight()` spawns `AKeeperOfTime` at `AUmbrellaArena::GetKeeperAnchorLocation()` (find the arena once; if
  none, use the origin and log a Warning).
- `AKeeperOfTime`: wings, three hanging mechanisms (front, middle, rear), the clock; each hittable part a component
  implementing `IUmbrellaShotReceiver`, with stable IDs, eligibility per phase and HP from the GDD baseline. Every attack
  in the contract (red pressure, yellow recovery shots, wing gust, close talon rake, front/middle/rear mechanism casts,
  clock double beat and cover) with telegraphs, using `AUmbrellaProjectile::Fire` with EnemyRed/EnemyYellow. Hit
  regions and timing come from tuning/encounter data, never from art.
- Placeholder visuals from engine primitives so the fight is playable before art (`arena` swaps art later).
- Pause: the director exposes `SetPaused` for `flow`; PAUSED freezes schedule and projectiles.

## Done
Worker-rules DoD, plus rule tests for the scheduler and phase transitions, and world tests: shots on an eligible part
reduce its HP and an ineligible part ignores them, phase advances when its parts break, retry restores the phase
checkpoint with full health, final clock hit = ENDING_SUCCESS, defeat and completion in one frame = defeat wins.
`tools/encounter_check.py` 0 problems.
