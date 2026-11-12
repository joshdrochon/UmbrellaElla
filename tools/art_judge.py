#!/usr/bin/env python3
"""Automatic art judge (stdlib only): scores game art against the team's own reference images, so no human has to
approve a look. The references and what each one judges are in pipeline/art/references.json (references only,
never shipped: Official Rules §7(h)). art_check.py (palette, paper texture) and screen_check.py (no flat fills, no
debug draws, 16:9) run first and cannot be overridden; this judge adds what they cannot see.

  scene SHOT [--refs-root DIR ...]     a build screenshot against the key-art composition (references.json "scene"):
        owl large on the right, chest clock glowing gold inside it, Ella small on the left, a black jagged skyline
        band along the bottom, rust-red bolts, paper texture; plus a perceptual similarity to the scene references
        (16x9 luminance layout correlation and edge-orientation histogram on a downscaled frame). Prints
        `art_judge: scene PASS|FAIL score=<s> ...`, one line per miss and a FIX: line. The smoke runs it on every
        gameplay map's screenshot (tools/ue_run.py shot_checks), so the daily and kickoff do too.
  element ID CANDIDATE.png ... [--pick]  each candidate against that element's own references (Ella poses vs the
        Ella sheets, owl vs the owl refs, bolts and wand shots vs the effect refs, ...): silhouette mask overlap,
        edge-orientation histogram and palette fit on the first frame (a sheet's grid from its .sprite.json sidecar).
        --pick prints `art_judge: PICK <file> score=<s>` for the best passing candidate, or `art_judge: NONE` (exit 1:
        regenerate with tools/assetgen.py image and judge again; the same failure twice -> needs-human)
  coverage                             every reference in references.json is used by at least one judge element (or
        is judge_exempt with a reason: the pattern diagrams, the frame-grid data) and at least one card (a
        pipeline/day0-cards.md card, whose Done-when then runs art_judge.py, or an MVP item), and every element names
        known refs. Team art joined automatically (references.json team_art) is style context only and needs neither
        until it gets its own entry; a team-art image that cannot be read fails
Every reference is in this repo under pipeline/art/reference/ (Git LFS); --refs-root (repeatable, default this repo)
only matters for a copy elsewhere. A judge element with none of its references found FAILS: no reference is not a pass.
The per-card hard gate with the evidence line is tools/art_ref_check.py.
  calibrate [--write]                  the bar from the team's own art (Josh, 11 Nov): leave-one-out, each team image of an
        element scored against the element's other images; score_min = the lowest minus 0.02, detail_min (interior
        detail: a flat render or placeholder caps its score below any score_min) = the lowest team detail minus 0.02,
        scene similarity_min the same over the scene references. Only images under pipeline/art/reference/ count
        (the fixed set every repo has), so the numbers do not change with a repo's Assets/ studies. --write records
        every number in references.json.
The scene's layout ranges stay provisional until the first in-engine rebuild of the key art (card 0.10) is scored;
they are in references.json, so a recalibration is one reviewed edit.
Exit 0 = pass, 1 = fail, 2 = usage or unreadable input.
"""
import argparse
import json
import math
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from png import read_png  # noqa: E402

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
REFS = os.path.join(ROOT, "pipeline", "art", "references.json")
GRID_W, GRID_H = 160, 90


def refs_hash(path=REFS):
    """First 12 hex of the sha256 of references.json: the evidence line carries it (check_pr rule artref)."""
    import hashlib
    with open(path, "rb") as fh:
        return hashlib.sha256(fh.read().replace(b"\r\n", b"\n")).hexdigest()[:12]


def roles_of(r):
    """An entry's roles as a list (references.json role is a list; a bare string is read as one role)."""
    role = r.get("role") or []
    return [role] if isinstance(role, str) else list(role)


KINDS = ("image", "data", "described")


