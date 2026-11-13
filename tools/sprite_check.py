#!/usr/bin/env python3
"""Art Director / Asset Specialist gate for exported sprite sheets and flipbook frames (PNG).

Thresholds live in pipeline/art/style.json under "sprite" (one set per kind: silhouette, fx, tile).

Checks, per frame:
  size        all frames the same size; equal to --size if given; sheet divisible by --grid
  pow2        sheet (or each frame file) is power-of-two sized, when style.json require_pow2 is true or --pow2
  background  the 1-px border ring is transparent (share of visible border pixels <= border_visible_max),
              and the frame has transparent pixels at all (a flat background means it was not cut out)
  fringe      share of visible pixels that are semi-transparent (alpha between alpha_clear_max and
              alpha_solid_min). Masked sprite materials cut alpha at one value, so a wide soft edge turns
              into ragged holes. This is not a pixel-art rule: the art bible wants painted, filtered edges.
  halo        share of edge pixels (semi-transparent, or transparent next to a visible pixel) that are light
              (L* >= halo_l_min), measured only when the solid pixels are darker than that on average.
              A light matte bleeds into dark silhouettes under bilinear filtering.
  fill        alpha-mask fill ratio = visible pixels / bounding box of visible pixels. Too low: wispy shape
              that will not read; too high: a box, background not removed.
  dark        share of visible pixels with L* <= dark_l_max (silhouettes are near-black, art bible pillar 2)
  empty       a frame with no visible pixels (trailing empty cells of a sheet are allowed)
  pivot       silhouette sheets with "anim" or "loop": true (one-shots too): the feet point of each frame
              moves at most sprite.pivot_drift_max_px across frames (max minus min). Feet point = bottom-center
              of the lowest sprite.pivot_feet_rows opaque rows (sidecar "feet_rows" overrides), so an umbrella
              that opens to one side does not move it. A sidecar may raise the limit with "pivot_drift_max_px"
              + "pivot_drift_reason".
  anim        sidecar "anim" names a row of style.json "anims"; frame count and "fps" must fit that row
  seam        kind tile: mean delta E76 between the left and right edge columns (and top/bottom with
              "tile_axes": "xy") is at most seam_delta_e_max, so copies side by side show no seam

Other modes (rules in style.json; detail in pipeline/art/import-rules.md):
  --sources CONTENT SOURCE  every asset folder under CONTENT (Content/UmbrellaElla/Art) that holds a .uasset has a
              layered source (.psd, .kra, .ase, .aseprite) under SOURCE/<same folder>/ outside Raw/ (Art/Source),
              or the Blender scene it was rendered from (a .blend anywhere under that folder, Raw/ included),
              so every imported asset can be edited and re-exported (asset-specialist.md checklist)
  --names DIR          asset names under DIR (Content/UmbrellaElla/Art) match style.json "naming"
  --import-report F    an editor dump of texture/sprite/flipbook settings (JSON) meets "unreal_import"
  --config DIR         Config/*.ini carry the Paper2D import defaults in "unreal_import.config"
  --uproject FILE      the .uproject enables Paper2D and does not list PaperZD ("unreal_import.uproject")
  --width-ratio OPEN CLOSED   umbrella open vs closed sheet: opaque box width ratio >= sprite.umbrella_width_ratio_min

Usage:
  python3 tools/sprite_check.py sheet.png --grid 128x128 [--frames 6] [--kind silhouette]
  python3 tools/sprite_check.py frame_01.png frame_02.png ... [--size 128x128]
  python3 tools/sprite_check.py --scan Art          # every PNG under Art/ needs a <name>.sprite.json sidecar
     sidecar: {"kind": "silhouette", "grid": [128, 128], "frames": 6, "size": [128, 128],
               "margin": 0, "spacing": 0, "loop": true, "anim": "IdleFloat", "fps": 8,
               optional "pivot_drift_max_px": 3, "pivot_drift_reason": "<why this sheet may drift more>",
               optional "feet_rows": 6}
     a PNG with no sidecar FAILS unless a folder on its path is in sprite.sidecar_exempt_dirs (Raw, Reference)
     a sidecar PNG that is still a Git LFS pointer is a SKIP; with --fail-lfs-pointer it is a FAIL (use in CI)
  add --require-dir to fail when the scanned folder does not exist; add --json for machine-readable output
Exit 0 = pass (or nothing to check), 1 = fail, 2 = usage/input error.
"""
import argparse
import configparser
import json
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from png import read_png  # noqa: E402
import frame_register  # noqa: E402
from art_check import DEFAULT_STYLE, delta_e, rgb_to_lab  # noqa: E402

LFS_POINTER = b"version https://git-lfs"


def parse_wh(s):
    w, h = s.lower().split("x")
    return int(w), int(h)


def is_pow2(n):
    return n > 0 and n & (n - 1) == 0


def grid_fits(n, cell, margin, spacing):
    """True when n px holds a whole number of cells: margin + k*cell + (k-1)*spacing + margin."""
    inner = n - 2 * margin + spacing
    return inner > 0 and inner % (cell + spacing) == 0


def frames_from_sheet(w, h, rows, grid, margin=0, spacing=0):
    gw, gh = grid
    out = []
    for y0 in range(margin, h - margin - gh + 1, gh + spacing):
        for x0 in range(margin, w - margin - gw + 1, gw + spacing):
            out.append([row[x0:x0 + gw] for row in rows[y0:y0 + gh]])
    return out


def edge_seam(rows, clear, axes="x"):
    """Mean delta E76 between opposite edge pixels (left/right; and top/bottom for "xy").
    None when no opposite pair is opaque on both sides."""
    h, w = len(rows), len(rows[0]) if rows else 0
    pairs = [(rows[y][0], rows[y][w - 1]) for y in range(h)]
    if "y" in axes:
        pairs += [(rows[0][x], rows[h - 1][x]) for x in range(w)]
    ds = [delta_e(rgb_to_lab(a[:3]), rgb_to_lab(b[:3])) for a, b in pairs if a[3] > clear and b[3] > clear]
    return round(sum(ds) / len(ds), 2) if ds else None


