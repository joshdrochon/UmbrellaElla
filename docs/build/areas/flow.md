# Area: flow (start screen, mode flow, pause, win/lose screens, settings, story)

Branch `area/flow`. Read `docs/build/worker-rules.md` first.

## Rule IDs
G1 first: FLOW-02, FLOW-04, FLOW-34, FLOW-35, ART-04 (start screen with Start Game and Start Director's Cut; Start Game
goes straight to the Keeper with one basic shot; pause with Continue, Settings, Quit; defeat retry screen; the win:
story text over the background, then credits), plus the smoke hook (below).
Later (G2/G3): FLOW-03 (first-start tutorials, Pause then Skip), FLOW-36 .. FLOW-41, FLOW-43, FLOW-44, FLOW-45, FLOW-49
(settings: Sound, Controller remap, Credits, Back, Save; Director's Cut win statistics; Director-only Game Options),
MOVE-08, MOVE-09, MOVE-10, MOVE-17 (menu navigation, remapping UI), NAR-02 .. NAR-08 (Director's Cut story).

## GDD sections
2 (Player journey and modes), 6 (Story and dialogue), 7 (Menus, settings and accessibility, win results, settings and
earned-character interactions), 8 "Start screen and menu visual direction" and typography, 3 "Menus and remapping".

## File lane (only these)
- `Source/UmbrellaElla/Public/Core/UmbrellaGameMode.h` and `Private/Core/UmbrellaGameMode.cpp` (you own the GameMode),
  `{Public,Private}/Flow/**`, `UI/Menus/**`, `Story/**`, `Settings/**`, `Smoke/**`
- `Source/UmbrellaElla/Private/Tests/Flow/**`
- `Content/UmbrellaElla/Input/Menu/**`, `Content/UmbrellaElla/UI/Menus/**`, `docs/build/areas/flow-status.md`,
  `docs/build/requests/flow.md`

## What to build
- GameMode + `AUmbrellaPlayerController`: the title screen first (C++ UMG/Slate widgets, no Blueprint logic); Start
  Game sets `EUmbrellaPlayMode::StartGame`, broadcasts ModeSelected, spawns `AUmbrellaArena` if the map has none,
  sets its camera as view target, spawns/possesses Ella, calls `UEncounterDirectorSubsystem::BeginKeeperFight()`.
  Director's Cut: until the level exists, it routes to the same Keeper fight with a "Director's Cut" banner (record).
- IMC_Menu at priority 10 (your `Input/Menu/` assets or runtime-built): opening a menu adds it and removes gameplay
  input; closing reverses; resume waits for neutral input (CORE-05, MOVE-09). Pause (Escape / gamepad Menu):
  Continue, Settings (stub page for G1), Quit; PAUSED freezes the world (`SetGamePaused` plus the director's pause).
- Defeat: on PlayerDefeated show the retry screen (Retry -> `ResetForRestart`, Quit to title). Win: on
  EncounterCompleted show the story text over the background, then credits, then back to title.
- Smoke hook (needed by `tools/ue/smoke.sh`; contract in `pipeline/unreal-rules.md` "Smoke hook contract" and
  `python3 tools/ue_run.py --help`): log `SMOKE_EFFECTIVE at=start ...` at the first gameplay frame and `SMOKE_OK ...`
  with map, fps, commit, view/aspect, debugdraw=0, workbench; honor `-SmokeQuitAfter=<s>` (passes the title through its
  own Start Game path). Read flags via `Harness/UmbrellaFeatureFlags.h`, tuning via reflection over UUmbrellaTuning.
- 16:9 lock: the play camera constrains aspect 1.777778 (the arena owns the camera; you set view target).

## Done
Worker-rules DoD, plus world tests: Start Game reaches the fight state (director ACTIVE) with Ella possessed, pause
blocks gameplay input (`UmbrellaElla.Flow.World.MenuBlocksGameplayInput`), PlayerDefeated shows retry and Retry
calls ResetForRestart, EncounterCompleted reaches credits.
