# Owl sharpness (Josh, Nov 13 ~20:30): where the softness comes from

`owl-sharpness-side-by-side.png`, same crop, left to right (all scaled to the 944x622 cell; in-game panels pixel-repeated):
1. raw video frame (keeper-idle.mp4, frame 4 at 12 fps, 1280x720, on green)
2. keyed grid cell 2 of the approved grid (oid 8bb4d531, unchanged), over grey
3. in-game before (`ingame-before-1280.png`, 1280x720, -SmokeKeeper)
4. in-game after, PREVIEW only (`ingame-after-preview-sharpen1-1280.png`: same run with `-ExecCmds="r.Tonemapper.Sharpen 1"`; nothing committed, the setting is engine-wide and not this lane's)

Numbers: `owl-sharpness.json`, made by `tools/build/assets/art_keeper_sharpness.py` (any python with numpy, e.g. Blender's
`python3.13 -I`). Sharpness = mean luma gradient on the inner figure; "ideal" = the cell downscaled with lanczos to the
same on-screen size.
