# move status

Branch `area/move`. Build exit 0, `tools/ue/test.sh` PASS 26/26 (19 of them `UmbrellaElla.Move.*`), module_check 0, manifest_check 0, feel_check 0.

## Done (G1 and G3 lists)
| Rule IDs | Where | Proof (tests in `Private/Tests/Move/`) |
|---|---|---|
| MOVE-04, 05, 06, 07, 08 | `Input/UmbrellaInputBindings`, `EllaInputAdapterComponent` | `Move.DefaultBindings`, `Move.World.InputAssetsBuilt` |
| MOVE-13, 19, 20, CORE-05 | `Umbrella/UmbrellaAction` (rules), `UmbrellaStateComponent` | `Move.ActionRules`, `Move.StateLockWaitsForNeutral`, `World.Rise…`, `World.AbsorbFallAndFreeFall`, `World.LockStopsMotionAndFire` |
| MOVE-21, 11, 18, 15 | `Motor/MotorModel`, `EllaMotorComponent` | `Move.Baseline`, `Move.StateSpeedsAndTrim`, `Move.HopDashTuned`, `Move.NoDirectSteering`, `World.HopAndDashMoveAsTuned` (each at 1/30, 1/60, 1/120 s) |
| MOVE-22 | wind in `MotorModel` | `Move.WindRideAndDecay`, `World.RideCurrentFromEvents` |
| UMB-05 (lift) | `LiftMultiplier`, motor listens to PlayerHealthChanged | `World.LiftScalesWithHealth` |
| MOVE-14, COM-06 | `AttackEmitterComponent`, `AttackCadence` | `Move.SmallBlastCadence`, `World.ShootFallFiresRightOnlyWhileDropping` |
| COM-05, COM-10, MOVE-12, COM-11 | `Attack/SpellRules`, emitter selection state | `Move.SpellAvailability`, `Move.SpellBaseline`, `World.SpellSelectionAndFire`, `World.FireIsUnlimited` |
| COM-07, 08, 09 | `SpellRules::BuildVolley`, emitter | `Move.SpellVolleys`, `World.SpellSelectionAndFire` |
| MOVE-16 | shared contract, no per-mode branch | `World.ControlsSameInBothModes` |
| CORE-04 | module_check 0 problems, no cross-lane includes except public headers | `module_check` |

Shared test helper for other areas: `Private/Tests/Shared/UmbrellaTestWorld.h` (`FUmbrellaTestWorld`: `SpawnElla`, `TickFrames`, `TickSeconds`, `CountActors<T>`).

## Interfaces other lanes use
- Input: IA_* and IMC_Default are built in C++ at runtime (no .uasset, nothing to merge). Priority 0. No editor script needed.
- `UEllaMotorComponent`: `SetLocked` lives on `UUmbrellaStateComponent::SetLocked(bool)` (pause, presentation, terminal). Resume waits for neutral. `IsHopProtected()` for Health. `SetPlayBounds(FBox2D)` (X, Z) for Arena.
- `UUmbrellaStateComponent::GetAction()`; also broadcasts UmbrellaConfigChanged, Detail = Rise/ShootFall/AbsorbFall/FreeFall, SourceId Ella.
- Absorb numbers (UMB-05) are in `GetDefault<UUmbrellaTuning>()->UmbrellaFlight` (AbsorbRange, AbsorbConeDegrees, PullSpeed, CaptureDistance, HealPerYellow, HealPerRecoveryRank).
- `UAttackEmitterComponent`: `SetPlayMode` (Flow), `SetDirectorLevel` (Progression), `GetEquippedSpell`, `OnEquippedSpellChanged()`, `IsWheelOpen()`, `GetWheelPreview()`, `GetStreamLength()` (beam visual). Wheel hold opens the wheel and locks the state; the wheel UI is Flow's.

## Event contracts I assumed (other lanes must match)
- Wind (arena): WindEntered/WindExited, SourceId = current id, TargetId Ella or none, `Value` = current speed in units/s, `Detail` = `Right|Left|Up|Down` or `"x,z"`. Ride only works with Ride held, overhead, inside a current.
- Health: PlayerHealthChanged `Value` = active health in hits, `Amount` = per-life capacity in hits (0 = use 3). Motor answers with LiftAvailabilityChanged, `Value` = multiplier.

## Decisions I made that are Josh's to confirm
1. Overhead Hop direction: the GDD does not say. I hop horizontally 40 units, right by default, left with left input (mirrors the falling dash). Alternative: vertical hop.
2. Streamed Blast: the shot service has no beam, so each of the 10 ticks/s fires a thin pulse (width 14, damage 4, speed 1200, range 1400). `GetStreamLength()` gives the beam length for the visual. Alternative: a real beam actor (projectile lane).
3. Spell wheel: right-stick directions are bound as four digital keys (not an analog wheel axis); 0.45 stick threshold not implemented (uses the project 0.25 axis config).
4. Burst option (1-5 shots, spacing 0.08 s) for Small Blasts not built; default is one shot.

