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
