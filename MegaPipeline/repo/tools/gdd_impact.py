#!/usr/bin/env python3
"""What a GDD revision (or a feature-manifest change) touches. Stdlib only.

Compares two GDD snapshots (docs/gdd/GDD-<rev>.md) or two feature manifests (docs/feature-manifest.json shape):
  added / removed      IDs in one and not the other (feature IDs, QA-, T- and DEC- IDs)
  changed              IDs whose GDD lines (or manifest record) differ
  status               feature IDs whose status changed (old -> new)
Then lists every line in the repo that cites one of those IDs: Day-0 cards, test-map rows, presets, manifest
records and doc lines (docs/gdd/ itself is skipped: snapshots are never edited).

The first output line is the one check_pr.py looks for in a PR's "## GDD impact" section:
  gdd_impact old=<rev> new=<rev> added=N removed=N changed=N status=N cited=N

Usage:
  python3 tools/gdd_impact.py docs/gdd/GDD-B1.0.md docs/gdd/GDD-1.3.md
  git show origin/main:docs/feature-manifest.json > /tmp/old.json && python3 tools/gdd_impact.py /tmp/old.json docs/feature-manifest.json
Exit 0 always on readable input (the list is information); 2 = unreadable input.
"""
import argparse
import json
import os
import re
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FEATURE_RE = r"(?:(?:CORE|UMB|COM|SURV|WIND|OWL|HAZ|FLOW|END|NAR|VFX|DEF|ANIM|BG|CAM|MOVE|ART)-\d{2}|QA-BASE)"
FEATURE_ID = re.compile(r"(?<![\w-])" + FEATURE_RE + r"(?![\w-])")
ANY_ID = re.compile(r"(?<![\w-])(?:" + FEATURE_RE + r"|QA-\d{2}|T-\d{2}|DEC-\d{2})(?![\w-])")
STATUSES = ("CONFIRMED", "APPROVED_P0", "APPROVED_P1", "PROPOSED", "EXPERIMENT", "DEFERRED", "OPEN", "REJECTED")
REVISION = re.compile(r"^\|\s*Revision\s*\|\s*([^|]+?)\s*\|", re.M)
CITE_DIRS = ("docs/", "pipeline/", ".github/", "prompts/")
CITE_FILES = ("AGENTS.md", "CLAUDE.md", "README.md")
CITE_EXT = (".md", ".json", ".csv", ".yml", ".yaml", ".txt")
CITE_SKIP = ("docs/gdd/",)


def read(path):
    with open(path, encoding="utf-8") as fh:
        return fh.read()


def body(text):
    """The GDD text below the read-only header (everything after the first '---' line)."""
    parts = re.split(r"^---\s*$", text, maxsplit=1, flags=re.M)
    return parts[1] if len(parts) == 2 else text


# A GDD section that opens with this sentence is authoring guidance the GDD itself excludes from the reviewed build
# body (GDD SH1.0 section 12 "Pipeline key and export": "Authoring guidance only. Exclude this guidance and
# illustrative records from the reviewed build-body export"). IDs it mentions as examples (QA-BASE) are not citations.
GUIDANCE_MARK = re.compile(r"^Authoring guidance only\b")
HEADING = re.compile(r"^(#+)\s")


def cited_body(text):
    """body(text) without the sections the GDD marks as authoring guidance (GUIDANCE_MARK on the first text line)."""
    lines = body(text).splitlines()
    out, skip_level, i = [], None, 0
    while i < len(lines):
        line = lines[i]
        h = HEADING.match(line)
        if h:
            level = len(h.group(1))
            if skip_level is not None and level <= skip_level:
                skip_level = None
            if skip_level is None:
                nxt = next((x for x in lines[i + 1:] if x.strip()), "")
                if GUIDANCE_MARK.match(nxt.strip()):
                    skip_level = level
        if skip_level is None:
            out.append(line)
        i += 1
    return "\n".join(out) + "\n"


ROW_ID_CELL = re.compile(r"^\[[^\]]*\]$")


def idless_rows(text):
    """[(placeholder cell, behavior, status word or None)] for requirement-table rows whose first cell is a bracketed
    placeholder ([pending], [unassigned]) instead of a Rule ID (GDD SH1.0 prints 7 approved ones and 5 OPEN ones)."""
    out, head = [], None
    for line in body(text).splitlines():
        if not line.strip().startswith("|"):
            head = None
            continue
        cells = [c.strip() for c in line.strip().strip("|").split("|")]
        if head is None:
            head = [c.lower() for c in cells]
            continue
        if set(cells[0]) <= set("-: ") or not head or head[0] != "rule id":
            continue
        if ROW_ID_CELL.match(cells[0]):
            status = next((w for w in STATUSES if re.search(r"\b" + w + r"\b", cells[-1])), None)
            out.append((cells[0], " | ".join(cells[1:-1]), status))
    return out


def revision(text):
    m = REVISION.search(text)
    return m.group(1).strip() if m else "?"


def snapshot_ids(text):
    """{id: sorted list of the GDD lines that mention it}."""
    out = {}
    for line in body(text).splitlines():
        norm = re.sub(r"\s+", " ", line).strip()
        for m in ANY_ID.finditer(line):
            out.setdefault(m.group(0), set()).add(norm)
    return {k: sorted(v) for k, v in out.items()}


def snapshot_statuses(text):
    """{feature id: status cell} from table rows whose first cell is the ID and last cell holds a status word."""
    out = {}
    for line in body(text).splitlines():
        if not line.strip().startswith("|"):
            continue
        cells = [c.strip() for c in line.strip().strip("|").split("|")]
        if cells and FEATURE_ID.fullmatch(cells[0]) and cells[0] not in out:
            last = cells[-1]
            if any(re.search(r"\b" + s + r"\b", last, re.I) for s in STATUSES):
                out[cells[0]] = last
    return out


