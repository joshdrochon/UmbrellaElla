#!/usr/bin/env python3
"""The art loop: art work does not stop until it reaches the bar the references set (stdlib only).

Every art card is split into its smallest judgeable pieces: one per judge element its references cover (an owl pose,
an Ella pose, each projectile, the wind zone, the skyline, the paper) plus `scene` (the full frame) when it has a
composition reference (pipeline/art/references.json). For each piece:
  1. a BUILDER session makes or revises the piece (its card's owner role);
  2. the deterministic checks run: art_check.py, screen_check.py, art_ref_check.py (the card's own references) and,
     for gameplay sprites, hitbox_check.py. A FAIL goes straight back to the builder;
  3. a separate CRITIC session with fresh context judges BLIND: our output and one of the piece's references, renamed
     X.png and Y.png in a random order, in an empty folder with a fixed prompt (critic_prompt). The critic never sees
     the builder's notes, the round number, file names, or which image is ours. It answers binary: WINNER: X, Y or
     SAME (indistinguishable in style and quality), and GAP: the single biggest thing the loser lacks. A number score
     is a refused verdict;
     Each round has two blind pairs: ours against one of the piece's references, and ours against the piece's
     quality-bar image (references.json quality_bar: the top tier, for detail and finish);
  4. the loop passes when the critic picks neither the reference nor the quality bar over ours (it picks ours, or
     SAME, in both pairs) AND every deterministic check passes. There is no round cap: the exit is reaching the bar.
Stuck rule instead of a cap (D-new-no-round-cap): when STUCK_ROUNDS (3) rounds in a row bring no improvement on both
the critic (the reference still wins, with the same gap) and the deterministic score (no new best), the piece raises
NEEDS HUMAN with the first and the
latest image and the critic's gap list. Any improvement resets the count, so a piece that keeps getting better keeps
going. Every round is logged (piece, round, verdict, gap, scores) to Saved/Logs/pipeline/art-loop.jsonl and the
SQLite journal (tools/journal.py), so progress is visible.
Evidence (tools/check_pr.py rule artloop, kickoff's art gate): a card closes only with an
`art_loop: PASS card=<id> piece=<p> verdict=<ours|same> rounds=<n> refs=<hash12> commit=<sha>` line for each of its
pieces on the current commit and references.json.

Blender art (pipeline/art/blender/; Josh, 11 Nov): the builder's revision each round is a change to the Blender
scene (the recipe, stand_ins.py or the look: model detail, materials, lines, light), rendered again with
tools/assetgen.py blender. A sprite sheet (a .sprite.json sidecar with more than one frame) is judged three ways each
round: one frame (picked by the seed) against a piece reference, one frame against the quality bar, and the whole
sheet in motion against a reference sheet (`motion` pair: identity, line weight, palette and pivot hold frame to
frame). The deterministic checks are measured here, never declared: art_ref_check.py for the piece, and for a sprite
screen_check.py's flat/grey/outline rules and art_check.py's colour rules (on_palette, off_style, off_band; the
share rules belong to the full frame, the `scene` piece). A labelled placeholder or a practice stand-in never passes.
Ship gate: a passing round writes `<file stem>.artloop.json` next to the file (sha256 of its bytes, every pair's
outcome, every check, refs=, the commit judged). tools/check_pr.py (rule artship) fails a PR that adds or changes
shipped art (an image under Art/ outside Art/Source/, or Content/*/Art|UI|VFX) without that record and a pasted
`art_loop: PASS ... file=<path> sha=<sha12> ...` line for the header commit; tools/submission_check.py art (and
assets) fails the package on any shipped image without it. No label, sign-off or human approval passes a piece:
the stuck rule asks for help, it never lowers the bar.

Stricter bar (Josh, 11 Nov): every round is judged by a PANEL of 3 fresh blind critic sessions per pair, and all
must answer ours or SAME, against EVERY reference image of the element (the scene's for `scene`), the quality-bar
image, every reference sheet in motion (a sheet) and, for an element piece, its in-engine context: the newest
capture made after the piece (the smoke's screenshot), against the key art. Each session folder hides the pair
among calibration pairs (evals/art-judge/critic-calibration.json: a crude render against team art, which must win;
a near-identical pair, SAME); a session that misses one does not count. Answers are logged in the
evals/art-judge/agreement.csv columns (Saved/Logs/pipeline/critic-calibration.csv). The numeric element judge's
score_min and detail_min, and the scene's similarity_min, are calibrated from the team's own art
(tools/art_judge.py calibrate, leave-one-out).

  pieces --card ID                          the card's pieces
  blind --card ID --piece P --ours FILE --out DIR [--seed N] [--kind reference|quality_bar|motion|context]
                                            one calibrated critic folder (lettered pairs, prompt.md); the key goes
                                            to DIR + ".key.json", outside the critic's folder
  panel --card ID --piece P --ours FILE --out DIR [--round N]   every critic folder of one round (PANEL per pair);
                                            each session's answer goes to <folder>.answer.md
  verdict --panel DIR --card ID --piece P [--checks fail]   read every answer, check calibration, unseal the keys,
                                            measure the checks, log the round, print pass|continue|stuck; a pass
                                            writes the record
  evidence --card ID                        print the art_loop PASS lines of this commit (exit 1 if a piece has none)
Exit 0 = ok / pass, 1 = not passed (continue or stuck), 2 = usage.
"""
import argparse
import csv
import datetime
import hashlib
import json
import os
import random
import re
import shutil
import subprocess
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, HERE)
import art_judge
import art_share  # noqa: E402

STUCK_ROUNDS = 3
LOG = os.path.join("Saved", "Logs", "pipeline", "art-loop.jsonl")
CRITIC_DIR = os.path.join("pipeline", "art", "critic")   # tracked: one <piece>.json of round verdicts per piece
VERDICT = re.compile(r"^\s*WINNER:\s*(X|Y|SAME)\s*$", re.M | re.I)
GAP = re.compile(r"^\s*GAP:\s*(.+)$", re.M)
NUMBER_SCORE = re.compile(r"\b\d+(?:\.\d+)?\s*/\s*10\b|\bscore\s*[:=]\s*\d", re.I)
# Words that would leak the builder's side into the critic's prompt
LEAKS = re.compile(r"\bround\b|\battempt\b|\biteration\b|\bours\b|\breference\b|\bbuilder\b|\bprevious\b|"
                   r"\bimproved?\b|\bour\b|\bgenerated\b|\bcandidate\b", re.I)

CRITIC_PROMPT = """You are a harsh art critic. Two images are in this folder: X.png and Y.png. They show the same kind of
game art piece ({what}). The style standard is ink on aged paper: near-black silhouettes, two accent families only
(gold/amber and rust red), etched lines, textured paper, never flat fills.

Compare X and Y on style and craft only. Be strict: small differences in line quality, texture, value structure,
silhouette and finish count.

Answer with exactly two lines and nothing else:
WINNER: X        (X is clearly better)
WINNER: Y        (Y is clearly better)
WINNER: SAME     (you cannot tell which is better; they are indistinguishable in style and quality)
GAP: <the single biggest thing the losing image lacks; for SAME, the one thing both still lack>

Never give a number, a score or a rating. Do not explain beyond the GAP line.
"""

# A critic session's folder (blind, calibrate=True): lettered folders A, B, C, each with X.png and Y.png. One is the
# pair being judged; the others are calibration pairs from evals/art-judge/critic-calibration.json (a crude render
# against team art: the team art must win; a crude render against a near-identical copy of itself: SAME). The
# critic cannot tell
# them apart. A session that misses any calibration pair does not count (judge(): refused, the round fails).
PANEL_PROMPT = """You are a harsh art critic. This folder holds lettered folders ({letters}). Each one holds two
images, X.png and Y.png, of game art ({what}). An image may be one frame or an animation sheet (frames left to
right, then top to bottom): judge a sheet as motion too, playing it frame after frame in a loop; the figure must keep
the same identity, proportions, line weight and colours in every frame, its anchor point must hold still, and no
frame may pop. The style standard is ink on aged paper: near-black silhouettes, two accent families only (gold/amber
and rust red), etched lines, textured paper, never flat fills.

Judge every lettered folder on its own, on style and craft only. Be strict: small differences in line quality,
texture, value structure, silhouette, finish and motion count. The two images of a folder can differ a lot: one may
be flat, blocky, blurry or a plainly cruder drawing of the same kind of thing. Look at both at full size first. When
one is clearly better crafted, name it (X or Y), even if the two show different subjects. Answer SAME only when you
truly cannot tell X and Y apart in style and quality, as when they are the same picture.

Answer with exactly one line per lettered folder and nothing else, in this form:
A: WINNER: X | GAP: <the single biggest thing the losing image lacks; for SAME, the one thing both still lack>
(WINNER is X, Y or SAME.)

Never give a number, a score or a rating.
"""
KINDS = ("reference", "quality_bar", "motion", "context")
PANEL = 3   # fresh blind critic sessions per pair per round; every one must answer ours or SAME
REDRAW_MAX = 2 * PANEL   # extra sessions drawn per pair when some do not calibrate: bounded; a vote that missed a
#                          calibration folder is never counted, so a pair that cannot reach PANEL counted votes fails
CALIBRATION = os.path.join("evals", "art-judge", "critic-calibration.json")
CAL_LOG = os.path.join("Saved", "Logs", "pipeline", "critic-calibration.csv")
AGREEMENT_COLS = ["date", "pair_id", "seed", "model", "prompt_version", "rubric_version", "judge_closer",
                  "judge_rows_x", "judge_rows_y", "order_stable", "expected_closer", "note"]
PANEL_LINE = re.compile(r"^\s*([A-H])\s*[:.)]\s*WINNER:\s*(X|Y|SAME)\b\s*(?:\|?\s*GAP:\s*(.*))?$", re.M | re.I)
SHIPPED_EXT = (".png", ".jpg", ".jpeg", ".webp", ".tga")
RECORD = ".artloop.json"   # the pass record next to a shipped file: <stem>.artloop.json
NOT_ART = ("placeholder", "source=reference (practice)")   # provenance origins that never pass
CHECKS = ("art_check", "screen_check", "art_ref_check")
LFS_OID = re.compile(rb"^version https://git-lfs\.github\.com/spec/v1\s*\noid sha256:([0-9a-f]{64})")


def refs_hash_of(root):
    return refs_and_hash(root)[1]


def refs_and_hash(root=ROOT):
    path = os.path.join(root, "pipeline", "art", "references.json")
    return art_judge.load_refs(path), art_judge.refs_hash(path)


def _bar_only(refs, el):
    """The element's look reference is a quality-bar image alone (wind-zone: bar-other-realm's ribbons, 11 Nov)."""
    bar = set((refs.get("quality_bar") or {}).get("refs") or [])
    return bool(el["refs"]) and set(el["refs"]) <= bar


def pieces(refs, card):
    """The card's judgeable pieces: each element its references cover, plus `scene` with a composition reference.
    The quality-bar images judge every piece but make none, except an element whose only reference is a quality-bar
    image: the cards that image lists make it."""
    bar = set((refs.get("quality_bar") or {}).get("refs") or [])
    allmine = art_judge.card_refs(refs, card)
    mine = allmine - bar
    out = [e for e, el in sorted(refs["elements"].items())
           if mine & set(el["refs"]) or (_bar_only(refs, el) and allmine & set(el["refs"]))]
    if mine & set(refs["scene"]["refs"]):
        out.append("scene")
    return out


