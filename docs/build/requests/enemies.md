# Requests from the enemies lane

## 1. Tuning member (Core/UmbrellaTuning.h)
Add `#include "Enemy/EnemyTuning.h"` and
`UPROPERTY(Config, EditAnywhere, Category = "Enemy") FEnemyTuning Enemy;`
Until then the lane reads `FEnemyTuning()` defaults directly (same values).

## 2. EnemyKilled event (Core/UmbrellaEvent.h)
Append `EnemyKilled` to `EUmbrellaEventType` (SourceId = enemy, Detail = type name Roadwarden/Floodstrider/SkyCourier, Value = max HP).
Until then enemies broadcast `BossPartDestroyed` with Detail=`Enemy` on a kill. Courier withdrawal broadcasts nothing (no kill XP).
The GDD gives no kill-XP number, so the lane does not broadcast `XPAwarded`.

## 3. Projectile service
`AUmbrellaProjectile` is a stub (no motion, no contact). Enemies call `AUmbrellaProjectile::Fire` and implement
`IUmbrellaShotReceiver`; they need the service to call `ReceiveShot` on the hit actor. Hit box blocks `PlayerShot`.

## 4. Open rounding
FLOW-46 "rounding for indivisible totals" is OPEN in the GDD. Default built: yellow count = floor(Count / (RedPerYellow + 1)),
raised to the reserved early-yellow count.

## Wind overlap never reaches the Motor (found by BrokenMill.World.WindCarriesEllaPastOneShotPerPass)
`AWindCurrent::BroadcastEntered/Exited` (Field lane) sets `TargetId = Other->GetFName()` (the pawn's actor name, e.g.
`BP_Ella_C_0`). `UEllaMotorComponent::IsEventForElla` (Motor lane) accepts only `TargetId == UmbrellaPlayerIds::Ella` or none,
so a real overlap is ignored and no wind ever moves Ella in play. Fix on main (either one):
- `Private/Field/WindCurrent.cpp`: when `Other` is the player pawn (`Cast<APawn>(Other)->IsPlayerControlled()` or `Other->IsA<AEllaCharacter>()`),
  use `UmbrellaPlayerIds::Ella` as `TargetId` in both Broadcast functions; or
- `Private/Motor/EllaMotorComponent.cpp` `IsEventForElla`: also accept `Event.TargetId == GetOwner()->GetFName()`.
The enemies test works around it by broadcasting the event with `TargetId = Ella` and the wind actor's own force and label.
