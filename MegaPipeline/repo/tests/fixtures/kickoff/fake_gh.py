#!/usr/bin/env python3
"""A stand-in for the gh CLI (tests only): issues, PRs, labels and comments in a JSON file ($FAKE_GH_STATE), with the
argument shapes tools/kickoff.py and tools/connections.py use. No network.
PRs: `pr view --json headRefOid` reads the head from the bare origin ($FAKE_GH_ORIGIN); `pr checks` answers
$FAKE_GH_CHECKS (pass, the default; fail; pending; none) the way gh does (exit 1 failed, 8 pending); `pr merge
--squash --match-head-commit <sha>` squash-merges the head into origin main, or fails with $FAKE_GH_MERGE_FAIL.
GitHub outages: $FAKE_GH_FAIL (a count, or `always`) calls whose argv contains $FAKE_GH_FAIL_ON (default `issue list`)
fail the way gh does on a transient error ($FAKE_GH_FAIL_TEXT, default the HTTP 401 a live run saw). With
FAKE_GH_FAIL_AFTER=1 the call is done first, then reported failed (a 502 after GitHub wrote it)."""
import argparse
import json
import os
import shutil
import subprocess
import sys
import tempfile

try:
    import fcntl
except ImportError:   # Windows: no fcntl; msvcrt locks a byte range instead
    fcntl = None
    import msvcrt

STATE = os.environ["FAKE_GH_STATE"]


def load():
    if not os.path.exists(STATE):
        return {"issues": [], "prs": [], "next": 1}
    with open(STATE, encoding="utf-8") as fh:
        return json.load(fh)


def save(s):
    with open(STATE + ".tmp", "w", encoding="utf-8") as fh:
        json.dump(s, fh, indent=1)
    os.replace(STATE + ".tmp", STATE)


def body(a):
    if getattr(a, "body_file", None):
        with open(a.body_file, encoding="utf-8") as fh:
            return fh.read()
    return getattr(a, "body", None) or ""


def head_oid(pr):
    origin = os.environ.get("FAKE_GH_ORIGIN")
    if not origin or not pr.get("headRefName"):
        return None
    p = subprocess.run(["git", "--git-dir", origin, "rev-parse", "-q", "--verify", f"refs/heads/{pr['headRefName']}"],
                       capture_output=True, text=True)
    return p.stdout.strip() or None


def view(it, fields):
    out = {}
    for f in fields.split(","):
        v = it.get(f)
        if f == "labels":
            v = [{"name": n} for n in it.get("labels", [])]
        if f == "headRefOid" and "headRefName" in it:
            v = head_oid(it)
        out[f] = v
    return out


def checks(pr):
    mode = os.environ.get("FAKE_GH_CHECKS", "pass")
    if mode == "none":
        print(f"no checks reported on the '{pr['headRefName']}' branch", file=sys.stderr)
        return 1
    bucket = {"pass": "pass", "fail": "fail", "pending": "pending"}[mode]
    print(json.dumps([{"name": "Pipeline checks / linux", "bucket": bucket},
                      {"name": "Pipeline checks / windows", "bucket": "pass"}]))
    return {"pass": 0, "fail": 1, "pending": 8}[mode]


def git(*args, cwd):
    p = subprocess.run(["git", "-c", "core.hooksPath=/dev/null", *args], cwd=cwd, capture_output=True, text=True,
                       env=dict(os.environ, GIT_LFS_SKIP_SMUDGE="1"))
    if p.returncode:
        raise RuntimeError(p.stderr.strip())
    return p.stdout.strip()


def merge(pr, sha):
    if os.environ.get("FAKE_GH_MERGE_FAIL"):
        print(os.environ["FAKE_GH_MERGE_FAIL"], file=sys.stderr)
        return 1
    if pr["state"] != "OPEN":
        print(f"Pull request #{pr['number']} is not open", file=sys.stderr)
        return 1
    if head_oid(pr) != sha:
        print(f"Head branch was modified. Review and try the merge again ({sha[:7]})", file=sys.stderr)
        return 1
    work = tempfile.mkdtemp(prefix="fake-gh-merge-")
    try:
        git("clone", "-q", os.environ["FAKE_GH_ORIGIN"], work, cwd=os.path.dirname(work))
        git("config", "user.email", "gh@fake", cwd=work)
        git("config", "user.name", "github", cwd=work)
        git("fetch", "-q", "origin", pr["headRefName"], cwd=work)
        git("merge", "--squash", "-q", "FETCH_HEAD", cwd=work)
        git("commit", "-q", "-m", f"{pr['title']} (#{pr['number']})", cwd=work)
        git("push", "-q", "origin", "HEAD:main", cwd=work)
        pr["mergeCommit"] = {"oid": git("rev-parse", "HEAD", cwd=work)}
    except RuntimeError as e:
        print(f"merge failed: {e}", file=sys.stderr)
        return 1
    finally:
        shutil.rmtree(work, ignore_errors=True)
    pr["state"] = "MERGED"
    return 0


def main(argv):
    lock = open(STATE + ".lock", "a")
    if fcntl:
        fcntl.flock(lock, fcntl.LOCK_EX)
    else:
        lock.seek(0)
        msvcrt.locking(lock.fileno(), msvcrt.LK_LOCK, 1)   # retries for 10 s, then raises
    s = load()
    if outage(argv):
        return 1
    rc = handle(s, argv)
    if rc == 0 and outage(argv, after=True):
        return 1
    return rc


