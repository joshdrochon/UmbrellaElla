# artui status (worker, 12 Nov)

## 1. The bar cannot be skipped: DONE
- `pipeline/art/references.json`: 12 screen elements (`ui-title`, `ui-pause`, `ui-settings`, `ui-credits`, `ui-defeated`,
  `ui-story-text`, `ui-journey-complete`, `ui-purchase`, `ui-level-up`, `ui-tutorial`, `ui-hud-clock`, `ui-xp-ring`).
  Each is judged against `title-screen` and the quality bar `bar-other-realm`, and names its widgets and screens in a
  `ui` block.
- `tools/ui_check.py screens` (in `ci`): fails a widget class (UUserWidget, Slate S-widget, AHUD; `final` and
  .cpp-only classes too) or an `E...Screen` value under a `UI/` or `Flow/` folder that no screen element names, and an
  element that names something gone. `ci --release` fails without references.json.
- Tests: `tests/test_ui_check.py` class `Screens` (11 tests; the fake screen with no element fails) and
  `test_ci_release_passes_with_every_input`.

## 2. One shared UI style: DONE (code), applied to every screen
- `Source/UmbrellaElla/Public|Private/UI/Style/`: `FUmbrellaUIStyle` (display face, body face, colours, panel, slider,
  checkbox, ground painter), `SUmbrellaButton` (lettered button; focus or hover = bright gold label, a rule under it, a
  rule and diamond pointing at it), `SUmbrellaRule` (heading rule drawn as a clock hand), `SUmbrellaGround`.
- Display face "Umbrella Storybook": made by `Art/Source/UI/Font/build_font.py` (stdlib Python; every glyph is a stroke
  skeleton swept with a broad-nib pen; lowercase = small capitals). The game embeds the bytes
  (`UmbrellaStorybookFont.inl`), so there is no loose file to stage and nothing to cook. Body text stays the plain
  sans-serif (accessibility U14).
