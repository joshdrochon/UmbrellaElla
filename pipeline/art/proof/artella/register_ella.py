#!/usr/bin/env python3
"""Register Ella strip frames (anchor + scale) and rebuild the previews. Needs pillow, numpy, scipy, ffmpeg.
  python3 register_ella.py [state ...]
Anchor = bottom-centre of the lowest solid band of the alpha mask (feet). Every frame is scaled so its mask
height equals the strip median, translated so the anchor sits at one pixel, then re-cut. Registered frames go
to registered/<state>/; previews are rewritten in preview/<state>/ (8 FPS, paper | dark)."""
import json, os, subprocess, sys
import numpy as np
from PIL import Image
from scipy import ndimage

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, "..", "..", "..", ".."))
PAPER = os.path.join(ROOT, "pipeline", "art", "reference", "Test_Assets", "SKY_StarPaper_Tile.png")
FPS, PANEL_W, PANEL_H, SPRITE_H, DARK = 8, 480, 600, 540, "0x1c1c22"
STATES = {"open": ("up-open/R1/frames_up-open", "Ella_up-open", 4),
          "attack": ("attack/R2/frames_attack", "Ella_attack", 3),
          "shield": ("shield/R2/frames_shield", "Ella_shield", 3),
          "closed": ("closed/R2/frames_closed", "Ella_closed", 3)}
THRESH, BAND = 128, 0.04


def measure(img):
    """Mask of the main figure (drops specks under 2% of the largest part), height, feet anchor (x, y)."""
    a = np.asarray(img)[..., 3] > THRESH
    lab, n = ndimage.label(a, structure=np.ones((3, 3)))
    sizes = ndimage.sum(a, lab, range(1, n + 1))
    keep = [i + 1 for i, s in enumerate(sizes) if s >= 0.02 * sizes.max()]
    m = np.isin(lab, keep)
    ys, xs = np.where(m)
    top, bot = ys.min(), ys.max()
    h = bot - top + 1
    band = ys >= bot - max(2, int(BAND * h))
    return dict(h=float(h), ax=float(xs[band].mean()), ay=float(bot), top=int(top))


def stats(ms, label):
    off = [float(np.hypot(b["ax"] - a["ax"], b["ay"] - a["ay"])) for a, b in zip(ms, ms[1:])]
    dr = [abs(b["h"] - a["h"]) / a["h"] * 100 for a, b in zip(ms, ms[1:])]
    return dict(set=label, max_anchor_offset_px=round(max(off), 1), max_scale_drift_pct=round(max(dr), 1),
                offsets=[round(o, 1) for o in off], drifts=[round(d, 1) for d in dr])


def register(state):
    folder, prefix, count = STATES[state]
    src = os.path.join(HERE, folder)
    imgs = [Image.open(os.path.join(src, "%s_%02d.png" % (prefix, i))).convert("RGBA") for i in range(count)]
    before = [measure(i) for i in imgs]
    target = float(np.median([m["h"] for m in before]))
    scaled, ext = [], []
    for im, m in zip(imgs, before):
        s = target / m["h"]
        im2 = im.resize((round(im.width * s), round(im.height * s)), Image.LANCZOS)
        m2 = measure(im2)  # re-measure after scaling so the anchor is exact
        ax, ay = m2["ax"], m2["ay"]
        scaled.append((im2, ax, ay))
        ext.append((ax, im2.width - ax, ay, im2.height - ay))
    L, R, U, D = (int(np.ceil(max(e[k] for e in ext))) for k in range(4))
    W, H = L + R, U + D
    out = os.path.join(HERE, "registered", state)
    os.makedirs(out, exist_ok=True)
    after = []
    for i, (im2, ax, ay) in enumerate(scaled):
        c = Image.new("RGBA", (W, H), (0, 0, 0, 0))
        c.alpha_composite(im2, (L - round(ax), U - round(ay)))
        c.save(os.path.join(out, "%s_%02d.png" % (prefix, i)))
        after.append(measure(c))
    return stats(before, "before"), stats(after, "after"), out, (W, H), target


def run(args):
    subprocess.run(["ffmpeg", "-hide_banner", "-loglevel", "error", "-y"] + args, check=True)


def previews(state, frames_dir):
    _, prefix, count = STATES[state]
    pattern = os.path.join(frames_dir, prefix + "_%02d.png")
    out = os.path.join(HERE, "preview", state)
    os.makedirs(out, exist_ok=True)
    spr = "[0:v]format=rgba,scale=-2:%d,split=2[a][b]" % SPRITE_H
    bg1 = "[1:v]scale=%d:%d:force_original_aspect_ratio=increase,crop=%d:%d[p]" % (PANEL_W, PANEL_H, PANEL_W, PANEL_H)
    bg2 = "color=c=%s:s=%dx%d:r=%d[d]" % (DARK, PANEL_W, PANEL_H, FPS)
    fc = ";".join([spr, bg1, bg2, "[p][a]overlay=(W-w)/2:(H-h)/2:shortest=1[l]",
                   "[d][b]overlay=(W-w)/2:(H-h)/2:shortest=1[r]", "[l][r]hstack,fps=%d" % FPS])
    base = ["-framerate", str(FPS), "-start_number", "0", "-i", pattern, "-loop", "1", "-i", PAPER]
    mp4_in = ["-stream_loop", "5", "-framerate", str(FPS), "-start_number", "0", "-i", pattern, "-loop", "1", "-i", PAPER]
    run(mp4_in + ["-filter_complex", fc + ",format=yuv420p[o]", "-map", "[o]", "-frames:v", str(count * 6),
                  "-r", str(FPS), "-movflags", "+faststart", os.path.join(out, state + "_preview.mp4")])
    run(base + ["-filter_complex", fc + ",split[s0][s1];[s0]palettegen=reserve_transparent=0[pal];[s1][pal]paletteuse[o]",
                "-map", "[o]", "-frames:v", str(count), "-loop", "0", os.path.join(out, state + "_preview.gif")])
    # strip: paper and dark side by side, aligned frames
    sh = 400
    W = Image.open(os.path.join(frames_dir, "%s_00.png" % prefix))
    sw = round(W.width * sh / W.height)
    pap = Image.open(PAPER).convert("RGB")
    s = max(sw / pap.width, sh / pap.height)
    pap = pap.resize((max(sw, round(pap.width * s)), max(sh, round(pap.height * s))))
    row = Image.new("RGB", (sw * count * 2, sh))
    for i in range(count):
        fr = Image.open(os.path.join(frames_dir, "%s_%02d.png" % (prefix, i))).convert("RGBA").resize((sw, sh), Image.LANCZOS)
        for k, bg in enumerate((pap.crop((0, 0, sw, sh)).convert("RGBA"), Image.new("RGBA", (sw, sh), (0x1c, 0x1c, 0x22, 255)))):
            t = bg.copy(); t.alpha_composite(fr)
            row.paste(t.convert("RGB"), ((k * count + i) * sw, 0))
    row.save(os.path.join(out, state + "_strip.png"))


if __name__ == "__main__":
    res = {}
    for st in (sys.argv[1:] or STATES):
        b, a, d, size, tgt = register(st)
        previews(st, d)
        res[st] = dict(before=b, after=a, canvas=size, target_height=tgt)
        print(st, json.dumps(res[st]))
    json.dump(res, open(os.path.join(HERE, "registration_report.json"), "w"), indent=1)