def measure_frame(rows, sp):
    clear, solid_min = sp["alpha_clear_max"], sp["alpha_solid_min"]
    h, w = len(rows), len(rows[0]) if rows else 0
    vis = semi = dark = transparent = 0
    solid = solid_l = 0
    border = border_vis = 0
    edge = edge_light = 0
    x0, y0, x1, y1 = w, h, -1, -1
    lcache = {}

    def light(px):
        key = px[:3]
        if key not in lcache:
            lcache[key] = rgb_to_lab(key)[0]
        return lcache[key]

    for y in range(h):
        row = rows[y]
        for x in range(w):
            a = row[x][3]
            on_border = x == 0 or y == 0 or x == w - 1 or y == h - 1
            if on_border:
                border += 1
            if a <= clear:
                transparent += 1
                # transparent pixel touching a visible one: its RGB is what bilinear filtering blends in
                if any(0 <= nx < w and 0 <= ny < h and rows[ny][nx][3] > clear
                       for nx, ny in ((x - 1, y), (x + 1, y), (x, y - 1), (x, y + 1))):
                    edge += 1
                    if light(row[x]) >= sp["halo_l_min"]:
                        edge_light += 1
                continue
            vis += 1
            if on_border:
                border_vis += 1
            x0, y0, x1, y1 = min(x0, x), min(y0, y), max(x1, x), max(y1, y)
            L = light(row[x])
            if a >= solid_min:
                solid += 1
                solid_l += L
            else:
                semi += 1
                edge += 1
                if L >= sp["halo_l_min"]:
                    edge_light += 1
            if L <= sp["dark_l_max"]:
                dark += 1
    m = {"size": [w, h], "visible": vis, "transparent_share": round(transparent / max(1, w * h), 4)}
    if vis:
        bbox = (x1 - x0 + 1) * (y1 - y0 + 1)
        m.update({
            "bbox": [x0, y0, x1 - x0 + 1, y1 - y0 + 1],
            "fill": round(vis / bbox, 4),
            "fringe": round(semi / vis, 4),
            # halo only means something around a darker shape; a light shape's own soft edge is not a matte
            "halo": round(edge_light / edge, 4) if edge and (not solid or solid_l / solid < sp["halo_l_min"]) else 0.0,
            "dark_share": round(dark / vis, 4),
            "border_visible": round(border_vis / max(1, border), 4),
        })
    return m


def feet_point(rows, clear, n):
    """Bottom-center of the lowest n rows that hold a visible pixel: ((min x + max x + 1) / 2, bottom + 1).
    With n >= the shape's height this is the bottom-center of the opaque box. None for an empty frame."""
    ys = [y for y, row in enumerate(rows) if any(px[3] > clear for px in row)]
    if not ys:
        return None
    bottom = ys[-1]
    xs = [x for y in range(max(0, bottom - n + 1), bottom + 1) for x, px in enumerate(rows[y]) if px[3] > clear]
    return ((min(xs) + max(xs) + 1) / 2, bottom + 1)


def evaluate_frame(m, k):
    fails = []
    if not m["visible"]:
        return ["empty: frame has no visible pixels"]
    if m["transparent_share"] == 0 and k["border_visible_max"] < 1.0:
        fails.append("background: no transparent pixels at all (background not cut out)")
    if m["border_visible"] > k["border_visible_max"]:
        fails.append(f"background: border_visible {m['border_visible']} > {k['border_visible_max']} (frame edge is not transparent)")
    if m["fringe"] > k["fringe_max"]:
        fails.append(f"fringe {m['fringe']} > {k['fringe_max']} (too many semi-transparent pixels for a masked sprite)")
    if m["halo"] > k["halo_max"]:
        fails.append(f"halo {m['halo']} > {k['halo_max']} (light matte around the shape; will show as a light outline)")
    if not (k["fill_min"] <= m["fill"] <= k["fill_max"]):
        fails.append(f"fill {m['fill']} outside [{k['fill_min']}, {k['fill_max']}] (silhouette too wispy, or a box)")
    if m["dark_share"] < k["dark_share_min"]:
        fails.append(f"dark_share {m['dark_share']} < {k['dark_share_min']} (silhouette is not near-black)")
    return fails


