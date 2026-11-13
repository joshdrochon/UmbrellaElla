"""The UI grain: a seamless 512x512 tile of paper fibre and ink stipple, drawn 1:1 over every menu ground so the
painted ground (shown at about half its painted size) keeps an etched, printed finish. Numpy inside Blender's
Python (D-new-art-blender); fixed seed, no outside image read.

  /Applications/Blender.app/Contents/MacOS/Blender -b --python Art/Source/UI/Grain/build_grain.py
Writes Art/Source/UI/Ground/Raw/T_UI_Grain_PH.png (RGBA: dark ink specks and pale paper flecks, alpha carries strength).
"""
import os
import struct
import zlib

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, "..", "..", "..", ".."))
OUT = os.path.join(ROOT, "Art", "Source", "UI", "Ground", "Raw", "T_UI_Grain_PH.png")
N = 512
SEED = 1113
INK = np.array([0.07, 0.06, 0.05])
PAPER = np.array([0.93, 0.85, 0.68])


def write_png(path, rgba):
    h, w, _ = rgba.shape
    raw = b"".join(b"\x00" + rgba[y].tobytes() for y in range(h))

    def chunk(tag, data):
        c = struct.pack(">I", len(data)) + tag + data
        return c + struct.pack(">I", zlib.crc32(tag + data) & 0xFFFFFFFF)
    png = b"\x89PNG\r\n\x1a\n" + chunk(b"IHDR", struct.pack(">IIBBBBB", w, h, 8, 6, 0, 0, 0)) + chunk(b"IDAT", zlib.compress(raw, 9)) + chunk(b"IEND", b"")
    with open(path, "wb") as fh:
        fh.write(png)


def blur(a, k):
    """Wrap-around box blur (keeps the tile seamless)."""
    for axis in (0, 1):
        acc = np.zeros_like(a)
        for s in range(-k, k + 1):
            acc += np.roll(a, s, axis=axis)
        a = acc / (2 * k + 1)
    return a


rng = np.random.default_rng(SEED)
fine = rng.random((N, N))
fibre = blur(rng.random((N, N)), 1) * 0.6 + blur(np.roll(rng.random((N, N)), 3, axis=1), 2) * 0.4
fibre = (fibre - fibre.mean()) / fibre.std()
dark = np.clip((0.975 - fine) / 0.025, 0.0, 1.0) * 0.40            # ink stipple, ~2.5 % of pixels
light = np.clip((fine - 0.985) / 0.015, 0.0, 1.0) * 0.25          # paper flecks, ~1.5 %
dark = np.maximum(dark, np.clip(fibre - 1.8, 0.0, 1.0) * 0.16)   # fibre streaks darken a little more
alpha = np.maximum(dark, light)
col = np.where((dark >= light)[..., None], INK, PAPER)
out = np.dstack([col, alpha])
write_png(OUT, (out * 255.0 + 0.5).astype(np.uint8))
print("build_grain: wrote", out.shape)