def piece_refs(refs, card, piece):
    allmine = art_judge.card_refs(refs, card)
    mine = allmine - set((refs.get("quality_bar") or {}).get("refs") or [])
    el = refs["scene"] if piece == "scene" else refs["elements"][piece]
    if piece != "scene" and _bar_only(refs, el):
        mine = allmine
    byid = art_judge.refs_by_id(refs)
    return [byid[r]["path"] for r in el["refs"] if r in mine and byid[r].get("kind") == "image"]


def quality_ref(refs, piece):
    qb = refs.get("quality_bar") or {}
    rid = (qb.get("by_piece") or {}).get(piece, qb.get("default"))
    byid = art_judge.refs_by_id(refs)
    if rid not in byid:
        raise ValueError(f"piece {piece} has no quality-bar image in references.json")
    return byid[rid]["path"]


def critic_prompt(what, target=None):
    """The critic's whole prompt. It takes only the piece description and, for a piece with a written style target
    (references.json kind "described"), that target: no builder text, round or file names."""
    text = CRITIC_PROMPT.format(what=what)
    if target:
        text += "\nThe style target for this piece, in words (judge both images against it too):\n" + \
            "\n".join(f"- {t}" for t in target) + "\n"
    return text


def critic_prompt_problems(prompt, builder_text=""):
    """Why a prompt may not go to the critic: it leaks the builder's side."""
    out = []
    body = prompt.replace(CRITIC_PROMPT.split("{what}")[0], "").replace(CRITIC_PROMPT.split("{what}")[1], "")
    m = LEAKS.search(body)
    if m:
        out.append(f"the critic prompt leaks the builder's side ('{m.group(0)}')")
    for ln in (builder_text or "").splitlines():
        if len(ln.strip()) > 12 and ln.strip() in prompt:
            out.append("the critic prompt contains the builder's own text")
            break
    if re.search(r"\.png\b", prompt.replace("X.png", "").replace("Y.png", "")):
        out.append("the critic prompt names a file other than X.png and Y.png")
    return out


def sheet_info(path):
    """(frames, frame w, frame h) from the file's .sprite.json sidecar when it is a sheet of 2+ frames, else None."""
    side = os.path.splitext(path)[0] + ".sprite.json"
    try:
        with open(side, encoding="utf-8") as fh:
            s = json.load(fh)
        n = int(s.get("frames") or 0)
        fw, fh_ = (s.get("grid") or s.get("size") or [0, 0])[:2]
        return (n, int(fw), int(fh_)) if n > 1 and fw and fh_ else None
    except (OSError, ValueError, TypeError):
        return None


