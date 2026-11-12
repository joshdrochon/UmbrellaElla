#!/usr/bin/env python3
"""One command for the whole jam loop, for Claude Code and Codex alike. A human runs it, from a plain terminal.

  tools/kickoff.sh                               (Windows: tools\\kickoff.ps1) no options: print the pipeline version,
                                                 run the connection check, then start with the agent CLI it finds
                                                 (asks one question when both Claude Code and Codex are installed)
  tools/kickoff.sh [--agent claude|codex] [--split [KIND=AGENT,...]] [--until G1]
  options: --check (the pipeline version, the team-art line and the connection check only; exit 1 when a team-art
           image under Assets/ or Mockups/ cannot be read) --dry-run (the plan, nothing launched or written)
           --prompt TEXT / --prompt-file F (the tester's own prompt: recorded and added to every session prompt)
           --gdd REV|FILE (test this GDD revision: checked first by tools/gdd_select.py, then run-scoped and recorded;
           --set-current also points docs/gdd/CURRENT at it)
           --practice (write and commit .pipeline-practice in a test repo) --parallel N (default 2)
           --watch MIN (keep polling for human answers instead of stopping when only humans can move)
           --split [KIND=AGENT,...] (or KICKOFF_SPLIT): with both Claude Code and Codex installed, run the session kinds
           build, review, critic and producer on different CLIs; no value = build=codex,review=claude,critic=claude,
           producer=claude (a kind left out stays on --agent). Each session takes its model from its CLI's column in
           pipeline/agent-ops/model-tiers.md. With one CLI installed it says so and runs every session on it

No typing after that. It:
  1. checks the connections (tools/connections.py) and refuses to start while a required one is missing;
     installs the git hooks (tools/install_git_hooks.py); names any missing API key in one line;
  2. before the jam start without practice mode (the team repo), runs PRE-JAM mode: it files and runs only the
     pre-jam cards (pipeline/day0-cards.md "Pre-jam cards:": tools, agent setup, rules and the synthetic workbench
     sample, Official Rules 7(h)); every other card waits for the start (D39). Practice mode runs every card;
  3. runs the Producer in a fresh non-interactive session: it files or refreshes the cards from
     pipeline/day0-cards.md and the plan, with each `Human:` from the docs/jam-brief.md People table; kickoff files
     them, then runs check_card on every open card until 0 problems (no round cap; needs-human only after 3 Producer
     cycles in a row with the same problems and no fewer of them, D-new-no-round-cap);
  4. repeatedly picks ready cards (every After card merged, the lane free, check_card passes) and runs each in a
     fresh non-interactive session (`claude -p` or `codex exec`) with JAM_ROLE, the card and the model tier from
     pipeline/agent-ops/model-tiers.md, up to N at once with non-overlapping lanes, each in its own git worktree
     (.pipeline/worktrees/<branch>). The agent commits; kickoff runs the queued asset API steps
     (tools/assetgen.py fulfil, with the keys the agent never sees), pushes, opens the PR from the agent's pr.md,
     runs the card's reviewer role in another fresh session and posts its verdict. A session that crashes, times out,
     exits non-zero or produces nothing runs again in the same run; MAX_FAILS in a row label the card blocked and
     raise NEEDS HUMAN with the exit code and the session's last line (AGENTS.md section 6);
  4a. merge: on an approved PR kickoff itself squash-merges (`gh pr merge --squash --match-head-commit`) once every
     required CI check on the head is green (pending: it waits, KICKOFF_CI_POLL / KICKOFF_CI_WAIT), the reviewer's
     last verdict after the last push is approve, and tools/check_pr.py passes on the head (rule artship is the art
     ship gate); a PR that changes a gate path also passes this checkout's own check_pr rule gate. Then it closes
     the card; after card 0.16 or 0.17 merges it sets their repo settings itself (gh variable set, branch protection
     with the required check `checks`, Actions may open PRs; repo_settings) and reads them back on the card. Agent
     sessions never push or merge. A failed merge is tried again, then NEEDS HUMAN `merge PR #N: ...` with the gh
     error or the gate that blocked it;
  4e. jam-start: when card 0.3 starts (on or after the Official Rules start, never in a practice repo), kickoff tags
     `jam-start` on main and pushes the tag (ensure_jam_start; an existing tag is never moved);
  4f. a card whose Done-when says `Runs on: the Windows packaging machine` is built and fixed only by a kickoff
     running there; kickoff anywhere else lists it as waiting (its review and merge run anywhere). Its twin,
     `Runs on: the Mac build machine` (the Mac scripts, tools/ue/*.sh), is built only by a kickoff on macOS;
  4g. --until G1 (KICKOFF_UNTIL): a run that targets a gate. It builds only the cards on the gate's path: the Day-0
     cards pipeline/day0-cards.md lists on its `**G1 cards:**` line, every card whose MVP item docs/jam-brief.md tags
     [G1] (filed by the Producer once card 0.3 merges), and every card those list in After. When all of them are
     merged it runs the gate's Mac package itself: `bash tools/ue/daily.sh` on main in .pipeline/worktrees/g1-package
     (build, tests, package, smoke; KICKOFF_PACKAGE_CMD replaces it in tests). A DAILY line with package and smoke
     PASS ends the run (`KICKOFF G1 reached: ...`); a failure goes to the Producer as a bug card on the path, and the
     same failure 3 times in a row fails the run. It never closes the gate. `--dry-run --until G1` and
     `--check --until G1` print the path in order from the files and fail on any step on it that needs a person or
     the Windows machine;
  4h. audio loop: when a builder session started `tools/audio_loop.py start` (Saved/AudioLoop/<card>/state.json),
     kickoff runs each piece's round, a fresh blind CRITIC session on its packet (audio role, critic tier), the
     verdict, and on a fail a builder session with the critic's gap, until every piece passes (no round cap; the
     stuck rule raises NEEDS HUMAN after 3 flat rounds). A piece whose takes are all tracked placeholders (the audio
     API failed: no key, an HTTP error, no credits left) is not judged. Then it appends `audio_loop.py close` to pr.md;
  4b. art gate (Josh, 10 Nov: art checks are automatic): after a builder session whose PR built or packaged the game
     (a pasted SMOKE_OK line, or a change that needs package evidence: maps, Config, Content/, Art/, UI or presenter
     code; tools/check_pr.py needs_package), it re-runs tools/art_check.py, tools/screen_check.py and
     tools/art_judge.py scene on each smoke screenshot the session made (Saved/Logs/pipeline/*-shot.png) and checks the
     pasted smoke has their PASS lines (check_pr rule art). A failure is a failed build: the same agent gets the
     failure lines and fixes the visual (regenerate, rescale, reposition) in the same card, then the gate runs again;
     no round cap: 3 rounds in a row with the same failures and no fewer of them label the card blocked and raise
     NEEDS HUMAN (D-new-no-round-cap). No human approves a
     look; GitHub CI cannot run Unreal, so this runs here, on the build machine;
  4c. art loop (tools/art_loop.py): on an art card (pipeline/art/references.json assigns it references) each piece
     the builder lists in $JAM_OUTBOX/art-pieces.json ({"<piece>": "<file in the worktree>"}) is judged by a PANEL
     of 3 fresh blind CRITIC sessions per pair (tools/art_loop.py run_piece): against every reference of the piece's
     element, its quality-bar image, every reference sheet in motion (a sheet) and the newest in-engine capture
     against the key art. Each folder hides the pair among calibration pairs; a session that misses one does not
     count. Until every counted session picks ours or SAME on every pair and the measured checks pass, the GAP goes
     back to the builder (a change to the Blender scene). No round cap; 3 rounds in a row with no improvement raise
     NEEDS HUMAN with the first and latest image and the gaps. On a pass kickoff commits the <stem>.artloop.json
     record itself (agent sessions never write one) and appends the file-bound `art_loop: PASS ... file= sha=`
     line to pr.md (check_pr rules artloop and artship);
  4d. daily on Windows (D-new-merge-daily): on the native Windows packaging machine, and only while gates.json
     native_windows_shell is allow, each merged card gets a QA and Build session that runs tools\\ue\\daily.ps1 on its
     merge commit (worktree .pipeline/worktrees/qa-daily, one at a time); the DAILY line goes on the card and into
     this checkout's daily record. Elsewhere, or while it is block, a person runs daily.ps1 as before;
  5. stops only at the human checkpoints (pipeline/human-checkpoints.md): it labels the issue needs-human, comments
     `NEEDS HUMAN: <who> <what> <link> <UTC time>`, prints one line, and keeps running the other cards. It never
     closes a gate or submits. A grace-expired ask goes to its director session (2 h grace default), except
     gate closes and uploads, which wait for a human. Agents own every card: a gate-path change comes back as
     the session's $JAM_OUTBOX/gate.patch, kept under .pipeline/gate-patches/UE-<id>/, and kickoff applies it itself
     with `tools/git_gate.py apply UE-<id> --auto` (by=kickoff): the tools, not a person, decide (every path in the
     card's lane, no guardrail enforcer changed, no guardrail file loosened). A refused patch goes back to the
     builder with the reasons (MAX_FAILS, then blocked and asked). A card whose PR merged is closed by
     kickoff; a GitHub-only card (no files) is checked by its reviewer role and closed on approve;
  6. journals every session, push, PR, verdict and ask in the SQLite journal (tools/journal.py), so a second run
     picks up where the first stopped; a journal error is reported once and the run goes on without it;
  7. writes a run record at run start (journal.py runs): the tester prompt, the pipeline version and commit, the
     agent, the model of each role and the GDD revision, then every session's exact prompt and exit code, and the
     end line. `journal.py compare A B` lines two runs up for A/B testing.
Every failure prints one plain line that says what to type or do next (KICKOFF_DEBUG=1 shows the Python traceback).

Agent contract (AGENTS.md "Kickoff sessions"): env JAM_ROLE, JAM_CARD, JAM_ISSUE, JAM_OUTBOX, JAM_KICKOFF=1; the
agent writes $JAM_OUTBOX/pr.md, review.md (VERDICT: approve|changes), cards/<UE-id>.json (Producer),
needs-human.txt, comment.md, gate.patch (its gate-path changes as a git patch), and commits but never pushes.
Agent commands (every Codex flag below is in `codex exec --help`, Codex CLI 0.167.0):
  claude -p <prompt> --model <id> --permission-mode bypassPermissions --disallowedTools <push/merge> [--effort high] [--mcp-config F --strict-mcp-config]
  codex exec -s workspace-write -C <worktree> --add-dir <git dir> --add-dir <outbox> -o <outbox>/last-message.md
        -c shell_environment_policy.inherit=all [-m <model>] [-c model_reasoning_effort="high"] <prompt>
  [VERIFY on Codex CLI] the config keys shell_environment_policy.inherit (shown as an example in the help) and
  model_reasoning_effort, and the GPT model IDs in model-tiers.md (an empty cell: Codex uses its default model).
Test seams: KICKOFF_AGENT_CMD replaces the agent program (a stub), KICKOFF_GH the gh program, KICKOFF_NOW the clock,
KICKOFF_SKIP_CHECK=1 skips the connection check (tests only), KICKOFF_PACKAGING_MACHINE=1 plays the Windows packaging
machine (it builds `Runs on:` cards), KICKOFF_MAC_MACHINE=1 plays the Mac build machine (the sandbox plays both, so a sim
runs the same on every OS).
Exit 0 = ran (or only humans can move now), 2 = usage or refused (inside an agent session, real repo --practice,
a --gdd file that fails its import check), 3 = before the jam start without practice mode: only the pre-jam cards ran
(PRE-JAM mode), 4 = a required connection is missing.
"""
import argparse
import concurrent.futures
import traceback
import datetime as dt
import json
import os
import re
import shlex
import shutil
import subprocess
import sys
import tempfile
import threading
import time

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, HERE)
# What a pipeline install has at the repo root. Kickoff checks it before anything else (a missing file would
# otherwise end in a Python traceback).
PIPELINE_FILES = ("AGENTS.md", "tools/journal.py", "tools/check_card.py", "tools/connections.py", "tools/keys.py",
                  "tools/practice.py", "tools/start_session.py", "pipeline/agent-ops/gates.json",
                  "pipeline/day0-cards.md", "pipeline/agent-ops/model-tiers.md", "docs/jam-brief.md")
AGENTS_SECTION = "Kickoff sessions"
TEAM_REPO_URL = "https://github.com/RickTheBuilder/GameJam2026.git"


def glob_shots(wt):
    d = os.path.join(wt, "Saved", "Logs", "pipeline")
    return sorted(os.path.join(d, f) for f in (os.listdir(d) if os.path.isdir(d) else []) if f.endswith("-shot.png"))


def me():
    """The command the person types, on this OS."""
    return "tools\\kickoff.ps1" if os.name == "nt" else "tools/kickoff.sh"


def git_top(root):
    try:
        p = subprocess.run(["git", "-C", root, "rev-parse", "--show-toplevel"], capture_output=True, text=True,
                           timeout=10)
    except (OSError, subprocess.SubprocessError):
        return None
    return os.path.realpath(p.stdout.strip()) if p.returncode == 0 and p.stdout.strip() else None


def install_problem(root=ROOT):
    """One plain line when the pipeline is not installed at the repo root, else None."""
    top = git_top(root)
    if top is None:
        return (f"kickoff: {root} is not a git repo, so the pipeline cannot run here. Fix: type "
                f"`git clone {TEAM_REPO_URL}`, go into the new GameJam2026 folder, and run {me()} there.")
    if top != os.path.realpath(root):
        copy = (f'robocopy "{root}" "{top}" /E' if os.name == "nt" else f'cp -R "{root}/." "{top}/"')
        return (f"kickoff: the pipeline is in {root}, but it must sit at the repo root {top}. Fix: type `{copy}`, "
                f"then run {me()} from {top}.")
    missing = [f for f in PIPELINE_FILES if not os.path.isfile(os.path.join(root, f))]
    if not missing:
        try:
            with open(os.path.join(root, "AGENTS.md"), encoding="utf-8") as fh:
                if AGENTS_SECTION not in fh.read():
                    missing = [f"the '{AGENTS_SECTION}' section of AGENTS.md"]
        except OSError:
            missing = ["AGENTS.md"]
    if missing:
        return (f"kickoff: the pipeline is not fully installed in {root} (missing: {', '.join(missing[:3])}). Fix: "
                f"type `git pull origin main` in that folder, then run {me()} again.")
    return None


_PROBLEM = install_problem()
if _PROBLEM and __name__ == "__main__":
    print(_PROBLEM, flush=True)
    sys.exit(2)
import check_card  # noqa: E402
import check_pr  # noqa: E402
import git_gate  # noqa: E402
import gdd_select  # noqa: E402
import journal  # noqa: E402
import keys  # noqa: E402
import practice  # noqa: E402
import repo_map  # noqa: E402
import start_session  # noqa: E402

GATES = os.path.join(ROOT, "pipeline", "agent-ops", "gates.json")
WORKTREES = os.path.join(ROOT, ".pipeline", "worktrees")
GATE_PATCHES = os.path.join(ROOT, ".pipeline", "gate-patches")
PATCH_PATH = re.compile(r"^\+\+\+ b/(\S+)|^diff --git a/\S+ b/(\S+)", re.M)
# A card whose Done-when says it runs on the Windows packaging machine: only a kickoff there builds or fixes it
# (pipeline/day0-cards.md `Runs on:` lines); kickoff anywhere else leaves it waiting.
RUNS_ON_WINDOWS = re.compile(r"\bRuns on: the Windows packaging machine\b", re.I)
# Its twin: a card whose Done-when runs the Mac scripts (tools/ue/*.sh) says `Runs on: the Mac build machine`; a kickoff
# on Windows leaves it waiting, so a Mac line never lands on a machine that cannot run it.
RUNS_ON_MAC = re.compile(r"\bRuns on: the Mac build machine\b", re.I)
UNTIL_GATES = ("G1", "G2", "G3", "G4")
OUTBOXES = os.path.join(ROOT, ".pipeline", "outbox")
LABELS = ("task", "todo", "doing", "review", "blocked", "needs-human", "cut", "superseded", "gate")
NOT_DONE = {"cut", "superseded"}
HIGH_EFFORT = ("Hard calls", "Critic")   # model-tiers.md: these tiers run at high reasoning effort
SPLIT_KINDS = ("build", "review", "critic", "producer")
SPLIT_DEFAULT = "build=codex,review=claude,critic=claude,producer=claude"
STUCK_ROUNDS = 3        # D-new-no-round-cap: loops have no round cap; needs-human only after 3 rounds in a row with
                        # no improvement (the same gap and no better score)
CLAUDE_DENY = ["Bash(git push:*)", "Bash(gh pr merge:*)", "Bash(gh pr close:*)", "Bash(gh issue close:*)",
               "Bash(gh repo:*)", "Bash(gh api -X DELETE:*)", "Bash(git_gate.py apply:*)"]   # kickoff's own steps
MAX_FAILS = 2           # AGENTS.md section 6: same failure twice -> blocked
AGENT_ENV = ("CLAUDECODE", "JAM_ROLE", "CODEX_SANDBOX", "CODEX_THREAD_ID")
KICK = "KICKOFF"
VERDICT = re.compile(r"^\s*VERDICT:\s*(approve|changes)\b", re.I | re.M)
PUSHED = re.compile(r"^\s*PUSHED:", re.M)
SEAT_LEFT = re.compile(r"\bhuman\b|\bTD\b|\bseat\b|\bowner\b|\beach teammate\b", re.I)
SESSION_TIMEOUT = int(os.environ.get("KICKOFF_SESSION_TIMEOUT", "10800"))
GIT_TIMEOUT = int(os.environ.get("KICKOFF_GIT_TIMEOUT", "1800"))   # a fetch or push that hangs never stalls the run
CI_POLL = int(os.environ.get("KICKOFF_CI_POLL", "60"))       # seconds between checks of a PR whose CI is still running
CI_WAIT = int(os.environ.get("KICKOFF_CI_WAIT", "21600"))    # CI still pending after this many seconds: a failed merge
# gh retries a transient GitHub failure (a 401 the keyring login answers right after, a secondary rate limit, 429,
# 5xx, a timeout, a network error) after each of these waits: 5 tries over about 2 minutes. KICKOFF_GH_RETRY_DELAYS
# ("5,15,30,60") overrides it (the tests use 0s).
GH_RETRY_DELAYS = tuple(float(x) for x in os.environ.get("KICKOFF_GH_RETRY_DELAYS", "5,15,30,60").split(",") if x.strip())
GH_TRANSIENT = re.compile(r"HTTP 401|Bad credentials|HTTP 429|rate limit|HTTP 5\d\d|Bad Gateway|"
                          r"Service Unavailable|Gateway Time-?out|timed out|timeout|connection (?:reset|refused)|"
                          r"could not resolve|no such host|network is unreachable|dial tcp|\bEOF\b|TLS handshake|"
                          r"temporary failure|something went wrong", re.I)
