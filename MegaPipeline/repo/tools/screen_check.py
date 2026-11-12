#!/usr/bin/env python3
"""Deterministic "no debug or placeholder visuals" check for a screenshot of the DEFAULT build (stdlib only).

art_check.py scores the frame as a whole (palette, paper texture). This check looks for the local things a whole-frame
score can average away, and for the 16:9 lock:
  flat     a large region of one flat colour that is close to a filled rectangle (area >= flat_area_min of the frame,
           bounding-box fill >= rect_fill_min): an untextured primitive, a flat-fill gameplay zone (a solid teal wind
           box), a plain placeholder card. The art bible's etched style is never a flat fill (pipeline/art/art-bible.md)
  grey     a smaller flat near-neutral grey box (area >= grey_area_min): a hitbox or collision debug draw, an engine
           default primitive, a grey stand-in under an actor
  outline  a one-colour rectangle outline (a DrawDebugBox-style frame) whose box is >= outline_area_min of the frame
  aspect   the gameplay view inside the letterbox/pillarbox bars (near-black uniform strips in matching pairs at the
           frame edges) is 16:9 within --aspect-tol; with no bars the whole frame must be 16:9. A 2560x1080 screenshot
           with no bars is gameplay that was not locked to 16:9 (pipeline/unreal-rules.md, Display)
Bars are never flagged as flat. A region a human approved as part of the look (a HUD panel) is passed with
--ignore x,y,w,h (frame pixels); each ignore is printed so a reviewer sees it.

It runs by itself in every smoke (tools/ue_run.py smoke-log runs it on the hook's SMOKE_SHOT screenshot), so in the
daily and in kickoff; the PR pastes its line. Thresholds: pipeline/art/style.json `screen_check` (defaults below).

--strict (menu and tutorial captures) also fails small flat dots and boxes: placeholder stand-ins for control glyphs.
Usage: python3 tools/screen_check.py SHOT.png [--strict] [--aspect 16:9] [--aspect-tol 0.01] [--ignore x,y,w,h] [--json]
Prints `screen_check: PASS|FAIL image=<p> size=WxH view=WxH aspect=<a> bars=<none|letterbox|pillarbox> flat=<n>
grey=<n> outline=<n>`, one line per problem, and a FIX: line for the agent.
Exit 0 = pass, 1 = fail, 2 = usage or unreadable image.
"""
import argparse
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from png import read_png  # noqa: E402

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DEFAULT_STYLE = os.path.join(ROOT, "pipeline", "art", "style.json")
DEFAULTS = {
    "flat_tol": 2,             # max channel difference from the region's seed colour that still counts as flat
    "flat_area_min": 0.01,     # share of the frame
    "grey_area_min": 0.0025,
    "grey_chroma_max": 8,      # max(r,g,b) - min(r,g,b)
    "grey_value_min": 24,
    "grey_value_max": 232,
    "rect_fill_min": 0.9,      # region pixels / bounding-box pixels
    "outline_area_min": 0.01,  # bounding box share of the frame
    "outline_fill_max": 0.35,
    "outline_edge_share": 0.9,  # share of the region's pixels within 2 px of its bounding box
    "bar_value_max": 12,       # brightest channel of a letterbox/pillarbox bar pixel
    "aspect": "16:9",
    "aspect_tol": 0.01,
}
# --strict (menu and tutorial captures): small flat shapes count too, so placeholder dots and boxes standing in for
# control glyphs fail; a round dot fills about 0.785 of its box
STRICT = {"flat_area_min": 0.0008, "grey_area_min": 0.0003, "rect_fill_min": 0.7}
FIX = {
    "flat": "replace the flat fill with etched art from the art bible (Gameplay zones: etched lines, engraved "
            "border, paper tint): regenerate it with tools/assetgen.py image, import it, re-run the smoke",
    "grey": "a debug draw or a placeholder is on screen in the default build: put the draw behind ue.Debug (off by "
            "default) or hide the collision component in game (bHiddenInGame), or replace the stand-in with its art",
    "outline": "a debug box is drawn in the default build: put DrawDebug* behind ue.Debug (off by default)",
    "aspect": "lock the gameplay view to 16:9: the view target camera sets Constrain Aspect Ratio on with Aspect "
              "Ratio 1.777778, and no widget draws in the bars (pipeline/unreal-rules.md, Display)",
}


