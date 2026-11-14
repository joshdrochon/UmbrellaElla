"""Keeper wing-gust clip helpers (numbers only; run with a python that has numpy, e.g. Blender's python -I).

  input  --grid APPROVED_GRID.png --out INPUT.png
         Cell 0 of the owner-approved idle grid (6 x 4 cells), scaled (--scale 0.8) and composited on flat #00FF00,
         centred in 1280x720 (--drop px lower), so Veo starts from the approved design with room for the wing beat.
  strip  --keyed DIR --indices i,j,... --out STRIP.png [--cell-w 640]
         One fixed crop (union of all picked keyed masks + pad) for every frame, scaled down to --cell-w wide (0 = crop width; never up), packed in
         ONE row (M_ArtSlot samples only the top row), plus <stem>.sprite.json.
  side   --left A.png --right B.png --out OUT.png [--labels "a|b"]
         Two images side by side on a dark ground at one height (approval sheet).
"""
import argparse, json, os, sys
import numpy as np


def read_png(path):
    sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", ".."))
    import png  # tools/png.py (stdlib reader/writer)
    w, h, rows = png.read_png(path)
    a = np.array(rows, dtype=np.uint8).reshape(h, w, -1)
    if a.shape[2] == 3:
        a = np.concatenate([a, np.full((h, w, 1), 255, np.uint8)], axis=2)
    return a


def write_png(path, a):
    import struct, zlib
    a = np.ascontiguousarray(a[..., :4].astype(np.uint8))
    h, w = a.shape[:2]
    raw = np.concatenate([np.zeros((h, 1), np.uint8), a.reshape(h, w * 4)], axis=1).tobytes()

    def chunk(t, d):
        return struct.pack(">I", len(d)) + t + d + struct.pack(">I", zlib.crc32(t + d) & 0xFFFFFFFF)
    with open(path, "wb") as f:
        f.write(b"\x89PNG\r\n\x1a\n" + chunk(b"IHDR", struct.pack(">IIBBBBB", w, h, 8, 6, 0, 0, 0))
                + chunk(b"IDAT", zlib.compress(raw, 9)) + chunk(b"IEND", b""))


def resize(a, w, h):
    """Area-average down (box filter on premultiplied colour); numbers only."""
    src = a.astype(np.float64)
    al = src[..., 3:4] / 255.0
    pre = np.concatenate([src[..., :3] * al, src[..., 3:4]], axis=2)
    sh, sw = pre.shape[:2]
    ys = (np.arange(h + 1) * sh / h).astype(int)
    xs = (np.arange(w + 1) * sw / w).astype(int)
    c = pre.cumsum(0).cumsum(1)
    c = np.pad(c, ((1, 0), (1, 0), (0, 0)))
    tot = c[ys[1:]][:, xs[1:]] - c[ys[:-1]][:, xs[1:]] - c[ys[1:]][:, xs[:-1]] + c[ys[:-1]][:, xs[:-1]]
    n = ((ys[1:] - ys[:-1])[:, None] * (xs[1:] - xs[:-1])[None, :])[..., None]
    m = tot / n
    out_a = m[..., 3:4]
    rgb = np.where(out_a > 0, m[..., :3] / np.maximum(out_a / 255.0, 1e-6), 0)
    return np.clip(np.concatenate([rgb, out_a], axis=2) + 0.5, 0, 255).astype(np.uint8)


def cmd_input(a):
    g = read_png(a.grid)
    cw, ch = g.shape[1] // 6, g.shape[0] // 4
    cell = g[:ch, :cw]
    if a.scale != 1.0:
        cell = resize(cell, int(round(cw * a.scale)), int(round(ch * a.scale)))
    cell = cell.astype(np.float64)
    ch, cw = cell.shape[:2]
    out = np.zeros((720, 1280, 3), np.float64); out[..., 1] = 255.0
    x, y = (1280 - cw) // 2, (720 - ch) // 2 + a.drop
    al = cell[..., 3:4] / 255.0
    out[y:y + ch, x:x + cw] = cell[..., :3] * al + out[y:y + ch, x:x + cw] * (1 - al)
    rgba = np.concatenate([out, np.full((720, 1280, 1), 255.0)], axis=2)
    write_png(a.out, np.clip(rgba + 0.5, 0, 255).astype(np.uint8))
    print(f"INPUT {a.out} cell {cw}x{ch} at ({x},{y}) on #00FF00 1280x720")


