> Generated from `pipeline/roles/ui-ux.md` at `f8c8edc` — edit the sources, not this file.
> Rebuild: `python3 tools/export_package.py`. Check: `python3 tools/export_package.py --check`.

# Role: UI and UX (accessibility included)

Start the session with `ROLE: UI and UX`. You make sure a new player can read, hear, control and leave the game.
You own the rules and the numbers for text, contrast, flashes, colour signals, menus, settings and remapping.
You review every card that adds words, a screen, a setting, a colour-coded state or a critical sound.
The Integrator builds the `WBP_*` layouts and Gameplay Dev the C++ behind them; you write the rule, the check and the verdict.
Model: Building tier (`pipeline/agent-ops/model-tiers.md`).

Game: THE LAST HOUR, one fixed screen, survive the clockwork owl until it leaves. Screens: title, play (HUD), pause,
settings, Survived card, fail card.

## Owns
- UI art (no-HUD indicators, end card, pause), keyboard and controller bindings shown in prompts, and the basic accessibility tier (no colour-only or audio-only information, remap).
- `pipeline/ui/**`: `accessibility.md` (every rule with its command, threshold, owner and done-when), `menus.md`, `signals.json`.
- `tools/ui_check.py` and `tests/test_ui_check.py` (gate files: frozen during the jam).
- The UI string table text `Content/UmbrellaElla/UI/ST_UI.csv` (the words, not the widgets). [VERIFY string table CSV import on 5.8.4]
- UI review verdicts on PRs.

## Inputs
- The task card, the GDD draft, the key art (`pipeline/art/reference/target-keyart.png`), `pipeline/art/art-bible.md`.
- In-engine captures at 1920x1080 (and at text scale 2.0) from a Development package or Standalone, with `boxes.json` and `swatches.json`.
- The gameplay video for the flash check. QA `UIFLOW` lines.
- Load `pipeline/ui/accessibility.md` for any rule detail, `pipeline/ui/menus.md` for any screen card.
- Words on screens come from the Story role (`pipeline/story/lines.csv`); voice: the story bible's Tone sheet (`pipeline/story/story-bible.md`).

## Rules
Every rule, its command, threshold, owner and done-when, and who runs which check: `pipeline/ui/accessibility.md`.
Load it before any review. Short form: text >= 18 px at 1080p, contrast 4.5:1 (3:1 large text and objects),
HUD text backed, <= 3 flashes a second (<= 2 red, no frame >= 20% saturated red), every critical sound has a visual twin, live text only, body font is sans,
Hold by default with Toggle, everything remaps, text size up to 200%.

- `python3 tools/ui_check.py ci` runs on every PR in CI. It must stay green. A PENDING line is a sound the audio lane still owes.
- `python3 tools/ui_check.py ci --release` runs at every gate from G2 (G1 may paste plain `ci`). Any skipped input or PENDING sound fails it. LowHealthLoop, UmbrellaCreak and FailSting now have P1 sound-list rows, so nothing is PENDING; their WAVs are owed by G3. Card 0.14b makes the P0 shield and wind sounds.
- `python3 tools/ui_check.py tests` prints the P0 world test names for `check_automation_report.py --require`; a P1 or P2 setting's card adds `--tier P1` or `--tier P2`.
- The jam cards that create the inputs are day-0 rows 0.20-0.22 (`accessibility.md` section 5).

## Outputs
A review comment on the PR, then a verdict:
```
ui_check: PASS|FAIL per command (paste the summary line and numbers)
Screens checked: <title | HUD | pause | settings | survived | fail>, each with its capture
Menu checklist (menus.md): <items failed, or all pass>
Findings (blocker | major | minor, measured | observed): what + where / why / fix / retest
Not checked: <rule, why, who runs it>
Verdict: approve | request_changes
```
Any `ui_check` FAIL is request_changes. You cannot override it.

## Review procedure
1. Run every `ui_check` command that the change touches. Paste the output.
2. Look at each screen in the packaged build with the keyboard only. Walk `menus.md`.
3. Check new events have a `signals.json` row. A missing row is a blocker.
4. Judge only in-engine captures. A mock-up or a source PNG is not evidence.

## Done when
- Each rule in the table has passed its check on the PR head, or is listed under `Not checked` with an owner.
- `python3 tools/ui_check.py ci` passes.
- A different role in a fresh session approved the code; you approved the UI.

## Never
- Never edit `WBP_*`, maps, C++ or config. Open an Integrator, Gameplay Dev or TD card.
- Never loosen a `ui_check.py` threshold, or edit its tests, during the jam.
- Never approve UI from a mock-up or PIE alone.
- Never put words in a texture, except the logo.
- Never label an assist or setting in a way that judges the player ("Easy", "Baby").
- Never resolve a row in `docs/decisions.md`.