GH_REJECTED = re.compile(r"HTTP 401|Bad credentials|HTTP 429|rate limit", re.I)   # GitHub refused it: nothing was done
GH_CYCLE_FAILS = 5   # scheduler cycles in a row whose gh reads still fail after the retries: then the run ends failed
GREEN = ("pass", "skipping")   # gh pr checks buckets that let a PR merge; fail, cancel and pending do not
LOCK = threading.Lock()            # the console only: say() takes it, so nothing that can block may hold it
JOURNAL_LOCK = threading.Lock()    # one journal write at a time (SQLite); never held while printing
GIT_LOCK = threading.RLock()   # worktree add and push write the shared .git/config


class Refused(Exception):
    pass


def norm_gap(g):
    return re.sub(r"\s+", " ", (g or "").strip().lower().rstrip("."))


def no_progress(history, rounds=STUCK_ROUNDS):
    """True when the newest `rounds` rounds (oldest first; each (gap, score), score = what is left to fix, lower is
    better) came in a row with the same gap and no better score than the round before (D-new-no-round-cap). There is
    no round cap: a loop that keeps improving, or keeps changing its biggest gap, runs on."""
    tail = history[-rounds:]
    if len(tail) < rounds:
        return False
    return all(norm_gap(a[0]) == norm_gap(b[0]) and b[1] >= a[1] for a, b in zip(tail, tail[1:]))


def review_rounds(pr):
    """[(gap, score)] of the reviewer's `VERDICT: changes` comments since the last approve, oldest first: the gap is the
    first reason line after the verdict, the score the number of reason lines (fewer = better)."""
    out = []
    for cm in pr.get("comments") or []:
        b = cm.get("body") or ""
        m = VERDICT.search(b)
        if not m:
            continue
        if m.group(1).lower() != "changes":
            out = []
            continue
        reasons = [ln.strip() for ln in b[m.end():].splitlines() if ln.strip()]
        out.append((reasons[0] if reasons else "", len(reasons)))
    return out


def say(msg):
    with LOCK:
        print(msg, flush=True)


def now():
    v = os.environ.get("KICKOFF_NOW")
    if v:
        return dt.datetime.fromisoformat(v.replace("Z", "+00:00"))
    return dt.datetime.now(dt.timezone.utc)


def stamp():
    return now().astimezone(dt.timezone.utc).strftime("%Y-%m-%dT%H:%MZ")


def git_argv(*args):
    """git's argv. Native Windows: core.longpaths on every call, so a worktree add, checkout or pull can write the
    repo's deep paths (.pipeline\\worktrees\\<branch>\\MegaPipeline\\... is past MAX_PATH 260)."""
    return ["git", "-c", "core.longpaths=true", *args] if native_windows() else ["git", *args]


def git(*args, cwd=ROOT, check=False, env=None):
    try:
        p = subprocess.run(git_argv(*args), cwd=cwd, capture_output=True, text=True, env=env, timeout=GIT_TIMEOUT,
                           stdin=subprocess.DEVNULL)
    except subprocess.TimeoutExpired:
        if check:
            raise RuntimeError(f"git {' '.join(args)}: timed out after {GIT_TIMEOUT} s")
        return 124, ""
    if check and p.returncode != 0:
        # progress lines ("Updating files: 95% ...") would push the real error out of the 300 characters shown
        err = "\n".join(ln for ln in p.stderr.replace("\r", "\n").splitlines()
                        if ln.strip() and not re.match(r"(Updating files|Checking out files|Filtering content):", ln))
        raise RuntimeError(f"git {' '.join(args)}: {err.strip()[-300:]}")
    return p.returncode, p.stdout.strip()


# ---------- GitHub (gh) ----------
class GHError(RuntimeError):
    """A gh call that still failed after its retries (a RuntimeError, so every existing handler still catches it)."""


class GH:
    def __init__(self):
        exe = os.environ.get("KICKOFF_GH") or "gh"
        self.argv = [sys.executable, exe] if exe.endswith(".py") else [exe]
        self.on_retry = say   # one line per retry; Kickoff also writes it to the journal

    def _attempt(self, args, ok, probe=None, retry=True):
        """Run gh with the retries: (CompletedProcess or None on a timeout, last error text). ok(p) = the answer to
        keep. A transient failure (GH_TRANSIENT) is tried again after each GH_RETRY_DELAYS wait; any other failure
        returns at once. probe() is asked before a retry when GitHub may have done the call anyway (5xx, timeout,
        network): a create that went through is never made twice."""
        tries = len(GH_RETRY_DELAYS) + 1 if retry else 1
        what = f"gh {' '.join(args[:3])}"
        for n in range(1, tries + 1):
            try:
                p = subprocess.run(self.argv + args, cwd=ROOT, capture_output=True, text=True, timeout=120,
                                   stdin=subprocess.DEVNULL)
                err = " ".join((p.stderr or p.stdout).split())[-300:]   # one line: stdout, journal, the ask
                if ok(p) or not GH_TRANSIENT.search(err):
                    return p, err
            except subprocess.TimeoutExpired:
                p, err = None, "no answer in 120 s"
            if n == tries:
                return p, err
            if probe and not GH_REJECTED.search(err):
                try:
                    done = probe()
                except (RuntimeError, OSError, ValueError, TypeError, KeyError):
                    done = None
                if done is not None:
                    self.on_retry(f"GH RETRY {what}: GitHub did it after all ({err[:120]}); not sent again")
                    return subprocess.CompletedProcess(args, 0, done, ""), ""
            delay = GH_RETRY_DELAYS[n - 1]
            self.on_retry(f"GH RETRY {what}: try {n} of {tries} failed ({err[:160]}); next try in {delay:g} s")
            time.sleep(delay)

    def run(self, *args, body=None, probe=None, retry=True):
        tmp = None
        args = list(args)
        if body is not None:
            fd, tmp = tempfile.mkstemp(suffix=".md")
            with os.fdopen(fd, "w", encoding="utf-8") as fh:
                fh.write(body)
            args += ["--body-file", tmp]
        try:
            p, err = self._attempt(args, lambda p: p.returncode == 0, probe, retry)
        finally:
            if tmp:
                os.remove(tmp)
        if p is None:
            raise GHError(f"gh {' '.join(args[:3])}: no answer in 120 s")
        if p.returncode != 0:
            raise GHError(f"gh {' '.join(args[:3])}: {err}")
        return p.stdout

    def issues(self):
        return json.loads(self.run("issue", "list", "--state", "all", "--label", "task", "--limit", "500", "--json",
                                   "number,title,body,labels,state,comments") or "[]")

    def all_issues(self):
        return json.loads(self.run("issue", "list", "--state", "all", "--limit", "500", "--json",
                                   "number,title,labels,state,comments") or "[]")

    def prs(self):
        return json.loads(self.run("pr", "list", "--state", "all", "--limit", "500", "--json",
                                   "number,headRefName,state,url,comments,title,mergeCommit") or "[]")

    def create_issue(self, title, body, labels):
        args = ["issue", "create", "--title", title]
        for lb in labels:
            args += ["--label", lb]

        def filed():   # the failed try made the issue anyway (kickoff only creates a title no issue has yet)
            rows = json.loads(self.run("issue", "list", "--state", "all", "--limit", "500", "--json", "number,title",
                                       retry=False) or "[]")
            it = next((i for i in rows if i.get("title") == title), None)
            return f"#{it['number']}" if it else None
        return int(re.search(r"(\d+)\s*$", self.run(*args, body=body, probe=filed).strip()).group(1))

    def edit_body(self, n, body):
        self.run("issue", "edit", str(n), body=body)

    def label(self, n, add=(), remove=()):
        args = ["issue", "edit", str(n)]
        for lb in add:
            args += ["--add-label", lb]
        for lb in remove:
            args += ["--remove-label", lb]
        if len(args) > 3:
            self.run(*args)

    def comment(self, n, body):
        self.run("issue", "comment", str(n), body=body)

    def close(self, n):
        self.run("issue", "close", str(n))

    def create_pr(self, head, base, title, body):
        def opened():   # the failed try opened the PR anyway
            rows = json.loads(self.run("pr", "list", "--state", "open", "--limit", "500", "--json",
                                       "number,headRefName,state", retry=False) or "[]")
            pr = next((p for p in rows if p.get("headRefName") == head), None)
            return f"#{pr['number']}" if pr else None
        out = self.run("pr", "create", "--head", head, "--base", base, "--title", title, body=body, probe=opened)
        return int(re.search(r"(\d+)\s*$", out.strip()).group(1))

    def pr_comment(self, n, body):
        self.run("pr", "comment", str(n), body=body)

    def pr_edit_body(self, n, body):
        self.run("pr", "edit", str(n), body=body)

    def pr_view(self, n, fields):
        return json.loads(self.run("pr", "view", str(n), "--json", fields) or "{}")

    def pr_checks(self, n):
        """[(name, bucket)] of the checks on the PR head: the required ones when branch protection names any, else
        every check reported. None = no check reported at all. gh exits 1 (a failed check) or 8 (pending) with the
        JSON still printed, so the exit code alone is not an error."""
        for required in (True, False):
            args = ["pr", "checks", str(n), "--json", "name,bucket"] + (["--required"] if required else [])
            p, _ = self._attempt(args, lambda p: p.returncode in (0, 8) or bool(p.stdout.strip()))
            if p is None:
                raise GHError(f"gh pr checks {n}: no answer in 120 s")
            try:
                rows = json.loads(p.stdout) if p.stdout.strip() else None
            except ValueError:
                rows = None
            if rows:
                return [(r.get("name") or "?", (r.get("bucket") or "").lower()) for r in rows]
            if p.returncode not in (0, 1, 8) or (p.returncode == 1 and "no " not in (p.stderr or "").lower()):
                raise GHError(f"gh pr checks {n}: {(p.stderr or p.stdout).strip()[-300:]}")
        return None

    def pr_merge(self, n, sha):
        """Squash merge (one commit per card, D-new-port-7; lane_guard reverts it alone), only at the head it checked."""
        self.run("pr", "merge", str(n), "--squash", "--match-head-commit", sha)

    def ensure_labels(self):
        failed = False
        for lb in LABELS:
            try:   # after one failure the rest get one try each: an outage costs one label's retries, not all
                self.run("label", "create", lb, "--force", retry=not failed)
            except RuntimeError:
                failed = True


# ---------- cards ----------
def gates():
    with open(GATES, encoding="utf-8") as fh:
        return json.load(fh)


def native_windows():
    """Native Windows (not WSL); AGENT_OPS_PLATFORM overrides sys.platform for the tests, as in hook.py."""
    return (os.environ.get("AGENT_OPS_PLATFORM") or sys.platform) == "win32"


def packaging_machine():
    """This kickoff may build `Runs on: the Windows packaging machine` cards: native Windows, or
    KICKOFF_PACKAGING_MACHINE=1 (a test seam; the sandboxed sims play that machine)."""
    return native_windows() or os.environ.get("KICKOFF_PACKAGING_MACHINE") == "1"


def mac_machine():
    """This kickoff may build `Runs on: the Mac build machine` cards: macOS (AGENT_OPS_PLATFORM overrides sys.platform
    for the tests, as in native_windows), or KICKOFF_MAC_MACHINE=1 (a test seam, the twin of KICKOFF_PACKAGING_MACHINE:
    the sandboxed sims play that machine on any host)."""
    return ((os.environ.get("AGENT_OPS_PLATFORM") or sys.platform) == "darwin"
            or os.environ.get("KICKOFF_MAC_MACHINE") == "1")


def windows_daily():
    """kickoff runs the daily itself (a QA and Build session per merge) only on the native Windows packaging machine,
    and only while gates.json lets agents run shells there (native_windows_shell: allow)."""
    return native_windows() and gates().get("native_windows_shell", "block") == "allow"


def role_keys():
    return {v: k for k, v in gates()["roles"].items()}


def labels_of(it):
    return {(lb.get("name") if isinstance(lb, dict) else str(lb)) for lb in it.get("labels") or []}


class Card:
    def __init__(self, it):
        self.number = it["number"]
        self.title = it.get("title") or ""
        self.body = it.get("body") or ""
        self.labels = labels_of(it)
        self.state = (it.get("state") or "OPEN").upper()
        self.comments = it.get("comments") or []
        f, _ = check_card.parse(self.body, check_card.template_fields(ROOT), self.title)
        self.fields = f
        self.cid = f.get("ID") or ""
        self.key = check_card.card_key(self.cid) if self.cid else f"#{self.number}"
        rk = role_keys()
        self.owner = (f.get("Owner role") or "").strip()
        self.reviewer = (f.get("Reviewer role") or "").strip()
        self.owner_key = rk.get(self.owner)
        self.reviewer_key = rk.get(self.reviewer)
        self.human = (f.get("Human") or "").strip()
        after = f.get("After") or ""
        self.after = [check_card.card_key(r) for r in check_card.WAIT_REF.findall(after)] \
            if not re.fullmatch(r"\s*(none|–|-)?\s*", after, re.I) else []
        lane = f.get("File lane") or ""
        self.github_only = bool(check_card.NO_FILES_LANE.fullmatch(lane))
        self.lanes = [g for g in check_card.lane_globs(lane) if g not in check_card.ROW_SCOPED]
        self.windows = bool(RUNS_ON_WINDOWS.search(self.body))
        self.mac = bool(RUNS_ON_MAC.search(self.body))
        m = re.match(r"\s*(?:MVP\s*)?#?(\d+)\b", f.get("MVP item") or "")
        self.mvp = int(m.group(1)) if m else None   # the docs/jam-brief.md MVP number (gate_targets reads its [G<n>])

    @property
    def done(self):
        return self.state == "CLOSED" and not (self.labels & NOT_DONE)

    @property
    def open(self):
        return self.state != "CLOSED"

    def branch_prefix(self):
        return f"ue-{self.key}-"

    def problems(self):
        out = check_card.problems(self.body, ROOT, self.title)
        if self.human and SEAT_LEFT.search(self.human):
            out.append(f"Human '{self.human}' is a seat, not a person: fill it from docs/jam-brief.md People")
        return out


def slug(title):
    t = re.sub(r"^\s*\[[^\]]*\]\s*", "", title).lower()
    return "-".join(re.findall(r"[a-z0-9]+", t)[:4]) or "card"


def people(root=ROOT):
    """{seat (lower-case prefix): first person token} from the docs/jam-brief.md People table."""
    try:
        with open(os.path.join(root, "docs", "jam-brief.md"), encoding="utf-8") as fh:
            text = fh.read()
    except OSError:
        return {}
    sec = check_card.section(text, "People")
    out = {}
    for cells in check_card.table_rows(sec):
        if len(cells) >= 2 and cells[1] and "TBD" not in cells[1]:
            name = re.split(r"[ ,(]", cells[1].strip())[0]
            if name:
                out[cells[0].lower()] = name
    return out


def seat_person(seat_words, root=ROOT):
    for k, v in people(root).items():
        if k.startswith(seat_words.lower()):
            return v
    return None


def ask_who(card_human, fallback_seat="producer / time keeper"):
    if card_human and not SEAT_LEFT.search(card_human):
        return card_human.split()[0]
    return seat_person(fallback_seat) or "Producer"


