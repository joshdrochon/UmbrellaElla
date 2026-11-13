#!/usr/bin/env python3
"""Pass-record verifier (Josh, Nov 12): a pass in pipeline/art/critic/<piece>.json counts only when the panel's raw
evidence next to it says so. Stdlib only.

  art_pass_verify.py check [--base REF] [--no-remeasure]   FAIL lines for every record that says passed but does not verify
  art_pass_verify.py newly-passed BASE                     pieces whose newest record is a verified pass that BASE lacks
  art_pass_verify.py summary                               one line: verified passes

A record that says passed (verdict ours or same, checks true) must have, in pipeline/art/critic/<piece>/<round>/:
manifest.json (its sha256 is the record's `manifest`), every file the manifest lists with the listed sha256 and no
file it does not list, each panel session's raw answer text, the packet images it judged and its key. Then the verdict
is derived again from those raw answers with the parser tools/art_loop.py uses (votes, calibration, the pairs every
piece needs) and must equal the record; the shipped image's sha256 must equal the record's and (newest record) the
bytes on disk; the deterministic checks are measured again on the shipped bytes (art_ref_check and the rest). With
--base, a record that changed since BASE must come with changed evidence files. A hand-written record has none of this.
The gate also re-runs the blind panel on each newly passed piece (art_loop.py gate-rerun): that run is the proof the
panel really ran, since someone who writes the record can write matching evidence too.
Exit 0 = every claimed pass verifies, 1 = a FAIL line.
"""
import glob
import json
import os
import subprocess
import sys

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
sys.path.insert(0, os.path.join(ROOT, "tools"))
import art_loop  # noqa: E402

CRITIC = art_loop.CRITIC_DIR


def claims_pass(rec):
    return isinstance(rec, dict) and rec.get("verdict") in ("ours", "same") and bool(rec.get("checks"))


def load_piece_records(root):
    """{piece: [records]} from the tracked piece files."""
    out = {}
    for path in sorted(glob.glob(os.path.join(root, CRITIC, "*.json"))):
        try:
            with open(path, encoding="utf-8") as fh:
                data = json.load(fh)
        except (OSError, ValueError):
            continue
        if isinstance(data, dict) and data.get("id"):
            out[data["id"]] = [r for r in data.get("records", []) if isinstance(r, dict)]
    return out


def verify_record(root, piece, rec, newest=True, remeasure=True):
    """Problems (empty = the record verifies) for one record that says passed. A record that does not say passed has
    nothing to verify."""
    if not claims_pass(rec):
        return []
    rnd = rec.get("round")
    ev_rel = rec.get("evidence") or ""
    want = f"{CRITIC}/{piece}/{rnd}"
    if not rec.get("manifest") or not ev_rel:
        return ["says passed but has no panel evidence (manifest): a record is written only by the panel run"]
    if ev_rel != want:
        return [f"evidence folder {ev_rel!r} is not {want}"]
    ev = os.path.join(root, ev_rel)
    mp = os.path.join(ev, "manifest.json")
    if not os.path.isfile(mp):
        return [f"evidence {ev_rel}/manifest.json is missing"]
    if art_loop.file_sha256(mp) != rec["manifest"]:
        return [f"{ev_rel}/manifest.json does not hash to the record's manifest {rec['manifest'][:12]}"]
    try:
        with open(mp, encoding="utf-8") as fh:
            man = json.load(fh)
    except ValueError:
        return [f"{ev_rel}/manifest.json is not JSON"]
    probs = []
    listed = man.get("files") or {}
    on_disk = {}
    for dirpath, _, names in os.walk(ev):
        for n in names:
            full = os.path.join(dirpath, n)
            on_disk[art_loop.rel_to(full, ev)] = full
    on_disk.pop("manifest.json", None)
    for f, sha in sorted(listed.items()):
        if f not in on_disk:
            probs.append(f"evidence file {f} is missing")
        elif art_loop.file_sha256(on_disk[f]) != sha:
            probs.append(f"evidence file {f} changed after the panel (sha256 differs from the manifest)")
    for f in sorted(set(on_disk) - set(listed)):
        probs.append(f"evidence file {f} is not in the manifest")
    if probs:
        return probs
    names = man.get("sessions") or []
    for n in names:
        for f in (f"sessions/{n}.answer.md", f"keys/{n}.key.json", f"packets/{n}/prompt.md"):
            if f not in listed:
                probs.append(f"session {n}: {f} is not in the evidence")
        if not any(k.startswith(f"packets/{n}/") and k.lower().endswith(".png") for k in listed):
            probs.append(f"session {n}: no packet images in the evidence")
    if probs:
        return probs
    if man.get("prompt") != rec.get("prompt") or not man.get("prompt"):
        probs.append("the record's prompt id differs from the manifest's")
    if (man.get("piece"), man.get("round")) != (piece, rnd):
        probs.append("the manifest is for another piece or round")
    try:
        got, _ = art_loop.rederive(root, ev)
    except (OSError, ValueError, KeyError) as ex:
        return probs + [f"the raw answers cannot be read again ({ex})"]
    for k in ("verdict", "pairs", "panel", "calibration", "missing"):
        if got[k] != rec.get(k):
            probs.append(f"{k} re-derived from the raw critic answers is {got[k]!r}, the record says {rec.get(k)!r}")
    if sorted(rec.get("critic_sessions") or []) != got["sessions"]:
        probs.append("the record's critic sessions are not the sessions in the evidence")
    # what a pass needs, from the evidence itself
    kinds = {c.split(":", 1)[0] for c in man.get("required") or []}
    need = {"reference", "quality_bar"} | ({"motion"} if man.get("sheet") else set()) | \
        ({"context"} if piece != "scene" else set())
    if need - kinds:
        probs.append(f"the panel did not judge {', '.join(sorted(need - kinds))}")
    if not art_loop.panel_passed(dict(got, checks=rec.get("checks"), results=man.get("results"), combos=man["required"])):
        probs.append("the raw answers do not make a unanimous calibrated panel pass")
    for c in art_loop.CHECKS:
        if (man.get("results") or {}).get(c) != "pass":
            probs.append(f"the manifest has no PASS for {c}")
    shipped = man.get("shipped") or {}
    if shipped.get("sha256") != rec.get("files") or shipped.get("file") != rec.get("file"):
        probs.append("the record's image hash is not the one the panel judged")
    if newest:
        full = os.path.join(root, rec.get("file") or "")
        if not rec.get("file") or rec["file"].startswith("..") or not os.path.isfile(full):
            probs.append(f"the shipped image {rec.get('file')!r} is missing")
        elif art_loop.content_sha(full) != rec.get("files"):
            probs.append(f"{rec['file']} changed after its panel (sha256 differs from the record)")
        elif remeasure:
            try:
                ok, _, lines, results = art_loop.measure(root, rec.get("card") or "", piece, full)
            except (OSError, ValueError, KeyError) as ex:
                return probs + [f"the checks could not be measured again ({ex}); fails closed"]
            if results != man.get("results") or not ok:
                bad = [c for c in art_loop.CHECKS if results.get(c) != "pass"]
                probs.append("measured again on the shipped bytes, " + (", ".join(bad) or "the checks differ from the manifest")
                             + " do not pass")
    return probs


