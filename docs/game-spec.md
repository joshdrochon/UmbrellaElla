# Game spec defaults (owner: game design owner)

The current GDD snapshot (`docs/gdd/CURRENT`, now `docs/gdd/GDD-SH1.0.md`) and `docs/feature-manifest.json` win on mechanics.
This file holds the defaults agents need that the GDD leaves to the team. Every line is a default, not a decision. Change it
in a PR the game design owner approves. Where a row in `docs/decisions.md` covers the same thing, that row wins. Numbers live
in `pipeline/feel/feel.json` (movement and feel) and `pipeline/level/encounter.json` (the Keeper fight); this file does not copy them.
GDD SH1.0 prints the starting numbers in its rule text (`docs/feature-manifest.json` `approved_parameters`, traced by
`tools/manifest_check.py`); its section 9 ranges are blank (D-new-sh10-param-ranges). The prototype defaults for details the
GDD leaves OPEN are listed in the ledger's import report and follow D-new-sh10-open-details.

## Controls (GDD SH1.0 MOVE-04..MOVE-10, MOVE-17)
Bindings are data (Input Adapter, `Content/UmbrellaElla/Input/`). Keyboard / mouse and controller are both required, all remappable (MOVE-10).
| Action | Keyboard / mouse | Gamepad |
|---|---|---|
| Rise: release Shoot and Absorb (overhead) | – | – |
| Shoot + drop (unlimited, fires right) | Left mouse / J | R2 / RT |
| Absorb + drop (catch yellow, heal) | Right mouse / K | L2 / LT |
| Fast free fall (no fire, no suction) | both | both |
| Hop (overhead) / context dash (falling) | Space | Cross / A |
| Falling dash back / forward | Q / E | L1 / LB, R1 / RB |
| Ride a harmless current (overhead, inside it) | Left Shift | Triangle / Y |
| Trim up / down | W / S, arrows | Left stick |
| Spells (Director's Cut) | 1-4, [ / ] | Right stick, D-pad |
| Pause | Esc, F1 | Options / Menu |
| Retry after defeat | Enter | Cross / A |
Direct horizontal steering is OFF and there is no mouse aiming (MOVE-07). Fire always goes right. Controls show in the
tutorial and the pause menu, read from the current bindings. Every menu works with keyboard only (`pipeline/ui/menus.md`).

## Movement modes (GDD SH1.0 MOVE-19, MOVE-21)
Neither held = overhead rise; Shoot only = shooting fall; Absorb only = absorbing fall; both = fast free fall. Each mode is a
speed, not gravity (`feel.json` rise_speed / fall_speed / free_fall_speed: 240 / 660 / 1220, the felt speeds Josh kept,
D-new-move-speeds; GDD 120 / 330 / 610). Wind, gust push and damage modify motion
separately. The bottom and the ceiling top are both lethal: reaching either line is death (WIND-03, D-new-ceiling-lethal). Lift falls with active health to `lift_min` (SURV-05). Dash invulnerability is OFF; hop protection and post-hit
protection are separate (MOVE-15).

## The Keeper arena and the level (GDD SH1.0 section 5; D-new-sh10-units, D-new-sh10-camera)
- Keeper fight (both modes): fixed 16:9 single screen, 1920 x 1080 units (1 unit = 1 cm). Map `L_Graybox` first, then the arena map the Integrator builds from it (D23).
- Director's Cut level: nine chunks from the 12-chunk / 24-variant catalogue, 1920 units each, three refuges with checkpoints, a side-scrolling camera that reveals the next current, hazard and exit (FLOW-24, HAZ-37, CAM-08).
- The bottom is lethal; supports and solid land are harmless (WIND-03). Rising past the ceiling top is death too (D-new-ceiling-lethal).

## Keeper phases (GDD SH1.0 OWL-06..OWL-35; owner: Encounter Director)
Wings, then the three hanging mechanisms front → middle → rear, then the clock; a checkpoint at each phase start. Death retries
the current phase with full active health and exactly 3 current lives. Success happens once at the final clock hit; the Keeper
withdraws alive in about 2.5 s. Same-frame defeat versus final clock hit is OPEN: default, defeat wins (one terminal event).
Attacks, numbers and breaks: the `GDD-SH1.0` preset in `pipeline/level/encounter.json` (`pipeline/level/encounter.md`).

## Screens and flow (FLOW-02..FLOW-04, FLOW-34..FLOW-41, FLOW-49; D-new-lose)
Start (Start Game, Start Director's Cut) → first-start tutorial (Pause → Skip) → play. Start Game goes straight to the Keeper;
Director's Cut plays the level first. Win: ending story text over the background, then credits with music; Director's Cut then
shows Journey Complete statistics (Try Again, Main Menu). Fail screen when the last life empties: says what ended the run,
then Retry (the checkpoint, not a mid-run restart) or Quit. Pause: Continue, Settings, Quit.
Settings and accessibility: `pipeline/ui/accessibility.md`, `pipeline/ui/menus.md`.

## Health (GDD SH1.0 SURV-05, FLOW-30..FLOW-33)
One top-left antique clock: the health hand (III full, back toward XII on hits) and the life hand. 3 hits per life, 3 lives;
incoming damage 1 (red, yellow, gust, traps), 1.25 (chain head), 1.5 (talon). Yellow absorbed while dropping heals 0.5 (+0.3 per
recovery rank), active life first, then a spent reserve. No revival after final defeat. Reference model: `tools/progression_model.py`.

## Feedback the player reads
| Signal | Means | Owner |
|---|---|---|
| Clock HUD hands and arc | Active health and lives (FLOW-30) | Art Director |
| Keeper wings, mechanisms and clock | Phase, eligible target, warning / strike / recovery (ANIM-06) | Art Director |
| Broad ash-blue current vs jagged front | Safe current vs hostile gust (OWL-17, BG-05) | Art Director |
| XP ring (Director's Cut) | XP toward the next level, pulse and clock sound on level-up (FLOW-48) | UI and UX |
| Sound | Warnings, launches, hits, catches, state changes (`pipeline/audio/sound-list.csv`) | Audio |
Every critical event has one sound and one visual: `pipeline/ui/signals.json`, checked by `python3 tools/ui_check.py signals`.

## Engine tests
GDD SH1.0 acceptance scenarios QA-29..QA-42 (the manifest `tests` of each feature) and the engine tests in
`pipeline/qa/test-map.md`. A card for a feature is not ready without its test in Done-when (`pipeline/checklists/design-review.md`).

## Audio
The sound list is `pipeline/audio/sound-list.csv` (Audio role); tier P0 = due at G1. Music and sound effects are separate
deliverables (`pipeline/roles/audio.md`). Every sound has a provenance row (`pipeline/art/provenance.csv`).
