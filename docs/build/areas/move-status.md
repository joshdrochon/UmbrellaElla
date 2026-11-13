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
