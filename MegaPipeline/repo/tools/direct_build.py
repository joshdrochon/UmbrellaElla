#!/usr/bin/env python3
"""The direct build: what tools/kickoff.sh runs while docs/build/MODE says `direct`. Stdlib only. No GitHub card,
issue or PR: gh is never called and the workers may not call it either.

For every area HANDOFF.md (on origin/main) does not mark done, merged, or held by someone else, as one job:
  1. A worktree .pipeline/direct/<name> on area/<name> (origin's branch, else new from main), main merged in; the
     lane guard (tools/area.py) is installed for the repo.
  2. A Claude Code worker builds there from docs/build/areas/<name>.md: `claude -p <prompt> --permission-mode
     bypassPermissions --disallowedTools Bash(git push:*) Bash(gh:*) --model sonnet`, JAM_ROLE=gameplay-dev.
  3. Kickoff commits what the worker left inside the lane (on native Windows the agent hook blocks a worker's shell,
     so kickoff does the commit); a tracked change outside the lane is stashed, never committed or lost.
  4. The local gates run in the worktree: docs/build/gates.txt on main (one command per line; `mac:` / `win:` limits
     a line to one OS; {py} is this Python; `cmd => text` also needs that text in the output), else DEFAULT_GATES.
     Unreal commands wait for an engine slot (tools/ue_slot.py, UE_SLOTS default 2).
  5. All gates pass: one at a time, main is merged into the area again, its lane is checked against main, it is merged
     into main and `git push --atomic origin main area/<name>` runs (rejected because someone pushed first: fetch,
     merge again, push again). A gate fails: only area/<name> is pushed, so the next person resumes from it.
  6. HANDOFF.md's row for the area gets the result (Status; Who has it = free), committed on main and pushed:
     `merged <sha>` (resumed next run: the brief may have more), `done (merged <sha>)` once the worker wrote
     AREA DONE in its status file (skipped from then on), `gates failed: ...` or `stopped: <why>`.
Jobs at once: every ready area whose lane overlaps no running area's lane (default auto), at most os.cpu_count();
--parallel N / KICKOFF_PARALLEL caps it. KICKOFF_AGENT_CMD (tests) replaces `claude`.
Exit 0 = every area merged (or nothing to do), 1 = an area failed a gate or was refused, 2 = cannot start.
"""
import os
import re
import shlex
import shutil
import subprocess
import sys
import threading

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import area  # noqa: E402

MODE_FILE = "docs/build/MODE"
GATES_FILE = "docs/build/gates.txt"
WORKER_ROLE = area.ROLE
WORKER_MODEL = "sonnet"
WORKER_DENY = ["Bash(git push:*)", "Bash(gh:*)"]
# The gates HANDOFF.md lists (and tools/build/gate.sh greps): `command => text the output must contain`.
DEFAULT_GATES = [
    "mac: tools/ue/build.sh => build exit: 0",
    "win: powershell -NoProfile -ExecutionPolicy Bypass -File tools/ue/build.ps1 => build exit: 0",
    "mac: tools/ue/test.sh => PASS",
    "win: powershell -NoProfile -ExecutionPolicy Bypass -File tools/ue/test.ps1 => PASS",
    "{py} tools/module_check.py => 0 problem", "{py} tools/manifest_check.py => 0 problem",
    "{py} tools/feel_check.py => 0 problem", "{py} tools/encounter_check.py => 0 problem",
]
FINISHED = ("done",)   # "merged <sha>" areas run again: their brief may have more work (status file)
FREE = ("", "-", "free", "nobody", "none", "kickoff")
DONE_MARK = "AREA DONE"   # a worker writes it in docs/build/areas/<name>-status.md when the brief is finished


QUESTION = ("Run with the GitHub ceremonies (cards, PRs, reviews: `cards`) or without (direct local build: `direct`)? "
            "[direct] ")
CI_ENV = ("CI", "GITHUB_ACTIONS")


def saved_mode(root):
    """'direct' or 'cards' from docs/build/MODE, or None when there is no MODE file."""
    try:
        with open(os.path.join(root, MODE_FILE), encoding="utf-8") as fh:
            word = fh.read().strip().lower()
    except OSError:
        return None
    return "cards" if word == "cards" else "direct"


