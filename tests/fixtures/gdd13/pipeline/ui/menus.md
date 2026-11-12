# Menu checklist (plain UMG)

Loaded on demand for any card that adds or changes the title, pause, settings, Survived or fail screen.
The UI and UX reviewer ticks each line against the packaged build. QA proves it with the UIFLOW `menu-nav-keyboard` field
(`pipeline/ui/accessibility.md`, section 4).
Menus are plain UMG `UUserWidget`s. No CommonUI plugin (D-new-umg): a few small screens do not need it.

Words: every string comes from the Story role's `pipeline/story/lines.csv` (same id as the `ST_UI.csv` key); `python3 tools/story_check.py --table Content/UmbrellaElla/UI/ST_UI.csv` and `--scan` print PASS.

Screens: title → play → pause (also during the end event) → settings → Survived or fail card → restart → quit.

1. Title: Play has focus when the screen opens. One press of Confirm starts the encounter (`play-presses 1`).
2. Focus wraps top to bottom and bottom to top on the title, pause and settings screens. Set the first and last button's Navigation to Wrap. [VERIFY UMG Wrap navigation rule on 5.8.4]
3. Focus order is top to bottom, then left to right, the same on every screen. Nothing reachable only by mouse.
3b. The mouse works too. On title, pause, settings, Survived and fail the cursor is visible and every button clicks. In play the cursor is hidden and captured. It returns on pause and on the end cards. UIFLOW `mouse-menus` and `mouse-play` prove it (E11).
4. Confirm and Back prompts sit bottom-right, in that order, on every screen. Labels come from the current binding (`Prompt.*` strings). UIFLOW `prompts-consistent` proves 3 and 4.
5. Buttons activate on release, not on press, so a held key from gameplay does not click a menu button. UIFLOW `release-activate` proves it. Set each `UButton` Press Method to Button Release. [VERIFY UButton Press Method on 5.8.4]
6. Back always closes the current screen. Esc and P both open and close pause.
6b. Quit is always there: title has Quit (string `Title.Quit`, closes the game, exit 0), pause has Quit to title (`Pause.QuitToTitle`), the Survived card has Quit. Nobody needs Alt+F4. `ui_check.py quit` and UIFLOW `quit-title` / `quit-pause` prove it.
7. The pause screen shows the controls (from the bindings) and has Resume, Settings, Restart, Quit to title.
8. Settings rows: Umbrella (Hold / Toggle), Remap controls (every action, Pause too; UIFLOW `remap`), Music and SFX (only if Day 3 has slack, D-new-audio-rules), Screen shake and background motion (On / Off), Text size (100 / 150 / 200%, E10), Game speed (100 / 85 / 70%, P1), Umbrella wear (100 / 50%, P2) and Projectile speed (100 / 80%, P2) (D-new-assist). Each saves at once.
9. Menus use `IMC_Menu` so gameplay input never fires under a menu (`pipeline/unreal/cpp-rules.md`, input rule).
10. The Survived and fail cards wait for input. No auto-advance.
11. Every menu action is one key. No chords. No gameplay input needs more than 2 presses per second (Xbox XAG 107). UIFLOW `keyboard-only` covers it.
12. `WBP_*` widgets have no property bindings and no Event Tick; the HUD updates from events. Paste the empty Bindings panel and the Event Graph in the PR. [VERIFY]

## Menu look (the menu style bar, Josh 11 Nov)
Every menu screen and transition (title, pause, settings, Survived, fail) has the feel of a paper cut-out,
shadow-puppet animated end-credits sequence (the target is the 2004 film "Lemony Snicket's A Series of Unfortunate
Events"), made in our brand and never deviating from our art: the key art, `style.json`, the etched paper and Ricky's
references. Written target (`pipeline/art/references.json` `menu-style-bar`, kind "described"; no frame of the film
is stored or copied: copyright, Official Rules §7(h), §15(d)):
- layered paper cut-out silhouettes in near-black ink; three or more parallax depth planes;
- hand-made, stop-motion-like motion: stepped timing, slight jitter, never smooth tweened easing;
- ink-and-paper textures on every surface; gothic storybook typography; our palette only;
- a painted vignette in the menu art (the post-process vignette stays off, `pipeline/art/art-bible.md`).
Card 0.21b's screens go through the art loop (piece `menu-screen`): blind critic rounds against the brand references
with this written target, until the critic cannot pick them over ours, plus the deterministic checks
(`art_check.py`, `screen_check.py`, `art_ref_check.py`). Same enforcement as other art (`check_pr.py` artref, artloop).

## Required screens and settings (team meeting, 11 Nov)
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
