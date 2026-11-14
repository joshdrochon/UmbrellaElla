"""Trim a border of N px off a PNG (numbers only; the image model sometimes draws a thin frame line at the edge,
which stops the chroma key reading the corners). Usage: art_keeper_trim.py IN OUT [--px N]"""
import argparse, os, sys
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", ".."))
import png  # noqa: E402

def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("inp"); ap.add_argument("out"); ap.add_argument("--px", type=int, default=8)
    a = ap.parse_args(argv)
    w, h, rows = png.read_png(a.inp)
    n = a.px
    out = [r[n:w - n] for r in rows[n:h - n]]
    png.write_png(a.out, w - 2 * n, h - 2 * n, out)
    print(f"TRIM {a.out} {w - 2 * n}x{h - 2 * n} (cut {n} px each side)")
    return 0

if __name__ == "__main__":
    sys.exit(main())
