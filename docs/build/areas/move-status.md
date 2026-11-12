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
