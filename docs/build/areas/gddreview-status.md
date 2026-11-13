# gddreview status

Independent review of the 471 `unbindable` entries from area/gddcheck (merged `origin/area/gddcheck` and `main` first). Every entry read one by one against its GDD wording and the game source. No game value changed.

## Done
- `tools/build/gdd_check.py`: two binding kinds that were missing. `expr` (arithmetic over tuning defaults; `floor min max abs xp_to(level, base)`; only plain arithmetic is evaluated) and `const` with `index` (nth literal of `Symbol(a, b)`). Tests added in `tests/test_gdd_check.py` (21 pass); the test tree now copies files that `const` bindings read.
- 239 entries moved to a real binding: 237 compare today, 2 are `playtest` bindings no log reports yet (`HAZ-09.value`, `HAZ-09.radius_leaves`, UNMEASURED).
  Worked arithmetic: Broken Mill clearances, windows and first-contact times now follow the tuning (mirrors `FBrokenMillRules`). XP totals 916/1981/3096/7000 follow `XpCurveBase` via `xp_to`. Point totals 61/16/42/3/121 follow `LevelCap`, ranks, caps. Healing/defense/suction/cone ladders follow the rank tuning. Unlock levels, slider/text-scale limits, HUD aspect, ending hold, lift weight 0.7, keeper protected reserve 40%, reduced interval x1.6.
- 232 stay unbindable, each with a reason that names its own number and wording (218 distinct reasons; the rest share a reason because they are the same fact, e.g. the three example builds).

## New mismatches (Rule ID, GDD value, game value)
None. The 3 known HAZ-10 mismatches remain (muzzle X 44 vs 60, muzzle Z 6 vs 0, radius 6 vs 12).

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

REVIEWED=471 MOVED_TO_BOUND=239 MISMATCH=3 BOUND=597 UNBINDABLE=232 UNBOUND_P0=0
