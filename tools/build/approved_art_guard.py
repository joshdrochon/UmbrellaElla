#!/usr/bin/env python3
"""Approved art stays in the build (lead order, Nov 13 20:05).

  python3 tools/build/approved_art_guard.py check --base <rev> [--head <rev>] [--approvals <json>]
  python3 tools/build/approved_art_guard.py list [--rev <rev>]       # which uassets ship which approval

Why: Josh approved the Ella idle grid (pipeline/art/approvals.json); a lane later re-imported a re-toned sheet over the
same texture (d550580c, feca5adb) and the approved art left the build without anyone deciding it.

Which textures ship an approval (read at base and head):
  * pipeline/art/standins.json rows whose piece or sha256 is the approval's -> their visual id -> the slot in
    docs/build/art-inventory.csv -> Content/<slot>_PH.uasset (and the passed name <slot>.uasset, which wins when it exists);
  * ALIASES below (approved pieces with no standins row; keeper-idle -> keeper:body-hover-flap, lead order);
  * any Content/UmbrellaElla/Art uasset whose embedded import record (AssetImportData "FileMD5") is the md5 of an
    approved file.
A merge base..head FAILS when it
  1. deletes such a uasset, or changes / adds one whose embedded FileMD5 is not the md5 of an approved file in head
     (re-importing the approved bytes passes; new bytes pass only with an approvals.json entry in head for them);
  2. points such a slot's standins.json row at bytes that are not approved, or changes / deletes an approved file;
  3. adds code (Source/, Config/) that tints, recolours, hides or swaps such a slot: an added line with a tint/hide/swap
     word within 3 lines of the slot's texture name, visual id or piece id; unless approvals.json in head has a new
     entry for that piece.
The uasset bytes come from the local LFS store (no download); a uasset it cannot read fails (fail closed).
"""
import argparse
import csv
import hashlib
import io
import json
import os
import re
import subprocess
import sys

APPROVALS = "pipeline/art/approvals.json"
STANDINS = "pipeline/art/standins.json"
INVENTORY = "docs/build/art-inventory.csv"
CONTENT_ART = "Content/UmbrellaElla/Art/"
# Approved pieces that ship through a slot with no standins.json row (lead order, Nov 13 20:05).
ALIASES = {"keeper-idle": ["keeper:body-hover-flap"]}
CODE_PREFIXES = ("Source/", "Config/")
CODE_WORDS = re.compile(
    r"tint|colou?r|hidden|\bhide|visib|opacity|alpha|swap|replace|override|SetMaterial|SetTexture|darken|desaturat"
    r"|silhouette|brightness|multiply|Emissive", re.I)
CODE_WINDOW = 3
FILE_MD5 = re.compile(rb'"FileMD5"\s*:\s*"([0-9a-f]{32})"')
LFS_HEAD = b"version https://git-lfs"


def git(root, *args, binary=False, check=True):
    p = subprocess.run(["git", "-C", root] + list(args), capture_output=True)
    if check and p.returncode:
        raise RuntimeError("git %s: %s" % (" ".join(args), p.stderr.decode(errors="replace").strip()))
    return p.stdout if binary else p.stdout.decode("utf-8", errors="replace")


def blob(root, rev, path):
    """File bytes at rev (LFS pointers resolved from the local store), or None if absent / unreadable."""
    p = subprocess.run(["git", "-C", root, "show", "%s:%s" % (rev, path)], capture_output=True)
    if p.returncode:
        return None
    data = p.stdout
    if not data.startswith(LFS_HEAD):
        return data
    m = re.search(rb"oid sha256:([0-9a-f]{64})", data)
    if not m:
        return None
    oid = m.group(1).decode()
    common = git(root, "rev-parse", "--path-format=absolute", "--git-common-dir").strip()
    local = os.path.join(common, "lfs", "objects", oid[:2], oid[2:4], oid)
    if os.path.isfile(local):
        with open(local, "rb") as fh:
            return fh.read()
    s = subprocess.run(["git", "-C", root, "lfs", "smudge", "--skip"], input=data, capture_output=True)
    out = s.stdout
    return None if s.returncode or out.startswith(LFS_HEAD) else out


def load_json(root, rev, path, default):
    data = blob(root, rev, path)
    if data is None:
        return default
    try:
        return json.loads(data.decode("utf-8"))
    except ValueError:
        return default