def mode(root):
    """The saved mode; no MODE file = direct."""
    return saved_mode(root) or "direct"


def resolve_mode(root, override=None, ask=input, tty=None, env=None, say=print):
    """--mode wins for one run. Else docs/build/MODE. Else, on a terminal outside CI, ask once and save the answer;
    with no terminal (or in CI) use direct without asking."""
    if override:
        return override
    found = saved_mode(root)
    if found:
        return found
    env = os.environ if env is None else env
    tty = sys.stdin.isatty() if tty is None else tty
    if not tty or any(env.get(k) for k in CI_ENV):
        return "direct"
    for _ in range(3):
        ans = (ask(QUESTION) or "").strip().lower()
        if ans in ("", "direct", "d"):
            pick = "direct"
        elif ans in ("cards", "card", "c"):
            pick = "cards"
        else:
            say("kickoff: type cards or direct (Enter = direct).")
            continue
        os.makedirs(os.path.join(root, os.path.dirname(MODE_FILE)), exist_ok=True)
        with open(os.path.join(root, MODE_FILE), "w", encoding="utf-8", newline="\n") as fh:
            fh.write(pick + "\n")
        say(f"kickoff: saved `{pick}` to {MODE_FILE}. Change it later: edit that file (cards or direct), or pass "
            f"--mode cards|direct for one run. Commit the file to give the whole team the same mode.")
        return pick
    return "direct"


def cells(line):
    return [c.strip() for c in line.strip().strip("|").split("|")]


def table(text):
    """HANDOFF.md's area table -> (header cells, {area: row cells}, {area: line index}). Empty when there is none."""
    lines = text.splitlines()
    for i, ln in enumerate(lines):
        head = [c.lower() for c in cells(ln)] if ln.strip().startswith("|") else []
        if "area" in head and col(head, "status") is not None:
            rows, at = {}, {}
            br = col(head, "branch")
            for j in range(i + 1, len(lines)):
                if not lines[j].strip().startswith("|"):
                    break
                c = cells(lines[j])
                if set("".join(c)) <= set("-: "):
                    continue
                # The name: the Branch cell (`area/move`), else the Area cell's first word ("move: Ella movement").
                raw = c[br] if br is not None and br < len(c) and "area/" in c[br] else c[head.index("area")]
                name = re.split(r"[\s:]", raw.strip("` ").split("area/")[-1].strip("` "))[0]
                rows[name], at[name] = c, j
            return head, rows, at
    return [], {}, {}


def col(head, *names):
    for n in names:
        for k, h in enumerate(head):
            if h.startswith(n):
                return k
    return None


def todo(handoff, names):
    """(areas to resume, [(area, why skipped)])."""
    head, rows, _ = table(handoff)
    st, who = col(head, "status"), col(head, "who")
    go, skip = [], []
    for n in names:
        row = rows.get(n)
        if row is not None and st is not None and st < len(row) and row[st].lower().startswith(FINISHED):
            skip.append((n, row[st]))
        elif row is not None and who is not None and who < len(row) and row[who].lower() not in FREE:
            skip.append((n, f"held by {row[who]}"))
        else:
            go.append(n)
    return go, skip


def gates(ref):
    text = area.show(ref, GATES_FILE)
    lines = text.splitlines() if text is not None else DEFAULT_GATES
    me = "win" if os.name == "nt" else "mac"
    out = []
    for ln in lines:
        ln = ln.strip()
        if not ln or ln.startswith("#"):
            continue
        m = re.match(r"^(mac|win):\s*(.*)$", ln)
        if m:
            if m.group(1) != me:
                continue
            ln = m.group(2)
        out.append(ln.replace("{py}", shlex.quote(sys.executable) if os.name != "nt" else f'"{sys.executable}"'))
    return out


def worker_argv(prompt):
    stub = os.environ.get("KICKOFF_AGENT_CMD")
    base = shlex.split(stub) if stub else [shutil.which("claude") or "claude"]
    if not stub:
        base[0] = shutil.which(base[0]) or base[0]   # Windows: npm installs claude.cmd
    return base + ["-p", prompt, "--permission-mode", "bypassPermissions", "--disallowedTools", *WORKER_DENY,
                   "--model", WORKER_MODEL]


