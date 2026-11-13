#!/usr/bin/env python3
"""Deterministic art-direction check for IN-ENGINE screenshots (not source PNGs).

It measures a screenshot against the numbers in pipeline/art/style.json:
  on_palette    share of pixels close to an approved palette color (ΔE76 in CIELAB)
  off_style     share of strongly saturated pixels that match no approved color
  accent_area   share of pixels that are accent colors (gold / rust)
  dark_share    share of near-black silhouette pixels (L* below a cutoff)
  off_band      share of colorful pixels (chroma C* above a floor) whose hue is outside
                the allowed gold and rust bands. This catches "colorful storybook" drift.
  accents       style.json "accents" (D-new-palette-accents): the quality-bar colours (wind ash blue, the shot reds
                and yellows), each with a role, a hue and chroma band and a max share of the frame. A pixel off the
                palette that matches an accent in its band is on-palette and never off_style or off_band; the
                accents' shares (accent_<role>, accent_extra) fail past their caps.
  paper_texture share of side-by-side sampled pixel pairs (both lighter than the silhouette cutoff) whose
                L* differs by at least texture_delta_l. Painted paper varies pixel to pixel; a flat
                graybox, a flat fill or a near-uniform frame scores near 0 and fails paper_texture_min.

It is the cheap, objective half of the art gate. The LLM judge (evals/art-judge, blind X/Y against the key
art) covers what numbers cannot: shape language, mood, readability. No human approves art: `gate` below is the
whole art-direction check, and the Art Director agent regenerates or re-places until it passes.

Usage:
  python3 tools/art_check.py Saved/Screenshots/shot.png
  python3 tools/art_check.py --json shot.png
  python3 tools/art_check.py --extract reference.png   # print dominant colors to seed the palette
  python3 tools/art_check.py --measure-palette reference.png  # re-centre each named palette colour on the
    reference pixels nearest to it (within delta_e_tolerance). Prints the measured hex per name and the
    reference's own numbers, so card 0.7 can write them into style.json and set palette_status: measured.
  A provisional palette is a FAIL once the reference file exists (card 0.7 not done).
  python3 tools/art_check.py --sprite|--effect piece.png  # colour rules on the non-transparent pixels only
    (--effect: against the effect palette). Exit 0 pass, 1 a failed check, 2 an unreadable style file or image.
  python3 tools/art_check.py --swatch swatch_capture.png  # engine colour round-trip (CAM_Eval_Swatch)
    The capture shows the swatch sprite from make_art_calibration.py --swatch. Each cell's centre
    (inset by style.json swatch.inset) is averaged and compared with its palette hex. Any cell over
    swatch.delta_e_max (ΔE76) fails: fix tonemapping or post-process before judging any art.
  python3 tools/art_check.py --references [--json]   # the team's art references (pipeline/art/references.json,
    plus the images the current GDD embeds and every image under the team's art folders, Assets/ and Mockups/,
    references.json team_art): present or MISSING, then a `team art:` line with how many team images joined.
    Exit 1 while a required one is missing or a team-art image cannot be read.
  python3 tools/art_check.py --gate CAPTURE [--judge Saved/art-judge/judge-log.csv]
    The automated art gate. PASS needs all four: every required reference is present; the numeric check above
    passes on CAPTURE; the judge is calibrated (evals/art-judge/agreement.csv holds the calibration pairs of
    blind_pairwise.md for the pinned model, prompt and rubric, every row agreeing and order-stable); and the
    judge log holds the blind X/Y row `<capture stem>:target-keyart` (X = the capture, judged in both orders)
    with every rubric row true for X (`judge_rows_x` = all). Prints one `ART_GATE: PASS|FAIL ...` line.
Exit code 0 = pass, 1 = fail, 2 = usage/input error.
"""
import argparse
import colorsys
import csv
import io
import json
import math
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from png import read_png  # noqa: E402

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DEFAULT_STYLE = os.path.join(ROOT, "pipeline", "art", "style.json")
REFERENCE = os.path.join(ROOT, "pipeline", "art", "reference", "target-keyart.png")
REFERENCES = os.path.join("pipeline", "art", "references.json")
IMAGE_EXT = (".png", ".jpg", ".jpeg", ".webp")
JUDGE_DIR = os.path.join("evals", "art-judge")
JUDGE_LOG = os.path.join("Saved", "art-judge", "judge-log.csv")
JUDGE_COLS = ["date", "pair_id", "seed", "model", "prompt_version", "rubric_version", "judge_closer",
              "judge_rows_x", "judge_rows_y", "order_stable", "expected_closer", "note"]
CALIBRATION_PAIRS = 7   # evals/art-judge/blind_pairwise.md calibration table


def hex_to_rgb(h):
    h = h.lstrip("#")
    return tuple(int(h[i:i + 2], 16) for i in (0, 2, 4))


def _lin(c):
    c /= 255.0
    return c / 12.92 if c <= 0.04045 else ((c + 0.055) / 1.055) ** 2.4


def rgb_to_lab(rgb):
    r, g, b = (_lin(v) for v in rgb)
    x = (0.4124 * r + 0.3576 * g + 0.1805 * b) / 0.95047
    y = 0.2126 * r + 0.7152 * g + 0.0722 * b
    z = (0.0193 * r + 0.1192 * g + 0.9505 * b) / 1.08883

    def f(t):
        return t ** (1 / 3) if t > 0.008856 else 7.787 * t + 16 / 116

    fx, fy, fz = f(x), f(y), f(z)
    return (116 * fy - 16, 500 * (fx - fy), 200 * (fy - fz))


def delta_e(a, b):
    return ((a[0] - b[0]) ** 2 + (a[1] - b[1]) ** 2 + (a[2] - b[2]) ** 2) ** 0.5


