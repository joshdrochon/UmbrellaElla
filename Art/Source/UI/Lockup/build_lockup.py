"""The title lockup texture: the painted "Umbrella Ella / The Stolen Hour" lettering keyed out of its black ground.
Source: pipeline/art/proof/artui/ui-title-lockup/lockup_a.png (painted by us with tools/assetgen.py, prompt.md beside it).
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
SRC = os.path.join(ROOT, "pipeline", "art", "proof", "artui", "ui-title-lockup", "lockup_a.png")
OUT = os.path.join(ROOT, "Art", "Source", "UI", "Ground", "Raw", "T_UI_TitleLockup_PH.png")
ALPHA_FLOOR = 0.035     # below this brightness a pixel is background (jpeg-ish noise in the black)
DIM_MAX = 0.55         # ring/numeral paint is dimmer than the cream lettering
HAND_SAT = 0.33        # the gold hands are more saturated than cream
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
px = px[: h // 2 * 2, : w // 2 * 2]
px = px.reshape(h // 2, 2, w // 2, 2, 3).mean(axis=(1, 3))
bright = px.max(axis=2)
# The painted clock ring and hands behind the lettering collide with the subtitle and the menu rule, and the ground
# already carries its own clock. Keep the lettering only: drop dim pixels (the ring, numerals) everywhere and the
# saturated gold hands inside the box they cross. Boxes are fractions of the image.
sat = (bright - px.min(axis=2)) / np.maximum(bright, 1e-4)
hh, ww = bright.shape
yy, xx = np.mgrid[0:hh, 0:ww]
hand_box = (xx > 0.52 * ww) & (yy > 0.50 * hh)
drop = (bright < DIM_MAX) | (hand_box & (sat > HAND_SAT))
bright = np.where(drop, 0.0, bright)
px = np.where(drop[..., None], 0.0, px)
alpha = np.clip((bright - ALPHA_FLOOR) / (ALPHA_FULL - ALPHA_FLOOR), 0.0, 1.0)
rgb = np.where(alpha[..., None] > 0, px / np.maximum(bright, 1e-4)[..., None], 0.0)
rgb = np.clip(rgb * np.clip(bright / 1.0, 0, 1)[..., None] / np.maximum(alpha, 1e-4)[..., None], 0.0, 1.0)
rgb = np.where(alpha[..., None] > 0, rgb, 0.0)
out = np.dstack([rgb, alpha])
write_png(OUT, (out * 255.0 + 0.5).astype(np.uint8))
print("build_lockup: wrote", OUT, out.shape)
