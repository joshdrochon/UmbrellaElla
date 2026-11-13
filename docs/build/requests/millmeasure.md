# Requests from millmeasure (HAZ-08..13)

## 1. Motor hook for the HAZ-08 local restoring field (Motor / Field lane, with HAZ-07)
`FBrokenMillTuning::LocalRestoringGain` (2.4) and `LocalVerticalCompensation` (-78) exist but nothing reads them. The
onward ride needs a vertical pull toward the current's centre z 230 while Ella is inside the lower onward band. The
wind actor never writes velocity, so the Motor needs one input: an optional per-wind vertical term
`Vz += Gain * (CentreZ - RootZ) + Compensation`, carried on the WindEntered event (Value/Detail) or a new field.
Measured without it (MeasureOnwardRideBends): full lift leaves envelope 185-285 after 0.12-0.17 s, then the upper reset
carries her left.

## 2. HAZ-13 drift: Motor wind clamp 290 (Motor lane)
GDD estimate assumes wind 360, decay 12 (about 30 residual units). Room wind is 300 and the Motor clamps at 290, so the
measured residual drift is 20.2. Either raise the room WindSpeed and the clamp together or accept 20 and update the GDD row.

HAZ-09 shot radius, HAZ-10 muzzle/radius/cadence and HeroSize are in requests/enemies2.md item 4 (Attack lane).

## 3. Island shot margin (BrokenMill room, enemies2 lane)
After D-new-smallblast-fixture the exposed band is 390.5-519.5 vs GDD 402-520. `IslandShotMargin` (12) is only in the rule; the
island collider stops a shot at its top (390). Make the room block at IslandTop + IslandShotMargin, or drop the margin from the GDD row.
