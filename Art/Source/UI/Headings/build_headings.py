"""Painted screen headings ("Paused", "Settings"), keyed out of their black ground, one texture each.
Source: pipeline/art/proof/artui/ui-headings/headings_a.png (painted by us with tools/assetgen.py, prompt.md beside it).
Same keying as the title lockup (alpha = brightness on pure black). The sheet is split at the middle row, each half is
cropped to its lettering plus a margin, then half-sized by a 2x2 box average. Numpy inside Blender's Python
(D-new-art-blender); no random state.

  /Applications/Blender.app/Contents/MacOS/Blender -b --python Art/Source/UI/Headings/build_headings.py
Writes Art/Source/UI/Ground/Raw/T_UI_HeadPaused_PH.png and T_UI_HeadSettings_PH.png (RGBA); prints their sizes.
"""
import os
import struct
import zlib

import bpy
import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, "..", "..", "..", ".."))
SRC = os.path.join(ROOT, "pipeline", "art", "proof", "artui", "ui-headings", "headings_a.png")
OUTDIR = os.path.join(ROOT, "Art", "Source", "UI", "Ground", "Raw")
ALPHA_FLOOR = 0.035
ALPHA_FULL = 0.30
MARGIN = 8
BG_HEADROOM = 0.02     # the alpha floor sits this far above the painted black's own level (its median), so the
                       # model's not-quite-black ground keys out fully instead of leaving a faint dark patch


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
px = np.array(img.pixels[:], dtype=np.float32).reshape(h, w, 4)[::-1, :, :3]
for name, half in (("T_UI_HeadPaused_PH", px[: h // 2]), ("T_UI_HeadSettings_PH", px[h // 2:])):
    bright = half.max(axis=2)
    ys, xs = np.where(bright > 0.25)
    y0, y1 = max(ys.min() - MARGIN, 0), min(ys.max() + MARGIN, half.shape[0])
    x0, x1 = max(xs.min() - MARGIN, 0), min(xs.max() + MARGIN, half.shape[1])
    crop = half[y0:y1, x0:x1]
    crop = crop[: crop.shape[0] // 2 * 2, : crop.shape[1] // 2 * 2]
    crop = crop.reshape(crop.shape[0] // 2, 2, crop.shape[1] // 2, 2, 3).mean(axis=(1, 3))
    b = crop.max(axis=2)
    floor = max(ALPHA_FLOOR, float(np.median(b[b < ALPHA_FULL])) + BG_HEADROOM)
    alpha = np.clip((b - floor) / (ALPHA_FULL - floor), 0.0, 1.0)
    rgb = np.where(alpha[..., None] > 0, crop / np.maximum(b, 1e-4)[..., None], 0.0)
    rgb = np.clip(rgb * np.clip(b, 0, 1)[..., None] / np.maximum(alpha, 1e-4)[..., None], 0.0, 1.0)
    rgb = np.where(alpha[..., None] > 0, rgb, 0.0)
    out = np.dstack([rgb, alpha])
    write_png(os.path.join(OUTDIR, name + ".png"), (out * 255.0 + 0.5).astype(np.uint8))
    print("build_headings: wrote", name, out.shape[1], "x", out.shape[0], "alpha floor %.4f" % floor)