def worker_prompt(name, lane):
    return (area.prompt(name, lane) + "\n6. You run unattended under tools/kickoff.sh (direct build). Never run "
            "tools/kickoff, gh or git push. When you exit, kickoff commits what you left inside the lane, runs the "
            f"gates and merges the area if they pass. When every item of your brief is done, add the line "
            f"`{DONE_MARK}` to {area.BRIEFS}/{name}-status.md; kickoff then marks the area done in HANDOFF.md.")


LOCK = threading.Lock()        # one git operation on the shared repo (worktrees, main, HANDOFF) at a time
PRINT = threading.Lock()


def g(cwd, *a, check=True):
    return area.git(*a, check=check, root=cwd)


def changed(wt):
    """(tracked changed paths, untracked paths) in a working tree."""
    tracked, untracked = [], []
    for ln in g(wt, "status", "--porcelain", "-z", "--untracked-files=all").stdout.split("\0"):
        if len(ln) > 3:
            (untracked if ln.startswith("??") else tracked).append(ln[3:])
    return tracked, untracked


def commit_leftovers(wt, name, lane, say):
    tracked, untracked = changed(wt)
    inside = [p for p in tracked + untracked if area.in_lane(p, lane, name)]
    outside = [p for p in tracked if not area.in_lane(p, lane, name)]
    if outside:
        g(wt, "stash", "push", "-m", f"kickoff direct: {name} worker changes outside the lane", "--", *outside)
        say(f"stashed changes outside the {name} lane (not committed): {', '.join(outside)}")
    stray = [p for p in untracked if not area.in_lane(p, lane, name)]
    if stray:
        say(f"left untracked files outside the {name} lane alone: {', '.join(stray[:10])}")
    if inside:
        g(wt, "add", "-A", "--", *inside)
        g(wt, "commit", "-q", "-m", f"{name}: worker changes (kickoff direct build)")
        say(f"committed {len(inside)} file(s) the worker left in the {name} lane")


def run_gates(wt, cmds, say):
    for line in cmds:
        c, _, want = line.partition(" => ")
        r = subprocess.run(c, shell=True, cwd=wt, capture_output=True, text=True)
        out = r.stdout + r.stderr
        tail = out.strip().splitlines()[-1:] or [""]
        ok = r.returncode == 0 and (not want or want in out)
        say(f"gate `{c}` exit {r.returncode}{'' if ok else ' FAIL'} {tail[0][:160]}")
        if not ok:
            return c
    return None


def push(*refs):
    return g(area.ROOT, "push", "--atomic", area.REMOTE, *refs, check=False)


def main_at(ref):
    """Check out main at ref (origin/main) in the main clone. Only this module's own unpushed HANDOFF commits are
    dropped; any other local-only commit on main stops the run."""
    root = area.ROOT
    if not area.ref_exists("main"):
        g(root, "switch", "-q", "-c", "main", ref)
        return
    g(root, "switch", "-q", "main")
    if ref == "main":
        return
    extra = [x for x in g(root, "log", "--format=%s", "main", f"^{ref}").stdout.split("\n") if x]
    if any(not (x.startswith("HANDOFF: ") or x.startswith("Merge area/")) for x in extra):
        raise area.Refused(f"your local main has commits {ref} does not: {extra[:3]}. Push or drop them, then rerun.")
    g(root, "reset", "-q", "--hard", ref)


