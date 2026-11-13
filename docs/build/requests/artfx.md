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

## 5. Check defects that stop every VFX piece (triage verdict: "check defect", Nov 13; main e10efbd9 still has all three)
Evidence: gold impact v2 (`pipeline/art/proof/artfx/GoldImpact/sheet.png`), 9-session panel: verdict=reference, calibration 3/9, score 0.526.
1. `tools/art_check.py` colour rules (on_palette, off_style, off_band) are full-frame rules. A gold sprite with bronze/amber shading
   fails them (on_palette 0.55, off_style 0.32, off_band 0.15). Needed: a sprite/effect mode that reads only the non-transparent
   pixels against the effect palette, with a test on a known-good and a known-bad sprite.
2. Critic sessions miss calibration folder C (clearly different pair) and answer SAME: 3/9 calibrated, so a round cannot count.
   Needed: a calibrated-session rule (re-draw uncalibrated sessions until N calibrated) or a fixed folder C prompt.
3. The `context` pair compares a near-black graybox capture against the key art, so it judges the scene, not the burst.
   Needed: a context reference for effects (a crop of the effect in the key art, or an effect-on-its-own-background capture).
Until these land no `vfx-*` piece can pass; more paint would only add `_PH` candidates. Spend stays 4.56 of 33.82.
