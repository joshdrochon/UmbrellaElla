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

## Nov 12 update
- Projectile Service: a shot is destroyed on any blocking hit. A component that blocks the shot's channel (PlayerShot for
  player blasts, EnemyShot for enemy shots) and whose actor has no shot receiver stops the shot (`ProjectileRules::IsSolidStop`).
  Proved by `Projectile.World.BlockingWallDestroysShot` (blocks for both kinds; an Ignore wall lets the shot through).
- Clock HUD (SURV-05, FLOW-30, FLOW-32): unchanged tests above still pass.
- Result: build exit 0, test PASS tests=35 failed=0, module_check 0 problems, manifest_check 0 problems.

## Left
Nothing in this lane. Progression moved to the progression area. Open design item: life-hand angles (see requests/health.md).