def worktree(name, ref):
    """.pipeline/direct/<name> on area/<name>: origin's branch, a local one, or new from ref; main merged in."""
    br, rb = f"area/{name}", f"{area.REMOTE}/area/{name}"
    wt = os.path.join(area.ROOT, ".pipeline", "direct", name)
    remote = area.has_remote() and area.ref_exists(rb)
    if area.ref_exists(br):
        if remote and g(area.ROOT, "merge-base", "--is-ancestor", br, rb, check=False).returncode == 0:
            g(area.ROOT, "branch", "-f", br, rb) if not os.path.isdir(wt) else None
        elif remote and g(area.ROOT, "merge-base", "--is-ancestor", rb, br, check=False).returncode != 0:
            raise area.Refused(f"your {br} and {rb} both have commits the other lacks: someone else also works on "
                               f"{name} (one person per area). Ask them, then merge by hand.")
    else:
        g(area.ROOT, "branch", "--no-track", br, rb if remote else ref)
    if not os.path.isdir(wt):
        g(area.ROOT, "worktree", "add", "-q", wt, br)
    else:
        if g(wt, "status", "--porcelain", "--untracked-files=no").stdout.strip():
            raise area.Refused(f"{wt} has uncommitted changes from an earlier run. Commit or discard them there first.")
        if remote:
            g(wt, "merge", "-q", "--ff-only", rb, check=False)
    return wt


def merge_in(wt, ref, what):
    r = g(wt, "merge", "--no-edit", ref, check=False)
    if r.returncode:
        files = g(wt, "diff", "--name-only", "--diff-filter=U", check=False).stdout.split()
        g(wt, "merge", "--abort", check=False)
        raise area.Refused(f"merging {what} conflicts in {', '.join(files) or r.stdout.strip()[:200]} (merge aborted)")


def merge_and_push(wt, name, lane, say):
    """Under LOCK: main into the area, the lane check, the area into main, one atomic push. Retries a rejected push."""
    br = f"area/{name}"
    for attempt in range(3):
        area.fetch()
        ref = area.base_ref()
        merge_in(wt, ref, f"main into {br}")
        stray = [p for p in g(area.ROOT, "diff", "--name-only", f"{ref}...{br}").stdout.split()
                 if not area.in_lane(p, lane, name)]
        if stray:
            raise area.Refused(f"{br} changes files outside its lane: {', '.join(stray)}. Not merged.")
        main_at(ref)
        r = g(area.ROOT, "merge", "--no-ff", "--no-edit", "-m", f"Merge {br}", br, check=False)
        if r.returncode:
            g(area.ROOT, "merge", "--abort", check=False)
            raise area.Refused(f"merging {br} into main conflicts:\n{r.stdout[:300]}")
        if not area.has_remote():
            return True
        if push("main", br).returncode == 0:
            say(f"merged into main and pushed main + {br}")
            return True
        say(f"push rejected (someone pushed first); merging again ({attempt + 1}/3)")
    return False


def set_row(text, name, status):
    head, rows, at = table(text)
    lines = text.splitlines()
    if name in rows:
        row = rows[name] + [""] * max(0, len(head) - len(rows[name]))
        row[col(head, "status")] = status
        who = col(head, "who")
        if who is not None:
            row[who] = "free"
        lines[at[name]] = "| " + " | ".join(row) + " |"
        return "\n".join(lines) + "\n"
    return text.rstrip("\n") + f"\n- {name}: {status}\n"


def update_handoff(name, status, say):
    """Under LOCK: HANDOFF.md's row on main, committed and pushed (rejected: fetch and redo)."""
    for _ in range(3):
        area.fetch()
        ref = area.base_ref()
        main_at(ref)
        text = area.show(ref, area.HANDOFF) or "# Handoff\n"
        with open(os.path.join(area.ROOT, area.HANDOFF), "w", encoding="utf-8", newline="\n") as fh:
            fh.write(set_row(text, name, status))
        g(area.ROOT, "add", area.HANDOFF)
        g(area.ROOT, "commit", "-q", "-m", f"HANDOFF: {name} {status}")
        if not area.has_remote() or push("main").returncode == 0:
            say(f"HANDOFF.md updated: {name} = {status}")
            return True
    say("could not push the HANDOFF.md update; it is committed on your local main")
    return False


def cap_jobs(cap):
    cpus = max(1, os.cpu_count() or 1)
    return max(1, min(cap, cpus)) if cap and cap > 0 else cpus


