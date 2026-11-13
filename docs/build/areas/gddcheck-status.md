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
- (superseded, see Unbound policy) 578 UNBOUND values (`python3 tools/build/gdd_check.py --list`). Biggest: QA-30 70, SURV-06 35, SURV-07 34, FLOW-15 33, HAZ-39 30.
  Many are not game constants (test counts, formulas, history); binding the rest is follow-up work for the owning lanes.
- A decisions row excuses by citing the Rule ID anywhere in the row, so a passing mention also excuses. Not tightened (the brief says "cites").
- Spec keys are positional where a GDD list has no labels (`MOVE-21.units.2`). If the GDD wording shifts, the key moves and the old binding fails as stale, which forces a review.
- prepackage runs it as a reported check (not blocking), because the 3 known mismatches would block packaging until fixed. The merge gate blocks new FAILs.

## Unbound policy (Josh, Nov 12)
Every GDD number is bound in `gdd-bindings.json` or listed in its `unbindable` object with a reason. The spec now carries
`priority` per value (from the row's `APPROVED_P<n>`; all 218 rows are P0). Unbound and unlisted: P0 `FAIL UNBOUND P0 rule=...`
(exit 1), P1/P2 or priority-less `WARN`. An `unbindable` entry with no reason, a key the spec lacks, or one that is also bound, fails.
- 107 more values bound this slice (health, recovery, defense, suction, spell multipliers, unlock levels, run multipliers, Keeper timings, Broken Mill prototype, field fractions). All match the GDD.
- 471 values listed `unbindable` with a category reason (worked arithmetic 119, derived/per-rank terms 106, QA restatements 82, sequence terms 64, identifiers 47, catalogue/seed 20, art 20, camera 9, other 4).
- Reasons were assigned by rule and wording pattern, not read one by one. The "derived/per-rank" and "worked arithmetic" groups may hide a real game value (e.g. an individual Broken Mill coordinate). Review those two before trusting the zero.
- Tests: `test_unbound_p0_value_fails`, `test_unbound_p1_value_only_warns`, plus reason/stale/double-listing and priority tests (19 total, pass). `gdd_spec.py --check` and `pipeline_check.py` clean.

MISMATCH=3 BOUND=360 UNBINDABLE=471 UNBOUND_P0=0 UNBOUND_P1P2=0
