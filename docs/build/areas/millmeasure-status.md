
## HAZ-08..13 (worker pass, main 1ab85de)
The measurement tests already exist (enemies2): `BrokenMill.World.MeasureOnwardRideBends`, `MeasureRedRayPaths`,
`MeasureFiringFixture`, `MeasureFiringWindow`, `MeasureEmissionsPerPass`, `MeasureDelayedImpact`. Re-run on main:
build exit 0, 6/6 PASS, MEASURE lines unchanged from `enemies2-status.md`.
MATCH: red rays (25.4 / 421.6 / 30.2), speed/damage/range/burst/rise/fall, worked case from 680, hits per pass at fall 264 and 396, delayed impact.
GAP, not fixable in the BrokenMill lane: HAZ-08 restoring field (needs Motor hook), HAZ-09/10/11/12(330)/13 contact (Attack
fixture radius 12 / muzzle +60, GDD forbids tuning), HAZ-13 drift (Motor clamp). Requests: `requests/millmeasure.md`.
Rule-status rows HAZ-08..13 updated from "not measured" to the measured numbers. No code changed.

## Small Blast fixture to GDD HAZ-10 (D-new-smallblast-fixture)
Changed: `AttackTuning` MuzzleOffset (44,0,6), BlastRadius 6; `AttackCadence::Step` no longer subtracts from an idle countdown.
New test `UmbrellaElla.Move.SmallBlastCadenceGaps` (every gap 12 frames at 60 fps). Build exit 0; Move 32/32, BrokenMill 24/24 PASS.
Re-measured: HAZ-09 all MATCH (78 clearance now). HAZ-10 all MATCH (cadence gaps 0.200, muzzle +44/+6, radius 6) except HeroSize (not built).
HAZ-11: upper edge 519.5 MATCH, lower edge 390.5 vs 402. Cause: the island stops a shot at its top (390), not at IslandShotMargin 12; BrokenMill room (enemies2 lane). Windows 0.489/0.391/0.326 follow.
HAZ-12: 264 and 396 MATCH, 330 gives 2-2 (same cause). HAZ-13: contact 1.017 vs 1.014 MATCH; drift 20.2 vs 30 (Motor clamp, request 2).
Still open: HAZ-08 Motor hook (request 1), HAZ-13 clamp (request 2), HeroSize, island margin (enemies2 lane).
