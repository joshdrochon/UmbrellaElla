#!/usr/bin/env python3
"""Practice mode for test repos. Stdlib only.

A committed `.pipeline-practice` file at the repo root marks a practice repo (`tools/kickoff.sh --practice` writes
and commits it). In a practice repo:
  - D39 is lifted: cards may build game files (Source/, Content/, Config/, the .uproject) before the jam start, and
    `submission_check.py assets` does not apply the contest-start date (Official Rules 7(h) binds the team repo only);
  - the submission is hard-blocked: `submission_check.py` zip (final, not the G1-G3 gate zips), page, signoff,
    files --final, devlog --published, footage --final, prejam and declaration exit 1; `check_card.py --gate-record`
    fails a G4 record; `pipeline_check.py --release` fails; the agent hook blocks every `butler` command;
  - `status_board.py` prints PRACTICE at the top.
The marker never belongs on the team repo: `pipeline_check.py` fails when it exists and the repo is the real one
(origin URL or $GITHUB_REPOSITORY names gates.json `practice.real_repo`), so CI on the real repo goes red.

  python3 tools/practice.py status      prints `practice=yes|no real_repo=yes|no`; exit 1 if the marker is on the real repo
"""
import json
import os
import re
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
MARKER = ".pipeline-practice"
DEFAULT_REAL = "RickTheBuilder/GameJam2026"
MARKER_TEXT = ("Practice repo (tools/practice.py). D39 is lifted here: cards may build game files before the jam start.\n"
               "Submission, upload and G4 are blocked. Never commit this file to the team repo: CI fails there.\n")
BLOCK_LINE = ("PRACTICE: this is a practice repo ({marker}); {what} is blocked here. The submission, every upload and G4 "
              "happen only on the team repo.")


def config(root=ROOT):
    try:
        with open(os.path.join(root, "pipeline", "agent-ops", "gates.json"), encoding="utf-8") as fh:
            return json.load(fh).get("practice") or {}
    except (OSError, ValueError):
        return {}


def real_slug(root=ROOT):
    return (config(root).get("real_repo") or DEFAULT_REAL).strip().lower()


def is_practice(root=ROOT):
    return os.path.isfile(os.path.join(root, MARKER))


def slug_of(url):
    """'https://github.com/O/R.git' / 'git@github.com:O/R' -> 'o/r'."""
    m = re.search(r"github\.com[:/]+([^/\s]+)/([^/\s]+?)(?:\.git)?/?$", (url or "").strip())
    return f"{m.group(1)}/{m.group(2)}".lower() if m else ""


def origin_url(root=ROOT):
    try:
        r = subprocess.run(["git", "-C", root, "remote", "get-url", "origin"], capture_output=True, text=True,
                           timeout=10)
    except (OSError, subprocess.SubprocessError):
        return ""
    return r.stdout.strip() if r.returncode == 0 else ""


def is_real_repo(root=ROOT, env=None):
    env = os.environ if env is None else env
    real = real_slug(root)
    gh_repo = (env.get("GITHUB_REPOSITORY") or "").strip().lower()
    return gh_repo == real or slug_of(origin_url(root)) == real


def marker_problems(root=ROOT, env=None):
    if is_practice(root) and is_real_repo(root, env):
        return [f"{MARKER} is on the team repo ({real_slug(root)}): practice mode lifts D39 and blocks the "
                "submission. Delete the file (`git rm .pipeline-practice`); practice belongs in a test repo"]
    return []


def blocked(what, root=ROOT):
    """The one-line refusal when practice mode blocks `what`, else None."""
    return BLOCK_LINE.format(marker=MARKER, what=what) if is_practice(root) else None


def main(argv=None):
    argv = sys.argv[1:] if argv is None else argv
    if argv[:1] != ["status"]:
        print(__doc__)
        return 2
    print(f"practice={'yes' if is_practice() else 'no'} real_repo={'yes' if is_real_repo() else 'no'}")
    probs = marker_problems()
    for p in probs:
        print("FAIL: " + p)
    return 1 if probs else 0


if __name__ == "__main__":
    sys.exit(main())
