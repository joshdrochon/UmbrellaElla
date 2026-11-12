#!/usr/bin/env python3
"""Durable local journal, so an agent (or the pipeline) resumes exactly where it stopped. Stdlib only.

GitHub stays the shared source of truth across machines. This journal is one machine's exact local record:
what ran, with which exit code, the last checkpoint and the next step. It lives in .pipeline/journal.db
(git-ignored; JOURNAL_DB overrides the path, for tests).

Append-only: one `events` table (id, utc, machine, role, card, branch, commit, kind, command, exit_code,
output_tail, note, next_step); kind is start | step | checkpoint | handoff | end. Triggers refuse UPDATE and
DELETE. WAL mode, synchronous=FULL, and each event is its own transaction, so a kill loses at most the
event being written. Output tails (last TAIL_LINES lines), commands and notes go through the secret patterns
in tools/secrets_check.py and every match is redacted before it is stored.

Commands (the card defaults to $JAM_CARD, then the branch name ue-<id>-...; the role to $JAM_ROLE):
  start      --role R --card C              records machine, branch and commit
  step       --card C --cmd "..." --exit N [--tail-file F]
  checkpoint --card C --note "..." [--next "..."]   (no --next: the last next step carries forward)
  handoff    --card C --note "..." --next "..."
  end        --card C [--note "..."]
  run        --card C -- <command...>        runs it, streams its output, records the step. The output is also
             written line by line to .pipeline/runs/<id>.log, so a run killed mid-way still shows its tail
  resume     --card C   last checkpoint, steps after it (an unfinished run shows as INTERRUPTED), the next
             step if the card has not ended, and a WARNING when the current commit or branch differs
  export     --card C   markdown for the GitHub handoff comment and the PR body (## Journal)
  commit-hook           used by the git post-commit hook (tools/install_git_hooks.py); never fails

Run records (A/B testing of builds; kickoff, practice and start_session write them at run start):
  runs [--last N]       the newest run records: id, time, kind, agent, pipeline version, GDD revision, prompt hash
  run-outcome --run N --outcome pass|fail|partial|stopped [--note "..."]   a tester's verdict on a run's build
  compare A B           two runs side by side: same prompt? same pipeline version? same GDD? sessions, failed
                        sessions and outcomes
  version               prints the pipeline version line (`pipeline <version>+<commit>[-dirty]`)
The GDD revision is the snapshot docs/gdd/CURRENT names, or the file $JAM_GDD names when kickoff --gdd chose one for
the run (tools/gdd_select.py; CURRENT itself unchanged).
Tables `runs` (agent, models, pipeline version and commit, GDD revision, the tester prompt), `run_prompts` (the exact
prompt of every session, with its card, role and model) and `run_outcomes` (each session's exit code, kickoff's end
line, a tester's verdict) sit in the same journal.db, append-only like `events`.

Exit 0 = ok, 2 = usage error (no card, bad arguments). `run` exits with the command's exit code.
"""
import argparse
import collections
import datetime as dt
import hashlib
import os
import re
import socket
import sqlite3
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, HERE)
from secrets_check import redact  # noqa: E402  same patterns as the repo secret scan

