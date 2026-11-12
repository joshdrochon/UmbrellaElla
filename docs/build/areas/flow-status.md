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
- NOT MET: "director ACTIVE" is not asserted (main's director has no state getter). Requested in
  `docs/build/requests/flow.md`; keeper's branch has `GetState()`. Once 'Merge area/keeper' is in main, StartGameReachesFight
  asserts `EEncounterState::Active` and the retry test asserts the director went back to Ready.
- Smoke `input=`/`gamepad=` report `none` (need Motor/Attack actions from other lanes). `UMBRELLAELLA_BUILD_COMMIT` and
  `UMBRELLAELLA_WORKBENCH` are read if the Target defines them (not my lane), else `unknown`/0.
- Camera 16:9 lock and view-rect measure depend on the arena's camera (stub has none yet).
- Credits carry placeholders `[EXECUTIVE PRODUCER NAME - Josh to supply]` and `[ROLE - Josh to supply]` (test: WinStoryThenCredits... in FlowRulesTest).
- No music (audio lane); no WASD menu nav yet.

## Later (not started)
FLOW-03 tutorials, FLOW-36..41, 43..45, 49 (settings pages, win statistics, Game Options), MOVE-08..10, MOVE-17,
NAR-02..08.

Also in flow's lane, not started: the progression purchase screen and level-up screen, plus `SetPurchaseContext` calls at
refuges and between runs (waits for area/progression on main; docs/build/requests/progression.md). Integration calls
waiting on other areas: pause/title menus -> `USettingsMenuSubsystem::OpenSettings` and `SetPlayMode` (settings),
`UStorySubsystem::BeginNewRun` for Director's Cut (story), ModeSelected Detail 'DirectorsCut'/'StartGame'.
Minor, from review: freeze or protect Ella during Story/Credits; menu strings move to FlowStoryText later.
