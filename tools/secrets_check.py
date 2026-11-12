#!/usr/bin/env python3
"""Secrets and agent-config guardrails. Stdlib only; runs locally and in CI.

Rules (owner: Agent Ops; human owner: the Technical Director human):
  secret      a tracked text file holds a key or token: AWS (AKIA...), GitHub (ghp_, gho_, ghs_, ghu_,
              github_pat_), OpenAI/Anthropic style (sk-...), Slack (xox?-), Google (AIza...), or a
              "BEGIN ... PRIVATE KEY" block
  secretfile  a tracked file that is a secret by its name: .env, .env.* (not .env.example), *.pem,
              *.key, *.p12, *.pfx, id_rsa*, id_ed25519*
  gitignore   .gitignore does not ignore .env, .env.local, x.pem and x.key
  settings    .claude/settings.json is missing or differs from pipeline/agent-ops/settings.json, or the
              template does not deny Edit on every gate path in pipeline/agent-ops/gates.json, or its
              PreToolUse guard matcher misses Edit, Write, Bash, PowerShell or editor MCP (mcp__*) tools, or
              it lacks a REQUIRED_DENY or REQUIRED_ASK rule (.env and key reads, ~/.ssh, ~/.aws, ~/.config/gh,
              curl, wget, web tools; push --force, gh pr merge, release, api), or sandbox.allowUnsandboxedCommands
              is not false, or sandbox.excludedCommands has more than 1 entry or one that is not the UBT path
              (the only sandbox exception allowed, by TD PR)
  mcp         .mcp.json lists a URL that is not loopback (127.0.0.1, localhost, ::1), a server with no
              vetted row in pipeline/agent-ops/components.csv, or a literal env/header value
              (it must be a ${VAR} reference)
  components  a components.csv row has vetted_by empty or TBD, or [VERIFY] in any cell; or a plugin
              enabled in the .uproject has no vetted engine-plugin row (that part skips while there is
              no .uproject). Lines starting with # in components.csv are notes. With --build-version FILE
              (Engine/Build/Build.version on the packaging machine), the engine row and each "built into"
              engine-plugin row must carry that Major.Minor.Patch version
  agents      a .claude/agents/<name>.md tools: line differs from pipeline/agent-ops/agent-tools.json,
              or a non-research agent lists a web tool, or a gates.json role has no .claude/agents/<role>.md,
              or agent-tools.json and gates.json list different roles

Usage: python3 tools/secrets_check.py [--root PATH] [--rules secret,mcp,...] [--paths FILE...]
       python3 tools/secrets_check.py --redact < text   (prints text with secrets replaced)
       python3 tools/secrets_check.py --text PATH... (rule secret on text outside git: exported PR bodies and
           comments, a prompt-log export, an unzipped package folder; "-" reads stdin. Before each gate)
       python3 tools/secrets_check.py --agent-stub ROLE  (prints the .claude/agents/ROLE.md that passes rule agents)
       python3 tools/secrets_check.py --install  (card 0.17, TD human only: copies the settings template to
           .claude/settings.json, writes one .claude/agents/<role>.md per gates.json role, then runs rules
           settings and agents; exit 0 only when both pass)
Exit 0 = clean, 1 = problems found.
"""
import argparse
import csv
import json
import os
import re
import subprocess
import sys
from urllib.parse import urlparse