def check(paths, style, kind="silhouette", grid=None, size=None, frames=None, pow2=None,
          margin=0, spacing=0, loop=False, anim=None, fps=None, tile_axes="x",
          drift_max=None, drift_reason=None, feet_rows=None, anchor_band=None, span_mode=None):
    sp = style["sprite"]
    if kind not in sp["kinds"]:
        raise ValueError(f"unknown kind '{kind}' (style.json has {sorted(sp['kinds'])})")
    k = sp["kinds"][kind]
    need_pow2 = sp.get("require_pow2", False) if pow2 is None else pow2
    report = {"kind": kind, "files": paths, "frames": [], "failures": []}
    fl = report["failures"]
    frame_rows = []
    for p in paths:
        w, h, rows = read_png(p)
        if need_pow2 and not (is_pow2(w) and is_pow2(h)):
            fl.append(f"pow2: {os.path.basename(p)} is {w}x{h}, not power-of-two")
        if grid:
            if not (grid_fits(w, grid[0], margin, spacing) and grid_fits(h, grid[1], margin, spacing)):
                fl.append(f"size: {os.path.basename(p)} {w}x{h} is not a whole number of {grid[0]}x{grid[1]} cells "
                          f"with margin {margin} and spacing {spacing} (check the sidecar's margin and spacing)")
            frame_rows += [(f"{os.path.basename(p)}#{i}", fr)
                           for i, fr in enumerate(frames_from_sheet(w, h, rows, grid, margin, spacing))]
        else:
            frame_rows.append((os.path.basename(p), rows))
    sizes = {(len(r[0]) if r else 0, len(r)) for _, r in frame_rows}
    if len(sizes) > 1:
        fl.append(f"size: frames differ in size {sorted(sizes)}")
    if size and sizes and sizes != {tuple(size)}:
        fl.append(f"size: frames are {sorted(sizes)}, declared {size[0]}x{size[1]}")
    measured = [(name, measure_frame(r, sp)) for name, r in frame_rows]
    # trailing empty cells of a sheet are padding, not a missing frame
    while grid and measured and not measured[-1][1]["visible"] and len(measured) > 1:
        measured.pop()
    if frames is not None and len(measured) != frames:
        fl.append(f"size: {len(measured)} non-empty frames, expected {frames}")
    for (name, m), (_, r) in zip(measured, frame_rows):
        m["frame"] = name
        m["failures"] = evaluate_frame(m, k)
        if "seam_delta_e_max" in k and m["visible"]:
            m["seam"] = edge_seam(r, sp["alpha_clear_max"], tile_axes)
            if m["seam"] is not None and m["seam"] > k["seam_delta_e_max"]:
                m["failures"].append(f"seam {m['seam']} > {k['seam_delta_e_max']} (edges do not match; copies side by side show a seam)")
        report["frames"].append(m)
        fl += [f"{name}: {f}" for f in m["failures"]]
    if loop or (anim is not None and kind == "silhouette"):
        n_rows = feet_rows if feet_rows is not None else sp["pivot_feet_rows"]
        feet = [feet_point(r, sp["alpha_clear_max"], n_rows)
                for (_, m), (_, r) in zip(measured, frame_rows) if m["visible"]]
        lim = sp["pivot_drift_max_px"]
        if drift_max is not None:
            if not (drift_reason or "").strip():
                fl.append("pivot: sidecar sets pivot_drift_max_px with no pivot_drift_reason")
            else:
                lim = drift_max
        if feet:
            dx = max(f[0] for f in feet) - min(f[0] for f in feet)
            dy = max(f[1] for f in feet) - min(f[1] for f in feet)
            report["pivot_drift_px"] = [dx, dy]
            if max(dx, dy) > lim:
                fl.append(f"pivot: feet point (bottom-center of the lowest {n_rows} opaque rows) drifts {dx:g} px in x, "
                          f"{dy:g} px in y across frames (limit {lim}; the feet will jump)")
    if (loop or (anim is not None and kind == "silhouette")) and len(frame_rows) > 1:
        # jitter: anchor offset (px) and scale drift (%) between consecutive frames, limits measured on the team's
        # reference animations (tools/frame_register.py JITTER_LIMITS). One-shots are not wrapped; loops are.
        keep = [i for i, (_, m) in enumerate(measured) if m["visible"]]   # original frame numbers of the live frames
        live = [(len(frame_rows[i][1][0]) if frame_rows[i][1] else 0, len(frame_rows[i][1]), frame_rows[i][1]) for i in keep]
        band = anchor_band or (feet_rows if feet_rows is not None else sp["pivot_feet_rows"])   # what the cutter registered on
        jit = frame_register.jitter(live, clear=sp["alpha_clear_max"], band=band, span_mode=span_mode or "base", loop=loop)
        jit["worst"] = [keep[w] for w in jit["worst"]]
        report["jitter"] = {k_: round(v, 2) for k_, v in jit.items() if k_ != "worst"}
        lim = dict(frame_register.JITTER_LIMITS)
        if drift_max is not None and (drift_reason or "").strip():   # the sidecar's reasoned pivot override covers this too
            lim["offset_px"] = max(lim["offset_px"], drift_max)
        if jit["offset_px"] > lim["offset_px"]:
            fl.append(f"jitter: anchor moves {jit['offset_px']:g} px between frames {jit['worst'][0]} and "
                      f"{jit['worst'][0] + 1} (limit {lim['offset_px']:g}; register the strip: assetgen frames)")
        if jit["scale_pct"] > lim["scale_pct"]:
            fl.append(f"jitter: figure scale drifts {jit['scale_pct']:.1f}% between frames {jit['worst'][1]} and "
                      f"{jit['worst'][1] + 1} (limit {lim['scale_pct']:g}%; register the strip: assetgen frames)")
    if anim is not None:
        table = style.get("anims", {})
        row = table.get(anim) if anim != "note" else None
        if row is None:
            fl.append(f"anim: '{anim}' is not in style.json anims ({sorted(a for a in table if a != 'note')})")
        else:
            lo_hi = row.get("frames")
            if lo_hi and not (lo_hi[0] <= len(measured) <= lo_hi[1]):
                fl.append(f"anim: {anim} has {len(measured)} frames, the art bible allows {lo_hi[0]}-{lo_hi[1]}")
            want = row["fps"] if isinstance(row["fps"], list) else [row["fps"], row["fps"]]
            if fps is not None and not (want[0] <= fps <= want[1]):
                fl.append(f"anim: {anim} at {fps} fps, the art bible says {want[0] if want[0] == want[1] else want}")
    report["pass"] = not fl
    return report


def sidecar_exempt(path, folder, sp):
    rel = os.path.relpath(os.path.dirname(path), folder)
    exempt = {d.lower() for d in sp.get("sidecar_exempt_dirs", [])}
    return any(part.lower() in exempt for part in rel.split(os.sep))


