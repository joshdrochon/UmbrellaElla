# playtest requests

## 1. Real wind currents never move Ella (blocks CAM-04, CAM-07; affects every wind in the game)
Found by the played `-SmokePlaytest` run, Nov 12 (log `the playtest run log run-2026-11-12b (playtest worktree, not committed)`, line `PLAYTEST_WINDDIAG`):
`ella_id=EllaCharacter_0 contract_id=Ella overlap=1 rode_from_volume=0 rode_with_contract_id=1`.
Ella is inside the Broken Mill lower current, the volume broadcasts `WindEntered`, and the Motor drops it.

Cause: `AWindCurrent::BroadcastEntered/Exited` (Field) set `TargetId = Other->GetFName()` (the actor name, `EllaCharacter_0`),
the repo-wide convention (Projectile, Trap, StreamBeam, Health do the same; `WindTests` asserts "target is pawn").
`UEllaMotorComponent::IsEventForElla` (Motor) accepts only `NAME_None` or `UmbrellaPlayerIds::Ella`. No test joins the two:
Motor tests send `TargetId` None, Wind tests stop at the event.

Fix (Motor lane, one line; follows the convention instead of changing every sender):

```diff
--- a/Source/UmbrellaElla/Private/Motor/EllaMotorComponent.cpp
+++ b/Source/UmbrellaElla/Private/Motor/EllaMotorComponent.cpp
 bool UEllaMotorComponent::IsEventForElla(const FUmbrellaEvent& Event) const
 {
-	return Event.TargetId.IsNone() || Event.TargetId == UmbrellaPlayerIds::Ella;
+	const AActor* Owner = GetOwner();
+	return Event.TargetId.IsNone() || Event.TargetId == UmbrellaPlayerIds::Ella || (Owner && Event.TargetId == Owner->GetFName());
 }
```

Plus a world test (Motor or Field lane): spawn Ella and an `AWindCurrent`, move Ella into the volume, step the motor,
read `IsRiding()` and a positive X velocity. The playtest re-run after the fix: `-SmokePlaytest` (no relay flag).

Workaround in this lane: `-PlaytestWindRelay` re-sends the volume's events with `TargetId=Ella`. Its lines carry
`relay=1`; `tools/build/playtest_check.py` prints them as a projection and never counts them toward a row.
