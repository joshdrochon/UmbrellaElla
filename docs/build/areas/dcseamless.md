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
