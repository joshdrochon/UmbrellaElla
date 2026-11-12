#!/usr/bin/env python3
"""Hitbox-vs-art alignment check. Stdlib only. Colliders are gameplay data; the art aligns to them.

GDD 1.3 section 7C, Fairness and calibration: "Replaced graphics must remain visually aligned with the independently
defined gameplay collider and muzzle/catch anchors. When art and gameplay geometry visibly disagree, first adjust
visual-only scale, pivot or offset. If actual hitbox or physics changes are needed for fairness, log a separate
feature/configuration change, run adjacent gameplay regressions, and obtain Richard approval. Never silently resize
collisions to an atlas or damage mask."

Two files:
  pipeline/feel/hitboxes.json     collider data (Gameplay Dev). One shape per gameplay sprite: Ella's hurtbox, bolts,
                                  the owl BODY and CLOCK targets. The player hurtbox and the bolt collider also name
                                  their tuning value ("fixed": pipeline/feel/feel.json forgiveness, the mirror of the
                                  *Tuning.h values) and must equal it. No tool writes this file; a change is a separate
                                  approved change (Richard).
  pipeline/art/visual-align.json  the art's visual-only scale and offset per entity, and the SHA-256 of the art it was
                                  aligned on. `fit` writes it. The game applies it to the sprite component only.

The check measures each sprite's alpha mask (PNG, after its visual scale and offset) against the collider:
  coverage  opaque art pixels inside the collider / all opaque art pixels
  spill     collider pixels with no opaque art under them / all collider pixels
Opaque = alpha >= "alpha_solid". Limits per role ("roles" in hitboxes.json; per entity with an override_reason):
  player  the hurtbox sits inside the art (a graze never hurts), never bigger: coverage_max < 1
  hazard  bolts: a little smaller than the art is fair
  target  owl body and clock: close to the art
With several frames, the worst frame decides. New art (a hash that differs from visual-align.json) fails until `fit`
re-aligns it, so an art swap waits for a PASS.

Commands:
  check [--root R] [--fail-lfs-pointer] [--require] [--json]   exit 1 on any misalignment, a stale or missing
        alignment, a collider that is not its tuning value, a missing sprite or a silhouette sidecar without a hitbox
  fit ID [--root R]   the lane agent's own fix when check fails (no human): searches a visual-only scale (0.5x-2x)
        and the offset that centres the art on the collider, keeps the one whose worst frame lands nearest the middle
        of the role limits, writes it to visual-align.json, and re-runs check. It never writes collider data. When no
        visual-only change reaches the limits it prints `NEEDS HUMAN: Richard hitbox change request ...` with a traced
        shape as a suggestion for Richard, and exits 3. That call is human-only: no grace default
  suggest SPRITE --role R [--frame x,y,w,h] [--inset PX] [--max-points N]   prints a polygon traced from the alpha mask,
        for a hitbox change request. Suggestion only: nothing is written
  lfs-include   comma list of the sprite paths, for `git lfs pull --include` in CI
A .sprite.json sidecar of kind "silhouette" under Art/ names its entity ("hitbox": "<id>") or says
"hitbox": "none" with a "hitbox_reason".

Exit 0 = pass (or nothing to check), 1 = fail, 2 = usage or input error, 3 = needs Richard (hitbox change request).
Last line: `hitbox_check: PASS entities=<n> ...` or `hitbox_check: FAIL <n> problem(s)`.
"""
import argparse
import hashlib
import json
import math
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, HERE)
from png import read_png  # noqa: E402

