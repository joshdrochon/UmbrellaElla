# Progression status

Slice 1 (all Rule IDs of the area, rule layer, subsystem, persistence, UI), commit on `area/progression`.
Evidence: `build exit: 0` (editor target), full `test.sh` PASS tests=36 failed=0 (24 are Progression, 4 Persistence),
`module_check` 0 problems, `manifest_check` 0 problems. Not run: package, PIE/visual check of the two widgets.

## Done (Rule ID -> where -> test)
| Rule IDs | Code | Tests (`UmbrellaElla.Progression.*`) |
|---|---|---|
| FLOW-15, SURV-06 curve, levels, points, 10 tracks, costs | `Progression/ProgressionRules` | XpCurveMatchesOracle, RankValues, CommitIsAtomicAndGated |
| FLOW-16 unlocks 1/10/20/30 | same | UnlockScheduleMatchesOracle |
| FLOW-05, FLOW-06, FLOW-21 run scaling, Final Hour (all stats maxed), enemy count with shortfall | same | RunScalingMatchesOracle, AllStatsMaxedTriggersFinalHour, World.OnlyAWonRunAdvancesScaling |
| FLOW-07, FLOW-08, FLOW-13, FLOW-20 level retry keeps, boss retry rolls back XP+ranks+derived level/unlocks, quit reload, part XP | same + `ProgressionSubsystem` | BossCheckpointRollsBackCoherently, BossRollbackRemovesUnlocksFromRolledBackXp, LevelCheckpointRetryKeepsXpAndRanks, QuitReloadRestoresLastCheckpoint, World.BossRetryRollsBackXpAndPartsPayAgain |
| FLOW-10 win carries growth | same | WinKeepsGrowthAndCountsOnce |
| FLOW-12 retry XP again | subsystem | World.LevelRetryKeepsXpAndRewardsAgain |
| FLOW-19 kill XP table (withdrawal, absorb, checkpoint = 0) | rules | KillXpTable, World.KillsAwardXpAndLevels |
| FLOW-11, FLOW-17, FLOW-18, FLOW-29 purchase vs reallocation, safe context, atomic commit | rules + subsystem | PurchaseVersusReallocation, World.PurchaseNeedsContext |
| FLOW-14, FLOW-22 baseline, persistence (checksum, backup, two corrupt = blocked) | `Persistence/ProgressionSaveGame` | Persistence.RoundTrip, CorruptMainFallsBackToBackup, TwoCorruptCopiesBlock, ChecksumSeesEveryField, World.ProfileSurvivesRelaunch |
| FLOW-23 developer fixture, shadow progress | rules + subsystem | DeveloperFixtureLevels, World.ShadowProgressNeverTouchesTheProfile |
| Start Game: no XP, baseline getters | subsystem | World.StartGameGivesNoXp |
| FLOW-42 purchase flow (stage, review cost, confirm atomic, cancel/context change discards) | `ProgressionDraft`, `UI/Progression/ProgressionPurchaseWidget` | DraftStagesWithoutChangingLiveValues |
| FLOW-48 XP ring (fill, overflow carry, MAX, pulse, reduced motion, hidden in Start Game) | `UI/Progression/XpRingWidget` | RingFillAndMax (fill logic); drawing not tested |

Oracle: golden numbers in the tests were taken from `tools/progression_model.py` (cumulative XP 916/1981/3096/7000, run scaling table, max cost 61).

## Getters other areas read (`UProgressionSubsystem::Get(WorldContext)`)
GetLevel, GetLevelProgress, GetUnspentPoints, GetRank(Track), IsSpellUnlocked(Spell), GetUnlockedSpells, GetHitCapacity,
GetMaxLives, GetHealPerYellow, GetDamageReduction, GetSuctionRange, GetSuctionConeDegrees, GetSpellDamageMultiplier,
GetRunScaling (HP/cadence/count for this run), IsFinalHourRun (flow shows the intro), OnLevelGained delegate.
Event contract is in `docs/build/requests/progression.md`.

## Decisions I defaulted (yours to change)
- A completed run is counted once per run, on `RunCompleted` or `EncounterCompleted`.
- Wings pay 60 per `BossPartDestroyed` of a wing part (two wings = 120); GDD does not say per wing or per pair.
- Unknown `CheckpointReached` detail = level checkpoint (keeps XP); `Phase`/`Boss`/`Keeper` = boss checkpoint.
- All stats first maxed during a lost run: Final Hour starts the next run anyway (evaluated at run start).
- A relaunch loads the last checkpoint's XP/ranks (quit/reload rule), a win clears the checkpoint.
- Refund only at `RunStart` context with completed runs >= 1; purchase at SafeRefuge, BetweenRuns, RunStart.

## Left / blocked
- `UUmbrellaTuning` has no Progression member (Core): request 1 in `docs/build/requests/progression.md`. Until applied, tuning is a default struct.
- Not wired by me (other lanes): who calls `SetPurchaseContext`, `UXpRingWidget::Show`, `UProgressionPurchaseWidget::Show`; health reading ranks; audio on `LevelGained`.
- Widgets are not visually checked (no PIE here); the ring is placed at tuning `RingViewportPosition`, not measured against the clock.
- Partial-reserve persistence and refund remapping are OPEN in the GDD; not invented.
