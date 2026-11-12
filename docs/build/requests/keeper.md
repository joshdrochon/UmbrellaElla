# Keeper requests to other lanes (no Core edit needed)

1. health: on `CheckpointRetried` (event `Amount` = 3, `TargetId` Ella) restore full active health and exactly 3 current lives. The director does not touch Ella's health.
2. health: Keeper chain, talon and gust damage reaches Ella as `ReceiveShot` with `Kind = EnemyRed`, `Damage` 1.25 / 1.5 / 1, `SourceId` = attack name (`MECH_Front_Cast`, `TALON_Rake`, `GUST_Band`). The gust is meant to bypass post-hit protection; read `SourceId == GUST_Band`.
3. projectile: Keeper parts block `UmbrellaCollision::PlayerShot` (box components, query only). Call `ReceiveShot` on the hit component; `Consumed` removes the shot, `Ignored` lets it pass (broken parts pass).
4. arena: `GetKeeperAnchorLocation()` is still the zero stub; the director uses whatever it returns.
5. flow: `UEncounterDirectorSubsystem::SetPaused(bool)` for the pause menu; `ResetForRestart()` on Retry (resumes at the checkpoint phase); `EncounterCompleted.Value` is the departure time in seconds.
