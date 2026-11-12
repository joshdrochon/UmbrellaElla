> Generated from `pipeline/ui/accessibility.md`, `pipeline/ui/menus.md`, `pipeline/ui/signals.json`, `tools/ui_check.py` at `a11903f` — edit the sources, not this file.
> Rebuild: `python3 tools/export_package.py`. Check: `python3 tools/export_package.py --check`.

# UI UX Pipeline

A readable copy for people. Agents load these rules from the repo paths listed below.

## About this pipeline

- **Purpose:** Menus, prompts and the basic accessibility tier, each rule with a command and a threshold.
- **Owner:** UI and UX role.
- **Inputs:** The GDD UI needs, the art bible, the feel signals.
- **Outputs:** UI art, the UI string text, UI review verdicts.
- **Gates:** `ui_check.py ci` in CI; `ui_check.py ci --release` at each gate.

## Built from

- Rules: `pipeline/ui/accessibility.md`, `pipeline/ui/menus.md`, `pipeline/ui/signals.json`
- Commands and checks: `tools/ui_check.py`

## Rules

### `pipeline/ui/accessibility.md`

#### UI and accessibility rules (THE LAST HOUR)

> GDD SH1.0 note (D-new-gdd-sh10): lines on this page that still describe the GDD 1.3 encounter (one owl bolt, the front shield, the 90 s survival timer, wear stages, the 1.3 QA-01..QA-28 tests) are history. The current design is `docs/gdd/GDD-SH1.0.md` and `docs/feature-manifest.json`, which win; the owning role re-files this page against the SH1.0 Rule IDs on its next card.


Loaded on demand by the UI and UX role card (`pipeline/roles/ui-ux.md`) and by any card that adds a screen,
a HUD element, a setting, a colour-coded state or a critical sound. Game: single-screen survival against the
clockwork owl (GDD 1.3). Thresholds live in `tools/ui_check.py`; this file says why and who.

`[VERIFY]` = needs the 5.8.4 engine to confirm the API or setting name. No engine was available when this was written.

##### 1. Gates you can run now (no engine)

| # | Rule | Command | Threshold | Owner | Done when |
|---|---|---|---|---|---|
| U1 | Text is big enough | `ui_check.py contrast <capture> --boxes <boxes.json>` (also `text-floor --res WxH`) | glyph height >= 18 px at 1080p, scaled by height (12 px at 720p, 36 px at 2160p) | UI and UX | every text box on the title, pause, settings, HUD and end cards passes |
| U2 | Text and HUD contrast | same command | worst 5% of background: text 4.5:1, large text (>= 24 px, or >= 18.66 px bold) 3:1, objects 3:1 | UI and UX | same captures pass |
| U3 | HUD text over the sky has a backing | same command (`"hud": true` needs `"backing": "plate"` or `"outline"`) | outline: >= 80% of glyph edge pixels have an outline pixel within 2 px (calibrated on test fixtures: drawn outline 100%, none on half-dark sky ~50%, none on paper 0%) [VERIFY on the first real HUD capture] | UI and UX | every HUD box declares and passes |
| U4 | Gameplay objects read against the paper | same command, `"kind": "object"` boxes on bolts, arcs, the hero silhouette, the umbrella canopy and the gust-zone flow lines | 3:1 | Art Director | `CAM_Eval_Stress` capture passes with all five box types present |
| U5 | Colour-coded states differ without colour | `ui_check.py grayscale <capture> --swatches <swatches.json>` | L* gap >= 20 between any two states of a group | Art Director | umbrella tiers group and bolt-vs-arc group pass on the swatch capture |
| U6 | Flashes | `ui_check.py flashes <frame folder> --fps 30` | <= 3 general and <= 2 red flashes in any 1 s; no frame >= 20% saturated red; >= 10 s of footage | UI and UX (QA runs it) | the busiest 10 s of the gameplay video passes |
| U7 | Sound has a visual twin, colour has a second signal | `ui_check.py signals` (reads `pipeline/ui/signals.json`) | no blank or TBD cell; second signal is not only a colour; `sound_id` is blank only when the sound is "none"; each `sound_id` is a row in `pipeline/audio/sound-list.csv`; two events share a `sound_id` only with a `shared_ok` reason (distinct sound per key event); a row marked `"sound_status": "requested"` prints PENDING until the audio lane adds its id, and fails `ci --release` | UI and UX | passes in CI; no PENDING line at G2 |
| U8 | Words are live text in a string table | `ui_check.py strings` (reads `Content/UmbrellaElla/UI/ST_UI.csv`) | no all-caps over 2 words; hints, prompts, settings in sentence case; assist labels never judge the player; `Prompt.*` uses `{Key}` and never names a key; `Hint.*`, `Instr.*`, `Settings.*`: <= 15 words per sentence, and in rows of 5+ words <= 10% of words over 3 syllables | UI and UX | passes in CI |
| U9 | UI scales with the screen | `ui_check.py config` | `UIScaleRule=ShortestSide` under `[/Script/Engine.UserInterfaceSettings]` [VERIFY key] | Technical Director | passes in CI |
| U10 | HUD updates from events | `ui_check.py widgets` | no `NativeTick` in a `UUserWidget` | Dev Lead | passes in CI |
| U12 | Shake stays small and can be turned off | `ui_check.py shake` (reads `pipeline/feel/feel.json`) | `shake_off_option: true`; every `kind: shake` has `amp_pct_h` <= 2.5 | Game Designer (feel.json) | passes in CI |
| U14 | Body text is a plain sans-serif; blackletter only for titles and the logo | `ui_check.py fonts` (reads `Content/UmbrellaElla/UI/text-styles.csv`: `Style,Font,Use`, one row per text style, `Use` = `title` or `body`) | every body style uses one font; that font is never a title font and never a blackletter face. The reviewer checks the row matches the style asset's Font field and the font has a provenance row. [VERIFY: an editor-utility export of the styles would replace hand entry] | Integrator (writes the rows with the styles) | passes in CI |
| U13 | Text scale 2.0 does not clip (E9) | `ui_check.py layout <capture at 2.0> --boxes <boxes at 2.0> --scale 2`, then `contrast` on the same pair | no text box within 4 px (at 1080p) of the screen edge; no two text boxes overlap; no glyph pixel on its box edge; every text `px` >= 2 x floor (36 px at 1080p) | UI and UX (QA captures) | the title, pause, settings, HUD and both end-card captures at 2.0 pass |
| U15 | A player can always quit (no Alt+F4) | `ui_check.py quit` (also in `ci`) | string table has `Title.Quit` and `Pause.QuitToTitle`; game code outside `Smoke/` and `Tests/` calls `QuitGame` or `RequestExit` | Gameplay Dev (card 0.21) | passes in CI; G1 already needs the code half |
| U11 | UI flow works in the package | `ui_check.py flow-check <record> --commit <sha>` | every UIFLOW field `pass`; `play-presses` <= 1 | QA and Build | a gate record passes |