SECRET_PATTERNS = [
    ("aws-access-key", re.compile(r"\b(?:AKIA|ASIA)[0-9A-Z]{16}\b")),
    ("github-token", re.compile(r"\b(?:ghp|gho|ghs|ghu|ghr)_[A-Za-z0-9]{30,}\b")),
    ("github-pat", re.compile(r"\bgithub_pat_[A-Za-z0-9_]{40,}\b")),
    ("api-key-sk", re.compile(r"\bsk-(?:ant-|proj-|live-)?[A-Za-z0-9_-]{20,}")),   # Anthropic, OpenAI, Stability
    ("elevenlabs-key", re.compile(r"\bsk_[0-9a-f]{40,}\b")),   # [VERIFY] the current ElevenLabs key shape
    ("slack-token", re.compile(r"\bxox[abposr]-[A-Za-z0-9-]{10,}")),
    ("google-api-key", re.compile(r"\bAIza[0-9A-Za-z_-]{35}\b")),
    ("private-key", re.compile(r"-----BEGIN (?:[A-Z]+ )*PRIVATE KEY-----")),
]
SECRET_NAME = re.compile(r"(^|/)(\.env(\.(?!example$)[^/]+)?|id_rsa[^/]*|id_ed25519[^/]*|[^/]+\.(pem|key|p12|pfx))$")
GITIGNORE_PROBES = [".env", ".env.local", "probe.pem", "probe.key"]
LOOPBACK = {"127.0.0.1", "localhost", "::1"}
VAR_REF = re.compile(r"^\$\{[A-Za-z_][A-Za-z0-9_]*(:-[^}]*)?\}$")
MAX_BYTES = 2 * 1024 * 1024
SETTINGS = ".claude/settings.json"
TEMPLATE = "pipeline/agent-ops/settings.json"
GATES = "pipeline/agent-ops/gates.json"
COMPONENTS = "pipeline/agent-ops/components.csv"
AGENT_TOOLS = "pipeline/agent-ops/agent-tools.json"
GUARDED_TOOLS = ["Edit", "Write", "MultiEdit", "NotebookEdit", "Bash", "PowerShell", "mcp__unreal__run_python"]
REQUIRED_DENY = ["Read(./.env)", "Read(./.env.*)", "Read(./**/*.key)", "Read(./**/*.pem)",
                 "Read(~/.ssh/**)", "Read(~/.aws/**)", "Read(~/.config/gh/**)",
                 "Bash(curl *)", "Bash(wget *)", "WebFetch", "WebSearch"]
REQUIRED_ASK = ["Bash(git push --force *)", "Bash(git push -f *)", "Bash(gh pr merge *)", "Bash(gh release *)", "Bash(gh api *)"]
MAX_SANDBOX_EXCLUDED = 1
UBT_COMMAND = re.compile(r"(UnrealBuildTool|Build\.(sh|bat|command))", re.I)
ALL_RULES = ["secret", "secretfile", "gitignore", "settings", "mcp", "components", "agents"]


def git_files(root):
    try:
        out = subprocess.run(["git", "ls-files", "-z"], cwd=root, capture_output=True, check=True).stdout
    except (subprocess.CalledProcessError, FileNotFoundError):
        return []
    return [p for p in out.decode().split("\0") if p]


def find_secrets(text):
    hits = []
    for n, line in enumerate(text.splitlines(), 1):
        for name, rx in SECRET_PATTERNS:
            if rx.search(line):
                hits.append((n, name))
    return hits


def redact(text):
    for name, rx in SECRET_PATTERNS:
        text = rx.sub(f"[REDACTED:{name}]", text)
    return text


def read_text(path):
    try:
        if os.path.getsize(path) > MAX_BYTES:
            return None
        with open(path, "rb") as fh:
            raw = fh.read()
    except OSError:
        return None
    if b"\0" in raw[:8192] or raw.startswith(b"version https://git-lfs"):
        return None
    return raw.decode("utf-8", errors="replace")


def check_secret(root, files):
    probs = []
    for f in files:
        text = read_text(os.path.join(root, f))
        if text is None:
            continue
        for n, name in find_secrets(text):
            probs.append(("secret", f"{f}:{n}", f"looks like a {name}; remove it, rotate it, and keep keys in your shell env"))
    return probs


def check_secretfile(files):
    return [("secretfile", f, "secret file is tracked; `git rm --cached` it and rotate what it held")
            for f in files if SECRET_NAME.search(f)]


