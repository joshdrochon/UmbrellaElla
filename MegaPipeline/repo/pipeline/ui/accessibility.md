# UI and accessibility rules (THE LAST HOUR)

> GDD SH1.0 note (D-new-gdd-sh10): lines on this page that still describe the GDD 1.3 encounter (one owl bolt, the front shield, the 90 s survival timer, wear stages, the 1.3 QA-01..QA-28 tests) are history. The current design is `docs/gdd/GDD-SH1.0.md` and `docs/feature-manifest.json`, which win; the owning role re-files this page against the SH1.0 Rule IDs on its next card.


Loaded on demand by the UI and UX role card (`pipeline/roles/ui-ux.md`) and by any card that adds a screen,
a HUD element, a setting, a colour-coded state or a critical sound. Game: single-screen survival against the
clockwork owl (GDD 1.3). Thresholds live in `tools/ui_check.py`; this file says why and who.

`[VERIFY]` = needs the 5.8.4 engine to confirm the API or setting name. No engine was available when this was written.

## 1. Gates you can run now (no engine)

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

### Capture inputs
- Captures: 1920x1080 PNG from a Development package or Standalone, via the eval cameras (`pipeline/unreal/commands-and-packaging.md`).
- `boxes.json`: list of `{"name", "x", "y", "w", "h", "kind": "text"|"object", "colour": "#rrggbb", "px", "bold", "hud", "backing", "outline"}`.
  `colour` is the glyph or object fill from the style. The check also measures the glyph from the capture (the darkest or lightest 1% of the box,
  on the side the declared colour is on) and uses whichever of the two gives lower contrast. A tint or opacity the style hides is caught.
  `px` is the glyph cap height in the capture. Pad each box at least 3 px so it holds background and the outline.
  The contrast is taken against the worst 5% of background pixels in the box, so it works for dark ink on light paper and for light text on dark sky.
  For `layout`, draw each text box on the widget's bounds, so a clipped label shows as glyph pixels on the box edge.
- `swatches.json`: list of `{"group", "swatches": [{"name", "x", "y", "w", "h"}]}`.
- Flash frames: `ffmpeg -i clip.mp4 -vf fps=30,scale=480:270 frames/%04d.png`. Small frames keep the check under a minute.

## 2. Rules that need the engine (owner writes the world test)

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

## 3. Rules without a number (review checklist for the UI and UX reviewer)
- All words are live UMG text from the string table, except the logo.
- The body font in `text-styles.csv` (U14) is a plain sans-serif with a provenance row.
- Instructions in sentence case. Never all caps over 2 words.
- Each colour-coded state also differs in shape, icon, label or motion (`signals.json`).
- Timing is never told by music alone (GDD section 7). The end is shown by the background motif and the end-trigger visual.
- Health is a small diegetic indicator plus the hit sound, never colour alone.
- Fail card says why you failed in words ("Hit by a bolt", "Fell out of the sky").
- `WBP_*` has no property bindings and no Event Tick. Proof: a screenshot of each widget's Bindings panel (empty) and its Event Graph (no Event Tick node) pasted in the PR. [VERIFY: an editor-utility dump that `ui_check widgets` can read would replace the screenshot; needs the engine]
- Every menu action is one key. No chords (two keys at once). No gameplay input needs more than 2 presses per second.

## 4. UIFLOW record line
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

## 5. Jam cards the UI gates need
`ui_check ci --release` fails until these exist: Day-0 cards 0.20 (strings, styles, DPI), 0.21 (menu and settings C++,
Gameplay Dev), 0.21b (menu layouts, Integrator) and 0.22 (capture boxes) in `pipeline/day0-cards.md`.

The G2-G4 gate records paste `ui_check ci --release`; G1 (first playable, no player screens yet, GDD SH1.0 section 11) pastes
plain `ui_check ci`. Boxes cost time and move with the widgets, so they are phased. G2: HUD and pause (card 0.22). G3: title, settings,
Survived and fail at 1.0 and 2.0 (a UI and UX card filed after G2). A widget move on a covered screen redraws its boxes in the same PR.

## 6. Who runs what
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
