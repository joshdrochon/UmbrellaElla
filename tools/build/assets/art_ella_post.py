"""Ella paint post-process: recolour the outer outline band of a keyed (transparent) sprite to warm candle-cream.

The model paints the 3 px outline lemon-lime (hue ~100, outside the art_check gold/rust band). Keep each pixel's
lightness, move its hue to spark-white #FFE6C4. Only pixels within BAND px of transparency change.
Usage: python3 tools/build/assets/art_ella_post.py IN.png OUT.png [BAND]
"""
import colorsys
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", ".."))
import png  # noqa: E402

CREAM = (255, 230, 196)


def edge_depth(rows, w, h, band):
    """Chebyshev-ish distance (<= band) from the nearest transparent pixel, 0 for transparent."""
    inf = band + 1
    d = [[inf if rows[y][x][3] > 8 else 0 for x in range(w)] for y in range(h)]
    for _ in range(band):
        nd = [r[:] for r in d]
        for y in range(h):
            for x in range(w):
                if d[y][x] == 0:
                    continue
                m = inf
                for yy, xx in ((y - 1, x), (y + 1, x), (y, x - 1), (y, x + 1)):
                    if 0 <= yy < h and 0 <= xx < w:
                        m = min(m, d[yy][xx] + 1)
                    else:
                        m = min(m, 1)
                nd[y][x] = min(d[y][x], m)
        d = nd
    return d


def recolour(rows, w, h, band=4):
    d = edge_depth(rows, w, h, band)
    ch, cs, cv = colorsys.rgb_to_hsv(*(c / 255 for c in CREAM))
    out = []
    for y in range(h):
        row = []
        for x in range(w):
            r, g, b, a = rows[y][x]
            if a > 8 and d[y][x] <= band:
                hh, ss, vv = colorsys.rgb_to_hsv(r / 255, g / 255, b / 255)
                if ss > 0.12 and vv > 0.6:   # only the bright outline, never the cloth
                    # keep lightness (value), take cream hue, cap saturation at cream's
                    r2, g2, b2 = colorsys.hsv_to_rgb(ch, min(ss, cs * 1.4), vv)
                    r, g, b = round(r2 * 255), round(g2 * 255), round(b2 * 255)
            row.append((r, g, b, a))
        out.append(row)
    return out


def main(argv):
    w, h, rows = png.read_png(argv[1])
    band = int(argv[3]) if len(argv) > 3 else 4
    png.write_png(argv[2], w, h, recolour(rows, w, h, band))
    print(f"POST {argv[2]} band={band}")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
