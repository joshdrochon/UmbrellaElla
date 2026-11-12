#!/usr/bin/env python3
"""Gate-path library and the gate-patch tool route. Stdlib only.

No git hook runs this (Josh, 12 Nov: the local pre-commit / pre-push gate guard is gone). An agent's gate-path
change (pipeline/agent-ops/gates.json `gate_paths`) is caught on the PR: tools/check_pr.py rule gate fails a PR that
changes a gate path unless the commit came through kickoff's tool route: on a card PR it reads the commits of the PR
head for the `GATE EDIT: by=kickoff` trailer apply --auto writes (never the PR body) and re-checks them, and kickoff's
merge gate runs the base branch's rule gate too. tools/kickoff.py, tools/check_pr.py and the lane
checks import gate_hits, auto_problems, apply_patch and with_gate_line from here.

  python3 tools/git_gate.py check PATH...                            (prints the gate paths among PATHs)
  python3 tools/git_gate.py apply UE-<id> [--by NAME] [--yes] [--no-pr] [--auto]
      Applies an agent's gate patch. Agents own the work: a session writes its gate-path change as
      $JAM_OUTBOX/gate.patch and kickoff keeps it in .pipeline/gate-patches/UE-<id>/. This shows the patch's files,
      asks once (y/N; --yes skips), applies it in the card's worktree, commits it through the human route (JAM_HUMAN),
      pushes the branch, writes `GATE EDIT: by=<name> <paths>` under Evidence in the card's PR (opening the PR from
      the session's pr.md if the card had none), and takes the needs-human label off the card. --no-pr: commit and
      push only, and print the GATE EDIT line to paste. An agent session (JAM_ROLE set) is always refused. check_pr
      fails a person's `by=<name>` commit on a card PR (an agent could forge it); it serves only a PR with no card.
      --auto (what kickoff runs; by=kickoff): no question, and the tools decide instead of a person. auto_problems
      refuses the patch unless every path is in the card's File lane, no path is a guardrail enforcer (GUARD_CORE),
      and no guardrail file is loosened (gates.json and .claude/settings*.json: nothing removed from a deny-type
      list, nothing added to an allow-type list, mcp_enabled and native_windows_shell never opened). check_pr.py rule
      gate re-runs the same check in CI on each commit with the `GATE EDIT: by=kickoff` trailer, and kickoff's merge gate runs the base
      branch's check_pr too, so a patch cannot weaken the checker that judges it.
Exit 0 = done (apply: applied), 1 = apply refused, or the patch does not apply, 2 = usage error.
"""
import json
import os
import re
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
GATES_REL = "pipeline/agent-ops/gates.json"
DEFAULT_AGENT_ENV = ("JAM_ROLE", "JAM_KICKOFF", "CLAUDECODE", "CODEX_SANDBOX", "CODEX_SANDBOX_NETWORK_DISABLED",
                     "CODEX_THREAD_ID")


def git(*args, cwd=None):
    r = subprocess.run(["git", *args], cwd=cwd, capture_output=True, text=True)
    return r.returncode, r.stdout


def glob_to_re(glob):
    """The same glob rules as pipeline/agent-ops/hook.py (** any depth, * one segment)."""
    out, i = "", 0
    while i < len(glob):
        if glob.startswith("**/", i):
            out, i = out + "(?:.*/)?", i + 3
        elif glob.startswith("**", i):
            out, i = out + ".*", i + 2
        elif glob[i] == "*":
            out, i = out + "[^/]*", i + 1
        elif glob[i] == "?":
            out, i = out + "[^/]", i + 1
        else:
            out, i = out + re.escape(glob[i]), i + 1
    return re.compile("^" + out + "$")


def gate_hits(paths, globs):
    rx = [(g, glob_to_re(g)) for g in globs]
    return sorted({p for p in paths for g, r in rx if r.match(p) or (g.endswith("/**") and p == g[:-3])})