# ---------- the run ----------
class Kickoff:
    journal_lost = 0   # journal and run-record writes that failed this run (the first one is reported)

    def __init__(self, agent, parallel=2, dry=False, watch=None, tester_prompt=None, prejam=False, split=None,
                 max_cards=0, until=None):
        self.agent, self.parallel, self.dry, self.watch = agent, max(1, parallel), dry, watch
        self.split = dict(split or {})   # session kind -> agent CLI (--split); empty: every session on self.agent
        self.prejam = check_card.prejam_cards(ROOT) if prejam else None   # PRE-JAM mode: only these card IDs
        self.tester_prompt = (tester_prompt or "").strip() or None
        self.run_id = None
        self.gh = GH()
        self.gh.on_retry = self.gh_retry
        self.practice = practice.is_practice(ROOT)
        self.jdb = journal.db_path()
        self.seen = set()            # (kind, card, PR state) started this run: never twice in one run
        self.running = {}            # card key -> (kind, lanes)
        self.raised = 0
        self.sessions = 0
        self.last_done = None
        self.base = "main"
        self.remote = git("remote")[1].split()
        self.daily_q = []            # (card, merged PR) waiting for their QA and Build daily session (windows_daily)
        self.daily_lock = threading.Lock()   # one daily at a time: one packaging machine, one Packaged/ folder
        self.fail_count = {}         # (card id, builder|reviewer) -> failed sessions in a row this run
        self.run_failures = []       # failures with no card to ask on (the Producer, a crashed job): the run fails
        self.ci_pending = set()      # job signatures of merges waiting for CI; re-planned every CI_POLL seconds
        self.ci_since = {}           # (PR number, head sha) -> first time its CI was seen pending
        self.max_cards = max(0, max_cards or 0)   # --max-cards: 0 = no bound
        self.done_merged, self.done_blocked = set(), set()   # card keys that reached merged / blocked this run
        self.started = set()         # card keys whose build started this run: in flight, never cut by the bound
        self.until = until or None   # --until G<n>: build only the cards on that gate's path, end on its Mac package
        self.reached = None          # --until: the DAILY line of the Mac package that reached the gate
        self.milestone_hist = []     # --until: (failure signature, count) per failed Mac package, for the stuck rule

    # ----- journal -----
    def journal_call(self, fn, *args, **kw):
        """fn(con, ...) on the journal. A journal error never stops or blocks the run: the first one is reported
        once (outside every lock), later ones are counted, and the call returns None."""
        try:
            with JOURNAL_LOCK:
                con = journal.connect(self.jdb)
                try:
                    return fn(con, *args, **kw)
                finally:
                    con.close()
        except Exception as e:
            with JOURNAL_LOCK:
                self.journal_lost += 1
                first = self.journal_lost == 1
            if first:
                say(f"kickoff: journal not written ({type(e).__name__}: {str(e)[:160]}); the run goes on without "
                    f"it (later journal errors are counted, not shown; journal: {self.jdb})")
            return None

    def j(self, card, kind, **kw):
        if self.dry:
            return None
        return self.journal_call(journal.add, card, kind, branch=kw.pop("branch", ""), commit=kw.pop("commit", ""),
                                 **kw)

    def runlog(self, fn, *args, **kw):
        """Write to the run record tables (never fails the run)."""
        if self.dry or (self.run_id is None and fn is not journal.start_run):
            return None
        return self.journal_call(fn, *args, **kw)

    def model_map(self):
        out = []
        for role in sorted(gates()["roles"]):
            agent = self.agent_for("producer" if role == "producer" else "build")
            try:
                tier, m = self.model(role, agent=agent)
            except Exception:
                continue
            out.append(f"{role}={m or 'default'}" + (f"@{agent}" if self.split else ""))
        return ", ".join(out)

    def agent_label(self):
        """'claude', or 'split build=codex,review=claude,...' for a split run."""
        if not self.split:
            return self.agent
        return "split " + ",".join(f"{k}={self.agent_for(k)}" for k in SPLIT_KINDS)

    FAILED_NOTES = {"builder": ("kickoff: builder failed", "kickoff: builder produced nothing"),
                    "reviewer": ("kickoff: reviewer failed",), "merge": ("kickoff: merge failed",)}
    RESET_NOTES = {"builder": ("kickoff: pushed", "kickoff: builder failures asked"),
                   "reviewer": ("kickoff: verdict", "kickoff: reviewer failures asked"),
                   "merge": ("kickoff: merged", "kickoff: merge failures asked", "kickoff: pushed")}

    def fails(self, card_id, what="builder"):
        """Failed sessions in a row for this card (the journal, so a rerun of kickoff keeps the count; this run's
        own count when the journal cannot be read)."""
        mine = getattr(self, "fail_count", {}).get((card_id, what), 0)
        evs = self.journal_call(journal.events, card_id) or []
        n = 0
        for e in evs:
            note = e["note"] or ""
            if e["kind"] == "step" and note.startswith(self.FAILED_NOTES[what]):
                n += 1
            if e["kind"] == "step" and note.startswith(self.RESET_NOTES[what]):
                n = 0
        return max(n, mine)

    @staticmethod
    def session_reason(code, box):
        """One line on why a session failed: its exit code and the last line it printed."""
        last = ""
        try:
            with open(os.path.join(box, "session.log"), encoding="utf-8", errors="replace") as fh:
                last = next((ln.strip() for ln in reversed(fh.read().splitlines()) if ln.strip()), "")
        except OSError:
            pass
        last = last[:160]
        if code == 124:
            return f"the session timed out after {SESSION_TIMEOUT} s" + (f": {last}" if last else "")
        if code == 127:
            return "the agent CLI could not start" + (f": {last}" if last else "")
        return f"the session exited with code {code}" + (f": {last}" if last else "")

    def session_failed(self, c, cid, what, why, box=None, pr=None):
        """A failed builder or reviewer session: 'retry' (the run starts it again now) until MAX_FAILS in a row
        (AGENTS.md section 6: the same failure twice), then a NEEDS HUMAN ask with the reason. Never idle."""
        key = (cid, what)
        self.fail_count[key] = self.fail_count.get(key, 0) + 1
        self.j(cid, "step", command=what, exit_code=1, note=f"kickoff: {what} failed: {why}"[:300])
        n = self.fails(cid, what)
        if n < MAX_FAILS:
            say(f"RETRY {cid} {what}: {why}; it runs again now ({n} of {MAX_FAILS})")
            return "retry"
        self.fail_count[key] = 0
        log = os.path.relpath(os.path.join(box, "session.log"), ROOT) if box else "none (kickoff error)"
        say(f"BLOCKED {cid}: {MAX_FAILS} {what} {'tries' if what == 'merge' else 'sessions'} failed in a row: {why}")
        if what == "builder":
            self.block(c)
            self.gh.comment(c.number, f"ROLE: Producer | session {stamp()} (tools/kickoff.py)\nBLOCKED: {MAX_FAILS} "
                                      f"builder sessions failed in a row (AGENTS.md section 6). Last: {why}\n"
                                      f"Session log: {log}")
        if what == "reviewer" and pr:
            self.raise_ask(c.number, ask_who(c.human), f"review PR #{pr}: {MAX_FAILS} reviewer sessions failed in a "
                           f"row, last: {why} (read {log})", f"#{pr}")
        elif what == "merge" and pr:
            self.raise_ask(c.number, ask_who(c.human), f"merge PR #{pr}: kickoff could not merge it ({MAX_FAILS} tries "
                           f"in a row), last: {why}. Fix the cause (or merge it with a squash merge), then run "
                           f"{me()} again", f"#{pr}")
        else:
            self.raise_ask(c.number, ask_who(c.human), f"unblock card {cid}: {MAX_FAILS} {what} sessions failed in a "
                           f"row, last: {why} (read {log}, fix the card or the setup, remove `blocked`)")
        self.j(cid, "step", command=what, exit_code=0, note=f"kickoff: {what} failures asked (count starts again)")
        return None

    # ----- GitHub outages -----
    def gh_retry(self, line):
        """One line per gh retry, on stdout and in the journal."""
        say(line)
        self.j(KICK, "step", command="gh retry", exit_code=1, note=f"kickoff: {line}"[:300])

    def gh_cycle_failed(self, e, n):
        """A scheduler cycle whose gh calls still failed after their retries: skip it, wait, plan again. True (the
        run ends failed, with the reason) after GH_CYCLE_FAILS such cycles in a row."""
        why = str(e)[:200]
        self.j(KICK, "step", command="gh", exit_code=1, note=f"kickoff: gh cycle {n} of {GH_CYCLE_FAILS} failed: {why}"[:300])
        if n >= GH_CYCLE_FAILS:
            say(f"ERROR GitHub: {n} cycles in a row failed after their retries; the run stops. Last: {why}")
            self.run_failures.append(f"GitHub did not answer for {n} cycles in a row (last: {why[:160]}); check "
                                     "`gh auth status` and https://www.githubstatus.com")
            return True
        wait = GH_RETRY_DELAYS[-1] if GH_RETRY_DELAYS else 0
        say(f"SKIP cycle: GitHub failed after the retries ({why}); planning again in {wait:g} s "
            f"({n} of {GH_CYCLE_FAILS})")
        time.sleep(wait)
        return False

    def gh_job_failed(self, sig, kind, key, err):
        """A job stopped by a gh call that still failed after its retries (its own failure path could not reach
        GitHub either): True = run it again next cycle, up to MAX_FAILS times; then it is a run failure."""
        n = self.__dict__.setdefault("gh_job_fails", {}).get(sig, 0) + 1
        self.gh_job_fails[sig] = n
        if n > MAX_FAILS:
            return False
        say(f"RETRY {kind} UE-{key}: GitHub failed under it ({str(err)[:160]}); it runs again next cycle "
            f"({n} of {MAX_FAILS})")
        self.j(f"UE-{key}", "step", command="gh", exit_code=1, note=f"kickoff: gh failed under {kind}: {err}"[:300])
        return True

    # ----- asks -----
    def raise_ask(self, number, who, what, link=None, role="Producer"):
        link = link or f"#{number}"
        try:
            it = next((i for i in self.gh.all_issues() if i["number"] == number), {})
        except RuntimeError:
            it = {}
        if "needs-human" in labels_of(it) and any(what in (c.get("body") or "") for c in it.get("comments") or []):
            return False
        line = f"NEEDS HUMAN: {who} {what} {link} {stamp()}"
        self.gh.label(number, add=["needs-human"])
        self.gh.comment(number, f"ROLE: {role} | session {stamp()} (tools/kickoff.py)\n{line}")
        self.raised += 1
        say(f"NEEDS HUMAN #{number}: {who} {what} {link}")
        self.j(f"#{number}", "step", command="needs-human", exit_code=0, note=f"kickoff: asked {who}: {what}")
        return True

    # ----- base and worktrees -----
    def refresh_base(self):
        if "origin" in self.remote:
            with GIT_LOCK:
                git("fetch", "-q", "origin")
            rc, _ = git("rev-parse", "--verify", "-q", "origin/main")
            return "origin/main" if rc == 0 else "main"
        return "main"

    def worktree(self, branch):
        path = os.path.join(WORKTREES, branch)
        if os.path.isdir(path):
            return path
        os.makedirs(WORKTREES, exist_ok=True)
        with GIT_LOCK:
            rc, _ = git("rev-parse", "--verify", "-q", f"refs/heads/{branch}")
            if rc == 0:
                git("worktree", "add", path, branch, check=True)
            elif "origin" in self.remote and git("rev-parse", "--verify", "-q", f"origin/{branch}")[0] == 0:
                git("worktree", "add", "--no-track", "-b", branch, path, f"origin/{branch}", check=True)
            else:
                git("worktree", "add", "--no-track", "-b", branch, path, self.refresh_base(), check=True)
        return path

    def git_dir(self):
        rc, out = git("rev-parse", "--git-common-dir")
        return out if os.path.isabs(out) else os.path.join(ROOT, out)

    # ----- agent sessions -----
    def agent_for(self, kind):
        """The agent CLI for a session kind (build, review, critic, producer): --split, else the one agent."""
        return self.split.get(kind, self.agent)

    def model(self, role, review=False, critic=False, agent=None):
        """(tier, model) for a session: a blind critic runs at the Critic tier, a reviewer at the Hard calls tier
        (pipeline/agent-ops/model-tiers.md); Claude takes the Model column, Codex the GPT column."""
        agent = agent or self.agent
        if critic:
            tier, cmodel = start_session.model_for(role, tier="Critic")
        else:
            tier, cmodel = start_session.model_for("dev-lead" if review else role)
            if review:
                tier = "Hard calls"
        if agent == "claude":
            return tier, cmodel
        with open(start_session.TIERS, encoding="utf-8") as fh:
            for cells in start_session.table_rows(fh.read()):
                if len(cells) >= 4 and cells[0] == tier:
                    m = re.search(r"`([\w.:-]+)`", cells[3])
                    return tier, (m.group(1) if m else None)
        return tier, None

    def agent_argv(self, prompt, model, tier, cwd, outbox, role, agent=None):
        import mcp_config
        agent = agent or self.agent
        base = shlex.split(os.environ.get("KICKOFF_AGENT_CMD") or agent)
        base[0] = shutil.which(base[0]) or base[0]   # Windows: npm installs codex.cmd / claude.cmd
        mcp = mcp_config.session_args(agent, role, os.path.join(ROOT, ".pipeline", "mcp"))
        high = tier in HIGH_EFFORT
        if agent == "claude":
            # acceptEdits cannot run git commit / python3 / gh in -p mode (a card's builder must commit and run its
            # checks), so sessions run unprompted; only kickoff pushes, merges or closes (Josh, 12 Nov)
            argv = base + ["-p", prompt, "--permission-mode", "bypassPermissions", "--disallowedTools"] + CLAUDE_DENY
            argv += ["--model", model] if model else []
            argv += ["--effort", "high"] if high else []
            return argv + mcp
        argv = base + ["exec", "-s", "workspace-write", "-C", cwd, "--add-dir", self.git_dir(), "--add-dir", outbox,
                       "-o", os.path.join(outbox, "last-message.md"), "-c", "shell_environment_policy.inherit=all"]
        argv += ["-m", model] if model else []
        argv += ["-c", 'model_reasoning_effort="high"'] if high else []
        return argv + mcp + [prompt]

    def session(self, card_id, role, cwd, outbox, prompt, extra_env, review=False, critic=False):
        kind = "critic" if critic else "review" if review else "producer" if role == "producer" else "build"
        agent = self.agent_for(kind)
        tier, model = self.model(role, review, critic, agent)
        env = keys.scrub({k: v for k, v in os.environ.items() if k not in ("JAM_HUMAN",) + AGENT_ENV})
        env.update({"JAM_ROLE": role, "JAM_CARD": card_id, "JAM_OUTBOX": outbox, "JAM_KICKOFF": "1",
                    "JAM_MODEL": model or "codex-default", "JAM_PRACTICE": "1" if self.practice else "0"})
        env.setdefault("JAM_HOST", journal.machine_label())
        env.update(extra_env)
        argv = self.agent_argv(prompt, model, tier, cwd, outbox, role, agent)
        self.sessions += 1
        self.runlog(journal.add_run_prompt, self.run_id, card_id, role, model or "default", prompt)
        self.j(card_id, "start", role=role, note=f"kickoff: {'critic' if critic else 'review' if review else 'session'} {agent} "
                                                 f"tier={tier} model={model or 'default'}")
        log = os.path.join(outbox, "session.log")
        started = time.time()
        try:
            with open(log, "w", encoding="utf-8") as fh:
                p = subprocess.run(argv, cwd=cwd, env=env, stdout=fh, stderr=subprocess.STDOUT,
                                   timeout=SESSION_TIMEOUT, stdin=subprocess.DEVNULL)
            code = p.returncode
        except subprocess.TimeoutExpired:
            code = 124
        except OSError as e:
            code = 127
            with open(log, "a", encoding="utf-8") as fh:
                fh.write(str(e))
        with open(log, encoding="utf-8", errors="replace") as fh:
            tail = journal.tail(fh.read())
        self.j(card_id, "step", role=role, command=f"{agent} session ({role})", exit_code=code,
               output_tail=tail, note=f"kickoff: session ended in {time.time() - started:.0f} s")
        self.runlog(journal.add_run_outcome, self.run_id, "session", exit_code=code, card=card_id,
                    note=f"{role} {'review' if review else 'session'}")
        if agent == "claude":
            try:   # the spend log is a record: it never fails or stalls the session
                subprocess.run([sys.executable, os.path.join(HERE, "spend_log.py"), "log", "--from-agent-log", "--since",
                                dt.datetime.fromtimestamp(started, dt.timezone.utc).strftime("%Y-%m-%dT%H:%M:%S"),
                                "--role", role, "--card", card_id, "--model", model or "unknown"],
                               cwd=ROOT, capture_output=True, timeout=300)
            except (subprocess.TimeoutExpired, OSError) as e:
                say(f"kickoff: spend log not written for {card_id} ({type(e).__name__})")
        return code

    def outbox(self, name):
        os.makedirs(OUTBOXES, exist_ok=True)
        return tempfile.mkdtemp(prefix=f"{name}-{now().strftime('%Y%m%dT%H%M%S')}-", dir=OUTBOXES)

    def prompt(self, role, card_id, issue, body, task, extra=""):
        mode = ("PRACTICE repo (.pipeline-practice): D39 is lifted, build game files today; submission, upload and G4 "
                "stay blocked." if self.practice else
                "PRE-JAM on the team repo: only the pre-jam cards run. Official Rules 7(h) allows tools, agent "
                "configurations, MCP settings, prompts and scripts before the start: no Source/, Content/, Config/ or "
                "game .uproject, and the workbench sample stays synthetic (no umbrella or owl)." if self.prejam is not None
                else "Team repo: the Official Rules apply as written (D39 before the jam start).")
        return "\n".join([
            f"ROLE: {role}. Non-interactive kickoff session (tools/kickoff.py): nobody reads this chat or answers a "
            f"question. Follow AGENTS.md, including its 'Kickoff sessions' section; your role card is "
            f"pipeline/roles/{role}.md.",
            f"Card {card_id} ({issue}). Task: {task}",
            mode,
            "Outbox: $JAM_OUTBOX (write the files AGENTS.md names there). Commit with `UE-<id>: <what>` and the "
            "trailer `Role: <role>`; never push, kickoff pushes and opens the PR. You own all the card's work: a "
            "change to a gate path goes in $JAM_OUTBOX/gate.patch (a git patch, paths inside the card's File lane only; "
            "kickoff applies it through the tool checks, tools/git_gate.py apply --auto), never a person's to write. At a human checkpoint write the "
            "NEEDS HUMAN line to $JAM_OUTBOX/needs-human.txt and stop that step. API asset steps "
            "(tools/assetgen.py image|sfx|music) queue for kickoff: finish what you can, the next session has them.",
            extra,
            repo_map.prompt_line(ROOT),   # the team's own top-level folders, which docs/repo-map.md does not describe
            ("Tester prompt for this run (recorded in the run record; follow it where AGENTS.md allows): "
             + self.tester_prompt) if self.tester_prompt else "",
            (f"GDD for this run (kickoff --gdd, {journal.gdd_revision(ROOT).split(' (')[0]}): read "
             f"{os.environ[journal.GDD_ENV]} in place of the snapshot docs/gdd/CURRENT names. Never edit it; repo "
             "checks (manifest_check, check_card) still read docs/gdd/CURRENT.") if os.environ.get(journal.GDD_ENV)
            else "",
            "Card text (a starting copy; re-read the issue when you can):",
            body or "(no text)",
        ])

    # ----- Producer -----
    def producer_pass(self, problems_text="", note=""):
        issues = self.gh.issues()
        box = self.outbox("PRODUCER")
        with open(os.path.join(box, "issues.json"), "w", encoding="utf-8") as fh:
            json.dump([{"number": i["number"], "title": i["title"], "state": i.get("state"),
                        "labels": sorted(labels_of(i))} for i in issues], fh, indent=1)
        task = ("File or refresh the cards: every row of pipeline/day0-cards.md whose After cards have all merged "
                "(issues.json in the outbox lists what exists and what is closed), and the plan's next cards, as "
                "issue-form JSON in $JAM_OUTBOX/cards/<UE-id>.json. Replace every seat in Owner role / human with "
                "that seat's person from the docs/jam-brief.md People table. Each card passes "
                "`python3 tools/check_card.py` with 0 problems."
                + (" PRE-JAM mode: file only the pre-jam cards (" + ", ".join(sorted(self.prejam, key=check_card.natural))
                   + "); the rest wait for the jam start." if self.prejam is not None else "")
                + (f" This run targets {self.until} (--until): file the MVP cards for every MVP item docs/jam-brief.md "
                   f"tags [{self.until}] or earlier first, as soon as card 0.3 has merged, each with its MVP item number "
                   "and every card it needs in After." if self.until else ""))
        extra = ("Fix these check_card problems on the cards you filed:\n" + problems_text) if problems_text else ""
        if note:
            extra = "\n\n".join(x for x in (note, extra) if x)
        for attempt in range(1, MAX_FAILS + 1):   # a failed Producer session runs again, then fails the run
            rc = self.session("KICKOFF-PRODUCER", "producer", ROOT, box,
                              self.prompt("producer", "KICKOFF-PRODUCER", "the card board", "", task, extra), {})
            filed = self.publish_cards(box, issues)
            say(f"PRODUCER session exit={rc}: {filed} card(s) filed or refreshed")
            if rc == 0:
                return filed
            why = self.session_reason(rc, box)
            if attempt < MAX_FAILS:
                say(f"RETRY KICKOFF-PRODUCER: {why}; it runs again now ({attempt} of {MAX_FAILS})")
                box = self.outbox("PRODUCER")
                with open(os.path.join(box, "issues.json"), "w", encoding="utf-8") as fh:
                    json.dump([{"number": i["number"], "title": i["title"], "state": i.get("state"),
                                "labels": sorted(labels_of(i))} for i in issues], fh, indent=1)
        self.run_failures.append(f"the Producer session failed {MAX_FAILS} times in a row: {why} "
                                 f"(read {os.path.relpath(os.path.join(box, 'session.log'), ROOT)})")
        return filed

    def publish_cards(self, box, issues):
        d = os.path.join(box, "cards")
        if not os.path.isdir(d):
            return 0
        by_id = {}
        for i in issues:
            m = re.match(r"\s*\[([^\]]+)\]", i.get("title") or "")
            if m:
                by_id[m.group(1).strip().upper()] = i
        n = 0
        for f in sorted(os.listdir(d)):
            if not f.endswith(".json"):
                continue
            with open(os.path.join(d, f), encoding="utf-8") as fh:
                c = json.load(fh)
            m = re.match(r"\s*\[([^\]]+)\]", c.get("title") or "")
            if not m:
                continue
            old = by_id.get(m.group(1).strip().upper())
            if old is None and self.prejam is not None and check_card.card_key(m.group(1)) not in self.prejam:
                continue   # PRE-JAM mode: a card that makes game files waits for the jam start (D39)
            if old is None:
                num = self.gh.create_issue(c["title"], c["body"], ["task", "todo"])
                self.j(f"#{num}", "step", command="gh issue create", exit_code=0, note=f"kickoff: filed {c['title']}")
                n += 1
            elif (old.get("state") or "").upper() != "CLOSED" and (old.get("body") or "") != c["body"]:
                self.gh.edit_body(old["number"], c["body"])
                self.j(f"#{old['number']}", "step", command="gh issue edit", exit_code=0,
                       note=f"kickoff: refreshed {c['title']}")
                n += 1
        return n

    def card_problems(self, cards):
        out = []
        open_cards = [c for c in cards if c.open]
        for c in open_cards:
            out += [f"#{c.number} {c.cid}: {p}" for p in c.problems()]
        return out   # lanes: the scheduler never runs two cards whose lanes overlap

    def producer_until_clean(self):
        filed = self.producer_pass()
        probs = self.card_problems(self.cards())
        cycle = 1
        hist = [("; ".join(sorted(probs)), len(probs))]
        while probs and not no_progress(hist):   # no round cap (D-new-no-round-cap)
            say(f"CHECK_CARD {len(probs)} problem(s); Producer fix cycle {cycle + 1}")
            filed += self.producer_pass("\n".join(probs[:40]))
            probs = self.card_problems(self.cards())
            hist.append(("; ".join(sorted(probs)), len(probs)))
            cycle += 1
        if probs:   # stuck: the same problems 3 cycles in a row, no fewer of them
            for c in self.cards():
                mine = [p for p in probs if p.startswith(f"#{c.number} ")]
                if mine and c.open:
                    self.raise_ask(c.number, ask_who(None), f"fix the card: {mine[0].split(': ', 1)[1][:120]}")
        say(f"CHECK_CARD {len(probs)} problem(s) after {cycle} Producer cycle(s)")
        return filed

    def cards(self):
        return [Card(i) for i in self.gh.issues()]

    # ----- one card -----
    def card_pr(self, c, prs):
        mine = [p for p in prs if (p.get("headRefName") or "").startswith(c.branch_prefix())]
        return sorted(mine, key=lambda p: p["number"])[-1] if mine else None

    @staticmethod
    def verdict(pr):
        state, changes = None, 0
        for cm in pr.get("comments") or []:
            b = cm.get("body") or ""
            m = VERDICT.search(b)
            if m:
                state = m.group(1).lower()
                changes += state == "changes"
            elif PUSHED.search(b):
                state = None
        return state, changes

    def builder(self, c, fix=""):
        cid = f"UE-{c.key}"
        refused = self.__dict__.setdefault("gate_refused", {}).pop(c.key, "")
        if refused:   # the tool route refused the last gate.patch: the retry gets the reasons
            fix = "\n".join(x for x in (fix, refused) if x)
        try:
            prs = self.gh.prs()
            pr = self.card_pr(c, prs)
            branch = pr["headRefName"] if pr else f"ue-{c.key}-{slug(c.title)}"
            wt = self.worktree(branch)
            self.gh.label(c.number, add=["doing"], remove=["todo"])
            base = self.refresh_base()
            before = git("rev-parse", "HEAD", cwd=wt)[1]
            patch = None
            started = time.time()
            queued, cycle = [], 0
            while True:   # no round cap: runs while the session queues assets; stops when it queues none
                box = self.outbox(cid)
                with open(os.path.join(box, "card.json"), "w", encoding="utf-8") as fh:
                    json.dump({"number": c.number, "title": c.title, "body": c.body}, fh)
                task = ("Build the card in this worktree" + (" (assets you queued are now in place; continue)"
                                                            if cycle else "") + ". Write pr.md for the PR.")
                extra = ("Review feedback to fix:\n" + fix) if fix else ""
                code = self.session(cid, c.owner_key, wt, box, self.prompt(c.owner_key, cid, f"#{c.number}", c.body, task,
                                                                    extra),
                             {"JAM_ISSUE": f"#{c.number}", "JAM_BRANCH": branch})
                asked = self.post_outbox(c, box)
                patch = self.keep_gate_patch(c, box, branch, wt) or patch
                req = self.read(box, "asset-requests.jsonl") or ""
                if not self.fulfil(c, box, wt):
                    break
                queued.append((req, 0))
                cycle += 1
                if no_progress(queued):
                    self.raise_ask(c.number, ask_who(c.human), f"card {cid}: the session queued the same asset steps "
                                   f"{STUCK_ROUNDS} times in a row (no progress); read its session log")
                    asked = True
                    break
            gate_line = None
            if patch and not code:
                gate_line, why = self.apply_gate_patch(c, cid, wt)
                if not gate_line:
                    self.gate_refused[c.key] = (f"kickoff refused your gate.patch (tools/git_gate.py apply --auto): "
                                                f"{why}. Keep every gate path inside the card's File lane, never "
                                                "change a guardrail enforcer, and never loosen a guardrail file.")
                    return self.session_failed(c, cid, "builder", f"gate patch refused: {why}"[:300], box)
            if code and not asked:   # a crash, a timeout or a non-zero exit: its commits are not a finished card
                return self.session_failed(c, cid, "builder", self.session_reason(code, box), box)
            if not asked and not self.art_gate_loop(c, cid, wt, base, box, branch, started):
                return
            if not asked and not self.art_loop_card(c, cid, wt, box, branch):
                return
            if not asked and not self.art_gate_loop(c, cid, wt, base, box, branch, started, with_loop=True):
                return   # the card does not go to review without every art_loop and art_ref_check PASS line
            if not asked:
                done_audio = self.audio_loop_card(c, cid, wt, box, branch)
                if done_audio is not True:
                    return done_audio   # stuck (asked) or a failed session (retried)
            ahead = git("rev-list", "--count", f"{base}..HEAD", cwd=wt)[1]
            moved = git("rev-parse", "HEAD", cwd=wt)[1] != before
            if int(ahead or 0) and (moved or not pr):
                penv = dict(keys.scrub(os.environ))
                if gate_line:   # the tool route's gate commit goes through the hooks' human route as kickoff
                    penv["JAM_HUMAN"] = git_gate.AUTO_BY
                with GIT_LOCK:
                    rc, out = git("push", "-u", "origin", branch, cwd=wt, env=penv)
                if rc != 0:
                    self.raise_ask(c.number, ask_who(c.human), f"the push of {branch} was refused: "
                                   f"{out[-100:] or 'see the hook message'}")
                    return
                self.j(cid, "step", command=f"git push origin {branch}", exit_code=0, note="kickoff: pushed")
                self.fail_count.pop((cid, "builder"), None)
                body = self.read(box, "pr.md") or (pr or {}).get("body") or (
                    f"## Task\nPart of #{c.number}. Card ID: {cid}  Owner role: {c.owner}  Reviewer role: {c.reviewer}\n")
                if gate_line:
                    body = self.with_gate_commit(body, gate_line, wt)
                if pr is None or pr.get("state") != "OPEN":
                    n = self.gh.create_pr(branch, "main", f"{cid}: {re.sub(r'^\s*\[[^]]*\]\s*', '', c.title)}", body)
                    self.j(cid, "step", command="gh pr create", exit_code=0, note=f"kickoff: opened PR #{n}")
                    say(f"PR #{n} opened for {cid} ({branch})")
                else:
                    if self.read(box, "pr.md") or gate_line:   # the new evidence: check_pr reads the body at the new head
                        self.gh.pr_edit_body(pr["number"], body)
                    self.gh.pr_comment(pr["number"], f"ROLE: {c.owner} | session {stamp()} (tools/kickoff.py)\n"
                                                     f"PUSHED: fixes for the review, {git('rev-parse', 'HEAD', cwd=wt)[1][:12]}")
                self.gh.label(c.number, add=["review"], remove=["doing"])
            elif c.github_only and self.read(box, "comment.md"):
                self.j(cid, "step", command="card done (no files)", exit_code=0, note="kickoff: pushed (no files)")
                if not (c.reviewer_key and self.review_issue(c, wt)):
                    self.raise_ask(c.number, ask_who(c.human), f"check and close card {cid} (GitHub-only lane, no PR)")
            elif not asked:
                return self.session_failed(c, cid, "builder", "the session produced no commit and no ask "
                                           f"({self.session_reason(code, box)})", box)
        except Exception as e:  # one card's failure never stops the others; it is retried, then asked
            say(f"ERROR {cid}: {e}")
            return self.session_failed(c, cid, "builder", f"kickoff error {type(e).__name__}: {str(e)[:200]}",
                                       locals().get("box"))

    def keep_gate_patch(self, c, box, branch, wt):
        """The session's gate-path changes ($JAM_OUTBOX/gate.patch): kept under .pipeline/gate-patches/UE-<id>/ with
        the card's lane, for apply_gate_patch (tools/git_gate.py apply --auto). Returns the patch's paths, or None."""
        text = self.read(box, "gate.patch")
        if not text:
            return None
        paths = sorted({a or b for a, b in PATCH_PATH.findall(text)})
        cid = f"UE-{c.key}"
        d = os.path.join(GATE_PATCHES, cid)
        os.makedirs(d, exist_ok=True)
        with open(os.path.join(d, "gate.patch"), "w", encoding="utf-8") as fh:
            fh.write(text + "\n")
        pr = self.read(box, "pr.md")
        if pr:
            with open(os.path.join(d, "pr.md"), "w", encoding="utf-8") as fh:
                fh.write(pr + "\n")
        with open(os.path.join(d, "meta.json"), "w", encoding="utf-8") as fh:
            json.dump({"card": cid, "issue": c.number, "branch": branch, "worktree": wt, "paths": paths,
                       "title": c.title, "lanes": c.lanes}, fh, indent=1)
        self.j(cid, "step", command="gate.patch", exit_code=0, note=f"kickoff: gate patch kept ({len(paths)} path(s))")
        say(f"GATE PATCH {cid}: {', '.join(paths[:4]) or 'no paths'} -> .pipeline/gate-patches/{cid}/ (kickoff applies "
            "it through the tool checks)")
        return paths or ["(see the patch)"]

    def apply_gate_patch(self, c, cid, wt):
        """No person applies a gate patch: kickoff runs tools/git_gate.py apply --auto on the kept patch (every path in
        the card's lane, no guardrail enforcer, no guardrail loosened), which commits it in the card's worktree as
        `GATE EDIT: by=kickoff`. CI's check_pr rule gate and the merge gate re-run the same checks.
        Returns (GATE EDIT line, None) or (None, why it was refused)."""
        env = {k: v for k, v in keys.scrub(os.environ).items() if k not in AGENT_ENV + ("JAM_KICKOFF", "JAM_HUMAN")}
        rc, lines = git_gate.apply_patch(cid, git_gate.AUTO_BY, no_pr=True, root=ROOT, env=env, auto=True)
        text = "\n".join(x for x in lines if x)
        self.j(cid, "step", command=f"tools/git_gate.py apply {cid} --auto", exit_code=rc,
               output_tail=journal.tail(text), note="kickoff: gate patch, tool route")
        line = next((m.group(0) for m in re.finditer(r"GATE EDIT: by=\S+ \S+", text)), None)
        if rc != 0 or not line:
            why = next((x.split(": ", 1)[-1] for x in lines if "REFUSED" in x or "does not apply" in x
                        or "failed" in x), text.splitlines()[-1] if text else f"exit {rc}")
            say(f"GATE PATCH {cid} refused: {why[:200]}")
            return None, why[:400]
        os.replace(os.path.join(GATE_PATCHES, cid, "gate.patch"), os.path.join(GATE_PATCHES, cid, "applied.patch"))
        say(f"GATE PATCH {cid} applied by kickoff (tool checks passed): {line}")
        return line, None

    @staticmethod
    def with_gate_commit(body, gate_line, wt):
        """The PR body after kickoff's gate commit: the GATE EDIT line under Evidence, and the header moved from the
        session's commit to the new head only when the gate commit is the one commit on top of it (it adds the patch's
        paths and nothing else), with a line saying so."""
        head = git("rev-parse", "HEAD", cwd=wt)[1]
        prev = git("rev-parse", "HEAD~1", cwd=wt)[1]
        m = check_pr.HEADER.search(body or "")
        if m and prev.lower().startswith(m.group("commit").lower()):
            body = body[:m.start("commit")] + head[:12] + body[m.end("commit"):]
            gate_line += (f"\nkickoff: gate commit {head[:12]} on top of the session's {prev[:12]} applies gate.patch "
                          "only (tools/git_gate.py apply --auto)")
        return git_gate.with_gate_line(body, gate_line)

    def review_issue(self, c, wt):
        """A GitHub-only card (no files, no PR): its reviewer role checks the result on GitHub in a fresh session;
        approve closes the card. True = closed."""
        cid = f"UE-{c.key}"
        box = self.outbox(cid + "-review")
        with open(os.path.join(box, "card.json"), "w", encoding="utf-8") as fh:
            json.dump({"number": c.number, "title": c.title, "body": c.body}, fh)
        task = (f"Review card {cid} (#{c.number}) as {c.reviewer}, a fresh session that did not do it. Its lane is "
                "GitHub only, so there is no PR: check each Done-when line against GitHub (`gh issue view "
                f"{c.number} --comments` and what the lines name). Write review.md: first line `ROLE: <your role> | "
                "session <UTC time>`, then `VERDICT: approve` or `VERDICT: changes` and the reasons.")
        self.session(cid, c.reviewer_key, wt, box, self.prompt(c.reviewer_key, cid, f"#{c.number}", c.body, task),
                     {"JAM_ISSUE": f"#{c.number}", "JAM_REVIEW": "1"}, review=True)
        rv = self.read(box, "review.md")
        if not (rv and VERDICT.search(rv)):
            return False
        self.gh.comment(c.number, rv)
        if VERDICT.search(rv).group(1).lower() != "approve":
            return False
        self.close_card(c, "its reviewer approved the GitHub-only result")
        return True

    def merge_gate(self, c, n):
        """(state, why, head sha) for PR #n: 'ok' when every gate passes, 'pending' while CI runs, else 'fail'.
        Gates: the reviewer agent's last verdict (after the last push) is approve; check_pr on the head has 0 problems
        (its artship rule is the art ship gate); every required CI check on the head is green."""
        view = self.gh.pr_view(n, "state,headRefName,headRefOid,body,comments,title")
        sha = view.get("headRefOid") or ""
        if (view.get("state") or "").upper() != "OPEN":
            return "fail", f"PR #{n} is {view.get('state')}, not open", sha
        if self.verdict(view)[0] != "approve":
            return "fail", "the reviewer's last verdict is not `VERDICT: approve` (or a push came after it)", sha
        wt = self.worktree(view["headRefName"])
        with GIT_LOCK:
            git("fetch", "-q", "origin", view["headRefName"], cwd=wt)
        git("merge", "-q", "--ff-only", "FETCH_HEAD", cwd=wt)
        here = git("rev-parse", "HEAD", cwd=wt)[1]
        if not sha or here != sha:
            return "fail", f"the PR head is {sha[:12] or 'unknown'} but its worktree is at {here[:12]}", sha
        base = self.refresh_base()
        mbase = git("merge-base", base, "HEAD", cwd=wt)[1]
        changed = git("diff", "--name-only", f"{mbase}..HEAD", cwd=wt)[1]
        d = tempfile.mkdtemp(prefix="merge-gate-")
        try:
            files = {"body.md": view.get("body") or "", "changed.txt": changed + "\n",
                     "card.json": json.dumps({"title": c.title, "body": c.body})}
            for name, text in files.items():
                with open(os.path.join(d, name), "w", encoding="utf-8") as fh:
                    fh.write(text)
            try:   # the PR's own tree: its check_pr reads the files at the head (agents cannot change tools/)
                p = subprocess.run([sys.executable, os.path.join(wt, "tools", "check_pr.py"), os.path.join(d, "body.md"),
                                    "--changed", os.path.join(d, "changed.txt"), "--head", sha, "--base", mbase,
                                    "--card", os.path.join(d, "card.json")], cwd=wt, capture_output=True, text=True,
                                   timeout=1800, env=dict(keys.scrub(os.environ)))
                rc, lines = p.returncode, [ln for ln in p.stdout.splitlines() if ln.strip()]
            except subprocess.TimeoutExpired:
                rc, lines = 124, ["check_pr timed out after 1800 s"]
        finally:
            shutil.rmtree(d, ignore_errors=True)
        self.j(f"UE-{c.key}", "step", command=f"tools/check_pr.py (merge gate, PR #{n})", exit_code=rc,
               output_tail=journal.tail("\n".join(lines)), note="kickoff: merge gate check_pr")
        if rc != 0:
            probs = [ln[2:] for ln in lines if ln.startswith("- ")]
            return "fail", (f"check_pr: {len(probs)} problem(s): " + "; ".join(probs[:3]))[:400] if probs else \
                (lines[-1] if lines else f"check_pr exit {rc}"), sha
        if git_gate.gate_hits(changed.split(), gates().get("gate_paths") or []):
            # a gate change: this checkout's own rule gate judges it too, so a patch cannot weaken the checker
            probs = check_pr.gate_problems(check_pr.sections(view.get("body") or ""), changed.split(), ROOT,
                                           {"title": c.title, "body": c.body}, sha, mbase)
            self.j(f"UE-{c.key}", "step", command=f"check_pr rule gate from the base checkout (PR #{n})",
                   exit_code=1 if probs else 0, output_tail=journal.tail("\n".join(probs)),
                   note="kickoff: merge gate, base rule gate")
            if probs:
                return "fail", ("base check_pr rule gate: " + "; ".join(probs[:2]))[:400], sha
        checks = self.gh.pr_checks(n)
        if checks is None:
            return "fail", "no CI check reported on the PR head (CI did not run)", sha
        red = [f"{name} ({b})" for name, b in checks if b not in GREEN + ("pending",)]
        if red:
            return "fail", "CI check(s) not green: " + ", ".join(red[:6]), sha
        waiting = [name for name, b in checks if b == "pending"]
        if waiting:
            since = self.ci_since.setdefault((n, sha), time.time())
            if time.time() - since > CI_WAIT:
                return "fail", f"CI still pending after {CI_WAIT // 60} min: " + ", ".join(waiting[:6]), sha
            return "pending", "CI still running: " + ", ".join(waiting[:6]), sha
        return "ok", f"{len(checks)} CI check(s) green, reviewer approved, check_pr 0 problems", sha

    def merger(self, c, pr):
        """kickoff merges an approved card PR itself once every gate passes (agents never push or merge). A failed
        merge is tried again (MAX_FAILS), then a NEEDS HUMAN ask with the gh error. 'pending' = CI still running."""
        cid, n = f"UE-{c.key}", pr["number"]
        try:
            state, why, sha = self.merge_gate(c, n)
            if state == "pending":
                say(f"MERGE {cid} PR #{n}: waiting, {why}")
                return "pending"
            if state == "fail":
                return self.session_failed(c, cid, "merge", why, pr=n)
            with GIT_LOCK:
                self.gh.pr_merge(n, sha)
        except Exception as e:
            return self.session_failed(c, cid, "merge", f"{type(e).__name__}: {str(e)[:300]}", pr=n)
        self.fail_count.pop((cid, "merge"), None)
        self.j(cid, "step", command=f"gh pr merge {n} --squash --match-head-commit {sha[:12]}", exit_code=0,
               note=f"kickoff: merged PR #{n} ({why})")
        say(f"MERGED {cid} PR #{n} at {sha[:12]}: {why}")
        try:
            merged = self.gh.pr_view(n, "number,state,mergeCommit,headRefName")
        except (RuntimeError, ValueError):
            merged = dict(pr, state="MERGED")
        self.close_card(c, f"PR #{n} is merged (kickoff: {why})")
        self.repo_settings(c)
        if windows_daily():
            self.daily_q.append((c, merged))
        return None

    # Repo settings a card's merge turns on. kickoff runs them itself with the token the person set up (an agent
    # session never runs gh variable or gh api: gates.json ask_commands); fixed commands, never a session's text.
    PROTECTION = {"required_status_checks": {"strict": False, "contexts": ["checks"]}, "enforce_admins": False,
                  "required_pull_request_reviews": None, "restrictions": None, "allow_force_pushes": False,
                  "allow_deletions": False}

    def repo_settings(self, c):
        """Card 0.16 merged: PIPELINE_CLOCK=on, TRACKER_ISSUE=<the tracker issue>, one clock run. Card 0.17 merged:
        branch protection on main (required check `checks`, the pipeline-checks.yml job; no force push, no delete;
        no required review, because the reviewer is a fresh agent session and kickoff merges on its approve) and
        Actions may open pull requests (main-red.yml's revert PRs). Each is read back on the card. A failure is an
        ask with the gh error; the run goes on."""
        if c.key not in ("0.16", "0.17"):
            return
        steps = []
        if c.key == "0.16":
            tracker = next((i["number"] for i in self.gh.all_issues() if "tracker" in labels_of(i)), None)
            if tracker is None:
                self.raise_ask(c.number, ask_who(c.human), "set TRACKER_ISSUE: kickoff found no issue labelled "
                               "tracker (card 0.1)")
                return
            steps = [("variable", "set", "PIPELINE_CLOCK", "--body", "on"),
                     ("variable", "set", "TRACKER_ISSUE", "--body", str(tracker)),
                     ("workflow", "run", "clock"), ("variable", "list")]
        fd, prot = tempfile.mkstemp(suffix=".json")
        with os.fdopen(fd, "w", encoding="utf-8") as fh:
            json.dump(self.PROTECTION, fh)
        if c.key == "0.17":
            steps = [("api", "-X", "PUT", "repos/{owner}/{repo}/branches/main/protection", "--input", prot),
                     ("api", "-X", "PUT", "repos/{owner}/{repo}/actions/permissions/workflow", "-f",
                      "default_workflow_permissions=write", "-F", "can_approve_pull_request_reviews=true"),
                     ("api", "repos/{owner}/{repo}/branches/main/protection")]
        out = []
        try:
            for st in steps:
                try:
                    got = self.gh.run(*st)
                except RuntimeError as e:
                    self.j(f"UE-{c.key}", "step", command="gh " + " ".join(st[:4]), exit_code=1, note=str(e)[:300])
                    self.raise_ask(c.number, ask_who(c.human), f"set the repo setting `gh {' '.join(st[:4])}`: "
                                   f"kickoff could not ({str(e)[:160]})")
                    return
                self.j(f"UE-{c.key}", "step", command="gh " + " ".join(st[:4]), exit_code=0,
                       note="kickoff: repo setting")
                out.append(f"$ gh {' '.join(x if x != prot else 'PROTECTION.json' for x in st)}\n"
                           f"{(got or '').strip()[-600:]}")
        finally:
            os.remove(prot)
        self.gh.comment(c.number, f"ROLE: Producer | session {stamp()} (tools/kickoff.py)\nRepo settings set by "
                                  "kickoff after the merge (read-back below):\n```\n" + "\n".join(out) + "\n```")
        say(f"SETTINGS UE-{c.key}: {len(steps)} repo setting step(s) done")

    def ensure_jam_start(self, root=ROOT):
        """Card 0.3 starts: kickoff tags `jam-start` on main itself (the pre-jam record the declaration and the Sponsor
        read, docs/pre-jam-declaration.md), only when no such tag exists, only on or after the Official Rules start,
        and never in a practice repo (D39 is lifted there; there is no pre-jam record). Returns the sha, or None."""
        import submission_check
        if getattr(self, "practice", False) or now() < submission_check.JAM_START:
            return None
        origin = "origin" in git("remote", cwd=root)[1].split()
        if origin:
            with GIT_LOCK:
                rc, out = git("ls-remote", "--tags", "origin", "refs/tags/jam-start", cwd=root)
            if rc == 0 and out.strip():
                return None   # already tagged (by a person or an earlier run): never moved
            with GIT_LOCK:
                git("fetch", "-q", "origin", cwd=root)
        rc, sha = git("rev-parse", "-q", "--verify", "refs/tags/jam-start^{commit}", cwd=root)
        if rc != 0:
            ref = "origin/main" if origin and git("rev-parse", "-q", "--verify", "origin/main", cwd=root)[0] == 0 \
                else "main"
            sha = git("rev-parse", ref, cwd=root, check=True)[1]
            git("tag", "jam-start", sha, cwd=root, check=True)
        elif not origin:
            return None
        if origin:
            with GIT_LOCK:
                git("push", "-q", "origin", "refs/tags/jam-start", cwd=root, check=True,
                    env=dict(keys.scrub(os.environ)))
        self.j("UE-0.3", "step", command=f"git tag jam-start {sha[:12]} && git push origin jam-start", exit_code=0,
               note=f"kickoff: tagged jam-start at {sha[:12]} (card 0.3 started; pre-jam record)")
        say(f"JAM-START tagged on main at {sha[:12]} (card 0.3 starts; docs/pre-jam-declaration.md)")
        return sha

    def block(self, c):
        self.gh.label(c.number, add=["blocked"], remove=["doing"])
        self.__dict__.setdefault("done_blocked", set()).add(c.key)

    def bounded(self):
        """--max-cards N reached: N cards merged (or closed) or blocked in this run; no new build session starts."""
        return bool(self.max_cards) and len(self.done_merged | self.done_blocked) >= self.max_cards

    def close_card(self, c, why):
        self.gh.comment(c.number, f"ROLE: Producer | session {stamp()} (tools/kickoff.py)\nDONE: {why}; closed by kickoff")
        self.gh.label(c.number, remove=[lb for lb in ("doing", "review", "todo", "needs-human") if lb in c.labels])
        self.gh.close(c.number)
        self.__dict__.setdefault("done_merged", set()).add(c.key)
        self.__dict__.setdefault("done_blocked", set()).discard(c.key)
        self.j(f"UE-{c.key}", "step", command="gh issue close", exit_code=0, note=f"kickoff: closed ({why})")
        say(f"DONE UE-{c.key} #{c.number}: {why}")

    def art_problems(self, wt, base, box, since, card=None, with_loop=False):
        """The art gate's failures for this worktree (empty = pass, or nothing was built)."""
        import check_pr
        import ue_run
        changed = [p for p in git("diff", "--name-only", f"{base}..HEAD", cwd=wt)[1].split("\n") if p.strip()]
        body = self.read(box, "pr.md") or ""
        smoked = bool(check_pr.SMOKE_LINE.search(body))
        probs = []
        if card:   # rule artref (and artloop once the loop ran): the card's own references, enforced in code
            probs += [p for p in check_pr.artref_problems({"Task": f"Card ID: UE-{card}", "Evidence": body}, changed, wt)
                      if with_loop or "art_loop" not in p]
        if not smoked and not check_pr.needs_package({}, changed):
            return probs
        if smoked and check_pr.smoke_hook_exists(wt, changed):
            probs += check_pr.art_evidence_problems(body, wt, changed)
        shots = [p for p in glob_shots(wt) if os.path.getmtime(p) >= since - 1]
        if not shots and smoked and not ue_run.art_bootstrap(wt):
            probs.append("no smoke screenshot (Saved/Logs/pipeline/*-shot.png) from this session: run the smoke "
                         "script, which takes it")
        for shot in shots:
            no_player = os.path.basename(shot).startswith(tuple(f"smoke-{m}" for m in ("L_Title", "L_StyleFrame")))
            _, fails = ue_run.shot_checks(shot, wt, scene=not no_player)
            if fails and not ue_run.art_bootstrap(wt):
                probs += [f"{os.path.basename(shot)}: {f}" for f in fails]
        return probs

    def art_gate_loop(self, c, cid, wt, base, box, branch, started, with_loop=False):
        """Run the art gate; on a failure the builder fixes it and the gate runs again. No round cap
        (D-new-no-round-cap): False = stuck, the same failures with no fewer of them 3 rounds in a row."""
        hist = []
        while True:
            probs = self.art_problems(wt, base, box, started, c.key, with_loop)
            if not probs:
                return True
            sig = "; ".join(sorted(re.sub(r"[-\w]*-shot\.png: ", "", p)[:120] for p in probs))
            self.j(cid, "step", command="art gate", exit_code=1, note=f"kickoff: art gate failed: {sig}"[:300])
            hist.append((sig, len(probs)))
            if no_progress(hist):
                self.block(c)
                self.gh.comment(c.number, f"ROLE: Producer | session {stamp()} (tools/kickoff.py)\nBLOCKED: the art "
                                          f"gate failed the same way {STUCK_ROUNDS} rounds in a row with no fewer "
                                          "failures (D-new-no-round-cap):\n" + "\n".join(probs[:8]))
                say(f"BLOCKED {cid}: the art gate made no progress in {STUCK_ROUNDS} rounds")
                self.raise_ask(c.number, ask_who(c.human), f"unblock card {cid}: the art gate (art_check, screen_check, "
                               f"art_judge) failed the same way {STUCK_ROUNDS} rounds in a row (read the card comment, "
                               "fix the art brief or the references, remove `blocked`)")
                return False
            say(f"ART GATE {cid}: {len(probs)} failure(s), first: {probs[0][:160]}; the agent fixes it and smokes again")
            started = time.time()
            fix = ("The automatic art gate failed (a failed build; no human approves art). Fix the visual in this "
                   "card's lane: regenerate it with tools/assetgen.py image and pick with tools/art_judge.py element "
                   "--pick, or rescale or reposition it (visual-only scale and offset), or turn the debug draw off; then "
                   "package, run the smoke script again and paste its whole output in pr.md. Failures:\n"
                   + "\n".join(probs))
            self.session(cid, c.owner_key, wt, box, self.prompt(c.owner_key, cid, f"#{c.number}", c.body,
                                                                "Fix the art gate failures below.", fix),
                         {"JAM_ISSUE": f"#{c.number}", "JAM_BRANCH": branch})
            self.post_outbox(c, box)

    def art_loop_card(self, c, cid, wt, box, branch):
        """Builder and blind critic for each piece of an art card until it reaches the bar. False = stopped (stuck)."""
        import art_loop
        import art_ref_check
        refs, rh = art_loop.refs_and_hash(wt)
        pieces = art_loop.pieces(refs, c.key)
        if not pieces:
            return True
        def commit():
            return git("rev-parse", "HEAD", cwd=wt)[1][:12]
        for piece in pieces:
            def listed(piece=piece):
                try:
                    with open(os.path.join(box, "art-pieces.json"), encoding="utf-8") as fh:
                        rel = json.load(fh).get(piece)
                except (OSError, ValueError):
                    rel = None
                return os.path.join(wt, rel) if rel else None

            def build(gap, piece=piece):
                if gap or not listed():
                    why = (f"The blind critic's biggest gap for piece {piece}: {gap}" if gap else
                           f"List piece {piece} in $JAM_OUTBOX/art-pieces.json")
                    self.session(cid, c.owner_key, wt, box, self.prompt(
                        c.owner_key, cid, f"#{c.number}", c.body, f"Art loop, piece {piece}: revise this piece only "
                        "(change the Blender scene: pipeline/art/blender/ recipe, model, materials, lines, light; "
                        "render again with tools/assetgen.py blender), commit, and keep "
                        "$JAM_OUTBOX/art-pieces.json pointing at its file.", why),
                        {"JAM_ISSUE": f"#{c.number}", "JAM_BRANCH": branch})
                    self.post_outbox(c, box)
                return listed() or os.path.join(wt, "missing.png")

            def checks(f, piece=piece):
                if not os.path.isfile(f):
                    return False, 0.0, ["no file"]
                try:
                    rc, lines = art_ref_check.run(c.key, f if piece == "scene" else None,
                                                  None if piece == "scene" else piece, [f], root=wt, commit=commit())
                except (OSError, ValueError, KeyError) as e:
                    return False, 0.0, [str(e)]
                m = re.search(r"score=([\d.]+)", lines[-1]) if lines else None
                return rc == 0, float(m.group(1)) if m else 0.0, lines

            n = [0]

            def make_pair(f, piece=piece):
                n[0] += 1
                out = []
                for kind in ("ref", "bar"):   # the piece's reference, then the top-tier quality bar
                    d = os.path.join(box, "critic", f"{piece}-{n[0]}-{kind}")
                    key = art_loop.blind(refs, c.key, piece, f, d, root=wt, quality=kind == "bar")
                    with open(key, encoding="utf-8") as fh:
                        out.append((d, json.load(fh)))
                return out

            def critic(pair):
                cbox = self.outbox(f"{cid}-critic-{os.path.basename(pair)}")
                with open(os.path.join(pair, "prompt.md"), encoding="utf-8") as fh:
                    prompt = fh.read()
                if art_loop.critic_prompt_problems(prompt, c.body):
                    return ""
                self.session(f"{cid}-critic", "art-director", pair, cbox, prompt + "\nAlso write your answer lines "
                             "(one per lettered folder) to $JAM_OUTBOX/verdict.md.", {"JAM_REVIEW": "1", "JAM_ISSUE": ""},
                             review=True, critic=True)
                # one fresh session per folder; its outbox name is the session id the pass record keeps
                return (self.read(cbox, "verdict.md") or self.read(cbox, "session.log") or "", os.path.basename(cbox))

            def log(rec, piece=piece):
                art_loop.log_round(wt, c.key, piece, rec, rh, commit())
                say(f"ART LOOP {cid} {piece} round {rec['round']}: critic={rec['verdict']} checks="
                    f"{'pass' if rec['checks'] else 'fail'} score={rec['score']} gap={rec['gap'][:80]}")

            state, hist = art_loop.run_piece(build, critic, checks, make_pair, log)
            if state == "stuck":
                self.block(c)
                gaps = "\n".join(f"- round {r['round']}: {r['verdict']}, score {r['score']}: {r['gap']}" for r in hist[-6:])
                self.gh.comment(c.number, f"ROLE: Producer | session {stamp()} (tools/kickoff.py)\nBLOCKED: art loop piece "
                                          f"{piece} made no progress in {art_loop.STUCK_ROUNDS} rounds.\nFirst: "
                                          f"{os.path.relpath(hist[0]['file'], wt)}\nLatest: "
                                          f"{os.path.relpath(hist[-1]['file'], wt)}\nCritic gaps:\n{gaps}")
                self.raise_ask(c.number, ask_who(c.human), f"art loop stuck on {cid} piece {piece}: no improvement in "
                               f"{art_loop.STUCK_ROUNDS} rounds (first and latest image and the gaps are on the card)")
                return False
            last = hist[-1]
            f = last.get("file") or ""
            rel = os.path.relpath(f, wt).replace(os.sep, "/") if f else ""
            rp = art_loop.record_path(f) if f else ""
            if rp and os.path.isfile(rp):   # kickoff's own commit: agent sessions may never write or commit a record
                renv = {k: v for k, v in keys.scrub(os.environ).items() if k not in AGENT_ENV}
                git("add", os.path.relpath(rp, wt), cwd=wt)
                git("commit", "-q", "-m", f"{cid}: art-loop pass record for {piece} ({rel})\n\nRole: art loop "
                    "(tools/kickoff.py)", cwd=wt, env=renv)
                self.j(cid, "step", command=f"git commit {os.path.relpath(rp, wt)}", exit_code=0,
                       note=f"kickoff: art-loop pass record for {piece}")
            line = art_loop.pass_line(c.key, piece, last["verdict"], len(hist), rh, commit(),
                                      rel if rp and os.path.isfile(rp) else None, last.get("sha"), last.get("pairs"))
            with open(os.path.join(box, "pr.md"), "a", encoding="utf-8") as fh:
                fh.write("\n" + line + "\n")
            say(line)
        return True

    def audio_loop_card(self, c, cid, wt, box, branch):
        """The audio builder-critic loop (pipeline/audio/style-target.md section 5) for a card whose builder started
        `tools/audio_loop.py start` (Saved/AudioLoop/<card>/state.json in its worktree). Per piece: `round`, a fresh
        blind critic session on the packet (never the builder's), `verdict`; a fail sends the critic's gap back to the
        builder, whose queued API steps kickoff fulfils. No round cap; the loop's stuck rule (3 flat rounds) blocks
        the card and asks the audio owner. A piece whose takes are all tracked placeholders (the audio API failed) is
        not judged. Then `close`, whose lines go into pr.md. True = done (or no audio loop); otherwise the builder's
        return value."""
        import audio_loop as al
        sroot = os.path.join(wt, "Saved", "AudioLoop")
        found = []
        for d in sorted(os.listdir(sroot)) if os.path.isdir(sroot) else []:
            try:
                with open(os.path.join(sroot, d, "state.json"), encoding="utf-8") as fh:
                    st = json.load(fh)
            except (OSError, ValueError):
                continue
            if check_card.card_key(str(st.get("card") or "")) == c.key:
                found.append((d, st))
        if not found:
            return True
        loop_card = found[0][1]["card"]
        sdir = os.path.join(sroot, found[0][0])
        audio = os.path.join(wt, "Audio", "Source")

        def run(*args):
            p = subprocess.run([sys.executable, os.path.join(HERE, "audio_loop.py"), args[0], "--card", loop_card,
                                "--root", wt, *args[1:]], cwd=wt, capture_output=True, text=True)
            return p.returncode, (p.stdout or "") + (p.stderr or "")

        def state():
            with open(os.path.join(sdir, "state.json"), encoding="utf-8") as fh:
                return json.load(fh)

        for sid in list(found[0][1].get("pieces") or {}):
            errors = 0
            while True:
                if al.placeholder_piece(wt, audio, sid):
                    say(f"AUDIO LOOP {cid} {sid}: tracked placeholder takes (the audio API could not make them); "
                        "not judged")
                    break
                pc = state()["pieces"][sid]
                last = pc["rounds"][-1] if pc["rounds"] else None
                if last and last.get("verdict") == "pass" and last.get("style_pass"):
                    break
                if pc.get("stuck"):
                    self.block(c)
                    self.raise_ask(c.number, ask_who(c.human, "audio owner"), f"audio loop stuck on {cid} piece {sid}: "
                                   "no improvement in 3 rounds; listen and answer with `tools/audio_loop.py resume` "
                                   "(pipeline/audio/style-target.md section 5)")
                    return False
                if not last or last.get("verdict"):
                    rc, out = run("round", "--piece", sid)
                    if rc:
                        return self.session_failed(c, cid, "builder", f"audio_loop round {sid}: {out.strip()[-200:]}",
                                                   box)
                    n = len(pc["rounds"]) + 1
                else:
                    n = last["n"]
                packet = os.path.join(sdir, sid, f"round-{n}", "packet")
                with open(os.path.join(packet, "brief.md"), encoding="utf-8") as fh:
                    brief = fh.read()
                cbox = self.outbox(f"{cid}-audio-critic-{sid}-{n}")
                self.session(f"{cid}-critic", "audio", packet, cbox, brief + "\nWrite your answer as the JSON reply the "
                             "brief asks for to $JAM_OUTBOX/reply.json.", {"JAM_REVIEW": "1", "JAM_ISSUE": ""},
                             review=True, critic=True)
                reply = os.path.join(cbox, "reply.json")
                if not os.path.isfile(reply):
                    errors += 1
                    if errors >= MAX_FAILS:
                        return self.session_failed(c, cid, "builder", f"the audio critic for {sid} wrote no "
                                                   "reply.json twice", cbox)
                    continue
                rc, out = run("verdict", "--piece", sid, "--critic", os.path.basename(cbox), "--reply", reply)
                say(f"AUDIO LOOP {cid} {sid} round {n}: " + (out.strip().splitlines() or ["no output"])[0][:160])
                self.j(cid, "step", command=f"audio_loop verdict {sid}", exit_code=rc, output_tail=journal.tail(out),
                       note=f"kickoff: audio loop round {n}")
                if rc == 0 or rc == al.STUCK:
                    continue   # done, or stuck (the next pass of the loop asks)
                if rc != 1:   # a refused reply (rows missing, a pass with a false row): a new critic judges the round
                    errors += 1
                    if errors >= MAX_FAILS:
                        return self.session_failed(c, cid, "builder", f"audio_loop verdict {sid}: "
                                                   f"{out.strip()[-200:]}", cbox)
                    continue
                errors = 0
                gap = re.search(r"builder revises: (.+)", out)
                self.session(cid, c.owner_key, wt, box, self.prompt(
                    c.owner_key, cid, f"#{c.number}", c.body, f"Audio loop, piece {sid}: revise this piece only "
                    f"(`python3 tools/assetgen.py sfx --sound {sid} --prompt \"<the gap as a change>\" --out ...` for "
                    "each take, or music), commit. Never run audio_loop.py round or verdict: kickoff does.",
                    f"The blind critic's biggest gap for {sid}: {gap.group(1) if gap else out.strip()[-200:]}"),
                    {"JAM_ISSUE": f"#{c.number}", "JAM_BRANCH": branch})
                self.post_outbox(c, box)
                self.fulfil(c, box, wt)
        rc, out = run("close")
        with open(os.path.join(box, "pr.md"), "a", encoding="utf-8") as fh:
            fh.write("\n```\n$ python3 tools/audio_loop.py close --card " + loop_card + "\n" + out.strip() + "\n```\n")
        say(f"AUDIO LOOP {cid}: " + (out.strip().splitlines() or ["no output"])[-1])
        if rc:
            return self.session_failed(c, cid, "builder", "audio_loop close: " + out.strip()[-200:], box)
        return True

    def reviewer(self, c, pr):
        cid = f"UE-{c.key}"
        try:
            wt = self.worktree(pr["headRefName"])
            git("pull", "-q", "--ff-only", cwd=wt)
            box = self.outbox(cid + "-review")
            with open(os.path.join(box, "card.json"), "w", encoding="utf-8") as fh:
                json.dump({"number": c.number, "title": c.title, "body": c.body, "pr": pr["number"]}, fh)
            task = (f"Review PR #{pr['number']} (branch {pr['headRefName']}, this worktree) as {c.reviewer}, a fresh "
                    "session that did not write it. Write review.md: first line `ROLE: <your role> | session "
                    "<UTC time>`, then `VERDICT: approve` or `VERDICT: changes` and the reasons.")
            code = self.session(cid, c.reviewer_key, wt, box, self.prompt(c.reviewer_key, cid, f"#{c.number}", c.body,
                                                                          task),
                                {"JAM_ISSUE": f"#{c.number}", "JAM_PR": f"#{pr['number']}", "JAM_REVIEW": "1"},
                                review=True)
            self.post_outbox(c, box)
            rv = self.read(box, "review.md")
            if rv and VERDICT.search(rv):
                self.gh.pr_comment(pr["number"], rv)
                v = VERDICT.search(rv).group(1).lower()
                self.j(cid, "step", command=f"review PR #{pr['number']}", exit_code=0, note=f"kickoff: verdict {v}")
                self.fail_count.pop((cid, "reviewer"), None)
                say(f"REVIEW {cid} PR #{pr['number']}: {v}")
                return None
            return self.session_failed(c, cid, "reviewer", f"the reviewer wrote no VERDICT for PR #{pr['number']} "
                                       f"({self.session_reason(code, box)})", box, pr["number"])
        except Exception as e:
            say(f"ERROR {cid} review: {e}")
            return self.session_failed(c, cid, "reviewer", f"kickoff error {type(e).__name__}: {str(e)[:200]}",
                                       locals().get("box"), pr["number"])

    @staticmethod
    def read(box, name):
        p = os.path.join(box, name)
        if os.path.isfile(p):
            with open(p, encoding="utf-8") as fh:
                return fh.read().strip()
        return None

    def post_outbox(self, c, box):
        asked = False
        cm = self.read(box, "comment.md")
        if cm:
            self.gh.comment(c.number, cm)
        for ln in (self.read(box, "needs-human.txt") or "").splitlines():
            m = check_card.NEEDS_HUMAN.search(ln.strip())
            if m:
                self.raise_ask(c.number, m.group("who"), m.group("what"), m.group("link"),
                               role=c.owner or "Producer")
                asked = True
        return asked

    def fulfil(self, c, box, wt):
        """Run the session's queued asset API steps with the keys; commit the files. True = run the card again."""
        if not os.path.isfile(os.path.join(box, "asset-requests.jsonl")):
            return False
        env = dict(os.environ, JAM_ROLE=c.owner_key, JAM_OUTBOX=box)
        try:
            p = subprocess.run([sys.executable, os.path.join(HERE, "assetgen.py"), "fulfil", "--outbox", box], cwd=wt,
                               capture_output=True, text=True, env=env, timeout=SESSION_TIMEOUT)
        except subprocess.TimeoutExpired:
            p = subprocess.CompletedProcess([], 124, "", f"assetgen fulfil timed out after {SESSION_TIMEOUT} s")
        say(f"ASSETS UE-{c.key}: " + (p.stdout.strip().splitlines() or ["none"])[-1])
        self.j(f"UE-{c.key}", "step", command="tools/assetgen.py fulfil", exit_code=p.returncode,
               output_tail=journal.tail(p.stdout + p.stderr), note="kickoff: asset API steps")
        git("add", "-A", cwd=wt)
        genv = dict(keys.scrub(os.environ), JAM_ROLE=c.owner_key, JAM_KICKOFF="1")
        git("commit", "-q", "-m", f"UE-{c.key}: generated assets (tools/assetgen.py fulfil)\n\nRole: {c.owner}",
            cwd=wt, env=genv)
        return True

    # ----- scheduler -----
    def plan(self):
        """(jobs to start, waiting lines). A job is (kind, card, pr)."""
        cards = self.cards()
        prs = self.gh.prs()
        by_key = {c.key: c for c in cards}
        by_num = {f"#{c.number}": c for c in cards}
        held = [g for k, (kind, lanes) in self.running.items() for g in lanes]
        for c in cards:
            pr = self.card_pr(c, prs)
            if c.open and pr and pr.get("state") == "OPEN" and c.key not in self.running:
                held += c.lanes
        jobs, waiting = [], []
        targets = self.gate_targets(cards)[0] if getattr(self, "until", None) else None
        for c in sorted(cards, key=lambda c: check_card.natural(c.key)):
            if not c.open or c.key in self.running:
                continue
            merged = self.card_pr(c, prs)
            if merged and merged.get("state") == "MERGED":   # merged (by kickoff, or by a person after an ask)
                self.close_card(c, f"PR #{merged['number']} is merged")
                if windows_daily():
                    self.daily_q.append((c, merged))
                continue
            if c.labels & {"needs-human", "blocked"}:
                waiting.append(f"#{c.number} {c.cid}: {'needs-human' if 'needs-human' in c.labels else 'blocked'}")
                continue
            deps = [by_key.get(a) or by_num.get(a) for a in c.after]
            if any(d is None or not d.done for d in deps):
                continue
            pr = self.card_pr(c, prs)
            if self.prejam is not None and c.key not in self.prejam:
                waiting.append(f"#{c.number} {c.cid}: waits for the jam start (PRE-JAM mode)")
                continue
            if c.owner_key is None:   # check_card rejects a person as Owner; an old card can still say it
                self.raise_ask(c.number, ask_who(c.human), f"fix card UE-{c.key}: Owner role {c.owner or 'Human'} is "
                               "not an agent role (agents own every card; a person's part is a HUMAN <kind>: line)")
                continue
            if c.windows and not packaging_machine() and not (pr and pr.get("state") == "OPEN" and
                                                           self.verdict(pr)[0] in ("approve", None)):
                waiting.append(f"#{c.number} {c.cid}: runs on the Windows packaging machine (kickoff there picks it)")
                continue
            if c.mac and not mac_machine() and not (pr and pr.get("state") == "OPEN" and
                                                    self.verdict(pr)[0] in ("approve", None)):
                waiting.append(f"#{c.number} {c.cid}: runs on the Mac build machine (kickoff there picks it)")
                continue
            if pr and pr.get("state") == "OPEN":
                v, changes = self.verdict(pr)
                if v == "approve":   # kickoff merges it once CI, check_pr and the art ship gate pass (merger)
                    jobs.append(("merge", c, pr, ""))
                elif v == "changes" and no_progress(review_rounds(pr)):
                    self.raise_ask(c.number, ask_who(c.human), f"decide PR #{pr['number']}: {STUCK_ROUNDS} review "
                                   "rounds in a row named the same gap with no fewer findings (D-new-no-round-cap)",
                                   f"#{pr['number']}")
                elif v == "changes":
                    fb = next((cm["body"] for cm in reversed(pr.get("comments") or []) if VERDICT.search(
                        cm.get("body") or "")), "")
                    jobs.append(("fix", c, pr, fb))
                elif c.reviewer_key is None:   # check_card rejects a person as reviewer; an old card can say it
                    self.raise_ask(c.number, ask_who(c.human), f"fix card UE-{c.key}: Reviewer role "
                                   f"{c.reviewer or '(empty)'} is not an agent role, so PR #{pr['number']} has no "
                                   "reviewer session", f"#{pr['number']}")
                else:
                    jobs.append(("review", c, pr, ""))
                continue
            if targets is not None and c.key not in targets:
                waiting.append(f"#{c.number} {c.cid}: not on the {self.until} path (--until {self.until})")
                continue
            probs = c.problems()
            if probs:
                waiting.append(f"#{c.number} {c.cid}: check_card {len(probs)} problem(s)")
                continue
            if any(check_card.globs_overlap(a, b) for a in c.lanes for b in held):
                waiting.append(f"#{c.number} {c.cid}: lane busy")
                continue
            held += c.lanes
            jobs.append(("build", c, None, ""))
        jobs += [("daily", c, pr, "") for c, pr in self.daily_q]
        return jobs, waiting, cards

    def gate_targets(self, cards):
        """--until G<n>: (card keys on the gate's path, MVP numbers due at it that have no card yet). The path is the
        gate's Day-0 cards (pipeline/day0-cards.md `**G1 cards:**`, check_card.gate_cards), every filed card whose MVP
        item docs/jam-brief.md tags at or before the gate (check_card.gate_mvp), and every card those list in After,
        directly or not (a filed card's After field; a Day-0 row not filed yet: its table After)."""
        due = set(check_card.gate_mvp(ROOT).get(self.until, []))
        table = {cid: after for cid, _, after in check_card.day0_table(ROOT)}
        live = [c for c in cards if not (c.labels & NOT_DONE)]
        by_key = {c.key: c for c in live}
        by_num = {f"#{c.number}": c for c in live}
        mvp = [c for c in live if c.mvp in due]
        todo = list(check_card.gate_cards(ROOT, self.until)) + [c.key for c in mvp]
        out = set()
        while todo:
            k = todo.pop()
            c = by_key.get(k) or by_num.get(k)
            k = c.key if c else k
            if k in out:
                continue
            out.add(k)
            todo += c.after if c else table.get(k, [])
        return out, sorted(due - {c.mvp for c in mvp})

    def milestone(self, cards):
        """--until: once every card on the gate's path is merged, the gate's Mac package: tools/ue/daily.sh on main
        (build, tests, package, smoke) in its own worktree, run by kickoff itself (no agent session). A DAILY line
        with package and smoke PASS reaches the gate. A failure goes to the Producer as a bug to file on the path; the
        same failure 3 times in a row with no fewer failing steps fails the run. Returns None (not there yet),
        'again' (a bug was filed: plan again) or 'stop'."""
        import ue_run
        targets, missing = self.gate_targets(cards)
        by_key = {c.key: c for c in cards if not (c.labels & NOT_DONE)}
        left = [k for k in targets if k not in by_key or not by_key[k].done]
        if missing or left:
            return None
        if not mac_machine():
            say(f"UNTIL {self.until}: every card on the path is merged; the {self.until} Mac package runs on the Mac "
                f"build machine (run {me()} --until {self.until} there)")
            return "stop"
        base = self.refresh_base()
        sha = git("rev-parse", base)[1]
        wt = os.path.join(WORKTREES, f"{self.until.lower()}-package")
        with GIT_LOCK:
            if os.path.isdir(wt):
                git("checkout", "-q", "--detach", sha, cwd=wt, check=True)
            else:
                os.makedirs(WORKTREES, exist_ok=True)
                git("worktree", "add", "-q", "--detach", wt, sha, check=True)
        rec = os.path.join(wt, ue_run.RECORD)
        before = len((self.read(os.path.dirname(rec), os.path.basename(rec)) or "").splitlines())
        cmd = shlex.split(os.environ.get("KICKOFF_PACKAGE_CMD") or "bash tools/ue/daily.sh")
        say(f"{self.until} PACKAGE: {' '.join(cmd)} on main {sha[:12]} (Mac Development package, launched by the smoke)")
        env = {k: v for k, v in keys.scrub(os.environ).items() if k not in AGENT_ENV}
        try:
            p = subprocess.run(cmd, cwd=wt, capture_output=True, text=True, env=env, timeout=SESSION_TIMEOUT)
            code, out = p.returncode, (p.stdout or "") + (p.stderr or "")
        except (OSError, subprocess.TimeoutExpired) as e:
            code, out = 124, f"{type(e).__name__}: {e}"
        new = [ln for ln in (self.read(os.path.dirname(rec), os.path.basename(rec)) or "").splitlines()[before:]
               if ln.startswith("DAILY ")]
        if new:   # this checkout's daily record, so `ue_run.py merge-check` here counts it
            mine = os.path.join(ROOT, ue_run.RECORD)
            os.makedirs(os.path.dirname(mine), exist_ok=True)
            with open(mine, "a", encoding="utf-8") as fh:
                fh.write("".join(ln + "\n" for ln in new))
        line = new[-1] if new else None
        ok = bool(line and ue_run.good_daily(line)) and code == 0
        self.j(KICK, "step", command=" ".join(cmd), exit_code=code, output_tail=journal.tail(out),
               note=f"kickoff: {self.until} Mac package on {sha[:12]}: {line or 'no DAILY line'}"[:300])
        if ok:
            self.reached = line
            say(f"{self.until} REACHED: {line}")
            return "stop"
        fails = sorted(set(re.findall(r"\b([a-z-]+)=FAIL", line or ""))) or ["no DAILY line"]
        self.milestone_hist.append((", ".join(fails), len(fails)))
        tail = "\n".join(out.strip().splitlines()[-20:])
        say(f"{self.until} PACKAGE FAILED on {sha[:12]}: {', '.join(fails)}")
        if no_progress(self.milestone_hist):
            self.run_failures.append(f"the {self.until} Mac package failed {STUCK_ROUNDS} times in a row on "
                                     f"{', '.join(fails)} (tools/ue/daily.sh; read the journal step)")
            return "stop"
        self.producer_pass(note=f"The {self.until} Mac package failed: `{' '.join(cmd)}` on main {sha[:12]} printed "
                                f"{line or 'no DAILY line'} (exit {code}). Last lines:\n{tail}\nFile one bug card for "
                                f"it whose MVP item is the [{self.until}] MVP item the failing step belongs to, so "
                                f"kickoff --until {self.until} builds it.")
        return "again"

    def daily_run(self, c, pr):
        """D-new-merge-daily on the Windows packaging machine: a QA and Build session runs tools\\ue\\daily.ps1 on the
        merge commit in its own worktree. The DAILY line goes on the merged card and into this checkout's record,
        so `ue_run.py merge-check` here counts it."""
        import ue_run
        cid = f"UE-{c.key}"
        with self.daily_lock:
            base = self.refresh_base()
            sha = ((pr or {}).get("mergeCommit") or {}).get("oid") or git("rev-parse", base)[1]
            wt = os.path.join(WORKTREES, "qa-daily")
            with GIT_LOCK:
                if os.path.isdir(wt):
                    git("checkout", "-q", "--detach", sha, cwd=wt, check=True)
                else:
                    os.makedirs(WORKTREES, exist_ok=True)
                    git("worktree", "add", "-q", "--detach", wt, sha, check=True)
            rec = os.path.join(wt, ue_run.RECORD)
            before = self.read(os.path.dirname(rec), os.path.basename(rec)) or ""
            box = self.outbox(f"DAILY-{cid}")
            task = (f"Card {cid} merged as {sha[:12]}. This worktree is detached at that commit. Run the daily "
                    "integration build here: `tools\\ue\\daily.ps1`, nothing else first. Never edit, commit or push. "
                    "Write $JAM_OUTBOX/comment.md: first line `ROLE: QA and Build | session <UTC time>`, then the DAILY "
                    "line exactly as printed; on a FAIL also the failing step and the last 20 lines of its log, and "
                    "that it is a bug for the Producer to file.")
            self.session(cid, "qa-build", wt, box, self.prompt("qa-build", cid, f"#{c.number}", "", task),
                         {"JAM_ISSUE": f"#{c.number}", "JAM_DAILY_COMMIT": sha})
            after = self.read(os.path.dirname(rec), os.path.basename(rec)) or ""
            new = [ln for ln in after.splitlines()[len(before.splitlines()):] if ln.startswith("DAILY ")]
            if new:
                mine = os.path.join(ROOT, ue_run.RECORD)
                os.makedirs(os.path.dirname(mine), exist_ok=True)
                with open(mine, "a", encoding="utf-8") as fh:
                    fh.write("".join(ln + "\n" for ln in new))
            line = new[-1] if new else None
            ok = bool(line and ue_run.good_daily(line))
            body = self.read(box, "comment.md") or (f"ROLE: QA and Build | session {stamp()} (tools/kickoff.py)\n"
                                                    + (line or "No DAILY line: the session did not finish daily.ps1."))
            self.gh.comment(c.number, body)
            self.j(cid, "step", command="tools\\ue\\daily.ps1 (QA and Build session)", exit_code=0 if ok else 1,
                   output_tail=line or "", note=f"kickoff: daily on {sha[:12]}")
            say(f"DAILY {cid} {sha[:7]}: " + ("PASS" if ok else "FAIL" if line else "no DAILY line"))
            return ok

    @staticmethod
    def sig(job):
        kind, c, pr, _ = job
        return (kind, c.key, pr["number"] if pr else None, len(pr.get("comments") or []) if pr else 0)

    def gate_check(self, cards):
        """Every filed card closed: the next gate is a human's call (never closed by kickoff)."""
        if any(c.open for c in cards) or not cards:
            return
        tags = check_card.gate_tags(ROOT)
        nxt = next((g for g in check_card.GATES if f"gate-{g}" not in tags), None)
        if not nxt:
            return
        if nxt == "G4" and self.practice:
            say("PRACTICE: G4 is blocked in a practice repo; nothing more to run")
            return
        try:
            gate = next((i for i in self.gh.all_issues() if re.match(rf"\s*\[GATE\] {nxt}\b", i.get("title") or "")),
                        None)
            num = gate["number"] if gate else self.gh.create_issue(
                f"[GATE] {nxt} close", f"Gate {nxt}: the gate record (pipeline/templates/gate-record.md), then the "
                "scope decision-maker's outcome. kickoff never closes a gate.", ["gate"])
        except RuntimeError as e:
            say(f"ERROR gate {nxt}: {e}")
            return
        self.raise_ask(num, seat_person("scope decision-maker") or "Scope-decision-maker",
                       f"close {nxt}: post the gate record and the outcome (check_card.py --gate-record)")

    def run(self):
        if not self.dry:
            if native_windows():   # agent sessions run plain git in the worktrees: the repo setting covers them
                git("config", "core.longpaths", "true")
            self.gh.ensure_labels()
            self.j(KICK, "start", role="producer", note=f"kickoff: agent={self.agent_label()} practice={self.practice}")
            self.run_id = self.runlog(journal.start_run, "practice" if self.practice else "kickoff", self.agent_label(),
                                      self.model_map(), self.tester_prompt,
                                      f"parallel={self.parallel} watch={self.watch or 'no'}", ROOT)
            if self.run_id is not None:
                say(f"RUN #{self.run_id}: pipeline {journal.pipeline_version(ROOT)['string']} | GDD "
                    f"{journal.gdd_revision(ROOT)} | agent {self.agent_label()} | prompt "
                    f"{journal.sha256(self.tester_prompt)[:12] if self.tester_prompt else 'none'} "
                    f"(compare runs: python3 tools/journal.py compare <a> <b>)")
        if self.dry:
            return self.dry_plan()
        pool = concurrent.futures.ThreadPoolExecutor(max_workers=self.parallel)
        futures = {}
        primed, gh_down = False, 0
        while True:
            try:   # a gh call that still fails after its retries skips this cycle; it never crashes the run
                if not primed:
                    self.producer_until_clean()
                    self.last_done = {c.key for c in self.cards() if c.done}
                    primed = True
                jobs, waiting, cards = self.plan()
                gh_down = 0
                jobs = [j for j in jobs if self.sig(j) not in self.seen]
                if self.bounded():   # in-flight cards finish (fix rounds, review, merge); no new card starts
                    jobs = [j for j in jobs if j[0] != "build" or j[1].key in self.started]
                for kind, c, pr, fb in jobs:
                    if len(futures) >= self.parallel:
                        break
                    self.seen.add(self.sig((kind, c, pr, fb)))
                    if kind in ("build", "fix"):
                        self.started.add(c.key)
                    if kind == "build" and c.key == "0.3":
                        try:
                            self.ensure_jam_start()
                        except Exception as e:   # the tag is a record: ask, and the card still runs
                            self.raise_ask(c.number, seat_person("producer / time keeper") or "Producer",
                                           f"tag jam-start on main: kickoff could not ({str(e)[:160]})")
                    self.running[c.key] = (kind, [] if kind == "daily" else c.lanes)
                    if kind == "daily":
                        self.daily_q = [q for q in self.daily_q if q[0].key != c.key]
                    fn = (lambda c=c, pr=pr: self.reviewer(c, pr)) if kind == "review" else \
                        (lambda c=c, pr=pr: self.daily_run(c, pr)) if kind == "daily" else \
                        (lambda c=c, pr=pr: self.merger(c, pr)) if kind == "merge" else \
                        (lambda c=c, fb=fb: self.builder(c, fb))
                    say(f"START {kind} UE-{c.key} #{c.number} " + (f"PR #{pr['number']} (kickoff, no agent session)"
                                                                   if kind == "merge" else "role=" +
                        (c.reviewer_key if kind == "review" else "qa-build" if kind == "daily" else c.owner_key)))
                    futures[pool.submit(fn)] = (c.key, self.sig((kind, c, pr, fb)), kind)
                if futures:
                    done, _ = concurrent.futures.wait(futures, return_when=concurrent.futures.FIRST_COMPLETED)
                    for f in done:
                        key, sig, kind = futures.pop(f)
                        self.running.pop(key, None)
                        err = f.exception()
                        if isinstance(err, GHError) and self.gh_job_failed(sig, kind, key, err):
                            self.seen.discard(sig)   # GitHub failed under the job: it runs again next cycle
                        elif err is not None:   # a job that crashed kickoff's own code: never a silent idle
                            say(f"ERROR {kind} UE-{key}: {type(err).__name__}: {err}")
                            self.run_failures.append(f"{kind} UE-{key} stopped on {type(err).__name__}: {str(err)[:160]}")
                        elif f.result() == "retry":
                            self.seen.discard(sig)   # the failed session runs again in this run (bounded: MAX_FAILS)
                        elif f.result() == "pending":
                            self.ci_pending.add(sig)
                    continue
                if self.ci_pending:   # nothing else to run: wait for CI, then plan again (bounded: CI_WAIT)
                    say(f"WAITING on CI for {len(self.ci_pending)} PR(s); checking again in {CI_POLL} s")
                    time.sleep(CI_POLL)
                    self.seen -= self.ci_pending
                    self.ci_pending.clear()
                    continue
                done_now = {c.key for c in cards if c.done}
                if done_now != self.last_done:
                    self.last_done = done_now
                    if self.producer_until_clean():
                        continue
                if self.until:   # --until: the gate's Mac package once its path is merged; kickoff never closes a gate
                    step = self.milestone(cards)
                    if step == "again":
                        continue
                    if step == "stop":
                        break
                else:
                    self.gate_check(cards)
                if self.watch and not self.bounded():
                    say(f"WAITING on humans ({len(waiting)}); polling again in {self.watch} min")
                    time.sleep(self.watch * 60)
                    continue
                break
            except GHError as e:
                gh_down += 1
                if self.gh_cycle_failed(e, gh_down):
                    break
        pool.shutdown()
        lost = f", {self.journal_lost} journal write(s) lost" if self.journal_lost else ""
        if self.run_failures:
            self.runlog(journal.add_run_outcome, self.run_id, "end", outcome="failed", exit_code=1,
                        note=f"{self.sessions} session(s), {self.raised} ask(s): " + "; ".join(self.run_failures))
            self.j(KICK, "checkpoint", note="kickoff: failed: " + "; ".join(self.run_failures),
                   next_step=f"read the failure above, fix it, then run {me()} again")
            say(f"KICKOFF FAILED: {'; '.join(self.run_failures)}. {self.sessions} session(s) this run, {self.raised} "
                f"new needs-human ask(s){lost}. Fix it, then run {me()} again (it resumes from the journal and GitHub).")
            return 1
        if self.reached:
            line = f"KICKOFF {self.until} reached: {self.reached}"
            self.runlog(journal.add_run_outcome, self.run_id, "end", outcome="reached", note=line)
            self.j(KICK, "checkpoint", note=f"kickoff: {line}", next_step=f"the {self.until} gate record (scope "
                   "decision-maker; pipeline/templates/gate-record.md)")
            say(f"{line} ({self.sessions} session(s), {self.raised} new needs-human ask(s){lost})")
            return 0
        if self.until:
            targets, missing = self.gate_targets(cards)
            by_key = {c.key: c for c in cards}
            left = sorted((k for k in targets if k not in by_key or not by_key[k].done), key=check_card.natural)
            say(f"UNTIL {self.until} not reached: " + ("; ".join(
                x for x in ((f"waiting on {', '.join('UE-' + k for k in left[:12])}" if left else ""),
                            (f"no card yet for MVP {', '.join(map(str, missing))}" if missing else "")) if x)
                or "the Mac package did not pass"))
        if self.bounded():
            done = self.done_merged | self.done_blocked
            line = (f"KICKOFF bounded: {len(done)} card(s) done this run (merged {len(self.done_merged)}, blocked "
                    f"{len(self.done_blocked)}); run again to continue")
            self.runlog(journal.add_run_outcome, self.run_id, "end", outcome="bounded", note=line)
            self.j(KICK, "checkpoint", note=f"kickoff: {line}", next_step=f"run {me()} again to continue")
            say(f"{line} ({self.sessions} session(s), {self.raised} new needs-human ask(s){lost})")
            return 0
        self.say_machine_waits(waiting)
        self.runlog(journal.add_run_outcome, self.run_id, "end", outcome="idle",
                    note=f"{self.sessions} session(s), {self.raised} ask(s)")
        self.j(KICK, "checkpoint", note=f"kickoff: idle after {self.sessions} session(s), {self.raised} ask(s)",
               next_step=f"humans answer the needs-human queue, then run {me()} again")
        say(f"KICKOFF idle: {self.sessions} session(s) this run, {self.raised} new needs-human ask(s){lost}. "
            f"Answer the needs-human queue, then run {me()} again (it resumes from the journal and GitHub)."
            + (f" PRE-JAM: every other card waits for the jam start; in a test repo `{me()} --practice` runs them."
               if self.prejam is not None else ""))
        return 0

    @staticmethod
    def say_machine_waits(waiting):
        """The cards this machine leaves to the other one, by name, so an idle run says what it waits for (the cards
        that list them in After wait with them; every other ready card runs here)."""
        for what, there in (("the Mac build machine", "tools/kickoff.sh on the Mac"),
                            ("the Windows packaging machine", "tools\\kickoff.ps1 there")):
            cards = [w.split(": ", 1)[0] for w in waiting if w.endswith(f"runs on {what} (kickoff there picks it)")]
            if cards:
                say(f"WAITING on {what}: {', '.join(cards)}; run {there} (the cards after them wait with them)")

    def dry_plan(self):
        say(f"DRY RUN agent={self.agent_label()} practice={'yes' if self.practice else 'no'} parallel={self.parallel}; "
            "nothing is launched or written")
        if getattr(self, "until", None):
            for ln in until_plan(self.until)[0]:
                say(ln)
        tier, model = self.model("producer", agent=self.agent_for("producer"))
        if self.split:
            for kind in SPLIT_KINDS:
                r = {"build": "gameplay-dev", "review": "dev-lead", "critic": "art-director", "producer": "producer"}[kind]
                t, m = self.model(r, kind == "review", kind == "critic", self.agent_for(kind))
                say(f"split: {kind} sessions on {self.agent_for(kind)} (tier={t} model={m or 'default'})")
        say(f"would run: Producer session (tier={tier} model={model or 'default'}): file/refresh cards from "
            "pipeline/day0-cards.md, then check_card until 0 problems")
        try:
            cards = self.cards()
            prs = self.gh.prs()
        except (RuntimeError, OSError, ValueError) as e:
            say(f"GitHub not readable ({e}); the first wave from pipeline/day0-cards.md:")
            for cid, name, after in check_card.day0_table(ROOT):
                if not after:
                    say(f"  UE-{cid} {name}")
            return 0
        done = {c.key for c in cards if c.done}
        for c in sorted(cards, key=lambda c: check_card.natural(c.key)):
            if not c.open:
                continue
            ready = all(a in done for a in c.after)
            pr = self.card_pr(c, prs)
            if self.prejam is not None and c.key not in self.prejam:
                what = "waits for the jam start (PRE-JAM mode)"
            elif c.owner_key is None:
                what = "Owner is not an agent role (check_card fails it)"
            elif pr and pr.get("state") == "OPEN":
                what = f"PR #{pr['number']}: review, then kickoff merges it when CI and check_pr pass"
            elif not ready:
                what = "waits on After"
            elif getattr(self, "until", None) and c.key not in self.gate_targets(cards)[0]:
                what = f"not on the {self.until} path (--until {self.until})"
            elif c.windows and not packaging_machine():
                what = "runs on the Windows packaging machine (kickoff there picks it)"
            elif c.mac and not mac_machine():
                what = "runs on the Mac build machine (kickoff there picks it)"
            else:
                t, m = self.model(c.owner_key, agent=self.agent_for("build"))
                what = (f"would build: role={c.owner_key} tier={t} model={m or 'default'}"
                        + (f" agent={self.agent_for('build')}" if self.split else ""))
            say(f"  UE-{c.key} #{c.number}: {what}")
        return 0


