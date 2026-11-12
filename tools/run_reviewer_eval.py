#!/usr/bin/env python3
"""Run the Dev Lead reviewer prompt on every seeded-defect case, then score it.

The reviewer CLI is whatever the teammate uses. It gets the prompt on stdin and must print
the review JSON. Defaults to Claude Code; for Codex pass --cmd "codex exec -".

Usage:
  python3 tools/run_reviewer_eval.py                       # claude -p
  python3 tools/run_reviewer_eval.py --cmd "codex exec -"
  python3 tools/run_reviewer_eval.py --only 04-attack-while-open
Writes evals/reviewer/runs/<timestamp>/<case>.json and prints the score from tools/score_review.py.
A pass also needs every defect in the MUST_CATCH cases caught.
"""
import argparse
import glob
import json
import os
import re
import shlex
import subprocess
import sys
import tempfile
import time

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CASES = os.path.join(ROOT, "evals", "reviewer", "cases")
sys.path.insert(0, os.path.join(ROOT, "tools"))
import score_review  # noqa: E402


def read(p):
    with open(p, encoding="utf-8") as fh:
        return fh.read()


DEFAULT_EVIDENCE = ("build: NONUNITY=1 tools/ue/build.sh exit 0 (UBT command line shows -DisableUnity -NoPCH -NoSharedPCH), 0 new warnings (log attached)\n"
                    "module_check: python3 tools/module_check.py -> module_check: 0 problem(s), exit 0 (output attached)\n"
                    "tests: check_automation_report.py Saved/Automation/index.json --baseline main-index.json --require <each test named in the task card> -> PASS tests=24 failed=0 notrun=0, every required test found and passed (output attached)\n"
                    "package: n/a for this card")


# Cases that must be fully caught in every run for a pass, on top of the score_review.py bar.
# A Dev Lead prompt change ships only when these are caught 3/3 (pipeline/roles/dev-lead.md, item 16).
MUST_CATCH = ["37-nonconst-query", "38-contradicting-comment"]


def must_catch_missed(rows):
    return [r["case"] for r in rows if r["case"] in MUST_CATCH and len(r["hits"]) < len(r["defects"])]


def evidence(case_dir):
    """A case may ship its own evidence.txt (e.g. to test missing or fake evidence)."""
    p = os.path.join(case_dir, "evidence.txt")
    return read(p).strip() if os.path.exists(p) else DEFAULT_EVIDENCE


# The core Unreal rules plus every on-demand file, so the reviewer sees the full rule set.
UNREAL_RULE_FILES = [os.path.join(ROOT, "pipeline", "unreal-rules.md")] + sorted(
    glob.glob(os.path.join(ROOT, "pipeline", "unreal", "*.md")))


def build_prompt(case_dir):
    return "\n\n".join([
        read(os.path.join(ROOT, "pipeline", "roles", "dev-lead.md")),
        "# Project C++ rules\n" + "\n\n".join(read(f) for f in UNREAL_RULE_FILES),
        "# Task card\n" + read(os.path.join(case_dir, "task.md")),
        "# Change under review (line numbers in findings refer to the new file)\n" + read(os.path.join(case_dir, "change.diff")),
        "# Evidence attached by the author\n" + evidence(case_dir),
        "Reply with ONLY the review JSON object described in your Outputs section. No prose, no code fences.",
    ])


def extract_json(text):
    """Return the first JSON object in the reply that has a "verdict" key.
    Prose after the JSON (the Dev Lead card asks for it) may contain braces, so decode objects one at a
    time instead of matching from the first '{' to the last '}'."""
    dec = json.JSONDecoder()
    i = text.find("{")
    while i != -1:
        try:
            obj, _ = dec.raw_decode(text, i)
            if isinstance(obj, dict) and "verdict" in obj:
                return obj
        except json.JSONDecodeError:
            pass
        i = text.find("{", i + 1)
    return {"verdict": "invalid", "findings": [], "raw": text[:2000]}


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--cmd", default='claude -p --disallowedTools "Read Glob Grep Bash Edit Write WebFetch WebSearch Agent"')
    ap.add_argument("--only", nargs="*")
    ap.add_argument("--timeout", type=int, default=600)
    a = ap.parse_args(argv)
    run_dir = os.path.join(ROOT, "evals", "reviewer", "runs", time.strftime("%Y%m%d-%H%M%S"))
    os.makedirs(run_dir)
    cases = sorted(c for c in os.listdir(CASES) if os.path.isdir(os.path.join(CASES, c)))
    if a.only:
        cases = [c for c in cases if c in a.only]
    for c in cases:
        prompt = build_prompt(os.path.join(CASES, c))
        t0 = time.time()
        try:
            # Run from an empty temp folder so the reviewer cannot open expected.json or the repo.
            out = subprocess.run(shlex.split(a.cmd), input=prompt, capture_output=True, text=True,
                                 timeout=a.timeout, cwd=tempfile.mkdtemp()).stdout
        except subprocess.TimeoutExpired:
            out = ""
        result = extract_json(out)
        result["_seconds"] = round(time.time() - t0, 1)
        with open(os.path.join(run_dir, c + ".json"), "w", encoding="utf-8") as fh:
            json.dump(result, fh, indent=2)
        print(f"{c}: {result.get('verdict')} ({len(result.get('findings', []))} findings, {result['_seconds']}s)")
    rows = score_review.score(CASES, run_dir)
    if a.only:
        rows = [r for r in rows if r["case"] in a.only]
    s = score_review.summarize(rows)
    s["must_catch_missed"] = must_catch_missed(rows)
    s["pass"] = s["pass"] and not s["must_catch_missed"]
    s["run_dir"] = os.path.relpath(run_dir, ROOT)
    s["cmd"] = a.cmd
    print(json.dumps(s, indent=2))
    with open(os.path.join(run_dir, "_summary.json"), "w", encoding="utf-8") as fh:
        json.dump(s, fh, indent=2)
    return 0 if s["pass"] else 1


if __name__ == "__main__":
    sys.exit(main())
