# titlemusic status

2026-11-13, P0 hotfix: the Start screen was silent.

Done:
- FLOW-34: the flow controller starts the looping MusicTitle when the Start screen opens (`FFlowRules::MusicFor`,
  `AUmbrellaPlayerController::PlayFlowMusic`). Picking a mode keeps the same component playing: the ModeSelected row
  sees MusicTitle already playing and does not restart it (`UUmbrellaCueSubsystem::EnsureMusic`, `GetMusicId`).
- FLOW-04: story text plays without music; credits start MusicTitle over the Start background.
- FLOW-37: the music component now plays through the settings subsystem's Music class (`GetMusicClass`), so the slider
  reaches it. Before, it played with no class the slider scales.

Tests (all PASS, 116/116 in Flow, Audio, Settings, Feedback, Field.World, Story):
- UmbrellaElla.Flow.World.StartScreenPlaysLoopingTitleMusic
- UmbrellaElla.Flow.World.ModePickKeepsTitleMusicWithoutRestart
- UmbrellaElla.Flow.World.CreditsPlayTitleMusicAfterStory
- UmbrellaElla.Flow.World.MusicVolumeReachesPlayingMusic

Left (outside this hotfix):
- SFX one-shots set SCL_SFX/SCL_UI/SCL_Telegraph, which have no parent, so the SFX and Master sliders do not reach them.
  Fix: parent them to the engine SFX class in tools/build/assets/arena_audio_core.py, or set the override from settings.
- Not heard on speakers: tests ran headless. Josh to confirm by ear in a build.

2026-11-13, D-new-music-at-launch (Josh): MusicTitle starts when the game world begins, not when the Start screen opens.
- `UUmbrellaCueSubsystem::OnWorldBeginPlay` calls `EnsureMusic(MusicTitle)` for game worlds (FLOW-34 flag); the flow
  controller's call and the mode pick are no-ops after that (start count stays 1).
- Test: UmbrellaElla.Flow.World.MusicPlayingOnFirstFrameAfterLaunch (no controller, no widget; music playing, looping, once).
- Build exit 0; Flow, Feedback, Settings, Field, Audio targeted tests PASS.