def day0_rows(root=ROOT):
    """{id: (name, owner cell, reviewer, after ids, done-when lines)} from the pipeline/day0-cards.md table."""
    out = {}
    with open(os.path.join(root, "pipeline", "day0-cards.md"), encoding="utf-8") as fh:
        for line in fh:
            cells = [x.strip() for x in line.strip().strip("|").split(" | ")] if line.startswith("| ") else []
            if len(cells) >= 7 and check_card.DAY0_ID.fullmatch(cells[0]):
                out[cells[0]] = (cells[1], cells[2], cells[3], check_card.DAY0_ID.findall(cells[5]),
                                 [d.strip() for d in cells[6].split("<br>")])
    return out


WIN_STEP = re.compile(r"\.ps1\b|\$env:|\bplatform=Win64\b", re.I)   # a step only the Windows machine can run


def until_plan(gate, root=ROOT):
    """(lines, problems): the order a kickoff --until <gate> on the Mac builds the gate's Day-0 cards in (After first),
    then the MVP cards and the Mac package; a problem for each card on the path that waits for the Windows machine,
    names a Windows step, has a person act (a `HUMAN <kind>:` line) or has no agent reviewer. Read from the files only
    (no GitHub), so it runs before anything is filed."""
    rows = day0_rows(root)
    rk = role_keys()
    path, todo = set(), list(check_card.gate_cards(root, gate))
    while todo:
        k = todo.pop()
        if k in path or k not in rows:
            continue
        path.add(k)
        todo += rows[k][3]
    order, placed = [], set()
    while len(order) < len(path):   # After first; ties in table order (natural)
        ready = sorted((k for k in path - placed if all(a in placed or a not in path for a in rows[k][3])),
                       key=check_card.natural)
        if not ready:
            break
        order.append(ready[0])
        placed.add(ready[0])
    due = check_card.gate_mvp(root).get(gate, [])
    lines, probs = [f"UNTIL {gate} on the Mac: {len(order)} Day-0 card(s), then the MVP cards for MVP "
                    f"{', '.join(map(str, due)) or 'none'}, then the {gate} Mac package"], []
    for n, k in enumerate(order, 1):
        name, owner, reviewer, after, done = rows[k]
        role = owner.partition("/")[0].strip()
        where = "Mac" if any(RUNS_ON_MAC.search(d) for d in done) else "any machine"
        lines.append(f"  {n:2}. UE-{k} {name[:64]} | build {role}, review {reviewer} | {where}"
                     + (f" | after {', '.join('UE-' + a for a in after)}" if after else ""))
        if any(RUNS_ON_WINDOWS.search(d) for d in done):
            probs.append(f"UE-{k}: runs on the Windows packaging machine, but {gate} lists it")
        win = [d for d in done if WIN_STEP.search(d) and not RUNS_ON_MAC.search(d)]
        if win:
            probs.append(f"UE-{k}: a Windows step on the {gate} path: {win[0][:100]}")
        for d in done:
            m = check_card.HUMAN_LINE.match(d)
            if m:
                probs.append(f"UE-{k}: a person acts (HUMAN {m.group('kind')}:): {d[:100]}")
        if rk.get(reviewer) is None:
            probs.append(f"UE-{k}: reviewer {reviewer!r} is not an agent role")
    lines.append(f"  then: the Producer files the MVP cards for MVP {', '.join(map(str, due))} ([{gate}] in "
                 "docs/jam-brief.md) once UE-0.3 merges; kickoff builds each and every card it lists in After")
    lines.append(f"  last: the {gate} Mac package, run by kickoff itself: `bash tools/ue/daily.sh` on main (build, "
                 "tests, package, smoke) must print a DAILY line with package=PASS and smoke=PASS")
    wait = sorted((k for k, r in rows.items() if any(RUNS_ON_WINDOWS.search(d) for d in r[4])), key=check_card.natural)
    lines.append(f"  not on the path (they wait for the Windows packaging machine): "
                 f"{', '.join('UE-' + k for k in wait) or 'none'}")
    lines.append(f"UNTIL {gate}: {len(probs)} step(s) need a person, the Windows machine or a human reviewer"
                 + (": " + "; ".join(probs) if probs else ""))
    return lines, probs


