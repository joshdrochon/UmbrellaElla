# Enemies2 status

Build `build exit: 0` (0 warnings); full `tools/ue/test.sh` PASS 254/254; `TEST_FILTER=UmbrellaElla.BrokenMill` PASS 15;
`module_check` 0 problems; `manifest_check` 0 problems. `pipeline_check` reports 1 problem that is not in this lane
(the settings2 area file names a request file that does not exist yet; same on main 89f6241).

## Done (rule -> test)
- HAZ-14 real winds, early/late reopen without theft -> `BrokenMill.World.RealWindsPickedByReopenHeight`
  (real `AWindCurrent` overlap events, real Motor: reopen z 417 rides reset left 55 units in 0.4 s, z 268.5 rides onward
  right 55 units, gap z 340 touches neither; falling through a band never rides it), `BrokenMill.EligibleWindByRoot`.
  The hand-broadcast wind event is gone; `WindCarriesEllaPastOneShotPerPass` is replaced by
  `BrokenMill.World.FallingPassRidesOnwardOneShot` (warned at (600,650), falls, reopens late, real onward current carries
  her right, the one snapshot shot never retargets and never touches her, one warning per pass, fresh entry rearms).
- HAZ-15 free-rise miss -> `BrokenMill.World.FreeRiseLeavesRegionShotMisses` (leaves the commit region after 0.48 s,
  shot still released at the captured point, misses, no second warning).
- HAZ-15 ordinary/free-fall misses, reopening heights, rescue envelope at minimum lift, no dash/hop ->
  `BrokenMill.World.MissedCurrentFallsAndMinimumLiftRescue`. Measured: 270->150 in 0.367 s ordinary / 0.200 s free fall
  (nominal 0.364 / 0.197); reopen is immediate (actual root within one frame of the decision height); rise 36.0/s at
  lift 0.3; back in the onward band after 0.42 / 1.17 / 1.78 / 2.40 s from reopen 196 / 169 / 147 / 125; floor
  clearance with the GDD half height 39: 77 / 50 / 28 / 6.

## Room change (in lane)
- `ABrokenMillRoom` now gates the two wind volumes by Ella's root (`FBrokenMillRules::GetEligibleWind`, flag HAZ_07):
  only the band her root is eligible for has collision. Found by the real-overlap test: Ella's capsule is the engine
  default (half height 88), taller than a 120-unit band, so in the 30-unit gap she overlapped both winds. Proven load-bearing:
  with the gate removed, 3 of the new world tests fail (gap touches both; late reopen pulled left).

## Workarounds and open items
- WIND-03 (levelchunks lane) not on main yet: the world wind tests spawn Ella with the actor name `Ella`, so the real
  overlap event's `TargetId` matches what the Motor accepts. Remove `bNamedElla` once WIND-03 lands. In play today no
  wind moves Ella.
- Ella's capsule is 34 x 88, not the GDD hurtbox (half width 23.4, half height 39): request in `docs/build/requests/enemies2.md`.
  With the real capsule the floor clearance at reopen 150 / 130 would be -21 / -43 (the room has no floor collider yet).
