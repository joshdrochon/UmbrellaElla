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

## 3. Apply run scaling to real enemies (enemies lane; FLOW-05, FLOW-06, FLOW-21) — added Nov 13
Progression owns the numbers and the rule functions; the enemies and level lanes own the actors and placement, so these clauses
stay `ii` until applied there. Rule functions ready in `Progression/ProgressionRules.h`:
`ScaledHp(Hp, Scaling)`, `ScaledFiringCooldown(Cooldown, Scaling)` (divides only an ordinary firing cooldown), and
`EnemyCount(Tuning, BaseCount, Scaling, LegalSlots, OutShortfall)`. Scaling for this run: `UProgressionSubsystem::Get(this)->GetRunScaling()`
(identity in Start Game and on run 1). Tests: `UmbrellaElla.Progression.RunScalingTouchesOnlyCooldownAndHp`, `RunScalingMatchesOracle`.

`Source/UmbrellaElla/Private/Enemy/UmbrellaEnemy.cpp`, in `AUmbrellaEnemy::Configure`, right after `Profile = FEnemyRules::MakeProfile(...)`:
```cpp
#include "Progression/ProgressionSubsystem.h"
...
	if (const UProgressionSubsystem* Progression = UProgressionSubsystem::Get(this))
	{
		const FRunScaling Scaling = Progression->GetRunScaling();
		Profile.Hp = FProgressionRules::ScaledHp(Profile.Hp, Scaling);
		// Only the shot-to-shot cycle is a firing cooldown; AimSeconds (telegraph), RecoverySeconds, ShotSpeed stay as tuned.
		Profile.CycleSeconds = FProgressionRules::ScaledFiringCooldown(Profile.CycleSeconds, Scaling);
	}
```
Keeper (keeper lane): the same `ScaledHp` on each destructible part's HP; no change to the Keeper's schedule, telegraphs or projectiles.
Count (level lane, `UmbrellaLevelDirector`): spawn `EnemyCount(...)` enemies, only into authored slots that pass the local threat cap,
and log the shortfall. Proof each lane adds: a world test that spawns an enemy with `CompletedRuns = 10` and reads `GetMaxHp() == 2 x base`,
`CycleSeconds == base / 1.3`, `AimSeconds`, `RecoverySeconds`, `ShotSpeed` unchanged.

## 4. Keep the health fraction on a capacity purchase/refund (health lane; FLOW-17) — added Nov 13
Progression now pushes ranks into Ella's health on every change (`UProgressionSubsystem::ApplyToHealth` -> `SetCapacity`,
`SetRecoveryRank`, `SetDefenseRank`). `UUmbrellaHealthComponent::SetCapacity` clamps Active instead of keeping the fraction.
`Source/UmbrellaElla/Private/Health/UmbrellaHealthComponent.cpp`, `SetCapacity`, replace the Active clamp with:
```cpp
	const float OldCapacity = State.Capacity;   // read before State.Capacity is assigned
	...
	State.Active = FProgressionRules::ActiveHealthAfterCapacityChange(State.Active, OldCapacity, State.Capacity);
```
(rule tested in `UmbrellaElla.Progression.HealthFractionKeptOnCapacityChange`: 2/3 -> 8/3 of 4, unrounded, empty stays empty).
Reserve handling on purchase/refund is OPEN in the GDD; not invented.

## 5. Flow: send the tutorial replay (flow lane; FLOW-22) — added Nov 13
When the player replays the tutorial, broadcast `ModeSelected` with Detail `TutorialReplay`; progression switches to shadow progress
and restores the earned profile on the next `ModeSelected` (`DirectorsCut`/`StartGame`). Test: `World.TutorialReplayUsesShadowProgress`.

## 6. Art-loop piece for the Final Hour intro (art/ui owners + lead tooling; FLOW-06) — added Nov 13
New widget `UFinalHourIntroWidget` (`Source/UmbrellaElla/Public/UI/Progression/FinalHourIntroWidget.h`): a full-screen story card,
dark ground, one centred line in the display font. It is the same kind of screen as the story captions, so:
- `tools/build/art_inventory.py` `WIDGET`: add `"UFinalHourIntroWidget": "ui-story-text"`.
- `pipeline/art/references.json` piece `ui-story-text`, `ui.widgets`: add `"UFinalHourIntroWidget"`.
Until then `art_inventory` and `ui_check` fail on it in precheck.

## 7. Shipped text rows (story lane, `pipeline/story/lines.csv`) — added Nov 13, ids as shipped
```
ui-final-hour-intro,screen,"Your borrowed time has run its course. Now, face the Final Hour.",,yes,FLOW-06 approved exact text; screen=final-hour; where=FinalHourIntroWidget.cpp
ui-purchase-review-0-points-in-total,screen,Review: {0} points in total,,yes,screen=purchase; where=ProgressionPurchaseWidget.cpp
ui-purchase-review-line,screen,"{0} {1} to {2}: {3} to {4}, {5}: {6} {7}",,yes,"screen=purchase; where=ProgressionPurchaseWidget.cpp (track, rank from/to, value from/to, Cost|Reallocation, n, point|points)"
ui-purchase-costs,label,Cost,,yes,screen=purchase; where=ProgressionPurchaseWidget.cpp
ui-purchase-reallocates,label,Reallocation,,yes,"screen=purchase; where=ProgressionPurchaseWidget.cpp; GDD FLOW-11 / FLOW-18 reallocation, run 2 onward"
ui-purchase-point,label,point,,yes,screen=purchase; where=ProgressionPurchaseWidget.cpp
ui-purchase-points,label,points,,yes,screen=purchase; where=ProgressionPurchaseWidget.cpp
```
(the review-line text contains commas; quote it in the CSV.)

## 8. Flow: drop the purchase screen's separate Done box (flow lane; B9) — added Nov 13
B9 (agentplay playthrough): `AUmbrellaPlayerController::ShowPurchaseScreen` adds `SFlowPurchaseDoneBox` at viewport Z+1, but
`UUserWidget::AddToViewport(Z)` puts the purchase widget at Z+10 (`UMG/Private/Blueprint/GameViewportSubsystem.cpp:192`,
"We add 10 to the zorder"), so the Done button always draws under the purchase screen's ground and panel and a click on it
lands on the panel. Progression now draws Done in the panel's own button row (`UProgressionPurchaseWidget::Done`, which calls
`ApplyCommand(EFlowCommand::Continue)`), test `UmbrellaElla.Progression.World.PurchaseDoneVisibleAndClickable`.
The flow's box is now a hidden second "Done" (the journey's `click Done` finds it first, so it still misses). Exact change in
`Source/UmbrellaElla/Private/Flow/UmbrellaPlayerController.cpp`, `ShowPurchaseScreen`: keep the Back-key holder for focus, but
give it no visible button, e.g. replace the `SUmbrellaButton` content with `SNullWidget::NullWidget` and focus the holder
itself (`SupportsKeyboardFocus` true), or delete the box and route Escape/F1/B/Menu through the existing Pause/Back input.
Then the journey line `key Escape  # the mouse cannot reach Done` can become `click Done`.
