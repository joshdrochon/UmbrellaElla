#!/usr/bin/env python3
"""Claude Code hooks for the jam. Stdlib only; runs on Mac and Windows.

Wired by pipeline/agent-ops/settings.json (copied to .claude/settings.json):
  guard   PreToolUse on Edit|Write|MultiEdit|NotebookEdit|Bash|PowerShell|mcp__.*.
          Exit 2 (blocks the call) when it writes a gate path from gates.json, a path the
          session's role may not touch (role_deny) or only kickoff writes (kickoff_only_paths: the art-loop
          pass records), runs a network command (curl, wget...), writes
          anything while the session has no known role, or calls an editor MCP tool not in mcp_allow.
          An MCP tool that runs editor Python or console commands gets permissionDecision "ask", and so do
          git push to main or with force, gh pr merge / release / api / repo settings, and a recursive or
          glob delete under Content/ or Source/ (gates.json ask_commands, protected_branches, delete_ask_paths).
          A shell command naming a credential folder (secret_read_paths: ~/.ssh, ~/.aws, ~/.config/gh) is blocked.
          Interpreter one-liners (python -c, perl -e, node -e, ruby -e): network modules are blocked, a gate path
          with a write call is blocked, a delete under delete_ask_paths asks. Every shell call on native Windows
          is blocked (gates.json native_windows_shell): no sandbox there.
          `git commit|push --no-verify` and `git -c core.hooksPath` are blocked (they skip tools/git_gate.py).
          In a practice repo (.pipeline-practice) every `butler` command is blocked.
          The role comes from JAM_ROLE (launch command) and the subagent type, never from transcript text.
  log     PostToolUse, PostToolUseFailure, UserPromptSubmit, Stop. Appends one JSON line to
          Saved/agent-log/<date>.jsonl: role, card, host, tool, args hash, timestamp; build result for
          tools/ue/build.*; prompt text on UserPromptSubmit; token totals on Stop.
  config  ConfigChange. Logs every change; exit 2 blocks project and local settings changes.

The Bash part of guard reads the command text, so it is a second net. The real Bash control is the
sandbox (settings.json "sandbox"), which also denies writes to every Edit(...) deny path.
Hook input fields used: tool_name, tool_input, cwd, session_id, transcript_path, prompt, source,
file_path, agent_type, tool_response, error. [VERIFY on 0.18: ConfigChange `source` values and agent_type]

Usage: python3 pipeline/agent-ops/hook.py guard|log|config   (hook JSON on stdin)
Exit 0 = allow, 2 = block (reason on stderr, which Claude Code shows the agent).
"""
import datetime
import hashlib
import json
import os
import re
import shlex
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
GATES_FILE = os.path.join(HERE, "gates.json")
WRITE_TOOLS = {"Edit", "Write", "MultiEdit", "NotebookEdit"}
SHELL_TOOLS = {"Bash", "PowerShell"}
SEPARATORS = re.compile(r"\|\||&&|[;|&\n]")
CARD_RE = re.compile(r"^ue-(\d+(?:\.\d+)?[a-z]?)-")
BLOCKED_CONFIG_SOURCES = {"project_settings", "local_settings"}
BUILD_RE = re.compile(r"(?:^|[\s/\\.])tools[/\\]ue[/\\]build\.(?:sh|ps1)\b")


def load_gates(path=GATES_FILE):
    with open(path, encoding="utf-8") as fh:
        return json.load(fh)


def glob_to_re(glob):
    out, i = "", 0
    while i < len(glob):
        if glob.startswith("**/", i):
            out += "(?:.*/)?"
            i += 3
        elif glob.startswith("**", i):
            out += ".*"
            i += 2
        elif glob[i] == "*":
            out += "[^/]*"
            i += 1
        elif glob[i] == "?":
            out += "[^/]"
            i += 1
        else:
            out += re.escape(glob[i])
            i += 1
    return re.compile("^" + out + "$")


