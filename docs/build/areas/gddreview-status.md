# gddreview status

Independent review of the 471 `unbindable` entries from area/gddcheck (merged `origin/area/gddcheck` and `main` first). Every entry read one by one against its GDD wording and the game source. No game value changed.

## Done
- `tools/build/gdd_check.py`: two binding kinds that were missing. `expr` (arithmetic over tuning defaults; `floor min max abs xp_to(level, base)`; only plain arithmetic is evaluated) and `const` with `index` (nth literal of `Symbol(a, b)`). Tests added in `tests/test_gdd_check.py` (21 pass); the test tree now copies files that `const` bindings read.
- 239 entries moved to a real binding: 237 compare today, 2 are `playtest` bindings no log reports yet (`HAZ-09.value`, `HAZ-09.radius_leaves`, UNMEASURED).
  Worked arithmetic: Broken Mill clearances, windows and first-contact times now follow the tuning (mirrors `FBrokenMillRules`). XP totals 916/1981/3096/7000 follow `XpCurveBase` via `xp_to`. Point totals 61/16/42/3/121 follow `LevelCap`, ranks, caps. Healing/defense/suction/cone ladders follow the rank tuning. Unlock levels, slider/text-scale limits, HUD aspect, ending hold, lift weight 0.7, keeper protected reserve 40%, reduced interval x1.6.
- 232 were left unbindable at review; 24 of them later moved to `not_in_game`, so the checker prints UNBINDABLE=208 and NOT_IN_GAME_P0=24; each with a reason that names its own number and wording (218 distinct reasons; the rest share a reason because they are the same fact, e.g. the three example builds).

## New mismatches (Rule ID, GDD value, game value)
None. `gdd_check` reports MISMATCH=0 on the merged tree (main fixed HAZ-10 in b0c80e58).

## Found while reviewing (not mismatches, need an owner)
| Key | GDD | Game | Note |
|---|---|---|---|
| HAZ-13.wind | 360 | 300 (`FBrokenMillTuning.WindSpeed`, `FFieldTuning.DefaultWindForce`) | residual-drift estimate uses 360; unreconciled |
| HAZ-03.guard_feet | x 1450 | guard centred at x 1440 | no feet field; z 390 does match |
| HAZ-08.inside_eligibility / value.4 | eligibility 185-275 | `LowerOnwardZ` 210-330 | GDD sentence conflicts with HAZ-06 |
| CAM-05.h.3 | 0.7H band "near" | `LevelPlan::HighFraction` 0.75 | bound with tol 0.06 because the GDD says "near" |
| HAZ-06 / HAZ-08 | lowered step centre 230, half-width 45, ascent start x 1640, root z 400, lift end (330,680), core z 300-780 | no field, no test literal (envelope 185-285 is a test literal, bound) | Broken Mill coordinates the game does not hold |
| HAZ-14 | HeroSize 0.75/1.3, hitbox 0.75/1 | test inputs only | HeroSize has no tuning field |

## Caveats
- `expr` bindings check the tuning defaults against the GDD's arithmetic. They do not run the game's rule functions; the Broken Mill tests do that.
- Playtest names `PLAYTEST_MILL_HAZ09.*` are proposed; the playtest runner does not emit them yet.
- Range-end targets (5-8 min, 600-800 XP, 10 runs) stay unbindable: the check compares one value, and no log line reports first-run minutes.


## Lead fix: `not_in_game` (Nov 12)
- 24 entries moved out of `unbindable` into a new top-level `not_in_game` list in `docs/build/gdd-bindings.json` (each: owner lane, what is missing, the old reason in `was`). They are real GDD values the game has no home for: Broken Mill coordinates (enemies2: lowered-step centre/half-width, ascent x 1640 + margin, root reopen z 400, protected core z 300-780, lift end 330/680 + half-width 30, guard feet x 1450), HeroSize and hitbox-scale fields (motor: HAZ-10/13/14, actor scale 0.5), camera guides CAM-05.value 0.3 and CAM-06.h.2 0.15 (arena).
- `gdd_check` prints `FAIL NOT_IN_GAME P0 <key> ... owner= missing=` (P0) or `WARN NOT_IN_GAME` (P1/P2). A malformed entry, a key the spec lacks, or one also bound/unbindable fails. Summary line now carries NOT_IN_GAME_P0 and NOT_IN_GAME_P1P2.
- Gate baseline: main has no `gdd_check.py`, so its baseline was empty and every fail already in the game (3 HAZ-10 mismatches + 24 NOT_IN_GAME) would have counted as new and blocked the merge that adds the check. `quality_gate.py check` now builds the baseline for any blocking check whose script is missing on main by running the merged tree's script over main's `Source/` and `Config/`. Fails already there pass; fails the merge adds still block. Once main has the script, the normal baseline applies.
- Tests: `tests/test_gdd_check.py` (P0 fails, P1 warns, malformed entry fails), `tests/test_build_gate_ports.py` (old fails not new, added fail new).
- Left in `unbindable` on purpose: HAZ-08.inside_eligibility/value.4 (GDD sentence conflicts with HAZ-06), HAZ-13.wind 360 vs 300 (game has the field; a mismatch to reconcile), retired fixtures, labels, ordinals, examples.

MISMATCH=3 BOUND=597 UNBINDABLE=208 NOT_IN_GAME_P0=24 NOT_IN_GAME_P1P2=0 UNBOUND_P0=0


## Review fixes (Nov 12)
- Tests start from current header text (muzzle 44/0/6, radius 6). `test_current_tree_has_no_mismatch_fail` replaces the stale HAZ-10 drift test; `test_vector_component_binding` edits 44/0/6 to 60/0/0 and expects a MuzzleOffset fail.
- `python3 -m unittest tests.test_gdd_check tests.test_build_gate_ports`: 28 tests, OK.
- `gdd_check`: MISMATCH=0 BOUND=597 UNBINDABLE=208 NOT_IN_GAME_P0=24 NOT_IN_GAME_P1P2=0 UNBOUND_P0=0 UNBOUND_P1P2=0
- Not done: AST walker for `EXPR_OK` (minor; bindings are hand-written).