def check_gitignore(root):
    probs = []
    for p in GITIGNORE_PROBES:
        r = subprocess.run(["git", "check-ignore", "-q", "--no-index", p], cwd=root, capture_output=True)
        if r.returncode != 0:
            probs.append(("gitignore", ".gitignore", f"does not ignore '{p}' (add .env, .env.*, !.env.example, *.pem, *.key)"))
    return probs


def load_json(root, rel):
    with open(os.path.join(root, rel), encoding="utf-8") as fh:
        return json.load(fh)


def _full(matcher, tool):
    try:
        return re.fullmatch(matcher, tool) is not None
    except re.error:
        return False


def check_settings(root):
    probs = []
    try:
        tpl = load_json(root, TEMPLATE)
        gates = load_json(root, GATES)
    except (OSError, ValueError) as e:
        return [("settings", TEMPLATE, f"cannot read template or gates: {e}")]
    deny = set(tpl.get("permissions", {}).get("deny", []))
    for g in gates.get("gate_paths", []):
        if f"Edit(./{g})" not in deny:
            probs.append(("settings", TEMPLATE, f"no deny rule Edit(./{g}) for gate path {g}"))
    for rule in REQUIRED_DENY:
        if rule not in deny:
            probs.append(("settings", TEMPLATE, f"permissions.deny lacks {rule}"))
    ask = set(tpl.get("permissions", {}).get("ask", []))
    for rule in REQUIRED_ASK:
        if rule not in ask:
            probs.append(("settings", TEMPLATE, f"permissions.ask lacks {rule}"))
    sb = tpl.get("sandbox", {})
    if sb.get("allowUnsandboxedCommands") is not False:
        probs.append(("settings", TEMPLATE, "sandbox.allowUnsandboxedCommands is not false"))
    excl = sb.get("excludedCommands") or []
    if len(excl) > MAX_SANDBOX_EXCLUDED:
        probs.append(("settings", TEMPLATE, f"sandbox.excludedCommands has {len(excl)} entries; at most {MAX_SANDBOX_EXCLUDED} (the UBT path)"))
    for c in excl:
        if not UBT_COMMAND.search(str(c)):
            probs.append(("settings", TEMPLATE, f"sandbox.excludedCommands entry '{c}' is not the UBT path; it is the only exception allowed"))
    if tpl.get("permissions", {}).get("disableBypassPermissionsMode") != "disable":
        probs.append(("settings", TEMPLATE, "permissions.disableBypassPermissionsMode is not \"disable\""))
    if not tpl.get("sandbox", {}).get("enabled"):
        probs.append(("settings", TEMPLATE, "sandbox.enabled is not true"))
    guard_matchers = [m.get("matcher", "") for m in tpl.get("hooks", {}).get("PreToolUse", [])
                      if any(re.search(r"agent-ops/hook\.py\"?\s+guard\b", h.get("command", "")) for h in m.get("hooks", []))]
    for tool in GUARDED_TOOLS:
        if not any(_full(mt, tool) for mt in guard_matchers):
            probs.append(("settings", TEMPLATE, f"PreToolUse guard matcher does not cover '{tool}'"))
    for ev, mode in (("PreToolUse", "guard"), ("PostToolUse", "log"), ("ConfigChange", "config")):
        cmds = [h.get("command", "") for m in tpl.get("hooks", {}).get(ev, []) for h in m.get("hooks", [])]
        if not any(re.search(r"agent-ops/hook\.py\"?\s+" + mode + r"\b", c) for c in cmds):
            probs.append(("settings", TEMPLATE, f"no {ev} hook running hook.py {mode}"))
    try:
        live = load_json(root, SETTINGS)
    except FileNotFoundError:
        return probs + [("settings", SETTINGS, f"missing; copy {TEMPLATE} to it (Day-0 card)")]
    except ValueError as e:
        return probs + [("settings", SETTINGS, f"not valid JSON ({e}); Claude Code would skip the whole file")]
    if live != tpl:
        probs.append(("settings", SETTINGS, f"differs from {TEMPLATE}; change the template by PR and copy it"))
    return probs


