# Requests from the health lane

## Open design details (decision rows, not code changes)
- **Life-hand positions** (FLOW-31 says exact angles are OPEN; do not invent). The HUD ships a prototype default so the
  clock is readable: life hand at IX with all lives, stepping toward XII as lives are lost, XII on defeat; restoring
  progress moves it back toward the next slot. Numbers: `FHudTuning::LifeHandFullDegrees` (270). The Producer should add
  a `docs/decisions.md` row if a different mapping is wanted.
- **Hit during post-hit protection**: the shot is consumed with no damage (it cannot wait outside and land later).

## Contract notes (no Core diff needed)
- **Absorb-fall input**: the absorb receiver reads `UUmbrellaStateComponent::GetAction()` on every Ella `UmbrellaConfigChanged` (spell equips share that event, so Detail is ignored). `SetPose` stays for tests.
- **Lift**: `UUmbrellaHealthComponent::GetLiftMultiplier()` returns 0.3 + 0.7 x active/capacity. The motor/umbrella lane
  multiplies lift by it (no hard reference needed beyond `AEllaCharacter::GetHealth()`).
- **Receivers**: `IUmbrellaShotReceiver` gained `GetShotPriority()` (default 0). Keeper parts implement `ReceiveShot`;
  enemy shots only touch `AEllaCharacter` or actors tagged `Player`, player shots touch everything else with collision
  (query uses all object types, so the target needs collision enabled).
- **Retry**: Health listens for `CheckpointRetried` (TargetId Ella, Amount equal to its MaxLives) and restores to its own MaxLives; nobody calls `ResetForRetry()` directly.
- `Content/UmbrellaElla/UI/HUD/**` is unused: the HUD is C++ canvas drawing, no assets.

## Core request (shared header)
- **GUST_Band SourceId**: Health bypasses post-hit protection for SourceId `GUST_Band` (keeper emits exactly that, see keeper.md). Both lanes hard-code the name; please add `UmbrellaSourceIds::GustBand = "GUST_Band"` to a Core header (e.g. `Core/UmbrellaPlayerIds.h` sibling) so one constant is shared. Health keeps its local constant until then.
