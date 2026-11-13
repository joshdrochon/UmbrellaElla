# herosize status

## Done: HAZ-10 (actor scale 0.5 x HeroSize, muzzle +44/+6 x HeroSize, blast radius x HeroSize), HAZ-13 (range upper 1.3, muzzle 57.2/7.8), HAZ-14 (HeroSize 0.75..1.3, hitbox 0.75..1)
- `FMotorTuning`: HeroSize, HeroSizeMin/Max, ActorScaleAtReference, HitboxScale, HitboxScaleMin/Max (all `// bake:`); `Motor/HeroSizeRules.h/.cpp` plain rules.
- Motor `BeginPlay` applies actor scale and capsule hitbox scale after subscribing to the bus (applying it earlier fired overlap events nobody heard and broke the BrokenMill ride measurements). Attack emitter scales muzzle offset and blast radius. Gated by HAZ_10/13/14 flags.
- Tests: `UmbrellaElla.Move.HeroSizeRules`, `UmbrellaElla.Move.World.HeroSizeScalesHurtboxAndMuzzle` (HeroSize 0.75/1.3 x hitbox 0.75/1).
- Evidence: build exit 0; full suite 307/307 PASS; module_check 0, manifest_check 0, pipeline_check 0 (commit 3481eb4d + motor fix).
- `docs/build/gdd-bindings.json`: the 8 HeroSize/hitbox gaps are now bound to the new fields.

## Left
- No area file existed (`docs/build/areas/herosize.md`), so scope came from the HeroSize rows only. `rule-status.csv` rows HAZ-10/13/14 are not updated (owned by the enemies lane).
- Muzzle is a flat offset scale; the beam and art are not re-checked at 0.75/1.3.
