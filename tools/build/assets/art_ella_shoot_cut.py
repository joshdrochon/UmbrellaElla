#!/usr/bin/env python3
# Usage: python3 tools/build/assets/art_ella_shoot_cut.py <repo root> <out dir>   (ellashoot lane, 14 Nov)
"""Cut Ella's hip-fire (still + baked recoil/bob) and aimed-shot (Veo clip) into 6x4 grids at the idle's scale/anchor."""
import glob, importlib.util, json, math, os, subprocess, sys
REPO = sys.argv[1]; OUT = sys.argv[2]
sys.path.insert(0, os.path.join(REPO, "tools")); import png
spec = importlib.util.spec_from_file_location("assetgen", os.path.join(REPO, "tools", "assetgen.py"))
ag = importlib.util.module_from_spec(spec); spec.loader.exec_module(ag)
SHOOT = os.path.join(REPO, "pipeline/art/proof/artella/shoot")
IDLE_BODY = 395.0          # idle figure hat tip to boot sole in a 654-px idle cell (ella-up-open-input 527 px x 540/720)
ANCHOR_Y, IDLE_W, IDLE_ANCHOR_X = 530, 481, 256.5   # idle cell 481x654, boot sole centre (Ella_idle_N24_00.png)
CELL_H = 654
STILL_TOP, STILL_SOLE, STILL_CX = 18, 751, 467.5    # keyed R1 still, 1344x768
S = IDLE_BODY / (STILL_SOLE - STILL_TOP)
def run(c): subprocess.run(c, check=True, capture_output=True)
def blank(w, h): return [[(0, 0, 0, 0)] * w for _ in range(h)]

def grid(cells, cols=6):
    w, h = len(cells[0][0]), len(cells[0]); rows = []
    for r in range(len(cells) // cols):
        for y in range(h):
            row = []
            for c in range(cols): row.extend(cells[r * cols + c][y])
            rows.append(row)
    return w * cols, h * (len(cells) // cols), rows
os.makedirs(OUT, exist_ok=True)
# ---- hip-fire: keyed still scaled to the idle body height, sole on the idle anchor; recoil twice + 2 px bob, 24 cells
tmp = os.path.join(OUT, "_still_scaled.png")
run(["ffmpeg", "-hide_banner", "-loglevel", "error", "-y", "-i", os.path.join(SHOOT, "R1/shoot_draft_key.png"),
     "-vf", "scale=%d:-1:flags=lanczos,format=rgba" % round(1344 * S), tmp])
sw, sh, srows = png.read_png(tmp)
ox, oy = round(IDLE_ANCHOR_X - STILL_CX * S), round(ANCHOR_Y - STILL_SOLE * S)
# Recoil (twice per loop): the upper body and the umbrella kick back up to 6 px and settle; the shift ramps to 0
# between the hands (cell y 330) and the knees (y 440), so the boots stay on the anchor (sprite_check pivot rule).
RECOIL = [0, -4, -6, -5, -3, -2, -1, 0, 0, 0, 0, 0]
HANDS_Y, KNEES_Y = 330, 440
def lerp_px(r, fx):
    x0 = int(math.floor(fx)); t = fx - x0
    a = r[x0] if 0 <= x0 < len(r) else (0, 0, 0, 0); b = r[x0 + 1] if 0 <= x0 + 1 < len(r) else (0, 0, 0, 0)
    return tuple(int(round(a[k] * (1 - t) + b[k] * t)) for k in range(4))
cells = []
for i in range(24):
    rec = RECOIL[i % 12]
    cell = blank(IDLE_W, CELL_H)
    for ty in range(CELL_H):
        y = ty - oy
        if not 0 <= y < sh:
            continue
        w = 1.0 if ty <= HANDS_Y else (0.0 if ty >= KNEES_Y else (KNEES_Y - ty) / (KNEES_Y - HANDS_Y))
        d = rec * w
        r = srows[y]
        for tx in range(IDLE_W):
            px = lerp_px(r, tx - ox - d) if d else (r[tx - ox] if 0 <= tx - ox < sw else (0, 0, 0, 0))
            if px[3]:
                cell[ty][tx] = px
    cells.append(cell)
gw, gh, grows = grid(cells)
png.write_png(os.path.join(OUT, "ella-shoot_N24_grid.png"), gw, gh, grows)
os.remove(tmp)
# ---- aimed shot: the R1 Veo clip 0..1.65 s (still pose -> arm out -> flash at the tip), 24 frames, same scale, static camera
# The aim pose swings her legs back as the arm comes up (the clip, not registration error): the boots travel; the
# camera is static and the cells are not re-registered, so the body does not slide (sprite_check pivot override).
AIM_DRIFT_MAX = 100
AIM_DRIFT_REASON = "aim pose: the legs swing back as the arm comes up (Veo clip, static camera, unregistered on purpose)"
AIM_W = 900; aim_ax = AIM_W / 2 + (IDLE_ANCHOR_X - IDLE_W / 2)
f = 1280 / 1344; sv = S / f
VEO_SOLE_X = 436.0   # frame 0 boot-sole centre measured in the clip (x of 1280; the still mapped gives 445)
vx, vy = round(aim_ax - VEO_SOLE_X * sv), round(ANCHOR_Y - STILL_SOLE * f * sv)
raw = os.path.join(OUT, "_aim_raw"); os.makedirs(raw, exist_ok=True)
for old in glob.glob(os.path.join(raw, "*.png")): os.remove(old)

run(["ffmpeg", "-hide_banner", "-loglevel", "error", "-y", "-t", "1.65", "-i", os.path.join(SHOOT, "R1/ella-shoot.mp4"),
     "-vf", "fps=24/1.65,scale=%d:-2:flags=lanczos,pad=%d:%d:%d:%d:color=0x00FF00,crop=%d:%d:0:0" % (round(1280 * sv), AIM_W + 2000, CELL_H, vx, vy, AIM_W, CELL_H),
     "-frames:v", "24", os.path.join(raw, "a_%03d.png")])
cells = []
for i, p in enumerate(sorted(glob.glob(os.path.join(raw, "a_*.png")))[:24]):
    k = os.path.join(raw, "k_%03d.png" % i); ag.chroma_key(p, k)
    cells.append(png.read_png(k)[2])
assert len(cells) == 24, len(cells)
gw, gh, grows = grid(cells)
png.write_png(os.path.join(OUT, "ella-aimshot_N24_grid.png"), gw, gh, grows)
for n, (w, c) in {"ella-shoot": (IDLE_W, 6.13), "ella-aimshot": (AIM_W, None)}.items():
    json.dump({"kind": "silhouette", "frames": 24, "grid": [w, CELL_H], "fps": c, "loop": n == "ella-shoot", "pivot": "bottom-centre",
               "anchor": [IDLE_ANCHOR_X if n == "ella-shoot" else aim_ax, ANCHOR_Y], "scale_from_source": S if n == "ella-shoot" else sv,
               **({} if n == "ella-shoot" else {"pivot_drift_max_px": AIM_DRIFT_MAX, "pivot_drift_reason": AIM_DRIFT_REASON})},
              open(os.path.join(OUT, n + "_N24_grid.sprite.json"), "w"), indent=1)
print("S=%.4f sv=%.4f still_off=%d,%d video_off=%d,%d aim_anchor_x=%.1f" % (S, sv, ox, oy, vx, vy, aim_ax))
import shutil; shutil.rmtree(raw)
