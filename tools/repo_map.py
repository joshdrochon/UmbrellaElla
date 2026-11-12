#!/usr/bin/env python3
"""The repo map (docs/repo-map.md) against the repo. Stdlib only.

docs/repo-map.md names every folder an agent may touch. Its "Pipeline folders" section lists the folders the installer
ships; the other sections list game, team and local folders that may not exist yet. This tool:
  - lists every tracked top-level folder the map does not describe (the team's own folders), with its file count and
    main file types. tools/kickoff.py adds that list to every agent prompt (prompt_line)
  - finds map problems for tools/pipeline_check.py (kind repomap): a pipeline folder the map leaves out, or a
    "Pipeline folders" entry that does not exist. Team folders never fail it.
Pipeline folders: the top-level folders of the files the installer ships, plus their subfolders under NESTED. In a repo
the pipeline was installed into, the shipped files are the install record's (.pipeline-installed.json, else
MegaPipeline/manifest.json); without either, the tracked files under PIPELINE_TOPS (the top-level folders the installer
ships today), so a team folder never counts. tests/test_repo_map.py checks every tracked top-level folder of the source
repo is in the map, which catches a new pipeline top-level folder.

Usage: python3 tools/repo_map.py            list the folders the map does not describe
       python3 tools/repo_map.py --check    list map problems
Exit 0 = ok, 1 = problems (--check), 2 = no docs/repo-map.md.
"""
import argparse
import json
import os
import re
import subprocess
import sys
from collections import Counter

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MAP = "docs/repo-map.md"
CHECKED = "## Pipeline folders"
NESTED = (".claude", ".github", "docs", "evals", "pipeline", "tests", "tools")
INSTALLED = ".pipeline-installed.json"
MANIFEST = "MegaPipeline/manifest.json"
PIPELINE_TOPS = (".claude", ".github", "docs", "evals", "pipeline", "prompts", "tests", "tools")
PROMPT_HEAD = "Other folders in this repo (team files; read-only unless your card links them): "
ENTRY = re.compile(r"^- ((?:`[^`]+`(?:, )?)+):")


def tracked(root):
    p = subprocess.run(["git", "ls-files", "-z"], cwd=root, capture_output=True)
    return [f for f in p.stdout.decode("utf-8", "replace").split("\0") if f] if p.returncode == 0 else []


def read_map(root):
    try:
        with open(os.path.join(root, MAP), encoding="utf-8") as fh:
            return fh.read()
    except OSError:
        return None


def entries(text):
    """[(path, line number, checked)] for every list entry; checked = under the "Pipeline folders" heading."""
    out, checked = [], False
    for n, line in enumerate(text.splitlines(), 1):
        if line.startswith("## "):
            checked = line.startswith(CHECKED)
            continue
        m = ENTRY.match(line)
        if m:
            out += [(p, n, checked) for p in re.findall(r"`([^`]+)`", m.group(1))]
    return out


def described_tops(text):
    return {p.split("/")[0] for p, _, _ in entries(text)}


def shipped_files(root, files):
    for rel in (INSTALLED, MANIFEST):
        try:
            with open(os.path.join(root, rel), encoding="utf-8") as fh:
                got = json.load(fh).get("files")
        except (OSError, ValueError, AttributeError):
            continue
        if got:
            return sorted(got)
    return [f for f in files if "/" in f and f.split("/")[0] in PIPELINE_TOPS]


def pipeline_folders(paths):
    out = set()
    for f in paths:
        parts = f.split("/")
        if len(parts) > 1:
            out.add(parts[0] + "/")
        if len(parts) > 2 and parts[0] in NESTED:
            out.add(parts[0] + "/" + parts[1] + "/")
    return out


def exists_exact(root, rel):
    cur = root
    for part in [p for p in rel.split("/") if p]:
        try:
            if part not in os.listdir(cur):
                return False
        except OSError:
            return False
        cur = os.path.join(cur, part)
    return True


def problems(root, files=None):
    """[(where, why)]; [] while docs/repo-map.md is absent (AGENTS.md names it, so the path check catches that)."""
    text = read_map(root)
    if text is None:
        return []
    files = tracked(root) if files is None else files
    ents = entries(text)
    named = {p for p, _, _ in ents}
    out = []
    for folder in sorted(pipeline_folders(shipped_files(root, files)) - named):
        out.append((MAP, f"pipeline folder {folder} is not in the map; add one line: what it holds, who writes it"))
    for path, n, checked in ents:
        if checked and not exists_exact(root, path.rstrip("/")):
            out.append((f"{MAP}:{n}", f"{path} is listed under Pipeline folders but does not exist"))
    return out


def other_folders(root, files=None):
    """[(folder, file count, [(ext, count), ...])] for each tracked top-level folder the map does not describe."""
    text = read_map(root)
    if text is None:
        return []
    files = tracked(root) if files is None else files
    known = described_tops(text)
    by_top = {}
    for f in files:
        top, sep, rest = f.partition("/")
        if sep and top not in known:
            by_top.setdefault(top, []).append(rest)
    out = []
    for top in sorted(by_top, key=str.lower):
        exts = Counter(os.path.splitext(f)[1].lower() or "(no ext)" for f in by_top[top])
        out.append((top + "/", len(by_top[top]), exts.most_common(3)))
    return out


def describe(folder, count, exts):
    return f"{folder} ({count} file{'s' if count != 1 else ''}: " + ", ".join(f"{e} {n}" for e, n in exts) + ")"


def prompt_line(root):
    """The kickoff prompt line naming the team's folders, or "" when there are none."""
    found = other_folders(root)
    return PROMPT_HEAD + "; ".join(describe(*f) for f in found) + "." if found else ""


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--root", default=ROOT)
    ap.add_argument("--check", action="store_true", help="list map problems (pipeline_check kind repomap)")
    a = ap.parse_args(argv)
    if read_map(a.root) is None:
        print(f"repo_map: no {MAP}")
        return 2
    if a.check:
        probs = problems(a.root)
        for where, why in probs:
            print(f"[repomap] {where}: {why}")
        print(f"repo_map: {len(probs)} problem(s)")
        return 1 if probs else 0
    found = other_folders(a.root)
    for f in found:
        print(describe(*f))
    print(f"repo_map: {len(found)} folder(s) not in {MAP}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
