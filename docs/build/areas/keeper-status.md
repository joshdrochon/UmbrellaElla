# keeper status

## Done (G1): OWL-06 .. OWL-35, FLOW-09
Build `build exit: 0` (unity and `NONUNITY=1`), `test.sh` PASS 49 tests (25 Keeper rule, 9 Keeper world, 14 Enemy, 1 bootstrap),
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


## Done (G2): COM-12 .. COM-18
Files: `Enemy/EnemyModel` (plain rules), `Enemy/UmbrellaEnemy` (actor, hit box, placeholder cube, fires via `AUmbrellaProjectile::Fire`),
numbers in `FKeeperTuning` (flat fields; HP carry the three manifest bake markers, other numbers are unmarked GDD values).

| Rule | Proof (`UmbrellaElla.Enemy.*`) |
|---|---|
| COM-12 types, variants share numbers, zero HP stops fire, contact damage off | BaselineNumbers, RoadwardenVariantsShareEveryNumber, ZeroHpStopsFire, World.PlayerShotsReduceHpAndDefeat |
| COM-13 both colours on every type; 2:1 allocation helper | BothShotColoursOnEveryType, ColourAllocationIsTwoRedToOneYellow |
| COM-14 Roadwarden cycle (patrol, 1 s aim, one committed 240 shot, 1 s recovery, 2.5 s cycle) | RoadwardenPatrolAimOneShotRecovery, ShotDirectionIsCommittedAtAimStart, NoFireWhenEllaIsBehind |
| COM-15 Floodstrider numbers | BaselineNumbers, BothShotColoursOnEveryType |
| COM-16 Sky Courier air patrol 400 at 100, 1.1 s hover, 180 shot | BaselineNumbers, CourierPatrolsInTheAir |
| COM-17 eight emissions total, slots 0-7, withdraw without XP, retry rebuilds | CourierEightEmissionsThenWithdraws, KillingACourierDiffersFromWithdrawal, World.DirectorRetryRebuildsEnemies |
| COM-18 | level layout (arena/level lane); enemy side: no fire at a target that is not ahead |
| HAZ-41 containment (patrol clamped to support) | PatrolStaysOnItsSupport |

Not done / for other lanes: kill XP award (progression lane reads `IsKilled`, no XP event sent from here), enemy art and
animation (arena reads `AnimationCue` events `enemy_patrol|aim|recovery|defeated|withdrawn`), placement and the
descent/return flow of COM-18 (level generator), yellow-lane safety (QA-40..42).
Open details I picked: enemies fire only when Ella is left of them; the Courier's mounts are one muzzle; `RedPerYellow` rounds to the nearest whole enemy.