DATA = os.path.join("pipeline", "feel", "hitboxes.json")
ALIGN = os.path.join("pipeline", "art", "visual-align.json")
FEEL = os.path.join("pipeline", "feel", "feel.json")
LFS_POINTER = b"version https://git-lfs"
LFS_OID = re.compile(rb"^oid sha256:([0-9a-f]{64})\s*$", re.M)
ROLES = ("player", "hazard", "target")
FIXED_ROLES = ("player", "hazard")
FIXED_KEYS = {"player_hurtbox_cm": "box", "bolt_hitbox_radius_cm": "circle"}
FIXED_TOL_PX = 0.5
LIMIT_KEYS = ("coverage_min", "coverage_max", "spill_max")
FITTABLE = ("coverage", "spill", "art changed", "not aligned")   # failures `fit` repairs with a visual-only change
SCALES = [round(1.03 ** i, 4) for i in range(-23, 24)]          # 0.51x .. 1.97x


class InputError(Exception):
    pass


# ---------------------------------------------------------------- files
def file_sha256(path):
    """SHA-256 of the real content; for a Git LFS pointer, the oid it names (the same value)."""
    with open(path, "rb") as fh:
        data = fh.read()
    if data.startswith(LFS_POINTER):
        m = LFS_OID.search(data)
        if m:
            return m.group(1).decode()
    return hashlib.sha256(data).hexdigest()


def is_lfs_pointer(path):
    with open(path, "rb") as fh:
        return fh.read(len(LFS_POINTER)) == LFS_POINTER


def load_json(path, default=None):
    if default is not None and not os.path.exists(path):
        return default
    try:
        with open(path, encoding="utf-8") as fh:
            return json.load(fh)
    except OSError as e:
        raise InputError(f"cannot read {path}: {e}")
    except ValueError as e:
        raise InputError(f"{path} is not valid JSON: {e}")


def masks_of(path, frames, solid):
    """One 2D bool mask per frame [x, y, w, h] (None = the whole image)."""
    w, h, rows = read_png(path)
    out = []
    for fr in frames:
        x0, y0, fw, fh = fr if fr else (0, 0, w, h)
        if x0 < 0 or y0 < 0 or fw <= 0 or fh <= 0 or x0 + fw > w or y0 + fh > h:
            raise InputError(f"{path}: frame {list(fr)} is outside the {w}x{h} image")
        out.append([[rows[y][x][3] >= solid for x in range(x0, x0 + fw)] for y in range(y0, y0 + fh)])
    return out


def entity_frames(ent):
    if ent.get("frames"):
        return [tuple(f) for f in ent["frames"]]
    return [tuple(ent["frame"]) if ent.get("frame") else None]


# ---------------------------------------------------------------- shapes
def shape_problems(s):
    if not isinstance(s, dict):
        return ["shape is not an object"]
    t = s.get("type")
    need = {"box": ("x", "y", "w", "h"), "circle": ("cx", "cy", "r"),
            "capsule": ("cx", "cy", "radius", "half_height"), "polygon": ("points",)}
    if t not in need:
        return [f"shape type '{t}' is not one of box, circle, capsule, polygon"]
    miss = [k for k in need[t] if k not in s]
    if miss:
        return [f"{t} shape needs {', '.join(miss)}"]
    if t == "polygon":
        pts = s["points"]
        if not isinstance(pts, list) or len(pts) < 3 or not all(isinstance(p, list) and len(p) == 2 for p in pts):
            return ["polygon needs 3 or more [x, y] points"]
    elif t == "box" and (s["w"] <= 0 or s["h"] <= 0):
        return ["box w and h must be > 0"]
    elif t == "circle" and s["r"] <= 0:
        return ["circle r must be > 0"]
    elif t == "capsule" and (s["radius"] <= 0 or s["half_height"] < s["radius"]):
        return ["capsule needs radius > 0 and half_height >= radius"]
    return []


def shape_bounds(s):
    t = s["type"]
    if t == "box":
        return s["x"], s["y"], s["x"] + s["w"], s["y"] + s["h"]
    if t == "circle":
        return s["cx"] - s["r"], s["cy"] - s["r"], s["cx"] + s["r"], s["cy"] + s["r"]
    if t == "capsule":
        return s["cx"] - s["radius"], s["cy"] - s["half_height"], s["cx"] + s["radius"], s["cy"] + s["half_height"]
    xs = [p[0] for p in s["points"]]
    ys = [p[1] for p in s["points"]]
    return min(xs), min(ys), max(xs), max(ys)