TAIL_LINES = 40
KINDS = ("start", "step", "checkpoint", "handoff", "end")
EXPORT_STEPS = 30
EXPORT_MARK = "journal.py export card="
SCHEMA = """
CREATE TABLE IF NOT EXISTS events (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  utc TEXT NOT NULL,
  machine TEXT,
  role TEXT,
  card TEXT NOT NULL,
  branch TEXT,
  "commit" TEXT,
  kind TEXT NOT NULL CHECK (kind IN ('start', 'step', 'checkpoint', 'handoff', 'end')),
  command TEXT,
  exit_code INTEGER,
  output_tail TEXT,
  note TEXT,
  next_step TEXT
);
CREATE INDEX IF NOT EXISTS events_card ON events(card, id);
CREATE TABLE IF NOT EXISTS runs (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  utc TEXT NOT NULL,
  machine TEXT,
  kind TEXT NOT NULL,
  agent TEXT,
  model TEXT,
  pipeline_version TEXT,
  pipeline_commit TEXT,
  gdd_revision TEXT,
  prompt TEXT,
  prompt_sha256 TEXT,
  note TEXT
);
CREATE TABLE IF NOT EXISTS run_prompts (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  run_id INTEGER NOT NULL,
  utc TEXT NOT NULL,
  card TEXT,
  role TEXT,
  model TEXT,
  prompt TEXT,
  prompt_sha256 TEXT
);
CREATE TABLE IF NOT EXISTS run_outcomes (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  run_id INTEGER NOT NULL,
  utc TEXT NOT NULL,
  kind TEXT NOT NULL CHECK (kind IN ('session', 'end', 'tester')),
  card TEXT,
  exit_code INTEGER,
  outcome TEXT,
  note TEXT
);
CREATE TRIGGER IF NOT EXISTS events_no_update BEFORE UPDATE ON events
  BEGIN SELECT RAISE(ABORT, 'journal is append-only'); END;
CREATE TRIGGER IF NOT EXISTS events_no_delete BEFORE DELETE ON events
  BEGIN SELECT RAISE(ABORT, 'journal is append-only'); END;
""" + "".join(f"""CREATE TRIGGER IF NOT EXISTS {t}_no_update BEFORE UPDATE ON {t}
  BEGIN SELECT RAISE(ABORT, 'journal is append-only'); END;
CREATE TRIGGER IF NOT EXISTS {t}_no_delete BEFORE DELETE ON {t}
  BEGIN SELECT RAISE(ABORT, 'journal is append-only'); END;
""" for t in ("runs", "run_prompts", "run_outcomes"))
PIPELINE_VERSION_FILE = os.path.join("pipeline", "VERSION")
PIPELINE_PATHS = ("tools", "pipeline", "prompts", "AGENTS.md", "CLAUDE.md", ".claude")
OUTCOMES = ("pass", "fail", "partial", "stopped")
COLS = ("id", "utc", "machine", "role", "card", "branch", "commit", "kind", "command", "exit_code",
        "output_tail", "note", "next_step")
RUN_NOTE = re.compile(r"^run #(\d+)\b")
RUNNING = "running"



def machine_label():
    """JAM_MACHINE, else JAM_HOST (tools/agent.sh sets it), else the hook's short hash of the machine name.
    The raw hostname never reaches an export or a PR body (it can carry a personal name)."""
    return (os.environ.get("JAM_MACHINE") or os.environ.get("JAM_HOST")
            or "host-" + hashlib.sha256(socket.gethostname().encode()).hexdigest()[:6])

def db_path():
    return os.environ.get("JOURNAL_DB") or os.path.join(ROOT, ".pipeline", "journal.db")


def runs_dir(path):
    return os.path.join(os.path.dirname(os.path.abspath(path)), "runs")


def connect(path=None):
    path = path or db_path()
    os.makedirs(os.path.dirname(os.path.abspath(path)), exist_ok=True)
    con = sqlite3.connect(path, timeout=15, isolation_level=None)  # autocommit; we open each transaction
    con.execute("PRAGMA journal_mode=WAL")
    con.execute("PRAGMA synchronous=FULL")
    con.executescript(SCHEMA)
    return con


def norm_card(card):
    """'ue-12' / '12' / 'UE-0.4a' -> 'UE-12' / 'UE-0.4a'; '#34' stays an issue number."""
    c = (card or "").strip()
    if not c:
        return ""
    if c.startswith("#"):
        return c
    c = re.sub(r"(?i)^ue-", "", c)
    return "UE-" + c


def git(*args, cwd=None):
    try:
        r = subprocess.run(["git", *args], cwd=cwd or os.getcwd(), capture_output=True, text=True, timeout=10)
    except (OSError, subprocess.SubprocessError):
        return None
    return r.stdout.strip() if r.returncode == 0 else None


def card_from_branch(branch):
    m = re.match(r"^ue-(\d+(?:\.\d+)?[a-z]?)-", branch or "")
    return "UE-" + m.group(1) if m else ""


def resolve_card(card):
    return norm_card(card or os.environ.get("JAM_CARD") or card_from_branch(git("rev-parse", "--abbrev-ref", "HEAD")))


def clean(text):
    return None if text is None else redact(text)


def tail(text, n=TAIL_LINES):
    if text is None:
        return None
    lines = text.splitlines()
    return clean("\n".join(lines[-n:]))


