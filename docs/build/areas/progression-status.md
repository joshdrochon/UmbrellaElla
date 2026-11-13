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

## Review round 1 fixes
- Kill XP now reads the events main actually broadcasts (strings in `docs/build/requests/progression.md` section 2): enemies by actor
  lookup, Broken Mill guard paid as Roadwarden (default, yours to change), keeper by TargetId part, keeper phase names = boss checkpoint.
  Tests: `World.RealEnemyAndMillKillsPayXp` (real AUmbrellaEnemy x3 + ABrokenMillRoom), `World.KeeperEventStringsDriveXpAndCheckpoints`.
  Test count is 26 Progression+Persistence in the last filtered run (earlier "36" was wrong).
- No emitters on main for the run events were a flow/keeper gap; both now broadcast the listed strings (not re-verified on main).
- `GetTuning()` stays the single switch point; lead adds the `Progression` member to `UUmbrellaTuning`.
- Open (minor): checkpoint written at run start precedes the run-2 reallocation, so a boss retry reverts it. Not changed.

## Clause slice (Nov 13, lead resume: `ii` clauses of lane progression in clause-audit.csv)
Evidence: `build exit: 0`; `TEST_FILTER=UmbrellaElla.Progression+UmbrellaElla.Persistence` PASS tests=41 failed=0;
`UmbrellaElla.Flow+UmbrellaElla.Health` PASS tests=56 failed=0; module_check 0. Break test: one build with a deliberate break per
clause made exactly the 9 new tests fail (9/41), then restored and re-passed.

Proven (tag `proven`, row in clause-proof.csv):
| Clause | Code | Test |
|---|---|---|
| FLOW-13 level checkpoint after boss checkpoint keeps the rollback | `ReachCheckpoint` keeps the boss snapshot; `BeginRun` starts a fresh chain | `LevelCheckpointAfterBossCheckpointKeepsRollback` |
| FLOW-17 effects derived from baseline once | `DeriveEffects` | `EffectsDerivedFromBaselineOnce` |
| FLOW-17 damage ranks change only damage | `DeriveEffects` | `DamageRanksChangeOnlyDamage` |
| FLOW-22 tutorial replay on shadow progress | `BeginTutorialReplay`, ModeSelected `Tutorial*` | `World.TutorialReplayUsesShadowProgress` |
| FLOW-42 review shows complete costs and effects | `FProgressionDraft::Review`, purchase widget review block | `ReviewListsCompleteCostsAndEffects` |
| SURV-06 +1 life per point reaches Ella | `ApplyToHealth` on every change and on Ella spawn | `World.LifePurchaseRaisesEllaLives` |
| FLOW-06 intro shown before the Extreme run + exact text | `ShowFinalHourIntro`, `UI/Progression/FinalHourIntroWidget` | `World.FinalHourIntroBeforeExtremeRun` |

Still `ii` (12), blocked on other lanes (exact diffs in `docs/build/requests/progression.md` 3-5):
- FLOW-05 x7, FLOW-06 "multipliers applied" + "telegraphs ... preserved", FLOW-21 x2: enemies/keeper/level must apply
  `ScaledHp`, `ScaledFiringCooldown`, `EnemyCount` (rules ready and tested: `RunScalingTouchesOnlyCooldownAndHp`).
- FLOW-17 health fraction: rule `ActiveHealthAfterCapacityChange` tested (`HealthFractionKeptOnCapacityChange`); health's
  `SetCapacity` clamps instead (request 4).

Defaults I chose (yours to change): Final Hour intro stays 4 s then removes itself, no skip input, shown every Extreme run start
(GDD leaves duration/skip/repeat OPEN). Tutorial replay starts on `ModeSelected` Detail containing `Tutorial` (flow does not send it yet).
Not run: PIE/visual check of the intro and review block.

## Keeper clauses (Nov 13, lead queue top)
Evidence: `build exit: 0`; `UmbrellaElla.Progression` PASS tests=38 failed=0; break build (no capacity push on retry, no keeper part XP) failed exactly
`KeeperRetryRestoresEllaCapacity` and `KeeperEventStringsDriveXpAndCheckpoints` (2/38), restored. Not run: module_check, PIE.
- OWL-06, OWL-10 retained/restored capacity: boss retry puts the checkpoint's max lives and hit capacity back on Ella, level retry keeps a purchase
  (`World.KeeperRetryRestoresEllaCapacity`; code already in `RetryFromCheckpoint` -> `NotifyChanged`).
- OWL-35 XP policy: keeper parts pay 60/60/80/100/150, eye 0, rollback pays again (`World.KeeperEventStringsDriveXpAndCheckpoints`).
- Request 7 ordering (Health heals after this rollback) is still Health's lane; Progression applies capacity synchronously on the same event.

## Lead resume (Nov 13, origin/main beccfa60): blocked
All 12 remaining `ii` clauses of lane progression (FLOW-05 x7, FLOW-06 x2, FLOW-17 health fraction, FLOW-21 x2) need code in other lanes.
Checked on origin/main: no file outside `Progression/` calls `GetRunScaling`, `ScaledHp` or `ScaledFiringCooldown` (request 3, enemies/keeper/level
lanes), and `UUmbrellaHealthComponent::SetCapacity` still clamps Active (`UmbrellaHealthComponent.cpp:156`, request 4, health lane).
The progression rule functions and their tests are done. Nothing left I can build in my lane for `ii`; the 28 `i` clauses (code there, test
missing) were not in this brief.
