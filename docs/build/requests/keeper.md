# Keeper requests to other lanes (no Core edit needed)

1. health: on `CheckpointRetried` (event `Amount` = 3, `TargetId` Ella) restore full active health and exactly 3 current lives. The director does not touch Ella's health.
2. health: Keeper chain, talon and gust damage reaches Ella as `ReceiveShot` with `Kind = EnemyRed`, `Damage` 1.25 / 1.5 / 1, `SourceId` = attack name (`MECH_Front_Cast`, `TALON_Rake`, `GUST_Band`). The gust is meant to bypass post-hit protection; read `SourceId == GUST_Band`.
3. projectile: Keeper parts block `UmbrellaCollision::PlayerShot` (box components, query only). Call `ReceiveShot` on the hit component; `Consumed` removes the shot, `Ignored` lets it pass (broken parts pass).
4. arena: `GetKeeperAnchorLocation()` is still the zero stub; the director uses whatever it returns.
5. flow: `UEncounterDirectorSubsystem::SetPaused(bool)` for the pause menu; `ResetForRestart()` on Retry (resumes at the checkpoint phase); `EncounterCompleted.Value` is the departure time in seconds.
6. health (FLOW-09, found Nov 13): `UUmbrellaHealthComponent::OnCheckpointRetried` resets only when `Event.Amount == State.MaxLives`.
   The director sends `Amount` = 3 (exactly 3 current lives, GDD FLOW-09). With purchased max lives (4+) the retry does not heal at all.
   Wanted: on a Keeper `CheckpointRetried` for Ella, set current lives to `Event.Amount` (3), keep `MaxLives`, full active health.
7. health + progression (FLOW-09 ordering): GDD says apply the boss-checkpoint rollback first, then heal with the resulting capacity.
   Both listen to the same `CheckpointRetried`; bus order decides. Wanted: Health heals after Progression's `RetryFromCheckpoint`
   (e.g. Health defers its reset to next tick, or Progression broadcasts a follow-up the Health lane listens to).
