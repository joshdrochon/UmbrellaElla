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
