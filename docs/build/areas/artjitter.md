# Area: artjitter

Started by the build lead from this brief (2026-11-12). It is the definition of done.

Area artjitter (art pipeline tools). Josh watched the Ella previews (area/artella the Ella previews on area/artella (pipeline art proof, preview folder)): they look good but jitter. Build:
1. Frame registration in the strip cutter (find it: tools/assetgen.py frames --cells and/or the art lanes' cut/fit scripts; make the shared one do it and point lanes at it): for each frame, find the anchor from the frame's alpha mask (feet / umbrella-handle pivot: e.g. the bottom-centre of the mask's lowest solid band, configurable per element in references.json or the sheet sidecar), translate every frame so the anchor sits at the same pixel, and normalise scale (mask height or a stable reference span) to the strip's median. Write the anchor into the sidecar.
2. A jitter check in tools/art_loop.py checks (and art_check sprite mode if that is where frame checks live): measure anchor offset (px) and scale drift (%) between consecutive frames; FAIL above a limit. Set the limit from a smooth reference animation (a reference sheet in pipeline/art/reference with cells, measured once and recorded with its source), never by eye.
3. Tests: a deliberately shaken strip (random 3-6 px offsets and 5% scale wobble) fails; the same strip after registration passes; the reference sheet passes.
Files: the cutter, tools/art_loop.py (the check only), the sprite check, tests, docs/build/art-image-model.md (one paragraph: 'Frame registration and jitter'). Targeted tests only. Merge main first. Commit, stop.