def row_spans(s, yc):
    """Intervals [a, b) of x where the shape holds the horizontal line y = yc."""
    t = s["type"]
    if t == "box":
        return [(s["x"], s["x"] + s["w"])] if s["y"] <= yc < s["y"] + s["h"] else []
    if t == "circle":
        d = s["r"] ** 2 - (yc - s["cy"]) ** 2
        return [(s["cx"] - math.sqrt(d), s["cx"] + math.sqrt(d))] if d > 0 else []
    if t == "capsule":
        r = s["radius"]
        dy = max(0.0, abs(yc - s["cy"]) - (s["half_height"] - r))
        d = r * r - dy * dy
        return [(s["cx"] - math.sqrt(d), s["cx"] + math.sqrt(d))] if d > 0 else []
    pts = s["points"]
    xs = []
    for i in range(len(pts)):
        (x1, y1), (x2, y2) = pts[i], pts[(i + 1) % len(pts)]
        if (y1 <= yc < y2) or (y2 <= yc < y1):
            xs.append(x1 + (yc - y1) * (x2 - x1) / (y2 - y1))
    xs.sort()
    return [(xs[i], xs[i + 1]) for i in range(0, len(xs) - 1, 2)]


def measure(mask, s, scale=1.0, offset=(0.0, 0.0)):
    """(coverage, spill, opaque px) of collider s over the art mask drawn at a visual scale about the frame centre,
    then moved by offset (frame pixels)."""
    h = len(mask)
    w = len(mask[0]) if h else 0
    fcx, fcy = w / 2.0, h / 2.0
    dx, dy = offset
    opaque = hit = 0
    spans = {}
    for y, row in enumerate(mask):
        Y = (y + 0.5 - fcy) * scale + fcy + dy
        for x, v in enumerate(row):
            if not v:
                continue
            opaque += 1
            X = (x + 0.5 - fcx) * scale + fcx + dx
            key = round(Y, 3)
            if key not in spans:
                spans[key] = row_spans(s, Y)
            if any(a <= X < b for a, b in spans[key]):
                hit += 1
    bx0, by0, bx1, by1 = shape_bounds(s)
    inside = covered = 0
    for Y in range(int(math.floor(by0)) - 1, int(math.ceil(by1)) + 1):
        for a, b in row_spans(s, Y + 0.5):
            for X in range(int(math.ceil(a - 0.5)), int(math.ceil(b - 0.5))):
                inside += 1
                sx = int(math.floor((X + 0.5 - fcx - dx) / scale + fcx))
                sy = int(math.floor((Y + 0.5 - fcy - dy) / scale + fcy))
                if 0 <= sy < h and 0 <= sx < w and mask[sy][sx]:
                    covered += 1
    cov = hit / opaque if opaque else 0.0
    spill = (inside - covered) / inside if inside else 1.0
    return cov, spill, opaque


