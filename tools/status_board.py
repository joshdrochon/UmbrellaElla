#!/usr/bin/env python3
"""Status board: one static page that shows where the jam stands. Stdlib only.

The Producer regenerates it every jam hour (pipeline/how-to-run-the-jam.md) and pastes or links it on the tracker.
It never writes to GitHub. It shows:
  Cards        every task card (issue labelled `task`): state from its labels (todo | doing | review | blocked | cut |
               superseded; closed = done), owner role, the card's Human, and a needs-human mark
  Needs human  each open needs-human card: who and what, from its newest `NEEDS HUMAN: <who/role> <what> <link>`
               comment (check_card.py --needs-human reads the same line)
  Sessions     which role and machine is on which card: the newest journal `start` per card (tools/journal.py),
               open until an `end`; with --source gh also the newest `ROLE: <role> | session ...` comment
  Open PRs     each open PR, its card (branch ue-<id>-... or `Closes #n`) and its checks: pass | fail | pending | none
  Gates        G1-G4 from the Clock in docs/jam-brief.md: due time, and closed (annotated tag gate-G<n>), record
               posted (a tracker comment `Gate: G<n> ...` with its Proposed outcome), OVERDUE, due or TBD

Sources:
  --source gh        gh issue list / gh pr list (needs a logged-in gh; the network)
  --source local     local git (ue-* branches, gate-G* tags) and the journal; no network, no GitHub
  --from-json DIR    saved gh output instead of calling gh: DIR/issues.json and DIR/prs.json (tests, offline)
The journal (JOURNAL_DB, else .pipeline/journal.db; --journal FILE) is read in every mode when it exists.

Problems (exit 1, the page is still written): a needs-human card with no NEEDS HUMAN comment, a card with two
state labels, a doing card with no session in the journal or comments.

Usage: python3 tools/status_board.py [--source gh|local] [--from-json DIR] [--repo OWNER/NAME] [--out FILE]
       [--html] [--now ISO] [--journal FILE] [--root PATH]
Default out: Saved/status-board.md (Saved/ is git-ignored); --html writes HTML instead (default .html name).
Exit 0 = written, no problems; 1 = written, with problems; 2 = unreadable input (bad JSON, gh failed, no source).
"""
import argparse
import datetime as dt
import html
import json
import os
import re
import sqlite3
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, HERE)
import check_card  # noqa: E402  same NEEDS HUMAN, card and Clock parsers as the gates

STATES = ("todo", "doing", "review", "blocked", "cut", "superseded")
ISSUE_FIELDS = "number,title,state,labels,assignees,comments,body,url"
PR_FIELDS = "number,title,headRefName,url,isDraft,body,statusCheckRollup"
BRANCH_CARD = re.compile(r"^ue-(\d+(?:\.\d+)?[a-z]?)-")
CLOSES = re.compile(r"(?i)\b(?:Closes|Fixes|Resolves|Part of)\s+#(\d+)")
ROLE_LINE = re.compile(r"^\s*ROLE:\s*([\w -]+?)\s*(?:\||$)", re.M)
GATE_COMMENT = re.compile(r"^\s*Gate:\s*(G[1-4])\b", re.M)
FAIL = {"FAILURE", "ERROR", "CANCELLED", "TIMED_OUT", "ACTION_REQUIRED", "STARTUP_FAILURE"}
OK = {"SUCCESS", "NEUTRAL", "SKIPPED"}


class InputError(Exception):
    """Unreadable input: exit 2."""


def gh_runner(argv):
    try:
        r = subprocess.run(argv, capture_output=True, text=True, timeout=60)
    except (OSError, subprocess.SubprocessError) as e:
        raise InputError(f"{argv[0]}: {e}")
    if r.returncode != 0:
        raise InputError(f"{' '.join(argv[:3])} exited {r.returncode}: {r.stderr.strip()[:200]}")
    return r.stdout


def load_list(text, what):
    try:
        data = json.loads(text)
    except (ValueError, TypeError) as e:
        raise InputError(f"{what}: not JSON ({e})")
    if not isinstance(data, list) or not all(isinstance(x, dict) for x in data):
        raise InputError(f"{what}: expected a JSON list of objects")
    return data


def collect_gh(runner=gh_runner, repo=None):
    extra = ["--repo", repo] if repo else []
    issues = load_list(runner(["gh", "issue", "list", "--state", "all", "--limit", "300", "--json", ISSUE_FIELDS]
                              + extra), "gh issue list")
    prs = load_list(runner(["gh", "pr", "list", "--state", "open", "--limit", "100", "--json", PR_FIELDS] + extra),
                    "gh pr list")
    return issues, prs


