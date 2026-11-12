# Game spec defaults (owner: game design owner)

The current GDD snapshot (`docs/gdd/CURRENT`, now `docs/gdd/GDD-1.3.md`) and `docs/feature-manifest.json` win on mechanics.
This file holds the defaults agents need that the GDD leaves to the team. Every line is a default, not a decision. Change it
in a PR the game design owner approves. Where a row in `docs/decisions.md` covers the same thing, that row wins. Numbers live
in `pipeline/feel/feel.json` (movement and feel) and `pipeline/level/encounter.json` (the owl); this file does not copy them.
GDD 1.3 §5A approves the starting numbers (`docs/feature-manifest.json` `approved_parameters`); where those two files differ, the GDD wins until they are re-filed (D-new-gdd13-numbers).

## Controls (GDD 1.3 §9; DEC-01)
Bindings are data (Input Adapter, `Content/UmbrellaElla/Input/`). PC keyboard/mouse and controller are both required.
| Action | Keyboard / mouse | Gamepad |
|---|---|---|
| Steer left/right | A / D, ← / → | Left stick |
| Attack descent (hold): ATTACK_DESCENT, auto-fire +X | Left mouse | R2 |
| Shield descent (hold): SHIELD_DESCENT, front block | Right mouse | L2 |
| Rise: release both = UP_OPEN | – | – |
| Pause | Esc | Options / Menu |
| Retry after defeat | R | Confirm |
SHIELD wins when both are held (GDD 1.3 §3 step 6). No vertical steering, no aim input and no fast-fall key.
ATTACK and SHIELD are holds by default; a Toggle option is open (D18, `docs/gdd/questions-1.3.md` Q8). Dev tools may remap; player remapping is P1 (D-new-remap).
Controls show on the title screen and in the pause menu, read from the current bindings.
Every menu works with keyboard only: arrows to move, Enter to choose, Esc to go back (`pipeline/ui/menus.md`).

## Umbrella states (GDD 1.3 §3)
UP_OPEN (default on release) gives lift (UMB-01). ATTACK_DESCENT (COM-01, UMB-02) and SHIELD_DESCENT (DEF-01) fall naturally
at normal gravity; NO_LIFT is the derived physics condition, not an input. OPEN_LEFT and OPEN_RIGHT (UMB-03) are PROPOSED, off;
INVERTED is an EXPERIMENT. DEFEATED stops control. Priority: lockout, then SHIELD, then ATTACK, else UP_OPEN. State changes never change gravity.

## The arena (GDD 1.3 §1, §6, §7, §7B)
- Fixed 16:9 single-screen camera (`camera_mode` in `docs/feature-manifest.json` `build_parameters`, APPROVED_P0 in GDD 1.3). Scrolling is CAM-02, an off experiment. One 2D plane (+X right, +Z up, Y = 0). Code reads the mode at scenario reset. Map `L_Graybox` first, then the arena map the Integrator builds from it (D23).
- First fixture (GDD 1.3 §7B): 1600 x 900 cm arena, owl at x = +560, player spawn x = -350, z = 0. The owl is on the right, so shots fire +X. A tunable test preset, not level geometry.
- Top and side bounds are safe and contain the player. The bottom is the defeat boundary (`PlayerDefeated`, reason bottom).
- The encounter is winnable without hitting any owl part (END-01).

## Encounter states (GDD 1.3 §8; owner: Encounter Director)
READY → ACTIVE → ENDING_SUCCESS or ENDING_FAILURE → RESTARTING → READY, plus PAUSED (one owner suspends everything).
Completion: 90 s of accumulated unpaused ACTIVE time (END-01, DEC-06); the rule stays replaceable. `pipeline/level/encounter.json` uses 90 s (re-filed, D-new-gdd13-numbers; `encounter_check.py` E29). Defeat and completion in the same update: defeat wins, one terminal event.
Intro, contest and desperation are tuning presets, not required phases. The owl chest clock is not the completion timer.
Patterns, timings and breathers: `pipeline/level/encounter.md`. Acceptance: `pipeline/checklists/level-sections.md`.

## Screens and flow (D-new-lose)
Title (Play, Settings, Quit) → encounter → Survived card (time survived, Retry, Quit) or Fail screen.
Fail screen at zero health or a bottom exit: says what ended the run, then Retry (back to the start with minimal delay, D5) or Quit to title.
Pause: Resume, Settings, Restart, Quit to title. Pause also works during the end event.
Settings and accessibility: `pipeline/ui/accessibility.md`.

## Health without a HUD (GDD 1.3 §6, §9, DEC-09)
One 100 HP value (DEC-04); 34 HP per owl bolt and 0.8 s invulnerability (GDD 1.3 §6; D17 superseded). Umbrella wear shows four stages: intact 67-100, damaged 34-66, critical 1-33, defeated 0. A front shield catch heals 20 HP when its 2 s cooldown is ready. A small indicator near Ella plus the hit sound shows health, never colour alone. After a hit: brief
invulnerability and a clear hit reaction (`docs/feel-spec.md`). Progress: clear telegraphs and end screens first; the background motif (VFX-01) later, never music alone (DEC-09).

## Feedback the player reads (GDD 1.3 §9; Feedback Adapter)
| Signal | Means | Owner |
|---|---|---|
| Umbrella fabric | Health stage (SURV-02, APPROVED_P0) | Art Director |
| Owl and its clock | Enemy state and the CLOCK hit cue, not the completion timer (GDD 1.3 §8) | Art Director |
| Wing pose and flow lines | Gusts (OWL-02, when its flag is on) | Art Director |
| Background motif | Encounter progress (VFX-01, flag off by default) | Art Director |
| Sound | Gust windup, bolt launch, hits, state change (`pipeline/audio/sound-list.csv`) | Audio |
Every critical event has one sound and one visual: `pipeline/ui/signals.json`, checked by `python3 tools/ui_check.py signals`.

## Engine tests
Required tests per GDD 1.3 test (QA-01..QA-28): `pipeline/qa/test-map.md`. A card for a feature is not ready without its test in Done-when
(`pipeline/checklists/design-review.md`).

## Audio
The sound list is `pipeline/audio/sound-list.csv` (Audio role). Music and sound effects are separate deliverables
(`pipeline/roles/audio.md`). Every sound has a provenance row (`pipeline/art/provenance.csv`).
