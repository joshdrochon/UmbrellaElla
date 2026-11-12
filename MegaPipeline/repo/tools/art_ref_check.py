#!/usr/bin/env python3
"""Hard gate: art made or placed by a card matches that card's own references (stdlib only).

Loads pipeline/art/references.json, takes the references that list the card in `cards`, and judges with
tools/art_judge.py against those only:
  --scene SHOT          a build screenshot or eval capture: art_check.py, screen_check.py and the key-art composition
                        judge (art_judge.py scene, similarity against the card's own scene references)
  --element ID FILE...  generated art for one judge element (ella-up-open, owl, owl-bolt, wind-zone, ...): the best
                        file must score at least the element's score_min against the card's references for it
Prints one line per check and the evidence line
  art_ref_check: PASS|FAIL card=<id> target=<scene|element:ID> score=<s> min=<m> refs=<hash12> commit=<sha> file=<name>
refs= is the first 12 hex of references.json's sha256 and commit= the HEAD it ran on, so tools/check_pr.py (rule
artref), kickoff's art gate and the card checks refuse a PASS made on another commit or an older or smaller
reference set. A FAIL is a failed build: regenerate (tools/assetgen.py image), rescale or reposition, run again; the
same FAIL twice raises NEEDS HUMAN. No human approves a look.
Usage: python3 tools/art_ref_check.py --card 0.10c --element wind-zone Art/Source/Scene/Raw/wind-*.png
       python3 tools/art_ref_check.py --card 0.10 --scene Saved/Screenshots/CAM_Eval_StyleFrame.png
Exit 0 = PASS, 1 = FAIL, 2 = usage (unknown card, a card with no references, an element the card has no refs for).
"""
import argparse
import io
import json
import os
import subprocess
import sys
from contextlib import redirect_stdout

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import art_check  # noqa: E402
import art_judge  # noqa: E402
import screen_check  # noqa: E402

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def head(root):
    try:
        return subprocess.run(["git", "-C", root, "rev-parse", "HEAD"], capture_output=True, text=True,
                              check=True).stdout.strip()[:12]
    except (OSError, subprocess.CalledProcessError):
        return "none"


def line(ok, card, target, score, smin, rh, commit, f):
    return (f"art_ref_check: {'PASS' if ok else 'FAIL'} card={card} target={target} score={score} min={smin} "
            f"refs={rh} commit={commit} file={os.path.basename(f)}")


def run(card, scene_shot=None, element_id=None, files=(), refs_path=art_judge.REFS, root=ROOT, commit=None):
    """(exit code, printed lines)."""
    refs = art_judge.load_refs(refs_path)
    rh = art_judge.refs_hash(refs_path)
    commit = commit or head(root)
    mine = art_judge.card_refs(refs, card)
    if not mine:
        return 2, [f"art_ref_check: card {card} has no references assigned in references.json: assign them first"]
    roots = [root, ROOT]
    out = []
    if scene_shot:
        only = mine & set(refs["scene"]["refs"])
        if not only:
            return 2, [f"art_ref_check: card {card} has no scene reference ({', '.join(refs['scene']['refs'])})"]
        style = os.path.join(root, "pipeline", "art", "style.json")
        with open(style, encoding="utf-8") as fh:
            st = json.load(fh)
        res = screen_check.check(scene_shot, screen_check.thresholds(style))
        view = scene_shot
        if res["bars"] != "none":
            view = screen_check.crop_view(scene_shot, res, os.path.splitext(scene_shot)[0] + "-view.png")
        af = art_check.evaluate(art_check.measure(view, st), st)
        out.append(f"  art_check: {'PASS' if not af else 'FAIL'}" + ("" if not af else " (" + "; ".join(af[:3]) + ")"))
        out.append("  " + screen_check.summary(dict(res, image=os.path.basename(scene_shot))))
        _, probs, score, sims = art_judge.scene(view, refs, roots, only)
        out += [f"  - {k}: {m}" for k, m in probs]
        ok = not af and res["pass"] and not probs
        out.append(line(ok, card, "scene", score, refs["scene"]["similarity_min"], rh, commit, scene_shot))
        return (0 if ok else 1), out
    el = refs["elements"].get(element_id)
    if not el:
        return 2, [f"art_ref_check: no judge element {element_id!r}"]
    only = mine & set(el["refs"])
    if not only:
        return 2, [f"art_ref_check: card {card} has no reference for element {element_id} ({', '.join(el['refs'])})"]
    _, rows, missing = art_judge.element(element_id, list(files), refs, roots, only)
    out += [f"  ! reference missing: {p}" for p in missing]
    best = max(rows, key=lambda r: r[1]) if rows else (files[0] if files else "none", 0.0, None)
    for f, sc, rid in rows:
        out.append(f"  {os.path.basename(f)} score={sc} closest={rid}")
    ok = bool(rows) and best[1] >= el["score_min"] and len(missing) < len(only)
    out.append(line(ok, card, f"element:{element_id}", best[1], el["score_min"], rh, commit, best[0]))
    return (0 if ok else 1), out


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--card", required=True)
    g = ap.add_mutually_exclusive_group(required=True)
    g.add_argument("--scene")
    g.add_argument("--element")
    ap.add_argument("files", nargs="*")
    ap.add_argument("--refs", default=art_judge.REFS)
    ap.add_argument("--root", default=ROOT)
    ap.add_argument("--commit")
    a = ap.parse_args(argv)
    if a.element and not a.files:
        ap.error("--element needs the generated files")
    try:
        rc, out = run(a.card, a.scene, a.element, a.files, a.refs, a.root, a.commit)
    except (OSError, ValueError, KeyError) as e:
        print(f"art_ref_check: {e}", file=sys.stderr)
        return 2
    print("\n".join(out))
    return rc


if __name__ == "__main__":
    sys.exit(main())
