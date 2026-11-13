"""Cut a painted 4-frame strip on flat green into an 8 x 1 sheet of 128 px cells (art lane artfx3, with a palette grade).
  Blender -b --factory-startup -P pipeline/art/proof/artfx3/cut_strip.py -- <strip.png> <out_sheet.png> [<out_keyed.png>]
Fixed geometry, no cell boxes: the green key (alpha from greenness, despill), the four bursts found as the four runs of
non-empty columns, one common scale for all four (sizes stay relative), each centred in its cell; frames doubled to 8 cells."""
import sys

import bpy
import numpy as np
SATCAP = float(__import__('os').environ.get('SATCAP', '0.55'))

src, out = sys.argv[sys.argv.index("--") + 1:][:2]
keyed_out = (sys.argv[sys.argv.index("--") + 1:] + [None, None, None])[2]
CELL, FR, FILL = 128, int(__import__('os').environ.get('FRAMES', '4')), 120
img = bpy.data.images.load(src)
w, h = img.size
px = np.array(img.pixels[:], dtype=np.float32).reshape(h, w, 4)
r, g, b = px[..., 0], px[..., 1], px[..., 2]
green = g - np.maximum(r, b)
alpha = np.clip(1.0 - (green - 0.12) / float(__import__('os').environ.get('KEYW', '0.30')), 0.0, 1.0)  # KEYW: narrower when the painted green is muted
alpha[green < 0.12] = 1.0
g2 = np.minimum(g, np.maximum(r, b) + 0.02)
# palette grade (artfx3): the model paints lemon-yellow golds and olive shadows; pull hues 48..110 deg toward gold (42 deg)
mx = np.maximum(np.maximum(r, g2), b); mn = np.minimum(np.minimum(r, g2), b); d = mx - mn + 1e-6
hue = np.where(mx == r, ((g2 - b) / d) % 6, np.where(mx == g2, (b - r) / d + 2, (r - g2) / d + 4)) * 60.0
sat = np.where(mx > 0, d / (mx + 1e-6), 0)
t = np.clip((hue - 44.0) / 66.0, 0, 1)
newh = np.where((hue > 44) & (hue < 110), 38.0 + 4.0 * t, hue)
newh = np.where((newh < 24) | (newh > 330), 26.0, newh)
sat = np.minimum(sat, SATCAP)
if __import__('os').environ.get('NOGRADE'):  # blue-white effects: keep the painted hue
    newh, sat = hue, np.minimum(np.where(mx > 0, d / (mx + 1e-6), 0), float(__import__('os').environ.get('NOGRADE_SAT', '1.0')))
c = mx * sat; hp = (newh % 360) / 60.0; x = c * (1 - np.abs(hp % 2 - 1)); m0 = mx - c
conds = [hp < 1, hp < 2, hp < 3, hp < 4, hp < 5]
r2 = np.select(conds, [c, x, 0 * c, 0 * c, x], c) + m0
g3 = np.select(conds, [x, c, c, x, 0 * c], 0 * c) + m0
b2 = np.select(conds, [0 * c, 0 * c, x, c, c], x) + m0
rgba = np.stack([r2, g3, b2, alpha], axis=-1)
if keyed_out:
    k = bpy.data.images.new("k", w, h, alpha=True)
    k.pixels = rgba.ravel().tolist()
    k.filepath_raw = keyed_out
    k.file_format = "PNG"
    k.save()
# fixed geometry: the burst centres sit at 1/8, 3/8, 5/8, 7/8 of the width; the cuts are the emptiest columns near 1/4, 1/2, 3/4
cnt = (alpha > 0.5).sum(axis=0)
cuts = [0]
for q in range(1, FR):
    lo, hi = int(w * q / FR - w * 0.4 / FR), int(w * q / FR + w * 0.4 / FR)
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
    # ink silhouette + paper grain at cell scale (a 2 px outline painted at 1K shrinks to nothing in a 128 px cell)
    a = cell[..., 3]
    op = a > 0.5
    pad = np.pad(op, 1, constant_values=False)
    inner = pad[:-2, 1:-1] & pad[2:, 1:-1] & pad[1:-1, :-2] & pad[1:-1, 2:]
    edge = op & ~inner
    ink = np.array([0.09, 0.085, 0.078], dtype=np.float32)
    cell[..., :3][edge] = 0.15 * cell[..., :3][edge] + 0.85 * ink
    rng = np.random.RandomState(7)
    grain = 1.0 + 0.07 * (rng.rand(CELL, CELL, 1).astype(np.float32) - 0.5) * 2
    cell[..., :3] = np.where(op[..., None], np.clip(cell[..., :3] * grain, 0, 1), cell[..., :3])
    cells.append(cell)
sheet = np.concatenate([cells[i * FR // 8] for i in range(8)], axis=1)
s = bpy.data.images.new("s", CELL * 8, CELL, alpha=True)
s.pixels = sheet.ravel().tolist()
s.filepath_raw = out
s.file_format = "PNG"
s.save()
print("CUT_OK bursts=%s scale=%.3f" % (merged, scale))
