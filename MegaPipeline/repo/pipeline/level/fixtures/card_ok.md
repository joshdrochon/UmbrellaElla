Fixture: an encounter card that passes `encounter_check.py --card`. Names and dates are made up for the test.

## Evidence
```
breather contest: 6.5 s
encounter_check: 0 problem(s)
```
Coverage signed: Sam Lee 2026-11-20
Accent check: no amber or red outside bolts, tells and the arc. Ana Ruiz 2026-11-20
Motion check: nothing but projectiles moves within 64 px of a projectile. Ana Ruiz 2026-11-20
Paper walk: #41 (no change)

## Engine tests
- `UmbrellaElla.Owl.EveryPatternHasTelegraph` PASS
- `UmbrellaElla.Owl.PhaseTableDistinct` PASS
- Not run: `UmbrellaElla.Owl.World.OriginLockedDuringTelegraph` (#20)
- Not run: `UmbrellaElla.Owl.World.PhaseChangePlaysCue` (#20)
- Not run: `UmbrellaElla.Owl.World.NoDamageAfterEndTrigger` (#20)