def match_any(rel, globs):
    for g in globs:
        if glob_to_re(g).match(rel):
            return g
        if g.endswith("/**") and rel == g[:-3]:
            return g  # the directory itself (rm -rf tools)
    return None


def project_root(data):
    return os.path.realpath(os.environ.get("CLAUDE_PROJECT_DIR") or data.get("cwd") or os.getcwd())


def rel_path(path, root, cwd):
    """Repo-relative POSIX path, or None when it is outside the project."""
    if not path:
        return None
    path = os.path.expanduser(path.strip().strip("'\""))
    full = path if os.path.isabs(path) else os.path.join(cwd, path)
    full = os.path.normpath(full)
    parent = os.path.dirname(full)
    real = os.path.join(os.path.realpath(parent), os.path.basename(full)) if os.path.isdir(parent) else full
    for cand in (real, full):
        try:
            rel = os.path.relpath(cand, root)
        except ValueError:  # other drive on Windows
            continue
        if not rel.startswith(".."):
            return rel.replace(os.sep, "/") if rel != "." else ""
    return None


def norm_role(role):
    return re.sub(r"[\s/_]+", "-", (role or "").strip().lower()) or None


def role_key(name, gates):
    """The gates.json roles key for a JAM_ROLE value or subagent type ('UI and UX', 'UI/UX', 'ui-ux' -> 'ui-ux'), else None."""
    roles = gates.get("roles") or {}
    n = norm_role(name)
    if not n:
        return None
    if n in roles:
        return n
    for key, display in roles.items():
        if norm_role(display) == n:
            return key
    return None


def session_roles(data, gates):
    """Role keys for this call: JAM_ROLE from the launch command, plus the subagent type when there is one.
    Both apply, so a subagent never gets more than the session that started it. Text in the transcript
    (a `ROLE:` line) is not trusted: anyone can type it. Unknown values are dropped."""
    keys = []
    for raw in (os.environ.get("JAM_ROLE"), data.get("agent_type")):
        k = role_key(raw, gates)
        if k and k not in keys:
            keys.append(k)
    return keys


def session_role(data, gates, root=None):
    """Display name for logs: the roles joined with '+', or None."""
    roles = gates.get("roles") or {}
    keys = session_roles(data, gates)
    return "+".join(roles.get(k, k) for k in keys) or None


def host_label():
    """JAM_HOST from the launch command, else a short hash of the machine name (no personal names in the repo)."""
    h = os.environ.get("JAM_HOST")
    if h:
        return re.sub(r"[^A-Za-z0-9_-]", "-", h)[:32]
    import socket
    return "host-" + hashlib.sha256(socket.gethostname().encode()).hexdigest()[:6]


def current_branch(root):
    head = os.path.join(root, ".git", "HEAD")
    try:
        if os.path.isfile(os.path.join(root, ".git")):  # worktree: .git is a file "gitdir: X"
            with open(os.path.join(root, ".git"), encoding="utf-8") as fh:
                gitdir = fh.read().split(":", 1)[1].strip()
            head = os.path.join(gitdir if os.path.isabs(gitdir) else os.path.join(root, gitdir), "HEAD")
        with open(head, encoding="utf-8") as fh:
            ref = fh.read().strip()
        return ref.split("refs/heads/", 1)[1] if "refs/heads/" in ref else None
    except (OSError, IndexError):
        return None


def card_of(branch):
    m = CARD_RE.match(branch or "")
    return m.group(1) if m else None


# ---------- guard ----------

def tool_paths(tool, ti):
    if tool == "NotebookEdit":
        return [ti.get("notebook_path")]
    if tool == "MultiEdit" or tool in ("Edit", "Write"):
        return [ti.get("file_path")]
    return []


def split_words(segment):
    try:
        return shlex.split(segment, posix=True)
    except ValueError:
        return segment.split()


PREFIX_WORDS = ("sudo", "command", "exec", "env", "nohup", "time", "xargs", "then", "do", "else")