def schema_problems(refs):
    """The one references.json schema (its _about): every entry has an id, a kind, roles from `roles`, cards, and
    judge / required booleans; ids and paths are unique."""
    out = []
    vocab = set(refs.get("roles") or {})
    if not vocab:
        out.append("references.json has no roles vocabulary")
    seen_id, seen_path = set(), set()
    for r in refs.get("references", []):
        rid = r.get("id") or r.get("path") or "?"
        if not r.get("id"):
            out.append(f"reference {rid} has no id")
        elif r["id"] in seen_id:
            out.append(f"reference id {r['id']} is listed twice")
        seen_id.add(r.get("id"))
        if r.get("path"):
            if r["path"] in seen_path:
                out.append(f"reference path {r['path']} is listed twice")
            seen_path.add(r["path"])
        if r.get("kind") not in KINDS:
            out.append(f"reference {rid} has kind {r.get('kind')!r}, not one of {', '.join(KINDS)}")
        rl = roles_of(r)
        if not isinstance(r.get("role"), list) or not rl:
            out.append(f"reference {rid}: role must be a non-empty list")
        bad = [x for x in rl if vocab and x not in vocab]
        if bad:
            out.append(f"reference {rid} has role(s) {', '.join(bad)} that are not in roles")
        for k in ("judge", "required"):
            if not isinstance(r.get(k), bool):
                out.append(f"reference {rid} has no {k} true/false")
        if r.get("judge") and r.get("judge_exempt"):
            out.append(f"reference {rid} is judge_exempt but judge is true")
        if not isinstance(r.get("consulted_by", []), list):
            out.append(f"reference {rid}: consulted_by must be a list")
    return out


def card_refs(refs, card):
    return {r["id"] for r in refs["references"] if card in r.get("cards", [])}


# A Day-0 card is an art card when its lane makes or places game art or UI art
ART_LANE = re.compile(r"Art/Source/|Content/UmbrellaElla/Art/|Content/UmbrellaElla/UI/|L_StyleFrame|L_KeyArt")


def load_refs(path=REFS):
    """references.json as every art tool reads it. A repo's own pipeline/art/references.json goes through
    tools/art_check.py load_spec (the one shared loader: the team art under Assets/ and Mockups/ joined, optional
    entries not in this checkout left out); any other file (a test fixture) is read as it is."""
    full = os.path.abspath(path)
    tail = os.sep + os.path.join("pipeline", "art", "references.json")
    if full.endswith(tail):
        import art_check
        return art_check.load_spec(full[:-len(tail)] or os.sep, full)
    with open(path, encoding="utf-8") as fh:
        return json.load(fh)


def find_ref(rel, roots):
    for r in roots:
        p = os.path.join(r, rel)
        if os.path.isfile(p):
            with open(p, "rb") as fh:
                if fh.read(8) == b"\x89PNG\r\n\x1a\n":   # an LFS pointer is not the image
                    return p
    return None


def lab(rgb):
    def lin(c):
        c /= 255.0
        return c / 12.92 if c <= 0.04045 else ((c + 0.055) / 1.055) ** 2.4
    r, g, b = (lin(v) for v in rgb[:3])
    x = (0.4124 * r + 0.3576 * g + 0.1805 * b) / 0.95047
    y = 0.2126 * r + 0.7152 * g + 0.0722 * b
    z = (0.0193 * r + 0.1192 * g + 0.9505 * b) / 1.08883

    def f(t):
        return t ** (1 / 3) if t > 0.008856 else 7.787 * t + 16 / 116
    fx, fy, fz = f(x), f(y), f(z)
    return 116 * fy - 16, 500 * (fx - fy), 200 * (fy - fz)