def thresholds(style_path=DEFAULT_STYLE):
    t = dict(DEFAULTS)
    try:
        with open(style_path, encoding="utf-8") as fh:
            t.update({k: v for k, v in (json.load(fh).get("screen_check") or {}).items() if k in DEFAULTS})
    except (OSError, ValueError):
        pass
    return t


def ratio(text):
    a, _, b = str(text).partition(":")
    return float(a) / float(b) if b else float(a)


def find_bars(w, h, px, limit):
    """(left, right, top, bottom) bar thickness in px. A bar is a run of edge columns (rows) whose every pixel is
    near-black; only matching pairs count (a dark rock band along the bottom alone is scene, not a letterbox)."""
    def dark(p):
        return max(p[0], p[1], p[2]) <= limit

    def col_dark(x, y0, y1):
        return all(dark(px[y * w + x]) for y in range(y0, y1))

    def row_dark(y, x0, x1):
        return all(dark(px[y * w + x]) for x in range(x0, x1))
    left = 0
    while left < w // 2 and col_dark(left, 0, h):
        left += 1
    right = 0
    while right < w // 2 and col_dark(w - 1 - right, 0, h):
        right += 1
    lr = min(left, right)
    top = 0
    while top < h // 2 and row_dark(top, lr, w - lr):
        top += 1
    bottom = 0
    while bottom < h // 2 and row_dark(h - 1 - bottom, lr, w - lr):
        bottom += 1
    tb = min(top, bottom)
    return lr, lr, tb, tb


def regions(w, h, px, skip, tol):
    """Connected 4-neighbour regions of one flat colour (each pixel within tol of the region's seed). Yields
    (count, x0, y0, x1, y1, seed colour, edge count) for regions of 2+ pixels; edge = pixels within 2 px of the bbox."""
    seen = bytearray(skip)
    for start in range(w * h):
        if seen[start]:
            continue
        seen[start] = 1
        sr, sg, sb = px[start][:3]
        stack = [start]
        members = []
        x0, y0, x1, y1 = w, h, -1, -1
        while stack:
            i = stack.pop()
            members.append(i)
            y, x = divmod(i, w)
            if x < x0:
                x0 = x
            if x > x1:
                x1 = x
            if y < y0:
                y0 = y
            if y > y1:
                y1 = y
            for j in (i - 1 if x > 0 else -1, i + 1 if x < w - 1 else -1, i - w, i + w):
                if 0 <= j < w * h and not seen[j]:
                    r, g, b = px[j][:3]
                    if abs(r - sr) <= tol and abs(g - sg) <= tol and abs(b - sb) <= tol:
                        seen[j] = 1
                        stack.append(j)
        if len(members) < 2:
            continue
        edge = 0
        for i in members:
            y, x = divmod(i, w)
            if x - x0 <= 2 or x1 - x <= 2 or y - y0 <= 2 or y1 - y <= 2:
                edge += 1
        yield len(members), x0, y0, x1, y1, (sr, sg, sb), edge


