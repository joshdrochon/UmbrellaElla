# move requests

None blocking. Two nice-to-haves for Core (build lead, optional):
1. `Harness/UmbrellaFeatureFlags`: no change needed.
2. `Config/DefaultInput.ini` has no stick threshold for a spell wheel; if the 0.45 wheel threshold from the GDD matters, add it there (not my lane).

## Needed from the keeper lane (Nov 13)
1. FLOW-09 rollback ordering: expose on `UEncounterDirectorSubsystem` a rollback step that runs before `CheckpointRetried` is broadcast
   (e.g. `ApplyCheckpointRollback()` that restores XP/upgrades to the checkpoint and returns), plus a bus event or return value saying it is done,
   so Health can heal against the resulting capacity. Today the retry heal (Health) cannot tell whether rollback ran first.
2. FLOW-09 level-checkpoint retry heal: the Level lane's death-retry path must broadcast `CheckpointRetried` (TargetId Ella, Amount 3) for
   level checkpoints too; only the Keeper director does today. Health already heals on that event.
3. OWL-09 reach and lift: a defined "supported owl size" (a number or a `FKeeperTuning` field) so a test can assert Ella's reach and lift
   cover it. Not provable from move's tuning alone.

## Lethal bottom: the health/arena rule is not wired (Nov 13, agentplay floor blocker)
The motor now holds Ella at the arena bottom (`UEllaMotorComponent::GetPlayFloorZ`, root Z = arena bottom + capsule
half-height), even with play bounds cleared, and reports `IsAtPlayFloor()`. Nothing applies the GDD "lethal bottom"
(WIND-03, FLOW-17, game-spec line 38): `AUmbrellaArena::LethalBottom` is overlap-only and no code listens to it.
Until the owner wires it, the bottom is a safe floor. Needed from health (or arena): on reaching the bottom, apply the
lethal rule. How much "lethal" costs (the current life, or defeat as old D-new-lose says) is a decision row, not move's.