def collect_json(d):
    out = []
    for name in ("issues.json", "prs.json"):
        p = os.path.join(d, name)
        if not os.path.isfile(p):
            raise InputError(f"{p}: missing")
        with open(p, encoding="utf-8") as fh:
            out.append(load_list(fh.read(), p))
    return out


def git_lines(root, *args):
    try:
        r = subprocess.run(["git", *args], cwd=root, capture_output=True, text=True, timeout=15)
    except (OSError, subprocess.SubprocessError):
        return []
    return r.stdout.split() if r.returncode == 0 else []


def collect_local(root):
    """Local branches ue-<id>-... as doing cards, gate-G<n> tags as closed gates. No GitHub."""
    branches = [b for b in git_lines(root, "for-each-ref", "--format=%(refname:short)", "refs/heads") if BRANCH_CARD.match(b)]
    tags = [t for t in git_lines(root, "tag", "-l", "gate-G*")]
    return branches, tags


def journal_sessions(path):
    """{card: {role, machine, utc, open}} from the newest start per card; open until an end after it."""
    if not path or not os.path.isfile(path):
        return {}
    con = None
    try:
        con = sqlite3.connect(f"file:{path}?mode=ro", uri=True, timeout=5)
        rows = con.execute("SELECT id, utc, machine, role, card, kind FROM events ORDER BY id").fetchall()
    except sqlite3.Error as e:
        raise InputError(f"{path}: not a readable journal ({e})")
    finally:
        if con is not None:
            con.close()
    out = {}
    for _id, utc, machine, role, card, kind in rows:
        if kind == "start":
            out[card] = {"role": role or "?", "machine": machine or "?", "utc": utc, "open": True, "from": "journal"}
        elif kind == "end" and card in out:
            out[card]["open"] = False
    return out


def label_names(item):
    return [(lb.get("name") if isinstance(lb, dict) else str(lb)) for lb in item.get("labels") or []]


def card_rows(issues, root):
    fields = check_card.template_fields(root)
    rows, problems = [], []
    for it in issues:
        labels = set(label_names(it))
        if "task" not in labels:
            continue
        c, _ = check_card.parse(it.get("body") or "", fields, it.get("title") or "")
        cid = c.get("ID") if re.match(r"(?i)UE-\d", c.get("ID") or "") else ""
        states = [s for s in STATES if s in labels]
        if len(states) > 1:
            problems.append(f"#{it.get('number')}: two state labels ({', '.join(states)}); keep one")
        if str(it.get("state") or "").upper() == "CLOSED":
            state = "done" if not states or states[0] not in ("cut", "superseded") else states[0]
        else:
            state = states[0] if states else "untriaged"
        rows.append({"number": it.get("number"), "id": cid, "title": c.get("Title") or it.get("title") or "",
                     "state": state, "owner": c.get("Owner role") or "?", "human": c.get("Human") or "?",
                     "needs_human": "needs-human" in labels, "comments": it.get("comments") or [],
                     "url": it.get("url") or ""})
    return rows, problems


def checks_state(pr):
    roll = pr.get("statusCheckRollup") or []
    if not roll:
        return "none"
    states = []
    for c in roll:
        if not isinstance(c, dict):
            continue
        if "state" in c and "conclusion" not in c:      # StatusContext
            s = str(c.get("state") or "").upper()
            states.append("fail" if s in FAIL else "pass" if s in OK else "pending")
        elif str(c.get("status") or "COMPLETED").upper() != "COMPLETED":
            states.append("pending")
        else:
            s = str(c.get("conclusion") or "").upper()
            states.append("fail" if s in FAIL else "pass" if s in OK else "pending")
    if "fail" in states:
        return "fail"
    return "pending" if "pending" in states or not states else "pass"


def pr_card(pr):
    m = BRANCH_CARD.match(pr.get("headRefName") or "")
    if m:
        return "UE-" + m.group(1)
    m = CLOSES.search(pr.get("body") or "")
    return f"#{m.group(1)}" if m else "none"


def comment_sessions(cards):
    out = {}
    for c in cards:
        for cm in c["comments"]:
            m = ROLE_LINE.search(cm.get("body") or "")
            if m:
                out[c["id"] or f"#{c['number']}"] = {"role": m.group(1).strip(), "machine": "-",
                                                    "utc": cm.get("createdAt") or "", "open": True, "from": "comment"}
    return out


