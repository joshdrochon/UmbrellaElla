# Requests from the health lane

## Open design details (decision rows, not code changes)
- **Life-hand positions** (FLOW-31 says exact angles are OPEN; do not invent). The HUD ships a prototype default so the
  clock is readable: life hand at IX with all lives, stepping toward XII as lives are lost, XII on defeat; restoring
  progress moves it back toward the next slot. Numbers: `FHudTuning::LifeHandFullDegrees` (270). The Producer should add
  a `docs/decisions.md` row if a different mapping is wanted.
- **Hit during post-hit protection**: the shot is consumed with no damage (it cannot wait outside and land later).

## Contract notes (no Core diff needed)
- **Absorb-fall input**: `UAbsorbReceiverComponent::SetPose(EAbsorbPose::AbsorbFall)` or an `UmbrellaConfigChanged` event
  with `Detail = "AbsorbFall"` and `Amount` 1 (on) / 0 (off). `UUmbrellaStateComponent` has no public getter yet, so the
  umbrella lane should broadcast that event on entering/leaving absorb-fall.
- **Lift**: `UUmbrellaHealthComponent::GetLiftMultiplier()` returns 0.3 + 0.7 x active/capacity. The motor/umbrella lane
  multiplies lift by it (no hard reference needed beyond `AEllaCharacter::GetHealth()`).
- **Receivers**: `IUmbrellaShotReceiver` gained `GetShotPriority()` (default 0). Keeper parts implement `ReceiveShot`;
  enemy shots only touch `AEllaCharacter` or actors tagged `Player`, player shots touch everything else with collision
  (query uses all object types, so the target needs collision enabled).
- **Retry**: Flow calls `UUmbrellaHealthComponent::ResetForRetry()`.
- `Content/UmbrellaElla/UI/HUD/**` is unused: the HUD is C++ canvas drawing, no assets.
