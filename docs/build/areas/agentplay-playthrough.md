HANDOFF BAR FAIL: every journey now reaches its end with no crash or soft-lock, and the Start Game paths pass with a readable picture, but in Director's Cut the Keeper fight happens off-screen (B5) and Ella starts the route off-screen (B6).

# Playthrough of the real game (agentplay, handoff bar)

Header: commit=7fb0f680 (origin/main 7da8aba6 merged: screenfix B2 + Ella-visible follow-up d8a48397, settings2 B3,
move floor, levelchunks walk test) + this commit's journey hook changes, engine=5.8.4, config=Development (editor -game),
host=mac, run=editor -game via `tools/build/run_game.sh`: a **visible 640x360 window**, -nosound. Build: `build exit: 0 warnings: 0`.
Journeys run one at a time (four windows at once steal mouse focus from each other: Retry and Continue clicks then land on an
inactive window, `active=0`; not a game fault). Captures + journey.log: `pipeline/qa/playthrough/{lose,pause,win,dc}/`.
Not merged into this run: artkeeper (Keeper cream box + lilac cube still on screen).

## How it is played
`-SmokeJourney=<script>` (workbench only, `Private/Smoke/JourneyHookSubsystem.cpp`) presses keys and clicks through
`FSlateApplication` like a keyboard and mouse. Scripts: `tools/build/journeys/*.txt`. Re-run one:
`tools/build/run_game.sh -SmokeJourney=tools/build/journeys/directors_cut.txt -SmokeJourneyOut=Saved/Journey/dc`
Assists, each named in the log: `hits` (damage through Ella's own `TakeHit`), `assistwin` (holds real J, delivers her basic
shot to the Keeper parts' own `ReceiveShot`, heals between hits), `routeassist N` (places Ella at checkpoint N through the
director's own `PlaceAtCheckpoint`; only used when the real-key `route` step before it failed).
New this run: `route N T [1]` walks with real keys only (D held, Space hop every 0.6 s, E dash every 0.9 s; `1` = hold J while
Ella is 300 above the stand height so she sinks back); Enter closes LevelUp/Story cards, Escape leaves a refuge Purchase.
`skipunless <Screen> n`. Every `shot` now measures Ella, the Keeper and the arena centre: projected pixel, and the picture's
luminance spread and mean in a box around it (`drawn` = spread or offset from the frame mean >= 12; `flat`, `offscreen`, `absent`).
Test: `UmbrellaElla.Smoke.Journey.*` 3/3 PASS (new `ParsesRouteSteps`).

## 1. LOSE (Start Game): PASS 31/31 (`lose/`)
| Step | Result | Measured |
|---|---|---|
| Start screen, title music picked | PASS | `01_start_screen.png`; `picked=MusicTitle` (playback unmeasured under -nosound) |
| Mouse: Start Game, tutorial by Enter | PASS | 3 taps; `02_tutorial.png` |
| Playing | PASS | `03_playing_keeper.png` frame_check PASS. Ella drawn (128,15) spread 20: a small figure at the very top edge (she sits at the ceiling z 1036). Keeper drawn (480,145) spread 0 mean 184: the flat cream box + lilac cube placeholder. Arena drawn |
| Natural hit | PASS | standing 8 s cost 1 life (3 to 2) |
| Defeated | PASS | 5 assisted hits; `04_defeated.png` Defeated / Retry / Quit to Title |
| Mouse: Retry | PASS | Playing after 0.3 s, retries=1, lives 3/3, health full; `05_after_retry.png` |
| Defeated again, mouse: Quit to Title | PASS | Start screen at once, `06_back_at_start.png`, `picked=MusicTitle` |

## 2. Pause and Settings (Start Game): PASS 29/29 (`pause/`); B3 closed
| Step | Result | Measured |
|---|---|---|
| Escape opens Paused; mouse Continue | PASS | `p01_paused.png`; Playing after 0.3 s |
| Mouse: Settings: picture | **PASS** (was FAIL) | `p02_settings.png` shows the Settings panel (Sound / Controller / Credits, volumes, Text Size, Reduced motion/flash, Back, Save) |
| Mouse: Back | PASS | Paused, `p03_paused_after_settings.png` |
| Escape inside Settings backs out | **PASS** (was FAIL) | Paused at once, `p03b_paused_after_escape.png` |
| Escape on Paused resumes | PASS | Playing after 0.3 s, `p04_playing_again.png` |
| Pause menu Quit | not run | it calls `QuitGame` and exits the app |

## 3. WIN, Start Game: PASS 26/26 (`win/`)
| Step | Result | Measured |
|---|---|---|
| Fight start | PASS | `w01_fight_start.png`: Ella drawn (128,15) top edge; Keeper placeholder drawn; arena drawn |
| Shoot J, absorb K, hop Space | PASS | z 1036 to 772 (shoot), to 111 (absorb); hop x 384 to 459. `w02_moves.png`: Ella drawn (155,291) spread 19 |
| Keeper wings, mechanisms, clock to the win | PASS (assisted) | Story 42.4 s after the fight began, 488 part hits |
| Story text, no music | PASS | "Eventually, the owl's pursuit ends, and ..." (`w04_story_text.png`); `picked=SurvivedSting`, music none |
| Credits with music, back to Start | PASS | Credits after 13.1 s (`w05_credits.png`), `picked=MusicTitle`; Title after 20.8 s |
| Floor | PASS | lowest Ella z this run 44; she stays in the arena (move floor fix holds) |

## 4. WIN, Director's Cut (title item 2): flow PASS 59/61 to Journey Complete and back (`dc/`); picture FAIL (B5, B6)
| Step | Result | Measured |
|---|---|---|
| Mouse: Director's Cut | PASS | Purchase opens first (5 points earned by an earlier run, `d00_purchase.png`); Escape to the Start screen, Director's Cut again, tutorial, Playing |
| Route start | PASS flow, **FAIL picture** | `d01_route_start.png`: Ella x -720, projected (-240,136): **off the left edge** (B6). Mother's line on screen. No Keeper (correct: not yet) |
| Real keys, no trim, 8 s | recorded | Ella rises to z 2 636 and leaves the top of the picture (`d01b_route_untrimmed.png`, ella offscreen (-24,-519)); an earlier 60 s run reached z 14 962. No ceiling on the route (B7) |
| CP0 to CP1, real keys + trim | **PASS, no assist** | 17.4 s, x -72 to 5 772. `d02_cp1.png`: Ella drawn (320,35), small figure near the top |
| CP1 to CP2, real keys + trim | FAIL, then assisted | stops at x 11 465 in all 3 runs (60 s each); `routeassist 2` placed her at x 12 720. Not proven a soft-lock: the walker keeps her low and a higher pass may exist (B8) |
| CP2 refuge | PASS | Purchase opens (`d03a_refuge_purchase.png`), Escape leaves; `d03_cp2.png` Ella drawn (320,234) |
| CP2 to CP3, real keys + trim | **PASS, no assist** | 20.1 s, x 12 778 to 19 218; CP3 refuge Purchase, Escape; `d04_cp3.png` Ella drawn (372,135) |
| CP3 to the Keeper handoff, real keys | **PASS, no assist** | 1.3 s; encounter active |
| Keeper fight | PASS flow, **FAIL picture** | `d05_keeper_handoff.png`: **Keeper offscreen (-5 600,145)**, Ella offscreen (514,-46) above the top. The Keeper spawns at the arena's anchor near x -720 while the camera follows Ella at x 19 800 (B5) |
| Wings to clock to the win | PASS (assisted) | 490 part hits, 44.8 s; 3 LevelUp cards closed by Enter |
| Director's Cut story, credits | PASS | "The owl's pursuit ends. He goes back ..." (`d07_story_text.png`); Credits after 12.1 s (`d08_credits.png`) |
| Journey Complete, mouse: Main Menu | PASS | Statistics after 20.8 s (`d09_after_credits.png`), Main Menu to the Start screen (`d10_back_at_start.png`) |
Mill: not in any run, by D-new-mill-in-route (open with Josh); not a fail. Start Game skipping the route: GDD FLOW-02; not a fail.

## Visibility per gameplay capture (measured; 640x360)
| Capture | Ella | Arena | Keeper |
|---|---|---|---|
| lose 03, 03b, 05, 05b; win w01; pause p04 | drawn, top edge (128,15), tiny | drawn | placeholder box, drawn (flat colour) |
| win w02 | drawn (155,291) | drawn | placeholder, drawn |
| dc d01 route start | **offscreen left** | drawn | absent (correct) |
| dc d01b after 8 s of rising | **offscreen top** | drawn | absent |
| dc d02 CP1 / d03 CP2 / d04 CP3 | drawn (320,35) / (320,234) / (372,135) | offscreen (route scrolls away from the arena: expected) | absent (correct) |
| dc d05 Keeper fight | **offscreen top** | offscreen | **offscreen** |

## Blockers (ID, owner lane)
- **B5 (Director's Cut Keeper off-screen), levelchunks + keeper**: `UEncounterDirectorSubsystem::SpawnKeeper` uses
  `Arena->GetKeeperAnchorLocation()` (arena near x -720); the handoff fires at `LevelPlan::KeeperHandoffX()` (x 19 777) and the
  camera stays on Ella. The whole Director's Cut fight is unseen. Needs the arena/anchor moved to the route end at handoff, or the
  camera handed to the arena. Lead decides which lane.
- **B6 (Ella off-screen at route start), levelchunks**: `CheckpointStandLocation(0)` is x -720; the scrolling camera clamps at
  route start, so Ella projects at x -240 px. She walks into view after about 1 s of input.
- **B7 (no ceiling on the route), move / levelchunks**: with nothing held Ella rises without limit on the route (z 14 962 after
  60 s); in Start Game the arena stops her at z 1 036. Also at the Keeper handoff she sits above the picture.
- **B8 (route stall at x 11 465), levelchunks**: the real-key walker stops there every run between CP1 and CP2. Not proven a
  soft-lock; needs one human try or a test that walks it.
- **B9 (Purchase Done hidden), progression / artui**: at 640x360 the Done button draws under the purchase panel; a mouse click
  lands on `SBorder` and nothing happens (`d00_purchase.png`). Escape and Enter still leave. Other sizes not checked.
- **B10 (Keeper look), artkeeper**: cream box + lilac cube placeholder in every Start Game fight shot; fix queued, not on main.
- Minor, not traced: Journey Complete shows "Shots fired 0" after ~45 s of J held (storyflow / progression statistics).
- Minor: Ella sits at the top edge in Start Game (projected y 15 at the ceiling); small at 640x360 (screenfix follow-up).
- Closed this run: B2 (black gameplay, screenfix), B3 (Settings picture + Escape, settings2), WIN floor (move). B1 is
  workbench-only (sound label overlay; the hook still sets it click-through).