def cmd_strip(a):
    idx = [int(v) for v in a.indices.split(",")]
    frames = [read_png(os.path.join(a.keyed, "keyed_%03d.png" % i)) for i in idx]
    m = np.zeros(frames[0].shape[:2], bool)
    for f in frames:
        m |= f[..., 3] > 8
    ys, xs = np.nonzero(m)
    pad = a.pad
    y0, y1 = max(0, ys.min() - pad), min(m.shape[0], ys.max() + pad + 1)
    x0, x1 = max(0, xs.min() - pad), min(m.shape[1], xs.max() + pad + 1)
    if (x1 - x0) % 2:
        x1 = x1 - 1 if x1 == m.shape[1] else x1 + 1
    if (y1 - y0) % 2:
        y1 = y1 - 1 if y1 == m.shape[0] else y1 + 1
    # Never upscale: a cell is at most the crop's own width (the box filter only averages down).
    cw = min(a.cell_w, x1 - x0) if a.cell_w > 0 else x1 - x0
    chh = int(round((y1 - y0) * cw / (x1 - x0)))
    chh += chh % 2
    cells = [f[y0:y1, x0:x1] if cw == x1 - x0 else resize(f[y0:y1, x0:x1], cw, chh) for f in frames]
    strip = np.concatenate(cells, axis=1)
    write_png(a.out, strip)
    side = {"kind": "silhouette", "frames": len(idx), "grid": [int(cw), int(chh)], "fps": a.fps, "loop": False,
            "pivot": "bottom-centre", "registration": "none: one fixed crop for all frames (locked camera)",
            "crop": [int(x0), int(y0), int(x1 - x0), int(y1 - y0)], "source_indices": idx, "rows": 1,
            "source_fps": a.source_fps}
    json.dump(side, open(os.path.splitext(a.out)[0] + ".sprite.json", "w"), indent=1)
    print(f"STRIP {a.out} {len(idx)} cells of {cw}x{chh} crop {side['crop']}")


def cmd_side(a):
    L, R = read_png(a.left), read_png(a.right)
    h = min(L.shape[0], R.shape[0], a.height)
    L = resize(L, int(round(L.shape[1] * h / L.shape[0])), h)
    R = resize(R, int(round(R.shape[1] * h / R.shape[0])), h)
    gap = 16
    out = np.zeros((h, L.shape[1] + R.shape[1] + gap, 4), np.float64)
    out[..., :3] = (0x29, 0x26, 0x22); out[..., 3] = 255
    for img, x in ((L, 0), (R, L.shape[1] + gap)):
        al = img[..., 3:4] / 255.0
        out[:, x:x + img.shape[1], :3] = img[..., :3] * al + out[:, x:x + img.shape[1], :3] * (1 - al)
    write_png(a.out, np.clip(out + 0.5, 0, 255).astype(np.uint8))
    print(f"SIDE {a.out} {out.shape[1]}x{h}")


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)
    p = sub.add_parser("input"); p.add_argument("--grid", required=True); p.add_argument("--out", required=True)
    p.add_argument("--scale", type=float, default=0.8); p.add_argument("--drop", type=int, default=30)
    p = sub.add_parser("strip"); p.add_argument("--keyed", required=True); p.add_argument("--indices", required=True)
    p.add_argument("--out", required=True); p.add_argument("--cell-w", type=int, default=640)
    p.add_argument("--pad", type=int, default=8); p.add_argument("--fps", type=float, default=10.0)
    p.add_argument("--source-fps", type=float, default=12.0)
    p = sub.add_parser("side"); p.add_argument("--left", required=True); p.add_argument("--right", required=True)
    p.add_argument("--out", required=True); p.add_argument("--height", type=int, default=720)
    a = ap.parse_args(argv)
    {"input": cmd_input, "strip": cmd_strip, "side": cmd_side}[a.cmd](a)


if __name__ == "__main__":
    main()
