# Area: dcseamless

Started from the lead brief (2026-11-14). It is the definition of done.

Josh, Nov 13 23:45: the Director's Cut route's background must read as one seamless painted world (no picture edges,
seams, repeated tiles, panels or frame borders), judged as the whole frame against Ricky's Other Realm study.
Hard limits: the 8 approved backdrop layers T_Bg*_PH and the title screen are locked (pipeline/art/approvals.json); fix
seams through composition only (placement, tiling, cross-fade, overlap, parallax ranges, edge fades or masks, removing
stray quads). New art only as a separate piece in its own slot, reported.
Steps: capture the DC route start to end and list each seam (x-range, file:line); fix one by one, measuring each seam
before and after; add a test that fails on the old seams; gate it.
Lane: Source/UmbrellaElla/*/Feedback/Background/**, the edge-fade path in Feedback/Art/ArtSlot.*,
Source/UmbrellaElla/Private/Tests/Feedback/BackdropSeamTests.cpp (+ the backdrop loop test it replaces),
tools/build/assets/art_slot_fade_material.py, tools/build/assets/art_scene_frameseam.py, tests/test_art_scene_frameseam.py,
Content/UmbrellaElla/Materials/M_ArtSlot_EdgeFade.uasset, pipeline/art/proof/dcseamless/**.

Lane extension (Nov 14, coordinator order on Josh's jolt report ~00:55: "pressing Space to move forward jolts the view";
Josh authorized merging without him): the jolt's cause is the camera follow, so this lane also owns the camera-follow
change in Source/UmbrellaElla/Public/Level/UmbrellaLevelDirector.h, Private/Level/UmbrellaLevelDirector.cpp
(StepCameraFollow, FCameraFollowState, StepFollow's DeltaSeconds) and Private/Tests/Level/CameraFollowTests.cpp.
Nothing else in the level lane is touched; cuts (checkpoint place, respawn, handoff retry: Ella moving > 400 units in one
step) still snap the camera.

Lane extension (Nov 14, coordinator orders on Josh's 15:42 and 16:02 reports; Josh authorized merging without him):
(a) "trapped on the bottom track": the route floor bar. This lane removes the per-slot placeholder floor from
Source/UmbrellaElla/Private/Level/LevelPlan.cpp (Build). (b) "remove vertical drafts in Director's Cut": LevelPlan::IsVerticalWind
(Public/Level/LevelPlan.h, Private/Level/LevelPlan.cpp), the matching assertions in Private/Tests/Level/LevelDirectorTests.cpp
and ChunkLayoutTests.cpp, the D-new-no-vertical-wind row in docs/decisions.md and the HAZ-25/27/34/36 notes in
docs/build/rule-status.csv. The chunk catalogue (ChunkCatalogueData.h, ChunkLayouts.*) and the motor are not touched.
The lethal bottom itself is the fallrules lane (main 1d95f1fd: reaching the bottom defeats Ella).
