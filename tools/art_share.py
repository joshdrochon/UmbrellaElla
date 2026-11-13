#!/usr/bin/env python3
"""Shared-layer judging (Josh, Nov 13): a piece built on another passed piece is judged only on what it adds.

references.json elements[<piece>] may carry  "base": "<piece>",  "base_mode": "reuse" | "repaint"  and "new": "<what the
piece adds>" (the critic brief). "base_region": [x, y] (reuse only) is where the base image sits inside the derived one
(default 0,0).
  reuse    the derived piece literally contains the base's pixels (UI background, backdrop stages, gear composited on a
           shared body). reuse_check compares the base's opaque pixels with the derived image at that place. Below
           REUSE_SHARE the reuse is false: the piece does not count (the base region was altered). At or above it, the
           panel judges only the added layer.
  repaint  a new painting over the base's identity (Ella states, effect families). consistency_check scores the piece
           against the base's shipped image with art_judge.element_score (silhouette, line style, value, aspect, with the
           off-palette and flat-fill gates) and needs at least the floor measured from the base's own known-good
           references (leave-one-out minimum, less MARGIN). Pass: the panel judges only what differs. Fail: the full
           panel, as before.
Measured 13 Nov: a byte-identical or re-encoded copy matches 1.000; compositing edges and resampling stay within
REUSE_TOL on all but a few percent of edge pixels, so REUSE_SHARE 0.98 passes them while an altered 10 percent patch
(measured 0.90) fails."""
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import art_judge  # noqa: E402

REUSE_TOL = 8        # per-channel difference (of 255) that still counts as the same pixel
REUSE_SHARE = 0.98   # share of the base's opaque pixels that must match inside the derived piece
SAMPLES = 60000      # at most this many base pixels are compared
MARGIN = 0.02        # taken off the leave-one-out floor, as art_judge's calibration does
FALLBACK_FLOOR = 0.35   # a base with fewer than two known-good references: its element score_min, else this
MODES = ("reuse", "repaint")


def _pixel(rows, x, y):
    return rows[y][x]


def reuse_check(base_path, derived_path, region=(0, 0)):
    """(ok, share): share of the base's opaque pixels that sit unchanged (within REUSE_TOL) in the derived image at
    `region`. A derived image too small to hold the base, or an unreadable file, is not a reuse."""
    try:
        bw, bh, brows = art_judge.read_png(base_path)
        dw, dh, drows = art_judge.read_png(derived_path)
    except (OSError, ValueError):
        return False, 0.0
    ox, oy = int(region[0]), int(region[1])
    if ox < 0 or oy < 0 or ox + bw > dw or oy + bh > dh:
        return False, 0.0
    step = max(1, int(((bw * bh) / SAMPLES) ** 0.5))
    n = good = 0
    for y in range(0, bh, step):
        for x in range(0, bw, step):
            b = brows[y][x]
            if b[3] < 128:
                continue
            d = drows[y + oy][x + ox]
            n += 1
            if d[3] >= 128 and max(abs(b[i] - d[i]) for i in range(3)) <= REUSE_TOL:
                good += 1
    share = good / n if n else 0.0
    return share >= REUSE_SHARE, round(share, 4)


def known_good_floor(refs, base, roots):
    """The lowest score one of the base's own known-good references gets against the rest of them (leave-one-out),
    less MARGIN. This is what a genuine member of the base's family scores, so the bar is not set by hand."""
    byid = art_judge.refs_by_id(refs)
    el = (refs.get("elements") or {}).get(base) or {}
    sigs = []
    for rid in el.get("refs", []):
        r = byid.get(rid) or {}
        if r.get("kind") != "image":
            continue
        p = art_judge.find_ref(r.get("path", ""), roots)
        s = art_judge.signature(p, r.get("cell")) if p else None
        if s:
            sigs.append(s)
    if len(sigs) < 2:
        return float(el.get("score_min", FALLBACK_FLOOR))
    low = min(max(art_judge.element_score(s, o) for j, o in enumerate(sigs) if j != i) for i, s in enumerate(sigs))
    return round(low - MARGIN, 3)


def consistency_check(refs, base, base_path, derived_path, roots):
    """(ok, score, floor): the derived image against the base's shipped image."""
    floor = known_good_floor(refs, base, roots)
    try:
        c, b = art_judge.signature(derived_path), art_judge.signature(base_path)
    except (OSError, ValueError):
        return False, 0.0, floor
    if not c or not b:
        return False, 0.0, floor
    score = art_judge.element_score(c, b)
    return score >= floor, score, floor


def assess(refs, piece, derived_path, base_path, roots):
    """None for a piece with no base. Else {mode, base, ok, brief, ...}. ok False in reuse mode: the piece fails (its
    base region was altered). ok False in repaint mode: no shortcut, the full panel. brief: the added layer, set only
    when the shortcut holds."""
    el = (refs.get("elements") or {}).get(piece) or {}
    base = el.get("base")
    if not base:
        return None
    mode = el.get("base_mode") or "repaint"
    out = {"mode": mode, "base": base, "ok": False, "brief": None}
    if mode not in MODES or not base_path or not os.path.isfile(base_path):
        return out
    if mode == "reuse":
        ok, share = reuse_check(base_path, derived_path, el.get("base_region") or (0, 0))
        out.update(ok=ok, share=share)
    else:
        ok, score, floor = consistency_check(refs, base, base_path, derived_path, roots)
        out.update(ok=ok, score=score, floor=floor)
    if ok and el.get("new"):
        out["brief"] = el["new"]
    return out


def brief_what(what, new):
    """The element's description with the added layer named. No builder-side words: the critic prompt is leak-checked."""
    return f"{what}. Judge only this part, the rest repeats a piece that already passed: {new}"