def segment_words(command):
    """Word lists, one per simple command, with env assignments and wrappers (sudo, env...) dropped."""
    for seg in SEPARATORS.split(command):
        words = split_words(seg)
        while words and (re.match(r"^[A-Za-z_][A-Za-z0-9_]*=", words[0]) or words[0] in PREFIX_WORDS):
            words = words[1:]
        if words:
            yield words


def cmd_name(word):
    cmd = os.path.basename(word).lower()
    return cmd[:-4] if cmd.endswith(".exe") else cmd


def shell_findings(command, gates):
    """Return (network_hits, write_targets) for a shell command string."""
    net = {c.lower() for c in gates.get("net_commands", [])}
    writers = {c.lower() for c in gates.get("write_commands", [])}
    net_hits, targets = [], []
    # Redirections anywhere: > file, >> file, >file
    for m in re.finditer(r"(?<![0-9&<])>>?\s*([^\s;|&<>]+)", command):
        if not m.group(1).startswith("&"):
            targets.append(m.group(1))
    for words in segment_words(command):
        cmd = cmd_name(words[0])
        args = [w for w in words[1:] if not w.startswith("-") and not w.startswith(">")]
        if cmd in net:
            net_hits.append(cmd)
        elif cmd in ("tee",):
            targets.extend(args)
        elif cmd == "cp" and args:
            targets.append(args[-1])
        elif cmd in writers:
            for a in args:
                targets.append(a.split("=", 1)[1] if cmd == "dd" and a.startswith("of=") else a)
        elif cmd in ("sed", "perl", "ruby") and any(w == "-i" or w.startswith("-i") or w == "--in-place" for w in words[1:]):
            targets.extend(args)
        elif cmd == "git" and len(words) > 1 and words[1] in ("checkout", "restore", "rm", "mv", "apply", "clean", "reset"):
            targets.extend(a for a in args[1:])
    for cmd, code in inline_codes(command):
        targets.extend(re.findall(r"open\(\s*['\"]([^'\"]+)['\"]\s*,\s*['\"][wax]", code))
        if NET_CODE.search(code):
            net_hits.append(f"{cmd} inline code that opens a network connection")
        if WRITE_CODE.search(code):
            targets.extend(m.group(0) for m in GATE_LIT.finditer(code))
    return net_hits, targets


# Interpreter one-liners (python -c, perl -e, node -e, ruby -e). The command text is all the hook sees,
# so it looks for network modules, gate paths with a write call, and deletes under delete_ask_paths.
INTERPRETERS = {"python": ("-c",), "python3": ("-c",), "py": ("-c",), "perl": ("-e", "-E"),
                "ruby": ("-e",), "node": ("-e", "--eval", "-p", "--print"), "deno": ("eval",), "bun": ("-e", "--eval")}
NET_CODE = re.compile(r"urllib|http\.client|requests|httpx|aiohttp|socket|ftplib|smtplib|LWP|HTTP::Tiny|IO::Socket|Net::"
                      r"|open-uri|Net::HTTP|fetch\(|require\(\s*['\"](?:node:)?(?:https?|net|tls|dgram)['\"]|https?://", re.I)
WRITE_CODE = re.compile(r"write|unlink|remove|rmtree|rmdir|rename|os\.replace|copy|move|truncate|chmod|mkdir|symlink", re.I)
DELETE_CODE = re.compile(r"unlink|remove|rmtree|rmdir|rm_rf|rm_r|\brmSync|\bdelete", re.I)
GATE_LIT = re.compile(r"(?<![\w/.-])(?:tools|tests|\.github|\.claude|evals|pipeline/roles|pipeline/agent-ops)/[^\s'\")]*"
                      r"|(?<![\w/.-])(?:AGENTS\.md|CLAUDE\.md|\.mcp\.json|\.gitignore|\.gitattributes)\b")


