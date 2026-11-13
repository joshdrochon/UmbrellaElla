#!/usr/bin/env python3
"""video_to_strip: a chroma-green mp4 -> keyed, registered frames, an N-frame strip, a sidecar, a looping GIF.

  python3 tools/build/video_to_strip.py --video X.mp4 --out DIR --stem Ella_idle --counts 8 12 [--fps 12]
      [--height 540] [--trim-start 0.0] [--paper PAPER.png]

Steps (stdlib + ffmpeg only, same as the rest of tools/):
 1. ffmpeg extracts frames at --fps, scaled to --height.
 2. tools/assetgen.py chroma_key keys and despills each frame.
 3. Registration: anchor = bottom-centre of the lowest solid band (4% of height) of the alpha mask; every frame is
    translated so its anchor sits on one pixel (same rule as pipeline/art/proof/artella/register_ella.py, minus the
    scale step: the report gives the height drift instead, so a drifting clip is visible rather than hidden).
 4. For each N: the loop is frames 0..e, e (in the last 40%) the end closest to frame 0; N frames are picked evenly
    from it, so the step from the last pick back to the first is like any other step.
 5. Writes <stem>_N<n>_NN.png frames, <stem>_N<n>_strip.png, <stem>_N<n>.frames.json (the same shape as
    `assetgen.py frames`, plus fps, anchor and the loop and jitter numbers), and the GIF over paper and dark.
Numbers: frame_distance (mean abs RGBA difference, 0..255) first->last pick vs the mean step."""
import argparse
import glob
import importlib.util
import json
import os
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
TOOLS = os.path.dirname(HERE)
sys.path.insert(0, TOOLS)
import png  # noqa: E402

THRESH, BAND = 128, 0.04


def _assetgen():
    spec = importlib.util.spec_from_file_location("assetgen", os.path.join(TOOLS, "assetgen.py"))
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def run(cmd):
    r = subprocess.run(cmd, capture_output=True, text=True)
    if r.returncode:
        raise ValueError("ffmpeg failed: " + r.stderr[-400:])


def extract(video, out_dir, fps, height, trim_start=0.0, crop=None):
    os.makedirs(out_dir, exist_ok=True)
    for old in glob.glob(os.path.join(out_dir, "raw_*.png")):
        os.remove(old)
    run(["ffmpeg", "-hide_banner", "-loglevel", "error", "-y", "-ss", str(trim_start), "-i", video,
         "-vf", f"fps={fps},scale=-2:{height}:flags=lanczos" + (f",crop={crop}" if crop else ""), os.path.join(out_dir, "raw_%03d.png")])
    return sorted(glob.glob(os.path.join(out_dir, "raw_*.png")))


def alpha_mask(w, h, rows):
    return [bytearray(1 if px[3] > THRESH else 0 for px in row) for row in rows]


def main_part(mask, w, h):
    """Mask with specks under 2% of the largest 8-connected part dropped."""
    lab = [[0] * w for _ in range(h)]
    sizes = [0]
    n = 0
    for y in range(h):
        for x in range(w):
            if mask[y][x] and not lab[y][x]:
                n += 1
                lab[y][x] = n
                st, cnt = [(x, y)], 0
                while st:
                    cx, cy = st.pop()
                    cnt += 1
                    for dy in (-1, 0, 1):
                        for dx in (-1, 0, 1):
                            nx, ny = cx + dx, cy + dy
                            if 0 <= nx < w and 0 <= ny < h and mask[ny][nx] and not lab[ny][nx]:
                                lab[ny][nx] = n
                                st.append((nx, ny))
                sizes.append(cnt)
    if n == 0:
        raise ValueError("the frame has no figure after keying")
    big = max(sizes)
    keep = {i for i, s in enumerate(sizes) if i and s >= 0.02 * big}
    return [bytearray(1 if lab[y][x] in keep else 0 for x in range(w)) for y in range(h)]


