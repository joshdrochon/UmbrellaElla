# artslots requests

## Playtest FLOW-25 measures 0/9 because of GetActorBounds(true, ...)
File: `Source/UmbrellaElla/Private/Smoke/PlaytestRun.cpp`, the stage loop that builds `Boxes` (~line 622).
`Layers[Index]->GetActorBounds(true, Origin, Extent)`: first arg is `bOnlyCollidingComponents`. Backdrop panels have no
collision, so Extent is zero and no layer ever covers a frame (log run-2026-11-12c: stages_covered=0).
Exact change: replace the Origin/Extent block with
`Boxes.Add(UUmbrellaBackdropSubsystem::LayerFootprint(CameraX, Specs[Index].Parallax));`
(or drop the loop: `Covered = Backdrop->CountCoveredStages();`). Both are on this branch and tested by
`UmbrellaElla.Feedback.World.BackdropCoversRoute`.

## Roadwarden equipment is not stored on the enemy (request 2)
File: `Source/UmbrellaElla/Public/Enemy/UmbrellaEnemy.h`. Add `UPROPERTY(EditAnywhere) ERoadwardenEquipment Equipment` plus
`ERoadwardenEquipment GetEquipment() const`. Until then the presenter keeps the variant itself:
`UEnemyPresenterSubsystem::SetEquipment(Enemy, Equipment)` (default SundialCaster). When the getter exists, call
`SetEquipment` from `ShowStandIn` with it.

## Stream beam rescales its cube after the art swap (request 3)
File: `Source/UmbrellaElla/Private/Attack/StreamBeamActor.cpp` line 114. `Visual->SetWorldScale3D(FVector(...))` writes a cube scale even when
the beam shows a picture (a plane). Exact change: replace it with
`ArtSlot::SetWorldBoxScale(Visual, FVector(FMath::Max(EffectiveLength, MinVisualLength) / CubeSize, BeamWidth / CubeSize * VisualDepthFraction, BeamWidth / CubeSize));`
(ArtSlot.h is already included there; it falls back to the same world scale while a cube shows). Until then `UShotPresenterSubsystem` re-sizes the picture on its tick, so
the wrong scale can show for the frames between a beam step and the next presenter tick.