`python3 tools/ui_check.py ci` runs U7–U10, U12, U14 and U15 and skips inputs that do not exist yet. It is green today.
`python3 tools/ui_check.py ci --release` fails on any skipped input or PENDING sound. It is part of every G-gate (the `Gate checks` line in `pipeline/templates/gate-record.md`).
CI runs `python3 tools/ui_check.py ci || [ $? -eq 2 ]` on every PR (requested in `.github/workflows/pipeline-checks.yml`).

###### Capture inputs
- Captures: 1920x1080 PNG from a Development package or Standalone, via the eval cameras (`pipeline/unreal/commands-and-packaging.md`).
- `boxes.json`: list of `{"name", "x", "y", "w", "h", "kind": "text"|"object", "colour": "#rrggbb", "px", "bold", "hud", "backing", "outline"}`.
  `colour` is the glyph or object fill from the style. The check also measures the glyph from the capture (the darkest or lightest 1% of the box,
  on the side the declared colour is on) and uses whichever of the two gives lower contrast. A tint or opacity the style hides is caught.
  `px` is the glyph cap height in the capture. Pad each box at least 3 px so it holds background and the outline.
  The contrast is taken against the worst 5% of background pixels in the box, so it works for dark ink on light paper and for light text on dark sky.
  For `layout`, draw each text box on the widget's bounds, so a clipped label shows as glyph pixels on the box edge.
- `swatches.json`: list of `{"group", "swatches": [{"name", "x", "y", "w", "h"}]}`.
- Flash frames: `ffmpeg -i clip.mp4 -vf fps=30,scale=480:270 frames/%04d.png`. Small frames keep the check under a minute.

##### 2. Rules that need the engine (owner writes the world test)

Each test name is listed by `python3 tools/ui_check.py tests` and passed to `check_automation_report.py --require`.