## Not run / left
- Hardware acceptance (real keyboard, mouse, gamepad) NOT RUN; tests drive the adapter's routing, not Enhanced Input events.
- Remapping UI/Save (MOVE-09/10/17) is not in my list.
- Ella is not visibly moved by art: AnimPresenter is arena's.
- Package/smoke not run (build lead).

## Settings integration (MOVE-17)
Adapter applies saved bindings in BindInput via ApplySavedBindings (soft dependency on USettingsMenuSubsystem). Test: UmbrellaElla.Move.World.SavedRemapReachesLiveContext. Move tests: 26 pass.

## Clause audit: every `ii` clause for lane move built (Nov 13)
Each test was proven by breaking its code on purpose: with the code disabled the test FAILED (round 1: all 8 new tests
failed; round 2: "only Small cycles" and the smoky face), then PASSED with the code restored
(`TEST_FILTER=UmbrellaElla.Move+Health+UI+Feedback`: 118/118). Rows in `docs/build/clause-proof.csv`; tags set to `proven`.

| Clause | Code | Test |
|---|---|---|
| MOVE-15 hop protection blocks damage in Health (+ i: distinct from post-hit) | `Health/UmbrellaHitProtectionSource.h` (interface, motor implements it), `UmbrellaHealthComponent::IsOwnerHitProtected` | `Move.World.HopProtectionBlocksHealthDamage` |
| COM-06 fold-ready / snap open + pulse / cock / reset tied to emission | `Attack/SpellPresentation` canopy cycle, stepped and pulsed by the emitter | `Move.World.CanopyCycleTiedToEmission` |
| COM-11 only Small uses fold/open/cock | same | `Move.SmallCanopyCycle` |
| COM-07 shoulder-braced Stream; COM-11 RegularFall vs ShoulderFall | `SpellPresentationRules::BodyPoseFor`, `UAttackEmitterComponent::GetBodyPose` | `Move.World.SpellBodyPoses` |
| COM-07 canopy strands converge around a dark body | `SpellPresentationRules::BeamStrands`, strand parts in `AStreamBeamActor` (dark body, no collision) | `Move.World.StreamStrandsConvergeOnDarkBody` |
| COM-11 locked-weapon UI shows 1/10/20/30 | `SpellPresentationRules::WheelEntries`, wheel drawn by `AUmbrellaHUD` while open | `Move.WheelShowsUnlockLevels` |
| FLOW-30 bronze/gold, smoky translucent face, etched rim | `ClockHudRules::BuildDialPlan` (smoky face always under the art; etched ring + 48 fine marks) | `Move.ClockDialLook` |
| FLOW-32 absorbed energy flows into the clock | HUD listens to PlayerHealthChanged `Heal` only; motes from Ella to the clock (`ClockHudRules::StepEnergy/EnergyPosition`) | `Move.World.HealEnergyFlowsIntoClock` |

