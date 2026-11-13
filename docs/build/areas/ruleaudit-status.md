# ruleaudit status

Checked on main 1ab85de: build exit 0; `UmbrellaElla.Story+Flow+BrokenMill+Health.World+Level` PASS 95/95.

## Set to built (evidence in the csv)
NAR-04, NAR-07, FLOW-49 (storyflow, dcb08d4).

## Notes rewritten, still partial
- WIND-03 / HAZ-14 / HAZ-15: bug still on main. WindCurrent sends the pawn name, Motor accepts only Ella. Tests pass by naming Ella "Ella".
- FLOW-45: no HUD, XP ring or Flow screen reads text scale or reduced motion (requests/settings.md 6 not applied).
- FLOW-28: health carry across route checkpoints not shown; QA-36 not run.
- HAZ-08..13: measured by enemies2; remaining GAPs named per row. Owner was ORPHAN, now enemies2 (restoring field) or lead (Attack fixture).

## Not audited
The other partial rows (art, VFX, audio, level chunks, playtest) have no code gap that a test run can close; notes left as written.
