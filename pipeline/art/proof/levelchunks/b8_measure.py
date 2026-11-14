"""B8 capture check (levelchunks): Ella stands at the left face of the 07A low solid in the walker's stall shot.
Usage: python3 pipeline/art/proof/levelchunks/b8_measure.py <shot.png> <ella_px_x> <ella_px_y>  (Ella's pixel from the journey's
`shot` line, ella=drawn(x,y)). Prints the solid's left edge, the gap to Ella and the solid's rows at that edge."""
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "..", "..", "tools"))
from png import read_png  # noqa: E402

GAP_MAX_PX = 12  # Ella's capsule radius (17 units) is about 5 px at 640 px wide; allow her drawn centre a little slack.


def cream(p):
    r, g, b = p[:3]
    # the stand-in solid colour, measured (211, 205, 186)
    return abs(r - 211) <= 8 and abs(g - 205) <= 8 and abs(b - 186) <= 8


def main():
    path, ex, ey = sys.argv[1], int(sys.argv[2]), int(sys.argv[3])
    w, h, rows = read_png(path)
    band = range(max(0, ey - 8), min(h, ey + 9))
    edges = [next((x for x in range(ex, min(w, ex + 60)) if cream(rows[y][x])), None) for y in band]
    edges = [e for e in edges if e is not None]
    left = min(edges) if edges else None
    run = None
    if left is not None:
        col, start = left + 5, None
        for y in range(h + 1):
            inside = y < h and cream(rows[y][col])
            if inside and start is None:
                start = y
            if not inside and start is not None:
                if start <= ey + 20 and y - 1 >= ey - 20:
                    run = (start, y - 1)
                start = None
    gap = None if left is None else left - ex
    print(f"b8_measure image={os.path.basename(path)} {w}x{h} ella=({ex},{ey}) solid_left_edge_x={left} gap_px={gap} "
          f"solid_rows={run} band_rows_hit={len(edges)}/{len(band)}")
    ok = gap is not None and 0 <= gap <= GAP_MAX_PX and run is not None
    print("B8_CAPTURE_" + ("OK" if ok else "FAIL") + ": Ella drawn at the left face of the 07A low solid")
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
