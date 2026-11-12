#!/usr/bin/env python3
"""MCP servers for both agents: Claude Code and Codex. Stdlib only.

Sources: pipeline/agent-ops/mcp.template.json (Unreal editor, HTTP), pipeline/agent-ops/mcp.tools.template.json
(GIMP, Aseprite, Blender; Claude format) and pipeline/agent-ops/codex-mcp.template.toml (the same servers in Codex
`[mcp_servers.<name>]` format). Role scoping: the Unreal server goes to gates.json mcp_roles; each tool server to its
asset-tools.json `mcp` roles, which must sit inside mcp_roles. Everything is OFF while gates.json mcp_enabled is false
(the kickoff record turns it on, a needs-human checkpoint).

  check                              both formats name the same servers with the same url/command/args, every
                                     server has a components.csv row, tool-server roles are inside mcp_roles
  session --agent claude|codex --role R --out DIR
                                     prints the agent CLI arguments that load only R's servers (nothing while off):
                                     claude: --mcp-config <DIR>/mcp-<R>.json --strict-mcp-config
                                     codex:  -c mcp_servers.<name>.url=... / .command=... / .args=[...]
tools/kickoff.py calls `session` for every agent session; nothing is written to ~/.codex/config.toml or a committed
.mcp.json. Exit 0 = ok, 1 = problems, 2 = usage.
"""
import argparse
import csv
import json
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
OPS = os.path.join("pipeline", "agent-ops")
EDITOR_TPL = os.path.join(OPS, "mcp.template.json")
TOOLS_TPL = os.path.join(OPS, "mcp.tools.template.json")
CODEX_TPL = os.path.join(OPS, "codex-mcp.template.toml")


def load_json(root, rel):
    with open(os.path.join(root, rel), encoding="utf-8") as fh:
        return json.load(fh)


def parse_toml(text):
    """The subset the template uses: [mcp_servers.<name>] tables of string and string-list values."""
    try:
        import tomllib
        return tomllib.loads(text)
    except ImportError:  # Python < 3.11
        out, cur = {}, None
        for ln in text.splitlines():
            ln = ln.split("#", 1)[0].strip()
            m = re.fullmatch(r"\[mcp_servers\.([\w-]+)\]", ln)
            if m:
                cur = out.setdefault("mcp_servers", {}).setdefault(m.group(1), {})
            elif cur is not None and "=" in ln:
                k, v = (x.strip() for x in ln.split("=", 1))
                cur[k] = json.loads(v)
        return out


def claude_servers(root=ROOT):
    s = dict(load_json(root, EDITOR_TPL).get("mcpServers") or {})
    s.update(load_json(root, TOOLS_TPL).get("mcpServers") or {})
    return s


def codex_servers(root=ROOT):
    with open(os.path.join(root, CODEX_TPL), encoding="utf-8") as fh:
        return parse_toml(fh.read()).get("mcp_servers") or {}


def gates(root=ROOT):
    return load_json(root, os.path.join(OPS, "gates.json"))


def server_roles(root=ROOT):
    g = gates(root)
    roles = {"unreal-mcp": list(g.get("mcp_roles") or [])}
    for name in load_json(root, EDITOR_TPL).get("mcpServers") or {}:
        roles[name] = list(g.get("mcp_roles") or [])
    for m in load_json(root, os.path.join(OPS, "asset-tools.json")).get("mcp") or []:
        if "roles" in m:
            roles[m["id"]] = list(m["roles"])
    return roles


def problems(root=ROOT):
    out = []
    try:
        cl, cx = claude_servers(root), codex_servers(root)
    except (OSError, ValueError) as e:
        return [f"cannot read an MCP template: {e}"]
    if sorted(cl) != sorted(cx):
        out.append(f"{CODEX_TPL} names {sorted(cx)}; the Claude templates name {sorted(cl)}: keep both formats equal")
    for name in sorted(set(cl) & set(cx)):
        a, b = cl[name], cx[name]
        for k in ("url", "command", "args"):
            if (a.get(k) or None) != (b.get(k) or None) and not (k == "args" and not a.get(k) and not b.get(k)):
                out.append(f"{name}: {k} is {a.get(k)!r} in Claude format and {b.get(k)!r} in {CODEX_TPL}")
    try:
        with open(os.path.join(root, OPS, "components.csv"), encoding="utf-8") as fh:
            names = {r["name"] for r in csv.DictReader(ln for ln in fh if not ln.startswith("#"))}
    except OSError:
        names = set()
    for name in sorted(cl):
        if name not in names:
            out.append(f"{name}: no mcp-server row in {OPS}/components.csv")
    allowed = set(gates(root).get("mcp_roles") or [])
    for name, roles in server_roles(root).items():
        extra = sorted(set(roles) - allowed)
        if extra:
            out.append(f"{name}: roles {extra} are not in gates.json mcp_roles")
    return out


def session_args(agent, role, out_dir, root=ROOT):
    """CLI args that load only `role`'s servers, or [] while mcp_enabled is false."""
    if not gates(root).get("mcp_enabled"):
        return []
    roles = server_roles(root)
    if agent == "claude":
        mine = {n: s for n, s in claude_servers(root).items() if role in roles.get(n, [])}
        if not mine:
            return []
        os.makedirs(out_dir, exist_ok=True)
        path = os.path.join(out_dir, f"mcp-{role}.json")
        with open(path, "w", encoding="utf-8") as fh:
            json.dump({"mcpServers": mine}, fh, indent=2)
        return ["--mcp-config", path, "--strict-mcp-config"]
    args = []
    for name, s in sorted(codex_servers(root).items()):
        if role not in roles.get(name, []):
            continue
        for k in ("url", "command", "args"):
            if k in s:
                args += ["-c", f"mcp_servers.{name}.{k}={json.dumps(s[k])}"]
    return args


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)
    c = sub.add_parser("check")
    c.add_argument("--root", default=ROOT)
    s = sub.add_parser("session")
    s.add_argument("--agent", choices=("claude", "codex"), required=True)
    s.add_argument("--role", required=True)
    s.add_argument("--out", required=True)
    s.add_argument("--root", default=ROOT)
    a = ap.parse_args(argv)
    if a.cmd == "check":
        p = problems(a.root)
        for x in p:
            print("FAIL: " + x)
        print(f"mcp_config: {len(p)} problem(s)" if p else "PASS: MCP servers match in Claude and Codex format")
        return 1 if p else 0
    print(" ".join(session_args(a.agent, a.role, a.out, a.root)))
    return 0


if __name__ == "__main__":
    sys.exit(main())
