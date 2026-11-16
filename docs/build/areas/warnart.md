# Area: warnart

Started by the build lead from Josh's order (2026-11-14, main 63266143). It is the definition of done.

1. Talon and chain-cast warning: a soft painted streak in the etched style (tapered, feathered edge, slight glow, low
   opacity at the tail), not a flat uniform solid line. Same colour family (#ff3658), same timing and hit areas.
2. Warning ring around the mechanism (VFX_KeeperWarning): a soft broken painted arc or pulse, not a hard neon circle.
3. visual_qa keeper must not drop; flat_box must pass. Before/after frames during a real talon and chain-cast warning.
Never: change approved art, touch Josh's game or the main checkout, add to approvals.json.

## Cross-area changes
- Owl (`Private/Owl/KeeperOfTime.cpp`): `TelegraphVisual` shows the painted streak (VFX sheet quad) instead of a flat cube;
  the talon tip cube is not drawn under the Keeper's art (a flat 29x30 px white square flat_box flagged at the claw).
  Hit areas and timing unchanged (presentation only).
- Feedback/Vfx (`VfxSheetVisual.cpp`): the VFX_KeeperWarning sheet loads the painted ring (`PaintedWarningArt::RingSheet`)
  in place of the placeholder; the catalog row (size, frames, fps, light) is unchanged. New `VfxSheetVisual::ShowTexture`.
- Defense (`AbsorbReceiverComponent.cpp`) and Encounter (`EncounterDirectorSubsystem.cpp` DeliverDamage), D-new-chain-absorb:
  holding Absorb blocks a chain cast; the Director asks Ella's shot receivers in priority order (Absorb first).
- Smoke (`SmokeHookSubsystem`, workbench only): `-SmokeHoldEllaAt=<x>,<z>` holds Ella at an arena fraction (full life
  kept) and the shot logs `SMOKE_AIM` (cast start, end, Ella, angle). `FKeeperFightModel::GetLockStart/GetLockEnd`.
