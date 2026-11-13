# Playthrough of the real game (agentplay, handoff bar)

Header: commit=341e49c8 (origin/main merged) + agentplay journey hook, engine=5.8.4, config=Development (editor -game),
host=mac, run=editor -game via `tools/build/run_game.sh` (640x360 window, -nosound). Build: `build exit: 0 warnings: 0`.

## How it is played
`-SmokeJourney=<script>` (workbench only, `Source/UmbrellaElla/Private/Smoke/JourneyHookSubsystem.cpp`) plays the game
from the Start screen. Keys go in through `FSlateApplication::ProcessKeyDown/UpEvent` and clicks through
`ProcessMouseMove/ButtonDown/ButtonUp` at the button's centre: the same entry points a keyboard and mouse use, so menus get
them by Slate focus and play gets them through the viewport. Each step logs `JOURNEY_STEP ... result=PASS|FAIL` with the
flow screen, lives, health, Ella's position and the Keeper phase. The first failed wait ends the run with
`JOURNEY_END blocker=...`. Scripts: `tools/build/journeys/*.txt`. Re-run:
`tools/build/run_game.sh -SmokeJourney=tools/build/journeys/lose.txt -SmokeJourneyOut=Saved/Journey/lose`

Assists, each named in the log:
- `hits`: raw damage through Ella's own `UUmbrellaHealthComponent::TakeHit` (stands in for waiting on Keeper attacks).
- `assistwin` (WIN path): holds Shoot and delivers Ella's basic shot to the Keeper's parts through their own
  `ReceiveShot`; heals her to full between hits.
- `texts`: logs every visible text in the window with its painted size (what the screen holds, independent of the picture).
- `firstrun`: the tutorial counts as not seen (memory only; the settings file is not touched).

## 1. LOSE path: PASS (31/31 steps; captures and log in `pipeline/qa/playthrough/lose/`)
| # | Step | Result | Measured |
|---|---|---|---|
| 1 | Launch to the Start screen | PASS | Title screen right away; `01_start_screen.png` shows the painted title, Start Game focused |
| 2 | Title music | PASS (pick only) | `picked=MusicTitle`; playback cannot be measured: run_game.sh forces -nosound, so no audio device exists |
| 3 | Mouse: click Start Game | PASS, workaround | Without the workaround the click hit `SSoundLabelList`, not the button (see blocker B1) |
| 4 | First-start tutorial, Enter through it | PASS | 3 Enter taps: Tutorial, Resuming, Playing (`02_tutorial.png`) |
| 5 | Playing: Keeper fight | PASS (flow); FAIL (picture) | Encounter Active, phase wings. Picture black, see B2 |
| 6 | Natural Keeper hits | PASS | Standing still 8 s cost 1 life (3/3 to 2/3) |
| 7 | Hits until defeated | PASS | 5 assisted hits; Defeat screen; `04_defeated.png` shows "Defeated", Retry, Quit to Title |
| 8 | Mouse: Retry | PASS | Resuming, then Playing after 0.3 s; retries=1, lives 3/3, health 3.00/3.00, phase wings (the checkpoint) |
| 9 | Defeated again, mouse: Quit to Title | PASS | Level reloads to the Start screen, `06_back_at_start.png`, `picked=MusicTitle` |

## 2. Pause and Settings: PASS with 2 FAILs (`pipeline/qa/playthrough/pause/`, script `pause_settings.txt`)
| # | Step | Result | Measured |
|---|---|---|---|
| 1 | Escape in play opens Paused | PASS | at once; `p01_paused.png`: Paused, Continue / Settings / Quit |
| 2 | Mouse: Continue | PASS | Resuming, Playing after 0.3 s (one earlier run took 7.5 s; not reproduced with key state logged) |
| 3 | Mouse: Settings | PASS (state) | screen=Settings; widget tree holds Sound / Controller / Credits tabs, Master Volume, Sound Effects, Music, Text Size, Reduced motion, Reduced flash, Back, Save |
| 4 | Settings picture | **FAIL** | every capture (window, viewport widget, engine screenshot) still shows the Paused menu, see B3 |
| 5 | Escape inside Settings backs out | **FAIL** | still Settings after 3 s; `USettingsMenuWidget::NativeOnKeyDown` handles only key capture (UI/Settings lane) |
| 6 | Mouse: Back | PASS | back to Paused |
| 7 | Escape on Paused resumes | PASS | Resuming, Playing after 0.3 s |
| - | Pause menu Quit | not run | it calls `QuitGame` and exits the app (there is no "quit to title" on the pause menu) |

