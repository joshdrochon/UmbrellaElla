"""Frame registration and jitter for sprite strips (stdlib only; frames are (w, h, rows) with rows of (r, g, b, a)).

anchor(): the point a frame is pinned on, from its alpha mask: bottom-centre of the lowest `band` rows that hold a
visible pixel (the feet, or an umbrella handle), the same point sprite_check's pivot check uses.
span(): the size that stands for the figure's scale (mask height by default; "width" or a fixed band is configurable).
register(): scale every frame about its anchor to the strip's median span, then translate so every anchor sits on one
pixel. jitter(): anchor offset (px) and span drift (%) between consecutive frames. Limits are the constant JITTER_LIMITS,
measured on a reference sheet (see that file), never by eye.

    python3 tools/frame_register.py measure sheet.png --grid 432x352 [--frames 5] [--row 0]
"""
import argparse
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from png import read_png  # noqa: E402

CLEAR = 8        # alpha at or below this is background (style.json sprite.alpha_clear_max)
BAND = 8         # rows of the lowest part that make the anchor (style.json sprite.pivot_feet_rows)
BASE_FRAC = 0.14  # "base" span: width of the lowest 14% of the mask height (hem / feet / tail), min 4 rows.
# 0.14 and up: every reference loop drifts 0.0%; at 0.12 and below the Owl tail reads 0.8%+ (measured Nov 12)
RESCALE_RANGE = (0.8, 1.25)   # a span change beyond this is a pose change (a flap, a crouch), not wobble: left alone


# Jitter limits, measured once with `measure` on the team's reference sheets (pipeline/art/reference/Test_Assets, the
# hand-made Witch and Owl animations; span "base", 8-row anchor band, the sheet's cell size from SpriteLayout.json):
#   CHR_Witch_Cast rows 0 and 1 (6 frames), CHR_Owl_Flap_Damage row 0 (6 frames, loop): offset 0.0 px, scale 0.0%.
#   CHR_Witch_Guard_Transition (5 frames, deliberate hem change): offset 2.5 px, scale 8.2% (a pose change, not wobble).
# offset_px: the transition's 2.5 px is the largest legitimate motion of an anchor between frames, rounded up.
# scale_pct: the loops' 0.0% plus 2 px of quantisation on the smallest base span they have (about 120 px): 1.7%, rounded up.
JITTER_LIMITS = {"offset_px": 3.0, "scale_pct": 2.0}


def mask_box(rows, clear=CLEAR):
    """(x0, y0, x1, y1) of the visible pixels, or None for an empty frame."""
    ys = [y for y, row in enumerate(rows) if any(px[3] > clear for px in row)]
    if not ys:
        return None
    x0 = min(next(x for x, px in enumerate(rows[y]) if px[3] > clear) for y in ys)
    x1 = max(len(rows[y]) - 1 - next(x for x, px in enumerate(reversed(rows[y])) if px[3] > clear) for y in ys)
    return x0, ys[0], x1, ys[-1]


def anchor(rows, clear=CLEAR, band=BAND):
    """(x, y) bottom-centre of the lowest `band` visible rows: x = (min + max + 1) / 2, y = bottom + 1. None if empty."""
    box = mask_box(rows, clear)
    if not box:
        return None
    bottom = box[3]
    xs = [x for y in range(max(box[1], bottom - band + 1), bottom + 1)
          for x, px in enumerate(rows[y]) if px[3] > clear]
    return ((min(xs) + max(xs) + 1) / 2, bottom + 1)


def span(rows, mode="base", clear=CLEAR):
    """The figure's scale along one axis. "base" (default): width of the lowest 14% of the mask, which a raised arm,
    a wand or a wing beat does not change. "height" / "width": the whole mask (pose changes move these). A number n:
    width of the lowest n rows."""
    box = mask_box(rows, clear)
    if not box:
        return 0
    if mode == "base":   # alone, a frame's own height; measure() gives every frame of a strip the same row count
        mode = str(max(4, round(BASE_FRAC * (box[3] - box[1] + 1))))
    if mode == "height":
        return box[3] - box[1] + 1
    if mode == "width":
        return box[2] - box[0] + 1
    xs = [x for y in range(max(box[1], box[3] - int(mode) + 1), box[3] + 1)
          for x, px in enumerate(rows[y]) if px[3] > clear]
    return max(xs) - min(xs) + 1 if xs else 0