# ---------------------------------------------------------------- tuning (fixed colliders)
def fixed_problems(ent, root):
    """The player hurtbox and the bolt collider equal their tuning value. A mismatch is never fitted."""
    fx = ent.get("fixed")
    if ent.get("role") in FIXED_ROLES and not fx:
        return [f"a {ent.get('role')} collider names its tuning value (GDD 1.3 7A/7C): add \"fixed\": {{\"from\": "
                f"one of {', '.join(FIXED_KEYS)}, \"cm_per_px\": F}}"]
    if not fx:
        return []
    key, cpp = fx.get("from"), fx.get("cm_per_px")
    if key not in FIXED_KEYS or not isinstance(cpp, (int, float)) or cpp <= 0:
        return [f"fixed needs from = one of {', '.join(FIXED_KEYS)} and cm_per_px > 0"]
    v = (load_json(os.path.join(root, FEEL)).get("forgiveness") or {}).get(key)
    sh = ent.get("shape") or {}
    if FIXED_KEYS[key] == "box":
        if not isinstance(v, dict):
            return [f"{FEEL} forgiveness.{key} needs w and h"]
        want, got = (v["w"] / cpp, v["h"] / cpp), (sh.get("w"), sh.get("h"))
    else:
        if not isinstance(v, (int, float)):
            return [f"{FEEL} forgiveness.{key} must be a number"]
        want, got = (v / cpp,), (sh.get("r"),)
    if sh.get("type") != FIXED_KEYS[key] or any(g is None or abs(g - x) > FIXED_TOL_PX for g, x in zip(got, want)):
        return [f"collider is not its tuning value ({key} = {FIXED_KEYS[key]} "
                f"{' x '.join(f'{x:g}' for x in want)} px at {cpp} cm/px). Collider data changes only by a separate "
                "approved change (Richard), never by fit"]
    return []


# ---------------------------------------------------------------- check
def limits(data, ent):
    base = dict((data.get("roles") or {}).get(ent.get("role")) or {})
    for k in LIMIT_KEYS + ("inset_px",):
        if k in ent:
            base[k] = ent[k]
    return base


def entity_problems(data, ent, root):
    f = []
    if ent.get("role") not in ROLES:
        f.append(f"role '{ent.get('role')}' is not one of {', '.join(ROLES)}")
    lim = limits(data, ent)
    miss = [k for k in LIMIT_KEYS if not isinstance(lim.get(k), (int, float))]
    if miss and not f:
        f.append(f"no limit for {', '.join(miss)} (roles.{ent.get('role')} in {DATA})")
    if any(k in ent for k in LIMIT_KEYS) and not (ent.get("override_reason") or "").strip():
        f.append("a per-entity limit needs an override_reason")
    if ent.get("role") == "player" and isinstance(lim.get("coverage_max"), (int, float)) and lim["coverage_max"] >= 1:
        f.append("player coverage_max must be below 1.0: the player hurtbox is never bigger than the art")
    f += shape_problems(ent.get("shape"))
    if not f:
        f += fixed_problems(ent, root)
    return f


def frame_reports(data, ent, root, scale, offset):
    path = os.path.join(root, ent["sprite"])
    lim = limits(data, ent)
    out, fails = [], []
    for fr, mask in zip(entity_frames(ent), masks_of(path, entity_frames(ent), data.get("alpha_solid", 128))):
        cov, spill, opaque = measure(mask, ent["shape"], scale, offset)
        out.append({"frame": list(fr) if fr else None, "coverage": round(cov, 3), "spill": round(spill, 3)})
        where = f"frame {list(fr)}" if fr else "sprite"
        if not opaque:
            fails.append(f"{where}: no opaque pixel")
            continue
        if cov < lim["coverage_min"]:
            fails.append(f"{where}: coverage {cov:.3f} < {lim['coverage_min']} (the collider misses art the player sees)")
        if cov > lim["coverage_max"]:
            fails.append(f"{where}: coverage {cov:.3f} > {lim['coverage_max']} (the art is too small for this "
                         f"{ent.get('role')} collider)")
        if spill > lim["spill_max"]:
            fails.append(f"{where}: spill {spill:.3f} > {lim['spill_max']} (the collider reaches empty space)")
    return out, fails