- Not built (HAZ-07, not this area's IDs): the missed-current low assist at (650,150) is a rule only, no current pushes
  left/up; rescue today is the onward band at minimum lift. The local restoring field (gain 2.4 / -78) is not built either.

## Lead additions (Nov 12 evening)
Build `build exit: 0` (0 warnings); full `tools/ue/test.sh` PASS 263/263; `TEST_FILTER=UmbrellaElla.BrokenMill` PASS 24;
`module_check` 0 problems; `manifest_check` 0 problems; `pipeline_check` 1 problem, same as before (settings2 area file).

### HAZ-16 (automated playtest said: one hit kills in about 1 s, no warning shown)
- Cause 1, room: the guard had no visible tell at all (only a state). Now a red placeholder card rises beside the muzzle for
  the whole warning and drops low for the quiet recovery after an aborted release (`FBrokenMillRules::GetTellPose`); the
  guard body card hides when it is down. Test: `BrokenMill.GuardProfileAndTellRules`, `BrokenMill.World.NaturalPassWarnsThenKills`.
- Cause 2, room bug: the island was a component of the guard's actor, so a friendly shot landing on the island counted as a
  guard hit, and the red shot flew through the island. The island is now its own actor (`ABrokenMillIsland`) and a solid stop
  for both shot channels. Test: `BrokenMill.World.IslandStopsShotsNeverAGuardHit` (friendly and red shots end at x 1328 / 1338,
  the island's left side minus their radius; guard HP untouched).
- Cause 3, playtest script (not this lane): it starts Ella on the target line below the commit region. Request 3.
- 20 HP comparison: `EMillGuardProfile::Comparison` changes guard HP only (10 -> 20); `SetGuardProfile` or `-MillGuardComparison`.
  The default stays the 10 HP introduction (GDD HAZ-03/12/16). Natural pass measured: 10 HP down at 1.77 s with 1 hit,
  20 HP down at 1.97 s with 2 hits (both exposed emissions); tell up 1.12 s from entry in both.
- Not done: human acceptance (player words, 1920x1080) stays with the playtest lane.

### HAZ-08..13 measured in motion (real room, real Ella, real winds and projectiles; 60 fps)
Tests: `BrokenMill.World.MeasureOnwardRideBends`, `MeasureRedRayPaths`, `MeasureFiringFixture`, `MeasureFiringWindow`,
`MeasureEmissionsPerPass`, `MeasureDelayedImpact`. Each logs `MEASURE` lines with MATCH/GAP.

| Row | Measured | GDD | Verdict |
|---|---|---|---|
| HAZ-08 onward ride, full lift trim -1/0/+1 | rises 96/120/144 per s, leaves band 210-330 after 0.63/0.50/0.42 s, upper reset then carries her LEFT (column exit x 597 at z 464-476) | stays in envelope 185-285 | GAP: onward choice is lost in motion |
| HAZ-08 onward ride, min lift 0.3 | stays in the band, exits the column right at 0.97 s; peak root 298/305/312; leaves 185-285 after 0.53/0.42/0.35 s; underside clearance at peak 13/6/-1 | 26 at root 285 | GAP |
| HAZ-09 red rays (15 across the commit region) | least rotor clearance 25.4; leftmost end x 421.6; margin to core edge 391.4: 30.2 | about 25; 421.6; about 30 | MATCH |
| HAZ-09 highest useful friendly shot | centre 532 + radius 12, rotor gap 66 | 526 + 6, gap 78 | GAP (Attack radius/muzzle) |
| HAZ-10 fixture | speed 700, damage 10, range 1500, burst 1, fall 264/330/396, rise 120: match. Muzzle +60/0, radius 12, first cadence gap 0.183 s | +44/+6, radius 6, 0.200 s | GAP (request 4); HeroSize not built |
| HAZ-11 exposed root band | 402.5-531.5, width 129, no holes; 0.489/0.391/0.326 s at fall 264/330/396 | 402-520, width 118; 0.447/0.358/0.298 s | GAP (same cause) |
| HAZ-12 worked case from root 680 | emission roots 674.5/614/548/482/416/350, hits 482 and 416 | 680/614/548/482/416/350, 482/416 exposed | MATCH except the first emission leaves after one frame of fall |
| HAZ-12 hits per pass (10 phases) | fall 264: 2-3; 330: 2-2; 396: 1-2 | 2-3 / 1-2 / 1-2 | 264 and 396 MATCH; 330 never gave 1 (wider band) |
| HAZ-13 first contact from x 650 | 0.983 s (muzzle x 710) | 1.014 s (muzzle 694) | GAP (muzzle) |
| HAZ-13 drift after closing out of the onward current | carried at 268/s, residual drift 20.2 | about 30 (wind 360, decay 12) | GAP: room wind 300 and Motor clamp 290 cap drift near 24 |
| HAZ-13 delayed impact after reopening | shot lands 0.98 s after emission while Ella has reopened and risen; target visible until impact | stays alive/visible | MATCH |

### Open (decisions for the lead/designer)
- HAZ-08 GAP is the missing local restoring field (HAZ-07: gain 2.4 / -78, not this area's IDs). Without it the onward
  current does not hold Ella; at full lift the upper reset takes her back. Building it is in this file lane.
- The Attack fixture differences (request 4) change the window, rotor gap and contact time; GDD HAZ-10 forbids tuning them
  for this room, so they stay.