def now_utc():
    return dt.datetime.now(dt.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def add(con, card, kind, role=None, command=None, exit_code=None, output_tail=None, note=None, next_step=None,
        branch=None, commit=None):
    """Append one event in its own transaction. Returns its id."""
    if kind not in KINDS:
        raise ValueError(f"kind '{kind}' is not one of {', '.join(KINDS)}")
    if branch is None:
        branch = git("rev-parse", "--abbrev-ref", "HEAD")
    if commit is None:
        commit = git("rev-parse", "HEAD")
    if role is None:
        role = os.environ.get("JAM_ROLE") or last_value(con, card, "role")
    row = (now_utc(), machine_label(), role, card, branch, commit, kind,
           clean(command), exit_code, output_tail, clean(note), clean(next_step))
    con.execute("BEGIN IMMEDIATE")
    try:
        cur = con.execute('INSERT INTO events (utc, machine, role, card, branch, "commit", kind, command, exit_code,'
                          " output_tail, note, next_step) VALUES (?,?,?,?,?,?,?,?,?,?,?,?)", row)
        con.execute("COMMIT")
    except BaseException:
        con.execute("ROLLBACK")
        raise
    return cur.lastrowid


def events(con, card):
    cur = con.execute('SELECT id, utc, machine, role, card, branch, "commit", kind, command, exit_code, output_tail,'
                      " note, next_step FROM events WHERE card = ? ORDER BY id", (card,))
    return [dict(zip(COLS, r)) for r in cur.fetchall()]


def last_value(con, card, col):
    r = con.execute(f'SELECT "{col}" FROM events WHERE card = ? AND "{col}" IS NOT NULL ORDER BY id DESC LIMIT 1',
                    (card,)).fetchone()
    return r[0] if r else None


def last_mark(evs):
    """The newest checkpoint or handoff, or None."""
    for e in reversed(evs):
        if e["kind"] in ("checkpoint", "handoff"):
            return e
    return None


def finished_runs(evs):
    return {int(m.group(1)) for e in evs if e["kind"] == "step" and (m := RUN_NOTE.match(e["note"] or ""))}


def interrupted(e, done):
    return e["kind"] == "step" and e["exit_code"] is None and e["note"] == RUNNING and e["id"] not in done


def run_log_tail(path, run_id, n=TAIL_LINES):
    try:
        with open(os.path.join(runs_dir(path), f"{run_id}.log"), encoding="utf-8", errors="replace") as fh:
            return tail(fh.read(), n)
    except OSError:
        return None


# ---------------------------------------------------------------- run records
def sha256(text):
    return hashlib.sha256((text or "").encode("utf-8")).hexdigest()


def pipeline_version(root=ROOT):
    """{'version', 'commit', 'dirty', 'string'}. string = `<pipeline/VERSION>+<short commit>[-dirty]`; dirty when
    a pipeline path (tools/, pipeline/, prompts/, AGENTS.md, ...) differs from the commit."""
    try:
        with open(os.path.join(root, PIPELINE_VERSION_FILE), encoding="utf-8") as fh:
            ver = fh.read().strip() or "0"
    except OSError:
        ver = "0"
    commit = git("rev-parse", "HEAD", cwd=root) or ""
    st = git("status", "--porcelain", "--", *PIPELINE_PATHS, cwd=root)
    dirty = bool(st)
    string = f"{ver}+{commit[:7] or 'nocommit'}" + ("-dirty" if dirty else "")
    return {"version": ver, "commit": commit, "dirty": dirty, "string": string}


GDD_ENV = "JAM_GDD"  # run-scoped GDD (tools/gdd_select.py, kickoff --gdd): this process and its sessions only


def gdd_revision(root=ROOT):
    """'1.3 (GDD-1.3.md sha256 <12 hex>)' from docs/gdd/CURRENT, or 'unknown'. With $JAM_GDD (a GDD file chosen
    for this run by kickoff --gdd): '1.4 (<path> sha256 <12 hex>, --gdd; CURRENT GDD-1.3.md)'."""
    if os.environ.get(GDD_ENV):
        return _gdd_override(root, os.environ[GDD_ENV])
    try:
        with open(os.path.join(root, "docs", "gdd", "CURRENT"), encoding="utf-8") as fh:
            name = fh.read().strip()
        with open(os.path.join(root, "docs", "gdd", name), "rb") as fh:
            digest = hashlib.sha256(fh.read()).hexdigest()[:12]
    except OSError:
        return "unknown"
    m = re.match(r"GDD-(.+)\.md$", name)
    return f"{m.group(1) if m else name} ({name} sha256 {digest})"


def _gdd_override(root, path):
    full = path if os.path.isabs(path) else os.path.join(root, path)
    try:
        with open(full, "rb") as fh:
            raw = fh.read()
    except OSError:
        return f"unknown ({GDD_ENV}={path} is missing)"
    m = re.search(rb"^\|\s*Revision\s*\|\s*([^|]+?)\s*\|", raw, re.M)
    rev = m.group(1).decode("utf-8", "replace").strip() if m else "?"
    shown = os.path.relpath(os.path.realpath(full), os.path.realpath(root)).replace(os.sep, "/")
    if shown.startswith(".."):
        shown = full.replace(os.sep, "/")
    try:
        with open(os.path.join(root, "docs", "gdd", "CURRENT"), encoding="utf-8") as fh:
            cur = fh.read().strip() or "?"
    except OSError:
        cur = "?"
    return f"{rev} ({shown} sha256 {hashlib.sha256(raw).hexdigest()[:12]}, --gdd; CURRENT {cur})"


def _insert(con, sql, row):
    con.execute("BEGIN IMMEDIATE")
    try:
        cur = con.execute(sql, row)
        con.execute("COMMIT")
    except BaseException:
        con.execute("ROLLBACK")
        raise
    return cur.lastrowid


def start_run(con, kind, agent=None, model=None, prompt=None, note=None, root=ROOT):
    """One run record at run start. Returns its id. The prompt is stored exactly (secrets redacted)."""
    v = pipeline_version(root)
    prompt = clean(prompt)
    return _insert(con, "INSERT INTO runs (utc, machine, kind, agent, model, pipeline_version, pipeline_commit, "
                        "gdd_revision, prompt, prompt_sha256, note) VALUES (?,?,?,?,?,?,?,?,?,?,?)",
                   (now_utc(), machine_label(), kind, agent, model, v["string"], v["commit"], gdd_revision(root),
                    prompt, sha256(prompt) if prompt else None, clean(note)))


def add_run_prompt(con, run_id, card, role, model, prompt):
    prompt = clean(prompt)
    return _insert(con, "INSERT INTO run_prompts (run_id, utc, card, role, model, prompt, prompt_sha256) "
                        "VALUES (?,?,?,?,?,?,?)", (run_id, now_utc(), card, role, model, prompt, sha256(prompt)))


def add_run_outcome(con, run_id, kind, outcome=None, exit_code=None, card=None, note=None):
    return _insert(con, "INSERT INTO run_outcomes (run_id, utc, kind, card, exit_code, outcome, note) "
                        "VALUES (?,?,?,?,?,?,?)", (run_id, now_utc(), kind, card, exit_code, outcome, clean(note)))


RUN_COLS = ("id", "utc", "machine", "kind", "agent", "model", "pipeline_version", "pipeline_commit", "gdd_revision",
            "prompt", "prompt_sha256", "note")


def get_run(con, run_id):
    r = con.execute("SELECT " + ", ".join(RUN_COLS) + " FROM runs WHERE id = ?", (run_id,)).fetchone()
    if not r:
        return None
    run = dict(zip(RUN_COLS, r))
    run["prompts"] = [dict(zip(("card", "role", "model", "prompt_sha256"), x)) for x in con.execute(
        "SELECT card, role, model, prompt_sha256 FROM run_prompts WHERE run_id = ? ORDER BY id", (run_id,))]
    run["outcomes"] = [dict(zip(("kind", "card", "exit_code", "outcome", "note"), x)) for x in con.execute(
        "SELECT kind, card, exit_code, outcome, note FROM run_outcomes WHERE run_id = ? ORDER BY id", (run_id,))]
    return run


def runs_text(con, last=20):
    rows = con.execute("SELECT id, utc, kind, agent, pipeline_version, gdd_revision, prompt_sha256 FROM runs "
                       "ORDER BY id DESC LIMIT ?", (last,)).fetchall()
    if not rows:
        return "journal: no run records yet (tools/kickoff.sh writes one at run start)"
    out = ["id | started | kind | agent | pipeline | GDD | prompt"]
    for i, utc, kind, agent, ver, gdd, ph in rows:
        out.append(f"{i} | {utc} | {kind} | {agent or '?'} | {ver} | {(gdd or '?').split(' (')[0]} | "
                   f"{(ph or 'none')[:12]}")
    return "\n".join(out)


def _final(run):
    for o in reversed(run["outcomes"]):
        if o["kind"] == "tester":
            return f"{o['outcome']} (tester{': ' + o['note'] if o['note'] else ''})"
    for o in reversed(run["outcomes"]):
        if o["kind"] == "end":
            return o["outcome"] or o["note"] or "ended"
    return "no outcome yet"


def compare_text(a, b):
    """Two run records side by side, for A/B: same prompt, same pipeline, same GDD, then the outcomes."""
    def prompts_sig(r):
        return sha256("\n".join(p["prompt_sha256"] or "" for p in r["prompts"]))[:12] if r["prompts"] else "none"

    def failed(r):
        return sum(1 for o in r["outcomes"] if o["kind"] == "session" and o["exit_code"] not in (0, None))
    rows = [("started", a["utc"], b["utc"], None),
            ("machine", a["machine"], b["machine"], None),
            ("kind", a["kind"], b["kind"], None),
            ("agent", a["agent"], b["agent"], True),
            ("model", a["model"], b["model"], True),
            ("pipeline version", a["pipeline_version"], b["pipeline_version"], True),
            ("GDD revision", a["gdd_revision"], b["gdd_revision"], True),
            ("tester prompt sha256", (a["prompt_sha256"] or "none")[:12], (b["prompt_sha256"] or "none")[:12], True),
            ("session prompts", f"{len(a['prompts'])} ({prompts_sig(a)})", f"{len(b['prompts'])} ({prompts_sig(b)})",
             True),
            ("failed sessions", str(failed(a)), str(failed(b)), None),
            ("outcome", _final(a), _final(b), None)]
    w = max(len(str(x[1])) for x in rows) + 2
    out = [f"compare run {a['id']} vs run {b['id']}", f"{'field':22}| {'run ' + str(a['id']):{w}}| "
           f"{'run ' + str(b['id']):{w}}| same"]
    for name, x, y, judged in rows:
        same = ("yes" if x == y else "NO") if judged else ""
        out.append(f"{name:22}| {str(x):{w}}| {str(y):{w}}| {same}")
    same_input = all(x == y for _, x, y, j in rows if j and _ != "session prompts")
    out.append("verdict: same prompt, pipeline, GDD, agent and model: an A/B of luck alone" if same_input else
               "verdict: inputs differ (rows marked NO): outcomes are not a like-for-like A/B")
    return "\n".join(out)


def resume_text(con, card, path, cur_commit=None, cur_branch=None):
    evs = events(con, card)
    if not evs:
        return (f"journal: no events for {card} on this machine ({path}).\n"
                "Read the card and PR comments on GitHub; start with: python3 tools/journal.py start --card " + card)
    done = finished_runs(evs)
    fin = {int(RUN_NOTE.match(e["note"]).group(1)): e for e in evs if RUN_NOTE.match(e["note"] or "")}
    mark = last_mark(evs)
    out = [f"journal: {card} ({len(evs)} events, {path})"]
    if mark:
        out.append(f"Last {mark['kind']} #{mark['id']} at {mark['utc']} by {mark['role'] or '?'} on {mark['machine']},"
                   f" branch {mark['branch'] or '?'}, commit {(mark['commit'] or '?')[:12]}")
        out.append(f"  note: {mark['note'] or ''}")
        out.append(f"  next: {mark['next_step'] or '(none written)'}")
        after = [e for e in evs if e["id"] > mark["id"]]
    else:
        out.append("No checkpoint yet; every event since the start follows.")
        after = evs
    steps = [e for e in after if e["kind"] in ("step", "start", "end") and not RUN_NOTE.match(e["note"] or "")]
    out.append("Since then:" if steps else "Since then: nothing")
    for e in steps:
        if interrupted(e, done):
            out.append(f"  #{e['id']} {e['utc']} INTERRUPTED (never finished): {e['command']}")
            t = run_log_tail(path, e["id"])
            if t:
                out += ["    | " + ln for ln in t.splitlines()]
        elif e["kind"] == "step":
            code = fin[e["id"]]["exit_code"] if e["id"] in fin else e["exit_code"]
            out.append(f"  #{e['id']} {e['utc']} exit={code} {e['command']}")
        else:
            out.append(f"  #{e['id']} {e['utc']} {e['kind']} {e['note'] or ''}".rstrip())
    ended = any(e["kind"] == "end" for e in after)
    nxt = mark["next_step"] if mark else None
    if ended:
        out.append("Card session ended (end event); no unfinished next step.")
    elif nxt:
        out.append(f"UNFINISHED next step: {nxt}")
    else:
        out.append("UNFINISHED: no next step written; write one with journal.py checkpoint --next")
    j_commit = last_value(con, card, "commit")
    j_branch = last_value(con, card, "branch")
    if cur_commit and j_commit and cur_commit != j_commit:
        out.append(f"WARNING: current commit {cur_commit[:12]} differs from the journaled {j_commit[:12]};"
                   " re-run the checks the journal claims before you trust them")
    if cur_branch and j_branch and cur_branch != j_branch:
        out.append(f"WARNING: current branch {cur_branch} differs from the journaled {j_branch}")
    return "\n".join(out)


def md_cell(text):
    return (text or "").replace("|", "\\|").replace("\n", " ").replace("`", "'")[:160]


def export_text(con, card):
    evs = events(con, card)
    done = finished_runs(evs)
    fin = {int(RUN_NOTE.match(e["note"]).group(1)): e for e in evs if RUN_NOTE.match(e["note"] or "")}
    machine = evs[-1]["machine"] if evs else machine_label()
    commit = (last_value(con, card, "commit") or "none")[:12]
    out = ["### Journal", f"`{EXPORT_MARK}{card} machine={machine} commit={commit} events={len(evs)}`", ""]
    rows = []
    for e in evs:
        if e["kind"] != "step" or RUN_NOTE.match(e["note"] or ""):
            continue
        if interrupted(e, done):
            code = "interrupted"
        elif e["id"] in fin:
            code = str(fin[e["id"]]["exit_code"])
        else:
            code = str(e["exit_code"])
        rows.append(f"| {e['id']} | {e['utc']} | {code} | `{md_cell(e['command'])}` |")
    if rows:
        skipped = len(rows) - EXPORT_STEPS
        out += ["| # | UTC | Exit | Command |", "|---|---|---|---|"] + rows[-EXPORT_STEPS:]
        if skipped > 0:
            out.append(f"({skipped} older steps not shown; `journal.py resume --card {card}` on {machine})")
    else:
        out.append("Steps: none journaled.")
    mark = last_mark(evs)
    out.append("")
    if mark:
        out.append(f"Last {mark['kind']}: {mark['utc']} {mark['role'] or ''}: {md_cell(mark['note'])}")
        out.append(f"Next step: {md_cell(mark['next_step']) or 'none written'}")
    else:
        out.append("Last checkpoint: none")
        out.append("Next step: none written")
    return "\n".join(out)


def run_cmd(con, card, path, argv):
    """Run argv, stream its output, journal it. A kill mid-run leaves the start step with no finish."""
    if argv and argv[0] == "--":
        argv = argv[1:]
    if not argv:
        print("journal run: no command after --", file=sys.stderr)
        return 2
    cmdline = subprocess.list2cmdline(argv) if os.name == "nt" else " ".join(_q(a) for a in argv)
    rid = add(con, card, "step", command=cmdline, note=RUNNING)
    os.makedirs(runs_dir(path), exist_ok=True)
    last = collections.deque(maxlen=TAIL_LINES)
    code = None
    try:
        with open(os.path.join(runs_dir(path), f"{rid}.log"), "w", encoding="utf-8") as log:
            try:
                p = subprocess.Popen(argv, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True,
                                     errors="replace", bufsize=1)
            except OSError as e:
                print(f"journal run: {e}", file=sys.stderr)
                code = 127
                last.append(str(e))
            else:
                for line in p.stdout:
                    sys.stdout.write(line)
                    sys.stdout.flush()
                    log.write(redact(line))
                    log.flush()
                    last.append(line.rstrip("\n"))
                code = p.wait()
    except KeyboardInterrupt:
        code = 130
    add(con, card, "step", command=cmdline, exit_code=code, output_tail=tail("\n".join(last)), note=f"run #{rid}")
    return code if code is not None else 1


def _q(a):
    return a if re.fullmatch(r"[\w@%+=:,./-]+", a) else "'" + a.replace("'", "'\\''") + "'"


def read_tail_file(path):
    if not path:
        return None
    with open(path, encoding="utf-8", errors="replace") as fh:
        return tail(fh.read())


def run_command(a):
    path = db_path()
    try:
        con = connect(path)
    except sqlite3.Error as e:
        print(f"journal: cannot open {path}: {e}", file=sys.stderr)
        return 2
    try:
        if a.action == "runs":
            print(runs_text(con, a.last))
            return 0
        if a.action == "run-outcome":
            if not get_run(con, a.run):
                print(f"journal: no run {a.run} (python3 tools/journal.py runs lists them)", file=sys.stderr)
                return 2
            i = add_run_outcome(con, a.run, "tester", outcome=a.outcome, note=a.note)
            print(f"journal: run {a.run} outcome #{i} {a.outcome}")
            return 0
        ra, rb = get_run(con, a.a), get_run(con, a.b)
        missing = [str(n) for n, r in ((a.a, ra), (a.b, rb)) if not r]
        if missing:
            print(f"journal: no run {', '.join(missing)} (python3 tools/journal.py runs lists them)", file=sys.stderr)
            return 2
        print(compare_text(ra, rb))
        return 0
    finally:
        con.close()


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="action", required=True)
    rp = sub.add_parser("runs")
    rp.add_argument("--last", type=int, default=20)
    ro = sub.add_parser("run-outcome")
    ro.add_argument("--run", type=int, required=True)
    ro.add_argument("--outcome", required=True, choices=OUTCOMES)
    ro.add_argument("--note")
    cp = sub.add_parser("compare")
    cp.add_argument("a", type=int)
    cp.add_argument("b", type=int)
    sub.add_parser("version")
    for name in ("start", "step", "checkpoint", "handoff", "end", "resume", "export", "run", "commit-hook"):
        p = sub.add_parser(name)
        p.add_argument("--card")
        if name == "start":
            p.add_argument("--role")
            p.add_argument("--note")
        if name == "step":
            p.add_argument("--cmd", required=True)
            p.add_argument("--exit", type=int, required=True)
            p.add_argument("--tail-file")
            p.add_argument("--note")
        if name in ("checkpoint", "handoff"):
            p.add_argument("--note", required=True)
            p.add_argument("--next", required=(name == "handoff"))
        if name == "end":
            p.add_argument("--note")
        if name == "run":
            p.add_argument("command", nargs=argparse.REMAINDER)
    a = ap.parse_args(argv)
    if a.action == "version":
        print("pipeline " + pipeline_version()["string"])
        return 0
    if a.action in ("runs", "run-outcome", "compare"):
        return run_command(a)
    card = resolve_card(a.card)
    if not card:
        if a.action == "commit-hook":
            return 0
        print("journal: no card; pass --card UE-<id>, set JAM_CARD, or work on a ue-<id>-<name> branch",
              file=sys.stderr)
        return 2
    path = db_path()
    try:
        con = connect(path)
    except sqlite3.Error as e:
        print(f"journal: cannot open {path}: {e}", file=sys.stderr)
        return 0 if a.action == "commit-hook" else 2
    try:
        if a.action == "start":
            role = a.role or os.environ.get("JAM_ROLE")
            i = add(con, card, "start", role=role, note=a.note)
            print(f"journal: start #{i} {card} role={role or '?'}")
        elif a.action == "step":
            i = add(con, card, "step", command=a.cmd, exit_code=a.exit, output_tail=read_tail_file(a.tail_file),
                    note=a.note)
            print(f"journal: step #{i} exit={a.exit}")
        elif a.action in ("checkpoint", "handoff"):
            nxt = a.next if a.next is not None else last_value(con, card, "next_step")
            i = add(con, card, a.action, note=a.note, next_step=nxt)
            print(f"journal: {a.action} #{i} next: {nxt or '(none)'}")
        elif a.action == "end":
            i = add(con, card, "end", note=a.note)
            print(f"journal: end #{i} {card}")
        elif a.action == "resume":
            print(resume_text(con, card, path, git("rev-parse", "HEAD"), git("rev-parse", "--abbrev-ref", "HEAD")))
        elif a.action == "export":
            print(export_text(con, card))
        elif a.action == "run":
            return run_cmd(con, card, path, a.command)
        elif a.action == "commit-hook":
            try:
                add(con, card, "step", command="git commit", exit_code=0,
                    note=git("log", "-1", "--format=%h %s"))
            except sqlite3.Error:
                pass
            return 0
    except OSError as e:
        print(f"journal: {e}", file=sys.stderr)
        return 2
    finally:
        con.close()
    return 0


if __name__ == "__main__":
    sys.exit(main())
