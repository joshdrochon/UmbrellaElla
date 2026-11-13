# Requests from the enemies2 lane

## 1. Ella's collision capsule (Core/EllaCharacter.cpp)
Ella uses the ACharacter default capsule (radius 34, half height 88). GDD SH1.0 HAZ-08/HAZ-09 size the Broken Mill
around a hurtbox of max half width 23.4 and max half height 39 (`FBrokenMillTuning::MaxHalfWidth/MaxHalfHeight`).
With 88 a root in the 30-unit gap between the mill winds touches both bands (`BrokenMill.World.RealWindsPickedByReopenHeight`
measured it before the room gate), and the underpass/floor clearances in HAZ-08 do not hold.
Change: in `AEllaCharacter::AEllaCharacter()` add `GetCapsuleComponent()->InitCapsuleSize(<half width>, <half height>);`
from the Health/Motor hurtbox tuning (owner decides the struct; GDD max values 23.4 / 39).
Workaround in lane: the room gates its wind volumes by Ella's root, so the capsule size no longer decides the wind.

## 2. WIND-03 (already in docs/build/requests/enemies.md, levelchunks lane)
Still open on main 89f6241. The enemies2 world tests name Ella `Ella` until it lands.