# ---------- entry ----------
QUESTION = ("Both Claude Code and Codex are installed. Which one should run the jam? Type claude or codex, then "
            "press Enter: ")


def detect_agent(explicit, ask=None):
    """The agent CLI to use: --agent, else the only one on PATH, else one plain question when both are."""
    if explicit:
        return explicit
    found = [a for a in ("claude", "codex") if shutil.which(a)]
    if not found:
        raise Refused("neither Claude Code nor Codex is installed. Install one: type `npm install -g @openai/codex` "
                      f"(Codex) or `npm install -g @anthropic-ai/claude-code` (Claude Code), then run {me()} again.")
    if len(found) == 1:
        say(f"kickoff: using {found[0]} (the only agent installed)")
        return found[0]
    ask = ask or input
    try:
        answer = ask(QUESTION).strip().lower()
    except EOFError:
        answer = ""
    if answer in ("claude", "claude code", "c"):
        return "claude"
    if answer in ("codex", "x"):
        return "codex"
    raise Refused(f"I did not get claude or codex as the answer. Run {me()} --agent codex or {me()} --agent claude.")


def set_practice():
    if practice.is_real_repo(ROOT):
        raise Refused(f"--practice is only for a test copy, and this is the team repo ({practice.real_slug(ROOT)}). "
                      f"Make a fork or a copy of the repo and run {me()} --practice there.")
    if practice.is_practice(ROOT):
        return
    rc, branch = git("rev-parse", "--abbrev-ref", "HEAD")
    if branch != "main":
        raise Refused(f"practice mode starts on the main branch, and you are on {branch}. Type `git checkout main`, "
                      f"then run {me()} --practice again.")
    if "origin" in git("remote")[1].split():   # kickoff merges PRs into origin main: start from it, then push on top
        rc, out = git("pull", "-q", "--ff-only", "origin", "main")
        if rc:
            raise Refused(f"your main has commits origin/main does not have, so the practice marker cannot be pushed. "
                          f"Type `git pull origin main`, fix what it says, then run {me()} --practice again.")
    with open(os.path.join(ROOT, practice.MARKER), "w", encoding="utf-8") as fh:
        fh.write(practice.MARKER_TEXT)
    git("add", practice.MARKER, check=True)
    env = dict(keys.scrub(os.environ), JAM_HUMAN=os.environ.get("JAM_HUMAN") or "kickoff-practice")
    for v in ("JAM_ROLE", "JAM_KICKOFF"):
        env.pop(v, None)
    git("commit", "-q", "-m", "Practice mode: .pipeline-practice (tools/kickoff.py --practice)", env=env, check=True)
    if "origin" in git("remote")[1].split():
        git("push", "-q", "origin", "main", env=env, check=True)
    say(f"PRACTICE mode on: {practice.MARKER} committed and pushed (D39 lifted; submission, upload and G4 blocked)")


