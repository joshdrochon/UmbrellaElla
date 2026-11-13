"""Key a painted skyline off its green ground (Blender python: numpy + bpy). Args after --: in out W H"""
import sys, bpy, numpy as np
a = sys.argv[sys.argv.index("--") + 1:]
src, dst, W, H = a[0], a[1], int(a[2]), int(a[3])
im = bpy.data.images.load(src)
w, h = im.size
px = np.array(im.pixels[:], dtype=np.float32).reshape(h, w, 4)
r, g, b = px[..., 0], px[..., 1], px[..., 2]
spill = g - np.maximum(r, b)
alpha = np.clip(1.0 - (spill - 0.04) / 0.16, 0.0, 1.0)
px[..., 1] = np.minimum(g, np.maximum(r, b) + 0.02)
px[..., 3] = alpha
px[..., :3] *= 1.0  # straight alpha
out = bpy.data.images.new("o", w, h, alpha=True)
out.pixels.foreach_set(px.ravel()); out.scale(W, H)
out.filepath_raw = dst; out.file_format = "PNG"; out.save()
print("keyed", dst, W, H, "transparent frac", float((alpha < 0.05).mean()))