def outage(argv, after=False):
    """True (and the gh error printed) when this call is one $FAKE_GH_FAIL fails; counted in $FAKE_GH_STATE.fails."""
    n = os.environ.get("FAKE_GH_FAIL")
    if not n or bool(os.environ.get("FAKE_GH_FAIL_AFTER")) != after:
        return False
    if os.environ.get("FAKE_GH_FAIL_ON", "issue list") not in " ".join(argv):
        return False
    f = STATE + ".fails"
    done = int(open(f).read()) if os.path.exists(f) else 0
    if n != "always" and done >= int(n):
        return False
    with open(f, "w") as fh:
        fh.write(str(done + 1))
    print(os.environ.get("FAKE_GH_FAIL_TEXT", "HTTP 401: Bad credentials (https://api.github.com/graphql)\n"
                                              "Try authenticating with:  gh auth refresh -h github.com"),
          file=sys.stderr)
    return True


def handle(s, argv):
    if argv[:2] == ["auth", "status"]:
        print("Logged in to github.com (fake)")
        return 0
    if argv[:2] == ["repo", "view"]:
        print(json.dumps({"viewerPermission": os.environ.get("FAKE_GH_PERMISSION", "WRITE")}))
        return 0
    if argv[:2] == ["label", "create"]:
        return 0
    if argv[:1] in (["variable"], ["workflow"], ["api"]):   # repo settings kickoff sets after cards 0.16 and 0.17
        rec = list(argv)
        if "--input" in rec:
            with open(rec[rec.index("--input") + 1], encoding="utf-8") as fh:
                rec[rec.index("--input") + 1] = json.load(fh)
        if argv[:2] == ["variable", "set"]:
            s.setdefault("variables", {})[argv[2]] = argv[argv.index("--body") + 1]
        elif argv[:2] == ["variable", "list"]:
            print("\n".join(f"{k}\t{v}" for k, v in sorted(s.get("variables", {}).items())))
        elif argv[0] == "api" and "-X" not in argv:
            print(json.dumps(next((r[r.index("--input") + 1] for r in reversed(s.get("settings", []))
                                   if r[0] == "api" and r[-2:-1] == ["--input"] and r[3] == argv[1]), {})))
        s.setdefault("settings", []).append(rec)
        save(s)
        return 0
    ap = argparse.ArgumentParser()
    ap.add_argument("noun")
    ap.add_argument("verb")
    ap.add_argument("number", nargs="?")
    for opt in ("--state", "--limit", "--json", "--title", "--body-file", "--body", "--head", "--base", "--search",
                "--match-head-commit"):
        ap.add_argument(opt)
    ap.add_argument("--squash", action="store_true")
    ap.add_argument("--required", action="store_true")
    ap.add_argument("--label", action="append", default=[])
    ap.add_argument("--add-label", action="append", default=[])
    ap.add_argument("--remove-label", action="append", default=[])
    a = ap.parse_args(argv)
    coll = "issues" if a.noun == "issue" else "prs"
    if a.verb == "list":
        items = s[coll]
        if a.state and a.state != "all":
            items = [i for i in items if i["state"].lower() == a.state.lower()]
        for lb in a.label:
            items = [i for i in items if lb in i.get("labels", [])]
        print(json.dumps([view(i, a.json or "number,title") for i in items]))
    elif a.verb == "create":
        n = s["next"]
        s["next"] += 1
        if coll == "issues":
            s["issues"].append({"number": n, "title": a.title, "body": body(a), "labels": list(a.label),
                                "state": "OPEN", "comments": []})
            print(f"https://github.com/fake/repo/issues/{n}")
        else:
            s["prs"].append({"number": n, "title": a.title, "body": body(a), "headRefName": a.head,
                             "baseRefName": a.base, "state": "OPEN", "comments": [],
                             "url": f"https://github.com/fake/repo/pull/{n}"})
            print(f"https://github.com/fake/repo/pull/{n}")
    else:
        it = next((i for i in s[coll] if i["number"] == int(a.number)), None)
        if it is None:
            print(f"no {a.noun} {a.number}", file=sys.stderr)
            return 1
        if a.verb == "view":
            print(json.dumps(view(it, a.json or "number,title,body")))
        elif a.verb == "checks":
            return checks(it)
        elif a.verb == "merge":
            if not a.squash or not a.match_head_commit:
                print("fake gh: kickoff merges with --squash --match-head-commit only", file=sys.stderr)
                return 2
            rc = merge(it, a.match_head_commit)
            if rc:
                return rc
        elif a.verb == "edit":
            if a.body_file or a.body:
                it["body"] = body(a)
            it["labels"] = [x for x in it.get("labels", []) if x not in a.remove_label]
            it["labels"] += [x for x in a.add_label if x not in it["labels"]]
        elif a.verb == "comment":
            it["comments"].append({"body": body(a)})
        elif a.verb == "close":
            it["state"] = "CLOSED"
        else:
            print(f"fake gh: {a.noun} {a.verb} not supported", file=sys.stderr)
            return 2
    if a.verb not in ("list", "view", "checks"):
        save(s)
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