def check_entity(data, align, ent, root, fail_lfs_pointer=False):
    """(report, skipped reason or None)."""
    eid = ent.get("id") or "?"
    rep = {"id": eid, "role": ent.get("role"), "sprite": ent.get("sprite"), "frames": [], "failures": []}
    f = rep["failures"]
    try:
        f += entity_problems(data, ent, root)
    except InputError as e:
        f.append(str(e))
    path = os.path.join(root, ent.get("sprite") or "")
    if not ent.get("sprite") or not os.path.isfile(path):
        f.append(f"sprite {ent.get('sprite')} not found")
        return rep, None
    va = align.get(eid)
    sha = file_sha256(path)
    if not va:
        f.append(f"art not aligned yet: no entry in {ALIGN}")
    elif va.get("art_sha256") != sha:
        f.append(f"art changed since it was aligned (art_sha256 {str(va.get('art_sha256'))[:12]} != file {sha[:12]}); "
                 "the art swap waits for a PASS")
    if is_lfs_pointer(path):
        if fail_lfs_pointer:
            f.append("still a Git LFS pointer, so no pixel was checked (git lfs pull first)")
            return rep, None
        return rep, "Git LFS pointer, not the image (git lfs pull)"
    if any(not any(w in x for w in FITTABLE) for x in f):
        return rep, None
    va = va or {}
    rep["frames"], fails = frame_reports(data, ent, root, va.get("scale", 1.0), tuple(va.get("offset_px", (0, 0))))
    f += fails
    return rep, None


def sidecar_problems(art_dir, ids):
    out = []
    if not art_dir or not os.path.isdir(art_dir):
        return out
    for d, _, fs in os.walk(art_dir):
        for name in sorted(fs):
            if not name.endswith(".sprite.json"):
                continue
            p = os.path.join(d, name)
            try:
                with open(p, encoding="utf-8") as fh:
                    meta = json.load(fh)
            except (OSError, ValueError):
                continue   # sprite_check.py reports a broken sidecar
            if meta.get("kind", "silhouette") != "silhouette":
                continue
            hb = meta.get("hitbox")
            if hb == "none":
                if not (meta.get("hitbox_reason") or "").strip():
                    out.append(f"{p}: hitbox none needs a hitbox_reason")
            elif not hb:
                out.append(f"{p}: a silhouette sprite names its hitbox (\"hitbox\": \"<id>\" in {DATA}, or \"none\" "
                           "with a hitbox_reason)")
            elif hb not in ids:
                out.append(f"{p}: hitbox '{hb}' is not an entity in {DATA}")
    return out


def run_check(root, fail_lfs_pointer=False, require=False):
    """(reports, skipped, problems)."""
    data = load_json(os.path.join(root, DATA))
    align = (load_json(os.path.join(root, ALIGN), {"entities": {}}).get("entities") or {})
    ents = data.get("entities") or []
    problems, reports, skipped = [], [], []
    ids = [e.get("id") for e in ents]
    for d in sorted({i for i in ids if ids.count(i) > 1}):
        problems.append(f"entity id '{d}' appears twice")
    if require and not ents:
        problems.append(f"no entities in {DATA} (--require)")
    for ent in ents:
        try:
            rep, skip = check_entity(data, align, ent, root, fail_lfs_pointer)
        except (InputError, ValueError, OSError) as e:
            rep, skip = {"id": ent.get("id"), "failures": [str(e)], "frames": []}, None
        if skip:
            skipped.append((ent.get("id"), skip))
            continue
        reports.append(rep)
        problems += [f"{rep['id']}: {x}" for x in rep["failures"]]
    problems += sidecar_problems(os.path.join(root, "Art"), set(ids))
    return reports, skipped, problems


def fix_ids(reports):
    return [r["id"] for r in reports if r["failures"] and all(any(w in f for w in FITTABLE) for f in r["failures"])]


# ---------------------------------------------------------------- fit (visual-only)
def opaque_box(mask):
    ys = [y for y, r in enumerate(mask) if any(r)]
    xs = [x for r in mask for x, v in enumerate(r) if v]
    return (min(xs), min(ys), max(xs) + 1, max(ys) + 1) if ys else None


def union(masks):
    out = [row[:] for row in masks[0]]
    for m in masks[1:]:
        if len(m) != len(out) or len(m[0]) != len(out[0]):
            raise InputError("every frame of one entity must be the same size")
        out = [[a or b for a, b in zip(r1, r2)] for r1, r2 in zip(out, m)]
    return out


