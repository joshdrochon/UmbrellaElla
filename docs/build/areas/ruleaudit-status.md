# ruleaudit status

Re-checked at b119b0f8 (main merged): `build exit: 0 mode=unity warnings: 0`; `TEST_FILTER=UmbrellaElla.Flow` `PASS tests=30 failed=0`.

## Set to built (evidence in the csv)
NAR-04, NAR-07, FLOW-49 (storyflow, dcb08d4). FLOW-49 caveat: keyboard focus on the Journey Complete widget is an artui follow-up.

## Notes rewritten, still partial
- WIND-03: built. Motor `IsEventForElla` accepts TargetId == owner actor name (EllaMotorComponent.cpp:167-172); `Move.World.RideCurrentFromVolume` covers it.
- HAZ-14 / HAZ-15: the only gap is that BrokenMill tests still name the pawn "Ella" instead of using the real-name path.
- FLOW-45: no HUD, XP ring or Flow screen reads text scale or reduced motion (requests/settings.md 6 not applied).
- FLOW-28: health carry across route checkpoints not shown; QA-36 not run.
- HAZ-08..13: measured by enemies2; remaining GAPs named per row. Owner was ORPHAN, now enemies2 (restoring field) or lead (Attack fixture).

## Not audited
The other partial rows (art, VFX, audio, level chunks, playtest) have no code gap that a test run can close; notes left as written.

## Rule audit (Nov 13, Opus): built rows vs GDD SH1.0 clauses vs evidence test bodies
Method: each built row's GDD text split into clauses; evidence test bodies read (plus any other test that asserts the clause).
A clause counts only when a test body asserts it. Unproven clause -> row `partial`, note `unproven: ...`, owner = area that closes it.

### Unproven, kept `built` (baseline), not downgraded
Josh's rule: the 150 baseline rows stay `built` (team count stays 150). `rule-status.csv` therefore has 92 rows `built` with an `unproven:` note and 51 `partial`.
The unproven clauses per rule are in `docs/build/clause-audit.csv` (tag i/ii; the single source). Proofs are in `clause-proof.csv`. The per-rule list that was here went stale and is removed.
`areas/ruleaudit-clauses.csv` is regenerated from `clause-audit.csv` (i/ii rows only; 30 clauses have no code pointer).
31 built rows have no clause in `clause-audit.csv`: judged fully proven by their named tests (MOVE-04..06/14/16/18/21, COM-08/10, FLOW-07/11/12/14/16/18/23/36..38/41, SURV-07, HAZ-25..30, NAR-02/03/08, ART-03).
Nov 13 review fix: `gdd:` proofs credit the number only. Clauses reworded `(value only)`; each got a separate behaviour clause tagged `i` (OWL-11/13/16/19/20, HAZ-03).

### Audited so far: 150 rows
FLOW-34 ART-04 FLOW-02 FLOW-03 FLOW-04 FLOW-35 FLOW-36 FLOW-37 FLOW-38 FLOW-39 FLOW-40 FLOW-41 FLOW-43 FLOW-49 NAR-04 NAR-07 NAR-08 NAR-02 NAR-03 HAZ-25 HAZ-26 HAZ-27 HAZ-28 HAZ-29 HAZ-30 HAZ-31 HAZ-32 HAZ-33 HAZ-34 HAZ-35 HAZ-36 HAZ-37 HAZ-40 MOVE-11 MOVE-12 MOVE-13 MOVE-14 MOVE-15 MOVE-18 MOVE-19 MOVE-20 MOVE-21 MOVE-22 UMB-05 WIND-03 COM-05 COM-06 COM-07 COM-08 COM-09 COM-10 COM-11 FLOW-05 FLOW-06 FLOW-07 FLOW-08 FLOW-09 FLOW-10 FLOW-11 FLOW-12 FLOW-13 FLOW-14 FLOW-15 FLOW-16 FLOW-17 FLOW-18 FLOW-19 FLOW-20 FLOW-21 FLOW-22 FLOW-23 FLOW-29 FLOW-42 OWL-06 OWL-07 OWL-08 OWL-09 OWL-10 OWL-11 OWL-12 OWL-13 OWL-15 OWL-16 OWL-17 OWL-18 OWL-19 OWL-20 OWL-21 OWL-22 OWL-23 OWL-24 OWL-25 OWL-26 OWL-27 OWL-28 OWL-29 OWL-30 OWL-31 OWL-32 OWL-33 OWL-34 OWL-35 HAZ-02 HAZ-03 HAZ-04 HAZ-05 HAZ-17 CAM-03 CAM-05 CAM-06 CAM-08 HAZ-19 HAZ-20 HAZ-21 HAZ-22 HAZ-23 FLOW-27 COM-12 COM-13 COM-14 COM-15 COM-16 COM-17 COM-18 FLOW-46 HAZ-41 FLOW-47 FLOW-24 HAZ-24 ART-03 VFX-06 VFX-09 CORE-04 CORE-05 FLOW-30 FLOW-31 FLOW-32 FLOW-33 SURV-05 SURV-06 SURV-07 MOVE-04 MOVE-05 MOVE-06 MOVE-07 MOVE-08 MOVE-09 MOVE-10 MOVE-16 MOVE-17

### Done
All 150 rows that were `built` on main at 56a187ec are audited; 119 moved to partial, 31 stay built.
Number clauses count as proven when gdd_check binds the GDD value (MISMATCH=0) and a test exercises that tuning field.
Code gap beyond tests: FLOW-05 run scaling (`UProgressionSubsystem::GetRunScaling`) has no consumer outside Progression.
Label: title button reads "Director's Cut"; GDD section 7 says "Start Director's Cut" (FLOW-34 note).

## Clause tagging (Nov 13, lead change)
Every unproven clause is tagged in its row note, `unproven(i)` code exists / only a test missing, `unproven(ii)` code missing.
Machine-readable list: `docs/build/areas/ruleaudit-clauses.csv` (rule,area,clause,tag,code_pointer).
Bound GDD numbers that gdd_check reports as matching count as proven by gdd_check (noted as "proven by gdd_check"), not downgraded. No row was re-promoted: each still has a behaviour clause with no test.