## 3. WIN path, Start Game: PASS in flow (26/26; `pipeline/qa/playthrough/win/`, script `win.txt`)
| # | Step | Result | Measured |
|---|---|---|---|
| 1 | Start Game by mouse, tutorial by Enter | PASS | Playing after 3 taps |
| 2 | Shoot (J 1.5 s), absorb (K 1 s), hop (Space) | PASS | z 1036 to 591 while shooting, to -72 while absorbing; hop moved x 384 to 460 |
| 3 | Keeper wings to mechanisms | PASS (assisted) | `JOURNEY_PHASE from=wings to=mechanisms part_hits=144` |
| 4 | Mechanisms to clock | PASS (assisted) | `part_hits=379` |
| 5 | Clock to the win | PASS (assisted) | Story screen 42.6 s after the fight began, 489 part hits; `T_VFX_Departure_PH` loads (the living departure) |
| 6 | Story text | PASS | `w04_story_text.png`: "Eventually, the owl's pursuit ends, and he retreats into the darkness, leaving Ella alive but still suspended between worlds." Music: `SurvivedSting` picked, no music id |
| 7 | Credits with music | PASS | Credits 13.1 s after the story began; names on screen (`w05_credits.png`); `picked=MusicTitle` (playback unmeasured under -nosound) |
| 8 | Credits end at the Start screen | PASS | Title 43.8 s after the credits began (`CreditsSeconds` is 24) |
| - | Gameplay picture | **FAIL** | black for the whole fight (B2) |
| - | Floor | **FAIL** | holding Shoot for the assisted fight dropped Ella to z = -28 063 (start 540) with no floor and no life lost; she leaves the camera. Rising stops at z = 1036. Code area: Motor play bounds / Arena (`ClearPlayBounds`, arena bounds) |

## Blockers found
- **B1 (workbench only, mouse)**: `Feedback/Audio/SoundLabelHud.cpp` adds `SSoundLabelList` full-screen and hit-testable on
  top of every menu. Every mouse click lands on it; the click also moves keyboard focus to `SViewport`, after which Enter
  does nothing either (measured: 38 Enter taps, still Title). The packaged game target (`UMBRELLAELLA_WORKBENCH=0`)
  does not build the list, so players are not hit; editor -game and Workbench builds are. One-line fix requested in
  `docs/build/requests/agentplay.md` (soundlabel lane). The journey hook sets it HitTestInvisible and logs
  `JOURNEY_WORKAROUND`.
- **B2 (gameplay picture black)**: on this Mac every gameplay capture is black except the HUD clock and a
  "Preparing Shaders (2)" line: composite capture, the engine's own screenshot (`FScreenshotRequest`), and the plain
  smoke shot (`-SmokeQuitAfter=15 -SmokeShot`: `frame_check FAIL black=0.984`). Same at RUN_RES=1280x720, and with
  `viewmode unlit` and post-processing off (so not a missing light). One earlier run (first launch after the build,
  "Preparing Textures (8)" on screen) drew the background and a Keeper card at 3 s. Under investigation; code area:
  render/scene (L_Graybox, arena camera), not flow. Flow and rules run normally under it. The on-screen
  "Preparing Shaders (2)" text never changes for minutes while the smoke hook's ready check reports 0 shader jobs, so the
  3D viewport looks frozen, not slow; menus, story and credits over it render fine. Not proven whether this
  is this shared Mac (load ~21, window behind other apps) or the game: needs one look at a visible window or the
  Windows package.
- **B3 (Settings picture)**: Settings is open in state and in the widget tree, yet the picture keeps the Paused menu
  (`p02_settings.png`, `p02_settings_vp.png`). The settings widget is added with `AddToPlayerScreen` (player layer) while
  the flow menus use `AddViewportWidgetContent`; a capture fault is not ruled out (same unknown as B2). The macOS window
  capture that would settle B2 and B3 is refused here (no screen-recording permission).
