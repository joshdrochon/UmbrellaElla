"""Cut a painted 4-frame strip on flat green into an 8 x 1 sheet of 128 px cells (art lane artfx).
  Blender -b --factory-startup -P Art/Source/VFX/Paint/cut_strip.py -- <strip.png> <out_sheet.png> [<out_keyed.png>]
Fixed geometry, no cell boxes: the green key (alpha from greenness, despill), the four bursts found as the four runs of
non-empty columns, one common scale for all four (sizes stay relative), each centred in its cell; frames doubled to 8 cells."""
import sys

import bpy
import numpy as np

src, out = sys.argv[sys.argv.index("--") + 1:][:2]
keyed_out = (sys.argv[sys.argv.index("--") + 1:] + [None, None, None])[2]
CELL, FR, FILL = 128, 4, 120
img = bpy.data.images.load(src)
w, h = img.size
px = np.array(img.pixels[:], dtype=np.float32).reshape(h, w, 4)
r, g, b = px[..., 0], px[..., 1], px[..., 2]
green = g - np.maximum(r, b)
alpha = np.clip(1.0 - (green - 0.12) / 0.30, 0.0, 1.0)
alpha[green < 0.12] = 1.0
g2 = np.minimum(g, np.maximum(r, b) + 0.02)
rgba = np.stack([r, g2, b, alpha], axis=-1)
if keyed_out:
    k = bpy.data.images.new("k", w, h, alpha=True)
    k.pixels = rgba.ravel().tolist()
    k.filepath_raw = keyed_out
    k.file_format = "PNG"
    k.save()
# fixed geometry: the burst centres sit at 1/8, 3/8, 5/8, 7/8 of the width; the cuts are the emptiest columns near 1/4, 1/2, 3/4
cnt = (alpha > 0.5).sum(axis=0)
cuts = [0]
for q in (1, 2, 3):
    lo, hi = int(w * q / 4 - w * 0.04), int(w * q / 4 + w * 0.04)
    seg = cnt[lo:hi]
    best = np.where(seg == seg.min())[0]
    cuts.append(lo + int(best[len(best) // 2]))
cuts.append(w)
merged = [[cuts[i], cuts[i + 1]] for i in range(FR)]
crops = []
for x0, x1 in merged:
    sub = alpha[:, x0:x1] > 0.5
    ys = np.where(sub.any(axis=1))[0]
    crops.append(rgba[ys[0]:ys[-1] + 1, x0:x1])
scale = FILL / max(max(c.shape[0], c.shape[1]) for c in crops)
cells = []
for c in crops:
    nh, nw = max(1, round(c.shape[0] * scale)), max(1, round(c.shape[1] * scale))
    ys = (np.arange(nh) / scale).astype(int).clip(0, c.shape[0] - 1)
    xs = (np.arange(nw) / scale).astype(int).clip(0, c.shape[1] - 1)
    # area-average downsample by box over source rows/cols
    ye = (np.arange(1, nh + 1) / scale).astype(int).clip(1, c.shape[0])
    xe = (np.arange(1, nw + 1) / scale).astype(int).clip(1, c.shape[1])
    small = np.zeros((nh, nw, 4), dtype=np.float32)
    for i in range(nh):
        for j in range(nw):
            blk = c[ys[i]:max(ye[i], ys[i] + 1), xs[j]:max(xe[j], xs[j] + 1)]
            a = blk[..., 3]
            s = a.sum()
            small[i, j, :3] = (blk[..., :3] * a[..., None]).sum(axis=(0, 1)) / s if s > 0 else 0
            small[i, j, 3] = a.mean()
    cell = np.zeros((CELL, CELL, 4), dtype=np.float32)
    y0, x0 = (CELL - nh) // 2, (CELL - nw) // 2
    cell[y0:y0 + nh, x0:x0 + nw] = small
    cells.append(cell)
sheet = np.concatenate([cells[i // 2] for i in range(8)], axis=1)
s = bpy.data.images.new("s", CELL * 8, CELL, alpha=True)
s.pixels = sheet.ravel().tolist()
s.filepath_raw = out
s.file_format = "PNG"
s.save()
print("CUT_OK bursts=%s scale=%.3f" % (merged, scale))
