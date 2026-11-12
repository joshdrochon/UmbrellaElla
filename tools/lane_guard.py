#!/usr/bin/env python3
"""Keep lanes running in parallel (AGENTS.md section 6). Stdlib only; the logic for two workflows.

  revert   .github/workflows/main-red.yml, when the pipeline checks fail on a push to main.
           Opens a revert PR of the breaking commit (each card is one squash commit, so one `git revert`)
           on branch revert-<sha7>, and comments on the tracker issue naming the integration owner from the
           docs/jam-brief.md People table, who merges it within REVERT_MIN minutes. The card goes back to doing.
           Skips when a revert PR for that commit is open. A red revert commit gets a comment, never a revert.
  blocked  .github/workflows/blocked-report.yml, daily. Posts one tracker comment: for every open card with
           the `blocked` label, the cards that wait on it (tools/check_card.py --blocked-by). Nothing else waits.

           The PR body has every check_pr.py section and `Revert of: <sha>`; check_pr passes it when the diff is exactly
           the inverse of that commit (final-10 A H3).
           GITHUB_TOKEN caveat: GitHub starts no workflow for a PR that GITHUB_TOKEN opened, so the required `checks`
           job never reports on it. main-red.yml passes the REVERT_TOKEN secret (a fine-grained PAT or GitHub App
           token with contents and pull-requests write) when it is set; without it, the integration owner closes and
           reopens the PR (a human event starts the checks).
Usage: python3 tools/lane_guard.py revert --sha SHA [--tracker N] [--dry-run]
       python3 tools/lane_guard.py blocked --tracker N [--dry-run]
--dry-run prints the git and gh commands instead of running them. Needs gh with GH_TOKEN in Actions.
Exit 0 = done (or nothing to do), 1 = a command failed, 2 = usage error.
"""
import argparse
import json
import os
import re
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, HERE)
import check_card  # noqa: E402

REVERT_MIN = 30
BOT = ("github-actions[bot]", "41898282+github-actions[bot]@users.noreply.github.com")


def sh(cmd, cwd=ROOT):
    """Run one command -> (exit code, stdout)."""
    r = subprocess.run(cmd, cwd=cwd, capture_output=True, text=True)
    if r.returncode != 0:
        sys.stderr.write(r.stderr)
    return r.returncode, r.stdout


def integration_owner(root=ROOT):
    """The person in the 'Integration owner' People row of docs/jam-brief.md, or a pointer to the empty seat."""
    try:
        text = check_card.read(os.path.join(root, "docs", "jam-brief.md"))
    except OSError:
        text = ""
    for line in text.splitlines():
        cells = [c.strip() for c in line.strip().strip("|").split("|")]
        if line.startswith("|") and cells and cells[0].lower().startswith("integration owner") and len(cells) > 1:
            who = cells[1]
            if who and not who.upper().startswith("TBD"):
                return who
    return "the integration owner (seat still TBD in the docs/jam-brief.md People table)"


def revert(sha, tracker=None, run=sh, root=ROOT):
    code, subject = run(["git", "log", "-1", "--format=%s", sha])
    if code != 0:
        return 1
    subject = subject.strip()
    short = sha[:7]
    owner = integration_owner(root)
    branch = f"revert-{short}"
    if subject.lower().startswith("revert"):
        msg = (f"main is red at {short} ({subject}), which is itself a revert. No automatic revert. "
               f"{owner}: fix main by hand. Other cards keep working; they wait to merge until main is green.")
        return comment(tracker, msg, run)
    code, out = run(["gh", "pr", "list", "--head", branch, "--state", "open", "--json", "number,url"])
    if code == 0 and out.strip() not in ("", "[]"):
        print(f"lane_guard: a revert PR for {short} is already open")
        return 0
    code, parents = run(["git", "rev-list", "--parents", "-n", "1", sha])
    merge = len(parents.split()) > 2
    steps = [
        ["git", "config", "user.name", BOT[0]],
        ["git", "config", "user.email", BOT[1]],
        ["git", "fetch", "origin", "main"],
        ["git", "checkout", "-B", branch, "origin/main"],
        ["git", "revert", "--no-edit"] + (["-m", "1"] if merge else []) + [sha],
        ["git", "push", "origin", f"HEAD:refs/heads/{branch}"],
    ]
    for cmd in steps:
        if run(cmd)[0] != 0:
            return comment(tracker, f"main is red at {short} ({subject}). The automatic revert failed at "
                                    f"`{' '.join(cmd[:3])}`. {owner}: revert it by hand within {REVERT_MIN} min.", run) or 1
    _, head = run(["git", "rev-parse", "HEAD"])
    _, files = run(["git", "diff", "--name-only", f"{sha}^1", sha])
    body = revert_body(sha, subject, head.strip(), files.split(), card_issue(sha, run) or tracker, owner)
    code, url = run(["gh", "pr", "create", "--base", "main", "--head", branch,
                     "--title", f"Revert {short}: main is red", "--body", body])
    if code != 0:
        return 1
    msg = (f"main is red at {short} ({subject}). Revert PR: {url.strip()}. {owner}: merge it within "
           f"{REVERT_MIN} min, then move the card back to `doing`. Other cards keep working on their branches; "
           "they wait to merge until main is green.")
    return comment(tracker, msg, run)