def fit_visual(data, ent, root):
    """The visual-only scale and offset whose worst frame lands nearest the middle of the coverage limits, or None."""
    path = os.path.join(root, ent["sprite"])
    if is_lfs_pointer(path):
        raise InputError(f"{ent['sprite']} is a Git LFS pointer: git lfs pull --include='{ent['sprite']}' first")
    masks = masks_of(path, entity_frames(ent), data.get("alpha_solid", 128))
    box = opaque_box(union(masks))
    if not box:
        raise InputError(f"{ent['sprite']}: no opaque pixel to align")
    h, w = len(masks[0]), len(masks[0][0])
    ax, ay = (box[0] + box[2]) / 2.0, (box[1] + box[3]) / 2.0
    x0, y0, x1, y1 = shape_bounds(ent["shape"])
    cx, cy = (x0 + x1) / 2.0, (y0 + y1) / 2.0
    lim = limits(data, ent)
    mid = (lim["coverage_min"] + lim["coverage_max"]) / 2
    best = None
    for sc in SCALES:
        # the art box centre lands on the collider centre: ((ax - w/2) * sc + w/2 + dx) == cx
        off = (round(cx - ((ax - w / 2.0) * sc + w / 2.0), 2), round(cy - ((ay - h / 2.0) * sc + h / 2.0), 2))
        worst = None
        for m in masks:
            cov, spill, opq = measure(m, ent["shape"], sc, off)
            if not (opq and lim["coverage_min"] <= cov <= lim["coverage_max"] and spill <= lim["spill_max"]):
                worst = None
                break
            worst = cov if worst is None else min(worst, cov)
        if worst is not None and (best is None or abs(worst - mid) < abs(best[0] - mid)):
            best = (worst, sc, off)
    return best


# ---------------------------------------------------------------- suggest (for Richard, never applied)
def erode(mask, n):
    for _ in range(max(0, int(n))):
        h, w = len(mask), len(mask[0])
        mask = [[mask[y][x] and all(0 <= y + dy < h and 0 <= x + dx < w and mask[y + dy][x + dx]
                                    for dy in (-1, 0, 1) for dx in (-1, 0, 1))
                 for x in range(w)] for y in range(h)]
    return mask


def poly_area(pts):
    return sum(pts[i][0] * pts[(i + 1) % len(pts)][1] - pts[(i + 1) % len(pts)][0] * pts[i][1]
               for i in range(len(pts))) / 2.0


def outline(mask):
    """The largest closed boundary loop of the opaque area, as pixel-corner points (holes are filled)."""
    h = len(mask)
    w = len(mask[0]) if h else 0

    def on(x, y):
        return 0 <= x < w and 0 <= y < h and mask[y][x]
    nxt = {}
    for y in range(h):
        for x in range(w):
            if not mask[y][x]:
                continue
            if not on(x, y - 1):
                nxt.setdefault((x, y), []).append((x + 1, y))
            if not on(x + 1, y):
                nxt.setdefault((x + 1, y), []).append((x + 1, y + 1))
            if not on(x, y + 1):
                nxt.setdefault((x + 1, y + 1), []).append((x, y + 1))
            if not on(x - 1, y):
                nxt.setdefault((x, y + 1), []).append((x, y))
    loops = []
    while nxt:
        start = next(iter(nxt))
        loop, p = [start], start
        while True:
            outs = nxt.get(p)
            if not outs:
                break
            q = outs.pop()
            if not outs:
                del nxt[p]
            if q == start:
                break
            loop.append(q)
            p = q
        if len(loop) >= 4:
            loops.append(loop)
    return max(loops, key=lambda lp: abs(poly_area(lp))) if loops else []


