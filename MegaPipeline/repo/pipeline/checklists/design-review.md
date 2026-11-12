# Design review checklist (run by the Producer before a rule card is ready)

Use it for cards that add or change a game rule or the arena: umbrella, wand, damage, health, wear,
gusts, owl patterns or phases, the end event. Art, import, tooling and pipeline cards skip it.
A card that fails any line is not ready. Fix the card or open a decision row.

## 1. Where each line comes from
Tag every design line the card quotes:
- `GDD RULE`: in the GDD snapshot `docs/gdd/CURRENT` names, with its feature ID authorized in `docs/feature-manifest.json`. Build it exactly.
- `DEFAULT (Dn)`: a default from `docs/decisions.md` or `docs/game-spec.md`. Build it, and name the row in the PR.
- `HYPOTHESIS (Pn)`: something a playtest is meant to check. Build it so it is easy to change (a tuning value, not code).
- `ILLUSTRATIVE`: comes only from the key art or an example. It adds no rule. A card may not build it as a rule.

## 2. The card says
- [ ] **Player outcome:** "The player sees X, does Y, and can tell why." If the card adds nothing the player sees, does or learns, flag it to the scope decision-maker.
- [ ] **Inputs:** which Enhanced Input actions it reads.
- [ ] **States and changes:** every state it adds or changes, and what moves between them.
- [ ] **Blocked path:** what happens when the player does it at the wrong time (opening while DEFEATED, a catch from the wrong side). The blocked path has its own cue and its own test.
- [ ] **Input conflicts:** the outcome for each one that applies. Open on the same frame as a hit. Close while still rising. Open during hit-stop. Pause during the end event. Anything not stated becomes a decision row first.
- [ ] **Pause, respawn, restart:** in Hold mode the umbrella state matches the held button after each one; in Toggle mode it keeps the last toggled state (D18).
- [ ] **Cues:** a visual and a sound for each state change, with the art-bible row and the `pipeline/audio/sound-list.csv` row that supply it. No state change without a cue. Each key state also reads with no sound.
- [ ] **Not colour alone:** each state cue differs by shape or motion, not colour alone.
- [ ] **No fast flashing:** no cue flashes more than 3 times per second. The card states each flash's duration and rate. Checked by `python3 tools/ui_check.py flashes` on a capture clip.
- [ ] **No feel words without a check.** "Responsive", "floaty", "fair", "readable", "satisfying" must name the number or the P-test that checks it.
- [ ] **Prompts wait for the player:** a text prompt stays until the action is done or the player dismisses it. No timed-out teaching text.
- [ ] **Settings persist:** a card that adds a setting (volume, window mode, umbrella mode, remap, assist) has a Done-when that changes it, restarts the packaged build, and reads the kept value from the log.
- [ ] **Owl windups:** each owl attack has its own windup sound, which starts at or before the visual tell and >= 0.2 s before danger (`audio_check.py --log`).
- [ ] **Owl pattern or phase card:** Done-when has `encounter_check.py` 0 problems and names the `UmbrellaElla.Owl.*` tests from `pipeline/checklists/level-sections.md`.
- [ ] **Named test copied:** a card that builds a feature has the tests of every `pipeline/qa/test-map.md` row that lists its feature ID in its Done-when.
- [ ] **Behind its flag:** a card for a non-CONFIRMED feature builds it behind its flag at the manifest default, with a flag-off test (`pipeline/unreal-rules.md`, Feature flags).
- [ ] **Menus by keyboard:** a card that adds or changes a menu has the Done-when "works with arrows, Enter and Esc only", proven by a packaged-build smoke step that goes title → play → pause → quit by keys.
- [ ] **No hidden help:** owl timing, damage and lift never change with how the player is doing. Any assist is a visible setting with a decision row, and the run log records it.
- [ ] **Gamepad too:** GDD SH1.0 MOVE-04 targets keyboard and controller. A card that adds an input action binds a gamepad key next to the keyboard key in `IMC_Default`/`IMC_Menu` (bindings stay the GDD's open default-bindings question until decided). From G2, at least one valid gate playtest run is on a gamepad (the observer notes the device).
- [ ] **Done-when** has the normal path plus at least one blocked or interrupted path.
- [ ] **New numbers or behavior** not in the GDD, game-spec or D20 (coyote time, knockback, buffers) have a decision row.

## 3. What else it can break (re-run before merge)
- [ ] A card that changes the camera, sprite scale, palette, background motion or owl telegraph art re-runs the P8 captures (`CAM_Eval_Arena`, `CAM_Eval_Stress` once it exists) with `art_check.py` and `ui_check.py contrast`, output pasted in the PR.
- [ ] A rule or tuning card lists under `Used by` the P-tests and `encounter_check.py` codes its change can move; those re-run before merge (encounter_check) or at the next gate (P-tests), and the gate record links them.

## 4. Same behavior, new look
A projectile or pattern that looks different but behaves the same is a new sprite or data asset on the existing class.
It is never a new C++ class.