def card_issue(sha, run=sh):
    """The card the reverted commit's PR linked (`Part of #n` in the merged PR's body), or None."""
    code, out = run(["gh", "pr", "list", "--state", "merged", "--search", sha, "--json", "number,body", "--limit", "5"])
    try:
        prs = json.loads(out or "[]") if code == 0 else []
    except ValueError:
        prs = []
    for pr in prs:
        m = re.search(r"(?i)\b(?:Part of|Closes|Fixes|Resolves)\s+#(\d+)", pr.get("body") or "")
        if m:
            return m.group(1)
    return None


def revert_body(sha, subject, head, files, issue, owner):
    """Final-10 A H3: the revert PR body has every section tools/check_pr.py asks for. Its Evidence carries
    `Revert of: <sha>`: check_pr checks that the PR's diff is exactly the inverse of that commit (same removed and
    added lines per file) in place of build, test, package and smoke evidence; the next daily builds and smokes it."""
    short = sha[:7]
    m = re.match(r"\s*\[?(UE-[\w.]+)", subject or "")
    card = m.group(1) if m else "UE-revert"
    binary = [f for f in files if f.endswith((".uasset", ".umap"))]
    issue_ref = f"#{issue}" if issue else "#<card issue: link it by hand>"
    return (f"## Task\nPart of {issue_ref}. Card ID: {card}  Owner role: Integrator  Reviewer role: Human only\n\n"
            "## What changed\n" + "\n".join(f"{f} (reverted)" for f in files) + "\n\n"
            f"## Done-when checks\n- [x] main is green again: this reverts {short} ({subject}), one squash commit\n\n"
            f"## Evidence\nRevert of: {sha}\n`git revert --no-edit {sha}` at {head or 'the branch head'}; check_pr.py "
            "checks this diff is exactly its inverse (the same removed and added lines). No build evidence: the next "
            "daily builds, tests, packages and smokes main.\n\n"
            f"## Not done / risks\nThe card goes back to `doing` and lands again with the fix: {issue_ref}\n"
            "Could not read: none\n"
            f"Next: {owner} merges within {REVERT_MIN} min (AGENTS.md section 6)\n\n"
            "## Binary assets touched\n" + ("\n".join(f"{f} (reverted by git; no lock needed for a revert of the "
                                                    "merged file)" for f in binary) or "none") + "\n\n"
            "## Journal\nRevert bot, no agent session\n")


def comment(tracker, msg, run=sh):
    print(msg)
    if not tracker:
        print("lane_guard: no tracker issue (repo variable TRACKER_ISSUE); comment not posted")
        return 0
    return 0 if run(["gh", "issue", "comment", str(tracker), "--body", msg])[0] == 0 else 1


def blocked_report(blocked, open_cards, root=ROOT):
    """Tracker comment text: each blocked card and exactly the cards that wait on it."""
    if not blocked:
        return "Blocked cards: none. Every lane is free."
    lines = ["Blocked cards and the cards that wait on them (`check_card.py --blocked-by`). Every other card keeps working."]
    for issue in sorted(blocked, key=lambda i: i.get("number") or 0):
        m = re.match(r"\s*\[([^\]]+)\]", issue.get("title") or "")
        ref = m.group(1) if m else f"#{issue.get('number')}"
        try:
            waiting = [t for _, t in check_card.blocked_by(ref, root, open_cards)]
        except KeyError:
            waiting = []
        lines.append(f"- #{issue.get('number')} {issue.get('title') or ''}: "
                     + ("; ".join(waiting) if waiting else "no card waits on it"))
    return "\n".join(lines)


def blocked(tracker, run=sh, root=ROOT):
    fields = "number,title,body"
    code, b = run(["gh", "issue", "list", "--label", "blocked", "--state", "open", "--json", fields, "--limit", "200"])
    code2, o = run(["gh", "issue", "list", "--state", "open", "--json", fields, "--limit", "500"])
    if code or code2:
        return 1
    try:
        msg = blocked_report(json.loads(b or "[]"), json.loads(o or "[]"), root)
    except ValueError as e:
        print(f"lane_guard: {e}", file=sys.stderr)
        return 1
    return comment(tracker, msg, run)


def dry(cmd):
    print("DRY: " + " ".join(cmd))
    if cmd[:2] == ["git", "log"]:
        return 0, "UE-0: dry run\n"
    if cmd[:3] == ["gh", "issue", "list"]:
        return 0, "[]"
    return 0, "[]" if cmd[:3] == ["gh", "pr", "list"] else ""


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="action", required=True)
    r = sub.add_parser("revert")
    r.add_argument("--sha", required=True)
    r.add_argument("--tracker")
    b = sub.add_parser("blocked")
    b.add_argument("--tracker")
    for p in (r, b):
        p.add_argument("--dry-run", action="store_true")
    a = ap.parse_args(argv)
    run = dry if a.dry_run else sh
    if a.action == "revert":
        if not re.fullmatch(r"[0-9a-f]{7,40}", a.sha):
            print(f"lane_guard: '{a.sha}' is not a commit sha", file=sys.stderr)
            return 2
        return revert(a.sha, a.tracker or None, run)
    return blocked(a.tracker or None, run)


if __name__ == "__main__":
    sys.exit(main())
