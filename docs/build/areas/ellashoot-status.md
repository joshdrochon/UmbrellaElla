# ellashoot status

## Done (14 Nov)
- Hip-fire: `ella-state:Shoot` draws T_Ella_Shoot_PH, 6x4 (`Art/Source/StandIns/ella-attack/ella-shoot_N24_grid.png`,
  proof `pipeline/art/proof/artella/shoot/`), cut by `tools/build/assets/art_ella_shoot_cut.py` from the R1 still at the
  idle's scale and anchor, with a baked upper-body recoil (boots fixed). The second Veo clip was not made (per-piece
  video cap; the command for Josh is with the build lead). Loops while held. Fixed: Shoot never showed in play (the
  presenter matched shots by actor name, shots carry the player id). Tests: `UmbrellaElla.Feedback.World.EllaShootAnimatesWhileShooting`,
  `UmbrellaElla.Feedback.EllaAnim.GridFrameAt`.
- Aimed shot (D-new-aimed-shot): `UAttackEmitterComponent` + `AAimedBeamActor`, `ella-state:AimShot` (T_Ella_AimShot_PH,
  6x4 from the R1 clip; its raw copy is under `Raw/` because the legs swing back by design). Tests:
  `UmbrellaElla.Move.World.AimedShotTapIsHipFire`, `UmbrellaElla.Move.World.AimedShotHoldFiresBeam`,
  `UmbrellaElla.Move.World.AimedBeamDamagesKeeper`, `UmbrellaElla.Move.AimedShotRibbonIsGradedNotFlat`.
- Hip-fire vs the Keeper: a real-input offscreen Start Game run (16 taps of J, Ella swept z 1036 -> 156) fired 58 Small
  Blasts and hit the Keeper 0 times: the part boxes spanned Y -70..-30, the shots fly at Y 25. The part box half depth
  is now `KeeperLook::PartShotHalfDepth` (Keeper plane to past the shot plane, Y -145..45); the same run: 4 hits.
  Test: `UmbrellaElla.Move.World.HipFireShotDamagesKeeperPart` (also: an enemy red shot through the wider box neither
  damages the Keeper nor stops; Keeper parts block only the player-shot channel, so Ella's own collision is unchanged).

## Open
- Owl owner / Dev Lead to confirm the Keeper part collider depth change (cross-area: `Public/Owl/KeeperLook.h`,
  `Private/Owl/KeeperPartComponent.cpp`); flagged by the gate review 14 Nov.
- Next commit after this gate: the red, thinner beam (Josh 14 Nov).