def inline_codes(command):
    """(interpreter, code) for each one-liner in the command. Split the whole command at once,
    so a ';' inside the quoted code does not cut it short."""
    try:
        words = shlex.split(command, posix=True)
    except ValueError:
        words = command.split()
    out = []
    for i, w in enumerate(words[:-2]):
        cmd = cmd_name(w.lstrip("(;&|"))
        flags = INTERPRETERS.get(re.sub(r"[\d.]+$", "", cmd) if cmd.startswith("python") else cmd)
        if not flags:
            continue
        for j in range(i + 1, len(words) - 1):
            if words[j] in flags:
                out.append((cmd, words[j + 1]))
                break
            if not words[j].startswith("-"):
                break
    return out


def inline_delete_ask(command, gates):
    """A reason to ask when an interpreter one-liner deletes under delete_ask_paths (perl -e 'unlink glob q(Content/*)')."""
    roots = [g[:-3] for g in gates.get("delete_ask_paths", []) if g.endswith("/**")]
    for cmd, code in inline_codes(command):
        if DELETE_CODE.search(code):
            hit = [r for r in roots if re.search(r"(?<![\w-])" + re.escape(r) + r"(?:[/\\'\")]|$)", code)]
            if hit:
                return (f"`{cmd}` inline code deletes under {', '.join(hit)}. "
                        "Deleting work needs a human (AGENTS.md section 4).")
    return None


def native_windows():
    """True on native Windows (not WSL). Claude Code's Bash sandbox runs on macOS, Linux and WSL only.
    AGENT_OPS_PLATFORM overrides sys.platform for the tests."""
    return (os.environ.get("AGENT_OPS_PLATFORM") or sys.platform) == "win32"


# ---------- ask: push, merge, repo settings, bulk deletes ----------

HOME_RE = (r"(?:~|\$\{?HOME\}?|\$env:USERPROFILE|%USERPROFILE%|/Users/[^/\s'\"]+|/home/[^/\s'\"]+"
           r"|[A-Za-z]:\\Users\\[^\\\s'\"]+)")
PUSH_FORCE_LONG = ("--force", "--force-with-lease", "--force-if-includes", "--mirror", "--delete", "--all", "--prune")
PS_DELETE = ("remove-item", "ri", "del", "erase", "rd")
GLOB_CHARS = re.compile(r"[*?\[]")


def secret_path_hits(command, gates):
    """Credential folders from gates.json secret_read_paths that the command names (~/.ssh, $HOME/.aws...)."""
    hits = []
    for p in gates.get("secret_read_paths", []):
        rest = p[2:] if p.startswith("~/") else p.lstrip("/")
        rx = HOME_RE + r"[\"']?[/\\]" + re.escape(rest).replace("/", r"[/\\]") + r"(?=[/\\\s\"';|&)]|$)"
        if re.search(rx, command, re.I):
            hits.append(p)
    return hits


def git_sub(words):
    """(subcommand, index) for a git command, skipping global options like -C dir."""
    i = 1
    while i < len(words) and words[i].startswith("-"):
        i += 2 if words[i] in ("-C", "-c", "--git-dir", "--work-tree", "--namespace") else 1
    return (words[i], i) if i < len(words) else (None, i)


def git_push_ask(args, protected, branch):
    pos, skip = [], False
    for a in args:
        if skip:
            skip = False
            continue
        if a.startswith("--"):
            if a.split("=", 1)[0] in PUSH_FORCE_LONG:
                return f"`git push {a}` forces, mirrors or deletes remote branches"
            skip = a in ("--repo", "--receive-pack", "--exec", "--push-option")
            continue
        if a.startswith("-") and len(a) > 1:
            if set(a[1:]) & set("fd"):
                return f"`git push {a}` forces or deletes"
            skip = a == "-o"
            continue
        pos.append(a)
    refspecs = pos[1:]
    if not refspecs:
        return f"`git push` while on '{branch}' pushes to a protected branch" if branch in protected else None
    for r in refspecs:
        if r.startswith("+"):
            return f"`git push {r}` force-pushes"
        src, colon, dst = r.partition(":")
        if colon and not src:
            return f"`git push {r}` deletes a remote branch"
        dest = (dst if colon else src)
        dest = dest[len("refs/heads/"):] if dest.startswith("refs/heads/") else dest
        if dest == "HEAD":
            dest = branch
        if dest in protected:
            return f"`git push` to '{dest}': never commit to main; kickoff merges the PR"
    return None


