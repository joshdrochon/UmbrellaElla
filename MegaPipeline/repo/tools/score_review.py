#!/usr/bin/env python3
"""Score a reviewer agent against seeded-defect cases (evals/reviewer/cases/*).

Rick's pipeline doc: "We should test the reviewer with known problems: an agent saying
'approved' is not proof that the code is good." This is that test.

Each case folder holds:
  change.diff     the change under review (we planted the defects)
  task.md         the task card the change claims to satisfy
  expected.json   {"clean": bool, "defects": [{"id", "severity", "file", "lines": [a, b], "keywords": [...],
                                             "also": [{"file", "lines": [a, b]}]  (optional)}],
                   "checks": {"tests": "missing" | "fail", "build": ...}  (optional)}
  evidence.txt    optional; replaces the default author evidence (see tools/run_reviewer_eval.py)

The reviewer writes one JSON file per case into a run folder:
  {"verdict": "approve" | "request_changes", "findings": [{"file", "line", "severity", "summary"}],
   "checks_seen": {"build": ..., "tests": ..., "package": ...}}

A planted defect counts as caught when a finding names the same file (or an "also" file), points
within LINE_SLACK lines of that file's planted range, and mentions at least one keyword.
"also" lists other places the same defect shows (e.g. the ini side of an ini/header mismatch).

An evidence defect ("checks") has no code line. Each key counts as one blocker, caught when the
reviewer's checks_seen has that key with a value other than "pass" AND the verdict is request_changes.

Bar (see evals/README.md):
  every blocker caught, overall recall >= 0.80, clean cases approved >= 0.80.

Usage: python3 tools/score_review.py evals/reviewer/cases evals/reviewer/runs/<run-id>
Exit 0 = bar met, 1 = bar missed, 2 = bad input.
"""
import json
import os
import sys

LINE_SLACK = 3
BAR = {"recall_min": 0.80, "clean_approve_min": 0.80}


def caught(defect, findings):
    places = [(defect["file"], defect["lines"])] + [(a["file"], a["lines"]) for a in defect.get("also", [])]
    kws = [k.lower() for k in defect.get("keywords", [])]
    for f in findings:
        name = os.path.basename(str(f.get("file", "")))
        try:
            line = int(f.get("line", -1))
        except (TypeError, ValueError):
            continue
        if not any(name == os.path.basename(file) and lo - LINE_SLACK <= line <= hi + LINE_SLACK
                   for file, (lo, hi) in places):
            continue
        text = str(f.get("summary", "")).lower()
        if not kws or any(k in text for k in kws):
            return True
    return False


def check_items(exp):
    """Evidence defects: one blocker per key in expected.json "checks"."""
    return [{"id": "checks." + key, "severity": "blocker", "check": key, "expect": val}
            for key, val in sorted((exp.get("checks") or {}).items())]


def check_caught(item, out):
    seen = out.get("checks_seen") or {}
    if not isinstance(seen, dict):
        return False
    value = str(seen.get(item["check"], "")).strip().lower()
    return out.get("verdict") == "request_changes" and value not in ("", "pass")


def score(cases_dir, run_dir):
    rows = []
    for case in sorted(os.listdir(cases_dir)):
        exp_path = os.path.join(cases_dir, case, "expected.json")
        if not os.path.isfile(exp_path):
            continue
        with open(exp_path, encoding="utf-8") as fh:
            exp = json.load(fh)
        out_path = os.path.join(run_dir, case + ".json")
        if os.path.isfile(out_path):
            try:
                with open(out_path, encoding="utf-8") as fh:
                    out = json.load(fh)
            except json.JSONDecodeError:
                out = {"verdict": "invalid", "findings": []}
        else:
            out = {"verdict": "missing", "findings": []}
        findings = out.get("findings", []) or []
        hits = [d for d in exp.get("defects", []) if caught(d, findings)]
        checks = check_items(exp)
        hits += [c for c in checks if check_caught(c, out)]
        rows.append({"case": case, "clean": exp.get("clean", False), "verdict": out.get("verdict"),
                     "defects": exp.get("defects", []) + checks, "hits": hits})
    return rows


def summarize(rows):
    total = sum(len(r["defects"]) for r in rows)
    hit = sum(len(r["hits"]) for r in rows)
    blockers = [d for r in rows for d in r["defects"] if d.get("severity") == "blocker"]
    blocker_hits = [d for r in rows for d in r["hits"] if d.get("severity") == "blocker"]
    clean = [r for r in rows if r["clean"]]
    clean_ok = [r for r in clean if r["verdict"] == "approve"]
    dirty = [r for r in rows if not r["clean"]]
    dirty_blocked = [r for r in dirty if r["verdict"] == "request_changes"]
    s = {
        "cases": len(rows),
        "recall": round(hit / total, 3) if total else 1.0,
        "blockers_caught": f"{len(blocker_hits)}/{len(blockers)}",
        "clean_approve_rate": round(len(clean_ok) / len(clean), 3) if clean else 1.0,
        "defective_blocked_rate": round(len(dirty_blocked) / len(dirty), 3) if dirty else 1.0,
        "missed": [f"{r['case']}:{d['id']}" for r in rows for d in r["defects"] if d not in r["hits"]],
    }
    s["pass"] = (len(rows) > 0 and total > 0 and len(clean) > 0 and s["recall"] >= BAR["recall_min"] and len(blocker_hits) == len(blockers)
                 and s["clean_approve_rate"] >= BAR["clean_approve_min"] and s["defective_blocked_rate"] == 1.0)
    return s


def main(argv=None):
    argv = sys.argv[1:] if argv is None else argv
    if len(argv) != 2 or not os.path.isdir(argv[0]) or not os.path.isdir(argv[1]):
        print(__doc__, file=sys.stderr)
        return 2
    s = summarize(score(argv[0], argv[1]))
    print(json.dumps(s, indent=2))
    return 0 if s["pass"] else 1


if __name__ == "__main__":
    sys.exit(main())
