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

## 2. Event strings progression listens for (verified against code on area/keeper, area/flow, enemies, Broken Mill)
- `ModeSelected` (flow): Detail `DirectorsCut` or `StartGame` (substrings `Director` / `Start`).
- Enemies (`AUmbrellaEnemy::Defeat`): `BossPartDestroyed`, Detail `Enemy`, SourceId = the actor FName. Progression finds the
  `AUmbrellaEnemy` by that name in the bound bus's world and pays by `GetEnemyType()` (Roadwarden 10, Floodstrider 20, Courier 10).
- Broken Mill guard (`ABrokenMillRoom::ReceiveShot`): same event, SourceId = the room actor; paid as a Roadwarden (10), GDD HAZ-03
  calls it the introductory Roadwarden. Decision for Josh: change to 0 if the guard should not pay.
- Keeper (`UEncounterDirectorSubsystem`): SourceId `KeeperOfTime`. `BossPartDestroyed` TargetId `WINGS`, `MECH_FRONT`, `MECH_MIDDLE`,
  `MECH_REAR`, `CLOCK` (`EYE` pays nothing); Detail is the phase (`wings`, `mechanisms`, `clock`) and is ignored for XP.
  `PhaseStarted` + `CheckpointReached` Detail = phase name (always a boss checkpoint); `CheckpointRetried` Detail = phase name;
  `EncounterCompleted` Detail `success` counts a completed run once. `RunCompleted` also accepted.
- Flow: after a refuge/run-start screen call `UProgressionSubsystem::SetPurchaseContext`; show `UProgressionPurchaseWidget`
  and `UXpRingWidget::Show` (Director's Cut only).
