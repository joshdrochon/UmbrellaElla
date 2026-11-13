"""Fit a keyed painted shot to a game canvas: crop to the alpha box, scale to FRACTION of the canvas width
(height for tall), centre. Run: Blender -b -P art_shots_fit.py -- in.png out.png W H FRACTION"""
import sys
import bpy
import numpy as np

ARGS = sys.argv[sys.argv.index("--") + 1:]
SRC, DST, CW, CH, FRAC = ARGS[:5]
RAMPS = {"red": ["171614", "8F173C", "FF3658", "FF7848", "FFF5DC"],
         "gold": ["171614", "94611E", "F5AA28", "FFD84A", "FFF5DC"]}
SNAP = ARGS[5] if len(ARGS) > 5 else ""
SOFT = float(ARGS[6]) if len(ARGS) > 6 else 0.0
NOISE = float(ARGS[7]) if len(ARGS) > 7 else 0.0   # grain: jitter the tone before snapping, so edges between ramp colours break up
CW, CH, FRAC = int(CW), int(CH), float(FRAC)
img = bpy.data.images.load(SRC)
w, h = img.size
a = np.array(img.pixels[:], dtype=np.float32).reshape(h, w, 4)
ys, xs = np.where(a[..., 3] > 0.02)
a = a[ys.min():ys.max() + 1, xs.min():xs.max() + 1]
h, w = a.shape[:2]
k = min(CW * FRAC / w, CH * FRAC / h) if CW == CH else CW * FRAC / w
nw, nh = max(1, round(w * k)), max(1, round(h * k))
tmp = bpy.data.images.new("t", w, h, alpha=True)
tmp.pixels = a.ravel().tolist()
tmp.alpha_mode = 'STRAIGHT'
tmp.scale(nw, nh)
s = np.array(tmp.pixels[:], dtype=np.float32).reshape(nh, nw, 4)
if SNAP:   # every opaque pixel becomes the nearest ramp colour; alpha kept
    cols = np.array([[int(h[i:i + 2], 16) / 255 for i in (0, 2, 4)] for h in RAMPS[SNAP]], np.float32)
    lin = cols   # 8-bit PNG pixels are read as sRGB values
    src = s[..., :3] + (np.random.default_rng(7).normal(0, NOISE, s[..., :3].shape[:2])[..., None] if NOISE else 0)
    d = ((src[..., None, :] - lin[None, None]) ** 2).sum(-1)
    snapped = lin[d.argmin(-1)]
    if SOFT:   # keep the painted grain and hatch; only snap saturated pixels (the off_style rule's target)
        mx, mn = s[..., :3].max(-1), s[..., :3].min(-1)
        hit = ((mx - mn) / np.maximum(mx, 1e-6)) > SOFT
        s[..., :3] = np.where(hit[..., None], snapped, s[..., :3])
    else:
        s[..., :3] = snapped
out = np.zeros((CH, CW, 4), np.float32)
y0, x0 = (CH - nh) // 2, (CW - nw) // 2
out[y0:y0 + nh, x0:x0 + nw] = s
o = bpy.data.images.new("o", CW, CH, alpha=True)
o.pixels = out.ravel().tolist()
o.alpha_mode = 'STRAIGHT'
o.filepath_raw = DST
o.file_format = 'PNG'
o.save()
print("FIT", DST, nw, nh)