def component_rows(root):
    """(line number, row dict) for each data row; '#' lines are notes and skipped."""
    out = []
    try:
        with open(os.path.join(root, COMPONENTS), encoding="utf-8", newline="") as fh:
            lines = [(n, ln) for n, ln in enumerate(fh, 1) if not ln.lstrip().startswith("#") and ln.strip()]
    except OSError:
        return out
    reader = csv.DictReader([ln for _, ln in lines])
    for (n, _), r in zip(lines[1:], reader):
        out.append((n, r))
    return out


def load_components(root):
    return {(r.get("kind") or "", (r.get("name") or "").strip()): r for _, r in component_rows(root)}


def vetted(rows, kind, name):
    r = rows.get((kind, name))
    return bool(r and (r.get("vetted_by") or "").strip() not in ("", "TBD"))


def check_mcp(root):
    path = os.path.join(root, ".mcp.json")
    if not os.path.exists(path):
        return []
    try:
        cfg = load_json(root, ".mcp.json")
    except ValueError as e:
        return [("mcp", ".mcp.json", f"not valid JSON: {e}")]
    rows = load_components(root)
    probs = []
    for name, srv in (cfg.get("mcpServers") or {}).items():
        where = f".mcp.json:{name}"
        url = srv.get("url")
        if url:
            host = urlparse(url).hostname or ""
            if host not in LOOPBACK:
                probs.append(("mcp", where, f"url host '{host}' is not loopback; the editor MCP must bind 127.0.0.1"))
        if not vetted(rows, "mcp-server", name):
            probs.append(("mcp", where, f"no vetted mcp-server row '{name}' in {COMPONENTS}"))
        for key in ("env", "headers"):
            for k, v in (srv.get(key) or {}).items():
                if not VAR_REF.match(str(v)):
                    probs.append(("mcp", where, f"{key}.{k} is a literal value; use a ${{VAR}} reference"))
    return probs


def engine_version(path):
    """'5.8.4' from an Engine/Build/Build.version file."""
    with open(path, encoding="utf-8") as fh:
        v = json.load(fh)
    return f"{v['MajorVersion']}.{v['MinorVersion']}.{v['PatchVersion']}"


def check_components(root, files, build_version=None):
    probs = []
    if build_version:
        try:
            want = engine_version(build_version)
        except (OSError, ValueError, KeyError) as e:
            probs.append(("components", build_version, f"cannot read Build.version: {e}"))
            want = None
        for n, r in component_rows(root) if want else []:
            engine_row = r.get("kind") == "engine" or (r.get("kind") == "engine-plugin" and "built into" in (r.get("source") or ""))
            if engine_row and (r.get("version") or "").strip() != want:
                probs.append(("components", f"{COMPONENTS}:{n}", f"'{r.get('name')}' version '{(r.get('version') or '').strip()}' is not the installed engine {want}"))
    for n, r in component_rows(root):
        where = f"{COMPONENTS}:{n}"
        if (r.get("vetted_by") or "").strip() in ("", "TBD"):
            probs.append(("components", where, f"'{r.get('name')}' has vetted_by '{(r.get('vetted_by') or '').strip()}'; the TD human checks source, version and licence, then writes their name"))
        if any("[VERIFY" in (v or "") for v in r.values() if isinstance(v, str)):
            probs.append(("components", where, f"'{r.get('name')}' still has a [VERIFY] tag; replace it with the checked value"))
    uprojects = [f for f in files if f.endswith(".uproject") and "/" not in f]
    if not uprojects:
        return probs
    rows = load_components(root)
    for up in uprojects:
        try:
            data = load_json(root, up)
        except (OSError, ValueError) as e:
            probs.append(("components", up, f"cannot read: {e}"))
            continue
        for p in data.get("Plugins") or []:
            if p.get("Enabled") and not vetted(rows, "engine-plugin", p.get("Name", "")):
                probs.append(("components", up, f"plugin '{p.get('Name')}' has no vetted engine-plugin row in {COMPONENTS}"))
    return probs