def scan(folder, style, fail_lfs_pointer=False):
    """Check every PNG under folder against its .sprite.json sidecar. Returns (reports, skipped).
    A PNG with no sidecar outside an exempt folder is a failed report, not a skip. A sidecar PNG that is
    still a Git LFS pointer is a skip, or a failed report with fail_lfs_pointer (CI after git lfs pull)."""
    reports, skipped = [], []
    for d, _, fs in os.walk(folder):
        for f in sorted(fs):
            if not f.lower().endswith(".png"):
                continue
            p = os.path.join(d, f)
            side = os.path.splitext(p)[0] + ".sprite.json"
            with open(p, "rb") as fh:
                head = fh.read(len(LFS_POINTER))
            if not os.path.isfile(side):
                if sidecar_exempt(p, folder, style["sprite"]):
                    skipped.append((p, "no .sprite.json sidecar (exempt folder)"))
                else:
                    reports.append({"kind": "?", "files": [p], "frames": [], "pass": False,
                                    "failures": ["sidecar: no .sprite.json next to it. Add one, or move the file "
                                                 f"into a {'/'.join(style['sprite'].get('sidecar_exempt_dirs', []))} folder "
                                                 "if it is not a game sprite"]})
            elif head == LFS_POINTER and fail_lfs_pointer:
                reports.append({"kind": "?", "files": [p], "frames": [], "pass": False,
                                "failures": ["lfs: still a Git LFS pointer, so no pixel was checked "
                                             "(run git lfs pull --include='Art/**/*.png' first)"]})
            elif head == LFS_POINTER:
                skipped.append((p, "Git LFS pointer, not the image (run git lfs pull)"))
            else:
                with open(side, encoding="utf-8") as fh:
                    meta = json.load(fh)
                reports.append(check([p], style, meta.get("kind", "silhouette"),
                                     tuple(meta["grid"]) if meta.get("grid") else None,
                                     tuple(meta["size"]) if meta.get("size") else None,
                                     meta.get("frames"), meta.get("pow2"),
                                     meta.get("margin", 0), meta.get("spacing", 0), meta.get("loop", False),
                                     meta.get("anim"), meta.get("fps"), meta.get("tile_axes", "x"),
                                     meta.get("pivot_drift_max_px"), meta.get("pivot_drift_reason"),
                                     meta.get("feet_rows"), meta.get("anchor_band"), meta.get("span_mode")))
    return reports, skipped


LAYERED_EXT = (".psd", ".kra", ".ase", ".aseprite")
SCENE_EXT = (".blend",)


def check_sources(content, source):
    """FAIL lines for asset folders under `content` with imported assets but no layered source file."""
    fails = []
    for name in sorted(os.listdir(content)):
        folder = os.path.join(content, name)
        if not os.path.isdir(folder):
            continue
        if not any(f.lower().endswith(".uasset") for _, _, fs in os.walk(folder) for f in fs):
            continue
        src = os.path.join(source, name)
        layered = [f for d, _, fs in os.walk(src) if "Raw" not in os.path.relpath(d, src).split(os.sep)
                   for f in fs if f.lower().endswith(LAYERED_EXT)]
        # the Blender scene the frames were rendered from (tools/assetgen.py blender keeps it beside them in Raw/)
        layered += [f for _, _, fs in os.walk(src) for f in fs if f.lower().endswith(SCENE_EXT)]
        if not layered:
            fails.append(f"{name}: imported assets but no layered source ({', '.join(LAYERED_EXT)}) or Blender "
                         f"scene (.blend) in {os.path.join(source, name)}/")
    return fails


def check_names(folder, style):
    """Asset file names under folder against style.json naming. Returns a list of failures."""
    nm = style["naming"]
    ok, banned = re.compile(nm["asset_regex"]), re.compile(nm["banned_regex"])
    fails = []
    for d, _, fs in os.walk(folder):
        for f in sorted(fs):
            stem, ext = os.path.splitext(f)
            if ext.lower() not in nm["extensions"]:
                continue
            rel = os.path.relpath(os.path.join(d, f), folder)
            if banned.search(stem):
                fails.append(f"name: {rel}: no _v2/_final/_new in names; versions live in git")
            elif not ok.match(stem):
                hint = ""
                if re.search(r"_\d(_PH)?$", stem):
                    hint = (" Frame number is not 2 digits. If the 5.8.4 Naming Template cannot pad, rename with "
                            "the fallback in pipeline/art/import-rules.md section 3")
                fails.append(f"name: {rel}: does not match {nm['asset_regex']} (T_/SPR_/FB_<Asset>_<State>[_NN][_PH]).{hint}")
    return fails


def sprite_kind(a, spr):
    """Kind of a dumped sprite: its own "kind" field, else the first kind_prefixes match, else silhouette."""
    if a.get("kind"):
        return a["kind"]
    for prefix, kind in spr.get("kind_prefixes", {}).items():
        if a.get("name", "").startswith(prefix):
            return kind
    return "silhouette"


