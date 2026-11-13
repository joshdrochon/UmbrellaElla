"""Our post step on the painted ground: paper grain, ink stipple and a light unsharp so the frame reads hand-made, not smooth.
Run in Blender's Python (numpy): blender -b --python grain_ground.py -- in.png out.png. Fixed seed, same bytes every run."""
import sys
import numpy as np
import bpy

src, dst = sys.argv[sys.argv.index("--") + 1:][:2]
img = bpy.data.images.load(src)
w, h = img.size
a = np.array(img.pixels[:], dtype=np.float32).reshape(h, w, 4)
rng = np.random.default_rng(7)

def blur(x, k):
    for ax in (0, 1):
        c = np.cumsum(np.pad(x, [(k, k) if i == ax else (0, 0) for i in range(x.ndim)], mode="edge"), axis=ax)
        x = (np.take(c, range(2 * k, c.shape[ax]), axis=ax) - np.take(c, range(0, c.shape[ax] - 2 * k), axis=ax)) / (2 * k)
    return x

rgb = a[..., :3]
lum = rgb.mean(axis=2, keepdims=True)
fine = rng.normal(0, 1, (h, w, 1)).astype(np.float32)
mid = blur(rng.normal(0, 1, (h, w, 1)).astype(np.float32), 2) * 2.2
fibre = blur(rng.normal(0, 1, (h, 1, 1)).astype(np.float32).repeat(w, 1), 6) * 0.0
grain = (0.7 * fine + 0.9 * mid) * 0.030 * (0.35 + lum)          # paper tooth, stronger in the lit areas
speck = (rng.random((h, w, 1)) > 0.9965).astype(np.float32) * rng.uniform(0.15, 0.35, (h, w, 1)).astype(np.float32)  # ink stipple
soft = blur(rgb, 2)
sharp = rgb + 0.9 * (rgb - soft)                                   # unsharp: crisper inked edges
out = np.clip(sharp + grain - speck * (0.6 + lum), 0, 1)
a[..., :3] = out
a[..., 3] = 1
img.pixels[:] = a.ravel()
img.filepath_raw = dst
img.file_format = "PNG"
img.save()
