"""Snap every opaque pixel of an effect sheet to the nearest colour of the effect palette (art_check.effect_style),
keeping alpha. Our post-process for painted sheets: the model's bronze/amber shading drifts off the art bible.
usage: python3 snap_palette.py in.png out.png"""
import json, os, sys
ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "..", ".."))
sys.path.insert(0, os.path.join(ROOT, "tools"))
import art_check
from png import read_png, write_png


def main():
    src, dst = sys.argv[1], sys.argv[2]
    style = json.load(open(os.path.join(ROOT, "pipeline/art/style.json")))
    pal = [art_check.hex_to_rgb(c["hex"]) for c in art_check.effect_style(style)["palette"]]
    w, h, rows = read_png(src)
    cache, out = {}, []
    for row in rows:
        o = []
        for px in row:
            if len(px) < 4 or px[3] < 128:
                o.append(tuple(px)); continue
            k = tuple(px[:3])
            if k not in cache:
                cache[k] = min(pal, key=lambda c: (c[0]-k[0])**2 + (c[1]-k[1])**2 + (c[2]-k[2])**2)
            o.append(tuple(cache[k]) + (px[3],))
        out.append(o)
    write_png(dst, w, h, out)


main()