def job(name, ref, cmds, say):
    """One area, start to finish. -> True when merged."""
    with LOCK:
        wt = worktree(name, ref)
        merge_in(wt, ref, f"main into area/{name}")
        _, lane = area.brief_and_lane(name, ref)
    env = dict(os.environ, JAM_ROLE=WORKER_ROLE, JAM_CARD=f"area-{name}")
    say(f"worker ({WORKER_MODEL}) started in {wt}")
    code = subprocess.call(worker_argv(worker_prompt(name, lane)), cwd=wt, env=env,
                           stdout=subprocess.DEVNULL if os.environ.get("KICKOFF_QUIET_WORKERS") else None)
    say(f"worker exited {code}")
    commit_leftovers(wt, name, lane, say)
    bad = run_gates(wt, cmds, say)
    with LOCK:
        if bad:
            if area.has_remote():
                push(f"area/{name}")
            update_handoff(name, f"gates failed: {bad} (at {area.last_commit('area/' + name).split()[0]})", say)
            return False
        if not merge_and_push(wt, name, lane, say):
            return False
        sha = area.last_commit("main").split()[0]
        status = os.path.join(wt, area.BRIEFS, f"{name}-status.md")
        try:
            with open(status, encoding="utf-8") as fh:
                finished = DONE_MARK in fh.read()
        except OSError:
            finished = False
        update_handoff(name, f"done (merged {sha})" if finished else f"merged {sha}", say)
        return True


def run(dry_run=False, say=print, cap=0):
    say("kickoff: docs/build/MODE is direct: building from HANDOFF.md, area by area. No GitHub cards, issues or PRs.")
    try:
        area.require_clean()
        area.fetch()
        ref = area.base_ref()
        handoff = area.show(ref, area.HANDOFF)
        if handoff is None:
            say(f"kickoff: no {area.HANDOFF} on {ref}. The build lead writes it (or set docs/build/MODE to cards).")
            return 2
        go, skip = todo(handoff, area.areas(ref))
        for n, why in skip:
            say(f"kickoff: skip {n}: {why}")
        lanes = {n: area.brief_and_lane(n, ref)[1] for n in go}
        cmds = gates(ref)
        limit = cap_jobs(cap)
        say(f"kickoff: areas to build: {', '.join(go) or 'none'}; at most {limit} at once "
            f"({'--parallel/KICKOFF_PARALLEL cap' if cap else 'auto: one per CPU'}, no two with overlapping lanes); "
            f"gates: {' ; '.join(cmds) or 'none'}")
        if dry_run or not go:
            return 0
        if not os.environ.get("KICKOFF_AGENT_CMD") and not shutil.which("claude"):
            say("kickoff: the direct build needs Claude Code (claude). Install it, then run tools/kickoff.sh again.")
            return 2
        main_at(ref)
        area.install_guard()
        results, running, waiting = {}, {}, list(go)
        done_ev = threading.Condition()

        def say_for(n):
            def f(msg):
                with PRINT:
                    say(f"kickoff [{n}]: {msg}")
            return f

        def runner(n):
            try:
                results[n] = job(n, ref, cmds, say_for(n))
            except area.Refused as e:
                say_for(n)(f"stopped: {e}")
                results[n] = False
                try:   # the next person sees why in HANDOFF.md
                    with LOCK:
                        update_handoff(n, "stopped: " + str(e).split(". ")[0].replace("|", "/")[:140], say_for(n))
                except Exception as e2:
                    say_for(n)(f"HANDOFF.md not updated: {e2}")
            except Exception as e:   # never a silent idle
                say_for(n)(f"stopped on {type(e).__name__}: {str(e)[:200]}")
                results[n] = False
            with done_ev:
                running.pop(n, None)
                done_ev.notify_all()

        with done_ev:
            while waiting or running:
                for n in list(waiting):
                    if len(running) >= limit:
                        break
                    if any(area.lanes_overlap(lanes[n], lanes[r]) for r in running):
                        continue
                    waiting.remove(n)
                    running[n] = threading.Thread(target=runner, args=(n,), daemon=True)
                    with PRINT:
                        say(f"kickoff: START area {n} ({len(running)} running)")
                    running[n].start()
                done_ev.wait(timeout=5)
        failed = [n for n in go if not results.get(n)]
        say(f"\nkickoff: direct build finished. Merged: {', '.join(n for n in go if n not in failed) or 'none'}. "
            f"Not merged: {', '.join(failed) or 'none'}.")
        return 1 if failed else 0
    except area.Refused as e:
        say(f"kickoff: {e}")
        return 1
