# windfix status

## Done (requests/millmeasure.md items 1-3, GDD HAZ-08/13)
1. Motor hook for the local restoring field: `AWindCurrent::SetLocalVerticalField(Gain, CentreZ, Comp)` puts "Dir@gain,centreZ,comp" in WindEntered Detail; `MotorModel::HasLocalField` / `LocalVerticalTerm`; Motor adds `Gain*(CentreZ-RootZ)+Comp` to Vz while riding. Broken Mill lower band reads `LocalRestoringGain` / `LocalVerticalCompensation`, centre `LowerOnwardCentreZ` 230. Tests: `Move.WindLocalVerticalField`, `Move.WindRideAndDecay`.
2. HAZ-13: room `WindSpeed` 360; new `Motor.WindMaxSpeed` 360 (Ella's horizontal max stays 290, MOVE-21). Only HAZ-13 gives a wind speed in the GDD; forced gusts (GUST_Band) bypass the clamp.
3. Island blocks shots at IslandTop + IslandShotMargin (402): solid raised 12, drawn cube unchanged. HAZ-11 lower edge 402.5 MATCH, HAZ-12 fall 330 gives 1-2 MATCH.
Build exit 0; full suite 286/286 PASS; module_check 0, manifest_check 0. Rows HAZ-06/07/08/12/13/14 updated.

## Left
- HAZ-13 drift 23.4 vs about 30: carried 311.3/s after 0.67 s (accel 3/s), so the GDD estimate (full 360) is not reached. GDD forbids tuning; a GDD row or accel decision is Josh's.
- HeroSize not built (HAZ-10/13).
- HAZ-07 priority algorithm is unsettled in the GDD; early/late reopen test exists (TwoWindsNeverSteal).
