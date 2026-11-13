# fixkeeper status
Done: (1) `Core/UmbrellaSourceIds.h`; Health and KeeperFightModel use it. (2) Gust push is WindEntered/WindExited (SourceId GUST_Band, TargetId Ella) from the Director; `AddActorWorldOffset` removed; the Motor applies it. (3) OWL-35 off: final hit still ends EndingSuccess, only the departure is skipped. (4) Push speed is multiplied by the model's world scale.
Tests: UmbrellaElla.Keeper.World.GustPushGoesThroughWindEventsNotPosition, ...FinalHitWithDepartureOffStillEndsInSuccess. Full UmbrellaElla filter: 209 pass, 0 failed.
Left: no test for the slow-scaled gust force (needs a slow state in a world test); Director API `SetDepartureEnabledForTest` stands in for the compile-time flag.

## Review round 1 (forced gust)
- Motor has a forced-push path: WindEntered from GUST_Band goes to ForcedPushes, added in MotorModel::Step via Input.ForcedVelocity. No ride blend, no decay, ignores Action/Ride/defense.
- Tests: GustForcedPushIgnoresActionAndRide, GustIsAForcedSourceNotACurrent, GustSpeedUsesWorldScaleOnce. Gust exists only in Wings and slow only in Mechanisms, so they never overlap; push is scaled once (Value = push x scale, Motor integrates real time).
- Removed unused LastDelta. Suite: 236 pass, module_check 0 problems.