def check_flipbook(a, anims, fb_rules):
    """One PaperFlipbook entry. keyframes is a list of {"sprite", "frame_run"}. Returns (failures, sprite names)."""
    n = a.get("name", "?")
    m = re.match(r"^FB_([A-Za-z0-9]+)_([A-Za-z0-9]+)", n)
    row = anims.get(m.group(2)) if m else None
    if row is None or not isinstance(row, dict):
        return [f"fps: {n}: no anims row for its <Anim> part in style.json"], []
    fails = []
    want = row["fps"] if isinstance(row["fps"], list) else [row["fps"], row["fps"]]
    if not (want[0] <= a.get("fps", -1) <= want[1]):
        fails.append(f"fps: {n} plays at {a.get('fps')} fps, the art bible says {want}")
    kf = a.get("keyframes")
    if not isinstance(kf, list) or not all(isinstance(k, dict) and k.get("sprite") for k in kf):
        return fails + [f"frames: {n} keyframes must be a list of {{\"sprite\", \"frame_run\"}} "
                        "(pipeline/art/import-rules.md section 2), got {kf!r}"], []
    sprites = [k["sprite"] for k in kf]
    unique = list(dict.fromkeys(sprites))
    lo_hi = row.get("frames")
    if lo_hi and not (lo_hi[0] <= len(unique) <= lo_hi[1]):
        fails.append(f"frames: {n} uses {len(unique)} different sprites, the art bible allows {lo_hi}")
    own = re.compile(rf"^SPR_{m.group(1)}_{m.group(2)}_(\d{{2}})(_PH)?$")
    idx = []
    for s in sprites:
        mm = own.match(s)
        if not mm:
            fails.append(f"frames: {n} keyframe {s} is not a SPR_{m.group(1)}_{m.group(2)}_NN frame of this anim")
            return fails, unique
        idx.append(int(mm.group(1)))
    if any(x == y for x, y in zip(idx, idx[1:])):
        fails.append(f"frames: {n} shows the same sprite in two keyframes in a row; use frame_run for a hold")
    elif row.get("order") != "any" and any(y < x for x, y in zip(idx, idx[1:])):
        fails.append(f"frames: {n} keyframes are out of order {idx}; frames play in ascending _NN")
    if any(not isinstance(k.get("frame_run", 1), int) or k.get("frame_run", 1) < 1 for k in kf):
        fails.append(f"frames: {n} has a keyframe with frame_run below 1")
    return fails, unique


def collect_sockets(a, spr, groups):
    """Check one sprite's sockets: each is {"name", "location": [x, y]}, and required names are present.
    Adds each frame's socket locations to groups[SPR_<Asset>_<Anim>] for socket_drift. Returns failures."""
    n = a.get("name", "?")
    fails, names = [], []
    for s in a.get("sockets") or []:
        loc = s.get("location") if isinstance(s, dict) else None
        if not (isinstance(loc, list) and len(loc) == 2 and all(isinstance(v, (int, float)) for v in loc)):
            fails.append(f"socket: {n} socket {s!r} needs {{\"name\", \"location\": [x, y]}} "
                         "(pipeline/art/import-rules.md section 2)")
            continue
        names.append(s.get("name"))
        m = re.match(r"^(SPR_[A-Za-z0-9]+_[A-Za-z0-9]+)_\d{2}(_PH)?$", n)
        if m:
            groups.setdefault(m.group(1), {}).setdefault(s.get("name"), []).append((n, loc))
    for prefix, need in spr["required_sockets"].items():
        if n.startswith(prefix):
            missing = [s for s in need if s not in names]
            if missing and not fails:
                fails.append(f"socket: {n} has no socket {missing}; spawn points come from sockets, not code offsets")
    return fails


def socket_drift(groups, limit):
    """One SPR_<Asset>_<Anim> set: each socket sits within limit px (max minus min, x and y) on every frame."""
    fails = []
    for group, by_name in sorted(groups.items()):
        for name, locs in sorted(by_name.items()):
            dx = max(l[0] for _, l in locs) - min(l[0] for _, l in locs)
            dy = max(l[1] for _, l in locs) - min(l[1] for _, l in locs)
            if max(dx, dy) > limit:
                fails.append(f"socket: {name} on {group}_NN moves {dx:g} px in x, {dy:g} px in y across frames "
                             f"(limit {limit}; the spawn point jumps)")
    return fails


DUMP_TOOL = "tools/ue/art_dump.py"
DUMP_ROOT = "/Game/UmbrellaElla/Art"


def gate_problems(dump, style):
    """Extra rules for a gate (--gate): the dump is the script's dump of the whole art folder, the rule
    names are verified on 5.8.4, and D13 has set the mips rule. A hand dump (a bare list) never covers a gate."""
    ui = style["unreal_import"]
    out = []
    if not isinstance(dump, dict) or dump.get("tool") != DUMP_TOOL or dump.get("root") != DUMP_ROOT:
        out.append(f"gate: not a {DUMP_TOOL} dump of {DUMP_ROOT} (a hand dump never covers a gate; "
                   "the dump needs {\"tool\", \"root\", \"assets\"})")
    if ui.get("status") != "verified":
        out.append(f"gate: style.json unreal_import.status is {ui.get('status')!r}; rule names must be verified "
                   "on 5.8.4 (card 0.4a) before a gate counts")
    if ui["texture"].get("mips") is None:
        out.append("mips: unreal_import.texture.mips is null (D13 open); a gate needs 'mips' or 'none' set")
    if ui["texture"].get("lod_group") is None:
        out.append("texture_group: unreal_import.texture.lod_group is null (D-new-art-texgroup open); "
                   "a gate needs one texture group set")
    return out


