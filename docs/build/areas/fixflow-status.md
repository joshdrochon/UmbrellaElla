# fixflow status
- Done: Flow level-up screen. `EFlowScreen::LevelUp`, `EFlowCommand::OpenLevelUp`; `HandleLevelGained` opens it on the
  `LevelGained` bus event (Director's Cut, Playing, FLOW_42 on). Back/Confirm/Pause close to Resuming, then Playing on neutral input.
  Progression has no level-up widget, so Flow draws its own SFlowMenu screen ("Level N") in the 16:9 view; swap in progression's if one lands.
- Tests: UmbrellaElla.Flow.LevelUpScreen, .Flow.World.LevelUpShowsAndResumes, .Flow.World.NoLevelUpScreenInStartGame.
- Run: build exit 0; UmbrellaElla.Flow PASS (20); module_check and manifest_check 0 problems. Full suite not run.
- Not done: the review-flow minor items. `../UmbrellaElla-areas/logs/review-flow.txt` does not exist, so I could not read them.