def load_gates(cwd=None):
    """gates.json as committed at HEAD; the working tree only before the first commit."""
    rc, out = git("show", f"HEAD:{GATES_REL}", cwd=cwd)
    if rc != 0:
        rc2, top = git("rev-parse", "--show-toplevel", cwd=cwd)
        path = os.path.join(top.strip() if rc2 == 0 else ROOT, GATES_REL)
        with open(path, encoding="utf-8") as fh:
            out = fh.read()
    return json.loads(out)


def actor(env, gates):
    """('human', name) | ('agent', var) | ('unmarked', None)."""
    names = gates.get("agent_env") or DEFAULT_AGENT_ENV
    hit = next((v for v in names if (env.get(v) or "").strip()), None)
    if hit:
        return "agent", hit
    who = (env.get("JAM_HUMAN") or "").strip()
    return ("human", who) if who else ("unmarked", None)


GATE_PATCHES = os.path.join(".pipeline", "gate-patches")
EVIDENCE = re.compile(r"^##\s*Evidence\s*$", re.M)


def gh_argv():
    exe = os.environ.get("KICKOFF_GH") or "gh"
    return [sys.executable, exe] if exe.endswith(".py") else [exe]


def gh(*args, body=None, cwd=None):
    import tempfile
    args = list(args)
    tmp = None
    if body is not None:
        fd, tmp = tempfile.mkstemp(suffix=".md")
        with os.fdopen(fd, "w", encoding="utf-8") as fh:
            fh.write(body)
        args += ["--body-file", tmp]
    try:
        r = subprocess.run(gh_argv() + args, cwd=cwd, capture_output=True, text=True)
    finally:
        if tmp:
            os.remove(tmp)
    if r.returncode != 0:
        raise RuntimeError((r.stderr or r.stdout).strip()[-200:])
    return r.stdout


def with_gate_line(body, line):
    """The PR body with `line` under ## Evidence (the section check_pr.py rule gate reads)."""
    body = body or ""
    m = EVIDENCE.search(body)
    if not m:
        return body.rstrip() + "\n\n## Evidence\n" + line + "\n"
    return body[:m.end()] + "\n" + line + body[m.end():]


AUTO_BY = "kickoff"   # the GATE EDIT name of the tool route (git_gate.py apply --auto, run by tools/kickoff.py)
# The files that enforce the guardrails: never changed by the tool route (a person's own commit only).
GUARD_CORE = ("tools/git_gate.py", "tools/install_git_hooks.py", "tools/check_pr.py", "tools/kickoff.py",
              "tools/secrets_check.py", "pipeline/agent-ops/hook.py")
# Guardrail files whose content may only tighten through the tool route.
GUARD_JSON = ("pipeline/agent-ops/gates.json", ".claude/settings.json", ".claude/settings.local.json")
ALLOW_KEYS = {"allow", "mcp_roles", "mcp_allow"}   # lists where an addition opens something up
CLOSED = {"mcp_enabled": False, "native_windows_shell": "block"}   # values the tool route never opens


def in_lane(path, lanes):
    globs = [g + "**" if g.endswith("/") else g for g in lanes or []]
    return bool(gate_hits([path], globs))


def loosened(old, new, where=""):
    """What `new` opens up compared with `old` (both parsed JSON): removed deny-type list items or dict keys, added
    allow-type list items, a CLOSED value opened."""
    out = []
    if isinstance(old, dict):
        if not isinstance(new, dict):
            return [f"{where or 'the file'} is no longer an object"]
        for k, v in old.items():
            at = f"{where}.{k}" if where else k
            if k in CLOSED and v == CLOSED[k] and new.get(k) != v:
                out.append(f"{at} opened ({v!r} -> {new.get(k)!r})")
            elif k not in new and isinstance(v, (list, dict)):
                out.append(f"{at} removed")
            elif k in new:
                out += loosened(v, new[k], at)
        for k, v in new.items():
            if k not in old and k in ALLOW_KEYS and v:
                out.append(f"{where + '.' if where else ''}{k} added")
    elif isinstance(old, list):
        if not isinstance(new, list):
            return [f"{where} is no longer a list"]
        key = where.rsplit(".", 1)[-1]
        olds = [json.dumps(x, sort_keys=True) for x in old]
        news = [json.dumps(x, sort_keys=True) for x in new]
        if key in ALLOW_KEYS:
            more = [x for x in news if x not in olds]
            if more:
                out.append(f"{where} adds {', '.join(more[:3])}")
        else:
            gone = [x for x in olds if x not in news]
            if gone:
                out.append(f"{where} drops {', '.join(gone[:3])}")
    return out