def sample_grid(path, max_samples):
    """Rows of sampled pixels on a regular grid; None where the pixel is transparent."""
    w, h, rows = read_png(path)
    total = w * h
    step = max(1, int((total / max_samples) ** 0.5))
    grid = []
    for y in range(0, h, step):
        row = rows[y]
        grid.append([row[x][:3] if row[x][3] >= 128 else None for x in range(0, w, step)])
    return w, h, grid


def sample_pixels(path, max_samples):
    w, h, grid = sample_grid(path, max_samples)
    return w, h, [p for row in grid for p in row if p is not None]


def paper_texture(grid, dark_l, delta_l, lab_of):
    """Share of horizontally adjacent non-dark sample pairs whose lightness differs by >= delta_l."""
    pairs = varied = 0
    for row in grid:
        prev = None
        for px in row:
            cur = lab_of(px)[0] if px is not None else None
            if cur is not None and prev is not None and cur > dark_l and prev > dark_l:
                pairs += 1
                if abs(cur - prev) >= delta_l:
                    varied += 1
            prev = cur
    return varied / pairs if pairs else 0.0


def measure(path, style):
    w, h, grid = sample_grid(path, style.get("max_samples", 60000))
    pixels = [p for row in grid for p in row if p is not None]
    if not pixels:
        raise ValueError("image has no opaque pixels")
    pal = [(c["name"], c["role"], rgb_to_lab(hex_to_rgb(c["hex"]))) for c in style["palette"]]
    tol = style["delta_e_tolerance"]
    dark_l = style["dark_l_max"]
    sat_min = style["off_style_saturation_min"]
    chroma_min = style["hue_gate"]["chroma_min"]
    bands = [tuple(b) for b in style["hue_gate"]["allowed_hue_bands_deg"]]
    roles = accent_roles(style)
    extra = {r["role"]: 0 for r in roles}
    cache = {}
    on = off = accent = dark = band_out = 0
    for px in pixels:
        key = (px[0] >> 2, px[1] >> 2, px[2] >> 2)
        hit = cache.get(key)
        if hit is None:
            lab = rgb_to_lab(px)
            best_name, best_role, best_d = None, None, 1e9
            for name, role, plab in pal:
                d = delta_e(lab, plab)
                if d < best_d:
                    best_name, best_role, best_d = name, role, d
            s = colorsys.rgb_to_hsv(px[0] / 255, px[1] / 255, px[2] / 255)[1]
            chroma = (lab[1] ** 2 + lab[2] ** 2) ** 0.5
            hue = math.degrees(math.atan2(lab[2], lab[1])) % 360
            outside = chroma > chroma_min and not any(lo <= hue <= hi for lo, hi in bands)
            xrole = None if best_d <= tol else accent_role(lab, chroma, hue, roles)
            hit = (best_d <= tol, best_role, lab[0] <= dark_l, s >= sat_min and lab[0] > dark_l, outside, xrole)
            cache[key] = hit
        near, role, is_dark, is_sat, outside, xrole = hit
        if xrole:   # a capped accent in its own role: on-palette, never off_style or off_band
            on += 1
            extra[xrole] += 1
        elif outside:
            band_out += 1
        if near:
            on += 1
            if role == "accent":
                accent += 1
        elif is_sat and not xrole:
            off += 1
        if is_dark:
            dark += 1
    n = len(pixels)
    lab_cache = {}

    def lab_of(px):
        v = lab_cache.get(px)
        if v is None:
            v = lab_cache[px] = rgb_to_lab(px)
        return v

    texture = paper_texture(grid, dark_l, style["texture_delta_l"], lab_of)
    return {
        "image": path,
        "size": [w, h],
        "samples": n,
        "on_palette": round(on / n, 4),
        "off_style": round(off / n, 4),
        "accent_area": round(accent / n, 4),
        "dark_share": round(dark / n, 4),
        "off_band": round(band_out / n, 4),
        "paper_texture": round(texture, 4),
        "accent_extra": round(sum(extra.values()) / n, 4),
        **{f"accent_{r}": round(v / n, 4) for r, v in extra.items()},
    }


EFFECT_RAMPS = (   # shading ramps of the GDD SH1.0 shot colours (references.json vfx_spec.palette), light to dark
    ("gold", ("#FFF5DC", "#FFD84A", "#E9C46A", "#F5AA28", "#94611E")),
    ("red", ("#FFF5DC", "#FF7848", "#FF3658", "#8F173C")),
)
RAMP_STEPS = 4   # palette entries added between two neighbouring ramp colours


def _hex(lab_rgb):
    return "#%02x%02x%02x" % tuple(max(0, min(255, round(c))) for c in lab_rgb)


def effect_style(style):
    """style.json widened for an effect sprite: the effect palette (the brand palette, the GDD SH1.0 shot colours and
    the shading ramps between them: gold and amber shade into bronze, red into shadow red) and the hue bands of the
    accent roles. Thresholds, tolerances and accent roles are untouched; only colours an effect is allowed to carry
    are added, so teal, magenta, blue and a flat rainbow still fail. Never a loosening of a threshold."""
    st = json.loads(json.dumps(style))
    pal = st["palette"]
    seen = {c["hex"].lower() for c in pal}
    for fam, ramp in EFFECT_RAMPS:
        rgb = [hex_to_rgb(h) for h in ramp]
        for i, h in enumerate(ramp):
            if h.lower() not in seen:
                seen.add(h.lower())
                pal.append({"name": f"fx-{fam}-{i}", "role": "accent", "hex": h})
        for (a, b), (ha, hb) in zip(zip(rgb, rgb[1:]), zip(ramp, ramp[1:])):
            for k in range(1, RAMP_STEPS):
                t = k / RAMP_STEPS
                mid = _hex(tuple(a[j] + (b[j] - a[j]) * t for j in range(3)))
                if mid.lower() not in seen:
                    seen.add(mid.lower())
                    pal.append({"name": f"fx-{fam}-ramp-{ha}-{hb}-{k}", "role": "accent", "hex": mid})
    bands = [list(b) for b in st["hue_gate"]["allowed_hue_bands_deg"]]
    for r in ((st.get("accents") or {}).get("roles") or {}).values():
        for b in r["hue_bands_deg"]:
            if r.get("chroma") and r["chroma"][1] >= 30:   # the saturated shot roles; the ash-blue wind role stays out
                bands.append(list(b))
    lo = min(b[0] for b in bands)
    hi = max(b[1] for b in bands)
    st["hue_gate"]["allowed_hue_bands_deg"] = [[lo, hi]]
    return st


