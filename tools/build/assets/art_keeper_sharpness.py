"""Where does the Keeper owl lose sharpness? One number per stage (numbers only, no judgement).

Stages, all on grid cell K (default 0) and the video frame it was cut from:
  (a) key:    partial-alpha pixels on the cut edge (feather) and how far the cut eats into the figure (grow)
  (b) grade:  pixels the grade changed and the sharpness ratio grid/raw on the inner figure (edges excluded)
  (c) resample: source px per cell px (crop vs cell size) and max difference of the ffmpeg lanczos step vs a plain decode
  (d) in-game: texels per screen pixel (cell width / matched on-screen width) and sharpness of the in-game crop vs the
      best possible picture at that size (the cell downscaled with lanczos), so scale loss and render loss are separate.
Sharpness = mean |gradient| of luma (Rec.709, 0..255) over the inner mask (alpha 255, 3 px in from the cut).

Run with any python that has numpy (Blender's: /Applications/Blender.app/Contents/Resources/<v>/python/bin/python3.13 -I):
  art_keeper_sharpness.py --video MP4 --grid PNG --sprite JSON [--ingame PNG ...] [--cell K] [--out DIR]
--out writes the same-crop side-by-side (raw | keyed cell | each in-game shot, all scaled to one height)."""
import argparse, json, os, subprocess, sys

import numpy as np


def ffmpeg_rgba(path, vf=None, frame=None):
    cmd = ["ffmpeg", "-hide_banner", "-loglevel", "error", "-i", path]
    if vf:
        cmd += ["-vf", vf]
    if frame is not None:
        cmd += ["-frames:v", "1"]
    cmd += ["-f", "rawvideo", "-pix_fmt", "rgba", "-"]
    probe = subprocess.run(["ffprobe", "-v", "error", "-select_streams", "v:0", "-show_entries", "stream=width,height",
                            "-of", "csv=p=0", path], capture_output=True, text=True, check=True).stdout.split(",")
    raw = subprocess.run(cmd, capture_output=True, check=True).stdout
    w, h = int(probe[0]), int(probe[1])
    if vf and "scale" in vf:  # size after the filter
        n = len(raw) // 4
        h = n // w if n % w == 0 else h
    return np.frombuffer(raw[: w * h * 4], np.uint8).reshape(h, w, 4).astype(np.float64)


def video_frame(video, index, fps, vf_extra=""):
    vf = "fps=%s%s,select=eq(n\\,%d)" % (fps, vf_extra, index)
    return ffmpeg_rgba(video, vf=vf, frame=True)


def luma(img):
    return img[..., 0] * 0.2126 + img[..., 1] * 0.7152 + img[..., 2] * 0.0722


def erode(mask, n):
    m = mask.copy()
    for _ in range(n):
        m[1:, :] &= m[:-1, :].copy(); m[:-1, :] &= m[1:, :].copy()
        m[:, 1:] &= m[:, :-1].copy(); m[:, :-1] &= m[:, 1:].copy()
    return m


def sharpness(img, mask):
    y = luma(img)
    gx = np.zeros_like(y); gy = np.zeros_like(y)
    gx[:, 1:-1] = (y[:, 2:] - y[:, :-2]) / 2; gy[1:-1, :] = (y[2:, :] - y[:-2, :]) / 2
    g = np.hypot(gx, gy)
    return float(g[mask].mean())


def resize(img, w, h, flags="lanczos"):
    """Resample an RGBA float image with ffmpeg (premultiplied, so clear pixels do not bleed colour)."""
    pm = img.copy(); pm[..., :3] *= pm[..., 3:4] / 255.0
    src = np.clip(np.rint(pm), 0, 255).astype(np.uint8)
    hh, ww = src.shape[:2]
    out = subprocess.run(["ffmpeg", "-hide_banner", "-loglevel", "error", "-f", "rawvideo", "-pix_fmt", "rgba", "-s",
                          "%dx%d" % (ww, hh), "-i", "-", "-vf", "scale=%d:%d:flags=%s" % (w, h, flags), "-f", "rawvideo",
                          "-pix_fmt", "rgba", "-"], input=src.tobytes(), capture_output=True, check=True).stdout
    o = np.frombuffer(out, np.uint8).reshape(h, w, 4).astype(np.float64)
    a = np.maximum(o[..., 3:4], 1e-6)
    o[..., :3] = np.where(o[..., 3:4] > 0, np.clip(o[..., :3] * 255.0 / a, 0, 255), 0)
    return o


def match(shot, cell_small, search):
    """Best offset of the downscaled cell in the shot: least mean squared luma error over the cell's solid pixels."""
    m = cell_small[..., 3] > 250
    t = luma(cell_small)
    s = luma(shot)
    h, w = t.shape
    x0, y0, x1, y1 = search
    best = None
    for step, rng in ((4, None), (1, 6)):
        xs = range(x0, x1, step) if rng is None else range(best[1] - rng, best[1] + rng + 1)
        ys = range(y0, y1, step) if rng is None else range(best[2] - rng, best[2] + rng + 1)
        for oy in ys:
            for ox in xs:
                if oy < 0 or ox < 0 or oy + h > s.shape[0] or ox + w > s.shape[1]:
                    continue
                d = s[oy:oy + h, ox:ox + w][m] - t[m]
                e = float((d * d).mean())
                if best is None or e < best[0]:
                    best = (e, ox, oy)
    return best


