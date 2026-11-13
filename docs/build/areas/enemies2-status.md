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