SPRITE_RULES = ("on_palette", "off_style", "off_band")


def measure_sprite(path, style, effect=False):
    """measure() for a sprite or an effect sheet: only the non-transparent pixels (alpha >= 128) are read, so the
    transparent ground never counts; an effect is read against the effect palette (effect_style). The frame-share
    rules (dark share, accent caps, paper texture) belong to a full frame, not a sprite."""
    st = effect_style(style) if effect else style
    return measure(path, st), st


def sprite_failures(path, style, effect=False):
    """The colour rules (on_palette, off_style, off_band) a sprite or an effect sheet fails; [] = pass."""
    m, st = measure_sprite(path, style, effect)
    return [f for f in evaluate(m, st) if f.startswith(SPRITE_RULES)]


def accent_roles(style):
    """[{role, share_max, delta_e_max, chroma, bands, labs}] from style.json accents (none: [])."""
    out = []
    for name, r in ((style.get("accents") or {}).get("roles") or {}).items():
        out.append({"role": name, "share_max": r["share_max"], "delta_e_max": r["delta_e_max"],
                    "chroma": tuple(r["chroma"]), "bands": [tuple(b) for b in r["hue_bands_deg"]],
                    "labs": [rgb_to_lab(hex_to_rgb(c["hex"])) for c in r["colours"]]})
    return out


def accent_role(lab, chroma, hue, roles):
    """The accent role a pixel belongs to: near one of the role's colours, inside its hue band and chroma range."""
    best = None
    for r in roles:
        lo, hi = r["chroma"]
        if not (lo <= chroma <= hi and any(a <= hue <= b for a, b in r["bands"])):
            continue
        d = min(delta_e(lab, x) for x in r["labs"])
        if d <= r["delta_e_max"] and (best is None or d < best[0]):
            best = (d, r["role"])
    return best[1] if best else None


def evaluate(m, style):
    t = style["thresholds"]
    fails = []
    if m["on_palette"] < t["on_palette_min"]:
        fails.append(f"on_palette {m['on_palette']} < {t['on_palette_min']} (too many colors outside the art bible)")
    if m["off_style"] > t["off_style_max"]:
        fails.append(f"off_style {m['off_style']} > {t['off_style_max']} (saturated colors the art bible does not allow)")
    if m["accent_area"] > t["accent_area_max"]:
        fails.append(f"accent_area {m['accent_area']} > {t['accent_area_max']} (gold/rust accents are meant to be rare)")
    if m["off_band"] > t["off_band_max"]:
        fails.append(f"off_band {m['off_band']} > {t['off_band_max']} (colorful pixels outside the gold and rust hue bands)")
    if m["paper_texture"] < t["paper_texture_min"]:
        fails.append(f"paper_texture {m['paper_texture']} < {t['paper_texture_min']} "
                     "(flat or near-uniform frame: no paper texture, e.g. an untextured graybox)")
    acc = style.get("accents") or {}
    if acc and m.get("accent_extra", 0) > acc["total_share_max"]:
        fails.append(f"accent_extra {m['accent_extra']} > {acc['total_share_max']} (the quality-bar accents together "
                     "are capped so the brand palette dominates; D-new-palette-accents)")
    for name, r in (acc.get("roles") or {}).items():
        v = m.get(f"accent_{name}", 0)
        if v > r["share_max"]:
            fails.append(f"accent_{name} {v} > {r['share_max']} (the {name} accent is capped: {r['what']})")
    if not (t["dark_share_min"] <= m["dark_share"] <= t["dark_share_max"]):
        fails.append(
            f"dark_share {m['dark_share']} outside [{t['dark_share_min']}, {t['dark_share_max']}] "
            "(black silhouettes missing or the frame is crushed to black)")
    return fails


