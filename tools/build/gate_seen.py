#!/usr/bin/env python3
"""The gate never re-runs or merges a branch head it already failed or held (Josh, Nov 12: a held head passed on a plain
re-run). The lane needs new commits after the verdict.

  gate_seen.py check  LOGDIR AREA SHA    exit 4 and print why when SHA was failed or held before, else exit 0
  gate_seen.py record LOGDIR AREA SHA VERDICT   VERDICT is FAIL or HOLD
"""
import json, os, sys, time


def path(logdir, area):
    return os.path.join(logdir, "gate-seen", f"{area}.json")


def load(logdir, area):
    try:
        with open(path(logdir, area)) as f:
            return json.load(f)
    except (OSError, ValueError):
        return {}


def check(logdir, area, sha):
    seen = load(logdir, area).get(sha)
    if seen:
        print(f"GATE REFUSE: area/{area} {sha[:8]} was {seen['verdict']} at {seen['at']}; it needs new commits first")
        return 4
    return 0


def record(logdir, area, sha, verdict):
    d = load(logdir, area)
    d[sha] = {"verdict": verdict, "at": time.strftime("%Y-%m-%d %H:%M")}
    os.makedirs(os.path.dirname(path(logdir, area)), exist_ok=True)
    tmp = path(logdir, area) + ".tmp"
    with open(tmp, "w") as f:
        json.dump(d, f, indent=1)
    os.replace(tmp, path(logdir, area))
    return 0


if __name__ == "__main__":
    a = sys.argv[1:]
    if len(a) == 4 and a[0] == "check":
        sys.exit(check(*a[1:]))
    if len(a) == 5 and a[0] == "record" and a[4] in ("FAIL", "HOLD"):
        sys.exit(record(*a[1:]))
    print(__doc__); sys.exit(2)
