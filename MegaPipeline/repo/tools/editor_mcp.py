#!/usr/bin/env python3
"""Editor MCP config check (pipeline/agent-ops/editor-mcp.md). Stdlib only.

  check     pipeline/agent-ops/mcp.template.json is valid: an mcpServers map, each server type http on a loopback
            URL (127.0.0.1, localhost, ::1), no literal env or header values, and a row for it in
            pipeline/agent-ops/components.csv. gates.json: mcp_enabled is a bool, mcp_roles is exactly the editor
            roles (EDITOR_ROLES) and each is a gates.json role. agent-tools.json: no role outside mcp_roles lists an
            mcp__ tool. settings.json keeps enableAllProjectMcpServers false.
            Off (mcp_enabled false): no repo-root .mcp.json exists. On: .mcp.json exists, its mcpServers equal the
            template's, and editor-mcp.md has `Kickoff record: enabled by=<name> at=<ISO date-time> link=<url>`
            (the needs-human checkpoint).

Usage: python3 tools/editor_mcp.py check [--root PATH]
Exit 0 = pass, 1 = problems, 2 = unreadable input.
"""
import argparse
import json
import os
import re
import sys
from urllib.parse import urlparse

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TEMPLATE = "pipeline/agent-ops/mcp.template.json"
GATES = "pipeline/agent-ops/gates.json"
AGENT_TOOLS = "pipeline/agent-ops/agent-tools.json"
SETTINGS = "pipeline/agent-ops/settings.json"
COMPONENTS = "pipeline/agent-ops/components.csv"
DOC = "pipeline/agent-ops/editor-mcp.md"
MCP_JSON = ".mcp.json"
EDITOR_ROLES = {"level-designer", "integrator", "art-director", "asset-specialist", "ui-ux"}
LOOPBACK = {"127.0.0.1", "localhost", "::1"}
VAR_REF = re.compile(r"^\$\{[A-Z_][A-Z0-9_]*\}$")
KICKOFF = re.compile(r"^Kickoff record: enabled by=(?!TBD\b)\S+ at=\d{4}-\d{2}-\d{2}T\d{2}:\d{2}\S* link=https?://\S+",
                     re.M)


def load(root, rel):
    with open(os.path.join(root, rel), encoding="utf-8") as fh:
        return json.load(fh) if rel.endswith(".json") else fh.read()


def server_problems(cfg, where, component_names):
    servers = cfg.get("mcpServers") if isinstance(cfg, dict) else None
    if not isinstance(servers, dict) or not servers:
        return [f"{where}: no mcpServers map"]
    out = []
    for name, srv in servers.items():
        w = f"{where}:{name}"
        if not isinstance(srv, dict):
            out.append(f"{w}: not an object")
            continue
        if srv.get("type") != "http":
            out.append(f"{w}: type is {srv.get('type')!r}; the Unreal MCP server is HTTP only (U25)")
        host = urlparse(str(srv.get("url") or "")).hostname or ""
        if host not in LOOPBACK:
            out.append(f"{w}: url host {host!r} is not loopback; the editor MCP binds 127.0.0.1 only")
        if "command" in srv:
            out.append(f"{w}: a command server runs a process outside the editor; only the editor's HTTP server")
        for key in ("env", "headers"):
            for k, v in (srv.get(key) or {}).items():
                if not VAR_REF.match(str(v)):
                    out.append(f"{w}: {key}.{k} is a literal value; use a ${{VAR}} reference")
        if name not in component_names:
            out.append(f"{w}: no mcp-server row '{name}' in {COMPONENTS}")
    return out


def problems(root=ROOT):
    out = []
    tpl = load(root, TEMPLATE)
    gates = load(root, GATES)
    comps = {ln.split(",")[0] for ln in load(root, COMPONENTS).splitlines()
             if not ln.startswith("#") and ",mcp-server," in ln}
    out += server_problems(tpl, TEMPLATE, comps)
    enabled = gates.get("mcp_enabled")
    if not isinstance(enabled, bool):
        out.append(f"{GATES}: mcp_enabled must be true or false (off until kickoff)")
    roles = set(gates.get("mcp_roles") or [])
    if roles != EDITOR_ROLES:
        out.append(f"{GATES}: mcp_roles is {sorted(roles)}; must be exactly {sorted(EDITOR_ROLES)}")
    for r in sorted(roles - set(gates.get("roles") or {})):
        out.append(f"{GATES}: mcp_roles names '{r}', which is not a role")
    for role, line in sorted((load(root, AGENT_TOOLS).get("agents") or {}).items()):
        if "mcp__" in line and role not in roles:
            out.append(f"{AGENT_TOOLS}: '{role}' lists an editor MCP tool but is not in mcp_roles")
    if load(root, SETTINGS).get("enableAllProjectMcpServers") is not False:
        out.append(f"{SETTINGS}: enableAllProjectMcpServers must stay false (each server is approved by a human)")
    have = os.path.exists(os.path.join(root, MCP_JSON))
    if enabled is not True:
        if have:
            out.append(f"{MCP_JSON} exists while mcp_enabled is false: the editor MCP stays off until kickoff")
        return out
    if not have:
        out.append(f"mcp_enabled is true but there is no {MCP_JSON}")
    else:
        live = load(root, MCP_JSON)
        out += server_problems(live, MCP_JSON, comps)
        if live.get("mcpServers") != tpl.get("mcpServers"):
            out.append(f"{MCP_JSON} mcpServers differ from {TEMPLATE}: update the template in the same PR")
    if not KICKOFF.search(load(root, DOC)):
        out.append(f"mcp_enabled is true but {DOC} has no `Kickoff record: enabled by=<name> at=<ISO> link=<url>` "
                   "line (the needs-human checkpoint)")
    return out


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("cmd", choices=["check"])
    ap.add_argument("--root", default=ROOT)
    a = ap.parse_args(argv)
    try:
        p = problems(a.root)
    except (OSError, ValueError) as e:
        print(f"NOT RUN: {e}")
        return 2
    for x in p:
        print("FAIL: " + x)
    print(f"editor_mcp: {len(p)} problem(s)" if p else "PASS: editor MCP config (off until kickoff)" if not
          load(a.root, GATES).get("mcp_enabled") else "PASS: editor MCP config (enabled at kickoff)")
    return 1 if p else 0


if __name__ == "__main__":
    sys.exit(main())