def verified_pieces(root, records=None, remeasure=False):
    """Pieces whose newest record says passed and verifies."""
    done = set()
    for piece, recs in (records if records is not None else load_piece_records(root)).items():
        if recs and claims_pass(recs[-1]) and not verify_record(root, piece, recs[-1], True, remeasure):
            done.add(piece)
    return done


def git(root, *args):
    p = subprocess.run(["git", "-C", root] + list(args), capture_output=True, text=True)
    return p.returncode, p.stdout


def base_records(root, base, piece):
    rc, out = git(root, "show", f"{base}:{CRITIC}/{piece}.json")
    if rc != 0:
        return []
    try:
        return [r for r in json.loads(out).get("records", []) if isinstance(r, dict)]
    except ValueError:
        return []


def changed_without_evidence(root, base, piece, recs):
    """A record that says passed and is new or different since `base` must have changed its evidence files."""
    old = {(r.get("card"), r.get("round")): r for r in base_records(root, base, piece)}
    out = []
    for r in recs:
        if not claims_pass(r) or old.get((r.get("card"), r.get("round"))) == r:
            continue
        ev = r.get("evidence") or f"{CRITIC}/{piece}/{r.get('round')}"
        rc, names = git(root, "diff", "--name-only", base, "--", ev)
        rc2, untracked = git(root, "ls-files", "--others", "--exclude-standard", "--", ev)
        if not (names.strip() or untracked.strip()):
            out.append(f"{piece} round {r.get('round')}: the record changed but its evidence files ({ev}) did not")
    return out


def check(root, base=None, remeasure=True):
    """FAIL lines for every record that says passed but does not verify."""
    lines = []
    for piece, recs in load_piece_records(root).items():
        for i, r in enumerate(recs):
            for p in verify_record(root, piece, r, i == len(recs) - 1, remeasure):
                lines.append(f"FAIL art_pass_verify: {piece} round {r.get('round')}: {p}")
        if base:
            lines += [f"FAIL art_pass_verify: {p}" for p in changed_without_evidence(root, base, piece, recs)]
    return lines


def newly_passed(root, base, remeasure=False):
    out = []
    for piece in sorted(verified_pieces(root, remeasure=remeasure)):
        new = load_piece_records(root)[piece][-1]
        old = base_records(root, base, piece)
        if not (old and old[-1] == new):
            out.append(piece)
    return out


def main(argv=None):
    a = list(sys.argv[1:] if argv is None else argv)
    root = ROOT
    if "--root" in a:
        i = a.index("--root")
        root = os.path.abspath(a[i + 1])
        del a[i:i + 2]
    cmd = a[0] if a else "check"
    if cmd == "check":
        base = a[a.index("--base") + 1] if "--base" in a else None
        lines = check(root, base, "--no-remeasure" not in a)
        print("\n".join(lines))
        print(f"art_pass_verify: {'FAIL' if lines else 'PASS'} ({len(verified_pieces(root))} verified passes, "
              f"{len(lines)} problems)")
        return 1 if lines else 0
    if cmd == "newly-passed" and len(a) > 1:
        print("\n".join(newly_passed(root, a[1])))
        return 0
    if cmd == "summary":
        print(f"art_pass_verify: verified passes: {', '.join(sorted(verified_pieces(root))) or 'none'}")
        return 0
    print(__doc__)
    return 2


if __name__ == "__main__":
    sys.exit(main())