| # | Rule | Test (`UmbrellaElla.UI.World.*`) | Owner | Done when |
|---|---|---|---|---|
| E1 | Hold is the default for ATTACK and SHIELD (GDD SH1.0 MOVE-04: hold left/right mouse or R2/L2; release both = UP_OPEN). A Toggle setting for each is open (`docs/gdd/questions-1.3.md` Q8, D18); if built, it lives in the settings menu, is saved between sessions, and SHIELD still wins. | `HoldToggleSetting`: set Toggle, press and release `IA_Shield`, assert SHIELD_DESCENT; press again, assert UP_OPEN; set Hold, release, assert UP_OPEN | Gameplay Dev | test passes |
| E2 | All actions remap, including Pause, on keyboard and mouse and on the controller (required, team meeting 11 Nov: `RemapUpdatesPrompt` and `RemapGamepadUpdatesPrompt` are P0, UIFLOW `remap` and `remap-gamepad`), through Enhanced Input user settings. [VERIFY `UEnhancedInputUserSettings` on 5.8.4] Prompts read the current binding; no key name is baked into art or text. Actions (GDD SH1.0 MOVE-04): `IA_Move`, `IA_Attack`, `IA_Shield`, `IA_Pause`, `IA_Retry` (`pipeline/unreal/cpp-rules.md` rule 6). | `RemapUpdatesPrompt`: remap `IA_Attack`, `IA_Shield`, `IA_Pause` and `IA_Move` [VERIFY names once card 0.3 lands]; assert the HUD prompt and the pause-screen controls list both show each new key, and the new Pause key opens pause | Gameplay Dev | test passes; UIFLOW `remap` passes |
| E3 | Music and SFX sliders, saved in `GameUserSettings`. | `VolumeSlidersSetSoundClass`: set SFX to 0.5, assert the SFX sound class volume is 0.5 [VERIFY sound mix API] | Gameplay Dev | test passes |
| E4 | Game speed 100 / 85 / 70% through global time dilation. Labels say what changes ("Game speed 85%"), never "Easy". | `GameSpeedScalesTimer`: set 70%, run 2 s of game time, assert the encounter timer moved 0.7x real time (±2%) | Gameplay Dev | test passes |
| E4b | Separate sliders: umbrella wear 100 / 50%, projectile speed 100 / 80%. | `AssistSlidersScale`: set wear 50%, apply one hit, assert integrity lost is 0.5x the 100% loss (±2%); set projectile speed 80%, spawn one bolt, assert its speed is 0.8x the 100% speed (±2%) | Gameplay Dev | test passes |
| E5 | Every setting survives a restart, text size included. A garbage or old `GameUserSettings.ini` boots to defaults (QA `settings` step). | `SettingsPersist`: write each setting, reload, assert equal | Gameplay Dev | test passes |
| E6 | Pause works during the end event. Nothing lethal runs after the end trigger. | `PauseDuringEndEvent`: trigger the end, pause, assert time stopped and no projectile alive | Gameplay Dev | test passes |
| E7 | The Survived card plays a sound, shows one text line and waits for input before it moves on. | `SurvivedCardWaitsForInput`: reach Survived, wait 5 s, assert the card is still up | Gameplay Dev | test passes |
| E8 | Shake sizes come from `pipeline/feel/feel.json` (game feel lane). Screen shake defaults to On at those sizes (largest 2.5% of screen height, U12). The 2.5% limit is untested on people, so the P1 playtest record asks every player "Did the shake bother you? yes / no"; one "yes" opens a Game Designer card to lower it or default it Off. The Off setting zeroes every shake and stops background motion. The settings label says both: "Screen shake and background motion". Every moving background actor (clouds, motif, parallax) carries the actor tag `BackgroundMotion`; this is how the test finds them, so it needs no layer names. | `ShakeOffZeroesShake`: set Off, apply a player hit, assert camera offset stays 0; assert at least 1 actor has the tag `BackgroundMotion` and every tagged actor's scroll speed is 0 | Gameplay Dev (test), Art Director (tags in the art bible) | test passes |
| E9 | Text scale 2.0 does not clip. QA gets 2.0 by setting Text size 200% (E10) in the package, then captures each screen. | U13 `layout --scale 2` on each screen captured at 2.0, plus UIFLOW `text-scale-2` | QA and Build | U13 passes on the screens due at that gate (section 5) and UIFLOW passes |
| E11 | The mouse works in menus. On title, pause, settings, Survived and fail the cursor is visible and every button clicks (hover moves focus, the click fires on release). In play the cursor is hidden and captured to the window, so left and right mouse (GDD SH1.0 MOVE-04) never click the desktop. It comes back on pause and on the end cards. | `CursorShownInMenusHiddenInPlay`: open each menu, assert `bShowMouseCursor` is true and the input mode lets UI take the mouse; enter play, assert it is false, the mouse is captured, and a left click fires `IA_Attack`; pause, assert the cursor is back [VERIFY input mode API on 5.8.4] | Gameplay Dev | test passes; UIFLOW `mouse-menus` and `mouse-play` pass |
| E12 | Quit works. Title Quit closes the game with exit code 0; pause Quit to title reaches the title. | `QuitButtonsExit`: press title Quit, assert the quit request was made; press pause Quit to title, assert the title screen shows | Gameplay Dev | test passes; UIFLOW `quit-title` and `quit-pause` pass |
| E10 | Players can resize text: settings row "Text size 100 / 150 / 200%". It sets the UI application scale on top of the Shortest Side DPI curve. [VERIFY on 5.8.4: `FSlateApplication::Get().SetApplicationScale` or `UUserInterfaceSettings::ApplicationScale` at runtime; cite the header] | `TextSizeSettingScalesUI`: set 200%, assert the application scale reads 2.0 and a HUD text widget's desired height is 2x (±2%) its 100% height; set 100%, assert 1.0 | Gameplay Dev | test passes and is in `SettingsPersist` |