def approvals(root, rev, override=None):
    if override:
        with open(override, encoding="utf-8") as fh:
            return json.load(fh).get("approvals", [])
    return load_json(root, rev, APPROVALS, {}).get("approvals", [])


def approved_md5s(root, rev, entries, standins):
    """{md5: piece} of the approved bytes found at rev (the approval's file or any standins copy with that sha256)."""
    out = {}
    for a in entries:
        paths = [a.get("file")] + [r.get("copy") for r in standins.values() if r.get("sha256") == a.get("sha256")]
        for path in filter(None, paths):
            data = blob(root, rev, path)
            if data is not None and hashlib.sha256(data).hexdigest() == a.get("sha256"):
                out[hashlib.md5(data).hexdigest()] = a["piece"]
                break
    return out


def slot_paths(root, rev):
    """visual id -> [Content/.../T_X_PH.uasset, Content/.../T_X.uasset]."""
    data = blob(root, rev, INVENTORY)
    out = {}
    if data is None:
        return out
    for r in csv.DictReader(io.StringIO(data.decode("utf-8"))):
        slot = (r.get("slot") or "").strip()
        if slot.startswith("/Game/"):
            rel = "Content/" + slot[len("/Game/"):]
            out[r["visual"]] = [rel + "_PH.uasset", rel + ".uasset"]
    return out


def embedded_md5(data):
    m = FILE_MD5.search(data or b"")
    return m.group(1).decode() if m else None


def guarded(root, rev, entries, md5s):
    """{uasset path: {"piece", "tokens"}} for every texture that ships an approved piece at rev."""
    standins = load_json(root, rev, STANDINS, {}).get("slots", {})
    slots = slot_paths(root, rev)
    out = {}

    def add(path, piece, visual):
        name = os.path.basename(path)[: -len(".uasset")]
        base = name[:-3] if name.endswith("_PH") else name
        g = out.setdefault(path, {"piece": piece, "tokens": set()})
        g["tokens"].update(t for t in (base, visual, piece) if t)

    for a in entries:
        piece = a.get("piece")
        visuals = [v for v, r in standins.items() if r.get("piece") == piece or r.get("sha256") == a.get("sha256")]
        visuals += ALIASES.get(piece, [])
        for v in visuals:
            for path in slots.get(v, []):
                add(path, piece, v)
    if md5s:
        names = git(root, "ls-tree", "-r", "--name-only", rev, "--", CONTENT_ART).split("\n")
        for path in (n for n in names if n.endswith(".uasset")):
            if path in out:
                continue
            md5 = embedded_md5(blob(root, rev, path))
            if md5 in md5s:
                add(path, md5s[md5], None)
    return out


def changes(root, base, head):
    out = []
    for line in git(root, "diff", "--name-status", "--no-renames", base, head).splitlines():
        parts = line.split("\t")
        if len(parts) >= 2:
            out.append((parts[0][0], parts[-1]))
    return out


def code_hits(root, base, head, tokens_by_piece):
    """[(file, line no, text, piece)] for added code lines that tint/hide/swap a guarded slot."""
    diff = git(root, "diff", "-U%d" % CODE_WINDOW, base, head, "--", *CODE_PREFIXES)
    hits = []
    path, hunk, lineno = None, [], 0

    def flush():
        for i, (n, kind, text) in enumerate(hunk):
            if kind != "+" or not CODE_WORDS.search(text):
                continue
            near = " ".join(t for _, _, t in hunk[max(0, i - CODE_WINDOW): i + CODE_WINDOW + 1])
            for piece, toks in tokens_by_piece.items():
                if any(t in near for t in toks):
                    hits.append((path, n, text.strip(), piece))
                    break

    for line in diff.splitlines():
        if line.startswith("+++ "):
            flush(); hunk = []
            path = line[6:] if line.startswith("+++ b/") else None
        elif line.startswith("@@"):
            flush(); hunk = []
            m = re.search(r"\+(\d+)", line)
            lineno = int(m.group(1)) if m else 0
        elif path and line[:1] in ("+", " ", "-") and not line.startswith("--- "):
            kind = line[:1]
            hunk.append((lineno, kind, line[1:]))
            if kind != "-":
                lineno += 1
    flush()
    return hits