def delete_args(cmd, words):
    """Paths a recursive or glob delete names ([""] = the whole working tree), else None."""
    flags = [w for w in words[1:] if w.startswith("-")]
    args = [w for w in words[1:] if not w.startswith("-")]
    if cmd == "rm":
        rec = any(f in ("--recursive", "--dir") or (not f.startswith("--") and set(f[1:]) & set("rR")) for f in flags)
    elif cmd in PS_DELETE or cmd == "rmdir" and any(f.lower().startswith("-r") for f in flags):
        rec = any(f.lower().startswith("-r") for f in flags) or cmd in ("rd", "rmdir")
    elif cmd == "git":
        sub, i = git_sub(words)
        rest = words[i + 1:]
        rflags = [w for w in rest if w.startswith("-")]
        rargs = [w for w in rest if not w.startswith("-")]
        if sub == "rm":
            rec = any(f == "-r" or (not f.startswith("--") and "r" in f[1:]) for f in rflags)
            return rargs if (rec or any(GLOB_CHARS.search(a) for a in rargs)) else None
        if sub == "clean" and any(f == "--force" or (not f.startswith("--") and "f" in f[1:]) for f in rflags):
            return rargs or [""]
        return None
    else:
        return None
    return args if (rec or any(GLOB_CHARS.search(a) for a in args)) else None


def reaches(rel, globs):
    """True when deleting rel (a path or a glob) removes something under one of globs."""
    dirs = [g[:-3] for g in globs if g.endswith("/**")]
    if GLOB_CHARS.search(rel):
        lit = GLOB_CHARS.split(rel, 1)[0]
        litdir = lit.rsplit("/", 1)[0] if "/" in lit else ""
        if litdir and match_any(litdir, globs):
            return True
        rx = glob_to_re(rel)
        return any(rx.match(d) for d in dirs)
    return bool(match_any(rel, globs)) or any(rel == "" or d.startswith(rel.rstrip("/") + "/") for d in dirs)


def shell_ask(command, gates, root, cwd):
    """A reason a human must approve this shell command, or None."""
    protected = gates.get("protected_branches", [])
    asks = [e.split() for e in gates.get("ask_commands", [])]
    keep = gates.get("delete_ask_paths", [])
    for words in segment_words(command):
        cmd = cmd_name(words[0])
        if cmd == "gh":
            nonflag = [w for w in words[1:] if not w.startswith("-")]
            for e in asks:
                if e[0] == "gh" and nonflag[:len(e) - 1] == e[1:]:
                    return f"`{' '.join(e)}` merges, releases or changes the repo. A human runs or approves it (AGENTS.md section 7)."
        if cmd == "git":
            sub, i = git_sub(words)
            if sub == "push":
                why = git_push_ask(words[i + 1:], protected, current_branch(root))
                if why:
                    return why + ". A human approves it."
        targets = delete_args(cmd, words)
        for t in targets or []:
            rel = rel_path(t, root, cwd) if t else ""
            if rel is not None and reaches(rel, keep):
                return (f"`{' '.join(words[:4])}` deletes in bulk under {', '.join(keep)}. "
                        "Deleting work needs a human (AGENTS.md section 4).")
    return None


def practice_repo(root):
    """A committed .pipeline-practice marks a practice repo (tools/practice.py)."""
    return bool(root) and os.path.isfile(os.path.join(root, ".pipeline-practice"))


def human_only_hit(command, gates):
    """A gates.json human_only_commands entry (butler push) anywhere in the command text, inline code included.
    Official Rules 17: a human entrant submits, never an AI agent."""
    for e in gates.get("human_only_commands", []):
        parts = [re.escape(w) for w in e.split()]
        rx = r"(?<![\w-])" + parts[0] + r"(?:\.exe)?" + "".join(r"['\"]?[\s,]+['\"]?" + w for w in parts[1:]) + r"(?![\w-])"
        if re.search(rx, command, re.I):
            return e
    return None