def parse_split(spec, primary, have=None):
    """{kind: agent} from --split / KICKOFF_SPLIT. '' or 'auto' = SPLIT_DEFAULT (builders on Codex, reviewers, critics
    and the Producer on Claude Code). A kind left out stays on the primary agent. Needs both CLIs installed (have:
    the agents found); with one, every session runs on it and the returned dict is empty. Raises Refused on a bad spec."""
    have = [a for a in ("claude", "codex") if shutil.which(a)] if have is None else have
    spec = (spec or "").strip()
    text = SPLIT_DEFAULT if spec in ("", "auto", "1", "yes") else spec
    out = {}
    for part in [p.strip() for p in text.split(",") if p.strip()]:
        kind, _, agent = part.partition("=")
        kind, agent = kind.strip().lower(), agent.strip().lower()
        if kind in ("builder", "builders"):
            kind = "build"
        if kind in ("reviews", "reviewer", "reviewers"):
            kind = "review"
        if kind in ("critics",):
            kind = "critic"
        if kind not in SPLIT_KINDS or agent not in ("claude", "codex"):
            raise Refused(f"--split {spec!r}: each part is <kind>=<agent>, kind one of {', '.join(SPLIT_KINDS)}, agent "
                          f"claude or codex (e.g. --split {SPLIT_DEFAULT})")
        out[kind] = agent
    missing = [a for a in set(out.values()) | {primary} if a not in have]
    if missing:
        say(f"kickoff: --split needs both Claude Code and Codex installed; {', '.join(sorted(missing))} is not, so every "
            f"session runs on {primary}")
        return {}
    return out


