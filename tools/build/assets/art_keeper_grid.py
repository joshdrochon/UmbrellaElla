"""Keeper idle grid with ONE fixed crop for every frame (numbers only).

video_to_strip.py registers each frame on the lowest band of its mask (feet). On the Keeper the lowest pixels are
the hanging mechanisms in one frame and a down-swept wing tip in the next, so that registration moves the whole body
up to ~55 px between frames. Veo's camera is locked, so the clip's own position is the right one: this tool crops every
picked keyed frame with the same box (the union of all masks plus a pad) and packs the 6-per-row grid + sidecar.

  python3 tools/build/assets/art_keeper_grid.py --keyed DIR --report Keeper_idle.report.json --n 24 --out GRID.png
"""
import argparse, json, os, sys
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", ".."))
import png  # noqa: E402

COLS = 6   # art_slots.GRID_COLS: every packed grid is cut 6 cells per row


def bbox(rows, w, h):
    x0, y0, x1, y1 = w, h, -1, -1
    for y, row in enumerate(rows):
        for x, p in enumerate(row):
            if p[3] > 8:
                if x < x0: x0 = x
                if x > x1: x1 = x
                if y < y0: y0 = y
                y1 = y
    return x0, y0, x1, y1


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--keyed", required=True); ap.add_argument("--report", required=True)
    ap.add_argument("--n", type=int, default=24); ap.add_argument("--out", required=True)
    ap.add_argument("--pad", type=int, default=8)
    a = ap.parse_args(argv)
    rep = json.load(open(a.report, encoding="utf-8"))
    loop = rep["sets"][str(a.n)]["loop"]
    idx = loop["indices"]
    frames = []
    for i in idx:
        w, h, rows = png.read_png(os.path.join(a.keyed, "keyed_%03d.png" % i))
        frames.append((w, h, rows))
    w, h = frames[0][0], frames[0][1]
    boxes = [bbox(r, w, h) for _, _, r in frames]
    x0 = max(0, min(b[0] for b in boxes) - a.pad); y0 = max(0, min(b[1] for b in boxes) - a.pad)
    x1 = min(w - 1, max(b[2] for b in boxes) + a.pad); y1 = min(h - 1, max(b[3] for b in boxes) + a.pad)
    cw, ch = x1 - x0 + 1, y1 - y0 + 1
    cw += cw % 2; ch += ch % 2
    nrows = -(-len(frames) // COLS)
    clear = (0, 0, 0, 0)
    out = [[clear] * (cw * COLS) for _ in range(ch * nrows)]
    for k, (_, _, rows) in enumerate(frames):
        gx, gy = (k % COLS) * cw, (k // COLS) * ch
        for y in range(ch):
            sy = y0 + y
            if sy >= h:
                continue
            src = rows[sy]
            dst = out[gy + y]
            for x in range(cw):
                sx = x0 + x
                if sx < w:
                    dst[gx + x] = tuple(src[sx])
    os.makedirs(os.path.dirname(os.path.abspath(a.out)), exist_ok=True)
    png.write_png(a.out, cw * COLS, ch * nrows, out)
    fps = rep["sets"][str(a.n)].get("fps") or round(rep["fps"] * a.n / (rep["loop_end"] + 1), 2)
    side = {"kind": "silhouette", "frames": len(frames), "grid": [cw, ch], "fps": fps, "loop": True,
            "pivot": "bottom-centre", "registration": "none: one fixed crop for all frames (locked camera)",
            "crop": [x0, y0, cw, ch], "source_indices": idx}
    with open(os.path.splitext(a.out)[0] + ".sprite.json", "w", encoding="utf-8") as fh:
        json.dump(side, fh, indent=1); fh.write("\n")
    print("GRID %s %dx%d cells %dx%d frames %d fps %s crop %s" % (a.out, cw * COLS, ch * nrows, cw, ch, len(frames), fps, side["crop"]))
    return 0


if __name__ == "__main__":
    sys.exit(main())