def front_matter_tools(text):
    m = re.match(r"^---\n(.*?)\n---", text, re.S)
    if not m:
        return None
    t = re.search(r"^tools:\s*(.*)$", m.group(1), re.M)
    return t.group(1).strip() if t else None


def split_tools(s):
    return [x.strip() for x in (s or "").split(",") if x.strip()]


def check_agents(root):
    try:
        spec = load_json(root, AGENT_TOOLS)
    except (OSError, ValueError) as e:
        return [("agents", AGENT_TOOLS, f"cannot read: {e}")]
    adir = os.path.join(root, ".claude", "agents")
    web, research = set(spec.get("web_tools", [])), set(spec.get("research_agents", []))
    probs = []
    try:
        roles = set((load_json(root, GATES).get("roles") or {}))
    except (OSError, ValueError):
        roles = set()
    listed = set(spec.get("agents", {}))
    for r in sorted(roles - listed):
        probs.append(("agents", AGENT_TOOLS, f"role '{r}' from {GATES} has no tools line"))
    for r in sorted(listed - roles):
        probs.append(("agents", AGENT_TOOLS, f"'{r}' is not a role in {GATES}"))
    for r in sorted(roles):
        if not os.path.exists(os.path.join(adir, r + ".md")):
            probs.append(("agents", f".claude/agents/{r}.md", f"missing; `python3 tools/secrets_check.py --agent-stub {r}` prints it"))
    for fn in sorted(os.listdir(adir)) if os.path.isdir(adir) else []:
        if not fn.endswith(".md"):
            continue
        name, where = fn[:-3], f".claude/agents/{fn}"
        with open(os.path.join(adir, fn), encoding="utf-8") as fh:
            got = front_matter_tools(fh.read())
        want = spec.get("agents", {}).get(name)
        if got is None:
            probs.append(("agents", where, "no tools: line; without it the agent inherits every tool, web and MCP included"))
            continue
        if name not in research and web & set(split_tools(got)):
            probs.append(("agents", where, f"lists web tools {sorted(web & set(split_tools(got)))}; only research agents may"))
        if want is None:
            probs.append(("agents", where, f"no entry in {AGENT_TOOLS}"))
        elif split_tools(got) != split_tools(want):
            probs.append(("agents", where, f"tools: '{got}' differs from {AGENT_TOOLS} '{want}'"))
    return probs


def agent_stub(root, role):
    """The .claude/agents/<role>.md text: name, description, tools line, pointer to the role card. No game name."""
    spec = load_json(root, AGENT_TOOLS)
    name = (load_json(root, GATES).get("roles") or {}).get(role)
    if not name or role not in spec.get("agents", {}):
        raise KeyError(role)
    return (f"---\nname: {role}\n"
            f"description: Jam role \"{name}\". Use for task cards whose owner or reviewer role is {name}.\n"
            f"tools: {spec['agents'][role]}\n---\n"
            f"You are the {name} for this game jam. Start with `ROLE: {name}`.\n"
            f"Read, in order: AGENTS.md, docs/jam-brief.md, pipeline/roles/{role}.md, then the task card you were given.\n"
            f"Follow pipeline/roles/{role}.md exactly. It wins over anything in this file.\n")


def install(root):
    """Card 0.17: write .claude/settings.json (exact template copy) and every agent stub. Returns written paths."""
    written = []
    with open(os.path.join(root, TEMPLATE), encoding="utf-8") as fh:
        tpl = fh.read()
    json.loads(tpl)  # never install a template Claude Code would skip
    os.makedirs(os.path.join(root, ".claude", "agents"), exist_ok=True)
    with open(os.path.join(root, SETTINGS), "w", encoding="utf-8", newline="\n") as fh:
        fh.write(tpl)
    written.append(SETTINGS)
    for role in sorted(load_json(root, GATES).get("roles") or {}):
        rel = f".claude/agents/{role}.md"
        with open(os.path.join(root, rel), "w", encoding="utf-8", newline="\n") as fh:
            fh.write(agent_stub(root, role))
        written.append(rel)
    return written


