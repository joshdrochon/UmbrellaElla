
## HAZ-08..13 (worker pass, main 1ab85de)
The measurement tests already exist (enemies2): `BrokenMill.World.MeasureOnwardRideBends`, `MeasureRedRayPaths`,
`MeasureFiringFixture`, `MeasureFiringWindow`, `MeasureEmissionsPerPass`, `MeasureDelayedImpact`. Re-run on main:
build exit 0, 6/6 PASS, MEASURE lines unchanged from `enemies2-status.md`.
MATCH: red rays (25.4 / 421.6 / 30.2), speed/damage/range/burst/rise/fall, worked case from 680, hits per pass at fall 264 and 396, delayed impact.
GAP, not fixable in the BrokenMill lane: HAZ-08 restoring field (needs Motor hook), HAZ-09/10/11/12(330)/13 contact (Attack
fixture radius 12 / muzzle +60, GDD forbids tuning), HAZ-13 drift (Motor clamp). Requests: `requests/millmeasure.md`.
Rule-status rows HAZ-08..13 updated from "not measured" to the measured numbers. No code changed.