def _seg_dist(p, a, b):
    dx, dy = b[0] - a[0], b[1] - a[1]
    if dx == dy == 0:
        return math.hypot(p[0] - a[0], p[1] - a[1])
    t = max(0.0, min(1.0, ((p[0] - a[0]) * dx + (p[1] - a[1]) * dy) / (dx * dx + dy * dy)))
    return math.hypot(p[0] - a[0] - t * dx, p[1] - a[1] - t * dy)


def _rdp(pts, eps):
    if len(pts) < 3:
        return pts
    i, d = max(((i, _seg_dist(pts[i], pts[0], pts[-1])) for i in range(1, len(pts) - 1)), key=lambda t: t[1])
    if d <= eps:
        return [pts[0], pts[-1]]
    return _rdp(pts[:i + 1], eps)[:-1] + _rdp(pts[i:], eps)


def simplify(loop, max_points):
    n = len(loop)
    pts = [loop[i] for i in range(n) if (loop[i][0] - loop[i - 1][0]) * (loop[(i + 1) % n][1] - loop[i][1])
           != (loop[i][1] - loop[i - 1][1]) * (loop[(i + 1) % n][0] - loop[i][0])] or loop
    if len(pts) <= max_points:
        return pts
    far = max(range(len(pts)), key=lambda i: math.hypot(pts[i][0] - pts[0][0], pts[i][1] - pts[0][1]))
    eps = 0.5
    while True:
        out = _rdp(pts[:far + 1], eps)[:-1] + _rdp(pts[far:] + [pts[0]], eps)[:-1]
        if len(out) <= max_points or eps > 1e4:
            return out
        eps *= 1.25


def suggest_shape(mask, inset=0, max_points=12):
    loop = outline(erode(mask, inset))
    if not loop:
        raise InputError("no opaque pixels left to trace")
    return {"type": "polygon", "points": [[int(x), int(y)] for x, y in simplify(loop, max_points)]}


def one_line(obj):
    return json.dumps(obj, separators=(", ", ": "))


def parse_frame(s):
    try:
        v = [int(x) for x in s.split(",")]
    except ValueError:
        v = []
    if len(v) != 4:
        raise InputError(f"--frame '{s}' is not x,y,w,h")
    return v


# ---------------------------------------------------------------- CLI
def print_check(reports, skipped, problems):
    for r in reports:
        for fr in r["frames"]:
            print(f"{r['id']} ({r['role']}): frame={fr['frame']} coverage={fr['coverage']} spill={fr['spill']}")
    for sid, why in skipped:
        print(f"SKIP {sid}: {why}")
    for x in problems:
        print(f"FAIL: {x}")
    for eid in fix_ids(reports):
        print(f"FIX: python3 tools/hitbox_check.py fit {eid}   (visual-only; the lane's agent runs it, then check "
              "re-runs. A human only by AGENTS.md section 6, or when fit asks for Richard)")
    if problems:
        print(f"hitbox_check: FAIL {len(problems)} problem(s)")
        return 1
    print(f"hitbox_check: PASS entities={len(reports)} skipped={len(skipped)}")
    return 0