def mcp_decision(tool, gates, keys=(), branch=None):
    """None = allow; ("ask", why) or ("block", why) for an editor MCP tool (name mcp__<server>__<tool>).
    Off until the team enables it at kickoff (mcp_enabled); only mcp_roles; only on a card branch (editor work goes
    through a card lane and a PR; pipeline/agent-ops/editor-mcp.md)."""
    if not tool.startswith("mcp__"):
        return None
    if gates.get("mcp_enabled") is not True:
        return ("block", f"'{tool}': the editor MCP is off (gates.json mcp_enabled false). The team turns it on at "
                         "kickoff, a needs-human checkpoint (pipeline/agent-ops/editor-mcp.md).")
    allowed = gates.get("mcp_roles") or []
    if keys and not all(k in allowed for k in keys):
        return ("block", f"'{tool}': role {'+'.join(keys)} has no editor MCP. Only {', '.join(allowed)} "
                         "(gates.json mcp_roles).")
    if not card_of(branch) or branch in gates.get("protected_branches", []):
        return ("block", f"'{tool}': editor work needs a card branch ue-<id>-<name> and a PR (branch is {branch!r}).")
    short = tool.split("__", 2)[-1].lower()
    words = [w.lower() for w in gates.get("mcp_ask_words", [])]
    if any(w in short for w in words):
        return ("ask", f"'{tool}' runs code or console commands as the editor process, outside the sandbox. "
                       "A human approves each call. One session drives an editor's MCP at a time.")
    if tool in gates.get("mcp_allow", []):
        return None
    return ("block", f"'{tool}' is not in gates.json mcp_allow (the tool list from card 0.4a). Ask the TD human to add it by PR.")


def guard(data, gates):
    """Return (block_reasons, ask_reason)."""
    tool = data.get("tool_name") or ""
    ti = data.get("tool_input") or {}
    root = project_root(data)
    cwd = data.get("cwd") or root
    keys = session_roles(data, gates)
    role = session_role(data, gates)
    role_globs = [g for k in keys for g in gates.get("role_deny", {}).get(k, [])]
    reasons = []
    ask = None
    unknown = ("No known role for this session. Start it with the launch command on the install card, "
               "e.g. `JAM_ROLE=gameplay-dev claude`. Known roles: " + ", ".join(sorted(gates.get("roles") or {})) + ".")

    def check(raw):
        rel = rel_path(raw, root, cwd)
        if rel is None:
            return
        g = match_any(rel, gates["gate_paths"])
        if g:
            reasons.append(f"'{rel}' is a gate file ({g}). Agents never edit gates during the jam; post the change on the card for the Technical Director human.")
            return
        g = match_any(rel, gates.get("kickoff_only_paths") or [])
        if g:
            reasons.append(f"'{rel}' is an art-loop pass record ({g}): only kickoff's art loop writes it "
                           "(tools/art_loop.py, blind critic panel). Loop the art; never write a record.")
            return
        if not keys:
            reasons.append(f"'{rel}': " + unknown)
            return
        g = match_any(rel, role_globs)
        if g:
            reasons.append(f"'{rel}' is outside the {role} lane ({g}).")

    if tool in WRITE_TOOLS:
        for p in tool_paths(tool, ti):
            check(p)
    elif tool in SHELL_TOOLS:
        command = ti.get("command") or ""
        if native_windows() and gates.get("native_windows_shell", "block") == "block":
            reasons.append("Native Windows has no Bash sandbox, so the hook would be the only wall. "
                           "Run agents in WSL, or build through a human on this machine (pipeline/agent-ops/README.md, Windows hosts).")
        hit = human_only_hit(command, gates)
        if hit:
            reasons.append(f"`{hit}` uploads or submits the jam entry. Official Rules 17: an entrant submits, never an AI "
                           "agent. The packaging and submission owner runs it by hand (pipeline/human-checkpoints.md).")
        if practice_repo(root) and re.search(r"(?<![\w-])butler(?:\.exe)?(?![\w-])", command, re.I):
            reasons.append("Practice repo (.pipeline-practice): every `butler` command is blocked; uploads happen only "
                           "from the team repo, by a human (tools/practice.py).")
        if re.search(r"(?<![\w-])git\b[^|;&\n]*\s(?:commit|push)\b[^|;&\n]*\s(?:--no-verify|-n)\b", command) or \
                re.search(r"(?<![\w-])git\b[^|;&\n]*-c\s+core\.hooksPath", command, re.I):
            reasons.append("`--no-verify` / `core.hooksPath` skips the git hooks that stop gate-path commits for every "
                           "agent (tools/git_gate.py). Commit normally.")
        net_hits, targets = shell_findings(command, gates)
        for n in net_hits:
            reasons.append(f"'{n}' is a network command. Build agents have no network tools; ask a human.")
        for p in secret_path_hits(command, gates):
            reasons.append(f"'{p}' holds credentials. Agents never read it (gates.json secret_read_paths).")
        for t in targets:
            check(t)
        if not reasons:
            ask = shell_ask(command, gates, root, cwd) or inline_delete_ask(command, gates)
    elif tool.startswith("mcp__"):
        if not keys:
            reasons.append(f"'{tool}': " + unknown)
        else:
            d = mcp_decision(tool, gates, keys, current_branch(root))
            if d and d[0] == "block":
                reasons.append(d[1])
            elif d:
                ask = d[1]
    return reasons, ask