def connection_gate(agent):
    import connections
    res = connections.check(ROOT, agent)
    lines = connections.write_out(res, os.path.join(ROOT, "Saved", "connections.txt"), ROOT)
    req = [r for r in res if r.required]
    missing_keys = [r.name.split()[2] for r in res if r.name.startswith("API key") and r.state == "NOT CONNECTED"]
    if missing_keys:
        say("kickoff: API keys missing (assets fall back to placeholders and procedural audio): "
            + ", ".join(missing_keys) + " -> tools/keys.py status")
    return lines, req


class PlainParser(argparse.ArgumentParser):
    def error(self, message):
        say(f"kickoff: I did not understand that ({message}). Type {me()} with no options to start, or {me()} --help.")
        sys.exit(2)


def read_prompt(a):
    if a.prompt_file:
        try:
            with open(a.prompt_file, encoding="utf-8") as fh:
                return fh.read()
        except OSError:
            raise Refused(f"I cannot read the prompt file {a.prompt_file}. Check the name, then run {me()} again.")
    return a.prompt


def team_art_lines():
    """(lines, bad): how many images under the team's art folders (Assets/, Mockups/) joined the art references
    (tools/art_check.py load_spec, references.json team_art), and each one that cannot be read. bad = one cannot."""
    import art_check
    try:
        spec = art_check.load_spec(ROOT)
    except (OSError, ValueError) as e:
        return [f"kickoff: team art: FAIL cannot read {art_check.REFERENCES} ({e})"], True
    probs = art_check.team_art_problems(spec)
    return ["kickoff: " + art_check.team_art_line(spec)] + ["kickoff: " + p for p in probs], bool(probs)