def extract(path, k=8):
    """Dominant colors by coarse quantization. Seeds style.json from the real reference."""
    _, _, pixels = sample_pixels(path, 80000)
    buckets = {}
    for r, g, b in pixels:
        key = (r >> 4, g >> 4, b >> 4)
        acc = buckets.setdefault(key, [0, 0, 0, 0])
        acc[0] += r
        acc[1] += g
        acc[2] += b
        acc[3] += 1
    top = sorted(buckets.values(), key=lambda a: -a[3])[:k]
    n = len(pixels)
    return [{"hex": "#%02x%02x%02x" % (a[0] // a[3], a[1] // a[3], a[2] // a[3]), "share": round(a[3] / n, 4)} for a in top]


def measure_palette(path, style, min_share=0.0005):
    """Each palette entry's mean colour over the reference pixels whose nearest entry it is (within
    delta_e_tolerance). Entries with less than min_share of the pixels keep their hex and get found=False."""
    _, _, pixels = sample_pixels(path, style.get("max_samples", 60000))
    if not pixels:
        raise ValueError("image has no opaque pixels")
    pal = [(c, rgb_to_lab(hex_to_rgb(c["hex"]))) for c in style["palette"]]
    tol = style["delta_e_tolerance"]
    sums = {c["name"]: [0, 0, 0, 0] for c, _ in pal}
    cache = {}
    for px in pixels:
        key = tuple(px)
        name = cache.get(key, "")
        if name == "":
            lab = rgb_to_lab(px)
            d, i = min((delta_e(lab, plab), i) for i, (_, plab) in enumerate(pal))
            name = cache[key] = pal[i][0]["name"] if d <= tol else None
        if name:
            acc = sums[name]
            for i in range(3):
                acc[i] += px[i]
            acc[3] += 1
    out = []
    for c, plab in pal:
        acc = sums[c["name"]]
        share = acc[3] / len(pixels)
        found = share >= min_share
        hx = "#%02x%02x%02x" % tuple(round(acc[i] / acc[3]) for i in range(3)) if found else c["hex"]
        out.append({"name": c["name"], "role": c["role"], "was": c["hex"], "hex": hx, "share": round(share, 4),
                    "shift_delta_e": round(delta_e(plab, rgb_to_lab(hex_to_rgb(hx))), 2), "found": found})
    return out


def provisional_failure(style, reference):
    """A FAIL line when the palette is still the by-eye guess although the reference is in the repo."""
    if style.get("palette_status") != "measured" and os.path.isfile(reference):
        try:
            shown = os.path.relpath(reference, ROOT)
        except ValueError:   # Windows: the reference is on another drive than the repo
            shown = os.path.abspath(reference)
        return [f"palette: style.json palette_status is {style.get('palette_status')!r} but {shown} "
                "exists; run card 0.7 (--measure-palette) before any verdict counts"]
    return []


# ---------- the team's art references and the automated art gate ----------
GDD_IMAGE = re.compile(r"!\[[^\]]*\]\(\s*<?([^)\s>]+)>?(?:\s+\"[^\"]*\")?\s*\)|<img\b[^>]*\bsrc=[\"']([^\"']+)[\"']", re.I)


GDD_ENV = "JAM_GDD"   # tools/journal.py GDD_ENV: the GDD a run picked with kickoff --gdd (tools/gdd_select.py)


def gdd_embedded(root, spec, gdd=None, env=None):
    """Images the current GDD embeds, as repo-relative paths. The GDD is `gdd` when given, else the file $JAM_GDD names
    (kickoff --gdd, tools/gdd_select.py: a run-scoped pick), else the one docs/gdd/CURRENT names."""
    env = os.environ if env is None else env
    try:
        if gdd is None and env.get(GDD_ENV):
            gdd = env[GDD_ENV]
        if gdd is None:
            with open(os.path.join(root, spec.get("from", "docs/gdd/CURRENT")), encoding="utf-8") as fh:
                name = fh.read().strip()
            gdd = os.path.join(root, "docs", "gdd", name)
        elif not os.path.isabs(gdd):
            gdd = os.path.join(root, gdd)
        with open(gdd, encoding="utf-8") as fh:
            text = fh.read()
    except OSError:
        return []
    out = []
    for m in GDD_IMAGE.finditer(text):
        ref = (m.group(1) or m.group(2) or "").strip()
        if not ref or re.match(r"[a-z]+:", ref, re.I) or not ref.lower().endswith(IMAGE_EXT):
            continue
        rel = os.path.relpath(os.path.realpath(os.path.join(os.path.dirname(gdd), ref)),
                              os.path.realpath(root)).replace(os.sep, "/")   # $JAM_GDD is a real path
        if rel not in out:
            out.append(rel)
    return out


LFS_POINTER = re.compile(rb"^version https://git-lfs\.github\.com/spec/v1\s*\noid sha256:([0-9a-f]{64})\s*\nsize (\d+)")
TEAM_ART = "team art"   # source / auto marker of an image joined from the team's art folders


def lfs_pointer(path):
    """(oid, size) when the file is a Git LFS pointer (a checkout without `git lfs pull`, like the CI runner), else
    None."""
    try:
        with open(path, "rb") as fh:
            head = fh.read(200)
    except OSError:
        return None
    m = LFS_POINTER.match(head)
    return (m.group(1).decode(), int(m.group(2))) if m else None


def image_problem(path):
    """Why a team-art image cannot be read as the picture its extension says, or None. A Git LFS pointer is fine
    here (it counts as present, like any listed reference on a pointer checkout). Cheap: signature and framing only
    (PNG: signature, IHDR with a size, IEND at the end; JPEG: start-of-image marker; WebP: RIFF/WEBP with the RIFF
    size matching the file)."""
    ext = os.path.splitext(path)[1].lower()
    try:
        size = os.path.getsize(path)
        with open(path, "rb") as fh:
            head = fh.read(32)
            fh.seek(max(0, size - 12))
            tail = fh.read(12)
    except OSError as e:
        return f"cannot open it ({e.strerror or e})"
    if size == 0:
        return "the file is empty"
    if lfs_pointer(path):
        return None
    if ext == ".png":
        if head[:8] != b"\x89PNG\r\n\x1a\n" or head[12:16] != b"IHDR":
            return "not a PNG (no PNG signature and IHDR)"
        w, h = int.from_bytes(head[16:20], "big"), int.from_bytes(head[20:24], "big")
        if not w or not h:
            return "a PNG with zero width or height"
        if tail[4:8] != b"IEND":
            return "a truncated PNG (no IEND chunk at the end)"
        return None
    if ext in (".jpg", ".jpeg"):
        return None if head[:3] == b"\xff\xd8\xff" else "not a JPEG (no start-of-image marker)"
    if ext == ".webp":
        if head[:4] != b"RIFF" or head[8:12] != b"WEBP":
            return "not a WebP (no RIFF/WEBP header)"
        return None if int.from_bytes(head[4:8], "little") + 8 <= size else "a truncated WebP (shorter than its RIFF size)"
    return "not an image type the art tools read"


def _content_key(path):
    """(size, digest) of a file's content; a Git LFS pointer gives the size and sha256 its object has, so a pointer
    and the real file compare equal. None when unreadable."""
    ptr = lfs_pointer(path)
    if ptr:
        return ptr[1], ptr[0]
    try:
        import hashlib
        with open(path, "rb") as fh:
            raw = fh.read()
    except OSError:
        return None
    return len(raw), hashlib.sha256(raw).hexdigest()


def _file_size(path):
    ptr = lfs_pointer(path)
    if ptr:
        return ptr[1]
    try:
        return os.path.getsize(path)
    except OSError:
        return None


def _skip_dir(name, words):
    return name.startswith(".") or any(w in name.lower() for w in words)


def team_art_images(root, ts):
    """(images, skipped) under the team's art folders (references.json team_art.folders), repo-relative and sorted:
    every png/jpg/jpeg/webp (any case). skipped = images in a folder whose name says obsolete (team_art.skip_words)."""
    words = [w.lower() for w in ts.get("skip_words", ["obsolete"])]
    out, skipped = [], []
    for top in ts.get("folders", ["Assets", "Mockups"]):
        base = os.path.join(root, top)
        for d, dirs, fs in os.walk(base):
            rel_d = os.path.relpath(d, root).replace(os.sep, "/")
            dead = any(_skip_dir(part, words) for part in rel_d.split("/")[1:])
            dirs[:] = sorted(dirs)
            for f in sorted(fs):
                if f.startswith(".") or not f.lower().endswith(IMAGE_EXT):
                    continue
                (skipped if dead else out).append(f"{rel_d}/{f}")
    return out, skipped


def _slug(text):
    return re.sub(r"[^a-z0-9]+", "-", text.lower()).strip("-")


def load_spec(root=ROOT, path=None):
    """pipeline/art/references.json as every art tool reads it (tools/art_judge.py load_refs is this for the repo's
    own file), with two run-time changes:
    - an entry with required false whose file is not in this checkout is left out, and its id is taken out of every
      judge element, the scene and the quality bar (the team-art entries name images only some repos have);
    - a listed image whose bytes equal an earlier listed one (the same picture filed twice, under two ids) is left
      out too, and its id is taken out of every judge element, the scene and the quality bar, so no picture counts
      twice;
    - team_art: every image under the team's art folders that is not listed yet (same path, the same bytes as a
      listed file or an image joined before it, or a path team_art.same_as names as a re-encoded copy of a listed id)
      joins `references` with the team_art defaults (`auto`: "team art").
    `_team_art` records what happened: joined, described (team images with their own entry), copies (skipped as the
    same bytes as a listed file, or same_as), listed_copies (listed entries left out as byte copies), obsolete (skipped
    folders), pointers (LFS pointers), left_out (optional entries not in this checkout) and problems (an image that
    cannot be read: art_check --references, --gate and art_judge coverage fail on them)."""
    path = path or os.path.join(root, REFERENCES)
    with open(path, encoding="utf-8") as fh:
        spec = json.load(fh)
    keep, left_out = [], []
    for r in spec.get("references", []):
        p = r.get("path")
        if r.get("required") is False and r.get("kind") != "described" and p \
                and not os.path.exists(os.path.join(root, p)):
            left_out.append(r)
            continue
        keep.append(r)
    by_size, listed_copies = {}, []   # content size -> earlier listed paths; digests only where sizes match
    for r in list(keep):
        p = r.get("path")
        if r.get("kind") != "image" or not p or not os.path.isfile(os.path.join(root, p)):
            continue
        n = _file_size(os.path.join(root, p))
        k = _content_key(os.path.join(root, p)) if by_size.get(n) else None
        first = next((o for o in by_size.get(n, []) if k and _content_key(os.path.join(root, o)) == k), None)
        if first:
            keep.remove(r)
            left_out.append(r)
            listed_copies.append((p, first))
        else:
            by_size.setdefault(n, []).append(p)
    gone = {r.get("id") for r in left_out}
    if gone:
        spec["references"] = keep
        for el in list((spec.get("elements") or {}).values()) + [spec.get("scene") or {}, spec.get("quality_bar") or {}]:
            if isinstance(el.get("refs"), list):
                el["refs"] = [x for x in el["refs"] if x not in gone]
    report = {"folders": [], "joined": [], "described": [], "copies": [], "obsolete": [], "pointers": [],
              "left_out": [r["path"] for r in left_out if r["path"] not in {c[0] for c in listed_copies}],
              "listed_copies": listed_copies, "problems": []}
    spec["_team_art"] = report
    ts = spec.get("team_art")
    if not ts:
        return spec
    report["folders"] = [f for f in ts.get("folders", ["Assets", "Mockups"]) if os.path.isdir(os.path.join(root, f))]
    images, report["obsolete"] = team_art_images(root, ts)
    listed = {r["path"]: r for r in spec.get("references", []) if r.get("path")}
    ids = {r.get("id") for r in spec.get("references", [])}
    by_id = {r.get("id"): r.get("path") for r in spec.get("references", [])}
    same_as = ts.get("same_as") or {}   # path -> listed id: the same picture saved with other bytes (re-encoded)
    sizes = {}   # content size -> [listed or joined paths]; digests only where sizes match
    for p in listed:
        s = _file_size(os.path.join(root, p))
        if s is not None:
            sizes.setdefault(s, []).append(p)
    digests = {}

    def digest(p):
        if p not in digests:
            digests[p] = _content_key(os.path.join(root, p))
        return digests[p]

    for rel in images:
        full = os.path.join(root, rel)
        why = image_problem(full)
        if why:
            report["problems"].append((rel, why))
            continue
        if lfs_pointer(full):
            report["pointers"].append(rel)
        if rel in listed:
            report["described"].append(rel)
            continue
        twin = same_as.get(rel)
        if twin in by_id:
            report["copies"].append((rel, by_id[twin]))
            continue
        s = _file_size(full)
        same = next((o for o in sizes.get(s, []) if digest(o) and digest(o) == digest(rel)), None)
        if same:
            report["copies"].append((rel, same))
            continue
        sizes.setdefault(s, []).append(rel)
        rid = base = "team-" + _slug(os.path.splitext(rel)[0])
        n = 2
        while rid in ids:
            rid, n = f"{base}-{n}", n + 1
        ids.add(rid)
        folder = rel.rsplit("/", 1)[0]
        spec.setdefault("references", []).append({
            "id": rid, "path": rel, "kind": "image", "role": list(ts.get("role", [TEAM_ART])),
            "what": f"team art in {folder}/, joined automatically (no description yet): look only, gameplay comes "
                    "from the GDD",
            "cards": list(ts.get("cards", [])), "consulted_by": list(ts.get("consulted_by", [])),
            "judge": bool(ts.get("judge", True)), "required": False, "auto": TEAM_ART, "origin": rel})
        report["joined"].append(rel)
    return spec


def team_art_problems(spec):
    return [f"team art {p} cannot be read ({why}): fix or replace the file (an LFS pointer needs `git lfs pull`), "
            "or move it into a folder whose name says obsolete" for p, why in (spec.get("_team_art") or {}).get(
                "problems", [])]


def team_art_line(spec):
    """One line a human sees (kickoff --check, art_check --references): how many team-art images are on the list."""
    t = spec.get("_team_art") or {}
    if not spec.get("team_art"):
        return "team art: references.json has no team_art, so images the team adds are not joined"
    where = ", ".join(f + "/" for f in spec["team_art"].get("folders", [])) or "the team's art folders"
    on = len(t.get("joined", [])) + len(t.get("described", []))
    extra = [f"{len(t['copies'])} copies of listed files skipped" if t.get("copies") else "",
             f"{len(t['listed_copies'])} listed entries left out as byte copies of an earlier one"
             if t.get("listed_copies") else "",
             f"{len(t['obsolete'])} in obsolete folders skipped" if t.get("obsolete") else "",
             f"{len(t['pointers'])} are LFS pointers (git lfs pull)" if t.get("pointers") else "",
             f"{len(t['left_out'])} optional entries not in this checkout" if t.get("left_out") else ""]
    line = (f"team art: {on} image(s) from {where} on the art references ({len(t.get('described', []))} with their own "
            f"entry, {len(t.get('joined', []))} joined automatically)")
    line += "".join(f"; {x}" for x in extra if x)
    if t.get("problems"):
        line = f"team art: FAIL {len(t['problems'])} image(s) cannot be read ({', '.join(p for p, _ in t['problems'])}); " \
               + line.split(": ", 1)[1]
    return line


def load_references(root=ROOT):
    """[{path, role, cards, judge, required, exists, source}]: pipeline/art/references.json's pictures and data files
    (kind image and data; a kind described entry has no file) as load_spec gives them (team art joined, optional
    entries not in this checkout left out), then the images the current GDD embeds (an image already listed keeps its
    entry, and counts as present when the GDD's copy exists). cards here = the entry's cards and consulted_by. A
    team-art image that cannot be read is listed with `unreadable` (reference_problems fails it)."""
    spec = load_spec(root)
    out = []
    for r in spec.get("references", []):
        kind = r.get("kind", "image")
        if kind == "described" or not r.get("path"):
            continue
        role = r.get("role", [])
        out.append({"path": r["path"], "role": [role] if isinstance(role, str) else list(role),
                    "cards": list(dict.fromkeys(list(r.get("cards", [])) + list(r.get("consulted_by", [])))),
                    "judge": bool(r.get("judge", kind == "image" and not r.get("judge_exempt"))),
                    "required": bool(r.get("required", True)), "exists": os.path.exists(os.path.join(root, r["path"])),
                    "source": TEAM_ART if r.get("auto") == TEAM_ART else REFERENCES.replace(os.sep, "/")})
    for p, why in spec["_team_art"]["problems"]:
        out.append({"path": p, "role": list((spec.get("team_art") or {}).get("role", [TEAM_ART])), "cards": [],
                    "judge": False, "required": True, "exists": True, "source": TEAM_ART, "unreadable": why})
    emb = spec.get("gdd_embedded")
    if emb:
        by_name = {os.path.basename(r["path"]): r for r in out}
        for rel in gdd_embedded(root, emb):
            hit = next((r for r in out if r["path"] == rel), None) or by_name.get(os.path.basename(rel))
            present = os.path.exists(os.path.join(root, rel))
            if hit:
                hit["exists"] = hit["exists"] or present
                if not hit["exists"] or hit["path"] != rel:
                    hit["gdd_path"] = rel
                continue
            out.append({"path": rel, "role": list(emb.get("role", ["composition target"])),
                        "cards": list(emb.get("cards", [])), "judge": bool(emb.get("judge", True)),
                        "required": bool(emb.get("required")), "exists": present, "source": "gdd"})
    return out


def reference_files(root=ROOT):
    """Every existing reference file (folders expanded), repo-relative: what submission_check.py assets never ships."""
    out = []
    try:
        refs = load_references(root)
    except (OSError, ValueError):
        return out
    for r in refs:
        full = os.path.join(root, r["path"])
        if os.path.isdir(full):
            for d, _, fs in os.walk(full):
                out += [os.path.relpath(os.path.join(d, f), root).replace(os.sep, "/") for f in fs]
        elif os.path.isfile(full):
            out.append(r["path"])
    return sorted(set(out))


def reference_problems(refs):
    return [f"reference {r['path']} is missing ({r['source']}; role={','.join(r['role'])}): the art gate compares "
            "against the team's own art; check out the team repo's main, where it lives" for r in refs
            if r["required"] and not r["exists"]] + \
        [f"team art {r['path']} cannot be read ({r['unreadable']}): fix or replace the file (an LFS pointer needs "
         "`git lfs pull`), or move it into a folder whose name says obsolete" for r in refs if r.get("unreadable")]


def judge_pin(root=ROOT):
    """(model, prompt_version, rubric_version) from the README pin and the prompt header."""
    try:
        readme = open(os.path.join(root, JUDGE_DIR, "README.md"), encoding="utf-8").read()
        prompt = open(os.path.join(root, "tools", "art_judge_prompt.md"), encoding="utf-8").read()
    except OSError:
        return None
    m = re.search(r"^Judge pin: model `([^`]+)`", readme, re.M)
    v = re.search(r"Prompt version: `([^`]+)`\. Rubric version: `([^`]+)`", prompt)
    return (m.group(1), v.group(1), v.group(2)) if m and v else None


def judge_rows(path):
    try:
        with open(path, encoding="utf-8") as fh:
            text = fh.read()
    except OSError:
        return None
    return list(csv.DictReader(io.StringIO(text)))


def pinned(r, pin):
    return pin and (r.get("model"), r.get("prompt_version"), r.get("rubric_version")) == pin


def calibration_problems(rows, pin):
    """The judge's calibration run: blind_pairwise.md's pairs for the pin, every row agreeing and order-stable."""
    if pin is None:
        return ["judge pin unreadable (evals/art-judge/README.md 'Judge pin:', tools/art_judge_prompt.md header)"]
    if rows is None:
        return [f"no calibration record ({JUDGE_DIR}/agreement.csv)"]
    cal = [r for r in rows if (r.get("note") or "").strip() == "calibration" and pinned(r, pin)]
    out = []
    if len({r.get("pair_id") for r in cal}) < CALIBRATION_PAIRS:
        out.append(f"judge not calibrated: {len(cal)} calibration row(s) for {'/'.join(pin)}, want the "
                   f"{CALIBRATION_PAIRS} pairs of evals/art-judge/blind_pairwise.md")
    out += [f"calibration {r.get('pair_id')}: judge {r.get('judge_closer')} vs expected {r.get('expected_closer')}, "
            f"order_stable={r.get('order_stable')}" for r in cal
            if (r.get("judge_closer") or "").strip() != (r.get("expected_closer") or "").strip()
            or (r.get("order_stable") or "").strip().lower() != "yes"]
    return out


def judge_problems(capture, rows, pin):
    pair = os.path.splitext(os.path.basename(capture))[0] + ":target-keyart"
    if rows is None:
        return [f"no judge log: the blind X/Y run of {pair} (evals/art-judge/blind_pairwise.md) writes it"]
    mine = [r for r in rows if (r.get("pair_id") or "").strip() == pair and pinned(r, pin)]
    if not mine:
        return [f"no pinned judge row {pair} in the judge log"]
    r = mine[-1]
    out = []
    if (r.get("order_stable") or "").strip().lower() != "yes":
        out.append(f"{pair}: the judge flipped between the two orders (order_stable={r.get('order_stable')})")
    if (r.get("judge_rows_x") or "").strip().lower() != "all":
        out.append(f"{pair}: rubric rows false for the capture: {r.get('judge_rows_x')} (art_judge_prompt.md R1-R11)")
    return out


def gate(capture, style, root=ROOT, judge_log=None):
    """(problems, numbers) for the automated art gate on one in-engine capture."""
    probs = reference_problems(load_references(root))
    m = measure(capture, style)
    probs += [f"numeric: {f}" for f in evaluate(m, style) + provisional_failure(style, os.path.join(
        root, "pipeline", "art", "reference", "target-keyart.png"))]
    pin = judge_pin(root)
    probs += calibration_problems(judge_rows(os.path.join(root, JUDGE_DIR, "agreement.csv")), pin)
    probs += judge_problems(capture, judge_rows(judge_log or os.path.join(root, JUDGE_LOG)), pin)
    return probs, m


def swatch_cells(n, cols):
    """(col, row) of each palette entry in the swatch layout."""
    return [(i % cols, i // cols) for i in range(n)]


def measure_swatch(path, style):
    """Mean colour of each swatch cell vs its palette hex. Returns a list of per-swatch dicts."""
    sw = style["swatch"]
    w, h, rows = read_png(path)
    pal = style["palette"]
    cols = sw["cols"]
    nrows = -(-len(pal) // cols)
    x0, y0, rw, rh = sw["rect"] or (0, 0, w, h)
    cw, ch = rw / cols, rh / nrows
    out = []
    for c, (cx, cy) in zip(pal, swatch_cells(len(pal), cols)):
        ix, iy = cw * sw["inset"], ch * sw["inset"]
        xs = range(int(x0 + cx * cw + ix), int(x0 + (cx + 1) * cw - ix))
        ys = range(int(y0 + cy * ch + iy), int(y0 + (cy + 1) * ch - iy))
        px = [rows[y][x] for y in ys for x in xs if 0 <= y < h and 0 <= x < w]
        if not px:
            raise ValueError(f"swatch cell {c['name']} is outside the capture; check style.json swatch.rect")
        mean = tuple(round(sum(p[i] for p in px) / len(px)) for i in range(3))
        d = round(delta_e(rgb_to_lab(mean), rgb_to_lab(hex_to_rgb(c["hex"]))), 2)
        out.append({"name": c["name"], "hex": c["hex"], "seen": "#%02x%02x%02x" % mean, "delta_e": d,
                    "pass": d <= sw["delta_e_max"]})
    return out


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("image", nargs="?")
    ap.add_argument("--style", default=DEFAULT_STYLE)
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--extract", action="store_true")
    ap.add_argument("--measure-palette", action="store_true",
                    help="image is the reference key art: print each palette name re-centred on it")
    ap.add_argument("--reference", default=REFERENCE, help=argparse.SUPPRESS)
    ap.add_argument("--sprite", action="store_true",
                    help="image is a sprite or sheet: colour rules on its non-transparent pixels only")
    ap.add_argument("--effect", action="store_true",
                    help="like --sprite, read against the effect palette (shot colours and their shading ramps)")
    ap.add_argument("--swatch", action="store_true", help="image is a CAM_Eval_Swatch capture")
    ap.add_argument("--references", action="store_true", help="list the team's art references, present or MISSING")
    ap.add_argument("--gate", action="store_true", help="the automated art gate on one in-engine capture")
    ap.add_argument("--judge", help="the judge log CSV for --gate (default Saved/art-judge/judge-log.csv)")
    ap.add_argument("--root", default=ROOT, help=argparse.SUPPRESS)
    a = ap.parse_args(argv)
    if a.references:
        try:
            refs = load_references(a.root)
        except (OSError, ValueError) as e:
            print(f"art_check: cannot read {REFERENCES}: {e}", file=sys.stderr)
            return 2
        if a.json:
            print(json.dumps(refs, indent=2))
        else:
            for r in refs:
                state = "UNREADABLE" if r.get("unreadable") else "present" if r["exists"] else "MISSING"
                print(f"{state} {r['path']}  role={','.join(r['role'])}"
                      f"{'' if r['required'] else ' (optional)'}{' (from the GDD)' if r['source'] == 'gdd' else ''}"
                      f"{' (team art, joined automatically)' if r['source'] == TEAM_ART else ''}"
                      f"{': ' + r['unreadable'] if r.get('unreadable') else ''}")
        probs = reference_problems(refs)
        out = sys.stderr if a.json else sys.stdout
        print(team_art_line(load_spec(a.root)), file=out)
        bad = sum(1 for r in refs if r.get("unreadable"))
        print(f"references: {len(refs) - len(probs)}/{len(refs)} present"
              + (f", {len(probs) - bad} required MISSING" if len(probs) > bad else "")
              + (f", {bad} team art UNREADABLE" if bad else ""), file=out)
        return 1 if probs else 0
    if not a.image:
        ap.error("an image is required (or --references)")
    if a.gate:
        try:
            with open(a.style, encoding="utf-8") as f:
                style = json.load(f)
            probs, m = gate(a.image, style, a.root, a.judge)
        except (OSError, ValueError, KeyError) as e:
            print(f"art_check: {e}", file=sys.stderr)
            return 2
        stem = os.path.splitext(os.path.basename(a.image))[0]
        if probs:
            print(f"ART_GATE: FAIL capture={a.image} problems={len(probs)}")
            for p in probs:
                print("  - " + p)
            return 1
        print(f"ART_GATE: PASS capture={a.image} numeric=PASS judge={stem}:target-keyart "
              f"refs={len(load_references(a.root))}")
        return 0
    if a.sprite or a.effect:
        try:
            with open(a.style, encoding="utf-8") as f:
                style = json.load(f)
            m, st = measure_sprite(a.image, style, a.effect)
        except (OSError, ValueError, KeyError) as e:
            print(f"art_check: {e}", file=sys.stderr)
            return 2
        fails = [f for f in evaluate(m, st) if f.startswith(SPRITE_RULES)]
        if a.json:
            print(json.dumps(dict(m, **{"pass": not fails, "failures": fails}), indent=2))
        else:
            print(("PASS" if not fails else "FAIL") + f"  {a.image}  (--{'effect' if a.effect else 'sprite'})")
            for k in SPRITE_RULES:
                print(f"  {k:12s} {m[k]}")
            for fl in fails:
                print("  - " + fl)
        return 0 if not fails else 1
    try:
        if a.extract:
            print(json.dumps(extract(a.image), indent=2))
            return 0
        with open(a.style, encoding="utf-8") as f:
            style = json.load(f)
        if a.measure_palette:
            m = measure(a.image, style)
            print(json.dumps({"palette": measure_palette(a.image, style), "reference": m}, indent=2))
            return 0
        if a.swatch:
            cells = measure_swatch(a.image, style)
            ok = all(c["pass"] for c in cells)
            if a.json:
                print(json.dumps({"pass": ok, "image": a.image, "swatches": cells}, indent=2))
            else:
                print(("PASS" if ok else "FAIL") + f"  --swatch {a.image}  max ΔE {max(c['delta_e'] for c in cells)}"
                      f" (limit {style['swatch']['delta_e_max']})")
                for c in cells:
                    print(f"  {'ok  ' if c['pass'] else 'FAIL'} {c['name']:12s} want {c['hex']} saw {c['seen']} ΔE {c['delta_e']}")
            return 0 if ok else 1
        m = measure(a.image, style)
    except (OSError, ValueError, KeyError) as e:
        print(f"art_check: {e}", file=sys.stderr)
        return 2
    fails = evaluate(m, style) + provisional_failure(style, a.reference)
    m["pass"] = not fails
    m["failures"] = fails
    if style.get("palette_status") != "measured":
        m["warning"] = "palette is provisional; run --extract on the reference key art and update style.json"
    if a.json:
        print(json.dumps(m, indent=2))
    else:
        print(("PASS" if not fails else "FAIL") + f"  {a.image}")
        for k in ("on_palette", "off_style", "off_band", "accent_area", "dark_share", "paper_texture") + tuple(
                k for k in m if k.startswith("accent_") and k != "accent_area"):
            print(f"  {k:12s} {m[k]}")
        for fl in fails:
            print("  - " + fl)
        if "warning" in m:
            print("  ! " + m["warning"])
    return 0 if not fails else 1


if __name__ == "__main__":
    sys.exit(main())