def measure(w, h, rows):
    """Figure height, feet anchor (x, y) and bbox, from the main part of the alpha mask."""
    m = main_part(alpha_mask(w, h, rows), w, h)
    ys = [y for y in range(h) if any(m[y])]
    top, bot = ys[0], ys[-1]
    ht = bot - top + 1
    lo = bot - max(2, int(BAND * ht))
    xs = [x for y in range(lo, bot + 1) for x in range(w) if m[y][x]]
    return {"h": ht, "ax": sum(xs) / len(xs), "ay": bot, "top": top}


def shift(rows, w, h, dx, dy, nw, nh):
    out = [[(0, 0, 0, 0)] * nw for _ in range(nh)]
    for y in range(h):
        ty = y + dy
        if 0 <= ty < nh:
            row = rows[y]
            o = out[ty]
            for x in range(w):
                tx = x + dx
                if 0 <= tx < nw and row[x][3]:
                    o[tx] = row[x]
    return out


def anchor_stats(ms):
    off = [((b["ax"] - a["ax"]) ** 2 + (b["ay"] - a["ay"]) ** 2) ** 0.5 for a, b in zip(ms, ms[1:])]
    dr = [abs(b["h"] - a["h"]) / a["h"] * 100 for a, b in zip(ms, ms[1:])]
    return {"max_anchor_step_px": round(max(off), 2) if off else 0.0, "max_height_step_pct": round(max(dr), 2) if dr else 0.0,
            "max_anchor_from_first_px": round(max(((m["ax"] - ms[0]["ax"]) ** 2 + (m["ay"] - ms[0]["ay"]) ** 2) ** 0.5
                                                 for m in ms), 2),
            "height_range_pct": round((max(m["h"] for m in ms) - min(m["h"] for m in ms)) / ms[0]["h"] * 100, 2)}


def register(frames):
    """frames: [(w, h, rows)]. Translate each so its feet anchor is on one pixel; one common canvas. Returns
    (frames, before stats, after stats, anchor)."""
    ms = [measure(*f) for f in frames]
    before = anchor_stats(ms)
    L = max(m["ax"] for m in ms)
    U = max(m["ay"] for m in ms)
    R = max(f[0] - m["ax"] for f, m in zip(frames, ms))
    D = max(f[1] - m["ay"] for f, m in zip(frames, ms))
    ax, ay = round(L), round(U)
    nw, nh = ax + int(R + 0.999) + 1, ay + int(D + 0.999) + 1
    out = []
    for (w, h, rows), m in zip(frames, ms):
        out.append((nw, nh, shift(rows, w, h, ax - round(m["ax"]), ay - round(m["ay"]), nw, nh)))
    after = anchor_stats([measure(*f) for f in out])
    return out, before, after, (ax, ay)


def distance(a, b):
    """Mean absolute RGBA difference (0..255) of two same-size frames; transparent pixels compare as alpha only."""
    tot = n = 0
    for ra, rb in zip(a[2], b[2]):
        for pa, pb in zip(ra, rb):
            if pa[3] == 0 and pb[3] == 0:
                continue
            tot += sum(abs(pa[i] - pb[i]) for i in range(4)) / 4
            n += 1
    return tot / n if n else 0.0


def loop_window(frames):
    """End index e in the last 40% closest to frame 0 (frames 0..e loop back to 0). Returns (e, dist list)."""
    n = len(frames)
    lo = max(2, int(n * 0.6))
    d = [(distance(frames[0], frames[e]), e) for e in range(lo, n)]
    best = min(d)
    return best[1], {e: round(v, 2) for v, e in d}


def pick(count, length):
    """count indices evenly over a loop of `length` frames (0..length-1, then back to 0)."""
    return [min(length - 1, round(i * length / count)) for i in range(count)]


def loop_report(frames, idx):
    steps = [distance(frames[a], frames[b]) for a, b in zip(idx, idx[1:])]
    closing = distance(frames[idx[-1]], frames[idx[0]])
    mean = sum(steps) / len(steps) if steps else 0.0
    return {"indices": idx, "mean_step": round(mean, 2), "max_step": round(max(steps), 2) if steps else 0.0,
            "last_to_first": round(closing, 2),
            "loop_ratio": round(closing / mean, 2) if mean else None,
            "loops": bool(mean) and closing <= 1.5 * max(steps)}