def cmd_fit(root, eid):
    data = load_json(os.path.join(root, DATA))
    ent = next((e for e in data.get("entities") or [] if e.get("id") == eid), None)
    if not ent:
        raise InputError(f"no entity '{eid}' in {DATA}")
    bad = entity_problems(data, ent, root)
    if bad:
        for x in bad:
            print(f"FAIL: {eid}: {x}")
        print(f"hitbox_check: fit FAIL {eid}: fit only moves art; fix the collider data first (it is never fitted)")
        return 1
    best = fit_visual(data, ent, root)
    path = os.path.join(root, ent["sprite"])
    if not best:
        masks = masks_of(path, entity_frames(ent), data.get("alpha_solid", 128))
        sug = suggest_shape(union(masks), limits(data, ent).get("inset_px", 0))
        print(f"NEEDS HUMAN: Richard hitbox change request for {eid}: no visual-only scale (0.5x-2x) or offset aligns "
              f"{ent['sprite']} with its collider inside the {ent['role']} limits (GDD 1.3 7C: a hitbox change is a "
              "separate approved change with adjacent regressions). Human-only, no grace default")
        print(f"suggested collider for Richard (not applied): {one_line(sug)}")
        print(f"hitbox_check: fit STOP {eid}: label the card needs-human; or redraw or re-crop the art "
              "(tools/assetgen.py) and run check again")
        return 3
    cov, sc, off = best
    apath = os.path.join(root, ALIGN)
    align = load_json(apath, {"_about": "Visual-only scale and offset per hitbox entity (tools/hitbox_check.py fit "
                                        "writes it). The game applies them to the sprite component only, never to "
                                        "collision (GDD 1.3 7C).", "entities": {}})
    align.setdefault("entities", {})[eid] = {"art_sha256": file_sha256(path), "scale": sc, "offset_px": list(off)}
    os.makedirs(os.path.dirname(apath), exist_ok=True)
    with open(apath, "w", encoding="utf-8") as fh:
        json.dump(align, fh, indent=2, sort_keys=True)
        fh.write("\n")
    print(f"hitbox_check: fit {eid}: collider unchanged; art scale {sc}, offset {list(off)} px written to {ALIGN} "
          f"(worst coverage {cov:.3f}); re-running check")
    return print_check(*run_check(root))


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)
    c = sub.add_parser("check")
    c.add_argument("--root", default=ROOT)
    c.add_argument("--fail-lfs-pointer", action="store_true")
    c.add_argument("--require", action="store_true", help="fail when the data file has no entities")
    c.add_argument("--json", action="store_true")
    ft = sub.add_parser("fit")
    ft.add_argument("id")
    ft.add_argument("--root", default=ROOT)
    sg = sub.add_parser("suggest")
    sg.add_argument("sprite")
    sg.add_argument("--role", required=True, choices=ROLES)
    sg.add_argument("--frame", action="append", help="x,y,w,h (repeat for each animation frame)")
    sg.add_argument("--inset", type=int)
    sg.add_argument("--max-points", type=int, default=12)
    sg.add_argument("--root", default=ROOT)
    li = sub.add_parser("lfs-include")
    li.add_argument("--root", default=ROOT)
    a = ap.parse_args(argv)
    try:
        if a.cmd == "lfs-include":
            data = load_json(os.path.join(a.root, DATA))
            print(",".join(sorted({e["sprite"] for e in data.get("entities") or [] if e.get("sprite")})))
            return 0
        if a.cmd == "fit":
            return cmd_fit(a.root, a.id)
        if a.cmd == "suggest":
            path = a.sprite if os.path.isabs(a.sprite) else os.path.join(a.root, a.sprite)
            if not os.path.isfile(path):
                raise InputError(f"sprite {a.sprite} not found")
            if is_lfs_pointer(path):
                raise InputError(f"{a.sprite} is a Git LFS pointer: git lfs pull --include='{a.sprite}' first")
            data = load_json(os.path.join(a.root, DATA))
            frames = [parse_frame(f) for f in a.frame] if a.frame else [None]
            inset = a.inset if a.inset is not None else ((data.get("roles") or {}).get(a.role) or {}).get("inset_px", 0)
            sug = suggest_shape(union(masks_of(path, frames, data.get("alpha_solid", 128))), inset, a.max_points)
            print(f"suggested collider (for a hitbox change request to Richard; not applied): {one_line(sug)}")
            return 0
        reports, skipped, problems = run_check(a.root, a.fail_lfs_pointer, a.require)
    except InputError as e:
        print(f"hitbox_check: {e}")
        return 2
    if a.json:
        print(json.dumps({"reports": reports, "skipped": skipped, "problems": problems}, indent=2))
        return 1 if problems else 0
    return print_check(reports, skipped, problems)


if __name__ == "__main__":
    sys.exit(main())
