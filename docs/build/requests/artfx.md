# artfx requests (build lead / other lanes)

## 1. Decision needed: nearby-surface light method (VFX-07, VFX-08; row D-new-sh10-vfx-lighting, open, owner Technical Director)
- Decision needed: how active magic lights nearby cloth, metal, clouds and scenery.
- Why it matters: VFX-08 says the choice stays OPEN and must not change the unlit sprite policy silently.
- Options: (a) per-effect additive light overlay, sprites stay unlit [built, the row's default]; (b) lit sprite materials
  (`/Paper2D/DefaultLitSpriteMaterial`) plus point lights, changes the import policy in `pipeline/art/import-rules.md`;
  (c) both: overlay now, lit materials later for selected surfaces.
- Lean: (a). It needs no change to any other lane's assets.
- Built now: (a), plus an unshadowed point light on the same effect so lit stand-in meshes also respond
  (`Source/UmbrellaElla/Public/Feedback/Vfx/VfxLightPolicy.h`). Switch: `UUmbrellaVfxDirectorSubsystem::SetIlluminationEnabled`.
- Proposed test: packaged or Standalone capture, same frame with illumination on and off (not run in this lane: headless runs are `-nullrhi`).
- Choice: Technical Director / Josh.

## 2. Settings lane: reduced flash
`UUmbrellaVfxDirectorSubsystem::SetReducedFlash(bool)` must be called next to the existing
`UUmbrellaVfxSubsystem::SetReducedFlash(bool)` (request already in `docs/build/requests/visuals.md`). Until then the director's
flash dimming only follows the flash-gap limit.

## 3. Lane note: `Feedback/VFX/**` is `Feedback/Vfx/**`
The brief's lane `Feedback/VFX/**` is the existing folder `Feedback/Vfx/` on a case-insensitive disk (Mac, Windows). New files
went there. `UmbrellaVfxSubsystem.{h,cpp}` (visuals lane, merged) got one change: its bus handler skips the events the new
effect director shows (player shots, Keeper events), so no event is shown twice. `PlayForEvent` is unchanged.
Tests live in `Private/Tests/Feedback/VfxDirectorTests.cpp`.

## 4. references.json has no element for these effects
`pipeline/art/references.json` (not in this lane) has judge elements only for `owl-bolt`, `bolt-hit`, `wand-shot`,
`umbrella-repair`, `wind-*`. The four-weapon, Keeper and light-shaft sheets have no element, so `tools/art_loop.py` cannot
open a blind panel for them. Needed: elements (refs + calibration) for at least `spell-small-blasts`, `spell-stream`,
`spell-twin-stars`, `spell-needle` (refs: the `study-ella-*` spell studies, bar-casters), `keeper-warning`, `keeper-strike`,
`clock-beat` (refs: `d-clock-double-beat`, `study-keeper-red-shots`) and `light-shaft` (no reference image exists yet).
Until then every sheet stays a tracked `_PH`.