def version_line(agent=None):
    import journal as jr
    return (f"kickoff: pipeline {jr.pipeline_version(ROOT)['string']} | GDD {jr.gdd_revision(ROOT)}"
            + (f" | agent {agent}" if agent else ""))


def main(argv=None):
    try:
        return _main(argv)
    except KeyboardInterrupt:
        say(f"kickoff: stopped by Ctrl+C. Run {me()} again to pick up where it stopped.")
        return 130
    except Exception as e:  # never a traceback for a person; KICKOFF_DEBUG=1 shows it
        if os.environ.get("KICKOFF_DEBUG") == "1":
            traceback.print_exc()
        say(f"kickoff: stopped by an unexpected error ({type(e).__name__}: {str(e)[:160]}). Run {me()} --check "
            "and send its output to the team.")
        return 2


def _main(argv=None):
    argv = sys.argv[1:] if argv is None else list(argv)
    first = not argv   # no options: version, the full connection check, then start
    ap = PlainParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--agent", choices=("claude", "codex"))
    ap.add_argument("--split", nargs="?", const="auto", default=os.environ.get("KICKOFF_SPLIT") or None,
                    metavar="KIND=AGENT,...", help="run builders, reviewers, critics and the Producer on different agent "
                    f"CLIs when both are installed (default {SPLIT_DEFAULT})")
    ap.add_argument("--check", action="store_true", help="run the connection check only")
    ap.add_argument("--live", action="store_true", help="with --check: one free auth request per API key")
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--practice", action="store_true")
    ap.add_argument("--parallel", type=int, default=int(os.environ.get("KICKOFF_PARALLEL", "2")))
    ap.add_argument("--watch", type=float, metavar="MIN")
    ap.add_argument("--max-cards", type=int, metavar="N", default=int(os.environ.get("KICKOFF_MAX_CARDS") or 0),
                    help="bound the run: start no new card once N cards merged or got blocked in this run; cards in "
                         "flight finish, then it stops (run again to continue)")
    ap.add_argument("--until", type=str.upper, choices=UNTIL_GATES, metavar="G1",
                    default=(os.environ.get("KICKOFF_UNTIL") or "").upper() or None,
                    help="target a gate: build only the cards on its path (its Day-0 cards, its MVP cards and what "
                         "they need), then run its Mac package (tools/ue/daily.sh) and stop when it passes")
    ap.add_argument("--prompt", help="the tester's prompt for this run (recorded; added to every session prompt)")
    ap.add_argument("--prompt-file", help="read the tester's prompt from this file")
    ap.add_argument("--gdd", metavar="REV|FILE", help="the GDD revision (1.4) or .md file this run tests")
    ap.add_argument("--set-current", action="store_true", help="with --gdd: also point docs/gdd/CURRENT at it")
    a = ap.parse_args(argv)
    try:
        problem = install_problem()
        if problem:
            say(problem)
            return 2
        inside = [k for k in AGENT_ENV if os.environ.get(k)]
        if inside:
            raise Refused(f"this window is inside an agent session ({'/'.join(inside)} is set). Open a new plain "
                          f"terminal window and run {me()} there.")
        tester_prompt = read_prompt(a)
        if a.set_current and not a.gdd:
            raise Refused(f"--set-current needs --gdd. Type {me()} --gdd 1.4 --set-current.")
        if a.gdd:   # before anything else: a GDD the pipeline cannot import never starts a run
            code, lines, env = gdd_select.choose(a.gdd, ROOT, set_current=a.set_current,
                                                 check=a.check or a.dry_run)
            for ln in lines:
                say(ln.replace("gdd_select: ", "kickoff: ", 1))
            if code:
                return 2
            os.environ.pop(journal.GDD_ENV, None)
            os.environ.update(env)   # run-scoped: this process and every agent session it starts
        elif os.environ.get(journal.GDD_ENV):
            os.environ.pop(journal.GDD_ENV)   # a stale JAM_GDD from the shell never picks the GDD silently
        art_bad = False
        if a.check or first or a.gdd:   # first thing a tester sees: which pipeline version (and GDD) this is
            say(version_line(a.agent))
            art_lines, art_bad = team_art_lines()   # then how much team art the art tools compare against
            for ln in art_lines:
                say(ln)
        agent = detect_agent(a.agent)
        split = {}
        if a.split is not None:
            have = ["claude", "codex"] if os.environ.get("KICKOFF_AGENT_CMD") else None   # tests: a stub plays both
            split = parse_split(a.split, agent, have)
            if split:
                say("kickoff: split run: " + ", ".join(f"{k} sessions on {split.get(k, agent)}" for k in SPLIT_KINDS))
        agents = sorted(set(split.values()) | {agent})
        if a.check:
            import connections
            rc = max(connections.main(["--agent", ag] + (["--live"] if a.live else [])) for ag in agents)
            plan_bad = False
            if a.until:   # the path a --until run takes, from the files: no person, no Windows step on it
                lines, probs = until_plan(a.until)
                for ln in lines:
                    say(ln)
                plan_bad = bool(probs)
            return max(rc, 1 if art_bad or plan_bad else 0)   # a team-art image that cannot be read fails the check
        if not a.dry_run:
            hooks = subprocess.run([sys.executable, os.path.join(HERE, "install_git_hooks.py"), "--repo", ROOT],
                                   capture_output=True, text=True)
            if hooks.returncode:
                say("kickoff: " + (hooks.stderr.strip().splitlines() or ["git hooks not installed"])[-1])
        if first and os.environ.get("KICKOFF_SKIP_CHECK") != "1":
            import connections
            if max(connections.main(["--agent", ag]) for ag in agents):
                say(f"kickoff: fix the NOT CONNECTED lines marked (required) above, then run {me()} again.")
                return 4
        if not a.dry_run and not first and os.environ.get("KICKOFF_SKIP_CHECK") != "1":
            lines, req = [], []
            for ag in agents:
                ln, rq = connection_gate(ag)
                lines, req = lines + ln, req + rq
            if req:
                for ln in lines:
                    if ln.startswith("NOT CONNECTED") and ln.endswith("(required)"):
                        say(ln)
                say(f"kickoff: {len(req)} required connection(s) missing (above). Do what each NOT CONNECTED line "
                    f"says, then run {me()} again. `{me()} --check` lists everything")
                return 4
        if a.practice and not a.dry_run:
            set_practice()
        import submission_check
        if now() < submission_check.JAM_START and not practice.is_practice(ROOT):
            say(f"kickoff: before the jam start ({submission_check.JAM_START.isoformat()}) agents may not build game "
                f"files (D39): PRE-JAM mode runs only the pre-jam cards (tools, agent setup, rules, the synthetic "
                f"workbench sample; Official Rules 7(h)). In a test repo run `{me()} --practice` once to run every card.")
            rc = Kickoff(agent, a.parallel, a.dry_run, a.watch, tester_prompt, prejam=True, split=split,
                         max_cards=a.max_cards, until=a.until).run()
            return 3 if rc == 0 else rc
        return Kickoff(agent, a.parallel, a.dry_run, a.watch, tester_prompt, split=split, max_cards=a.max_cards,
                       until=a.until).run()
    except Refused as e:
        say(f"kickoff: {e}")
        return 2


if __name__ == "__main__":
    sys.exit(main())
