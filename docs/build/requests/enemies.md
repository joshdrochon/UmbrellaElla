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