def downscale(rows, w, h, gw, gh, box=None):
    """Block-average to gw x gh (RGBA; alpha averaged). box = (x, y, w, h) crop first."""
    x0, y0, bw, bh = box or (0, 0, w, h)
    out = []
    for gy in range(gh):
        ya, yb = y0 + gy * bh // gh, max(y0 + gy * bh // gh + 1, y0 + (gy + 1) * bh // gh)
        row = []
        for gx in range(gw):
            xa, xb = x0 + gx * bw // gw, max(x0 + gx * bw // gw + 1, x0 + (gx + 1) * bw // gw)
            acc = [0, 0, 0, 0]
            n = 0
            for y in range(ya, yb, max(1, (yb - ya) // 4)):
                r = rows[y]
                for x in range(xa, xb, max(1, (xb - xa) // 4)):
                    p = r[x]
                    for i in range(4):
                        acc[i] += p[i]
                    n += 1
            row.append(tuple(v / n for v in acc))
        out.append(row)
    return out


def classify(px, t):
    """dark | gold | rust | paper for one pixel (CIELAB thresholds from references.json scene.classes)."""
    L, a, b = lab(px)
    chroma = math.hypot(a, b)
    hue = math.degrees(math.atan2(b, a)) % 360
    if L <= t["dark_l_max"]:
        return "dark"
    if chroma >= t["accent_chroma_min"] and t["gold_hue"][0] <= hue <= t["gold_hue"][1] and L >= t["gold_l_min"]:
        return "gold"
    if chroma >= t["accent_chroma_min"] and t["rust_hue"][0] <= hue <= t["rust_hue"][1] and L < t["gold_l_min"]:
        return "rust"
    return "paper"


def components(mask, gw, gh):
    """4-connected True regions: list of (count, x0, y0, x1, y1, cells)."""
    seen = [[False] * gw for _ in range(gh)]
    out = []
    for sy in range(gh):
        for sx in range(gw):
            if not mask[sy][sx] or seen[sy][sx]:
                continue
            seen[sy][sx] = True
            stack, cells = [(sx, sy)], []
            while stack:
                x, y = stack.pop()
                cells.append((x, y))
                for nx, ny in ((x - 1, y), (x + 1, y), (x, y - 1), (x, y + 1)):
                    if 0 <= nx < gw and 0 <= ny < gh and mask[ny][nx] and not seen[ny][nx]:
                        seen[ny][nx] = True
                        stack.append((nx, ny))
            xs, ys = [c[0] for c in cells], [c[1] for c in cells]
            out.append((len(cells), min(xs), min(ys), max(xs), max(ys), cells))
    return sorted(out, key=lambda c: -c[0])


def luminance_grid(grid):
    return [[lab(p)[0] for p in row] for row in grid]


def correlation(a, b):
    fa = [v for row in a for v in row]
    fb = [v for row in b for v in row]
    ma, mb = sum(fa) / len(fa), sum(fb) / len(fb)
    num = sum((x - ma) * (y - mb) for x, y in zip(fa, fb))
    den = math.sqrt(sum((x - ma) ** 2 for x in fa) * sum((y - mb) ** 2 for y in fb))
    return num / den if den else 0.0


def edge_hist(lum, bins=8):
    """Gradient-orientation histogram weighted by magnitude, normalised (a texture and stroke-direction signature)."""
    h = [0.0] * bins
    for y in range(1, len(lum) - 1):
        for x in range(1, len(lum[0]) - 1):
            gx = lum[y][x + 1] - lum[y][x - 1]
            gy = lum[y + 1][x] - lum[y - 1][x]
            m = math.hypot(gx, gy)
            if m > 1.0:
                h[int(((math.atan2(gy, gx) + math.pi) / (2 * math.pi)) * bins) % bins] += m
    s = math.sqrt(sum(v * v for v in h)) or 1.0
    return [v / s for v in h]


def cosine(a, b):
    return sum(x * y for x, y in zip(a, b))


def measure_scene(path, t):
    w, h, rows = read_png(path)
    g = downscale(rows, w, h, GRID_W, GRID_H)
    cls = [[classify(p, t["classes"]) for p in row] for row in g]
    gw, gh = GRID_W, GRID_H
    dark = [[c == "dark" for c in row] for row in cls]
    # skyline: per column, the run of dark cells up from the bottom edge
    sky = []
    for x in range(gw):
        n = 0
        while n < gh and dark[gh - 1 - n][x]:
            n += 1
        sky.append(n)
    sky_sorted = sorted(sky)
    sky_med = sky_sorted[gw // 2] / gh
    sky_cover = sum(1 for v in sky if v > 0) / gw
    above = [[dark[y][x] and y < gh - sky[x] for x in range(gw)] for y in range(gh)]
    comps = components(above, gw, gh)
    m = {"skyline_median": round(sky_med, 3), "skyline_cover": round(sky_cover, 3)}

    def box(c):
        return {"cx": round((c[1] + c[3] + 1) / 2 / gw, 3), "cy": round((c[2] + c[4] + 1) / 2 / gh, 3),
                "w": round((c[3] - c[1] + 1) / gw, 3), "h": round((c[4] - c[2] + 1) / gh, 3), "cells": c[0]}
    right = [c for c in comps if (c[1] + c[3]) / 2 / gw >= 0.5]
    owl = right[0] if right else None
    m["owl"] = box(owl) if owl else None
    # Ella is small and thin: her cells are the darker-than-paper cells (L* <= ella_l_max) in the left part, above
    # the skyline, away from the frame edge; grown by one cell they join into one figure (umbrella, body, cape),
    # and Ella is the largest such figure
    lum = [[lab(p)[0] for p in row] for row in g]
    x_lo, x_hi = int(t["ella_x_min"] * gw), int(t["ella_x_max"] * gw)
    cand = [[x_lo <= x < x_hi and y >= int(0.08 * gh) and y < gh - sky[x] - 2
             and lum[y][x] <= t["classes"]["ella_l_max"] for x in range(gw)] for y in range(gh)]
    grown = [[any(cand[yy][xx] for yy in range(max(0, y - 1), min(gh, y + 2)) for xx in range(max(0, x - 1), min(gw, x + 2)))
              for x in range(gw)] for y in range(gh)]
    figs = [c for c in components(grown, gw, gh) if c[0] >= 6]
    if figs:
        cells = [(x, y) for x, y in figs[0][5] if cand[y][x]]
        xs, ys = [c[0] for c in cells], [c[1] for c in cells]
        m["ella"] = box((len(cells), min(xs), min(ys), max(xs), max(ys), cells))
    else:
        m["ella"] = None
    gold = [(x, y) for y in range(gh) for x in range(gw) if cls[y][x] == "gold"]
    m["gold_share"] = round(len(gold) / (gw * gh), 4)
    if owl and gold:
        inside = [p for p in gold if owl[1] <= p[0] <= owl[3] and owl[2] <= p[1] <= owl[4]]
        m["clock_in_owl"] = round(len(inside) / len(gold), 3)
    else:
        m["clock_in_owl"] = 0.0
    m["rust_share"] = round(sum(1 for row in cls for c in row if c == "rust") / (gw * gh), 4)
    small = downscale(rows, w, h, 64, 36)
    m["_lum16"] = luminance_grid(downscale(rows, w, h, 16, 9))
    m["_edges"] = edge_hist(luminance_grid(small))
    return m


def cached_ref_scene(path, t):
    """measure_scene of a reference image, cached on disk by path, size, mtime and the class thresholds: every smoke
    compares against the same references, and reading a full-size reference costs seconds."""
    import hashlib
    import tempfile
    st = os.stat(path)
    key = hashlib.sha256(json.dumps([os.path.abspath(path), st.st_size, st.st_mtime, t["classes"], t["ella_x_min"],
                                     t["ella_x_max"]], sort_keys=True).encode()).hexdigest()[:20]
    cache = os.path.join(tempfile.gettempdir(), "art_judge_cache", key + ".json")
    try:
        with open(cache, encoding="utf-8") as fh:
            return json.load(fh)
    except (OSError, ValueError):
        pass
    m = measure_scene(path, t)
    try:
        os.makedirs(os.path.dirname(cache), exist_ok=True)
        with open(cache, "w", encoding="utf-8") as fh:
            json.dump(m, fh)
    except OSError:
        pass
    return m


def scene_problems(m, t):
    out = []
    o, e = m["owl"], m["ella"]
    if not (t["skyline_median"][0] <= m["skyline_median"] <= t["skyline_median"][1]) or \
            m["skyline_cover"] < t["skyline_cover_min"]:
        out.append(("skyline", f"skyline band median {m['skyline_median']:.0%} of the frame over {m['skyline_cover']:.0%} "
                               f"of the width; want {t['skyline_median'][0]:.0%}-{t['skyline_median'][1]:.0%} across "
                               f">= {t['skyline_cover_min']:.0%} (black jagged skyline along the bottom)"))
    if not o:
        out.append(("owl", "no large dark owl mass in the right half"))
    else:
        for k in ("cx", "h", "w"):
            lo, hi = t["owl"][k]
            if not lo <= o[k] <= hi:
                out.append(("owl", f"owl {k}={o[k]} outside {lo}-{hi} (owl large, right half, wings spread)"))
    if not e:
        out.append(("ella", "no Ella silhouette in the left part of the frame"))
    else:
        for k in ("cx", "h"):
            lo, hi = t["ella"][k]
            if not lo <= e[k] <= hi:
                out.append(("ella", f"Ella {k}={e[k]} outside {lo}-{hi} (Ella small on the left)"))
    if o and e and e["h"] and o["h"] / e["h"] < t["owl_to_ella_h_min"]:
        out.append(("scale", f"owl:Ella height {o['h'] / e['h']:.1f} < {t['owl_to_ella_h_min']} (Ella small, owl huge)"))
    if m["gold_share"] < t["gold_share_min"] or m["clock_in_owl"] < t["clock_in_owl_min"]:
        out.append(("clock", f"gold share {m['gold_share']} with {m['clock_in_owl']:.0%} inside the owl; want >= "
                             f"{t['gold_share_min']} and >= {t['clock_in_owl_min']:.0%} (chest clock glowing gold)"))
    if m["rust_share"] < t["rust_share_min"]:
        out.append(("bolts", f"rust share {m['rust_share']} < {t['rust_share_min']} (red cross-shaped owl bolts)"))
    return out


FIX = {"skyline": "add or rescale the black jagged skyline layer so it spans the bottom band",
       "owl": "reposition or rescale the owl sprite (visual-only scale and offset; never the collider)",
       "ella": "place Ella small on the left at her art-bible size",
       "scale": "rescale the art so the owl dwarfs Ella",
       "clock": "the chest clock must read gold inside the owl: fix its material or regenerate it",
       "bolts": "owl bolts must be rust-red crosses: regenerate them against their references",
       "similarity": "the frame does not look like the key art: compare with pipeline/art/reference/target-keyart.png "
                     "and rebuild layout, value structure and etched texture"}


def scene(shot, refs, roots, only=None):
    """only: restrict the similarity references to these ids (a card's own references)."""
    t = refs["scene"]
    m = measure_scene(shot, t)
    probs = scene_problems(m, t)
    sims = []
    for rid in [r for r in t["refs"] if only is None or r in only]:
        p = find_ref(refs_by_id(refs)[rid]["path"], roots)
        if p:
            r = cached_ref_scene(p, t)
            sims.append((rid, round(0.5 * (correlation(m["_lum16"], r["_lum16"]) + cosine(m["_edges"], r["_edges"])), 3)))
    if not sims:
        probs.append(("similarity", "none of the scene references were found under --refs-root"))
        score = 0.0
    else:
        score = max(s for _, s in sims)
        if score < t["similarity_min"]:
            probs.append(("similarity", f"best similarity {score} < {t['similarity_min']} ("
                                        + ", ".join(f"{r}={s}" for r, s in sims) + ")"))
    return m, probs, score, sims


def refs_by_id(refs):
    return {r["id"]: r for r in refs["references"]}


# ----- element judge -----

def first_frame(path):
    w, h, rows = read_png(path)
    side = os.path.splitext(path)[0] + ".sprite.json"
    box = (0, 0, w, h)
    if os.path.isfile(side):
        try:
            with open(side, encoding="utf-8") as fh:
                d = json.load(fh)
            cw, ch = d.get("frame_w") or d.get("cell_w"), d.get("frame_h") or d.get("cell_h")
            if not cw and isinstance(d.get("size"), list):
                cw, ch = d["size"]
            if cw and ch:
                box = (int(d.get("margin", 0)), int(d.get("margin", 0)), int(cw), int(ch))
        except (OSError, ValueError, TypeError):
            pass
    return w, h, rows, box


_SIGS = {}


def signature(path, cell=None):
    """(mask 24x24 fitted to the opaque bbox, edge histogram, dark share, opaque palette pixels). Memoised per file
    state (path, size, mtime, its sidecar's mtime): the reference sheets are large and judged again and again."""
    try:
        side = os.path.splitext(path)[0] + ".sprite.json"
        st = os.stat(path)
        k = (os.path.abspath(path), st.st_size, st.st_mtime_ns, tuple(cell or ()),
             os.stat(side).st_mtime_ns if os.path.exists(side) else 0)
    except OSError:
        k = None
    if k is not None and k in _SIGS:
        return _SIGS[k]
    out = _signature(path, cell)
    if k is not None:
        _SIGS[k] = out
    return out


def _signature(path, cell=None):
    w, h, rows, box = first_frame(path)
    if cell:
        box = (0, 0, min(w, cell[0]), min(h, cell[1]))
    x0, y0, bw, bh = box
    xs, ys = [], []
    for y in range(y0, y0 + bh, max(1, bh // 96)):
        r = rows[y]
        for x in range(x0, x0 + bw, max(1, bw // 96)):
            if r[x][3] >= 128:
                xs.append(x)
                ys.append(y)
    if not xs:
        return None
    fx0, fy0, fx1, fy1 = min(xs), min(ys), max(xs) + 1, max(ys) + 1
    g = downscale(rows, w, h, 24, 24, (fx0, fy0, fx1 - fx0, fy1 - fy0))
    mask = [[p[3] >= 128 for p in row] for row in g]
    lum = [[lab(p)[0] if p[3] >= 128 else 100.0 for p in row] for row in g]
    opaque = [p for row in g for p in row if p[3] >= 128]
    dark = sum(1 for p in opaque if lab(p)[0] <= 35) / max(1, len(opaque))
    off = 0
    counts = {}
    for p in opaque:
        L, a, b = lab(p)
        hue = math.degrees(math.atan2(b, a)) % 360
        if math.hypot(a, b) > 18 and not 20 <= hue <= 95:
            off += 1   # a hue outside the gold and rust bands (art bible pillar 3)
        k = tuple(int(v) // 6 for v in p[:3])
        counts[k] = counts.get(k, 0) + 1
    flat = max(counts.values()) / len(opaque) if counts else 0.0
    return {"mask": mask, "edges": edge_hist(lum), "dark": dark, "aspect": (fx1 - fx0) / float(fy1 - fy0),
            "offband": off / max(1, len(opaque)), "flat": flat, "detail": detail(rows, box)}


def detail(rows, box, delta_l=4.0):
    """Interior detail: the share of neighbouring opaque sample pairs (about 160 samples across the frame) whose L*
    differs by >= delta_l. Painted ink-on-paper art carries texture and line work inside the silhouette; a flat
    toon render or a placeholder does not (measured 11 Nov: team Ella art 0.29-0.68, the first Blender stand-ins
    0.05-0.17). Calibrated per element from the team art: references.json elements[*].detail_min."""
    x0, y0, bw, bh = box
    step = max(1, max(bw, bh) // 160)
    pts = {}
    for y in range(y0, y0 + bh, step):
        r = rows[y]
        for x in range(x0, x0 + bw, step):
            if r[x][3] >= 200:
                pts[(x, y)] = lab(r[x])[0]
    n = big = 0
    for (x, y), L in pts.items():
        for dx, dy in ((step, 0), (0, step)):
            q = pts.get((x + dx, y + dy))
            if q is not None:
                n += 1
                big += abs(q - L) >= delta_l
    return round(big / max(1, n), 3)


def element_score(cand, ref):
    inter = sum(1 for a, b in zip(sum(cand["mask"], []), sum(ref["mask"], [])) if a and b)
    union = sum(1 for a, b in zip(sum(cand["mask"], []), sum(ref["mask"], [])) if a or b) or 1
    iou = inter / union
    edges = max(0.0, cosine(cand["edges"], ref["edges"]))
    value = 1.0 - min(1.0, abs(cand["dark"] - ref["dark"]) * 2)
    aspect = min(cand["aspect"], ref["aspect"]) / max(cand["aspect"], ref["aspect"])
    base = 0.35 * iou + 0.3 * edges + 0.2 * value + 0.15 * aspect
    # hard style gates: an off-palette hue or a flat fill caps the score below any score_min
    if cand["offband"] > 0.05 or cand["flat"] > 0.6:
        base = min(base, 0.2)
    return round(base, 3)


def element(eid, cands, refs, roots, only=None):
    el = refs["elements"].get(eid)
    if not el:
        raise ValueError(f"no judge element {eid!r} in references.json (have: {', '.join(sorted(refs['elements']))})")
    byid = refs_by_id(refs)
    sigs, missing = [], []
    for rid in [r for r in el["refs"] if (only is None or r in only) and byid[r].get("kind") != "described"]:
        ref = byid[rid]
        p = find_ref(ref["path"], roots)
        if p is None:
            missing.append(ref["path"])
            continue
        s = signature(p, ref.get("cell"))
        if s:
            sigs.append((rid, s))
    rows = []
    for c in cands:
        cs = signature(c)
        if not cs or not sigs:
            rows.append((c, 0.0, None))
            continue
        best = max(((element_score(cs, s), rid) for rid, s in sigs), key=lambda x: x[0])
        score = best[0]
        if cs["detail"] < float(el.get("detail_min", 0.0)):
            score = min(score, 0.2)   # flat inside: below the team art's measured detail floor, below any score_min
        rows.append((c, score, best[1]))
    return el, rows, missing


# ----- calibration from the team's own art -----
MARGIN = 0.02


CALIBRATION_SET = "pipeline/art/reference/"


def calibrated_ref(ref):
    """In the fixed calibration set: an image that ships with the pipeline (under pipeline/art/reference/, Git LFS),
    the same in every repo. Team-repo images (Assets/, Mockups/, required false, team_art) are look and context
    references only: present or not, they never change a stored minimum."""
    return ref.get("kind") == "image" and (ref.get("path") or "").startswith(CALIBRATION_SET)


def calibrate(refs, roots, margin=MARGIN):
    """Leave-one-out on the team's own images (Josh, 11 Nov): for each judge element, each team image (not the
    quality bar) is scored against the element's other images; score_min = the lowest of those scores minus margin.
    detail_min = the lowest team image's interior detail minus margin. scene similarity_min the same over the scene
    references. An element with one team image and nothing else to compare keeps its score_min (not measurable).
    Only the fixed calibration set counts (calibrated_ref: pipeline/art/reference/), so the stored numbers are the
    same in every repo whether or not its Assets/ studies are checked out (CI, PipelineTesting PR #12)."""
    byid = refs_by_id(refs)
    bar = set((refs.get("quality_bar") or {}).get("refs") or [])
    out = {}
    for eid, el in refs["elements"].items():
        ids = [r for r in el["refs"] if calibrated_ref(byid[r]) and find_ref(byid[r]["path"], roots)]
        sigs = {r: signature(find_ref(byid[r]["path"], roots), byid[r].get("cell")) for r in ids}
        team = [r for r in ids if r not in bar and sigs[r]]
        loo = {}
        for r in team:
            others = [sigs[o] for o in ids if o != r and sigs[o]]
            if others:
                loo[r] = max(element_score(sigs[r], s) for s in others)
        det = {r: sigs[r]["detail"] for r in team}
        out[eid] = {"loo": loo, "detail": det,
                    "score_min": round(min(loo.values()) - margin, 3) if loo else None,
                    "detail_min": round(max(0.0, min(det.values()) - margin), 3) if det else None}
    t = refs["scene"]
    sc = {}
    fixed = [r for r in t["refs"] if calibrated_ref(byid[r])]
    for rid in fixed:
        p = find_ref(byid[rid]["path"], roots)
        others = [r for r in fixed if r != rid]
        if p and others:
            _, _, s, _ = scene(p, refs, roots, set(others))
            sc[rid] = s
    out["scene"] = {"loo": sc, "similarity_min": round(min(sc.values()) - margin, 3) if sc else None}
    return out


def write_calibration(path, cal, margin=MARGIN, when=None):
    """Write the measured numbers into references.json (elements' score_min/detail_min, scene similarity_min, and a
    `calibration` block with every leave-one-out score), keeping the file's layout."""
    import datetime
    with open(path, encoding="utf-8") as fh:
        spec = json.load(fh)
    when = when or datetime.date.today().isoformat()
    for eid, c in cal.items():
        if eid == "scene":
            if c["similarity_min"] is not None:
                spec["scene"]["similarity_min"] = c["similarity_min"]
            spec["scene"]["calibration"] = {"method": "leave-one-out on the scene references", "margin": margin,
                                            "measured": when, "loo": c["loo"]}
            continue
        el = spec["elements"][eid]
        if c["score_min"] is not None:
            el["score_min"] = c["score_min"]
        if c["detail_min"] is not None:
            el["detail_min"] = c["detail_min"]
        el["calibration"] = {"method": "leave-one-out on the team images under pipeline/art/reference/ (quality bar and Assets/ studies excluded)", "margin": margin,
                             "measured": when, "loo": c["loo"], "detail": c["detail"]}
        if c["score_min"] is None:
            el["calibration"]["note"] = "one team image and nothing to compare it with: score_min not measurable"
    with open(path, "w", encoding="utf-8") as fh:
        json.dump(spec, fh, indent=1, ensure_ascii=False)
        fh.write("\n")


def coverage(refs, root=ROOT):
    """Problems: a reference no judge element or no card uses; an element or card naming an unknown reference."""
    out = schema_problems(refs)
    ids = {r["id"] for r in refs["references"]}
    used = {rid for el in refs["elements"].values() for rid in el["refs"]} | set(refs["scene"]["refs"])
    for name, el in list(refs["elements"].items()) + [("scene", refs["scene"])]:
        for rid in el["refs"]:
            if rid not in ids:
                out.append(f"judge element {name} names unknown reference {rid}")
        if not el["refs"]:
            out.append(f"judge element {name} names no reference")
    cards, lanes = {}, {}
    try:
        with open(os.path.join(root, "pipeline", "day0-cards.md"), encoding="utf-8") as fh:
            for ln in fh:
                cells = [c.strip() for c in ln.strip().strip("|").split("|")]
                if len(cells) == 7 and re.fullmatch(r"0\.\d+[a-z]?", cells[0]):
                    cards[cells[0]] = cells[6]
                    lanes[cells[0]] = cells[4]
    except OSError:
        pass
    import art_check
    out += art_check.team_art_problems(refs)
    for r in refs["references"]:
        if r.get("auto"):   # joined from the team's art folders: style context only, until it gets its own entry
            continue
        if r.get("kind") == "described":
            if not r.get("description") or r.get("path"):
                out.append(f"reference {r['id']} is described: it has a description list and no image path")
            if not any(el.get("described") == r["id"] for el in refs["elements"].values()):
                out.append(f"described reference {r['id']} is no judge element's written target")
        elif not os.path.isfile(os.path.join(root, r["path"] or "")):
            out.append(f"reference {r['id']} is missing on disk: {r['path']}")
        if r["id"] not in used and not r.get("judge_exempt"):
            out.append(f"reference {r['id']} ({r['path']}) is used by no judge element (or judge_exempt with a reason)")
        if not r.get("cards"):
            out.append(f"reference {r['id']} ({r['path']}) is assigned to no card")
        for c in r.get("cards", []):
            if not (c in cards or re.fullmatch(r"MVP \d+", c)):
                out.append(f"reference {r['id']} names card {c!r}, which is not a Day-0 card or an MVP item")
            elif c in cards and r.get("kind") == "image" and not r.get("judge_exempt") \
                    and "art_ref_check.py" not in cards[c]:
                out.append(f"reference {r['id']} names card {c}, whose Done-when does not run tools/art_ref_check.py")
    qb = refs.get("quality_bar") or {}
    qids = set(qb.get("refs") or [])
    for r in refs["references"]:
        if ("quality bar" in roles_of(r)) != (r["id"] in qids):
            out.append(f"reference {r['id']}: role 'quality bar' and quality_bar.refs disagree")
    if not qids:
        out.append("references.json has no quality_bar: every art-loop round is also judged against the top bar")
    for name in list(refs["elements"]) + ["scene"]:
        if (qb.get("by_piece") or {}).get(name, qb.get("default")) not in qids:
            out.append(f"piece {name} has no quality-bar image to be judged against")
    exempt = refs.get("not_art_cards", {})
    for c, lane in sorted(lanes.items()):
        if ART_LANE.search(lane) and c not in exempt and not card_refs(refs, c):
            out.append(f"art card {c} (its lane makes or places art) has no reference assigned in references.json")
    return out


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--refs", default=REFS)
    ap.add_argument("--refs-root", action="append", default=[])
    sub = ap.add_subparsers(dest="cmd", required=True)
    s = sub.add_parser("scene")
    s.add_argument("shot")
    e = sub.add_parser("element")
    e.add_argument("id")
    e.add_argument("candidates", nargs="+")
    e.add_argument("--pick", action="store_true")
    sub.add_parser("coverage")
    c = sub.add_parser("calibrate")
    c.add_argument("--write", action="store_true", help="write the measured numbers into references.json")
    a = ap.parse_args(argv)
    roots = a.refs_root or [ROOT]
    try:
        refs = load_refs(a.refs)
        if a.cmd == "calibrate":
            cal = calibrate(refs, roots)
            for eid, cv in cal.items():
                low = min(cv["loo"].items(), key=lambda x: x[1]) if cv["loo"] else None
                if eid == "scene":
                    print(f"art_judge: calibrate scene similarity_min={cv['similarity_min']} lowest={low}")
                else:
                    print(f"art_judge: calibrate {eid} score_min={cv['score_min']} detail_min={cv['detail_min']} "
                          f"lowest={low} team={len(cv['detail'])}")
            if a.write:
                write_calibration(a.refs, cal)
                print(f"art_judge: wrote {os.path.relpath(a.refs, ROOT)}")
            return 0
        if a.cmd == "coverage":
            probs = coverage(refs)
            for p in probs:
                print("  - " + p)
            print(f"art_judge: coverage {'PASS' if not probs else 'FAIL'} references={len(refs['references'])} "
                  f"elements={len(refs['elements']) + 1} problems={len(probs)}")
            return 1 if probs else 0
        if a.cmd == "scene":
            m, probs, score, sims = scene(a.shot, refs, roots)
            o, el = m["owl"] or {}, m["ella"] or {}
            print(f"art_judge: scene {'PASS' if not probs else 'FAIL'} score={score} shot={os.path.basename(a.shot)} "
                  f"owl=cx{o.get('cx')}/h{o.get('h')} ella=cx{el.get('cx')}/h{el.get('h')} "
                  f"skyline={m['skyline_median']} gold={m['gold_share']} rust={m['rust_share']}")
            for k, msg in probs:
                print(f"  - {k}: {msg}")
            for k in dict.fromkeys(k for k, _ in probs):
                print(f"FIX: {k}: {FIX[k]}")
            return 1 if probs else 0
        el, rows, missing = element(a.id, a.candidates, refs, roots)
        for p in missing:
            print(f"  ! reference not found under --refs-root: {p}")
        if len(missing) == len(el["refs"]):
            print(f"art_judge: element {a.id} FAIL: none of its references were found (no reference is not a pass)")
            return 1
        best = None
        for c, sc, rid in rows:
            ok = sc >= el["score_min"]
            print(f"art_judge: element {a.id} {'PASS' if ok else 'FAIL'} score={sc} min={el['score_min']} "
                  f"candidate={os.path.basename(c)} closest={rid}")
            if ok and (best is None or sc > best[1]):
                best = (c, sc)
        if a.pick:
            print(f"art_judge: PICK {os.path.basename(best[0])} score={best[1]}" if best else
                  f"art_judge: NONE passed for {a.id}: regenerate with tools/assetgen.py image (prompt from the "
                  "art bible and the element's references) and judge again")
            return 0 if best else 1
        return 0 if all(sc >= el["score_min"] for _, sc, _ in rows) else 1
    except (OSError, ValueError, KeyError) as ex:
        print(f"art_judge: {ex}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    sys.exit(main())
