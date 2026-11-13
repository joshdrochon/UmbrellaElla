#!/usr/bin/env python3
"""Cut the effect itself out of the vfx concept sheets (originals never edited). Writes
pipeline/art/reference/crops/<element>/<name>.png (RGBA, keyed) and crops.json (source file, box, key).
Keys: red (chroma>=25 hue 330-60 or pale core, as the discord-crops), paper (differs from the box's own paper),
dark (L* > T on a dark scene), ellipse (round clock face). Stdlib only (tools/png.py, tools/art_judge.lab)."""
import json, math, os, sys
sys.path.insert(0, "tools")
from png import read_png, write_png
from art_judge import lab

D = "pipeline/art/reference/discord/"
S0258, S0800, S1220 = D + "20261110-0258_Ricky_1.png", D + "20261110-0800_Ricky_1.png", D + "20261110-1220_Ricky_1.png"
S_REALM = D + "20261111-0318_Ricky_other-realm.png"
OUT = "pipeline/art/reference/crops/"
# element -> [(name, source, (x0,y0,x1,y1), key, pieces)]
SPEC = {
 "vfx-keeper-warning": [("tell-ring", S0258, (60, 740, 150, 815), "red", "all"),
                        ("firing-tell", S0258, (610, 315, 675, 360), "red", "all")],
 "vfx-keeper-strike": [("travel", S0258, (410, 755, 595, 805), "red", "largest"),
                       ("release", S0258, (217, 731, 374, 827), "red", "all")],
 "vfx-keeper-recovery": [("fade", S0258, (600, 755, 745, 800), "red", "all"),
                         ],
 "vfx-clock-beat": [("shot-row", S0800, (570, 270, 1160, 330), "red", "all"),
                    ("hand-arc", S0800, (1190, 160, 1370, 300), "red", "all")],
 "vfx-clock-open": [("clock-face", S0800, (130, 165, 400, 430), "ellipse", "all"),
                    ("clock-cracked", S1220, (1265, 540, 1485, 790), "ellipse", "all")],
 "vfx-eye-exposed": [("clock-detail", S1220, (1265, 540, 1485, 790), "paper", "all"),
                     ("glass-crack", S1220, (170, 120, 330, 260), "ellipse", "all")],
 "vfx-departure": [("loose-hardware", S1220, (330, 730, 480, 850), "paper", "all"),
                   ("hardware-falls", S1220, (950, 740, 1130, 860), "paper", "all")],
 "vfx-restoration": [("umbrella-glow", S_REALM, (380, 320, 600, 450), "dark", "all"),
                     ("gold-shot", S_REALM, (1290, 225, 1420, 260), "dark", "all")],
}

def keyer(key, rows, w, h):
    px = lambda x, y: rows[y][x]
    m = [[False] * w for _ in range(h)]
    if key == "ellipse":
        cx, cy, rx, ry = (w - 1) / 2, (h - 1) / 2, w / 2, h / 2
        return [[((x - cx) / rx) ** 2 + ((y - cy) / ry) ** 2 <= 1 for x in range(w)] for y in range(h)]
    if key == "paper":
        edge = [lab(px(x, y)) for x in range(w) for y in (0, h - 1)] + [lab(px(x, y)) for y in range(h) for x in (0, w - 1)]
        edge.sort(key=lambda t: t[0]); ref = edge[len(edge) // 2]
    for y in range(h):
        for x in range(w):
            L, a, b = lab(px(x, y))
            if key == "red":
                c = math.hypot(a, b); hu = math.degrees(math.atan2(b, a)) % 360
                m[y][x] = (c >= 25 and (hu >= 330 or hu <= 60)) or (L > 90 and c < 22)
            elif key == "paper":
                m[y][x] = math.dist((L, a, b), ref) > 14
            elif key == "dark":
                m[y][x] = L > 22
    return m

def close(m, w, h, r=2):
    d = [[any(m[j][i] for j in range(max(0, y - r), min(h, y + r + 1)) for i in range(max(0, x - r), min(w, x + r + 1)))
          for x in range(w)] for y in range(h)]
    return [[all(d[j][i] for j in range(max(0, y - r), min(h, y + r + 1)) for i in range(max(0, x - r), min(w, x + r + 1)))
             for x in range(w)] for y in range(h)]

def pieces(m, w, h):
    seen, out = set(), []
    for sy in range(h):
        for sx in range(w):
            if m[sy][sx] and (sx, sy) not in seen:
                st, cells = [(sx, sy)], []; seen.add((sx, sy))
                while st:
                    x, y = st.pop(); cells.append((x, y))
                    for nx, ny in ((x+1,y),(x-1,y),(x,y+1),(x,y-1)):
                        if 0 <= nx < w and 0 <= ny < h and m[ny][nx] and (nx, ny) not in seen:
                            seen.add((nx, ny)); st.append((nx, ny))
                out.append(cells)
    return out

def main():
    for el, items in SPEC.items():
        meta = []
        for name, src, box, key, keep in items:
            W, H, rows = read_png(src)
            x0, y0, x1, y1 = box
            sub = [r[x0:x1] for r in rows[y0:y1]]
            w, h = x1 - x0, y1 - y0
            m = close(keyer(key, sub, w, h), w, h)
            ps = sorted(pieces(m, w, h), key=len, reverse=True)
            ps = ps[:1] if keep == "largest" else [p for p in ps if len(p) >= 12]
            alpha = set(c for p in ps for c in p)
            out = [[(sub[y][x][0], sub[y][x][1], sub[y][x][2], 255 if (x, y) in alpha else 0) for x in range(w)] for y in range(h)]
            os.makedirs(OUT + el, exist_ok=True)
            write_png(f"{OUT}{el}/{name}.png", w, h, out)
            meta.append({"file": f"{name}.png", "source": src, "box": [x0, y0, x1, y1], "key": key, "pieces": keep,
                         "opaque_px": len(alpha)})
            print(el, name, len(alpha), "of", w * h)
        json.dump({"element": el, "note": "crops of the effect cut from the concept sheets; originals untouched",
                   "crops": meta}, open(f"{OUT}{el}/crops.json", "w"), indent=1)

if __name__ == "__main__":
    main()
