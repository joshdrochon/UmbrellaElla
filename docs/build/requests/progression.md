# Requests from progression

## 1. Add a Progression member to UUmbrellaTuning (Core)
File: `Source/UmbrellaElla/Public/Core/UmbrellaTuning.h`

```cpp
#include "Progression/ProgressionTuning.h"
...
	UPROPERTY(Config, EditAnywhere, Category = "Progression")
	FProgressionTuning Progression;
```

Why: worker rule says numbers are read as `GetDefault<UUmbrellaTuning>()->Progression.X`. Until then
`UProgressionSubsystem::GetTuning()` returns a default-constructed `FProgressionTuning` (same shipped values), and every rule
function takes the tuning by const reference, so switching is a one-line change in `GetTuning()`.

## 2. Event details progression expects (for keeper, enemies, flow)
- `ModeSelected` Detail contains `Director` (Director's Cut) or `Start` (Start Game).
- `BossPartDestroyed`: Detail, TargetId or SourceId names the kill: `Roadwarden`, `Floodstrider`, `Courier`, `Wings`,
  `Front`, `Middle`, `Rear`, `Clock` (case-insensitive substring). `CourierWithdrawal` pays nothing.
- `CheckpointReached` Detail contains `Phase`, `Boss` or `Keeper` for a boss checkpoint; anything else is a level checkpoint.
- `CheckpointRetried` on every death retry. `EncounterCompleted` or `RunCompleted` on a win (counted once per run).
- Flow: after a refuge/run-start screen call `UProgressionSubsystem::SetPurchaseContext`; show `UProgressionPurchaseWidget`
  and `UXpRingWidget::Show` (Director's Cut only).
