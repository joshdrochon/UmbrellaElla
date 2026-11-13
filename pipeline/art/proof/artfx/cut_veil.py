"""Cut a painted 4-frame veil strip (full-frame overlays: light shaft, umbra, blackout, slow, spill) into an 8 x 1 sheet (art lane artfx).
  Blender -b --factory-startup -P pipeline/art/proof/artfx/cut_veil.py -- <strip.png> <out_sheet.png> <light|dark>
The picture is a 2 x 2 grid of four equal frames (row-major) painted edge to edge on a flat background: pure black for 'light' pieces (alpha = brightness),
pure white for 'dark' pieces (alpha = darkness). Each frame is box-averaged to a 128 px cell; frames doubled to 8 cells."""
import sys

import bpy
import numpy as np

src, out, mode = sys.argv[sys.argv.index("--") + 1:][:3]
CELL = 128
img = bpy.data.images.load(src)
w, h = img.size
px = np.array(img.pixels[:], dtype=np.float32).reshape(h, w, 4)[..., :3]
fw, fh = w // 2, h // 2
cells = []
for i in range(4):
    r0, c0 = divmod(i, 2)
    ih, iw = int(fh * 0.04), int(fw * 0.04)  # inset: the model draws a thin divider between panels
    f = px[r0 * fh + ih:(r0 + 1) * fh - ih, c0 * fw + iw:(c0 + 1) * fw - iw]
    fh2, fw2 = (f.shape[0] // CELL) * CELL, (f.shape[1] // CELL) * CELL
    f = f[:fh2, :fw2]
    f = f.reshape(CELL, fh2 // CELL, CELL, fw2 // CELL, 3).mean(axis=(1, 3))
    lum = f.mean(axis=2)
    if mode == "light":
        a = np.clip((lum - 0.04) / 0.9, 0, 1)
        rgb = f / np.maximum(lum[..., None], 1e-3) * np.minimum(lum[..., None] / 0.9, 1.0)
        rgb = np.clip(f / np.maximum(a[..., None], 0.05), 0, 1)
    else:
        a = np.clip((0.96 - lum) / 0.9, 0, 1)
        rgb = np.clip(1.0 - (1.0 - f) / np.maximum(a[..., None], 0.05), 0, 1)
    cells.append(np.concatenate([rgb, a[..., None]], axis=2).astype(np.float32))
sheet = np.concatenate([cells[i // 2] for i in range(8)], axis=1)
s = bpy.data.images.new("s", CELL * 8, CELL, alpha=True)
s.pixels = np.flipud(sheet).ravel().tolist() if False else sheet.ravel().tolist()
s.filepath_raw = out
s.file_format = "PNG"
s.save()
print("CUT_VEIL_OK", mode)