def manifest_view(data):
    """(revision, {id: record json}, {id: status}) from a manifest dict."""
    recs = {f.get("feature_id"): f for f in data.get("features", []) if isinstance(f, dict)}
    view = {k: json.dumps(v, sort_keys=True) for k, v in recs.items()}
    for k, v in recs.items():  # QA ids are cited through records too
        for t in v.get("tests") or []:
            view.setdefault(t, "")
    return data.get("manifest_version") or data.get("gdd_revision") or "?", view, {k: v.get("status") for k, v in recs.items()}


def load(path):
    text = read(path)
    if path.endswith(".json"):
        rev, view, status = manifest_view(json.loads(text))
        return rev, view, status
    return revision(text), snapshot_ids(text), snapshot_statuses(text)


def diff(old, new):
    """old/new: (rev, {id: lines}, {id: status}) -> dict with added, removed, changed, status."""
    _, oi, os_ = old
    _, ni, ns = new
    added = sorted(set(ni) - set(oi))
    removed = sorted(set(oi) - set(ni))
    changed = sorted(k for k in set(oi) & set(ni) if oi[k] != ni[k])
    status = sorted((k, os_.get(k), ns.get(k)) for k in set(os_) | set(ns) if os_.get(k) != ns.get(k))
    return {"added": added, "removed": removed, "changed": changed, "status": status}


def touched(d):
    return sorted(set(d["added"]) | set(d["removed"]) | set(d["changed"]) | {s[0] for s in d["status"]})


def repo_files(root):
    out = []
    for f in CITE_FILES:
        if os.path.isfile(os.path.join(root, f)):
            out.append(f)
    for d in CITE_DIRS:
        for base, dirs, files in os.walk(os.path.join(root, d)):
            dirs[:] = [x for x in dirs if not x.startswith(".") or d == ".github/"]
            for name in files:
                rel = os.path.relpath(os.path.join(base, name), root).replace(os.sep, "/")
                if rel.endswith(CITE_EXT) and not rel.startswith(CITE_SKIP):
                    out.append(rel)
    return sorted(set(out))


RECORD_FILES = {"docs/feature-manifest.json": ("features", "feature_id", "manifest record"),
                "pipeline/qa/presets.json": ("presets", "id", "preset")}


def record_citations(root, rel, want):
    """One citation per JSON record (feature or preset) that names a touched ID anywhere in it."""
    key, idk, label = RECORD_FILES[rel]
    try:
        data = json.loads(read(os.path.join(root, rel)))
    except (OSError, ValueError):
        return []
    out = []
    for i, r in enumerate(data.get(key, [])):
        hit = sorted({m.group(0) for m in ANY_ID.finditer(json.dumps(r))} & want)
        if hit:
            out.append((rel, None, f"{label} {r.get(idk)}", hit, json.dumps(r.get("name", ""))))
    return out


def citations(root, ids):
    """[(path, line no, kind, ids on the line, text)] for every repo line citing one of ids."""
    want = set(ids)
    out = []
    if not want:
        return out
    for rel in repo_files(root):
        if rel in RECORD_FILES:
            out += record_citations(root, rel, want)
            continue
        try:
            lines = read(os.path.join(root, rel)).splitlines()
        except OSError:
            continue
        for n, line in enumerate(lines, 1):
            hit = sorted({m.group(0) for m in ANY_ID.finditer(line)} & want)
            if not hit:
                continue
            kind = "doc"
            cells = [c.strip() for c in line.strip().strip("|").split("|")]
            if rel == "pipeline/day0-cards.md" and re.fullmatch(r"0\.\d+[a-z]?", cells[0] if cells else ""):
                kind = f"day0 card {cells[0]}"
            elif rel == "pipeline/qa/test-map.md" and line.strip().startswith("|"):
                kind = f"test-map row {cells[0]}"
            elif rel == "docs/decisions.md" and line.strip().startswith("|"):
                kind = f"decision row {cells[0]}"
            out.append((rel, n, kind, hit, line.strip()))
    return out


def report(old_path, new_path, root=ROOT):
    old, new = load(old_path), load(new_path)
    d = diff(old, new)
    ids = touched(d)
    cites = citations(root, ids)
    lines = [f"gdd_impact old={old[0]} new={new[0]} added={len(d['added'])} removed={len(d['removed'])} "
             f"changed={len(d['changed'])} status={len(d['status'])} cited={len(cites)}"]
    lines.append("added: " + (", ".join(d["added"]) or "none"))
    lines.append("removed: " + (", ".join(d["removed"]) or "none"))
    lines.append("changed: " + (", ".join(d["changed"]) or "none"))
    lines.append("status: " + (", ".join(f"{k} {a} -> {b}" for k, a, b in d["status"]) or "none"))
    lines.append("cited by:" if cites else "cited by: none")
    for rel, n, kind, hit, text in cites:
        where = rel if n is None else f"{rel}:{n}"
        lines.append(f"  {where} [{kind}] {','.join(hit)}: {text[:100]}")
    return lines, d


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("old")
    ap.add_argument("new")
    ap.add_argument("--root", default=ROOT)
    a = ap.parse_args(argv)
    try:
        lines, _ = report(a.old, a.new, a.root)
    except (OSError, ValueError) as e:
        print(f"gdd_impact: cannot read input: {e}")
        return 2
    print("\n".join(lines))
    return 0


if __name__ == "__main__":
    sys.exit(main())