def mcp_allow_ok(old, new):
    """gates.json mcp_allow may grow through the tool route (card 0.4a copies the real tool list) only with names
    that do not run code: none matches mcp_ask_words (the rule tools/editor_mcp.py check enforces)."""
    words = [w.lower() for w in (new.get("mcp_ask_words") or [])]
    added = [t for t in new.get("mcp_allow") or [] if t not in (old.get("mcp_allow") or [])]
    return [t for t in added if any(w in str(t).lower() for w in words)]


def auto_problems(paths, lanes, old_text, new_text):
    """Why the tool route refuses a gate change (empty = it may apply). paths: the changed gate paths; lanes: the
    card's File lane globs; old_text(path) / new_text(path): the file before and after (None = absent)."""
    out = []
    if not lanes:
        out.append("the card's File lane is unknown, so the gate paths cannot be checked against it")
    for p in paths:
        if p in GUARD_CORE:
            out.append(f"{p} enforces the guardrails: the tool route never changes it")
        elif lanes and not in_lane(p, lanes):
            out.append(f"{p} is outside the card's File lane ({', '.join(lanes[:4])})")
    for p in paths:
        if p not in GUARD_JSON:
            continue
        old, new = old_text(p), new_text(p)
        if old is None:
            continue   # a new guardrail file (card 0.17 installs .claude/): CI's secrets_check judges its content
        try:
            o, n = json.loads(old), json.loads(new or "null")
        except ValueError as e:
            out.append(f"{p} is not valid JSON after the patch ({e})")
            continue
        if p == GATES_REL and isinstance(o, dict) and isinstance(n, dict):
            bad = mcp_allow_ok(o, n)
            if bad:
                out.append(f"{p} mcp_allow adds tool(s) that run code ({', '.join(map(str, bad[:3]))})")
            o, n = dict(o, mcp_allow=[]), dict(n, mcp_allow=[])
        for why in loosened(o, n):
            out.append(f"{p}: {why} (a guardrail only tightens through the tool route)")
    return out


def show(sha, path, cwd):
    rc, out = git("show", f"{sha}:{path}", cwd=cwd)
    return out if rc == 0 else None


def patched(wt, patch, paths):
    """{path: text after the patch} for paths, from a throwaway index (the worktree is not touched)."""
    import tempfile
    fd, idx = tempfile.mkstemp(prefix="gate-index-")
    os.close(fd)
    os.remove(idx)
    env = dict(os.environ, GIT_INDEX_FILE=idx)
    try:
        subprocess.run(["git", "read-tree", "HEAD"], cwd=wt, env=env, capture_output=True, text=True)
        subprocess.run(["git", "apply", "--cached", patch], cwd=wt, env=env, capture_output=True, text=True)
        out = {}
        for p in paths:
            r = subprocess.run(["git", "show", f":{p}"], cwd=wt, env=env, capture_output=True, text=True)
            out[p] = r.stdout if r.returncode == 0 else None
        return out
    finally:
        if os.path.exists(idx):
            os.remove(idx)


