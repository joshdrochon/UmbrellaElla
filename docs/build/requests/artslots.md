# artslots requests

## Playtest FLOW-25 measures 0/9 because of GetActorBounds(true, ...)
File: `Source/UmbrellaElla/Private/Smoke/PlaytestRun.cpp`, the stage loop that builds `Boxes` (~line 622).
`Layers[Index]->GetActorBounds(true, Origin, Extent)`: first arg is `bOnlyCollidingComponents`. Backdrop panels have no
collision, so Extent is zero and no layer ever covers a frame (log run-2026-11-12c: stages_covered=0).
Exact change: replace the Origin/Extent block with
`Boxes.Add(UUmbrellaBackdropSubsystem::LayerFootprint(CameraX, Specs[Index].Parallax));`
(or drop the loop: `Covered = Backdrop->CountCoveredStages();`). Both are on this branch and tested by
`UmbrellaElla.Feedback.World.BackdropCoversRoute`.
