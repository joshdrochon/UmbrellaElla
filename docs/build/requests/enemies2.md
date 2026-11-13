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

## 3. Playtest lane (`Smoke/PlaytestRun.cpp`): start the HAZ-16 run where a natural pass starts
The scripted HAZ run puts Ella at `(RoomStartX, TargetCentre.Y)` = root z 455, below the commit region (z 620-690),
so the guard can never warn (`warned=0`) and the first shot on the line kills it (`run_s=1.00`). A natural pass enters
the commit region from the left. Change: start at `(Mill.ActivationX.X + 10, 680)` and hold Shoot (no trim steering needed;
the shoot-fall crosses the exposed band). `BrokenMill.World.NaturalPassWarnsThenKills` measures that pass in the real
room: tell up 1.1 s, guard shot released once, 10 HP down at 1.77 s (one hit, root 482), 20 HP comparison down at
1.97 s (two hits, roots 482 / 416). For the 20 HP comparison run add `-MillGuardComparison` (the room reads it in BuildRoom).
The room also has a visible tell now (`ABrokenMillRoom::GetTellVisual()`, `GetTellPose()`), if the run should read it.

## 4. Attack lane: the Small Blast fixture differs from GDD HAZ-10 (decision, not a fix in this lane)
Measured in motion (`BrokenMill.World.MeasureFiringFixture`): muzzle offset +60 / 0 (GDD +44 / +6 at HeroSize 1),
blast radius 12 (GDD 6), first cadence gap 0.183 s at 60 fps (the countdown starts at -dt, so the second shot leaves one
frame early; later gaps 0.200). GDD HAZ-10 says keep cadence and movement unchanged and do not tune them for this room,
so this lane does not touch them. They widen the exposed band to 402-532 (GDD 402-520) and cut the rotor gap to 66 (GDD 78).
