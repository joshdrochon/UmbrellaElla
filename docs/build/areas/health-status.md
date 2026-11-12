# health status

## G1 done (branch area/health)
| Rule ID | Built | Proved by |
|---|---|---|
| SURV-05 | health + lives model, post-hit protection 0.65 s, lift 0.3 + 0.7 x active/capacity, no revival | `Health.ThreeHitsCostALife`, `Health.FinalDepletionDefeatsOnceAndNoRevival`, `Health.LiftFollowsActiveHealthOnly`, `Health.World.PostHitProtectionBlocksSecondHit` |
| SURV-07 | 3 x 3 baseline, heal 0.5 / 0.8 / 1.1 / 1.4 by rank, active first then reserves, capped at max lives | `Health.HealingActiveFirstThenReserves`, `Health.World.YellowDuringAbsorbFallHealsAndIsConsumed` |
| FLOW-30 | one top-left clock in the 16:9 view, text >= 18 px (C++ canvas HUD) | `Health.ClockHudInsideSixteenByNineView`, `Health.ClockHudTextAtLeast18Px` |
| FLOW-31 | life hand, depletion, XII on defeat; PlayerDefeated once | `Health.LifeHandAdvancesTowardXIIAndEndsAtXII`, `Health.World.LastLifeBroadcastsDefeatedOnce` |
| FLOW-32 | gold arc, hands move on hit/heal, capped-speed follow (no gameplay delay), full-health catch distinct from healing | `Health.DrawnHandFollowsWithoutGameplayDelay`, `Health.World.FullHealthCatchIsValidAndNotHealing` |
| FLOW-33 | damage 1 / 1.25 / 1.5, defense applied once (1 / .9 / .8 / .7), overflow carries across lives | `Health.DamageScaleByDefenseRank`, `Health.DamageOverflowCarriesAcrossLives` |
| Projectile Service | motion X/Z, swept radius contact, lifetime, receiver chain by priority, player shots skip Ella, enemy shots only touch Ella, events | `Projectile.*`, `Health.World.PlayerShotsPassThroughElla`, `Health.World.RedShotCostsOneHit` |
Also: absorb component (yellow only during absorb-fall, red CatchFailed), `ResetForRetry`.

## Not run
- No HUD screenshot / PIE: the HUD drawing is untested visually (layout math is tested).
- Package: build lead.

## Left (G3 later list)
SURV-06, FLOW-05..FLOW-23 (except FLOW-09), FLOW-42, FLOW-48: progression (XP, level-62 curve, tracks, checkpoints,
persistence, run scaling, Final Hour, XP ring). Oracle `tools/progression_model.py`.
