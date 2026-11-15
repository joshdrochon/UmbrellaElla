# Area: ellashoot

Started by the build lead from Josh's brief (2026-11-14). It is the definition of done.

1. Ella's hip-fire (normal Shoot): the closed umbrella held like a lance at the waist, tip forward to the right, handle
   and closed canopy behind her; shots leave the tip. Cut to a 6x4 grid in the `ella-state:Shoot` slot (T_Ella_Shoot),
   same layout and 2x figure scale as T_Ella_Idle, looping while Shoot is held. Test: frames advance while shooting.
   If the Veo clip drifts, fall back to the approved still with a small motion.
2. Aimed shot (D-new-aimed-shot, Josh 14 Nov): tap Shoot = hip-fire as before; hold Shoot about 0.5 s = one long
   beam to the right in the game's look (painted, soft-edged, not a flat box), hitting the Keeper and enemies along its
   line for more damage than a hip-fire shot; Ella keeps falling. Numbers in feel.json; decision row. New slot
   `ella-state:AimShot` from the R1 Veo clip (play once, hold the last cell while the beam fires). Tests: tap fires
   hip-fire; a 0.5 s hold fires a beam that damages the Keeper; both states animate.
3. Follow-up (Josh/lead 14 Nov): hip-fire shots must be able to hit the Keeper (measured in a real-input run); add a
   test. After the gate: a red, thinner replacement beam (shot red #ff3658 family, about half the thickness).
Never: change approved art, touch Josh's game or the main checkout, add to approvals.json.

## Cross-area change (Owl): Keeper part collider depth
Josh's order (14 Nov, relayed by the build lead): hip-fire shots must hit the Keeper; fix the projectile plane or the part
colliders. Measured before: a real-input offscreen Start Game run fired 58 Small Blasts and hit the Keeper 0 times (part
boxes at Y -70..-30, shots at Y 25). Change: `KeeperLook::PartShotHalfDepth` (Keeper plane to past the shot plane,
Y -145..45) in `Private/Owl/KeeperPartComponent.cpp`. Measured after, same run: 4 hits. The parts still block only the
player-shot channel; an enemy shot through the box is not a hit and is not stopped
(`UmbrellaElla.Move.World.HipFireShotDamagesKeeperPart`). Owl owner / Dev Lead confirmation is open (status file).