def median(vals):
    s = sorted(vals)
    n = len(s)
    return s[n // 2] if n % 2 else (s[n // 2 - 1] + s[n // 2]) / 2


def _transform(w, h, rows, ax, ay, tx, ty, s, clear):
    """Frame scaled by s about (ax, ay) and moved so that point lands on (tx, ty); same canvas size."""
    out = [[(0, 0, 0, 0)] * w for _ in range(h)]
    exact = abs(s - 1.0) < 1e-9
    for y in range(h):
        sy = ay + (y + 0.5 - ty) / s - 0.5
        for x in range(w):
            sx = ax + (x + 0.5 - tx) / s - 0.5
            if exact:
                ix, iy = int(round(sx)), int(round(sy))
                if 0 <= ix < w and 0 <= iy < h and rows[iy][ix][3]:
                    out[y][x] = rows[iy][ix]
                continue
            x0, y0 = int(sx // 1), int(sy // 1)
            fx, fy = sx - x0, sy - y0
            acc = [0.0, 0.0, 0.0, 0.0]
            for dy, wy in ((0, 1 - fy), (1, fy)):
                for dx, wx in ((0, 1 - fx), (1, fx)):
                    px_, py_ = x0 + dx, y0 + dy
                    if 0 <= px_ < w and 0 <= py_ < h and wx * wy:
                        r, g, b, a = rows[py_][px_]
                        k = wx * wy * a        # premultiplied, so a soft edge does not pick up the matte's colour
                        acc[0] += r * k
                        acc[1] += g * k
                        acc[2] += b * k
                        acc[3] += k
            if acc[3] > 0.5:
                a = acc[3]
                out[y][x] = (int(round(acc[0] / a)), int(round(acc[1] / a)), int(round(acc[2] / a)),
                             min(255, int(round(a))))
    return out


def measure(frames, clear=CLEAR, band=BAND, span_mode="base"):
    """Per frame: anchor (x, y) and span. Empty frames give None. "base" uses one row count for the whole strip
    (14% of the median mask height), so a pose that is taller or shorter does not change what is measured."""
    if span_mode == "base":
        hs = [b[3] - b[1] + 1 for b in (mask_box(r, clear) for _, _, r in frames) if b]
        span_mode = str(max(4, round(BASE_FRAC * median(hs)))) if hs else "4"
    return [(anchor(r, clear, band), span(r, span_mode, clear)) for _, _, r in frames]


def register(frames, clear=CLEAR, band=BAND, span_mode="base", target=None):
    """(registered frames, info). Every frame is scaled about its anchor to the strip's median span (only within
    RESCALE_RANGE) and moved so its anchor sits on one pixel: `target` (x, y), else the median anchor, rounded.
    info is what the sidecar records: anchor (target), span, and per frame the anchor/span before and the scale applied."""
    meas = measure(frames, clear, band, span_mode)
    live = [m for m in meas if m[0] is not None]
    if not live:
        raise ValueError("register: every frame is empty")
    med_span = median([m[1] for m in live])
    tx, ty = target if target else (int(round(median([m[0][0] for m in live]))),
                                    int(round(median([m[0][1] for m in live]))))
    out, per = [], []
    for (w, h, rows), (anc, sp) in zip(frames, meas):
        if anc is None:
            out.append((w, h, rows))
            per.append({"anchor": None, "span": 0, "scale": 1.0})
            continue
        s = med_span / sp if sp else 1.0
        s = s if RESCALE_RANGE[0] <= s <= RESCALE_RANGE[1] else 1.0
        ax = int(round(anc[0]))   # integer pivot: a pure translation stays a copy, not a blur
        out.append((w, h, _transform(w, h, rows, ax, anc[1], tx, ty, s, clear)))
        per.append({"anchor": list(anc), "span": sp, "scale": round(s, 4)})
    info = {"anchor": [tx, ty], "span": med_span, "span_mode": span_mode, "band": band, "frames": per}
    return out, info


def jitter(frames, clear=CLEAR, band=BAND, span_mode="base", loop=False):
    """Between consecutive frames (and last to first when `loop`): the largest anchor offset in px (max of |dx|, |dy|)
    and the largest span change in %. Returns {"offset_px", "scale_pct", "worst": [frame index of each]}."""
    meas = [m for m in measure(frames, clear, band, span_mode) if m[0] is not None]
    pairs = list(zip(meas, meas[1:])) + ([(meas[-1], meas[0])] if loop and len(meas) > 2 else [])
    off = [max(abs(a[0][0] - b[0][0]), abs(a[0][1] - b[0][1])) for a, b in pairs]
    sc = [100.0 * abs(b[1] - a[1]) / a[1] if a[1] else 0.0 for a, b in pairs]
    return {"offset_px": max(off, default=0.0), "scale_pct": max(sc, default=0.0),
            "worst": [off.index(max(off)) if off else 0, sc.index(max(sc)) if sc else 0]}


def sheet_frames(path, grid, count=None, row=None):
    """Frames cut from a sheet PNG by its cell size, row-major (or just `row`); trailing empty cells dropped."""
    w, h, rows = read_png(path)
    gw, gh = grid
    cols, nrows = w // gw, h // gh
    out = []
    for r in ([row] if row is not None else range(nrows)):
        for c in range(cols):
            out.append((gw, gh, [rw[c * gw:(c + 1) * gw] for rw in rows[r * gh:(r + 1) * gh]]))
    while len(out) > 1 and mask_box(out[-1][2]) is None:
        out.pop()
    return out[:count] if count else out


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("cmd", choices=["measure"])
    ap.add_argument("sheet")
    ap.add_argument("--grid", required=True, help="cell size WxH")
    ap.add_argument("--frames", type=int)
    ap.add_argument("--row", type=int)
    ap.add_argument("--loop", action="store_true")
    a = ap.parse_args(argv)
    grid = tuple(int(v) for v in a.grid.lower().split("x"))
    fr = sheet_frames(a.sheet, grid, a.frames, a.row)
    print(json.dumps(dict(jitter(fr, loop=a.loop), frames=len(fr))))
    return 0


if __name__ == "__main__":
    sys.exit(main())
