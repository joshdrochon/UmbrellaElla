# keeper status

## Done (G1): OWL-06 .. OWL-35, FLOW-09
Build `build exit: 0` (unity and `NONUNITY=1`), `test.sh` Keeper filter PASS 34 tests (25 rule, 9 world),
`module_check` 0, `manifest_check` 0, `encounter_check` 0. Commit on `area/keeper`.

| Rule | Where | Proof (`UmbrellaElla.Keeper.*`) |
|---|---|---|
| OWL-06/09/10 phases, wing-first gating, checkpoints | `Encounter/KeeperFightModel`, `EncounterDirectorSubsystem` | PhaseGating, BaselineHp, WingBreakAdvancesToMechanisms, MechanismOrderAndClockOpening, World.PhaseAdvancesWhenItsPartsBreak |
| OWL-08 HP | `Owl/KeeperTuning.h` (bake markers) | BaselineHp |
| OWL-11/12 red, reduced pressure, no prefire | model `StartRedVolley` | RedPressure, RedIsReducedDuringPhysicalActivity |
| OWL-13/14 yellow | model `StartYellow` | YellowPackets |
| OWL-15..17 gust | model gust stages | GustLocksBandAndStopsWithWings, GustDamagesAndPushesOnce |
| OWL-18..20 talon | model talon | TalonWarnsStrikesAndRearms, TalonWarningDoesNoDamage |
| OWL-21..27 front/middle/rear casts | model casts, `AKeeperOfTime` heads | MechanismHeadIsTheHittableTarget, ChainHeadDamagesOncePerCast, MiddleCurveSignFollowsSerial, RearTwoStageHasSafePause |
| OWL-28 double beat | model `StartDoubleBeat` | ClockDoubleBeatRepeatsPaths |
| OWL-29..33 clock open/protect/final cycle, stun, slow, eye, blackout, time domains | model | ClockOpeningWindowAndRecovery, FinalExposureCycle, ClockStopsAtReserveBeforeFinal, BreakStunCancelsPhysicalMove, ClockHitStartsSlowAndEyeThenBlackout, SlowStretchesWorldTimersNotClockTimers |
| OWL-34 scheduler | model `TickPhysical` | PhysicalSchedulerSerialisesMoves |
| OWL-35 success, living departure | director `FinalizeEnding`, `AKeeperOfTime::BeginDeparture` | FinalClockHitEndsFight, World.FinalClockHitEndsInSuccess, World.DefeatAndCompletionInOneFrameDefeatWins |
| FLOW-09 retry at phase checkpoint | director `ResetForRestart`, model `RetryCheckpoint` | RetryRestoresPhaseCheckpoint, ClockDamageCarriesIntoCheckpoint, World.RetryRestoresPhaseCheckpointWithThreeLives |

Shape: `FKeeperFightModel` is plain C++ (no world); the director drives it, spawns `AKeeperOfTime`, fires shots with
`AUmbrellaProjectile::Fire`, and broadcasts PhaseStarted, CheckpointReached, CheckpointRetried, BossPartDestroyed,
BossTargetHit, BossAttackTelegraphed, EncounterCompleted. Placeholder visuals are engine cubes.

## Not run
- Package, smoke, PIE, the editor look of the placeholder Keeper (no editor session). Mac host only.
- `AUmbrellaProjectile::Fire` is still lane c's stub on this branch, so no test sees a real projectile fly or hit.
  Shots are proven as `FireShot` commands (speed, count, spread, damage) and as `ReceiveShot` calls on the parts.
- `encounter_check.py --wiring` not run (wants engine cards).

## Decisions I made (yours to overrule)
- Retry fires on `PlayerDefeated` only. `LifeLost` with lives left does not reset the fight (FLOW-09 says death, 3 lives).
- `ResetForRestart` after defeat re-enters the checkpoint phase itself (`bResumeAfterReset`, default true) and broadcasts
  `CheckpointRetried` with `Amount` = 3 lives. After a win it starts a fresh run (phase 1).
- Gust push direction: GDD gives 280 but no direction. I push Ella vertically away from the band centre.
- Every physical attack start (talon included) restarts the shared 6.5 s countdown.
- Slow cooldown (3 s) counts from the end of the slow.
- Final-phase exposure starts the moment the 2 s transition ends, then every 4.8 s; each opening also gives the 0.65 s fire pause.
- Same-frame defeat vs final hit: defeat wins (your area file); the win is finalised on the next `AdvanceFight`/tick.

## Needs another lane (see `docs/build/requests/keeper.md`)
- health: restore full health and lives on `CheckpointRetried`.
- flow: call `SetPaused`, `ResetForRestart`; credits on `EncounterCompleted` (`Value` = departure seconds).


## Enemies removed (Nov 12 14:22)
COM-12..COM-18 and `Enemy/**` moved to the enemies area. Removed from this branch with the keeper-side code that only served them
(enemy tuning fields, `ResetEnemies`, tuning-pointer refactor, enemy colours). Test-file `Step` renamed `KeeperTestStep` (unity -Wshadow).
Build exit 0, `UmbrellaElla.Keeper` PASS 34, module_check, manifest_check, encounter_check 0 problems.