def apply_patch(card, by, yes=False, no_pr=False, root=ROOT, env=None, ask=None, auto=False):
    """Apply a kept gate patch: as a person, or (auto, by=kickoff) through the tool checks (auto_problems).
    Returns (exit code, message lines)."""
    env = dict(os.environ if env is None else env)
    gates = load_gates(root)
    auto = auto or (by or "").strip().lower() == AUTO_BY
    if (env.get("JAM_ROLE") or "").strip():
        return 1, ["git_gate: BLOCKED: an agent session cannot apply a gate patch (JAM_ROLE is set). kickoff applies "
                   "it (--auto), or a person from a plain terminal."]
    if auto:
        by, yes = AUTO_BY, True
        env = {k: v for k, v in env.items() if k not in ("JAM_KICKOFF",)}
    kind, who = actor(dict(env, JAM_HUMAN=by or env.get("JAM_HUMAN", "")), gates)
    if kind == "agent":
        return 1, [f"git_gate: BLOCKED: an agent session cannot apply a gate patch ({who} is set). kickoff applies "
                   "it (--auto), or a person from a plain terminal."]
    name = (by or env.get("JAM_HUMAN") or "").strip()
    if not name or name.lower() in ("agent", "claude", "codex", "ai", "bot", "name", "tbd"):
        return 2, ["git_gate: say who you are: `python3 tools/git_gate.py apply " + card + " --by <your name>` "
                   "(the name the card names as Human, or the TD human's)"]
    cid = card if card.upper().startswith("UE-") else "UE-" + card
    d = os.path.join(root, GATE_PATCHES, cid)
    patch = os.path.join(d, "gate.patch")
    if not os.path.isfile(patch):
        return 2, [f"git_gate: no gate patch for {cid} ({os.path.relpath(patch, root)}); kickoff keeps one when a "
                   "session writes $JAM_OUTBOX/gate.patch"]
    try:
        with open(os.path.join(d, "meta.json"), encoding="utf-8") as fh:
            meta = json.load(fh)
    except (OSError, ValueError):
        meta = {}
    branch = meta.get("branch")
    wt = meta.get("worktree") or (os.path.join(root, ".pipeline", "worktrees", branch) if branch else None)
    if not wt or not os.path.isdir(wt):
        return 2, [f"git_gate: the card's worktree for {cid} is gone ({wt}); run tools/kickoff.sh once to recreate it"]
    rc, stat = git("apply", "--stat", patch, cwd=wt)
    chk = subprocess.run(["git", "apply", "--check", patch], cwd=wt, capture_output=True, text=True)
    rc, out = chk.returncode, chk.stdout + chk.stderr   # git apply says why on stderr
    if rc != 0:
        return 1, [f"git_gate: the {cid} gate patch does not apply on {branch}; the card goes back to its agent "
                   f"(comment on the card). git said: {out.strip()[-200:]}"]
    with open(patch, encoding="utf-8") as fh:
        text = fh.read()
    paths = sorted({a or b for a, b in re.findall(r"^\+\+\+ b/(\S+)|^diff --git a/\S+ b/(\S+)", text, re.M)})
    lines = [f"git_gate: {cid} gate patch on {branch}:", stat.rstrip()]
    if auto:
        before = {p: show("HEAD", p, wt) for p in paths if p in GUARD_JSON}
        after = patched(wt, patch, list(before)) if before else {}
        probs = auto_problems(paths, meta.get("lanes"), before.get, after.get)
        if probs:
            return 1, lines + ["git_gate: REFUSED (tool route): " + "; ".join(probs[:6])]
    if not yes:
        ask = ask or input
        print("\n".join(lines))
        try:
            answer = ask(f"Apply it as {name}? Type y and press Enter: ").strip().lower()
        except EOFError:
            answer = ""
        if answer not in ("y", "yes"):
            return 1, ["git_gate: not applied (no y). Comment on the card what to change; its agent redoes the patch."]
        lines = []
    human = {k: v for k, v in env.items() if k not in (gates.get("agent_env") or DEFAULT_AGENT_ENV)}
    human["JAM_HUMAN"] = name
    for step in (("apply", "--index", patch), ("commit", "-q", "-m",
                 f"{cid}: gate edit applied by {name} (tools/git_gate.py apply)\n\nGATE EDIT: by={name} {','.join(paths)}")):
        r = subprocess.run(["git", *step], cwd=wt, capture_output=True, text=True, env=human)
        if r.returncode != 0:
            return 1, lines + [f"git_gate: git {step[0]} failed: {(r.stderr or r.stdout).strip()[-200:]}"]
    gate_line = f"GATE EDIT: by={name} {','.join(paths)}"
    lines.append(f"git_gate: applied and committed as {name}: {gate_line}")
    if no_pr:
        lines.append("git_gate: --no-pr: push the branch and paste that line under Evidence in the card's PR")
        return 0, lines
    r = subprocess.run(["git", "push", "-q", "-u", "origin", branch], cwd=wt, capture_output=True, text=True, env=human)
    if r.returncode != 0:
        return 1, lines + [f"git_gate: push failed: {(r.stderr or r.stdout).strip()[-200:]}"]
    try:
        prs = json.loads(gh("pr", "list", "--state", "open", "--limit", "500", "--json", "number,headRefName,body",
                            cwd=root) or "[]")
        pr = next((p for p in prs if p.get("headRefName") == branch), None)
        if pr:
            gh("pr", "edit", str(pr["number"]), body=with_gate_line(pr.get("body"), gate_line), cwd=root)
            lines.append(f"git_gate: PR #{pr['number']} Evidence has the GATE EDIT line")
        else:
            try:
                with open(os.path.join(d, "pr.md"), encoding="utf-8") as fh:
                    body = fh.read()
            except OSError:
                body = f"## Task\nPart of #{meta.get('issue')}. Card ID: {cid}\n"
            title = re.sub(r"^\s*\[[^]]*\]\s*", "", meta.get("title") or "gate edit")
            out = gh("pr", "create", "--head", branch, "--base", "main", "--title", f"{cid}: {title}",
                     body=with_gate_line(body, gate_line), cwd=root)
            lines.append(f"git_gate: opened {out.strip().splitlines()[-1] if out.strip() else 'the PR'}")
        if meta.get("issue"):
            gh("issue", "edit", str(meta["issue"]), "--remove-label", "needs-human", cwd=root)
            gh("issue", "comment", str(meta["issue"]), body=f"Gate patch applied by {name} ({gate_line}); "
               "kickoff's next run reviews the PR.", cwd=root)
    except (RuntimeError, OSError, ValueError) as e:
        lines.append(f"git_gate: pushed; GitHub step not done ({e}). Paste `{gate_line}` under Evidence in the PR "
                     "and remove the card's needs-human label")
    return 0, lines


def main(argv=None, env=None):
    argv = sys.argv[1:] if argv is None else argv
    env = os.environ if env is None else env
    if argv and argv[0] == "apply":
        import argparse
        ap = argparse.ArgumentParser(prog="git_gate.py apply")
        ap.add_argument("card")
        ap.add_argument("--by")
        ap.add_argument("--yes", action="store_true")
        ap.add_argument("--no-pr", action="store_true")
        ap.add_argument("--auto", action="store_true", help="the tool route (kickoff): by=kickoff, the checks decide")
        a = ap.parse_args(argv[1:])
        rc, lines = apply_patch(a.card, a.by, a.yes, a.no_pr, env=env, auto=a.auto)
        print("\n".join(x for x in lines if x))
        return rc
    if not argv or argv[0] != "check":
        print(__doc__, file=sys.stderr)
        return 2
    try:
        gates = load_gates()
    except (OSError, ValueError) as e:
        print(f"git_gate: cannot read {GATES_REL}: {e}; blocked (fails closed)", file=sys.stderr)
        return 1
    for p in gate_hits(argv[1:], gates.get("gate_paths") or []):
        print(p)
    return 0


if __name__ == "__main__":
    sys.exit(main())