##### 3. Rules without a number (review checklist for the UI and UX reviewer)
- All words are live UMG text from the string table, except the logo.
- The body font in `text-styles.csv` (U14) is a plain sans-serif with a provenance row.
- Instructions in sentence case. Never all caps over 2 words.
- Each colour-coded state also differs in shape, icon, label or motion (`signals.json`).
- Timing is never told by music alone (GDD section 7). The end is shown by the background motif and the end-trigger visual.
- Health is a small diegetic indicator plus the hit sound, never colour alone.
- Fail card says why you failed in words ("Hit by a bolt", "Fell out of the sky").
- `WBP_*` has no property bindings and no Event Tick. Proof: a screenshot of each widget's Bindings panel (empty) and its Event Graph (no Event Tick node) pasted in the PR. [VERIFY: an editor-utility dump that `ui_check widgets` can read would replace the screenshot; needs the engine]
- Every menu action is one key. No chords (two keys at once). No gameplay input needs more than 2 presses per second.

##### 4. UIFLOW record line
QA plays the Development package with the keyboard only, then once more with the mouse in the menus, and appends:

```
UIFLOW | commit=<sha> | title-play pass | pause pass | pause-end-event pass | survived-card pass | fail-card pass | restart pass | quit-title pass | quit-pause pass | keyboard-only pass | menu-nav-keyboard pass | remap pass | release-activate pass | text-scale-2 pass | prompts-consistent pass | mouse-menus pass | mouse-play pass | play-presses 1
```

- `title-play`: one press of Play reaches control. `play-presses` counts the presses.
- `pause`: Esc and P pause in play; the pause screen shows the controls.
- `pause-end-event`: pause during the owl's departure; resume finishes the event.
- `survived-card` / `fail-card`: card shows, plays its sound, waits for input.
- `restart`: from the fail card back to control in under 3 s, no reload of the title.
- `keyboard-only`: the whole flow with the keyboard alone, every action one key, no chord, no mashing.
- `menu-nav-keyboard`: every menu reached and left with arrows, Enter and Esc; focus wraps (`pipeline/ui/menus.md`).
- `remap`: in settings, remap Umbrella, Pause and one move key. The HUD prompt and the pause controls list show the new keys. The new Pause key pauses; the old one does not.
- `release-activate`: hold Enter from gameplay into the pause screen, then let go: no button fires on the press. Click a button, drag off it, release: it does not fire. [VERIFY the UButton Press Method setting; once known, a `widgets` grep replaces this field]
- `text-scale-2`: see E9 and U13.
- `prompts-consistent`: on title, pause, settings, Survived and fail, the Confirm and Back prompts sit bottom-right, Confirm first, and focus moves top to bottom. One screen different fails.
- `quit-title`: title Quit closes the game, exit code 0, no Alt+F4. `quit-pause`: pause Quit to title reaches the title.
- `mouse-menus`: on title, pause, settings, Survived and fail the cursor shows, hover highlights, and a click works every button.
- `mouse-play`: in play the cursor is hidden and stays in the window; left and right mouse attack and shield. Pause brings the cursor back.
A field that was not tested is written `not run`, which fails. A blank field fails.

##### 5. Jam cards the UI gates need
`ui_check ci --release` fails until these exist: Day-0 cards 0.20 (strings, styles, DPI), 0.21 (menu and settings C++,
Gameplay Dev), 0.21b (menu layouts, Integrator) and 0.22 (capture boxes) in `pipeline/day0-cards.md`.

The G2-G4 gate records paste `ui_check ci --release`; G1 (first playable, no player screens yet, GDD SH1.0 section 11) pastes
plain `ui_check ci`. Boxes cost time and move with the widgets, so they are phased. G2: HUD and pause (card 0.22). G3: title, settings,
Survived and fail at 1.0 and 2.0 (a UI and UX card filed after G2). A widget move on a covered screen redraws its boxes in the same PR.

##### 6. Who runs what
Each owner's role card names its checks (requested). Until it does, cite this table on the task card.