def check(root, base, head, override=None):
    base_entries = approvals(root, base, override)
    head_entries = approvals(root, head, override)
    pieces = {a["piece"]: a for a in base_entries}
    pieces.update({a["piece"]: a for a in head_entries})
    entries = list(pieces.values())
    base_standins = load_json(root, base, STANDINS, {}).get("slots", {})
    head_standins = load_json(root, head, STANDINS, {}).get("slots", {})
    base_md5 = approved_md5s(root, base, entries, base_standins)
    head_md5 = approved_md5s(root, head, head_entries, head_standins)
    head_sha = {a.get("sha256") for a in head_entries}
    base_keys = {(a.get("piece"), a.get("sha256")) for a in base_entries}
    newly_approved = {a["piece"] for a in head_entries if (a.get("piece"), a.get("sha256")) not in base_keys}

    guard = guarded(root, base, entries, base_md5)
    for path, g in guarded(root, head, entries, head_md5).items():
        guard.setdefault(path, g)["tokens"] |= g["tokens"]
    problems = []
    changed = changes(root, base, head)
    for status, path in changed:
        if path in guard:
            piece = guard[path]["piece"]
            if status == "D":
                problems.append("%s: deletes the texture that ships approved %s" % (path, piece))
                continue
            data = blob(root, head, path)
            if data is None:
                problems.append("%s: cannot read its bytes at head (LFS object missing locally); approved %s unverified" % (path, piece))
                continue
            md5 = embedded_md5(data)
            if md5 not in head_md5:
                problems.append("%s: imports bytes md5 %s, not the approved %s (re-import the approved file, or Josh adds an "
                                "approvals.json entry for the new bytes)" % (path, md5 or "unknown", piece))
    # standins rows of guarded slots, and the approved files themselves
    for visual, row in head_standins.items():
        old = base_standins.get(visual)
        if old and old.get("sha256") in {a.get("sha256") for a in entries} and row.get("sha256") != old.get("sha256") \
                and row.get("sha256") not in head_sha:
            problems.append("%s row %s: now ships sha256 %s, not the approved %s" % (STANDINS, visual, row.get("sha256"), old.get("piece")))
    approved_files = {a.get("file"): a for a in entries if a.get("file")}
    approved_files.update({r.get("copy"): r for r in base_standins.values()
                           if r.get("copy") and r.get("sha256") in {a.get("sha256") for a in entries}})
    for status, path in changed:
        if path in approved_files and status in ("M", "D", "T"):
            data = blob(root, head, path)
            if data is None or hashlib.sha256(data).hexdigest() not in head_sha:
                problems.append("%s: changes or deletes an approved file" % path)
    tokens = {}
    for g in guard.values():
        tokens.setdefault(g["piece"], set()).update(g["tokens"])
    for path, n, text, piece in code_hits(root, base, head, tokens):
        if piece not in newly_approved:
            problems.append("%s:%d: adds code that may tint, hide or swap approved %s: %s" % (path, n, piece, text[:120]))
    return guard, problems


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    sub = ap.add_subparsers(dest="cmd", required=True)
    c = sub.add_parser("check"); c.add_argument("--base", required=True); c.add_argument("--head", default="HEAD")
    c.add_argument("--approvals", help="approvals json to use for both sides (history replays)"); c.add_argument("--root", default=".")
    l = sub.add_parser("list"); l.add_argument("--rev", default="HEAD"); l.add_argument("--root", default=".")
    a = ap.parse_args(argv)
    root = os.path.abspath(a.root)
    if a.cmd == "list":
        entries = approvals(root, a.rev)
        st = load_json(root, a.rev, STANDINS, {}).get("slots", {})
        for path, g in sorted(guarded(root, a.rev, entries, approved_md5s(root, a.rev, entries, st)).items()):
            print("%s\t%s" % (g["piece"], path))
        return 0
    guard, problems = check(root, a.base, a.head, a.approvals)
    if problems:
        print("APPROVED_ART FAIL (%d)" % len(problems))
        for p in problems:
            print("FAIL " + p)
        return 1
    print("APPROVED_ART PASS: %d approved texture(s) guarded, none replaced, recoloured or hidden" % len(guard))
    return 0


if __name__ == "__main__":
    sys.exit(main())
