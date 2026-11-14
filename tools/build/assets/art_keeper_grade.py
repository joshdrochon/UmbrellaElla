"""Colour grade for keyed Keeper art (numbers only; alpha kept).

  --sat S          scale saturation of opaque pixels (HLS)
  --clamp-hue      move colourful pixels (CIELAB chroma above style.json hue_gate chroma_min) whose hue angle is outside
                   style.json allowed_hue_bands_deg onto the nearest band edge (pulled 3 deg inside; a pale highlight that clips back out loses chroma until it holds), keeping L* and C*.
                   The image model paints the bronze slightly olive and the video despill leaves pink wing tips;
                   art_check off_band counts both.
  --chroma-floor C clamp from this C* (default chroma_min); 4 also catches the faint pink fringe the despill leaves
Usage: art_keeper_grade.py IN OUT [--sat 0.7] [--clamp-hue [--chroma-floor 4]]"""
import argparse, colorsys, json, math, os, sys
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", ".."))
import png  # noqa: E402
from art_check import rgb_to_lab  # noqa: E402

ROOT = os.path.abspath(os.path.join(HERE, "..", "..", ".."))
INSIDE_DEG = 3.0


def _gamma(c):
    c = max(0.0, c)
    return 1.055 * c ** (1 / 2.4) - 0.055 if c > 0.0031308 else 12.92 * c


def lab_to_rgb(lab):
    """Inverse of art_check.rgb_to_lab (D65, sRGB), clipped to 0..255."""
    L, a, b = lab
    fy = (L + 16) / 116
    fx, fz = fy + a / 500, fy - b / 200

    def finv(t):
        return t ** 3 if t ** 3 > 0.008856 else (t - 16 / 116) / 7.787

    x, y, z = finv(fx) * 0.95047, finv(fy), finv(fz) * 1.08883
    r = 3.2406 * x - 1.5372 * y - 0.4986 * z
    g = -0.9689 * x + 1.8758 * y + 0.0415 * z
    bb = 0.0557 * x - 0.2040 * y + 1.0570 * z
    return tuple(max(0, min(255, round(_gamma(v) * 255))) for v in (r, g, bb))


def clamp_hue(rgb, chroma_min, bands):
    L, a, b = rgb_to_lab(rgb)
    c = math.hypot(a, b)
    if c <= chroma_min:
        return rgb
    h = math.degrees(math.atan2(b, a)) % 360
    if any(lo <= h <= hi for lo, hi in bands):
        return rgb
    edges = [(lo + INSIDE_DEG) for lo, _ in bands] + [(hi - INSIDE_DEG) for _, hi in bands]
    target = min(edges, key=lambda e: min(abs(h - e), 360 - abs(h - e)))
    t = math.radians(target)
    # Pale highlights (L* ~95) leave the sRGB gamut when turned: clipping swings the hue back out, so lower chroma until it holds.
    for _ in range(12):
        out = lab_to_rgb((L, c * math.cos(t), c * math.sin(t)))
        L2, a2, b2 = rgb_to_lab(out)
        h2 = math.degrees(math.atan2(b2, a2)) % 360
        if math.hypot(a2, b2) <= chroma_min or any(lo <= h2 <= hi for lo, hi in bands):
            return out
        c *= 0.8
    return out


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("inp"); ap.add_argument("out")
    ap.add_argument("--sat", type=float, default=1.0)
    ap.add_argument("--clamp-hue", action="store_true")
    ap.add_argument("--chroma-floor", type=float, default=None,
                    help="clamp pixels above this C* instead of hue_gate chroma_min (4: also the faint pink despill fringe)")
    a = ap.parse_args(argv)
    with open(os.path.join(ROOT, "pipeline", "art", "style.json"), encoding="utf-8") as fh:
        gate = json.load(fh)["hue_gate"]
    bands = [tuple(x) for x in gate["allowed_hue_bands_deg"]]
    w, h, rows = png.read_png(a.inp)
    cache, moved = {}, 0
    out = []
    for row in rows:
        o = []
        for r, g, b, al in row:
            if al:
                key = (r, g, b)
                hit = cache.get(key)
                if hit is None:
                    px = key
                    if a.sat != 1.0:
                        hh, ll, ss = colorsys.rgb_to_hls(r / 255, g / 255, b / 255)
                        px = tuple(max(0, min(255, round(v * 255))) for v in colorsys.hls_to_rgb(hh, ll, ss * a.sat))
                    if a.clamp_hue:
                        px = clamp_hue(px, gate["chroma_min"] if a.chroma_floor is None else a.chroma_floor, bands)
                    hit = cache[key] = px
                if hit != (r, g, b):
                    moved += 1
                r, g, b = hit
            o.append((r, g, b, al))
        out.append(o)
    png.write_png(a.out, w, h, out)
    print(f"GRADE {a.out} sat x{a.sat} clamp_hue={a.clamp_hue} changed_px={moved}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