def check(path, t=None, ignore=()):
    """Return a result dict: pass, problems (list of dicts), view, aspect, bars, counts."""
    t = dict(DEFAULTS, **(t or {}))
    w, h, rows = read_png(path)
    px = [p for row in rows for p in row]
    lb, rb, tb, bb = find_bars(w, h, px, t["bar_value_max"])
    vw, vh = w - lb - rb, h - tb - bb
    bars = "pillarbox" if lb else "letterbox" if tb else "none"
    skip = bytearray(w * h)
    for y in range(h):
        for x in range(w):
            if x < lb or x >= w - rb or y < tb or y >= h - bb or px[y * w + x][3] < 128:
                skip[y * w + x] = 1
    for gx, gy, gw, gh in ignore:
        for y in range(max(0, gy), min(h, gy + gh)):
            for x in range(max(0, gx), min(w, gx + gw)):
                skip[y * w + x] = 1
    frame = float(max(1, vw * vh))
    problems = []
    for n, x0, y0, x1, y1, col, edge in regions(w, h, px, skip, t["flat_tol"]):
        bw, bh = x1 - x0 + 1, y1 - y0 + 1
        share, fill = n / frame, n / float(bw * bh)
        where = {"x": x0, "y": y0, "w": bw, "h": bh, "colour": "#%02x%02x%02x" % col, "area": round(share, 4),
                 "fill": round(fill, 3)}
        grey = max(col) - min(col) <= t["grey_chroma_max"] and t["grey_value_min"] <= max(col) <= t["grey_value_max"]
        if fill >= t["rect_fill_min"] and share >= t["flat_area_min"]:
            problems.append(dict(where, kind="grey" if grey else "flat"))
        elif fill >= t["rect_fill_min"] and grey and share >= t["grey_area_min"]:
            problems.append(dict(where, kind="grey"))
        elif (bw * bh / frame >= t["outline_area_min"] and fill <= t["outline_fill_max"] and bw >= 8 and bh >= 8
              and edge / float(n) >= t["outline_edge_share"]):
            problems.append(dict(where, kind="outline"))
    want = ratio(t["aspect"])
    aspect = vw / float(vh) if vh else 0.0
    if vh == 0 or abs(aspect - want) > float(t["aspect_tol"]):
        problems.append({"kind": "aspect", "view": f"{vw}x{vh}", "aspect": round(aspect, 3), "want": round(want, 3),
                         "bars": bars})
    counts = {k: sum(1 for p in problems if p["kind"] == k) for k in ("flat", "grey", "outline")}
    return {"pass": not problems, "image": path, "size": f"{w}x{h}", "view": f"{vw}x{vh}", "aspect": round(aspect, 3),
            "box": [lb, tb, vw, vh],
            "bars": bars, "problems": problems, **counts}


def crop_view(path, res, out):
    """Write the gameplay view (the frame inside the bars) to out; art_check scores that, not the bars."""
    from png import write_png
    x, y, vw, vh = res["box"]
    _, _, rows = read_png(path)
    write_png(out, vw, vh, [r[x:x + vw] for r in rows[y:y + vh]])
    return out


def summary(res):
    return (f"screen_check: {'PASS' if res['pass'] else 'FAIL'} image={res['image']} size={res['size']} "
            f"view={res['view']} aspect={res['aspect']:.3f} bars={res['bars']} flat={res['flat']} grey={res['grey']} "
            f"outline={res['outline']}")


def report(res):
    """Printed lines: the summary, one line per problem, one FIX: line per problem kind."""
    out = [summary(res)]
    for p in res["problems"]:
        if p["kind"] == "aspect":
            out.append(f"  - aspect: gameplay view {p['view']} is {p['aspect']} ({p['bars']} bars), want "
                       f"{p['want']} (16:9)")
        else:
            out.append(f"  - {p['kind']}: x={p['x']} y={p['y']} w={p['w']} h={p['h']} colour={p['colour']} "
                       f"area={p['area'] * 100:.2f}% fill={p['fill']}")
    for k in dict.fromkeys(p["kind"] for p in res["problems"]):
        out.append(f"FIX: {k}: {FIX[k]}")
    return out


def parse_box(text):
    try:
        x, y, w, h = (int(v) for v in text.split(","))
    except ValueError:
        raise argparse.ArgumentTypeError(f"--ignore wants x,y,w,h in pixels, got {text!r}")
    return x, y, w, h


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("image")
    ap.add_argument("--style", default=DEFAULT_STYLE)
    ap.add_argument("--aspect")
    ap.add_argument("--aspect-tol", type=float)
    ap.add_argument("--ignore", type=parse_box, action="append", default=[])
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--strict", action="store_true", help="menu and tutorial captures: small flat dots and boxes fail")
    a = ap.parse_args(argv)
    t = thresholds(a.style)
    if a.strict:
        t.update(STRICT)
    if a.aspect:
        t["aspect"] = a.aspect
    if a.aspect_tol is not None:
        t["aspect_tol"] = a.aspect_tol
    try:
        res = check(a.image, t, a.ignore)
    except (OSError, ValueError, ZeroDivisionError) as e:
        print(f"screen_check: {e}", file=sys.stderr)
        return 2
    if a.json:
        print(json.dumps(res, indent=2))
    else:
        for box in a.ignore:
            print("screen_check: ignoring x=%d y=%d w=%d h=%d (--ignore)" % box)
        print("\n".join(report(res)))
    return 0 if res["pass"] else 1


if __name__ == "__main__":
    sys.exit(main())