- Ground and HUD dial: `Art/Source/UI/Ground/build_ground.py` (numpy inside Blender 5.2.1's Python, fixed seed), imported
  by `Art/Source/UI/import_ui_art.py` to `Content/UmbrellaElla/UI/T_UI_Ground_PH`, `T_UI_ClockFace_PH`. Both are tracked
  `_PH` placeholders with provenance rows (so is the font).
- Restyled, paint and layout only: `SFlowBackground`, `SFlowMenu` (title, pause, tutorial, level-up, Defeated),
  `SFlowTextScreen` (story, credits), the purchase Done button and Director's Cut banner, `USettingsMenuWidget`,
  `UJourneyCompleteWidget`, `UStoryCaptionWidget`, `UProgressionPurchaseWidget`, `AUmbrellaHUD` (dial texture, blade
  hands, numerals in the display face). Text sizes are clamped to 18 or more by the style.
- One behaviour touch inside the widget: `SFlowMenu::OnFocusReceived` passes focus on to its first button, so the
  focused item is always marked (the input mode gave focus to the menu holder, and no item showed focus).
- Not restyled: `UXpRingWidget` (its colours and sizes live in the progression lane's tuning; it already is a thin gold ring).
- Tests: `UmbrellaElla.UI.Style.*` (6: face loads from the embedded bytes, text floor, contrast on ink, the button's own
  focus mark, shared brushes, clock-hand blade) and `tests/test_ui_style_art.py` (6: font build is fresh, deterministic,
  checksums, glyph coverage, winding, .inl bytes).
- Capture driver for the loop (development only): `-UIShots=<folder>` walks the real flow and saves one PNG per screen;
  `-UIShotsMode=dc` for the Director's Cut screens (`Private/Tests/UI/UIShotSubsystem`).

## 3. The loop
(see the round log below)

## Requests for the build lead: `docs/build/requests/artui.md`
1. `art_loop.py` asks every non-scene piece for a `context` pair (capture vs key art); a screen is its own capture and
   can never win that pair. Until it is changed no screen can get a pass line, whatever the critics answer.
2. `DirectoriesToAlwaysCook` for `/Game/UmbrellaElla/UI` (not verified in a package; workers do not package).
3. `ui_check.py widgets` misses `final` widget classes (left as is: fixing it fails main on the progression lane's ring).

## Round log (12 Nov, artui worker)
- Captured 9 screens with `-UIShots` (title, pause, settings, credits, defeated, story, tutorial, hud, known-bad). Title and
  Defeated read on-bar by eye: painted ground, Storybook lettering, gold focus mark.
- Blind panel on `ui-title` (round 1, `art_loop.py panel`, 6 fresh sonnet sessions): verdict `reference`, checks fail,
  calibration 4/6. Critic gap: "X is a small, soft render; thin lettering, less etched texture" (reference is full-res).
  Triage: ours = capture size. The safe launch (`run_game.sh`) is 640x360 and the ResX/ResY it passes first cannot be
  overridden; I tried `FSystemResolution::RequestResolutionChange` and `r.SetRes` from the capture driver, the PNG stayed
  640x360 (reverted, nothing committed). A 640 px frame will lose the detail pair against a 1080p reference whatever we paint.
- Also failing before any judging: `art_ref_check` says "card artui has no references assigned" (art_judge.card_refs reads
  `cards` on each reference; `title-screen` etc. list no `artui`), and the `context` pair cannot be won (request 1).
- BLOCKED (not the work): needs the lead. (a) a capture at 1280x720 or larger through run_game.sh (e.g. honour an env
  `RUN_GAME_RES`), (b) `artui` added to the `cards` of the references the screen elements use (`references.json`
  reference entries are outside my "screen elements only" lane), (c) request 1. No paint spend this round ($0).

## Round 2/3 (12 Nov, after merging main and ad9d6d1d context capture)
- Context capture made: `run_game.sh -SmokeShot=... -SmokeQuitAfter=15`. A relative -SmokeShot path lands under the
  editor's own folder (Engine/Binaries/Mac/Saved/...), not the worktree: pass an absolute path or copy it. Needs a
  prior `ue_slot.sh tools/ue/build.sh` or the launch dies on the UBT mutex.
- `art_ref_check --card artui --element ui-title` now PASSES (0.971). `required_pairs` for `ui-title` is now only
  reference + quality_bar (no context pair), so requests 1 and the cards gap are closed on main.
- Panel round on `ui-title` (6 sonnet critics run by me, `art_loop.py panel` makes folders only): calibration 5/6, 2 of 3
  sessions per pair counted, verdict `reference`. Every critic gives the same gap: our frame is "low-resolution and
  soft" with thin lettering and paper texture, next to a full-res reference. Same as round 1: capture size, 640x360.
- STILL BLOCKED on one thing: a capture larger than 640x360 through run_game.sh (e.g. env `RUN_GAME_RES` read into
  ResX/ResY, lead-owned file). Without it no screen can beat a 1080p reference on detail. No paint spend ($0).

## Round log 2 (12 Nov, artui worker, after lead e10efbd9)
- `artui` added to `cards` of `title-screen` and `bar-other-realm` (references.json, additions only); `ui_check.py ci` PASS.
- Captures at 1280x720 via `RUN_RES=1280x720 tools/build/run_game.sh -UIShots=...`: works, all 9 screens.
- `ui-title` round 4 (ground r1, 1280x720): checks pass (art_ref score 0.957), calibration 6/6, quality_bar pair: ours wins/same,
  reference pair: reference wins. Gap: "smoother, more digital surfaces; lacks grain, hand-made lettering, gold-edged rock".
  Triage: work (capture size no longer the cause).
- Ground r2 painted ($0.139, spent $6.675 total; prompt_r2.md: heavy grain, hand-inked contours, gold-rimmed rock edges).
  Brighter than the reference. Rounds 5 and 6: calibration 4/6, 1/3 calibrated sessions, score 0.866: no valid verdict.
  Not adopted; shipped ground stays r1 (r2 files kept under pipeline/art/proof/artui/ui-title/ for the next try).
- Next: darker r3 ground (keep the r1 value structure, add grain and gold edges), and a rougher inked title lettering pass
  (Art/Source/UI/Font/build_font.py: pen-wobble/distress). Then panel the other 11 screens; none judged yet.
- Note: UE import saves fail silently on read-only `.uasset` (LFS lockable); `chmod u+w` before `import_ui_art.py`.

## Candidates moved (12 Nov, lead rule "Where candidates live")
Ground paints r1/r2 (+ requests, prompts) now under `pipeline/art/proof/artui/ui-title/`; provenance paths updated.
`Art/Source/UI` holds only the font and the tracked `_PH` ground/clock-face. Main merged (references.json taken from main;
all 12 screen elements plus `ui-spell-wheel` present); `ui_check.py ci` PASS. `pipeline_check` has 2 problems, both
missing the agent-play script on main (not my lane).

## Round 7-9 (12 Nov, artui worker)
- references.json: `artui` re-added to `cards` of `title-screen` and `bar-other-realm` (main's merge had dropped it); art_ref_check PASS 0.958.
- Ground r3 (a, b) painted from r1 as input ($0.278, spent $8.935 of $33.82; prompt_r3.md). r3a (darker, border cropped, 2640x1485) shipped as the `_PH` ground; r3b kept in proof/ (paper frame too heavy).
- Panel on ui-title (1280x720, r3a): calibration 5/6, quality_bar pair ours wins, reference pair: reference wins. Gap (both sessions): "smoother digital finish, no inked line or paper grain; plain lettering next to the etched clock-hand lockup". Triage: work (lettering + grain), not capture size.
- Next: etched/distressed lettering in build_font.py plus a paper-grain overlay in the ground painter.

## Rounds 10-13 (12 Nov, artui worker)
- R10: font edge roughened (`INK_JITTER`, fixed hash; font tests pass). Gap unchanged: "plain lettering, no grain".
- Triage: the reference is a painted, ornate lockup with a clock-hand flourish; typeset text cannot match it. Work, not the check
  (critic calibration 5/6 to 6/6, quality-bar pair already won by ours).
- Painted title lockup (2 candidates, $0.278; prompt.md + prompt-review.md in `pipeline/art/proof/artui/ui-title-lockup/`):
  `lockup_a` keyed to alpha by `Art/Source/UI/Lockup/build_lockup.py` -> `T_UI_TitleLockup_PH`; `SFlowMenu` draws it for the title
  heading and falls back to the typeset text when the texture is missing. Provenance rows added.
- Tiled grain overlay `T_UI_Grain_PH` (`Art/Source/UI/Grain/build_grain.py`), drawn over the ground by `PaintGround`.
- R11 (lockup in): calibration 6/6, reference still wins 3/3: "cleaner, more digital; no grain; bright amber sky".
- R12/R13 (grain in): calibration 3/6 and 4/6, only 1 calibrated session on the reference pair, it picks the reference ("flatter,
  digital, pasted together"). Critic noise is high; no valid pass yet. Shipped `_PH` stays until a pass.
- Spend: $9.774 of $33.82 total (this lane $3.0 across r1-r3 and the lockup).
- Next: (1) lettering wear on the lockup (grain drawn over it too, or re-paint with heavier chipping), (2) mute the amber sky in
  the ground, (3) re-panel; then panel the other 11 screens (none judged yet).
- Checks on this commit: build exit 0, `UmbrellaElla.UI` 6/6 PASS, module_check 0 problems (the style assets singleton now found by object name, no mutable static), ui_check ci PASS, affected python tests ran clean.
- STATE: ui-title NOT passed (reference pair lost in r8-r13); the other 11 screens are not yet judged. Not blocked on the lead; the loop continues from "Next" above.