Lane note: FLOW-30/32 live in `UI/` and `Health/` (health's files); the lead moved those clauses to lane move (9e65976a).
Open for the presenter (Feedback lane): read `GetBodyPose()` and `GetCanopyPhase()` to pick the RegularFall/ShoulderFall
and fold/open/cock pictures; nothing draws them on Ella yet. Strands and the wheel are code-built stand-ins, not passed art.
Prototype defaults (no GDD number): canopy open 0.06 s + cock 0.08 s, 4 strands, energy flow 0.5 s, wheel label "Lv N".
Not run: on-screen check of the wheel, motes and dial (no canvas in tests).

## Clause audit: first `i` batch (Nov 13)
Code existed; added proving tests (`Private/Tests/Move/MoveProofTests.cpp`), Move tests 47/47 pass. Not break-tested this batch.
MOVE-07 arrow trim + right-stick spells, MOVE-19 right stick, MOVE-12/COM-05 all four spells never run out, MOVE-07 fire right while traveling left.
Left: 46 `i` clauses for lane move in clause-audit.csv.

## Clause audit: `i` batch 2 (Nov 13, Opus)
12 clauses proven with 9 new tests (`MoveRideCatchProofTests.cpp`, `MoveHealthProofTests.cpp`). Break-tested: each code path
broken on purpose -> its test FAILED (3/3 and 6/6), restored -> PASS. `TEST_FILTER=UmbrellaElla.Move`: 56/56.

| Clause | Test | Break used |
|---|---|---|
| MOVE-20 Absorb/Free fall end Ride | `Move.World.AbsorbAndFreeFallDisengageRide` | CanRide allowed any non-Shoot state |
| MOVE-20 remap keeps four combos | `Move.World.RemapKeepsFourCombinations` | saved remap not applied to IMC |
| UMB-05 no ammo/energy; repair not disabled; COM-05 no charge | `Move.World.CatchGivesNoChargeButRepairs` | catch-driven extra burst shot |
| SURV-05 Shoot-only fall no auto-catch | `Move.World.ShootFallDoesNotAutoCatch` | absorb pose open in ShootFall |
| SURV-05 no absorb cooldown | `Move.World.RepeatedCatchesHaveNoCooldown` | every 2nd yellow ignored |
| FLOW-31 / FLOW-33 handover adds no protection | `Move.World.LifeHandoverAddsNoProtection` | +1 s protection on life loss |
| FLOW-33 checkpoint passage no heal | `Move.World.CheckpointPassageDoesNotHeal` | CheckpointReached reset health |
| FLOW-33 ordinary projectile damage 1 | `Move.World.OrdinaryProjectileDamageIsOne` | fallback damage x1.25 |
| FLOW-32 life hand steady on partial change | `Move.LifeHandSteadyOnPartialChanges` | life hand read Active |

Note: `HealthTuning.PostHitProtectionSeconds` is 0.65; the GDD SURV-05 text says 0.6. Not changed (health's number, not a clause here).
Env: one test run hung at editor start in UBT `-Mode=ValidatePlatforms` (dotnet idle 10 min); killed, rerun passed.
Overlap: a `testmove` worker was started on the same lane=move `i` rows. These 12 are done here; it should skip them.

## Keeper clauses routed to move (Nov 13)
Gate review fixes: `PaintPart` renamed `BeamPaintPart`; clause-proof rows for COM-07 pose and COM-11 pose removed (no consumer draws the pose yet).
8 `i` clauses proven in `MoveKeeperProofTests.cpp` (real Ella + Encounter Director, both modes). Break-tested: retry broadcast removed,
extra checkpoint on part break, yellow fallback damage x1.25 -> 3/3 FAILED; restored -> 3/3 PASS.
| Clause | Test |
|---|---|
| FLOW-09 exactly 3 lives on retry, both modes | `Move.World.KeeperRetryGivesThreeLivesInBothModes` |
| OWL-06 both modes, phase advance carries health; OWL-10 checkpoint per phase, none mid-mechanism, health carried | `Move.World.KeeperPhasesCarryHealthAndCheckpointInBothModes` |
| OWL-13 yellow contact 1 health, Shoot alone never catches | `Move.World.KeeperYellowContactCostsOneAndShootNeverCatches` |

Not done, and why:
- FLOW-09 ii "keeps purchased max lives": GDD says retry gives exactly 3 current lives and keeps the bought maximum. Health restores `MaxLives` and ignores
  the retry unless `Event.Amount == MaxLives` (`UmbrellaHealthComponent.cpp:54-58, 139-144`). With max 4 the retry does nothing. Health lane's bug; not proven.
- OWL-06/OWL-10 ii capacity/upgrades on retry: same code path, blocked on the above.
- OWL-16 dash protection: dash grants none in tuning (`MotorTuning.h:42`, dash invulnerability OFF) and no code exists. Needs a decision: build optional dash protection, or reword the clause.
- OWL-13 absorb during fight (no cooldown/energy) is already proven by `Move.World.RepeatedCatchesHaveNoCooldown`/`CatchGivesNoChargeButRepairs`; aimed shots and 2.3 s cadence are model-level (keeper lane).
- FLOW-09 rollback ordering / level-checkpoint heal, OWL-09 reach and lift: not started (need the keeper rollback API and a defined "supported owl size").

## Lead answers applied (Nov 13)
- FLOW-09 keeps purchased max: `UmbrellaHealthComponent::ResetForRetry` now sets Lives to `Health.RetryLives` (3, capped at MaxLives) and keeps MaxLives and Capacity;
  the retry event is accepted when `Amount == RetryLives` (was `== MaxLives`, so max 4 ignored the retry). `Health.World.RetryRestoresFullLivesAndHealth` updated (3 lives, max 4).
  Proof: `Move.World.RetryGivesThreeLivesKeepsPurchasedMaximum`. Break-tested (retry set Lives=MaxLives -> FAILED, restored -> PASS).
- OWL-16 dash protection: not built (GDD baseline OFF). `Move.World.DashGivesNoProtectionByDefault` proves a dash gives none and a hit lands.
  Break-tested (IsProtectingFromHits true -> FAILED). No toggle exists in code, so none is claimed.
- Needed from keeper (rollback ordering, level-checkpoint heal, OWL-09 reach/lift): written in `requests/move.md`. Still unproven.

## Clause audit `ii` pass (Nov 13, Opus resume)
Merged origin/main (beccfa60). `docs/build/clause-audit.csv` has 0 rows tagged `ii` for lane move and 0 untagged: 26 `proven`, 36 `i`.
Nothing to build under the `ii` brief. The 36 `i` rows (code exists, proof missing) were the testmove lane's; that worker exited
(`logs/testmove.log`: WORKER_EXIT rc=143 at 11:44) with uncommitted edits in its worktree. Restarting it, or giving the `i` rows to move, is the lead's call.
One `i` row looks like missing code rather than a missing test: MOVE-15 "qualifying route rejects developer protection setting" (no developer protection setting exists in Source/).
