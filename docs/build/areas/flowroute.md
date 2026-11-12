# Director's Cut wiring in flow. Branch area/flowroute. Read docs/build/worker-rules.md first.
Wait until `git log main` shows "Merge area/level" (check every few minutes, max 60 min), then merge main.
1. Director's Cut start: flow spawns the level area's route director and calls `BuildRoute` (docs/build/areas/
   level-status.md, docs/build/requests/level.md), places Ella at the first checkpoint, and hands over to the Keeper
   fight at the route's end (UEncounterDirectorSubsystem::BeginKeeperFight). Start Game is unchanged.
2. Progression widgets: show the XP ring HUD in Director's Cut only (FLOW-48) and the purchase screen at refuges
   (FLOW-29/FLOW-42), per docs/build/requests/progression.md.
3. Widgets only for a local player controller (CreateWidget logs an error otherwise; world tests use non-local ones).
World tests: Director's Cut reaches the first checkpoint with the route built; Start Game still reaches the Keeper.
Lane: Flow/**, UI/Menus/**, Core/UmbrellaGameMode.*, Tests/Flow/**. Done: worker-rules DoD.
