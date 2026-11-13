# level status
Done (build exit 0, full suite PASS 212/212, module_check 0, manifest_check 0):
- FLOW-24, HAZ-24, HAZ-37: `AUmbrellaLevelDirector::BuildRoute(Seed)` spawns the nine-chunk route as engine-cube geometry; traps/enemies via `AUmbrellaTrap::ConfigureKind` / `AUmbrellaEnemy::Configure`; seeded enemy colours. Pure plan in `Level/LevelPlan`.
- FLOW-27, FLOW-28: refuges and checkpoint markers, `PlaceAtCheckpoint`, `CheckpointReached` event, Keeper handoff once (`BeginKeeperFight`).
- CAM-04..08: `StepFollow` / Tick calls `AUmbrellaArena::FollowEllaX`.
- CORE-06: `FBuildIdentity` has Revision (UMBRELLAELLA_BUILD_COMMIT) and AssetManifest (BUILD_INFO `asset_manifest=`).
Tests: `UmbrellaElla.Level.PlanIsSeededAndOrdered`, `.CheckpointsAndHandoff`, `.BuildIdentityRevisionAndManifest`, `.World.RouteSpawnsNineChunks`, `.World.CameraFollowsAndCheckpoints`.
Left: nothing spawns the director in a map yet (request 1 in docs/build/requests/level.md); asset_manifest not written by packaging (request 2). QA-36 camera measurement is playtest work.