# ---------- log ----------

def log_dir(root):
    return os.path.join(root, "Saved", "agent-log")


def append(root, rec):
    d = log_dir(root)
    os.makedirs(d, exist_ok=True)
    day = rec["ts"][:10]
    with open(os.path.join(d, day + ".jsonl"), "a", encoding="utf-8") as fh:
        fh.write(json.dumps(rec, sort_keys=True) + "\n")


def base_record(data, gates, root, event):
    branch = current_branch(root)
    return {
        "ts": datetime.datetime.now(datetime.timezone.utc).isoformat(timespec="seconds"),
        "event": event,
        "session": data.get("session_id"),
        "role": session_role(data, gates, root),
        "branch": branch,
        "card": card_of(branch),
        "host": host_label(),
    }


def args_hash(ti):
    return hashlib.sha256(json.dumps(ti, sort_keys=True, default=str).encode()).hexdigest()[:16]


def transcript_tokens(path):
    """Sum assistant usage in a Claude Code transcript (JSONL). [VERIFY on 0.18: usage field names]"""
    tot = {"input": 0, "output": 0, "cache_read": 0, "cache_write": 0}
    if not path or not os.path.exists(path):
        return tot
    seen = set()
    with open(path, encoding="utf-8", errors="replace") as fh:
        for line in fh:
            try:
                e = json.loads(line)
            except ValueError:
                continue
            msg = e.get("message") if isinstance(e, dict) else None
            u = msg.get("usage") if isinstance(msg, dict) else None
            if not isinstance(u, dict):
                continue
            mid = msg.get("id") or e.get("uuid")
            if mid in seen:
                continue
            seen.add(mid)
            tot["input"] += int(u.get("input_tokens") or 0)
            tot["output"] += int(u.get("output_tokens") or 0)
            tot["cache_read"] += int(u.get("cache_read_input_tokens") or 0)
            tot["cache_write"] += int(u.get("cache_creation_input_tokens") or 0)
    return tot


def do_log(data, gates):
    root = project_root(data)
    ev = data.get("hook_event_name") or ("UserPromptSubmit" if "prompt" in data else "PostToolUse")
    if ev == "UserPromptSubmit":
        rec = base_record(data, gates, root, "prompt")
        text = data.get("prompt") or ""
        rec.update(prompt=text, prompt_sha256=hashlib.sha256(text.encode()).hexdigest()[:16])
    elif ev in ("Stop", "SubagentStop"):
        rec = base_record(data, gates, root, "stop")
        rec["tokens"] = transcript_tokens(data.get("transcript_path"))
    else:
        rec = base_record(data, gates, root, "tool")
        rec.update(tool=data.get("tool_name"), args_sha256=args_hash(data.get("tool_input") or {}))
        build = build_result(data, ev)
        if build:
            rec.update(build)
    append(root, rec)
    return 0


