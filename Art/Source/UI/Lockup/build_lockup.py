"""The title lockup texture: the painted "Umbrella Ella / The Stolen Hour" lettering keyed out of its black ground.
Source: pipeline/art/proof/artui/ui-title-lockup/r2/ (painted by us with tools/assetgen.py, prompt.md beside it); env
LOCKUP_SRC picks another candidate file. r2 is composed so the clock arc and hand sit clear of the subtitle and menu,
so they are kept (r1 had to cut them out). The painted content is cropped to its bounding box and fitted, centred, into
the fixed 1584x672 canvas the UI style draws (UmbrellaUI::LockupImagePixelWidth/Height).
Alpha = how bright a pixel is (the paint is light on pure black), colour = the pixel divided by that alpha, so the
lettering sits on the ground with no black box. Half-size by a 2x2 box average. Numpy inside Blender's Python
(D-new-art-blender); no random state, so the bytes are the same every run.

  /Applications/Blender.app/Contents/MacOS/Blender -b --python Art/Source/UI/Lockup/build_lockup.py
Writes Art/Source/UI/Ground/Raw/T_UI_TitleLockup_PH.png (RGBA).
"""
import os
import struct
import zlib

import bpy
import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, "..", "..", "..", ".."))
SRC = os.environ.get("LOCKUP_SRC") or os.path.join(ROOT, "pipeline", "art", "proof", "artui", "ui-title-lockup", "r2", "draft_a.png")
if not os.path.isabs(SRC):
    SRC = os.path.join(ROOT, SRC)
CANVAS_W, CANVAS_H = 1584, 672   # UmbrellaUI::LockupImagePixelWidth/Height
BBOX_FLOOR = 0.12       # brightness that counts as painted content for the crop
EDGE = 8                # px band on the source edge that is never content
BBOX_MIN_PX = 4         # a row/column needs this many content pixels to count
MARGIN = 12            # px of empty canvas kept around the fitted content
OUT = os.path.join(ROOT, "Art", "Source", "UI", "Ground", "Raw", "T_UI_TitleLockup_PH.png")
ALPHA_FLOOR = 0.035     # below this brightness a pixel is background (jpeg-ish noise in the black)
ALPHA_FULL = 0.30       # at or above this brightness the pixel is fully opaque


def write_png(path, rgba):
    h, w, _ = rgba.shape
    raw = b"".join(b"\x00" + rgba[y].tobytes() for y in range(h))

    def chunk(tag, data):
        c = struct.pack(">I", len(data)) + tag + data
        return c + struct.pack(">I", zlib.crc32(tag + data) & 0xFFFFFFFF)
    png = b"\x89PNG\r\n\x1a\n" + chunk(b"IHDR", struct.pack(">IIBBBBB", w, h, 8, 6, 0, 0, 0)) + chunk(b"IDAT", zlib.compress(raw, 9)) + chunk(b"IEND", b"")
    with open(path, "wb") as fh:
        fh.write(png)


img = bpy.data.images.load(SRC)
w, h = img.size
px = np.array(img.pixels[:], dtype=np.float32).reshape(h, w, 4)[::-1, :, :3]   # Blender rows run bottom to top
# The model leaves a few grey pixels on the image edge: blank an EDGE band, then crop to the painted content, then box-shrink or nearest-grow it to fit the canvas, centred.
px[:EDGE] = 0.0
px[-EDGE:] = 0.0
px[:, :EDGE] = 0.0
px[:, -EDGE:] = 0.0
mask = px.max(axis=2) > BBOX_FLOOR
rows = np.nonzero(mask.sum(axis=1) >= BBOX_MIN_PX)[0]    # a stray dark-grey corner speck in the paint is not content
cols = np.nonzero(mask.sum(axis=0) >= BBOX_MIN_PX)[0]
px = px[rows.min(): rows.max() + 1, cols.min(): cols.max() + 1]
ch, cw = px.shape[:2]
scale = min((CANVAS_W - 2 * MARGIN) / cw, (CANVAS_H - 2 * MARGIN) / ch)
nw, nh = max(1, int(cw * scale)), max(1, int(ch * scale))
# area-average resample: each output pixel averages the source pixels whose centres fall in its span
yi = np.minimum((np.arange(ch) * nh) // ch, nh - 1)
xi = np.minimum((np.arange(cw) * nw) // cw, nw - 1)
acc = np.zeros((nh, nw, 3), np.float64)
cnt = np.zeros((nh, nw, 1), np.float64)
np.add.at(acc, (yi[:, None], xi[None, :]), px)
np.add.at(cnt, (yi[:, None], xi[None, :]), 1.0)
if scale > 1.0:   # growing: fill every output pixel from its nearest source pixel
    sy = np.minimum((np.arange(nh) * ch) // nh, ch - 1)
    sx = np.minimum((np.arange(nw) * cw) // nw, cw - 1)
    small = px[sy][:, sx]
else:
    small = (acc / np.maximum(cnt, 1.0)).astype(np.float32)
px = np.zeros((CANVAS_H, CANVAS_W, 3), np.float32)
oy, ox = (CANVAS_H - nh) // 2, (CANVAS_W - nw) // 2
px[oy: oy + nh, ox: ox + nw] = small
bright = px.max(axis=2)
alpha = np.clip((bright - ALPHA_FLOOR) / (ALPHA_FULL - ALPHA_FLOOR), 0.0, 1.0)
rgb = np.where(alpha[..., None] > 0, px / np.maximum(bright, 1e-4)[..., None], 0.0)
rgb = np.clip(rgb * np.clip(bright / 1.0, 0, 1)[..., None] / np.maximum(alpha, 1e-4)[..., None], 0.0, 1.0)
rgb = np.where(alpha[..., None] > 0, rgb, 0.0)
out = np.dstack([rgb, alpha])
write_png(OUT, (out * 255.0 + 0.5).astype(np.uint8))
print("build_lockup: wrote", OUT, out.shape)
