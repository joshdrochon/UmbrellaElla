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
  render/scene (L_Graybox, arena camera), not flow. Flow and rules run normally under it.
