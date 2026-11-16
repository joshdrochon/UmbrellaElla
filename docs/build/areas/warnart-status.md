# warnart status

## Done (14 Nov)
- Painted warning streak and ring (D-new-painted-warnings), runtime textures in `PaintedWarningArt` (no asset import).
- Tests: `UmbrellaElla.Keeper.PaintedWarningIsFeatheredNotFlat` (taper, feather, soft edge, broken ring, pulse, textured
  quad); `UmbrellaElla.Keeper.World.WarningMarkerIsAThinRedLineForEveryKind` bound on the short side 24 -> 72 cm (the
  painted quad is 64 cm with a feathered edge; the old blocks were 113-126 cm and still fail).
- Measured offscreen 1280x720, smoke `-SmokeShotWhen` frames (SMOKE_KEEPER talon physical=2 stage=1; cast phase=1
  physical=3 stage=1): flat shot-red pixels talon 888 -> 22, cast 4107 -> 0; flat_box before 1 box (talon tip) -> 0.
  Keeper+Feedback+Smoke 139/139 PASS; build exit 0, 0 warnings.

- Chain cast aim (Josh, 14 Nov): offscreen cast warning with Ella held at arena (0.25, 0.5):
  `SMOKE_AIM start=1310,538 end=510,553 ella=480,540 angle_deg=0.9`. The aim is locked at the warning start (it was).
- D-new-chain-absorb: Absorb blocks the chain cast. Tests `UmbrellaElla.Keeper.World.ChainCastAimsAtEllaAndADodgeMisses`
  (aim < 2 deg; staying is hit once; moving off the line during the warning: 0 hits, aim unchanged) and
  `UmbrellaElla.Keeper.World.AbsorbBlocksTheChainCast` (Absorb: health unchanged; closed: hurt). The Absorb test FAILs
  with the block disabled (checked). Keeper+Feedback+Smoke+Health+Defense+Move 240/240 PASS.

## Open
- Owl owner / Dev Lead confirmation of the cross-area changes (talon tip cube hidden under art; Absorb blocks the chain cast).