def gate_rows(root, now, tags=(), tracker_comments=()):
    path = os.path.join(root, "docs", "jam-brief.md")
    text = ""
    if os.path.isfile(path):
        with open(path, encoding="utf-8") as fh:
            text = fh.read()
    clk = check_card.clock(text) or {}
    posted = {}
    for cm in tracker_comments:
        m = GATE_COMMENT.search(cm.get("body") or "")
        if m:
            posted[m.group(1)] = check_card.field_value(cm.get("body") or "", "Proposed outcome") or "?"
    rows = []
    for g in check_card.GATES:
        due_raw = clk.get(g) or "TBD"
        due = check_card.parse_time(due_raw)
        if f"gate-{g}" in tags:
            st = "closed (tag gate-%s)" % g
        elif g in posted:
            st = f"record posted: {posted[g]}"
        elif due is None:
            st = "TBD"
        elif now >= due:
            st = "OVERDUE"
        else:
            st = "due"
        rows.append((g, due_raw, st))
    return rows


def cell(v):
    return str(v).replace("|", "\\|").replace("\n", " ")


def table(head, rows):
    out = ["| " + " | ".join(head) + " |", "|" + "---|" * len(head)]
    out += ["| " + " | ".join(cell(x) for x in r) + " |" for r in rows]
    return out if rows else out + ["| " + " | ".join(["none"] + [""] * (len(head) - 1)) + " |"]


def build(root, now, source, issues=(), prs=(), branches=(), tags=(), sessions=None):
    cards, problems = card_rows(issues, root)
    nh_lines, nh_probs = check_card.needs_human_queue(
        [{"number": c["number"], "labels": ["needs-human"] if c["needs_human"] else [], "comments": c["comments"]}
         for c in cards if c["state"] not in ("done", "cut", "superseded")])
    problems += nh_probs
    sess = dict(comment_sessions(cards))
    sess.update(sessions or {})
    for b in branches:
        cid = "UE-" + BRANCH_CARD.match(b).group(1)
        if not any(c["id"] == cid for c in cards):
            cards.append({"number": "-", "id": cid, "title": f"(branch {b})", "state": "doing", "owner": "?",
                          "human": "?", "needs_human": False, "comments": [], "url": ""})
    for c in cards:
        if c["state"] == "doing" and (c["id"] or f"#{c['number']}") not in sess:
            problems.append(f"{c['id'] or '#' + str(c['number'])}: doing, but no session in the journal or a ROLE: comment")
    tracker = next((it for it in issues if "jam tracker" in (it.get("title") or "").lower()), None)
    gates = gate_rows(root, now, tags, (tracker or {}).get("comments") or [])
    pr_rows = [(f"#{p.get('number')}", pr_card(p), p.get("title") or "", "draft" if p.get("isDraft") else "ready",
                checks_state(p)) for p in prs]
    order = {s: i for i, s in enumerate(("blocked", "review", "doing", "todo", "untriaged", "done", "cut", "superseded"))}
    cards.sort(key=lambda c: (order.get(c["state"], 9), str(c["number"])))
    counts = {s: sum(1 for c in cards if c["state"] == s) for s in order}
    sys.path.insert(0, os.path.join(ROOT, "tools"))
    import practice
    banner = ([f"**PRACTICE** repo (`{practice.MARKER}`): D39 lifted; submission, upload and G4 are blocked.", ""]
              if practice.is_practice(root) else [])
    md = [f"# Status board", ""] + banner + [
          f"Generated {now.isoformat(timespec='minutes')} from `{source}` by `tools/status_board.py`. Read-only; "
          "GitHub stays the source of truth.", "",
          "Cards: " + ", ".join(f"{s} {n}" for s, n in counts.items() if n) if cards else "Cards: none", "",
          "## Needs human", ""]
    md += [f"- {ln}" for ln in nh_lines] or ["- none"]
    md += ["", "## Cards", ""]
    md += table(["Card", "Issue", "State", "Owner role", "Human", "Needs human", "Title"],
                [(c["id"] or "-", f"#{c['number']}" if c["number"] != "-" else "-", c["state"], c["owner"],
                  c["human"], "yes" if c["needs_human"] else "", c["title"]) for c in cards])
    md += ["", "## Sessions", ""]
    md += table(["Card", "Role", "Machine", "Since (UTC)", "Open", "From"],
                [(k, v["role"], v["machine"], v["utc"], "yes" if v["open"] else "ended", v["from"])
                 for k, v in sorted(sess.items())])
    md += ["", "## Open PRs", ""]
    md += table(["PR", "Card", "Title", "Draft", "Checks"], pr_rows)
    md += ["", "## Gates", ""]
    md += table(["Gate", "Due", "Status"], gates)
    conn = connections_rows(root)
    if conn:
        md += ["", "## Connections", ""]
        md += [f"- {ln}" for ln in conn]
    md += ["", "## Problems", ""]
    md += [f"- {p}" for p in problems] or ["- none"]
    summary = (("PRACTICE " if banner else "") + f"STATUS-BOARD cards={len(cards)} needs-human={len(nh_lines)} prs={len(pr_rows)} "
               f"failing={sum(1 for r in pr_rows if r[4] == 'fail')} problems={len(problems)}")
    return "\n".join(md) + "\n", problems, summary


