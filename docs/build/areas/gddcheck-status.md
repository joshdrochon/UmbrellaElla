# gddcheck status

Lane: GDD conformance check. Run on main (`1ab85de`), GDD snapshot `GDD-SH1.0.md`.

## Done
- `tools/build/gdd_spec.py` -> `docs/build/gdd-spec.json` (831 numbers in 218 Rule ID rows; generated, `--check` fails if stale).
- `docs/build/gdd-bindings.json`: 253 spec values bound to `*Tuning.h` defaults (Attack, Motor, Health, Umbrella, Keeper,
  Enemy, Progression, BrokenMill) and one playtest value (HAZ-07.falling <- PLAYTEST_CAM07 decision_height).
- `tools/build/gdd_check.py`: FAIL lines stable (no line numbers); a `docs/decisions.md` row citing the Rule ID turns a FAIL into EXCUSED.
- Wired: `quality_gate.py` BLOCKING `gdd_check` (no new FAIL vs main); `prepackage.sh` Python checks (reported, like the others).
- `tests/test_gdd_check.py` (14 tests): a changed value fails, a decision row excuses it, stale/broken bindings fail, unbound counted.

## Mismatches on main (game values not changed in this lane)
| Rule ID | GDD value | Game value | Where |
|---|---|---|---|
| HAZ-10 (muzzle X) | +44 | +60 | `FAttackTuning::MuzzleOffset.X` |
| HAZ-10 (muzzle Z) | +6 | 0 | `FAttackTuning::MuzzleOffset.Z` |
| HAZ-10 (radius) | 6 | 12 | `FAttackTuning::BlastRadius` |

Other bound values (250) match. Playtest log has no PLAYTEST_CAM07 `decision_height` mismatch (270 = 270).

## Left / caveats
- 578 UNBOUND values (`python3 tools/build/gdd_check.py --list`). Biggest: QA-30 70, SURV-06 35, SURV-07 34, FLOW-15 33, HAZ-39 30.
  Many are not game constants (test counts, formulas, history); binding the rest is follow-up work for the owning lanes.
- A decisions row excuses by citing the Rule ID anywhere in the row, so a passing mention also excuses. Not tightened (the brief says "cites").
- Spec keys are positional where a GDD list has no labels (`MOVE-21.units.2`). If the GDD wording shifts, the key moves and the old binding fails as stale, which forces a review.
- prepackage runs it as a reported check (not blocking), because the 3 known mismatches would block packaging until fixed. The merge gate blocks new FAILs.

MISMATCH=3 BOUND=253 UNBOUND=578