def build_result(data, ev):
    """For a tools/ue/build.* shell call: {"build": True, "build_ok": bool, "error_sha256": hash of the last
    error lines}. PostToolUseFailure means it failed; otherwise an exit code field in tool_response decides.
    [VERIFY on 0.18: a nonzero Bash exit fires PostToolUseFailure, or which
    tool_response field carries the exit code]"""
    if data.get("tool_name") not in SHELL_TOOLS:
        return None
    if not BUILD_RE.search((data.get("tool_input") or {}).get("command") or ""):
        return None
    resp = data.get("tool_response")
    resp = resp if isinstance(resp, dict) else {"stdout": str(resp or "")}
    code = next((resp[k] for k in ("exit_code", "exitCode", "returncode", "code") if isinstance(resp.get(k), int)), None)
    ok = not (ev == "PostToolUseFailure" or resp.get("interrupted") or (code not in (None, 0)) or data.get("error"))
    err = str(data.get("error") or resp.get("stderr") or resp.get("stdout") or "")
    lines = [ln for ln in err.splitlines() if re.search(r"error|fail", ln, re.I)][-3:]
    sig = re.sub(r"\d+", "N", "\n".join(lines))  # line numbers and times do not make it a new failure
    return {"build": True, "build_ok": bool(ok), "error_sha256": None if ok else hashlib.sha256(sig.encode()).hexdigest()[:16]}


def main(argv):
    mode = argv[1] if len(argv) > 1 else ""
    try:
        data = json.load(sys.stdin)
    except ValueError:
        data = {}
    gates = load_gates(os.environ.get("AGENT_OPS_GATES") or GATES_FILE)
    root = project_root(data)
    if mode == "guard":
        reasons, ask = guard(data, gates)
        if ask and not reasons:
            rec = base_record(data, gates, root, "ask")
            rec.update(tool=data.get("tool_name"), args_sha256=args_hash(data.get("tool_input") or {}), reason=ask,
                       command=(data.get("tool_input") or {}).get("command"))
            try:
                append(root, rec)
            except OSError:
                pass
            print(json.dumps({"hookSpecificOutput": {"hookEventName": "PreToolUse", "permissionDecision": "ask",
                                                     "permissionDecisionReason": ask}}))
            return 0
        if reasons:
            rec = base_record(data, gates, root, "blocked")
            rec.update(tool=data.get("tool_name"), args_sha256=args_hash(data.get("tool_input") or {}), reason=reasons[0],
                       command=(data.get("tool_input") or {}).get("command") or (data.get("tool_input") or {}).get("file_path"))
            try:
                append(root, rec)
            except OSError:
                pass
            print("BLOCKED by pipeline/agent-ops/hook.py: " + " ".join(reasons), file=sys.stderr)
            return 2
        return 0
    if mode == "log":
        try:
            return do_log(data, gates)
        except OSError as e:
            print(f"agent-log write failed: {e}", file=sys.stderr)
            return 1
    if mode == "config":
        rec = base_record(data, gates, root, "config")
        src = data.get("source")
        rec.update(source=src, file_path=data.get("file_path"))
        block = src in BLOCKED_CONFIG_SOURCES
        rec["blocked"] = block
        try:
            append(root, rec)
        except OSError:
            pass
        if block:
            print(f"BLOCKED: {src} changed mid-session ({data.get('file_path')}). Settings change only by a reviewed PR; restart the session after it merges.", file=sys.stderr)
            return 2
        return 0
    print(__doc__, file=sys.stderr)
    return 1


if __name__ == "__main__":
    sys.exit(main(sys.argv))