def connections_rows(root):
    """The last `tools/connections.py` result (kickoff --check writes Saved/connections.txt), or []."""
    try:
        with open(os.path.join(root, "Saved", "connections.txt"), encoding="utf-8") as fh:
            return [ln.rstrip() for ln in fh if ln.strip()]
    except OSError:
        return []


def to_html(md):
    out = ["<!doctype html>", '<meta charset="utf-8">', "<title>Status board</title>",
           "<style>body{font-family:sans-serif;margin:16px}table{border-collapse:collapse}"
           "td,th{border:1px solid #999;padding:2px 6px}</style>"]
    in_table = False
    for ln in md.splitlines():
        if ln.startswith("|"):
            cells = [html.escape(c.strip().replace("\\|", "|")) for c in re.split(r"(?<!\\)\|", ln.strip())[1:-1]]
            if set("".join(cells)) <= set("-"):
                continue
            if not in_table:
                out.append("<table>")
                in_table = True
                out.append("<tr>" + "".join(f"<th>{c}</th>" for c in cells) + "</tr>")
            else:
                out.append("<tr>" + "".join(f"<td>{c}</td>" for c in cells) + "</tr>")
            continue
        if in_table:
            out.append("</table>")
            in_table = False
        if ln.startswith("## "):
            out.append(f"<h2>{html.escape(ln[3:])}</h2>")
        elif ln.startswith("# "):
            out.append(f"<h1>{html.escape(ln[2:])}</h1>")
        elif ln.startswith("- "):
            out.append(f"<p>&bull; {html.escape(ln[2:])}</p>")
        elif ln.strip():
            out.append(f"<p>{html.escape(ln)}</p>")
    if in_table:
        out.append("</table>")
    return "\n".join(out) + "\n"


def main(argv=None, runner=gh_runner):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--source", choices=["gh", "local"], default=None)
    ap.add_argument("--from-json", metavar="DIR")
    ap.add_argument("--repo")
    ap.add_argument("--out")
    ap.add_argument("--html", action="store_true")
    ap.add_argument("--now", help="ISO time with offset (default: now)")
    ap.add_argument("--journal", help="journal db (default JOURNAL_DB, else .pipeline/journal.db)")
    ap.add_argument("--root", default=ROOT)
    a = ap.parse_args(argv)
    if bool(a.source) == bool(a.from_json):
        print("status_board: pass exactly one of --source gh|local or --from-json DIR", file=sys.stderr)
        return 2
    now = check_card.parse_time(a.now) if a.now else dt.datetime.now(dt.timezone.utc)
    if now is None:
        print(f"status_board: --now {a.now!r} is not ISO 8601 with an offset", file=sys.stderr)
        return 2
    journal = a.journal or os.environ.get("JOURNAL_DB") or os.path.join(a.root, ".pipeline", "journal.db")
    try:
        issues, prs, branches, tags = [], [], [], []
        if a.from_json:
            issues, prs = collect_json(a.from_json)
            source = "saved gh JSON"
        elif a.source == "gh":
            issues, prs = collect_gh(runner, a.repo)
            source = "gh"
        else:
            branches, tags = collect_local(a.root)
            source = "local git + journal"
        sessions = journal_sessions(journal)
    except InputError as e:
        print(f"status_board: {e}", file=sys.stderr)
        return 2
    md, problems, summary = build(a.root, now, source, issues, prs, branches, tags, sessions)
    out = a.out or os.path.join(a.root, "Saved", "status-board." + ("html" if a.html else "md"))
    os.makedirs(os.path.dirname(os.path.abspath(out)), exist_ok=True)
    with open(out, "w", encoding="utf-8") as fh:
        fh.write(to_html(md) if a.html else md)
    for p in problems:
        print(f"[status-board] {p}")
    print(f"{summary} -> {out}")
    return 1 if problems else 0


if __name__ == "__main__":
    sys.exit(main())