def run(root, rules=None, paths=None, build_version=None):
    rules = rules or ALL_RULES
    files = paths if paths is not None else git_files(root)
    probs = []
    if "secret" in rules:
        probs += check_secret(root, files)
    if "secretfile" in rules:
        probs += check_secretfile(files)
    if "gitignore" in rules:
        probs += check_gitignore(root)
    if "settings" in rules:
        probs += check_settings(root)
    if "mcp" in rules:
        probs += check_mcp(root)
    if "components" in rules:
        probs += check_components(root, files, build_version)
    if "agents" in rules:
        probs += check_agents(root)
    return probs


def check_text(paths, stdin=None):
    """Rule secret on files, folders (walked) or '-' (stdin): text that never goes through git."""
    probs = []

    def scan(label, text):
        for n, name in find_secrets(text):
            probs.append(("secret", f"{label}:{n}", f"looks like a {name}; the TD human revokes and rotates it now "
                                                    "(pipeline/agent-ops/README.md), then delete the text"))
    for p in paths:
        if p == "-":
            scan("<stdin>", (stdin or sys.stdin).read())
        elif os.path.isdir(p):
            for d, _, names in os.walk(p):
                for n in sorted(names):
                    full = os.path.join(d, n)
                    text = read_text(full)
                    if text is not None:
                        scan(full, text)
        else:
            text = read_text(p)
            if text is None and not os.path.exists(p):
                probs.append(("secret", p, "path not found (nothing was checked)"))
            elif text is not None:
                scan(p, text)
    return probs


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--root", default=os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    ap.add_argument("--rules", help="comma list from: " + ",".join(ALL_RULES))
    ap.add_argument("--paths", nargs="*", help="check these repo-relative files instead of git ls-files")
    ap.add_argument("--redact", action="store_true", help="read stdin, print it with secrets replaced")
    ap.add_argument("--text", nargs="+", metavar="PATH", help="rule secret on files/folders outside git ('-' = stdin)")
    ap.add_argument("--agent-stub", metavar="ROLE", help="print the .claude/agents/ROLE.md stub and exit")
    ap.add_argument("--install", action="store_true", help="card 0.17: write .claude/settings.json and the agent stubs")
    ap.add_argument("--build-version", metavar="FILE", help="rule components: Engine/Build/Build.version to match")
    a = ap.parse_args(argv)
    if a.redact:
        sys.stdout.write(redact(sys.stdin.read()))
        return 0
    if a.text:
        probs = check_text(a.text)
        for kind, where, msg in probs:
            print(f"[{kind}] {where}: {msg}")
        print(f"secrets_check: {len(probs)} problem(s)")
        return 1 if probs else 0
    if a.agent_stub:
        try:
            sys.stdout.write(agent_stub(os.path.abspath(a.root), a.agent_stub))
        except KeyError:
            print(f"unknown role '{a.agent_stub}'", file=sys.stderr)
            return 2
        return 0
    if a.install:
        root = os.path.abspath(a.root)
        try:
            for rel in install(root):
                print(f"wrote {rel}")
        except (OSError, ValueError, KeyError) as e:
            print(f"install failed: {e}", file=sys.stderr)
            return 2
        a.rules = "settings,agents"
    rules = [r.strip() for r in a.rules.split(",")] if a.rules else None
    bad = [r for r in (rules or []) if r not in ALL_RULES]
    if bad:
        print(f"unknown rule(s): {bad}", file=sys.stderr)
        return 2
    probs = run(os.path.abspath(a.root), rules, a.paths, a.build_version)
    for kind, where, msg in probs:
        print(f"[{kind}] {where}: {msg}")
    print(f"secrets_check: {len(probs)} problem(s)")
    return 1 if probs else 0


if __name__ == "__main__":
    sys.exit(main())