| Owner | Runs |
|---|---|
| QA and Build | UIFLOW + `flow-check` (append the line to `Saved/Logs/pipeline/daily-records.txt`; `--gate-record` re-checks it from G2); `flashes`; 2.0 captures for `layout`; `check_automation_report.py --require $(python3 tools/ui_check.py tests)`; `ci --release` at each G-gate |
| Gameplay Dev | the `UmbrellaElla.UI.World.*` tests that `ui_check.py tests` prints (P0 on card 0.21; a P1/P2 setting's card asks for its tier) |
| Art Director | `contrast` (objects) and `grayscale` on `CAM_Eval_Stress` |
| Technical Director | `ui_check.py config`, `strings` |
| Integrator | `ui_check.py fonts` when a text style changes |
| Dev Lead | `ui_check.py widgets`; Bindings screenshot on `WBP_*` PRs |
| Game Designer | `ui_check.py shake`; the P1 shake question (E8) |

### `pipeline/ui/menus.md`

#### Menu checklist (plain UMG)

Loaded on demand for any card that adds or changes the title, pause, settings, Survived or fail screen.
The UI and UX reviewer ticks each line against the packaged build. QA proves it with the UIFLOW `menu-nav-keyboard` field
(`pipeline/ui/accessibility.md`, section 4).
Menus are plain UMG `UUserWidget`s. No CommonUI plugin (D-new-umg): a few small screens do not need it.

Words: every string comes from the Story role's `pipeline/story/lines.csv` (same id as the `ST_UI.csv` key); `python3 tools/story_check.py --table Content/UmbrellaElla/UI/ST_UI.csv` and `--scan` print PASS.

Screens: title (Start Game, Start Director's Cut; FLOW-34) → tutorial (first start, Pause then Skip; FLOW-03) → play → pause (Continue, Settings, Quit; FLOW-35) → settings (Sound, Controller, Credits; Game Options in Director's Cut only) → win ending and credits (FLOW-04) → statistics (Director's Cut, FLOW-49) → fail card → restart → quit.

1. Title: Play has focus when the screen opens. One press of Confirm starts the encounter (`play-presses 1`).
2. Focus wraps top to bottom and bottom to top on the title, pause and settings screens. Set the first and last button's Navigation to Wrap. [VERIFY UMG Wrap navigation rule on 5.8.4]
3. Focus order is top to bottom, then left to right, the same on every screen. Nothing reachable only by mouse.
3b. The mouse works too. On title, pause, settings, Survived and fail the cursor is visible and every button clicks. In play the cursor is hidden and captured. It returns on pause and on the end cards. UIFLOW `mouse-menus` and `mouse-play` prove it (E11).
4. Confirm and Back prompts sit bottom-right, in that order, on every screen. Labels come from the current binding (`Prompt.*` strings). UIFLOW `prompts-consistent` proves 3 and 4.
5. Buttons activate on release, not on press, so a held key from gameplay does not click a menu button. UIFLOW `release-activate` proves it. Set each `UButton` Press Method to Button Release. [VERIFY UButton Press Method on 5.8.4]
6. Back always closes the current screen. Esc and P both open and close pause.
6b. Quit is always there: title has Quit (string `Title.Quit`, closes the game, exit 0), pause has Quit to title (`Pause.QuitToTitle`), the Survived card has Quit. Nobody needs Alt+F4. `ui_check.py quit` and UIFLOW `quit-title` / `quit-pause` prove it.
7. The pause screen shows the controls (from the bindings) and has Continue, Settings and Quit (GDD SH1.0 FLOW-35), over the living ticking-clock background while gameplay stays frozen; during a tutorial it also has Skip (FLOW-03).
8. Settings rows: Sound (Master Volume, Sound Effects and Music sliders 0-100, FLOW-37), Controller (remap keyboard, mouse and controller, MOVE-17; UIFLOW `remap`), Credits (FLOW-39), Game Options (Director's Cut only, FLOW-38), Text size (100-200%, FLOW-45) and Reduced motion (FLOW-45). Each submenu has Back and Save (FLOW-40); dirty Back offers Save, Discard or Keep Editing.
9. Menus use `IMC_Menu` so gameplay input never fires under a menu (`pipeline/unreal/cpp-rules.md`, input rule).
10. The Survived and fail cards wait for input. No auto-advance.
11. Every menu action is one key. No chords. No gameplay input needs more than 2 presses per second (Xbox XAG 107). UIFLOW `keyboard-only` covers it.
12. `WBP_*` widgets have no property bindings and no Event Tick; the HUD updates from events. Paste the empty Bindings panel and the Event Graph in the PR. [VERIFY]

##### Menu look (the menu style bar, Josh 11 Nov)
Every menu screen and transition (title, pause, settings, Survived, fail) has the feel of a paper cut-out,
shadow-puppet animated end-credits sequence (the target is the 2004 film "Lemony Snicket's A Series of Unfortunate
Events"), made in our brand and never deviating from our art: the key art, `style.json`, the etched paper and Ricky's
references. Written target (`pipeline/art/references.json` `menu-style-bar`, kind "described"; no frame of the film
is stored or copied: copyright, Official Rules §7(h), §15(d)):
- layered paper cut-out silhouettes in near-black ink; three or more parallax depth planes;
- hand-made, stop-motion-like motion: stepped timing, slight jitter, never smooth tweened easing;
- ink-and-paper textures on every surface; gothic storybook typography; our palette only;
- a painted vignette in the menu art (the post-process vignette stays off, `pipeline/art/art-bible.md`).

##### Title screen target (Josh, 11 Nov; D-new-title-screen)
Card 0.21b's title screen builds to Ricky's title image: `pipeline/art/references.json` `title-screen`
(`pipeline/art/reference/discord/20261112-0443_Ricky_title-screen.png`, reference only, never shipped). Until the
team decides D-new-title-screen, the title screen follows this image and the other menus keep the menu style bar below.
- Scene: a painted, misty sepia frame of floating islands with a cottage and a windmill, filling the screen.
- A clock face in the top-left corner.
- Title lockup: large ornate serif lettering with a clock-hand flourish, in the upper part of the frame where the
  image puts it. The words come from the Story role's string table, never from the image: the image says
  "UMBRELLA GIRL", the game's title is still open (D-new-title-screen, D-new-story-canon).
- Menu below the title, in the image's place and lettering: START GAME (has focus when the screen opens, rule 1),
  then DIRECTOR'S CUT. Quit stays on the title (rule 6b, `Title.Quit`) as the last item in the same style. The
  button text comes from the Story role's string table like every other string.
- Judged as piece `menu-screen` (its refs now include `title-screen`), plus the deterministic checks below.

Card 0.21b's screens go through the art loop (piece `menu-screen`): blind critic rounds against the brand references
with this written target, until the critic cannot pick them over ours, plus the deterministic checks
(`art_check.py`, `screen_check.py`, `art_ref_check.py`). Same enforcement as other art (`check_pr.py` artref, artloop).

##### Required screens and settings (team meeting, 11 Nov)
- Menus keep the current structure and text sizes. Font and colours come from the art bible (gothic storybook type,
  our palette; none is approved by name, so the builder picks from the art bible and the art loop's critic judges).
- Settings has remapping for keyboard and mouse AND for the controller (`pipeline/ui/accessibility.md` E2):
  `UmbrellaElla.UI.World.RemapUpdatesPrompt` and `UmbrellaElla.UI.World.RemapGamepadUpdatesPrompt` are P0, and the
  UIFLOW line has `remap` and `remap-gamepad` pass.
- Tutorial: every control is shown with a proper control icon, keyboard and gamepad glyphs drawn in our etched style,
  that follows the current binding. No placeholder dots or boxes: a 1080p capture of each tutorial screen passes
  `python3 tools/screen_check.py --strict` (small flat dots and boxes fail). `UmbrellaElla.UI.World.TutorialShowsControlGlyphs`
  checks every prompt has a glyph for the active device.
- The tutorial can be skipped and the skip works: `UmbrellaElla.UI.World.TutorialSkipReachesPlay`, and UIFLOW
  `tutorial-skip` pass (`tools/ui_check.py flow-check`).
- 16:9 with bars on any other ratio (`pipeline/unreal-rules.md` Display); 60 fps target (the smoke's 1% low is at
  least 55); a missing or garbage `GameUserSettings.ini` falls back to 1920x1080, checked by the daily `settings`
  step (`SMOKE_EXPECT_RES=1920x1080`).

### `pipeline/ui/signals.json`

```json
{
 "note": "Every critical event: one sound AND one visual, and a second signal when it is colour-coded. Checked by: python3 tools/ui_check.py signals. Values are proposals from the GDD draft (6 Nov 2026); a design change edits the row, never deletes it. Owners: Asset Specialist makes the sound/visual, Art Director passes the grayscale capture, UI and UX keeps this file. sound_id names a row in pipeline/audio/sound-list.csv. A blank sound_id fails unless the sound is 'none'. Two events share a sound_id only with a shared_ok reason (key events need distinct sounds). sound_status 'requested' = asked of the audio lane: ci prints PENDING until the row exists, and ci --release fails on it. Drop the flag once the row lands. progress-motif needs a second signal that is not colour even if its colour cell is blank.",
 "events": [
  {
   "event": "owl-windup",
   "colour": "amber",
   "second_signal": "clock hands spin and owl leans back (pose change)",
   "sound": "clockwork wind-up ratchet",
   "visual": "amber clock flash on the owl chest, max 3 per second",
   "owner": "Asset Specialist",
   "sound_id": "ClockBeat"
  },
  {
   "event": "gust-incoming",
   "colour": "",
   "second_signal": "",
   "sound": "rising wind whoosh",
   "visual": "wing pose plus flow lines filling the gust rectangle before it is live",
   "owner": "Asset Specialist",
   "sound_id": "GustWindup"
  },
  {
   "event": "bolt-launch",
   "colour": "amber",
   "second_signal": "straight bolt shape with clock-gear head",
   "sound": "short metallic tick-launch",
   "visual": "bolt sprite leaves the clock",
   "owner": "Asset Specialist",
   "sound_id": "OwlBoltLaunch"
  },
  {
   "event": "arc-launch",
   "colour": "red",
   "second_signal": "curved trail and returning arrowhead shape, not the straight bolt",
   "sound": "lower swoop distinct from bolt launch",
   "visual": "red arc trail",
   "owner": "Asset Specialist",
   "sound_id": "CastWarning"
  },
  {
   "event": "shield-catch",
   "colour": "",
   "second_signal": "",
   "sound": "soft canvas thump, not the hurt sound",
   "visual": "catch flash on the front of the umbrella; the bolt vanishes with no hit-stop and no health change (GDD SH1.0 SURV-05, FLOW-33, 7A)",
   "owner": "Asset Specialist",
   "sound_id": "ShieldCatch"
  },
  {
   "event": "shield-heal",
   "colour": "",
   "second_signal": "",
   "sound": "rising mend chime after the catch",
   "visual": "umbrella wear steps back toward intact (+20 HP); never shown on a catch during the 2 s cooldown",
   "owner": "Asset Specialist",
   "sound_id": "ShieldHeal"
  },
  {
   "event": "wind-enter",
   "colour": "",
   "second_signal": "",
   "sound": "short wind lift whoosh",
   "visual": "flow lines always mark the safe wind zone boundary; they brighten while the player is inside (WIND-01)",
   "owner": "Asset Specialist",
   "sound_id": "GustCatch"
  },
  {
   "event": "player-hit",
   "colour": "",
   "second_signal": "",
   "sound": "hurt sound",
   "visual": "hit-stop, sprite blink at most 3 per second, one health pip removed",
   "owner": "Asset Specialist",
   "sound_id": "PlayerHurt"
  },
  {
   "event": "low-health",
   "colour": "",
   "second_signal": "",
   "sound": "heartbeat or ticking layer under the music",
   "visual": "one health pip left, pip outline pulses",
   "owner": "Asset Specialist",
   "sound_id": "LowHealthLoop",
   "sound_status": "requested"
  },
  {
   "event": "umbrella-tear",
   "colour": "",
   "second_signal": "",
   "sound": "fabric rip",
   "visual": "new tear appears on the canopy",
   "owner": "Asset Specialist",
   "sound_id": "UmbrellaCreak"
  },
  {
   "event": "umbrella-intact",
   "colour": "sepia",
   "second_signal": "whole canopy, no holes",
   "sound": "none (steady state)",
   "visual": "tier 1 canopy texture",
   "owner": "Art Director",
   "sound_id": ""
  },
  {
   "event": "umbrella-damaged",
   "colour": "sepia",
   "second_signal": "two visible holes and a bent rib",
   "sound": "fabric rip when entering the tier",
   "visual": "tier 2 canopy texture",
   "owner": "Art Director",
   "sound_id": "UmbrellaCreak",
   "shared_ok": "entering tier 2 is the tear itself; the tier change and the tear are one moment, so one sound"
  },
  {
   "event": "umbrella-critical",
   "colour": "red",
   "second_signal": "canopy in tatters with exposed ribs and flapping strips",
   "sound": "fabric rip plus strained creak loop",
   "visual": "tier 3 canopy texture",
   "owner": "Art Director",
   "sound_id": "LowHealthLoop",
   "sound_status": "requested",
   "shared_ok": "GDD SH1.0 ANIM-04: the living critical state is the low-health state, one sound; the clock HUD is the primary health display (SURV-05)"
  },
  {
   "event": "end-trigger",
   "colour": "",
   "second_signal": "",
   "sound": "clock chime, threats stop",
   "visual": "owl pauses, background motif completes, projectiles fade",
   "owner": "Asset Specialist",
   "sound_id": "EndEvent"
  },
  {
   "event": "survived",
   "colour": "",
   "second_signal": "",
   "sound": "end sting",
   "visual": "Survived card with one text line; waits for input",
   "owner": "UI and UX",
   "sound_id": "SurvivedSting"
  },
  {
   "event": "progress-motif",
   "colour": "gold",
   "second_signal": "the motif shape fills one more segment at 25, 50, 75 and 100% of the hour",
   "sound": "music adds a layer at 25% and 70%",
   "visual": "background motif changes shape as the hour runs out (concept is GDD section 12 open; the row stays whichever is picked)",
   "owner": "Art Director",
   "sound_id": "MusicContest"
  },
  {
   "event": "clock-hit",
   "colour": "",
   "second_signal": "",
   "sound": "metal clank on the clock",
   "visual": "clock hands jolt and the current wind-up stops",
   "owner": "Asset Specialist",
   "sound_id": "HitClock"
  },
  {
   "event": "wing-hit",
   "colour": "",
   "second_signal": "",
   "sound": "metal clank on the wing",
   "visual": "a new tear on the wing overlay; the next gust shows fewer flow lines",
   "owner": "Asset Specialist",
   "sound_id": "HitWing"
  },
  {
   "event": "failed",
   "colour": "",
   "second_signal": "",
   "sound": "fail sting",
   "visual": "fail card with the failure cause in text and a retry prompt",
   "owner": "UI and UX",
   "sound_id": "FailSting",
   "sound_status": "requested"
  }
 ]
}
```

## Commands and checks

### `tools/ui_check.py`

Usage text from the file:

```text
UI, UX and accessibility gates for THE LAST HOUR. Stdlib only; runs locally and in CI.
Rules, owners and done-when for each check: pipeline/ui/accessibility.md. Role: pipeline/roles/ui-ux.md.

Subcommands (exit 0 = pass, 1 = fail, 2 = input missing or bad arguments):
  text-floor --res WxH            smallest allowed text height in px at that resolution (18 at 1080p, scaled by height)
  contrast CAPTURE --boxes F      WCAG contrast of each text/object box against the worst 5% of its background;
                                  the glyph colour is measured from the capture (the declared colour only picks
                                  the side); text under the size floor fails; HUD text needs a backing plate or an
                                  ink outline that rings the glyph edges
  layout CAPTURE --boxes F [--scale S]  text boxes are not cut by the screen edge, do not overlap, glyphs do not
                                  touch their box edge; with --scale, text is at least S x the size floor (text scale 2.0)
  grayscale CAPTURE --swatches F  colour-coded states (umbrella tiers, bolt vs arc) must differ in grayscale L*
  flashes FRAME_DIR --fps N       more than 3 general or 2 red flashes in any 1 s fails; a frame >= 20% saturated red fails
  strings [CSV]                   UI string table: no all-caps over 2 words, sentence-case hints, plain assist labels,
                                  prompts use a {key} placeholder (never a baked key name), plain reading level
  signals [JSON]                  every critical event has a sound AND a visual; every colour-coded state has a second signal;
                                  a sound_id is never blank (unless the sound is "none") and never shared without shared_ok;
                                  a row with "sound_status": "requested" whose id is not in the sound list yet is
                                  PENDING (a note), and fails with --release
  fonts [CSV]                     text styles: every body style uses one font, never a title (blackletter) font
  shake [JSON]                    pipeline/feel/feel.json: an off switch exists and no shake is over 2.5% of screen height
  flow-check LOG --commit SHA     UIFLOW line: title, pause (also during the end event), survived/fail card, restart, quits,
                                  keyboard-only, menu navigation, remap, release-activate, text scale 2.0
  quit                            a player can always quit (no Alt+F4): the string table has Title.Quit and Pause.QuitToTitle,
                                  and game code outside Smoke/ and Tests/ calls QuitGame or RequestExit (the Quit button)
  config [INI]                    DefaultEngine.ini uses the Shortest Side DPI rule
  widgets [SRC]                   no NativeTick in UUserWidget subclasses (HUD updates from events)
  tests [--tier P0,MVP8,P1,P2|all] print the required UI automation test names (for check_automation_report.py --require);
                                  default P0 only (card 0.21). A P1/P2 setting's own card asks for its tier
  ci [--release]                  signals + strings + fonts + config + widgets + shake + quit; inputs not created yet are
                                  skipped and listed (--release: a skipped input or a PENDING sound fails, for the G-gates)
```

Run in CI by:

- `.github/workflows/pipeline-checks.yml`: UI inputs that exist yet (UI and UX; skips inputs not created)

Tests: `tests/test_export_package.py`, `tests/test_feel_check.py`, `tests/test_final10_fixes.py`, `tests/test_honest_jam.py`, `tests/test_pipeline_check.py`, `tests/test_plan_checks.py`, `tests/test_ui_check.py`