def frame_of(sheet, index, out):
    """Cut frame `index` of a sheet (row-major cells of its sidecar grid) to out."""
    from png import read_png, write_png
    n, fw, fh_ = sheet_info(sheet)
    w, _, rows = read_png(sheet)
    cols = max(1, w // fw)
    x, y = (index % n) % cols * fw, (index % n) // cols * fh_
    write_png(out, fw, fh_, [r[x:x + fw] for r in rows[y:y + fh_]])
    return out


def sheet_refs(refs, card, piece, root=ROOT):
    """The piece's reference sheets (entries with a `cell`), else all its references: the motion pair's other side."""
    byid = art_judge.refs_by_id(refs)
    paths = piece_refs(refs, card, piece)
    cells = [byid[r]["path"] for r in (refs["elements"].get(piece) or {}).get("refs", [])
             if r in byid and byid[r].get("cell") and byid[r].get("path") in paths]
    return cells or paths


def element_refs(refs, piece, root=ROOT):
    """Every team image the piece is judged against (the panel's `reference` pairs): the element's (or the scene's)
    image references present in this checkout, the quality bar excluded (it has its own pair)."""
    byid = art_judge.refs_by_id(refs)
    bar = set((refs.get("quality_bar") or {}).get("refs") or [])
    el = refs["scene"] if piece == "scene" else refs["elements"][piece]
    return [byid[r]["path"] for r in el["refs"] if r in byid and r not in bar and byid[r].get("kind") == "image"
            and byid[r].get("path") and any(os.path.exists(os.path.join(b, byid[r]["path"])) for b in (root, ROOT))]


def context_ref(refs, root=ROOT):
    """The composition target an in-engine capture is judged against: the key art, else the first scene reference."""
    byid = art_judge.refs_by_id(refs)
    ids = refs["scene"]["refs"]
    rid = "keyart" if "keyart" in ids else ids[0]
    return byid[rid]["path"]


def find_capture(root, ours):
    """The newest in-engine capture (the smoke's Saved/Logs/pipeline/*-shot.png or a Saved/Screenshots/ PNG) made after
    the piece's file: the piece at gameplay size in the game. None when there is none."""
    import glob
    shots = glob.glob(os.path.join(root, "Saved", "Logs", "pipeline", "*-shot.png")) + \
        glob.glob(os.path.join(root, "Saved", "Screenshots", "**", "*.png"), recursive=True)
    try:
        since = os.path.getmtime(ours)
    except OSError:
        return None
    shots = [s for s in shots if os.path.getmtime(s) >= since]
    return max(shots, key=os.path.getmtime) if shots else None


def calibration_set(root=ROOT):
    """[(crude file, elements)] from evals/art-judge/critic-calibration.json (this checkout, else the pipeline's)."""
    for base in (root, ROOT):
        p = os.path.join(base, CALIBRATION)
        if os.path.isfile(p):
            with open(p, encoding="utf-8") as fh:
                data = json.load(fh)
            out = [(os.path.join(base, c["file"]), c.get("elements", [])) for c in data.get("crude", [])]
            out = [(f, e) for f, e in out if os.path.isfile(f) and art_judge_readable(f)]
            if out:
                return out
    return []


def art_judge_readable(path):
    with open(path, "rb") as fh:
        return fh.read(8) == b"\x89PNG\r\n\x1a\n"


def near_copy(src, root):
    """A near-identical copy of an image (shifted one pixel), cached in the temp folder: a calibration pair's SAME.
    The calibration set's small renders are used, so no large team image is decoded per session."""
    import tempfile
    from png import read_png, write_png
    cache = os.path.join(tempfile.gettempdir(), "art-loop-cache")
    os.makedirs(cache, exist_ok=True)
    out = os.path.join(cache, "near-" + content_sha(src)[:16] + ".png")
    if not os.path.isfile(out):
        w, h, rows = read_png(src)
        write_png(out, w, h, [r[:1] + r[:-1] for r in rows])
    return out


def crude_of(src, root=ROOT):
    """A deliberately crude copy of a team image (coarse blocks, three flat tones per channel, no texture), cached in the
    temp folder: a calibration pair's clearly worse side for an element no crude render targets (a VFX burst: the Ella
    and owl renders show another subject, so critics answered SAME). The team image must win against it."""
    import tempfile
    from png import read_png, write_png
    cache = os.path.join(tempfile.gettempdir(), "art-loop-cache")
    os.makedirs(cache, exist_ok=True)
    out = os.path.join(cache, "crude-" + content_sha(src)[:16] + ".png")
    if not os.path.isfile(out):
        w, h, rows = read_png(src)
        cell = max(1, max(w, h) // 20)
        step = max(1, max(w, h) // 256)   # cap the work on a large image
        rows = [r[::step] for r in rows[::step]]
        w, h, cell = len(rows[0]), len(rows), max(1, cell // step)
        flat = []
        for y0 in range(0, h, cell):
            line = []
            for x0 in range(0, w, cell):
                px = [rows[y][x] for y in range(y0, min(h, y0 + cell)) for x in range(x0, min(w, x0 + cell))]
                a = sum(p[3] for p in px) // len(px)
                c = tuple(min(255, (sum(p[i] for p in px) // len(px)) // 85 * 85 + 40) for i in range(3))
                line += [c + (a,)] * min(cell, w - x0)
            flat += [line] * min(cell, h - y0)
        write_png(out, w, h, flat)
    return out


# Critic packets show images on a plain paper ground (Nov 12 critic-defect fix): a transparent sprite was shown over black,
# so its ink mass vanished and only the outline read, while the references are opaque on paper. Every image, ours and the
# reference alike, is flattened onto the same ground, so neither side gains from it.
PACKET_GROUND = (238, 229, 210)
# The game draws sprites on this paper tile (artshots, Nov 12: on a flat colour critics named a "flat, untextured ground"
# in most losses; on the tile nobody does). The flat colour stays only as the fallback when the tile is missing.
PAPER_TILE = "pipeline/art/reference/Test_Assets/SKY_StarPaper_Tile.png"
_PAPER = []


def packet_paper():
    """(w, h, rows) of the game's paper tile, or None when it is missing (read once)."""
    if not _PAPER:
        from png import read_png
        p = os.path.join(ROOT, PAPER_TILE)
        _PAPER.append(read_png(p) if os.path.isfile(p) else None)
    return _PAPER[0]


def flatten_on_ground(src):
    """A copy of src composited over the game's paper tile when it has any transparency, else src itself (cached by content)."""
    import tempfile
    from png import read_png, write_png
    w, h, rows = read_png(src)
    if all(px[3] == 255 for row in rows for px in row):
        return src
    cache = os.path.join(tempfile.gettempdir(), "art-loop-cache")
    os.makedirs(cache, exist_ok=True)
    out = os.path.join(cache, "paper-" + content_sha(src)[:16] + ".png")
    if not os.path.isfile(out):
        paper = packet_paper()
        if paper is None:
            pw, ph, prow = 1, 1, [[PACKET_GROUND + (255,)]]
        else:
            pw, ph, prow = paper
        flat = [[tuple((c * px[3] + gc * (255 - px[3])) // 255 for c, gc in zip(px[:3], prow[y % ph][x % pw]))
                 + (255,) for x, px in enumerate(row)] for y, row in enumerate(rows)]
        write_png(out, w, h, flat)
    return out


PACKET_MAX = 1568   # longest edge the critic's image viewer keeps at full detail; larger images are shrunk before it sees them


def fit_packet(src, limit=PACKET_MAX):
    """src itself when its longest edge is within limit; else a full-detail crop (never a resize): the subject's opaque
    bounding box (a fully opaque image: its centre), cut to at most limit x limit around the box centre. Cached by content.
    A large frame shown whole is shrunk by the viewer, and the critic then calls the figure a coarse pixel figure."""
    import tempfile
    from png import read_png, write_png
    w, h, rows = read_png(src)
    if max(w, h) <= limit:
        return src
    cache = os.path.join(tempfile.gettempdir(), "art-loop-cache")
    os.makedirs(cache, exist_ok=True)
    out = os.path.join(cache, f"fit{limit}-" + content_sha(src)[:16] + ".png")
    if not os.path.isfile(out):
        ys = [y for y, r in enumerate(rows) if any(px[3] > 0 for px in r)] or [0, h - 1]
        xs = [x for r in rows for x, px in enumerate(r) if px[3] > 0] or [0, w - 1]
        x0, x1, y0, y1 = min(xs), max(xs), min(ys), max(ys)
        cw, ch = min(x1 - x0 + 1, limit), min(y1 - y0 + 1, limit)
        x = int(min(max((x0 + x1 + 1 - cw) // 2, 0), w - cw))
        y = int(min(max((y0 + y1 + 1 - ch) // 2, 0), h - ch))
        write_png(out, cw, ch, [r[x:x + cw] for r in rows[y:y + ch]])
    return out


def _pair(folder, mine, other, rnd, frame_src=None, frame=None):
    os.makedirs(folder)
    mine_x = rnd.random() < 0.5
    a, b = (os.path.join(folder, "X.png"), os.path.join(folder, "Y.png"))
    if frame_src is not None:
        cell = (a if mine_x else b) + ".cell.png"
        frame_of(frame_src, frame, cell)
        shutil.copy(fit_packet(flatten_on_ground(cell)), a if mine_x else b)
        os.remove(cell)
    else:
        shutil.copy(fit_packet(flatten_on_ground(mine)), a if mine_x else b)
    shutil.copy(fit_packet(flatten_on_ground(other)), b if mine_x else a)
    return "X" if mine_x else "Y"


class PieceNotFound(ValueError):
    """The piece's colours are nowhere in the in-engine capture: there is nothing to crop for the context pair."""


CONTEXT_CROPS = os.path.join("evals", "art-judge", "context-crops.json")
LOCATE_SHARE = 0.03      # a colour is the piece's when it covers this share of the piece's opaque pixels
LOCATE_BG_SHARE = 0.10   # ...and is not the capture's background when it covers more than this share of the capture
LOCATE_DIST = 40         # RGB distance of a capture pixel to one of the piece's colours
LOCATE_MIN = 12          # fewest matching capture pixels that count as the piece being there


def piece_signature(ours):
    """The piece's own colours: [(r, g, b)] of its most common colours among opaque pixels (a sheet: every frame)."""
    from png import read_png
    _, _, rows = read_png(ours)
    hist = {}
    n = 0
    for row in rows:
        for px in row[::2]:
            if px[3] >= 200:
                k = (px[0] >> 4, px[1] >> 4, px[2] >> 4)
                acc = hist.setdefault(k, [0, 0, 0, 0])
                acc[0] += 1
                for i in range(3):
                    acc[i + 1] += px[i]
                n += 1
    out = []
    for c, r, g, b in sorted(hist.values(), reverse=True)[:6]:
        if n and c / n >= LOCATE_SHARE:
            out.append((r // c, g // c, b // c))
    return out


_LOCATED = {}


def locate_piece(capture, ours, pad=0.35, min_side=64):
    """Cached per (capture, piece file, their mtimes, pad, min_side): the pixel scan runs once per critic round, not per session.
    (x, y, w, h) of the piece in an in-engine capture, from the piece's own colours: capture pixels near one of its
    colours that are not the capture's background, trimmed to the 3rd..97th percentile on each axis, padded.
    Raises PieceNotFound when too few pixels match."""
    key = (os.path.abspath(capture), os.path.abspath(ours), os.path.getmtime(capture), os.path.getmtime(ours), pad, min_side)
    if key not in _LOCATED:
        _LOCATED[key] = _locate_piece(capture, ours, pad, min_side)
    return _LOCATED[key]


def _locate_piece(capture, ours, pad, min_side):
    from png import read_png
    sig = piece_signature(ours)
    w, h, rows = read_png(capture)
    total = w * h
    bg = {}
    for row in rows:
        for px in row[::3]:
            k = (px[0] >> 4, px[1] >> 4, px[2] >> 4)
            bg[k] = bg.get(k, 0) + 1
    seen = max(1, total // 3)
    sig = [c for c in sig if bg.get((c[0] >> 4, c[1] >> 4, c[2] >> 4), 0) / seen <= LOCATE_BG_SHARE]
    if not sig:
        raise PieceNotFound("the piece's colours are the capture's background")
    xs, ys = [], []
    lim = LOCATE_DIST * LOCATE_DIST
    for y, row in enumerate(rows):
        for x, px in enumerate(row):
            for c in sig:
                if (px[0] - c[0]) ** 2 + (px[1] - c[1]) ** 2 + (px[2] - c[2]) ** 2 <= lim:
                    xs.append(x)
                    ys.append(y)
                    break
    if len(xs) < LOCATE_MIN:
        raise PieceNotFound(f"the piece is not in the capture ({len(xs)} matching pixels)")
    xs.sort()
    ys.sort()
    lo, hi = int(len(xs) * 0.03), max(int(len(xs) * 0.97) - 1, 0)
    x0, x1, y0, y1 = xs[lo], xs[hi], ys[int(len(ys) * 0.03)], ys[hi]
    cw, ch = max(x1 - x0 + 1, 1), max(y1 - y0 + 1, 1)
    side = max(cw * (1 + 2 * pad), ch * (1 + 2 * pad), min_side)
    cx, cy = (x0 + x1) / 2, (y0 + y1) / 2
    side = min(side, w, h)
    x = int(min(max(cx - side / 2, 0), w - side))
    y = int(min(max(cy - side / 2, 0), h - side))
    return x, y, int(side), int(side)


def crop_png(src, rect, out):
    """Cut rect (x, y, w, h) of src to out (clamped to the image)."""
    from png import read_png, write_png
    w, h, rows = read_png(src)
    x, y, cw, ch = rect
    x, y = max(0, min(x, w - 1)), max(0, min(y, h - 1))
    cw, ch = max(1, min(cw, w - x)), max(1, min(ch, h - y))
    write_png(out, cw, ch, [r[x:x + cw] for r in rows[y:y + ch]])
    return out


def context_reference(refs, piece, root=ROOT):
    """(image, rect|None) the element's context pair shows against the capture crop: its crop of the key art
    (evals/art-judge/context-crops.json: where the matching element sits in the key art), else the element's own first
    reference image on its own background (rect None)."""
    key = context_ref(refs, root)
    for base in (root, ROOT):
        p = os.path.join(base, CONTEXT_CROPS)
        if os.path.isfile(p):
            with open(p, encoding="utf-8") as fh:
                crops = json.load(fh)
            hit = (crops.get("elements") or {}).get(piece) or next(
                (v for pre, v in (crops.get("prefixes") or {}).items() if piece.startswith(pre)), None)
            if hit and hit.get("ref", "keyart") in ("keyart", None):
                return key, tuple(hit["rect"])
            break
    own = element_refs(refs, piece, root)
    return (own[0] if own else key), None


def context_crops(refs, piece, capture, piece_file, root, out_dir):
    """(capture crop file, reference file, {capture: rect, reference: rect|None}) for an element's context pair: the
    in-engine capture cut to the piece, against the matching element of the key art (or the element alone)."""
    rect = locate_piece(capture, piece_file)
    ref, rrect = context_reference(refs, piece, root)
    os.makedirs(out_dir, exist_ok=True)
    mine = crop_png(capture, rect, os.path.join(out_dir, "capture-crop.png"))
    src = ref if os.path.isabs(ref) else (os.path.join(root, ref) if os.path.exists(os.path.join(root, ref))
                                          else os.path.join(ROOT, ref))
    theirs = crop_png(src, rrect, os.path.join(out_dir, "reference-crop.png")) if rrect else src
    return mine, theirs, {"capture": list(rect), "reference": list(rrect) if rrect else None}


def blind(refs, card, piece, ours, out_dir, seed=None, root=ROOT, quality=False, kind=None, ref=None,
          calibrate=True, piece_file=None):
    """Make one critic session's folder. Returns the key path (outside the folder).
    kind: reference (one of the piece's references; `ref` names which, else the seed picks), quality_bar (the piece's
    quality-bar image; quality=True is the same), motion (the whole sheet against a reference sheet) or context (ours
    is an in-engine capture with the piece in it, against the key art). A sheet in a reference or quality_bar pair is
    judged by one frame the seed picks. calibrate=True (the loop): the pair sits among calibration pairs in lettered
    folders, and the session counts only when it gets every calibration pair right (judge()).
    A context pair for a non-scene piece (piece_file given) is cut to the piece: the capture crop against the piece's
    key-art crop (context-crops.json), or against its own first reference image when it has no crop entry."""
    kind = kind or ("quality_bar" if quality else "reference")
    if kind not in KINDS:
        raise ValueError(f"unknown pair kind {kind!r} ({', '.join(KINDS)})")
    info = sheet_info(ours) if kind != "context" else None
    if kind == "motion" and not sheet_info(ours):
        raise ValueError(f"{ours} is not a sheet (no .sprite.json with 2+ frames): a motion pair needs one")
    if ref:
        cands = [ref]
    elif kind == "quality_bar":
        cands = [quality_ref(refs, piece)]
    elif kind == "context":
        cands = [context_ref(refs, root)]
    elif kind == "motion":
        cands = sheet_refs(refs, card, piece, root)
    else:
        cands = piece_refs(refs, card, piece)
    if not cands:
        raise ValueError(f"card {card} has no reference image for piece {piece}")
    rnd = random.Random(seed)
    other = os.path.join(root, rnd.choice(cands))
    if os.path.isdir(out_dir):
        shutil.rmtree(out_dir)
    frame = rnd.randrange(info[0]) if info and kind != "motion" else None
    crop = kind == "context" and piece_file and piece != "scene"
    what = refs["scene"]["what"].split(".")[0] if piece == "scene" or (kind == "context" and not crop) \
        else refs["elements"][piece]["what"]
    did = None if piece == "scene" else refs["elements"][piece].get("described")
    target = art_judge.refs_by_id(refs)[did]["description"] if did else None
    key = {"ours_file": os.path.abspath(ours), "reference": rel_to(other, root), "seed": seed, "kind": kind,
           "frame": frame, "card": card, "piece": piece, "root": os.path.abspath(root)}
    if crop:   # the capture cut to the piece against the matching element of the key art, not the whole frames
        ours, other, key["context_crop"] = context_crops(refs, piece, ours, piece_file, root,
                                                         tempfile.mkdtemp(prefix="art-ctx-"))
    if not calibrate:
        os.makedirs(out_dir)
        key["ours"] = _pair(os.path.join(out_dir, "tmp"), ours, other, rnd, ours if frame is not None else None, frame)
        for f in ("X.png", "Y.png"):
            os.replace(os.path.join(out_dir, "tmp", f), os.path.join(out_dir, f))
        os.rmdir(os.path.join(out_dir, "tmp"))
        prompt = critic_prompt(what, target)
        probs = critic_prompt_problems(prompt.split("\nThe style target for this piece")[0])
    else:
        crude = calibration_set(root)
        if not crude:
            raise ValueError(f"no critic calibration set ({CALIBRATION}): a critic session never runs uncalibrated")
        mine_el = [f for f, els in crude if piece in els]
        team = rnd.choice(element_refs(refs, piece, root) or cands)
        team = os.path.join(root, team) if not os.path.isabs(team) else team
        letters = ["A", "B", "C"]
        rnd.shuffle(letters)
        real, bad, same = letters
        os.makedirs(out_dir)
        key["ours"] = _pair(os.path.join(out_dir, real), ours, other, rnd, ours if frame is not None else None, frame)
        key["folder"] = real
        # A crude render of this element when the set has one; else a crude copy of the team image itself, so the pair
        # always shows the same kind of thing, plainly worse (the check defect behind 3/9 calibrated on the VFX pieces).
        rough = rnd.choice(mine_el) if mine_el else crude_of(team, root)
        crude_side = _pair(os.path.join(out_dir, bad), rough, team, rnd)
        _pair(os.path.join(out_dir, same), rough, near_copy(rough, root), rnd)   # two equal images: SAME
        key["calibration"] = {bad: "Y" if crude_side == "X" else "X", same: "SAME"}
        prompt = PANEL_PROMPT.format(letters=", ".join(sorted(letters)), what=what)
        if target:
            prompt += "\nThe style target for this piece, in words (judge every folder against it too):\n" + \
                "\n".join(f"- {t}" for t in target) + "\n"
        probs = critic_prompt_problems(prompt.split("\nThe style target for this piece")[0])
    if probs:
        raise ValueError("; ".join(probs))
    with open(os.path.join(out_dir, "prompt.md"), "w", encoding="utf-8") as fh:
        fh.write(prompt)
    kp = out_dir.rstrip("/\\") + ".key.json"
    with open(kp, "w", encoding="utf-8") as fh:
        json.dump(_repo_relative(key), fh)   # no home paths in tracked files (pipeline_check [private])
    return kp


def _repo_relative(o):
    """Paths under the repo or the home folder become repo-relative (or ~-free) strings."""
    home = os.path.expanduser("~")
    if isinstance(o, dict):
        return {k: _repo_relative(v) for k, v in o.items()}
    if isinstance(o, list):
        return [_repo_relative(v) for v in o]
    if isinstance(o, str) and o.startswith(home):
        try:
            r = os.path.relpath(o, ROOT)
            return r if not r.startswith("..") else o.replace(home, "~", 1)
        except ValueError:
            return o.replace(home, "~", 1)
    return o


def judge(text, key, root=None, session=""):
    """(winner X|Y|SAME of the judged pair, gap). A calibrated folder: one `<letter>: WINNER: ...` line per folder,
    and every calibration folder must be right, or the session is refused (ValueError). Each calibration answer is
    logged in the evals/art-judge/agreement.csv format (Saved/Logs/pipeline/critic-calibration.csv)."""
    if "calibration" not in key:
        return read_verdict(text)
    if NUMBER_SCORE.search(text or ""):
        raise ValueError("the critic gave a number score; the verdict is binary (WINNER: X|Y|SAME)")
    got = {}
    for m in PANEL_LINE.finditer(text or ""):
        got.setdefault(m.group(1).upper(), []).append((m.group(2).upper(), (m.group(3) or "").strip()))
    need = sorted(list(key["calibration"]) + [key["folder"]])
    if sorted(got) != need or any(len(v) != 1 for v in got.values()):
        raise ValueError(f"the critic must answer exactly one line for each folder {', '.join(need)}")
    wrong = [f for f, want in key["calibration"].items() if got[f][0][0] != want]
    if root:
        path = os.path.join(root, CAL_LOG)
        os.makedirs(os.path.dirname(path), exist_ok=True)
        new = not os.path.isfile(path)
        with open(path, "a", encoding="utf-8", newline="") as fh:
            w = csv.DictWriter(fh, AGREEMENT_COLS, lineterminator="\n")
            if new:
                w.writeheader()
            for f, want in sorted(key["calibration"].items()):
                w.writerow({"date": datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%MZ"),
                            "pair_id": f"{session or 'session'}:{f}", "seed": key.get("seed"),
                            "model": "art-loop critic session", "prompt_version": "art_loop PANEL_PROMPT",
                            "rubric_version": "", "judge_closer": got[f][0][0], "judge_rows_x": "",
                            "judge_rows_y": "", "order_stable": "", "expected_closer": want,
                            "note": "correct" if got[f][0][0] == want else "WRONG: session does not count"})
    if wrong:
        raise ValueError(f"the critic missed calibration folder(s) {', '.join(wrong)}: this session does not count")
    return got[key["folder"]][0]


# ---------- the deterministic checks, measured (never declared) ----------
def content_sha(path):
    """sha256 of the file's bytes; an LFS pointer gives the object id (the same number)."""
    with open(path, "rb") as fh:
        raw = fh.read()
    m = LFS_OID.match(raw)
    return m.group(1).decode() if m and len(raw) < 1024 else hashlib.sha256(raw).hexdigest()


def rel_to(path, root):
    return os.path.relpath(os.path.abspath(path), os.path.abspath(root)).replace(os.sep, "/")


def provenance_row(root, path):
    p = os.path.join(root, "pipeline", "art", "provenance.csv")
    try:
        with open(p, encoding="utf-8", newline="") as fh:
            for r in csv.DictReader(fh):
                if r.get("asset_path") == rel_to(path, root):
                    return r
    except OSError:
        pass
    return None


def not_art(root, path):
    """Why the file can never pass (a labelled placeholder or a practice stand-in), else None."""
    row = provenance_row(root, path) or {}
    origin = (row.get("origin") or "").lower()
    hit = [w for w in NOT_ART if w in origin]
    return f"{rel_to(path, root)} is a {hit[0]} (provenance origin: {row.get('origin')})" if hit else None



def jitter_problems(path):
    """Frame jitter of an animation sheet (its sidecar has 2+ frames and "anim" or "loop"): anchor offset (px) and
    scale drift (%) between consecutive frames over the limits in frame_register.JITTER_LIMITS. [] for anything else."""
    import frame_register
    info = sheet_info(path)
    try:
        with open(os.path.splitext(path)[0] + ".sprite.json", encoding="utf-8") as fh:
            side = json.load(fh)
    except (OSError, ValueError):
        return []
    if not info or not (side.get("anim") or side.get("loop")):
        return []
    n, fw, fh_ = info
    frames = frame_register.sheet_frames(path, (fw, fh_), n)
    j = frame_register.jitter(frames, band=side.get("anchor_band") or frame_register.BAND,
                           span_mode=side.get("span_mode") or "base", loop=bool(side.get("loop")))
    lim = frame_register.JITTER_LIMITS
    out = []
    if j["offset_px"] > lim["offset_px"]:
        out.append(f"jitter: anchor moves {j['offset_px']:g} px between consecutive frames (limit {lim['offset_px']:g})")
    if j["scale_pct"] > lim["scale_pct"]:
        out.append(f"jitter: figure scale drifts {j['scale_pct']:.1f}% between consecutive frames (limit {lim['scale_pct']:g}%)")
    return out


EFFECT_PIECES = ("vfx-", "owl-bolt", "bolt-hit", "wand-shot", "umbrella-repair")


def is_effect(path, piece=""):
    """An effect (shot, burst, glow): its sidecar says kind fx, or the piece is a vfx-* / shot element."""
    try:
        with open(os.path.splitext(path)[0] + ".sprite.json", encoding="utf-8") as fh:
            if json.load(fh).get("kind") == "fx":
                return True
    except (OSError, ValueError, AttributeError):
        pass
    return str(piece).startswith(EFFECT_PIECES)


def sprite_checks(path, root=ROOT, effect=False):
    """(screen_check ok, art_check ok, lines) on a sprite or sheet: screen_check's flat/grey/outline rules (its own
    aspect) and art_check's colour rules, read on the non-transparent pixels only (art_check.measure_sprite); an
    effect (effect=True) is read against the effect palette. The frame-share rules (dark share, accent caps, paper
    texture) belong to the full frame: the `scene` piece's art_ref_check runs them on a capture."""
    import art_check
    import screen_check
    style = os.path.join(root if os.path.isfile(os.path.join(root, "pipeline", "art", "style.json")) else ROOT,
                         "pipeline", "art", "style.json")
    t = screen_check.thresholds(style)
    t["aspect_tol"] = 1e9   # a sprite is not a 16:9 view; the flat, grey and outline rules still apply
    res = screen_check.check(path, t)
    with open(style, encoding="utf-8") as fh:
        st = json.load(fh)
    try:
        fails = art_check.sprite_failures(path, st, effect)
    except ValueError as e:
        fails = [str(e)]
    jit = jitter_problems(path)
    fails += jit
    lines = ["  " + screen_check.summary(dict(res, image=os.path.basename(path))),
             f"  art_check ({'effect' if effect else 'sprite'} colour rules): {'PASS' if not fails else 'FAIL'}" +
             ("" if not fails else " (" + "; ".join(fails[:3]) + ")")]
    return res["pass"], not fails, lines


def measure(root, card, piece, path):
    """(ok, score, lines, results) of the deterministic checks on our file. results: {check: pass|fail}."""
    import art_ref_check
    if not os.path.isfile(path):
        return False, 0.0, [f"no file {path}"], {c: "fail" for c in CHECKS}
    why = not_art(root, path)
    if why:
        return False, 0.0, [f"{why}: a placeholder is never art"], {c: "fail" for c in CHECKS}
    commit = head(root)
    rp = os.path.join(root, "pipeline", "art", "references.json")
    rp = rp if os.path.isfile(rp) else art_judge.REFS   # this checkout's references, not the tool's own copy
    if piece == "scene":
        rc, lines = art_ref_check.run(card, scene_shot=path, refs_path=rp, root=root, commit=commit)
        ac = any(ln.strip().startswith("art_check: PASS") for ln in lines)
        sc = any(ln.strip().startswith("screen_check: PASS") for ln in lines)
    else:
        rc, lines = art_ref_check.run(card, element_id=piece, files=[path], refs_path=rp, root=root, commit=commit)
        sc, ac, more = sprite_checks(path, root, is_effect(path, piece))
        lines = lines + more
    m = re.search(r"score=([\d.]+)", lines[-1] if piece == "scene" else
                  next((ln for ln in lines if ln.startswith("art_ref_check:")), ""))
    results = {"art_check": "pass" if ac else "fail", "screen_check": "pass" if sc else "fail",
               "art_ref_check": "pass" if rc == 0 else "fail"}
    return all(v == "pass" for v in results.values()), float(m.group(1)) if m else 0.0, lines, results


def read_verdict(text):
    """(winner X|Y|SAME, gap) or raises ValueError for a refused answer (none, two, or a number score)."""
    if NUMBER_SCORE.search(text or ""):
        raise ValueError("the critic gave a number score; the verdict is binary (WINNER: X|Y|SAME)")
    w = VERDICT.findall(text or "")
    if len(w) != 1:
        raise ValueError("the critic must answer exactly one `WINNER: X|Y|SAME` line")
    g = GAP.search(text)
    return w[0].upper(), (g.group(1).strip() if g else "")


def combine(verdicts):
    """One round's verdict over its pairs: reference if any pair prefers the other image, else same if any, else ours."""
    return "reference" if "reference" in verdicts else "same" if "same" in verdicts else "ours"


def outcome(winner, key):
    """ours | same | reference."""
    if winner == "SAME":
        return "same"
    return "ours" if winner == key["ours"] else "reference"


def decide(history, stuck_rounds=STUCK_ROUNDS):
    """pass | continue | stuck from the round history (oldest first). Each round: verdict (ours|same|reference),
    checks (True when every deterministic check passed), score (the deterministic score, higher is better).
    No round cap: only the bar ends the loop, and only a run of rounds with no improvement escalates."""
    if not history:
        return "continue"
    last = history[-1]
    if last["verdict"] in ("ours", "same") and last["checks"] and not missing_pairs(last):
        return "pass"
    flat = 0
    best = prev = None
    for r in history:
        improved = best is None or r["score"] > best["score"] + 1e-9 or \
            (r["verdict"] != "reference" and best["verdict"] == "reference") or (r["checks"] and not best["checks"])
        if improved:
            best, flat = r, 0
        elif prev is not None and gap_key(r.get("gap")) != gap_key(prev.get("gap")):
            flat = 0   # a new biggest gap is a change, not a stall (D-new-no-round-cap: the same gap, no better score)
        else:
            flat += 1
        prev = r
    return "stuck" if flat >= stuck_rounds else "continue"


def missing_pairs(rec):
    """What a round still lacks before it may pass. A panel round (`combos`): every required pair (each reference of
    the element, the quality bar, the motion pair for a sheet, the in-engine context for an element piece) answered
    ours or SAME by PANEL calibrated critic sessions, unanimously. A round with typed pairs only: reference and
    quality_bar, motion for a sheet. A round without typed pairs (a test's bare pair) is judged by its verdict alone."""
    if "combos" in rec:
        return list(rec.get("missing") or [])
    if "pairs" not in rec:
        return []
    need = ["reference", "quality_bar"] + (["motion"] if rec.get("sheet") else [])
    return [k for k in need if rec["pairs"].get(k) not in ("ours", "same")]


def gap_key(g):
    return re.sub(r"\s+", " ", (g or "").strip().lower().rstrip("."))


def required_pairs(refs, piece, ours, root=ROOT):
    """[(kind, other image or None, ours-side file)] a round must judge: every reference of the element (the scene for
    `scene`), the quality bar, every reference sheet in motion when ours is a sheet, and for an element piece its
    in-engine context (the newest capture after the piece, against the key art; None when there is no capture)."""
    out = [("reference", r, ours) for r in element_refs(refs, piece, root)]
    out.append(("quality_bar", quality_ref(refs, piece), ours))
    if sheet_info(ours):
        byid = art_judge.refs_by_id(refs)
        el = refs["elements"].get(piece) or {}
        sheets = [byid[r]["path"] for r in el.get("refs", []) if r in byid and byid[r].get("cell")
                  and byid[r]["path"] in [p for _, p, _ in out]]
        out += [("motion", r, ours) for r in (sheets or [p for k, p, _ in out if k == "reference"])]
    if piece != "scene" and not (refs["elements"].get(piece) or {}).get("ui"):   # a screen's capture is its own context
        out.append(("context", context_ref(refs, root), find_capture(root, ours)))
    return out


def session_folder(refs, card, piece, kind, other, mine, base, rnd_round, i, m, root=ROOT, piece_file=None):
    """One critic session's folder for pair number i of a round (session number m of that pair): (folder, key)."""
    d = os.path.join(base, f"{piece}-r{rnd_round}-{i:02d}-{kind}-c{m + 1}")
    seed = (rnd_round * 1000 + i * 10 + m)
    with open(blind(refs, card, piece, mine, d, seed=seed, root=root, kind=kind, ref=other, piece_file=piece_file),
              encoding="utf-8") as fh:
        key = json.load(fh)
    key["combo"] = f"{kind}:{other}"
    return d, key


def panel_folders(refs, card, piece, ours, base, rnd_round, root=ROOT):
    """Every critic folder of one round: PANEL calibrated folders per required pair (fresh order and calibration
    pairs each). Returns ([(folder, key)], [missing descriptions])."""
    out, missing = [], []
    for i, (kind, other, mine) in enumerate(required_pairs(refs, piece, ours, root)):
        if mine is None:
            missing.append("context (no in-engine capture made after the piece: import it and run the smoke, whose "
                           "screenshot is the capture)")
            continue
        try:
            for m in range(PANEL):
                out.append(session_folder(refs, card, piece, kind, other, mine, base, rnd_round, i, m, root,
                                          ours if kind == "context" else None))
        except PieceNotFound as e:
            missing.append(f"context ({e})")
    return out, missing


def redrawer(refs, card, piece, ours, base, rnd_round, root=ROOT):
    """redraw(key, m) for ask_calibrated: a fresh session (new seed, new calibration pairs) for key's pair."""
    specs = {f"{k}:{o}": (i, k, o, m) for i, (k, o, m) in enumerate(required_pairs(refs, piece, ours, root))
             if m is not None}

    def redraw(key, m):
        spec = specs.get(key.get("combo"))
        if spec is None:
            return None
        i, kind, other, mine = spec
        try:
            return session_folder(refs, card, piece, kind, other, mine, base, rnd_round, i, m, root,
                                  ours if kind == "context" else None)
        except (PieceNotFound, ValueError):
            return None
    return redraw


def summarise(answers, required, missing=()):
    """One round's verdict from [(key, outcome or None, gap)] over the required combos. Returns the record fields:
    pairs (each kind's combined outcome), combos, panel (fewest counted sessions on a combo), calibration, missing."""
    by = {}
    for key, out, g in answers:
        by.setdefault(key.get("combo") or key.get("kind") or "pair", []).append((key.get("kind"), out, g))
    kinds, miss, gaps, cal = {}, list(missing), [], {"sessions": 0, "passed": 0}
    for key, out, g in answers:
        if "calibration" in key:
            cal["sessions"] += 1
            cal["passed"] += out is not None
    counted = []
    for combo in required:
        votes = by.get(combo, [])
        good = [o for _, o, _ in votes if o is not None]
        counted.append(len(good))
        kind = combo.split(":", 1)[0]
        res = "reference" if len(good) < PANEL or any(o == "reference" for o in good) else \
            ("same" if "same" in good else "ours")
        kinds[kind] = combine([kinds[kind], res]) if kind in kinds else res
        if res == "reference":
            miss.append(combo + (f" ({len(good)}/{PANEL} calibrated sessions)" if len(good) < PANEL else ""))
        gaps += [g for _, o, g in votes if g and o not in ("ours", None)]   # a refused session is no art gap
    for k in ("reference", "quality_bar"):
        kinds.setdefault(k, "reference")
    refused = sorted({g for _, o, g in answers if o is None})
    gap = "; ".join(dict.fromkeys(gaps))
    if refused and not gap:
        gap = "critic sessions refused (calibration missed or no answer): judge again"
    return {"pairs": kinds, "combos": sorted(required), "panel": min(counted) if counted else 0,
            "calibration": cal, "missing": miss, "gap": gap, "refused": refused[:5]}


def run_piece(build, critic, checks, make_pair, log, stuck_rounds=STUCK_ROUNDS):
    """Drive one piece to the bar. build(gap) -> our file; checks(file) -> (passed, score, lines);
    make_pair(file) -> a list of (pair_dir, key) (one tuple is taken as a list of one); critic(pair_dir) -> the
    critic's text (it gets the folder only, one fresh session per call); log(record).
    With blind()'s keys the loop builds the whole panel itself: PANEL calibrated sessions per pair, against every
    reference of the element, the quality bar, the sheet in motion and the in-engine context, and it measures the
    deterministic checks itself. Returns ("pass"|"stuck", history)."""
    history, gap = [], ""
    while True:
        ours = build(gap)
        ok, score, _ = checks(ours)
        pairs = make_pair(ours)
        if isinstance(pairs, tuple):
            pairs = [pairs]
        pairs = list(pairs)
        ctx = next((k for _, k in pairs if isinstance(k, dict) and k.get("card") and k.get("root")), None)
        rec = {"round": len(history) + 1, "checks": ok, "score": score, "file": ours}
        if ctx:   # blind()'s keys: the full calibrated panel, the measured checks
            root, card, piece = ctx["root"], ctx["card"], ctx["piece"]
            refs, _ = refs_and_hash(root)
            base = os.path.dirname(pairs[0][0].rstrip("/\\"))
            folders, missing = panel_folders(refs, card, piece, ours, base, len(history) + 1, root)
            items = ask_calibrated(folders, lambda d: (lambda g: (g[0] if isinstance(g, tuple) else g) or "")(critic(d)),
                                   redrawer(refs, card, piece, ours, base, len(history) + 1, root), jobs=1)
            rec["round"] = unique_round(root, piece, rec["round"])
            rec.update(finish_round(root, card, piece, ours, items, missing, rec["round"], ok))
            attach_evidence(root, card, piece, rec, items, refs_hash_of(root))
        else:
            verdicts, gaps = [], []
            for pair, key in pairs:
                try:
                    winner, g = judge(critic(pair), key)
                    verdicts.append(outcome(winner, key))
                except ValueError as e:
                    verdicts.append("reference")
                    g = f"refused critic answer: {e}"
                if g and verdicts[-1] != "ours":
                    gaps.append(g)
            rec.update(verdict=combine(verdicts), gap="; ".join(gaps))
        history.append(rec)
        log(rec)
        state = decide(history, stuck_rounds)
        if state != "continue":
            return state, history
        gap = rec["gap"] if rec["checks"] else rec["gap"] + " (and the deterministic checks failed)"


def head(root=ROOT):
    try:
        return subprocess.run(["git", "-C", root, "rev-parse", "HEAD"], capture_output=True, text=True,
                              check=True).stdout.strip()[:12]
    except (OSError, subprocess.CalledProcessError):
        return "none"


def log_round(root, card, piece, rec, refs_hash, commit):
    rec = dict(rec, card=card, piece=piece, refs=refs_hash, commit=commit,
               at=datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"))
    path = os.path.join(root, LOG)
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "a", encoding="utf-8") as fh:
        fh.write(json.dumps(rec) + "\n")
    try:
        import journal
        con = journal.connect()
        try:
            journal.add(con, f"UE-{card}", "step", role="art-critic", command=f"art loop {piece} round {rec['round']}",
                        exit_code=0 if rec["verdict"] != "reference" and rec["checks"] else 1,
                        note=f"art loop: piece={piece} round={rec['round']} verdict={rec['verdict']} "
                             f"checks={'pass' if rec['checks'] else 'fail'} score={rec['score']} gap={rec['gap']}"[:300])
        finally:
            con.close()
    except Exception:   # the jsonl record is the evidence; the journal is the view
        pass
    write_critic_record(root, card, piece, rec, refs_hash, commit)
    write_record(root, card, piece, rec, refs_hash, commit)


def critic_entry(root, card, piece, rec, refs_hash="", commit=""):
    """One round as a tracked record: piece, round, verdict, checks, panel votes, image hash, date."""
    f = rec.get("file") or ""
    full = f if os.path.isabs(f) else os.path.join(root, f)
    sha = rec.get("sha") or (content_sha(full) if os.path.isfile(full) else "")
    return {"piece": piece, "round": rec.get("round"), "verdict": rec.get("verdict"),
            "checks": bool(rec.get("checks")), "results": rec.get("results") or {},
            "pairs": rec.get("pairs") or {}, "panel": rec.get("panel", 0),
            "calibration": rec.get("calibration") or {}, "missing": rec.get("missing") or [],
            "critic_sessions": list(rec.get("sessions") or []),
            "manifest": rec.get("manifest", ""), "evidence": rec.get("evidence", ""), "prompt": rec.get("prompt", ""),
            "files": sha, "file": rel_to(full, root) if f else "", "card": card, "refs": refs_hash, "commit": commit,
            "gap": rec.get("gap", ""),
            "at": rec.get("at") or datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")}


def write_critic_record(root, card, piece, rec, refs_hash="", commit="", entry=None):
    """Append the round to pipeline/art/critic/<piece>.json (same card/round replaces). Returns the path.
    Only the panel run's own process writes it: an agent session (JAM_ROLE set) is refused (None)."""
    if agent_session():
        print("art_loop: an agent session never writes pipeline/art/critic (JAM_ROLE is set): the panel run does",
              file=sys.stderr)
        return None
    entry = entry or critic_entry(root, card, piece, rec, refs_hash, commit)
    path = os.path.join(root, CRITIC_DIR, piece + ".json")
    data = {"id": piece, "records": []}
    try:
        with open(path, encoding="utf-8") as fh:
            data = json.load(fh)
    except (OSError, ValueError):
        pass
    keep = [r for r in data.get("records", []) if (r.get("card"), r.get("round")) != (entry["card"], entry["round"])]
    data = {"id": piece, "records": keep + [entry]}
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as fh:
        json.dump(data, fh, indent=1)
        fh.write("\n")
    return path


# ---------- the panel's raw evidence: a pass record is the panel run's output, never an agent's text ----------
def agent_session():
    return bool((os.environ.get("JAM_ROLE") or "").strip())


def prompt_id():
    """Which critic prompt judged: a name and the first 12 hex of the sha256 of both prompt templates."""
    h = hashlib.sha256((PANEL_PROMPT + "\0" + CRITIC_PROMPT).encode("utf-8")).hexdigest()[:12]
    return f"art_loop PANEL_PROMPT {h}"


def file_sha256(path):
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def panel_passed(rec):
    """The one pass test for a panel round (write_record, the evidence and the gate's re-run share it)."""
    cal = rec.get("calibration") or {}
    return bool(rec.get("verdict") in ("ours", "same") and rec.get("checks") and "combos" in rec
                and not missing_pairs(rec) and rec.get("panel", 0) >= PANEL
                # Calibration gates each vote, not the round (Nov 13): a session that missed a calibration pair is not
                # counted and ask_calibrated draws a fresh one; requiring every session to calibrate made those redraws
                # useless (ella-transition, ui-defeated: verdict ours on every pair, refused for 9/12 calibration).
                # Each pair still needs PANEL calibrated sessions, all ours or SAME (panel >= PANEL above).
                and cal.get("sessions", 0) > 0 and cal.get("passed", 0) >= PANEL
                and all((rec.get("results") or {}).get(c) == "pass" for c in CHECKS))


def evidence_dir(root, piece, rnd):
    return os.path.join(root, CRITIC_DIR, piece, str(rnd))


def unique_round(root, piece, n):
    """A round number no evidence folder of this piece already uses (a fresh tree restarts the Saved/ log at 1)."""
    base = os.path.join(root, CRITIC_DIR, piece)
    used = [int(x) for x in (os.listdir(base) if os.path.isdir(base) else []) if x.isdigit()]
    try:
        with open(os.path.join(base + ".json"), encoding="utf-8") as fh:
            used += [int(r.get("round") or 0) for r in json.load(fh).get("records", [])]
    except (OSError, ValueError, TypeError):
        pass
    return max(n, max(used, default=0) + 1) if n in used else n


def clean_key(key, root):
    """The key as kept in the repo: no absolute path (the packet is the folder that was judged)."""
    k = dict(key)
    k.pop("root", None)
    k["combo"] = f"{k['kind']}:{k['reference']}"
    for f in ("ours_file",):
        if k.get(f):
            r = rel_to(k[f], root)
            k[f] = os.path.basename(k[f]) if r.startswith("..") else r
    return k


def save_evidence(root, card, piece, rec, items, refs_hash):
    """Write the panel's raw evidence next to the record, pipeline/art/critic/<piece>/<round>/:
    sessions/<name>.answer.md (the critic's text exactly as it answered), packets/<name>/ (the images and prompt it
    judged), keys/<name>.key.json, and manifest.json (sha256 of every file, the shipped image's sha256, the prompt id).
    Returns (sha256 of manifest.json, evidence folder relative to root); None in an agent session."""
    if agent_session():
        return None
    d = evidence_dir(root, piece, rec["round"])
    if os.path.isdir(d):
        shutil.rmtree(d)
    for sub in ("sessions", "keys", "packets"):
        os.makedirs(os.path.join(d, sub))
    names = []
    for folder, key, text in items:
        name = os.path.basename(folder.rstrip("/\\"))
        names.append(name)
        with open(os.path.join(d, "sessions", name + ".answer.md"), "w", encoding="utf-8", newline="") as fh:
            fh.write(text or "")
        with open(os.path.join(d, "keys", name + ".key.json"), "w", encoding="utf-8") as fh:
            json.dump(clean_key(key, root), fh, indent=1, sort_keys=True)
            fh.write("\n")
        shutil.copytree(folder, os.path.join(d, "packets", name))
    files = {}
    for dirpath, _, fnames in os.walk(d):
        for fn in fnames:
            full = os.path.join(dirpath, fn)
            files[rel_to(full, d)] = file_sha256(full)
    f = rec.get("file") or ""
    full = f if os.path.isabs(f) else os.path.join(root, f)
    ctxf = rec.get("context")
    man = {"piece": piece, "round": rec["round"], "card": card, "refs": refs_hash, "prompt": prompt_id(),
           "shipped": {"file": rel_to(full, root), "sha256": content_sha(full)},
           "context": rel_to(ctxf, root) if ctxf else None, "sheet": bool(rec.get("sheet")),
           "sessions": sorted(names), "required": sorted(rec.get("combos") or []),
           "missing_in": [m for m in rec.get("missing") or [] if "calibrated sessions" not in m],
           "results": rec.get("results") or {}, "files": dict(sorted(files.items()))}
    mp = os.path.join(d, "manifest.json")
    with open(mp, "w", encoding="utf-8") as fh:
        json.dump(man, fh, indent=1, sort_keys=True)
        fh.write("\n")
    return file_sha256(mp), rel_to(d, root)


def rederive(root, ev):
    """Re-derive a round from the raw evidence in folder `ev` with the parser the panel run uses (judge, outcome,
    summarise, combine). Returns the record fields the evidence supports."""
    with open(os.path.join(ev, "manifest.json"), encoding="utf-8") as fh:
        man = json.load(fh)
    answers = []
    for name in man["sessions"]:
        with open(os.path.join(ev, "keys", name + ".key.json"), encoding="utf-8") as fh:
            key = json.load(fh)
        with open(os.path.join(ev, "sessions", name + ".answer.md"), encoding="utf-8", newline="") as fh:
            text = fh.read()
        try:
            winner, gap = judge(text, key)
            answers.append((key, outcome(winner, key), gap))
        except ValueError as ex:
            answers.append((key, None, f"refused critic session: {ex}"))
    summ = summarise(answers, man["required"], man.get("missing_in") or [])
    verdict = "reference" if summ["missing"] else combine(list(summ["pairs"].values()))
    return dict(summ, verdict=verdict, sessions=sorted(man["sessions"])), man


def judge_items(root, items, record=True):
    """[(folder, key, critic text)] -> ([(key, outcome|None, gap)], [session names]). A refused answer counts for
    nothing (None)."""
    answers, names = [], []
    for d, key, text in items:
        key = dict(key)
        key["combo"] = f"{key['kind']}:{key['reference']}"
        name = os.path.basename(d.rstrip("/\\"))
        names.append(name)
        try:
            winner, gap = judge(text, key, root if record else None, name)
            answers.append((key, outcome(winner, key), gap))
        except ValueError as ex:
            answers.append((key, None, f"refused critic session: {ex}"))
    return answers, names


def finish_round(root, card, piece, ours_file, items, missing, rnd, checks_ok=True, record=True):
    """One panel round from its sessions [(folder, key, critic text)]: judge them, summarise, measure the checks.
    Returns the round record (not yet logged)."""
    refs, _ = refs_and_hash(root)
    answers, names = judge_items(root, items, record)
    req = sorted({f"{k}:{o}" for k, o, m in required_pairs(refs, piece, ours_file, root) if m is not None}
                 | {a[0]["combo"] for a in answers})
    summ = summarise(answers, req, missing)
    ok, score, lines, results = measure(root, card, piece, ours_file)
    rec = dict(summ, round=rnd, checks=ok and checks_ok, score=score, file=ours_file, results=results,
               sheet=bool(sheet_info(ours_file)), sessions=names, measure_lines=lines,
               verdict="reference" if summ["missing"] else combine(list(summ["pairs"].values())),
               refs_judged=[c.split(":", 1)[1] for c in req if c.startswith("reference:")])
    ctxk = [k for k, _, _ in answers if k.get("kind") == "context"]
    if ctxk:
        rec["context"] = ctxk[0]["ours_file"]
    if os.path.isfile(ours_file):
        rec["sha"] = content_sha(ours_file)
    return rec


def attach_evidence(root, card, piece, rec, items, refs_hash):
    """On a passing round, save the raw evidence and cite it in the record (manifest hash, folder, prompt id)."""
    if not panel_passed(rec):
        return rec
    got = save_evidence(root, card, piece, rec, items, refs_hash)
    if got:
        rec.update(manifest=got[0], evidence=got[1], prompt=prompt_id())
    return rec


def claude_ask(folder):
    """One fresh blind critic session in `folder` (the claude CLI, no shell or edit tools). Returns its stdout."""
    with open(os.path.join(folder, "prompt.md"), encoding="utf-8") as fh:
        prompt = fh.read() + "\nThe folders are in the current folder. Look at the images with your file tools."
    env = {k: v for k, v in os.environ.items() if k not in ("CLAUDECODE", "CLAUDE_CODE_ENTRYPOINT")}
    p = subprocess.run(["claude", "-p", prompt, "--permission-mode", "bypassPermissions", "--disallowedTools",
                        "Bash", "Edit", "Write", "--model", os.environ.get("CRITIC_MODEL", "claude-sonnet-5-5")],
                       cwd=folder, env=env, capture_output=True, text=True)
    return p.stdout


def calibrated(text, key):
    """True when the session's answer parses and gets every calibration folder right (its vote may count)."""
    try:
        judge(text, key)
        return True
    except ValueError:
        return False


def ask_calibrated(folders, ask, redraw, jobs=None):
    """[(folder, key, text)] for every folder, with uncalibrated sessions redrawn until each pair has PANEL calibrated
    sessions, at most REDRAW_MAX redraws per pair (bounded). redraw(key, m) -> (folder, key) is a fresh session for
    the pair `key["combo"]`, m = its session number (>= PANEL). A session that missed a calibration folder stays in
    the list (logged, refused) but summarise() never counts its vote. A pair `redraw` cannot make is not redrawn."""
    texts = ask_all([d for d, _ in folders], ask, jobs)
    items = [(d, k, t) for (d, k), t in zip(folders, texts)]
    used = {}
    while True:
        good, drawn = {}, {}
        for _, k, t in items:
            c = k.get("combo") or f"{k.get('kind')}:{k.get('reference')}"
            drawn[c] = drawn.get(c, 0) + 1
            good[c] = good.get(c, 0) + calibrated(t, k)
        todo = []
        for c, n in good.items():
            for _ in range(min(PANEL - n, REDRAW_MAX - used.get(c, 0))):
                if n >= PANEL:
                    break
                key = next(k for _, k, _ in items if (k.get("combo") or f"{k.get('kind')}:{k.get('reference')}") == c)
                m = PANEL + used.get(c, 0)
                used[c] = used.get(c, 0) + 1
                got = redraw(key, m)
                if got is None:
                    used[c] = REDRAW_MAX
                    break
                todo.append(got)
        if not todo:
            return items
        more = ask_all([d for d, _ in todo], ask, jobs)
        items += [(d, k, t) for (d, k), t in zip(todo, more)]


def ask_all(folders, ask, jobs=None):
    """Run every critic session (fresh each, at most `jobs` at once). Returns the texts in folder order."""
    import concurrent.futures
    jobs = jobs or int(os.environ.get("CRITIC_JOBS") or 4)
    with concurrent.futures.ThreadPoolExecutor(max_workers=max(1, jobs)) as ex:
        return list(ex.map(lambda d: ask(d) or "", folders))


def panel_run(root, card, piece, ours, base, rnd, ask=claude_ask, checks_ok=True, record=True, refs=None):
    """The panel run itself: build every critic folder of the round, run one fresh session per folder, judge, measure.
    Returns (round record, items). Nothing is written to the repo here."""
    refs = refs or refs_and_hash(root)[0]
    shared = shared_layer(root, refs, piece, ours)
    if shared and shared["mode"] == "reuse" and not shared["ok"]:
        checks_ok = False   # the base region was altered: not a reuse, the piece does not count
    if shared and shared.get("brief"):   # the added layer only: the critic brief names what is new
        refs = json.loads(json.dumps(refs))
        el = refs["elements"][piece]
        el["what"] = art_share.brief_what(el["what"], shared["brief"])
    folders, missing = panel_folders(refs, card, piece, ours, base, rnd, root)
    items = ask_calibrated(folders, ask, redrawer(refs, card, piece, ours, base, rnd, root))
    rec = finish_round(root, card, piece, ours, items, missing, rnd, checks_ok, record)
    if shared:
        rec["shared"] = {k: v for k, v in shared.items() if k != "brief"}
    return rec, items


def shared_layer(root, refs, piece, ours):
    """art_share.assess for a piece with a base: the base's shipped image is the file of its newest record."""
    if piece == "scene" or not (refs["elements"].get(piece) or {}).get("base"):
        return None
    b = newest_record(root, refs["elements"][piece]["base"])
    base_path = os.path.join(root, b["file"]) if b and b.get("file") else None
    return art_share.assess(refs, piece, ours, base_path, [root, ROOT])


def newest_record(root, piece):
    try:
        with open(os.path.join(root, CRITIC_DIR, piece + ".json"), encoding="utf-8") as fh:
            recs = json.load(fh).get("records") or []
    except (OSError, ValueError):
        return None
    return recs[-1] if recs else None


def rerun(root, piece, base, ask=claude_ask):
    """The gate's proof that the panel really ran: judge the piece's shipped image again with fresh blind sessions on the
    same packets (the round's seeds; the in-engine context pair is the saved, hash-checked packet because the gate tree
    has no smoke capture). Returns (passed, rec). Writes nothing to the repo."""
    r = newest_record(root, piece)
    if not r or not r.get("file") or not r.get("evidence"):
        raise ValueError(f"{piece}: no record with evidence to re-run")
    refs, _ = refs_and_hash(root)
    ours = os.path.join(root, r["file"])
    saved = os.path.join(root, r["evidence"])
    folders, missing = panel_folders(refs, r.get("card") or "", piece, ours, base, int(r["round"]), root)
    missing = [m for m in missing if not m.startswith("context")]
    if not any(k.get("kind") == "context" for _, k in folders):   # no capture here: the saved context packet
        for name in sorted(os.listdir(os.path.join(saved, "keys"))):
            with open(os.path.join(saved, "keys", name), encoding="utf-8") as fh:
                key = json.load(fh)
            if key.get("kind") == "context":
                stem = name[:-len(".key.json")]
                d = os.path.join(base, "ctx-" + stem)
                shutil.copytree(os.path.join(saved, "packets", stem), d)
                key["ours_file"] = os.path.join(root, key["ours_file"])
                folders.append((d, key))
    items = ask_calibrated(folders, ask, redrawer(refs, r.get("card") or "", piece, ours, base, int(r["round"]), root))
    rec = finish_round(root, r.get("card") or "", piece, ours, items, missing, int(r["round"]), True, False)
    return panel_passed(rec), rec


# ---------- the ship gate's record ----------
def record_path(path):
    return os.path.splitext(path)[0] + RECORD


def shipped(rel):
    """A file that reaches the game as art: an image under Art/ outside Art/Source/ (raw renders, layered sources)."""
    rel = rel.replace(os.sep, "/").lstrip("./")
    return rel.startswith("Art/") and not rel.startswith("Art/Source/") and rel.lower().endswith(SHIPPED_EXT)


def is_screen(root, piece):
    """A UI screen piece (an element with a ui block): its capture is its own context, so it has no context pair."""
    try:
        refs, _ = refs_and_hash(root)
    except Exception:
        return False
    return bool((refs.get("elements", {}).get(piece) or {}).get("ui"))


def write_record(root, card, piece, rec, refs_hash, commit):
    """On a passing panel round (every required pair unanimous ours or SAME from PANEL calibrated sessions, every
    check measured PASS), write <stem>.artloop.json next to the file. Returns its path or None. Never for a
    placeholder, a stand-in, a file outside the repo or a round without the full panel."""
    if agent_session():
        print("art_loop: an agent session never writes a pass record (JAM_ROLE is set): kickoff's art loop does",
              file=sys.stderr)
        return None
    f = rec.get("file") or ""
    full = f if os.path.isabs(f) else os.path.join(root, f)
    cal = rec.get("calibration") or {}
    if not (panel_passed(rec) and os.path.isfile(full) and not rel_to(full, root).startswith("..")
            and not not_art(root, full)):
        return None
    need = ["reference", "quality_bar"] + (["motion"] if sheet_info(full) else []) + \
        (["context"] if piece != "scene" and not is_screen(root, piece) else [])
    if any(rec["pairs"].get(k) not in ("ours", "same") for k in need):
        return None
    sha = content_sha(full)
    if rec.get("sha") and rec["sha"] != sha:
        return None   # the file changed after it was judged
    out = record_path(full)
    ctxf = rec.get("context")
    data = {"file": rel_to(full, root), "sha256": sha, "card": card, "piece": piece, "verdict": rec["verdict"],
            "pairs": rec["pairs"], "panel": rec["panel"], "calibration": cal,
            "critic_sessions": list(rec.get("sessions") or []), "manifest": rec.get("manifest", ""),
            "refs_judged": rec.get("refs_judged", []),
            "context": rel_to(ctxf, root) if ctxf else None,
            "checks": {c: rec["results"][c] for c in CHECKS}, "rounds": rec.get("round"),
            "refs": refs_hash, "judged_commit": commit,
            "at": datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")}
    with open(out, "w", encoding="utf-8") as fh:
        json.dump(data, fh, indent=1)
        fh.write("\n")
    return out


def record_problems(root, rel, refs_hash=None):
    """Why the shipped file `rel` has no valid art-loop pass (empty = it has one). The record next to it must match
    the file's bytes and the current references.json and show: ours or SAME from a unanimous panel of PANEL calibrated
    blind critic sessions (each one right on every calibration pair) against every reference of its element, the
    quality bar, the sheet in motion (a sheet) and the piece in an in-engine capture (an element piece); art_check,
    screen_check and art_ref_check PASS. A placeholder or practice stand-in never has one. Nothing overrides it."""
    full = os.path.join(root, rel)
    if not os.path.isfile(full):
        return []
    why = not_art(root, full)
    if why:
        return [f"{why}: a placeholder or stand-in never ships; render it in Blender and loop it to the bar"]
    rp = record_path(full)
    try:
        with open(rp, encoding="utf-8") as fh:
            r = json.load(fh)
    except (OSError, ValueError):
        return [f"{rel} has no art-loop pass record ({rel_to(rp, root)}): run tools/art_loop.py until a panel of "
                f"{PANEL} calibrated blind critics picks ours or SAME against every reference, the quality bar, "
                "the motion and the in-engine context, and every check passes"]
    out = []
    if r.get("sha256") != content_sha(full):
        out.append(f"{rel} changed after its art-loop pass (sha256 differs from {rel_to(rp, root)}): loop it again")
    if r.get("verdict") not in ("ours", "same"):
        out.append(f"{rel}: its art-loop record has verdict {r.get('verdict')!r}")
    piece = r.get("piece") or ""
    need = ["reference", "quality_bar"] + (["motion"] if sheet_info(full) else []) + \
        (["context"] if piece != "scene" and not is_screen(root, piece) else [])
    lost = [k for k in need if (r.get("pairs") or {}).get(k) not in ("ours", "same")]
    if lost:
        out.append(f"{rel}: the art-loop record has no ours/SAME verdict for {', '.join(lost)}")
    if int(r.get("panel") or 0) < PANEL:
        out.append(f"{rel}: its art-loop pass had {r.get('panel') or 0} critic session(s) per pair, not a panel of "
                   f"{PANEL}")
    cal = r.get("calibration") or {}
    if not cal.get("sessions") or cal.get("passed") != cal.get("sessions"):
        out.append(f"{rel}: its art-loop critics were not all calibrated ({cal.get('passed', 0)}/"
                   f"{cal.get('sessions', 0)} sessions right on every calibration pair)")
    bad = [c for c in CHECKS if (r.get("checks") or {}).get(c) != "pass"]
    if bad:
        out.append(f"{rel}: the art-loop record has no PASS for {', '.join(bad)}")
    rh = refs_hash or refs_and_hash(root)[1]
    if r.get("refs") != rh:
        out.append(f"{rel}: its art-loop pass was against references {r.get('refs')}, not the current {rh}")
    try:
        refs, _ = refs_and_hash(root)
        want = element_refs(refs, piece, root) if piece == "scene" or piece in refs["elements"] else []
    except (OSError, ValueError, KeyError):
        want = []
    if len(set(r.get("critic_sessions") or [])) < PANEL:
        out.append(f"{rel}: its art-loop record names {len(set(r.get('critic_sessions') or []))} critic session(s); "
                   f"a pass needs a panel of {PANEL} per pair, each session named")
    out += recheck(root, rel, r)
    skipped = [p for p in want if p not in (r.get("refs_judged") or [])]
    if skipped:
        out.append(f"{rel}: its art-loop panel did not judge every reference of {piece} (missing {skipped[0]}"
                   + (f" and {len(skipped) - 1} more" if len(skipped) > 1 else "") + ")")
    return out


PIECE_NOTE = re.compile(r"for piece ([\w-]+)")


def provenance_piece(root, rel, depth=3):
    """The judge element a shipped file was made as: the `style targets for piece <id>` note on its provenance row
    or, for a sheet, on the rows of the frames it was assembled from (tools/assetgen.py writes both)."""
    r = provenance_row(root, os.path.join(root, rel)) or {}
    m = PIECE_NOTE.search(r.get("origin") or "")
    if m:
        return m.group(1)
    if depth:
        for inp in (r.get("input_images") or "").split(";"):
            if inp.strip():
                got = provenance_piece(root, inp.strip(), depth - 1)
                if got:
                    return got
    return None


def recheck(root, rel, r):
    """The ship gate's own measurement, never the record's word: the piece the provenance names must be the record's
    piece, and the deterministic checks run again on the shipped bytes (art_ref_check: the calibrated element judge
    with its detail floor; screen_check's flat/grey/outline rules; art_check's colour rules)."""
    full = os.path.join(root, rel)
    piece, card = r.get("piece") or "", r.get("card") or ""
    out = []
    made_as = provenance_piece(root, rel)
    if made_as is None:
        out.append(f"{rel}: its provenance names no judge piece (tools/assetgen.py writes `for piece <id>`): the "
                   "gate cannot tell which bar it must clear")
    elif made_as != piece:
        out.append(f"{rel}: its art-loop record says piece {piece!r}, its provenance says {made_as!r}")
    try:
        ok, _, lines, results = measure(root, card, piece, full)
    except (OSError, ValueError, KeyError) as e:
        return out + [f"{rel}: the ship gate could not re-run the checks ({e}); fails closed"]
    bad = [c for c in CHECKS if results.get(c) != "pass"]
    if bad:
        why = next((ln.strip() for ln in lines if "FAIL" in ln), "")
        out.append(f"{rel}: re-run on the shipped file, {', '.join(bad)} FAIL{(': ' + why) if why else ''} "
                   "(the record's word is not taken)")
    return out


def pass_line(card, piece, verdict, rounds, refs_hash, commit, file=None, sha=None, pairs=None):
    line = (f"art_loop: PASS card={card} piece={piece} verdict={verdict} rounds={rounds} refs={refs_hash} "
            f"commit={commit}")
    if file and sha:
        line += f" file={file} sha={sha[:12]}"
        if pairs:
            line += " pairs=" + ",".join(f"{k}:{pairs[k]}" for k in KINDS if k in pairs) + " checks=pass"
    return line


def unchanged_since_head(root, rel):
    """True when the file at HEAD is the file on disk (committed, no local change)."""
    try:
        p = subprocess.run(["git", "-C", root, "status", "--porcelain", "--", rel], capture_output=True, text=True,
                           check=True)
        return p.stdout.strip() == ""
    except (OSError, subprocess.CalledProcessError):
        return False


def evidence(root, card):
    """(lines, missing pieces) for the current commit and references.json. A round that judged a file is current
    while that file's bytes are the judged bytes and committed at HEAD (its line names HEAD, the file and its sha);
    a round without a file sha must have run on HEAD itself."""
    refs, rh = refs_and_hash(root)
    commit = head(root)
    recs = []
    try:
        with open(os.path.join(root, LOG), encoding="utf-8") as fh:
            recs = [json.loads(ln) for ln in fh if ln.strip()]
    except (OSError, ValueError):
        pass
    lines, missing = [], []
    for p in pieces(refs, card):
        mine = [r for r in recs if r.get("card") == card and r.get("piece") == p]
        last = mine[-1] if mine else None
        ok = bool(last) and last["verdict"] in ("ours", "same") and last["checks"] and last.get("refs") == rh \
            and not missing_pairs(last)
        f = (last or {}).get("file") or ""
        full = f if os.path.isabs(f) else os.path.join(root, f)
        if ok and last.get("sha") and os.path.isfile(full):
            rel = rel_to(full, root)
            if content_sha(full) == last["sha"] and unchanged_since_head(root, rel):
                lines.append(pass_line(card, p, last["verdict"], len(mine), rh, commit, rel, last["sha"],
                                       last.get("pairs")))
                continue
        elif ok and last.get("commit") == commit:
            lines.append(pass_line(card, p, last["verdict"], len(mine), rh, commit))
            continue
        missing.append(p)
    return lines, missing


def cmd_run(a, refs, rh):
    """The panel run: fresh blind critic sessions judge the shipped image, the raw answers and packets are saved next to
    the record and the record cites their manifest. Refused in an agent session (JAM_ROLE): kickoff or the gate runs it."""
    if agent_session():
        print("art_loop: run refused: an agent session never runs the panel that writes a record (JAM_ROLE is set)",
              file=sys.stderr)
        return 2
    tmp = tempfile.mkdtemp(prefix="art-panel-")
    try:
        prior = (newest_record(a.root, a.piece) or {}).get("round") or 0
        rnd = unique_round(a.root, a.piece, int(prior) + 1)
        rec, items = panel_run(a.root, a.card, a.piece, a.ours, tmp, rnd, claude_ask, a.checks == "pass", True, refs)
        attach_evidence(a.root, a.card, a.piece, rec, items, rh)
        for ln in rec.pop("measure_lines", []):
            print(ln)
        log_round(a.root, a.card, a.piece, rec, rh, head(a.root))
    finally:
        shutil.rmtree(tmp, ignore_errors=True)
    state = "pass" if panel_passed(rec) else "continue"
    print(f"art_loop: round {rec['round']} piece={a.piece} verdict={rec['verdict']} pairs="
          + ",".join(f"{k}:{v}" for k, v in rec["pairs"].items())
          + f" panel={rec['panel']} calibration={rec['calibration']['passed']}/{rec['calibration']['sessions']} "
          f"checks={'pass' if rec['checks'] else 'fail'} -> {state}"
          + (f" | GAP: {rec['gap']}" if rec["gap"] else "") + (f" | manifest {rec['manifest']}" if rec.get("manifest") else ""))
    return 0 if state == "pass" else 1


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--root", default=ROOT)
    sub = ap.add_subparsers(dest="cmd", required=True)
    p = sub.add_parser("pieces")
    p.add_argument("--card", required=True)
    b = sub.add_parser("blind")
    for k in ("--card", "--piece", "--ours", "--out"):
        b.add_argument(k, required=True)
    b.add_argument("--seed", type=int)
    b.add_argument("--kind", choices=KINDS, default="reference")
    pn = sub.add_parser("panel")
    for k in ("--card", "--piece", "--ours", "--out"):
        pn.add_argument(k, required=True)
    pn.add_argument("--round", type=int, default=1)
    v = sub.add_parser("verdict")
    for k in ("--panel", "--card", "--piece"):
        v.add_argument(k, required=True)
    v.add_argument("--checks", choices=["pass", "fail"], default="pass",
                   help="fail forces a failed round; pass is never taken on trust (the checks are measured)")
    r = sub.add_parser("run")
    for k in ("--card", "--piece", "--ours"):
        r.add_argument(k, required=True)
    r.add_argument("--checks", choices=["pass", "fail"], default="pass")
    g = sub.add_parser("gate-rerun")
    g.add_argument("--piece", required=True)
    e = sub.add_parser("evidence")
    e.add_argument("--card", required=True)
    a = ap.parse_args(argv)
    try:
        refs, rh = refs_and_hash(a.root)
        if a.cmd == "pieces":
            ps = pieces(refs, a.card)
            print(f"art_loop: card {a.card} pieces: " + (", ".join(ps) or "none"))
            return 0 if ps else 2
        if a.cmd == "blind":
            key = blind(refs, a.card, a.piece, a.ours, a.out, a.seed, a.root, kind=a.kind)
            print(f"art_loop: critic folder {a.out} (lettered pairs, prompt.md, kind={a.kind}); key {key}")
            return 0
        if a.cmd == "panel":
            folders, missing = panel_folders(refs, a.card, a.piece, a.ours, a.out, a.round, a.root)
            os.makedirs(a.out, exist_ok=True)
            with open(os.path.join(a.out, "panel.json"), "w", encoding="utf-8") as fh:
                json.dump({"card": a.card, "piece": a.piece, "ours": os.path.abspath(a.ours), "round": a.round,
                           "folders": [d for d, _ in folders], "missing": missing}, fh, indent=1)
            for d, _ in folders:
                print(f"art_loop: critic session folder {d} (one fresh blind session each; its answer goes to "
                      f"{d}.answer.md)")
            for m in missing:
                print(f"art_loop: cannot judge yet: {m}")
            return 0 if not missing else 1
        if a.cmd == "verdict":
            with open(os.path.join(a.panel, "panel.json"), encoding="utf-8") as fh:
                pj = json.load(fh)
            if (pj["card"], pj["piece"]) != (a.card, a.piece):
                print(f"art_loop: panel {a.panel} is for {pj['card']}/{pj['piece']}", file=sys.stderr)
                return 2
            ours_file = pj["ours"]
            items = []
            for d in pj["folders"]:
                with open(d.rstrip("/\\") + ".key.json", encoding="utf-8") as fh:
                    key = json.load(fh)
                if key.get("ours_file") not in (ours_file, None) and key.get("kind") != "context":
                    print("art_loop: every folder of one panel judges the same file", file=sys.stderr)
                    return 2
                try:
                    with open(d.rstrip("/\\") + ".answer.md", encoding="utf-8", newline="") as fh:
                        text = fh.read()
                except OSError:
                    text = ""
                items.append((d, key, text))
            commit = head(a.root)
            prior = []
            try:
                with open(os.path.join(a.root, LOG), encoding="utf-8") as fh:
                    prior = [json.loads(ln) for ln in fh if ln.strip()]
            except (OSError, ValueError):
                pass
            hist = [r for r in prior if r.get("card") == a.card and r.get("piece") == a.piece]
            rnd = unique_round(a.root, a.piece, len(hist) + 1)
            rec = finish_round(a.root, a.card, a.piece, ours_file, items, pj.get("missing") or [], rnd,
                               a.checks == "pass")
            attach_evidence(a.root, a.card, a.piece, rec, items, rh)
            ok, score, verdict, summ = rec["checks"], rec["score"], rec["verdict"], rec
            lines = rec.pop("measure_lines", [])
            for ln in lines:
                print(ln)
            log_round(a.root, a.card, a.piece, rec, rh, commit)
            state = decide(hist + [rec])
            print(f"art_loop: round {rec['round']} piece={a.piece} verdict={verdict} pairs="
                  + ",".join(f"{k}:{v}" for k, v in summ["pairs"].items())
                  + f" panel={summ['panel']} calibration={summ['calibration']['passed']}/"
                  f"{summ['calibration']['sessions']} checks={'pass' if ok else 'fail'} score={score} -> {state}"
                  + (f" | GAP: {summ['gap']}" if summ["gap"] else "")
                  + (f" | missing: {'; '.join(summ['missing'][:4])}" if summ["missing"] else ""))
            if state == "pass":
                rel = rel_to(ours_file, a.root)
                print(pass_line(a.card, a.piece, verdict, rec["round"], rh, commit, rel, rec.get("sha"),
                                summ["pairs"]))
                if shipped(rel):
                    print(f"art_loop: record {rel_to(record_path(ours_file), a.root)} written: commit it with the file")
            return 0 if state == "pass" else 1
        if a.cmd == "run":
            return cmd_run(a, refs, rh)
        if a.cmd == "gate-rerun":
            # The answers stay for triage (Nov 13: a failed re-run left nothing to read): ../logs/gate-rerun-<piece>/
            common = subprocess.run(["git", "-C", a.root, "rev-parse", "--path-format=absolute", "--git-common-dir"],
                                    capture_output=True, text=True).stdout.strip()   # the main checkout, from the gate or a lane
            main = os.path.dirname(common) if common else os.path.abspath(a.root)
            keep = os.path.join(os.path.dirname(main), "UmbrellaElla-areas", "logs", f"gate-rerun-{a.piece}")
            shutil.rmtree(keep, ignore_errors=True)
            try:
                os.makedirs(keep)
                tmp = keep
            except OSError:
                tmp = tempfile.mkdtemp(prefix="art-rerun-")
            good, rec = rerun(a.root, a.piece, tmp)
            print(f"art_loop: gate re-run piece={a.piece} verdict={rec['verdict']} pairs="
                  + ",".join(f"{k}:{v}" for k, v in rec["pairs"].items())
                  + f" panel={rec['panel']} calibration={rec['calibration']['passed']}/{rec['calibration']['sessions']}"
                  f" checks={'pass' if rec['checks'] else 'fail'} -> {'PASS' if good else 'FAIL'}"
                  + (f" | GAP: {rec['gap']}" if rec.get("gap") else "")
                  + (f" | missing: {'; '.join(rec['missing'][:4])}" if rec["missing"] else ""))
            return 0 if good else 1
        lines, missing = evidence(a.root, a.card)
        print("\n".join(lines))
        for m in missing:
            print(f"art_loop: piece {m} of card {a.card} has not reached the bar on this commit")
        return 1 if missing else 0
    except (OSError, ValueError, KeyError) as ex:
        print(f"art_loop: {ex}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    sys.exit(main())
