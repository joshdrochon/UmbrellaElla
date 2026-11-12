# flow status

## Slice 1 (G1): FLOW-02, FLOW-04, FLOW-34, FLOW-35, ART-04 + smoke hook
Built (all behind their flags via IsFeatureEnabled):
- `Flow/FlowRules` pure screen state machine (Title, Playing, Paused, Settings, Resuming, Defeat, Story, Credits).
- `AUmbrellaPlayerController`: Start Game / Start Director's Cut, pause (Escape, F1, gamepad Menu via runtime IMC_Menu at
  priority 10), Continue waits for neutral input, Settings stub, Quit, defeat Retry (calls `ResetForRestart`) and Quit to
  Title, win: story pages then credits then back to title (level reload). Gameplay input is blocked by disabling the
  pawn's input component while any menu is up.
- `AUmbrellaGameMode`: no pawn until a mode is chosen; `BeginFight` finds or spawns `AUmbrellaArena`, spawns Ella at its
  start, sets the arena as view target, calls `BeginKeeperFight()`.
- `UI/Menus/FlowMenuWidgets`: C++ Slate, pill buttons, drifting character-free background (clocks on pause).
- `Story/FlowStoryText`: ending pages and credits, word for word from the GDD.
- `Smoke/SmokeHookSubsystem`: active only with `-SmokeQuitAfter=`; presses Start Game via the Start screen path, logs
  SMOKE_EFFECTIVE at=start/end (reflection over UUmbrellaTuning + flags), SMOKE_SHOT, SMOKE_OK, quits.

Tests (`UmbrellaElla.Flow.*`): TitleStartsPlaying, PauseCycle, DefeatIsNotTheWin, WinStoryThenCredits,
TimelinesAndNeutral, SmokeLowFps; World: StartGameReachesFight, DirectorsCutReachesSameFight, MenuBlocksGameplayInput,
DefeatShowsRetryAndRetryResets, EncounterCompletedReachesCredits.

## Known gaps
- "Director ACTIVE" is not asserted: the director stub exposes no state. Retry is proven by the controller's retry
  count, not by a director read. Add a state getter in the keeper lane and tighten the test.
- Smoke `input=`/`gamepad=` report `none` (need Motor/Attack actions from other lanes). `UMBRELLAELLA_BUILD_COMMIT` and
  `UMBRELLAELLA_WORKBENCH` are read if the Target defines them (not my lane), else `unknown`/0.
- Camera 16:9 lock and view-rect measure depend on the arena's camera (stub has none yet).
- Credits omit the executive producer name (GDD redacts it) and Rick's role (OPEN).
- No music (audio lane); no WASD menu nav yet.

## Later (not started)
FLOW-03 tutorials, FLOW-36..41, 43..45, 49 (settings pages, win statistics, Game Options), MOVE-08..10, MOVE-17,
NAR-02..08.