def frame_rect(nn, tex_w, tex_h, cell, margin, spacing):
    """(x, y) of grid cell nn, counted left to right then top to bottom, as frames_from_sheet cuts them.
    None when the sheet has fewer cells."""
    xs = list(range(margin, tex_w - margin - cell[0] + 1, cell[0] + spacing))
    ys = list(range(margin, tex_h - margin - cell[1] + 1, cell[1] + spacing))
    if not xs or nn >= len(xs) * len(ys):
        return None
    return xs[nn % len(xs)], ys[nn // len(xs)]


def check_grid(a, textures, gate):
    """A SPR_<Asset>_<Anim>_NN frame must sit on cell NN of its sheet's grid (sidecar cell, margin, spacing,
    copied into the texture's "sheet" by the dump) with the cell's size. Returns failures."""
    n = a.get("name", "?")
    m = re.match(r"^SPR_([A-Za-z0-9]+)_([A-Za-z0-9]+)_(\d{2})(_PH)?$", n)
    if not m:
        return []
    tname = a.get("texture") or f"T_{m.group(1)}_{m.group(2)}"
    t = textures.get(tname)
    if t is None:
        return [f"grid: {n}: its texture {tname} is not in the dump"] if gate else []
    sheet = t.get("sheet") or {}
    if not sheet.get("grid"):
        return [f"grid: {tname} has no sheet grid (copy cell, margin, spacing from its .sprite.json sidecar)"]
    cell = tuple(sheet["grid"])
    at = frame_rect(int(m.group(3)), t.get("width", 0), t.get("height", 0), cell,
                    sheet.get("margin", 0), sheet.get("spacing", 0))
    uv, size = a.get("source_uv"), a.get("source_size")
    if at is None:
        return [f"grid: {n}: {tname} has no cell {m.group(3)} on a {cell[0]}x{cell[1]} grid"]
    if list(uv or []) != list(at) or list(size or []) != list(cell):
        return [f"grid: {n} is cut at {uv} size {size}, its sheet grid puts frame {m.group(3)} at "
                f"{list(at)} size {list(cell)} (extract in Grid mode with the sidecar's cell, margin, spacing)"]
    return []


def check_import_report(assets, style, gate=False):
    """Check an editor dump of asset settings (format in pipeline/art/import-rules.md) against style.json
    unreal_import. The dump is a list of assets, or the art_dump.py envelope {"tool", "root", "assets"}.
    gate=True adds gate_problems. Returns a list of failures, one per broken rule per asset."""
    ui = style["unreal_import"]
    tx, spr = ui["texture"], ui["sprite"]
    anims = style.get("anims", {})
    fb_rules = ui.get("flipbook", {})
    fails = gate_problems(assets, style) if gate else []
    if isinstance(assets, dict):
        assets = assets.get("assets")
    if not isinstance(assets, list) or not assets:
        return fails + ["dump: empty or not a JSON list; an empty dump checks nothing (run the dump over /Game/UmbrellaElla/Art)"]
    textures = {a.get("name"): a for a in assets if isinstance(a, dict) and a.get("class") == "Texture2D"}
    pivots, ppus, fb_sprites, sockets = {}, {}, set(), {}
    want_ppu = ui.get("pixels_per_unit")
    for a in assets:
        n, c = a.get("name", "?"), a.get("class")
        if c == "Texture2D":
            if a.get("filter") in tx["filter_banned"]:
                fails.append(f"filter: {n} uses {a.get('filter')}; painted art needs bilinear or trilinear")
            if a.get("srgb") is not tx["srgb"]:
                fails.append(f"srgb: {n} has sRGB {a.get('srgb')}, needs {tx['srgb']}")
            if a.get("compression") != tx["compression"]:
                fails.append(f"compression: {n} is {a.get('compression')}, needs {tx['compression']} (UserInterface2D)")
            if a.get("never_stream") is not tx["never_stream"]:
                fails.append(f"stream: {n} NeverStream is {a.get('never_stream')}, sprites must never stream")
            if a.get("lod_group") in tx["lod_group_banned"]:
                fails.append(f"texture_group: {n} is in {a.get('lod_group')} (the unfiltered 2D Pixels group)")
            elif tx.get("lod_group") is not None and a.get("lod_group") != tx["lod_group"]:
                fails.append(f"texture_group: {n} is in {a.get('lod_group')}, the project group is {tx['lod_group']} "
                             "(D-new-art-texgroup)")
            if tx.get("mips") == "mips":
                if a.get("mip_gen") == "TMGS_NoMipmaps":
                    fails.append(f"mips: {n} has no mips, D13 picked mips")
                if not (is_pow2(a.get("width", 0)) and is_pow2(a.get("height", 0))):
                    fails.append(f"mips: {n} is {a.get('width')}x{a.get('height')}, not power-of-two (no mips)")
            elif tx.get("mips") == "none" and a.get("mip_gen") != "TMGS_NoMipmaps":
                fails.append(f"mips: {n} has mips, D13 picked none")
        elif c == "PaperSprite":
            kind = sprite_kind(a, spr)
            allowed = spr["materials_by_kind"].get(kind)
            if allowed is None:
                fails.append(f"material: {n} has kind {kind!r}, not in {sorted(spr['materials_by_kind'])}")
            elif a.get("material") not in allowed:
                fails.append(f"material: {n} ({kind}) uses {a.get('material')}; {kind} needs {allowed} "
                             "(translucent only for fx glow)")
            if a.get("collision") != spr["collision"]:
                fails.append(f"collision: {n} sprite collision is {a.get('collision')}, needs None (collision lives on the actor)")
            if a.get("atlas_group") != spr["atlas_group"]:
                fails.append(f"atlas: {n} has atlas group {a.get('atlas_group')}; atlas groups are off")
            req = next((v for k, v in spr.get("required_pivot", {}).items() if n.startswith(k)), None)
            if req and a.get("pivot_mode") != req:
                fails.append(f"pivot: {n} pivot mode {a.get('pivot_mode')}, the art bible says {req} for this asset")
            elif a.get("pivot_mode") not in spr["pivot_modes"]:
                fails.append(f"pivot: {n} pivot mode {a.get('pivot_mode')} not in {spr['pivot_modes']}")
            else:
                # one pivot per asset across all anims (idle vs open must not jump)
                m = re.match(r"^(SPR_[A-Za-z0-9]+)_", n)
                if m:
                    pivots.setdefault(m.group(1), {}).setdefault(
                        (a.get("pivot_mode"), tuple(a.get("pivot", []) or [])), n)
            ppu = a.get("pixels_per_unit")
            if want_ppu is not None and ppu != want_ppu:
                fails.append(f"ppu: {n} has pixels_per_unit {ppu}, the project value is {want_ppu} (D-new-port-10)")
            elif want_ppu is None:
                ppus.setdefault(ppu, n)
            big = max(a.get("width", 0), a.get("height", 0)) > spr["full_rect_max_px"]
            if big and a.get("render_geometry") == spr["full_rect_geometry"]:
                fails.append(f"geometry: {n} is over {spr['full_rect_max_px']} px with Full Rect render geometry "
                             "(overdraw); use Tight or Shrink Wrapped")
            fails += check_grid(a, textures, gate)
            fails += collect_sockets(a, spr, sockets)
        elif c == "PaperFlipbook":
            f, used = check_flipbook(a, anims, fb_rules)
            fails += f
            fb_sprites.update(used)
        else:
            fails.append(f"dump: {n} has class {c!r}; the dump holds Texture2D, PaperSprite and PaperFlipbook only")
    for group, seen in sorted(pivots.items()):
        if len(seen) > 1:
            fails.append(f"pivot: sprites of {group} do not share one pivot across anims "
                         f"{sorted((str(k), v) for k, v in seen.items())}")
    fails += socket_drift(sockets, spr.get("socket_drift_max_px", 2))
    if len(ppus) > 1:
        fails.append(f"ppu: sprites use different pixels_per_unit {sorted(ppus.items(), key=str)}; one value for all (D-new-port-10)")
    cap = fb_rules.get("frames_total_max")
    if cap is not None and len(fb_sprites) > cap:
        fails.append(f"frames: flipbooks use {len(fb_sprites)} different sprites in total, the jam cap is {cap} (D-new-caps)")
    return fails


def check_uproject(path, style):
    """The .uproject Plugins list against unreal_import.uproject. Returns a list of failures."""
    rules = style["unreal_import"]["uproject"]
    with open(path, encoding="utf-8") as fh:
        proj = json.load(fh)
    plugins = {p.get("Name"): p for p in proj.get("Plugins", []) if isinstance(p, dict)}
    fails = []
    for name in rules["required_plugins"]:
        if plugins.get(name, {}).get("Enabled") is not True:
            fails.append(f"plugin: {os.path.basename(path)} does not list {{\"Name\": \"{name}\", \"Enabled\": true}}")
    for name in rules["banned_plugins"]:
        if name in plugins:
            fails.append(f"plugin: {os.path.basename(path)} lists {name}; it is not allowed (pipeline/unreal-rules.md)")
    return fails


def sheet_widths(path, style):
    """Opaque bounding-box width of each non-empty frame of a sheet. Grid, margin and spacing come from
    the <name>.sprite.json sidecar; with no sidecar the whole image is one frame."""
    sp = style["sprite"]
    w, h, rows = read_png(path)
    side = os.path.splitext(path)[0] + ".sprite.json"
    meta = {}
    if os.path.isfile(side):
        with open(side, encoding="utf-8") as fh:
            meta = json.load(fh)
    cells = (frames_from_sheet(w, h, rows, tuple(meta["grid"]), meta.get("margin", 0), meta.get("spacing", 0))
             if meta.get("grid") else [rows])
    out = []
    for fr in cells:
        m = measure_frame(fr, sp)
        if m["visible"]:
            out.append(m["bbox"][2])
    return out


def check_width_ratio(open_path, closed_path, style):
    """Umbrella open vs closed: narrowest open frame / widest closed frame >= umbrella_width_ratio_min.
    Returns (failures, ratio)."""
    need = style["sprite"]["umbrella_width_ratio_min"]
    ow, cw = sheet_widths(open_path, style), sheet_widths(closed_path, style)
    if not ow or not cw:
        return [f"width: {'open' if not ow else 'closed'} sheet has no visible frame"], None
    ratio = round(min(ow) / max(cw), 3)
    if ratio < need:
        return [f"width: open/closed silhouette width {min(ow)}/{max(cw)} px = {ratio}, needs >= {need} "
                "(the umbrella state must read from the shape alone)"], ratio
    return [], ratio


def same_value(ini_val, want):
    """True when want is None (not decided yet) or the ini value equals it (numbers compared as numbers)."""
    if want is None:
        return True
    try:
        return float(ini_val) == float(want)
    except (TypeError, ValueError):
        return ini_val.strip().lower() == str(want).lower()


def style_value(style, path):
    """unreal_import value at a dotted path, e.g. "texture.lod_group". None when missing."""
    v = style["unreal_import"]
    for part in path.split("."):
        v = v.get(part) if isinstance(v, dict) else None
    return v


def check_config(folder, style):
    """Config/*.ini against style.json unreal_import.config. Returns a list of failures."""
    fails = []
    for fname, sections in style["unreal_import"]["config"].items():
        path = os.path.join(folder, fname)
        cp = configparser.ConfigParser(strict=False, interpolation=None)
        cp.optionxform = str
        try:
            with open(path, encoding="utf-8") as fh:
                cp.read_string("".join(ln for ln in fh if not ln.lstrip().startswith(";")))
        except OSError:
            fails.append(f"config: {fname} missing")
            continue
        for section, keys in sections.items():
            sec = section.strip("[]")
            for key, rule in keys.items():
                val = cp.get(sec, key, fallback=None) if cp.has_section(sec) else None
                if val is None:
                    fails.append(f"config: {fname} {section} has no {key}")
                elif "equals_style" in rule and not same_value(val, style_value(style, rule["equals_style"])):
                    fails.append(f"config: {fname} {key}={val}, needs {style_value(style, rule['equals_style'])} "
                                 f"(style.json unreal_import.{rule['equals_style']})")
                elif "equals" in rule and val.strip().lower() != rule["equals"].lower():
                    fails.append(f"config: {fname} {key}={val}, needs {rule['equals']}")
                elif val.strip() in rule.get("not", []):
                    fails.append(f"config: {fname} {key}={val} is not allowed")
    return fails


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("images", nargs="*")
    ap.add_argument("--style", default=DEFAULT_STYLE)
    ap.add_argument("--kind", default="silhouette")
    ap.add_argument("--grid", type=parse_wh, help="cell size of a sheet, e.g. 128x128")
    ap.add_argument("--size", type=parse_wh, help="declared frame size, e.g. 128x128")
    ap.add_argument("--frames", type=int, help="expected number of non-empty frames")
    ap.add_argument("--pow2", action="store_true", default=None, help="require power-of-two textures")
    ap.add_argument("--scan", metavar="DIR", help="check every PNG under DIR against its .sprite.json sidecar")
    ap.add_argument("--names", metavar="DIR", help="check asset names under DIR (Content/UmbrellaElla/Art)")
    ap.add_argument("--import-report", metavar="JSON", help="check an editor dump of asset import settings")
    ap.add_argument("--gate", action="store_true",
                    help="with --import-report: the dump must be art_dump.py's whole-folder dump, names verified, D13 set")
    ap.add_argument("--config", metavar="DIR", help="check Config/*.ini for the Paper2D import defaults")
    ap.add_argument("--uproject", metavar="FILE", help="check the .uproject Plugins (Paper2D on, no PaperZD)")
    ap.add_argument("--width-ratio", nargs=2, metavar=("OPEN", "CLOSED"),
                    help="umbrella open vs closed sheet: opaque width ratio >= sprite.umbrella_width_ratio_min")
    ap.add_argument("--fail-lfs-pointer", action="store_true",
                    help="with --scan: a sidecar PNG that is still a Git LFS pointer is a FAIL, not a SKIP")
    ap.add_argument("--require-dir", action="store_true",
                    help="a missing --scan/--names/--config folder or --uproject file is a FAIL")
    ap.add_argument("--sources", nargs=2, metavar=("CONTENT", "SOURCE"),
                    help="every imported asset folder has a layered source file (Content/UmbrellaElla/Art Art/Source)")
    ap.add_argument("--json", action="store_true")
    a = ap.parse_args(argv)
    try:
        with open(a.style, encoding="utf-8") as f:
            style = json.load(f)
        if a.sources:
            content, source = a.sources
            if not os.path.isdir(content):
                print(f"sprite_check: {'FAIL' if a.require_dir else 'SKIP'} no {content}/ folder")
                return 1 if a.require_dir else 0
            fails = check_sources(content, source)
            print(("PASS" if not fails else "FAIL") + f"  --sources {content} {source}  errors={len(fails)}")
            for fl in fails:
                print("  - " + fl)
            return 0 if not fails else 1
        if a.width_ratio:
            fails, ratio = check_width_ratio(a.width_ratio[0], a.width_ratio[1], style)
            if a.json:
                print(json.dumps({"pass": not fails, "check": "width-ratio", "ratio": ratio, "failures": fails}, indent=2))
            else:
                print(("PASS" if not fails else "FAIL") + f"  --width-ratio ratio={ratio} "
                      f"min={style['sprite']['umbrella_width_ratio_min']}  errors={len(fails)}")
                for fl in fails:
                    print("  - " + fl)
            return 0 if not fails else 1
        for flag, folder, fn in (("names", a.names, check_names), ("config", a.config, check_config),
                                 ("uproject", a.uproject, check_uproject),
                                 ("import-report", a.import_report, None)):
            if not folder:
                continue
            if flag == "uproject" and not os.path.isfile(folder):
                print(f"sprite_check: {'FAIL' if a.require_dir else 'SKIP'} no {folder} file")
                return 1 if a.require_dir else 0
            if flag == "uproject":
                fails = fn(folder, style)
            elif fn is None:
                with open(folder, encoding="utf-8") as fh:
                    fails = check_import_report(json.load(fh), style, gate=a.gate)
            elif not os.path.isdir(folder):
                print(f"sprite_check: {'FAIL' if a.require_dir else 'SKIP'} no {folder}/ folder")
                return 1 if a.require_dir else 0
            else:
                fails = fn(folder, style)
            if a.json:
                print(json.dumps({"pass": not fails, "check": flag, "failures": fails}, indent=2))
            else:
                print(("PASS" if not fails else "FAIL") + f"  --{flag} {folder}  errors={len(fails)}")
                for fl in fails:
                    print("  - " + fl)
                if style["unreal_import"].get("status") != "verified" and flag != "names":
                    print("  ! rule names are unverified on 5.8.4 (style.json unreal_import.status)")
            return 0 if not fails else 1
        if a.scan:
            if not os.path.isdir(a.scan):
                print(f"sprite_check: {'FAIL' if a.require_dir else 'SKIP'} no {a.scan}/ folder")
                return 1 if a.require_dir else 0
            reports, skipped = scan(a.scan, style, a.fail_lfs_pointer)
        elif a.images:
            reports, skipped = [check(a.images, style, a.kind, a.grid, a.size, a.frames, a.pow2)], []
        else:
            ap.print_usage(sys.stderr)
            return 2
    except (OSError, ValueError, KeyError, TypeError) as e:
        print(f"sprite_check: {e}", file=sys.stderr)
        return 2
    ok = all(r["pass"] for r in reports)
    if a.json:
        print(json.dumps({"pass": ok, "reports": reports, "skipped": skipped}, indent=2))
    else:
        for r in reports:
            print(("PASS" if r["pass"] else "FAIL") + f"  {' '.join(r['files'])}  kind={r['kind']} frames={len(r['frames'])}")
            for m in r["frames"]:
                if m["visible"]:
                    print(f"  {m['frame']}: fill {m['fill']} fringe {m['fringe']} halo {m['halo']} "
                          f"dark {m['dark_share']} border {m['border_visible']}")
            for fl in r["failures"]:
                print("  - " + fl)
        for p, why in skipped:
            print(f"SKIP  {p}: {why}")
        if a.scan and not reports:
            print("sprite_check: SKIP nothing to check")
    if style["sprite"].get("status") != "measured" and reports and not a.json:
        print("  ! sprite thresholds are provisional (style.json sprite.status)")
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