def register(frame, cell):
    """Offset of `cell` in `frame` with the least luma error (both mean-removed) over the cell's inner solid pixels.
    Coarse pass on every 4th pixel at 4 px steps, then a 1 px pass at full resolution around the coarse best."""
    m = erode(cell[..., 3] > 250, 3); t = luma(cell); s = luma(frame)
    h, w = t.shape; H, W = s.shape
    if not m.any():
        raise ValueError("register: the cell has no solid pixels")

    def err(ox, oy, k):
        y0, x0 = max(oy, 0), max(ox, 0)
        ty, tx = y0 - oy, x0 - ox
        hh, ww = min(h - ty, H - y0), min(w - tx, W - x0)
        if hh < h // 2 or ww < w // 2:
            return None
        mm = m[ty:ty + hh:k, tx:tx + ww:k]
        if mm.sum() < 0.9 * m[::k, ::k].sum():   # most of the figure must be in the frame
            return None
        d = s[y0:y0 + hh:k, x0:x0 + ww:k][mm] - t[ty:ty + hh:k, tx:tx + ww:k][mm]
        d = d - d.mean()
        return float((d * d).mean()) ** 0.5

    best = None
    for oy in range(-h // 2, H - h // 2, 4):
        for ox in range(-w // 2, W - w // 2, 4):
            e = err(ox, oy, 4)
            if e is not None and (best is None or e < best[0]):
                best = (e, ox, oy)
    cx, cy = best[1], best[2]
    best = None
    for oy in range(cy - 4, cy + 5):
        for ox in range(cx - 4, cx + 5):
            e = err(ox, oy, 1)
            if e is not None and (best is None or e < best[0]):
                best = (e, ox, oy)
    return best


def write_png(path, img):
    a = np.clip(np.rint(img), 0, 255).astype(np.uint8)
    h, w = a.shape[:2]
    subprocess.run(["ffmpeg", "-hide_banner", "-loglevel", "error", "-y", "-f", "rawvideo", "-pix_fmt", "rgba", "-s",
                    "%dx%d" % (w, h), "-i", "-", "-frames:v", "1", path], input=a.tobytes(), check=True)


def over(img, bg=(128, 128, 128)):
    o = img.copy(); al = o[..., 3:4] / 255.0
    o[..., :3] = o[..., :3] * al + np.array(bg, np.float64) * (1 - al); o[..., 3] = 255
    return o


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--video", required=True); ap.add_argument("--grid", required=True); ap.add_argument("--sprite", required=True)
    ap.add_argument("--ingame", nargs="*", default=[]); ap.add_argument("--cell", type=int, default=0)
    ap.add_argument("--cols", type=int, default=6); ap.add_argument("--fps", default="12")
    ap.add_argument("--screen-cell-width", default="392,396,400,404,408",
                    help="candidate on-screen widths of one cell in px (game: body world width 600 / ortho 1.5 units per px at 1280 = 400)")
    ap.add_argument("--search", default="600,80,1100,460", help="x0,y0,x1,y1 window for the cell's top-left in the shot")
    ap.add_argument("--cells", default="0,1,2,3,4,5", help="cells the game may be showing (idle plays row 0)")
    ap.add_argument("--out", default=None)
    a = ap.parse_args(argv)
    side = json.load(open(a.sprite, encoding="utf-8"))
    cw, ch = side["grid"]
    grid = ffmpeg_rgba(a.grid)
    def cell(k):
        gx, gy = (k % a.cols) * cw, (k // a.cols) * ch
        return grid[gy:gy + ch, gx:gx + cw]
    c = cell(a.cell)
    src_index = side["source_indices"][a.cell]
    plain = video_frame(a.video, src_index, a.fps)
    lanc = video_frame(a.video, src_index, a.fps, ",scale=-2:720:flags=lanczos")
    res = {"cell": a.cell, "source_index": src_index}
    # (c) resample
    # The sidecar crop is relative to video_to_strip's own --crop, so find where the cell sits in the frame, and at
    # which scale: the cell scaled by sc and placed at the best offset, structure only (luma minus its mean: the grade
    # shifts levels).
    fits = {}
    for wpx in (cw - 12, cw, cw + 12):
        sm = c if wpx == cw else resize(c, wpx, int(round(wpx * ch / cw)))
        fits[wpx] = register(lanc, sm)
    best_w = min(fits, key=lambda k: fits[k][0])
    res["c_scale_fit_rms"] = {str(k): round(v[0], 2) for k, v in fits.items()}
    res["c_source_px_per_cell_px"] = round(best_w / cw, 4)
    cx, cy = fits[cw][1], fits[cw][2]
    res["c_cell_offset_in_frame"] = [cx, cy]
    res["c_video_size"] = [plain.shape[1], plain.shape[0]]
    res["c_lanczos_vs_plain_max_abs"] = float(np.abs(lanc[..., :3] - plain[..., :3]).max())
    pad = np.zeros((lanc.shape[0] + 2 * ch, lanc.shape[1] + 2 * cw, 4)); pad[ch:ch + lanc.shape[0], cw:cw + lanc.shape[1]] = lanc
    raw = pad[ch + cy:2 * ch + cy, cw + cx:2 * cw + cx]
    solid = c[..., 3] == 255
    inner = erode(solid, 3)
    same = np.all(c[..., :3] == raw[..., :3], axis=-1)
    res["c_cell_equals_raw_px_frac"] = round(float(same[solid].mean()), 4)
    # (a) key
    opaque = c[..., 3] > 0
    edge = opaque & ~erode(opaque, 1)
    res["a_partial_alpha_px"] = int(((c[..., 3] > 0) & (c[..., 3] < 255)).sum())
    res["a_edge_px"] = int(edge.sum())
    res["a_feather_px_frac_of_edge"] = round(res["a_partial_alpha_px"] / max(1, res["a_edge_px"]), 4)
    res["a_edge_sharpness_cell_over_raw"] = None
    # silhouette edge contrast: composite both over the same grey; ratio of gradient on the cut edge band
    band = opaque & ~erode(opaque, 2)
    band |= erode(~opaque, 0) & ~erode(~opaque, 2)
    res["a_edge_sharpness_cell_over_raw"] = round(sharpness(over(c), band) / sharpness(raw, band), 4)
    # (b) grade
    res["b_grade_changed_px_frac"] = round(1 - float(same[solid].mean()), 4)
    res["b_grade_mean_abs_rgb"] = round(float(np.abs(c[..., :3] - raw[..., :3])[solid].mean()), 3)
    res["b_inner_sharpness_raw"] = round(sharpness(raw, inner), 3)
    res["b_inner_sharpness_cell"] = round(sharpness(c, inner), 3)
    res["b_inner_sharpness_cell_over_raw"] = round(res["b_inner_sharpness_cell"] / res["b_inner_sharpness_raw"], 4)
    # (d) in-game
    sx0, sy0, sx1, sy1 = (int(v) for v in a.search.split(","))
    panels = [("raw video frame", over(raw)), ("keyed grid cell", over(c))]
    shots = []
    for path in a.ingame:
        shot = ffmpeg_rgba(path)
        best = None
        widths = [float(v) for v in a.screen_cell_width.split(",")]
        for wpx in widths:
            hpx = int(round(wpx * ch / cw))
            for k in (int(v) for v in a.cells.split(",")):
                small = resize(cell(k), int(round(wpx)), hpx)
                m = match(shot, small, (sx0, sy0, sx1, sy1))
                if m and (best is None or m[0] < best[0]):
                    best = (m[0], m[1], m[2], int(round(wpx)), hpx, k)
        e, ox, oy, wpx, hpx, k = best
        ideal = resize(cell(k), wpx, hpx)
        crop = shot[oy:oy + hpx, ox:ox + wpx]
        inner_s = erode(ideal[..., 3] == 255, 2)
        d = {"shot": os.path.basename(path), "matched_cell": k, "screen_px": [ox, oy, wpx, hpx], "rms_luma": round(e ** 0.5, 2),
             "texels_per_screen_px": round(cw / wpx, 3),
             "sharpness_ingame": round(sharpness(crop, inner_s), 3),
             "sharpness_ideal_lanczos_same_size": round(sharpness(ideal, inner_s), 3)}
        d["ingame_over_ideal"] = round(d["sharpness_ingame"] / d["sharpness_ideal_lanczos_same_size"], 4)
        # Split the render loss: contrast (luma spread, e.g. tone mapping or haze) and blur (gradient per unit of spread).
        si, sd = float(luma(crop)[inner_s].std()), float(luma(ideal)[inner_s].std())
        d["luma_mean_ingame_vs_ideal"] = [round(float(luma(crop)[inner_s].mean()), 1), round(float(luma(ideal)[inner_s].mean()), 1)]
        d["contrast_ingame_over_ideal"] = round(si / sd, 4)
        d["blur_ingame_over_ideal"] = round(d["ingame_over_ideal"] / (si / sd), 4)
        d["ideal_over_cell_full_size"] = round(d["sharpness_ideal_lanczos_same_size"] / res["b_inner_sharpness_cell"], 4)
        shots.append(d)
        panels.append(("in-game " + os.path.basename(path), resize(crop, cw, ch, "neighbor")))
    res["d_ingame"] = shots
    print(json.dumps(res, indent=1))
    if a.out:
        os.makedirs(a.out, exist_ok=True)
        strip = np.concatenate([p for _, p in panels], axis=1)
        write_png(os.path.join(a.out, "owl-sharpness-side-by-side.png"), strip)
        with open(os.path.join(a.out, "owl-sharpness.json"), "w", encoding="utf-8") as fh:
            json.dump(dict(res, panels=[n for n, _ in panels]), fh, indent=1); fh.write("\n")
    return 0


if __name__ == "__main__":
    sys.exit(main())