def strip_rows(frames):
    w, h = frames[0][0], frames[0][1]
    rows = []
    for y in range(h):
        row = []
        for f in frames:
            row.extend(f[2][y])
        rows.append(row)
    return w * len(frames), h, rows


def grid_rows(frames, cols):
    """Sheet of frames left to right, then top to bottom (the order sprite_check cuts), cols per row."""
    w, h = frames[0][0], frames[0][1]
    nrows = -(-len(frames) // cols)
    rows = []
    for r in range(nrows):
        for y in range(h):
            row = []
            for c in range(cols):
                i = r * cols + c
                if i < len(frames):
                    row.extend(frames[i][2][y])
                else:
                    row.extend([(0, 0, 0, 0)] * w)
            rows.append(row)
    return w * cols, h * nrows, rows


def write_set(out_dir, stem, frames, idx, fps, anchor, extra, cols=0):
    picked = [frames[i] for i in idx]
    names = []
    for i, f in enumerate(picked):
        p = os.path.join(out_dir, f"{stem}_{i:02d}.png")
        png.write_png(p, f[0], f[1], f[2])
        names.append(p)
    sw, sh, srows = strip_rows(picked)
    strip = os.path.join(out_dir, f"{stem}_strip.png")
    png.write_png(strip, sw, sh, srows)
    side = {"frames": len(picked), "frame": [picked[0][0], picked[0][1]], "pivot": "bottom-centre", "anchor": list(anchor),
            "fps": fps, "cut": "video frames, chroma-keyed, feet-anchor registered", "outputs": names, "strip": strip}
    side.update(extra)
    with open(os.path.join(out_dir, f"{stem}.frames.json"), "w", encoding="utf-8") as fh:
        json.dump(side, fh, indent=1)
        fh.write("\n")
    with open(os.path.splitext(strip)[0] + ".sprite.json", "w", encoding="utf-8") as fh:   # what tools/art_loop.py reads
        json.dump({"frames": len(picked), "grid": [picked[0][0], picked[0][1]], "fps": side["fps"], "loop": True,
                   "pivot": "bottom-centre"}, fh, indent=1)
        fh.write("\n")
    if cols:
        gw, gh, grows = grid_rows(picked, cols)
        grid = os.path.join(out_dir, f"{stem}_grid.png")
        png.write_png(grid, gw, gh, grows)
        with open(os.path.splitext(grid)[0] + ".sprite.json", "w", encoding="utf-8") as fh:
            json.dump({"kind": "silhouette", "frames": len(picked), "grid": [picked[0][0], picked[0][1]], "fps": side["fps"],
                       "loop": True, "pivot": "bottom-centre"}, fh, indent=1)
            fh.write("\n")
        side["grid_sheet"] = grid
    return names, strip, side


def gif(frames_dir, stem, count, fps, out, paper=None):
    """Looping GIF: paper | dark side by side (dark only when no paper)."""
    pat = os.path.join(frames_dir, stem + "_%02d.png")
    dark = "color=c=0x1c1c22:s=480x600:r=%d[d]" % fps
    spr = "[0:v]format=rgba,scale=-2:540,split=2[a][b]"
    if paper and os.path.isfile(paper):
        fc = ";".join([spr, "[1:v]scale=480:600:force_original_aspect_ratio=increase,crop=480:600[p]", dark,
                       "[p][a]overlay=(W-w)/2:(H-h)/2:shortest=1[l]", "[d][b]overlay=(W-w)/2:(H-h)/2:shortest=1[r]",
                       "[l][r]hstack,fps=%d" % fps])
        inp = ["-framerate", str(fps), "-i", pat, "-loop", "1", "-i", paper]
    else:
        fc = ";".join(["[0:v]format=rgba,scale=-2:540[a]", dark, "[d][a]overlay=(W-w)/2:(H-h)/2:shortest=1[l]", "[l]fps=%d" % fps])
        inp = ["-framerate", str(fps), "-i", pat]
    fc += ",split[s0][s1];[s0]palettegen=reserve_transparent=0[pal];[s1][pal]paletteuse[o]"
    run(["ffmpeg", "-hide_banner", "-loglevel", "error", "-y"] + inp +
        ["-filter_complex", fc, "-map", "[o]", "-frames:v", str(count), "-loop", "0", out])


def convert(video, out_dir, stem, counts, fps, height, trim_start=0.0, paper=None, crop=None, keyed=None, cols=0):
    ag = _assetgen()
    os.makedirs(out_dir, exist_ok=True)
    key_stats = []
    if keyed:
        names_k = sorted(f for f in os.listdir(keyed) if f.startswith("keyed_") and f.endswith(".png"))
        if len(names_k) < 4:
            raise ValueError(f"only {len(names_k)} keyed frames in {keyed}")
        frames = [png.read_png(os.path.join(keyed, f)) for f in names_k]
        key_stats = [{"green_inside_px": 0}]
    else:
        raws = extract(video, os.path.join(out_dir, "raw"), fps, height, trim_start, crop)
        if len(raws) < 4:
            raise ValueError(f"only {len(raws)} frames at {fps} fps; need at least 4")
        keyed_dir = os.path.join(out_dir, "keyed")
        os.makedirs(keyed_dir, exist_ok=True)
        frames = []
        for i, r in enumerate(raws):
            k = os.path.join(keyed_dir, "keyed_%03d.png" % i)
            key_stats.append(ag.chroma_key(r, k))
            frames.append(png.read_png(k))
    reg, before, after, anchor = register(frames)
    e, ends = loop_window(reg)
    result = {"video": video, "fps": fps, "source_frames": len(reg), "loop_end": e, "end_candidates": ends,
              "jitter_before": before, "jitter_after": after,
              "green_inside_px_max": max(s["green_inside_px"] for s in key_stats), "sets": {}}
    for n in counts:
        idx = pick(n, e + 1)
        lp = loop_report(reg, idx)
        out_stem = f"{stem}_N{n}"
        names, strip, side = write_set(out_dir, out_stem, reg, idx, round(n / ((e + 1) / fps), 2), anchor,
                                       {"loop": lp, "jitter_before": before, "jitter_after": after, "source": video}, cols)
        g = os.path.join(out_dir, f"{out_stem}_preview.gif")
        gif(out_dir, out_stem, n, side["fps"], g, paper)
        result["sets"][str(n)] = {"strip": strip, "gif": g, "loop": lp, "fps": side["fps"]}
    with open(os.path.join(out_dir, f"{stem}.report.json"), "w", encoding="utf-8") as fh:
        json.dump(result, fh, indent=1)
        fh.write("\n")
    return result


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--video", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--stem", default="Ella_idle")
    ap.add_argument("--counts", type=int, nargs="+", default=[8, 12])
    ap.add_argument("--fps", type=int, default=12)
    ap.add_argument("--height", type=int, default=540)
    ap.add_argument("--trim-start", type=float, default=0.0)
    ap.add_argument("--paper")
    ap.add_argument("--keyed", help="reuse already keyed frames (keyed_NNN.png) from this dir; skips ffmpeg and keying")
    ap.add_argument("--crop", help="ffmpeg crop w:h:x:y after scaling (pure-Python keying is slow: crop to the figure)")
    ap.add_argument("--grid-cols", type=int, default=0,
                    help="also write <stem>_N<n>_grid.png (+ .sprite.json), this many cells per row; use when a strip passes 8192 px")
    a = ap.parse_args(argv)
    try:
        r = convert(a.video, a.out, a.stem, a.counts, a.fps, a.height, a.trim_start, a.paper, a.crop, a.keyed, a.grid_cols)
    except (ValueError, subprocess.CalledProcessError) as e:
        print(f"FAIL: video_to_strip: {e}")
        return 1
    print(f"STRIPS {a.stem} source_frames={r['source_frames']} loop_end={r['loop_end']} "
          f"jitter {r['jitter_before']['max_anchor_step_px']} -> {r['jitter_after']['max_anchor_step_px']} px")
    for n, s in r["sets"].items():
        print(f"  N={n} fps={s['fps']} loop last->first {s['loop']['last_to_first']} vs mean step {s['loop']['mean_step']} "
              f"loops={s['loop']['loops']} -> {s['strip']}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
