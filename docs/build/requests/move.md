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
