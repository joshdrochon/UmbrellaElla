# fixflow status
- Done: Flow level-up screen. `EFlowScreen::LevelUp`, `EFlowCommand::OpenLevelUp`; `HandleLevelGained` opens it on the
  `LevelGained` bus event (Director's Cut, Playing, FLOW_48 on). Back/Confirm/Pause close to Resuming, then Playing on neutral input.
  Progression has no level-up widget, so Flow draws its own SFlowMenu screen ("Level N") in the 16:9 view; swap in progression's if one lands.
- Tests: UmbrellaElla.Flow.LevelUpScreen, .Flow.World.LevelUpShowsAndResumes, .Flow.World.NoLevelUpScreenInStartGame.
- Run: build exit 0; UmbrellaElla.Flow PASS (20); module_check and manifest_check 0 problems. Full suite not run.
- Review fixes: level-up gated on FLOW_48 (was FLOW_42). Back label and Settings stub heading/body moved to FFlowMenuText.
- Intended gating: FLOW_41 off hides the pause Settings entry; MOVE_08 off stops F1/gamepad Menu pausing. Each follows its own rule row.
- Not done: a FLOW_48-off test. Flags are baked constants (UmbrellaFeatureFlags.cpp, generated), so a test cannot flip one.
- Not run: build and tests after this change.