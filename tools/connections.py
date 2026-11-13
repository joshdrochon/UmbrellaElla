#!/usr/bin/env python3
"""Connection check: everything the pipeline needs, probed for real (a command run, a login asked, a version read).
Stdlib only. `tools/kickoff.sh --check` runs it, and kickoff runs it first and refuses to start while a required
item is missing.

One line per item:
  CONNECTED <name> (<how verified>)
  NOT CONNECTED <name> -> <exact one-line fix>          ("(required)" when kickoff cannot start without it)
  SKIPPED <name> (<why>)
and a summary: `N connected, M still need connecting`.

Items: Python; the agent CLIs (`claude --version`, `claude auth status`, `codex --version`, `codex login status`);
GitHub (`gh auth status`, push access from `gh repo view --json viewerPermission`), git-lfs, the git hooks
(tools/install_git_hooks.py --check); Unreal Engine 5.8.4 (UE_ROOT, Engine/Build/Build.version); the MCP servers
(Unreal, GIMP, Aseprite, Blender: both config formats valid, and each server answers an MCP initialize when
gates.json mcp_enabled is on); GIMP, GimpCLI, the Aseprite CLI, Blender headless; ffmpeg, sox, obs-websocket
(obs-cmd), 7-Zip or the Python zip step; butler (`butler version`, `butler status $BUTLER_TARGET` for the login);
the API keys (tools/keys.py: env or keychain; presence only, and a free auth request with --live); the Windows
packaging host (PowerShell and vswhere, on Windows only).

Required: Python, git, GitHub login and push access, the git hooks, git-lfs when the repo uses LFS, the chosen
agent's CLI and login; plus by role: Unreal for roles that build (gameplay-dev, technical-director, integrator,
qa-build), ffmpeg for qa-build (the video). Every other item has a fallback (assetgen.py) or is a human's tool.
Secrets are never printed: a key line says present/missing and where it was found, never the value.

  python3 tools/connections.py [--agent claude|codex] [--role R] [--live] [--out FILE] [--no-journal]
Exit 0 = every required item connected, 1 = a required item is missing.
Test seam: CONNECTIONS_HTTP_STUB=<file.py> defines get(url, headers) -> status code, in place of the network.
"""
import argparse
import importlib.util
import io
import json
import os
import platform
import re
import shutil
import subprocess
import sys
import zipfile

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, HERE)
import keys  # noqa: E402

BUILD_ROLES = {"gameplay-dev", "technical-director", "integrator", "qa-build"}
ENGINE = "5.8.4"
UE_DEFAULTS = ("/Users/Shared/Epic Games/UE_5.8", r"C:\Program Files\Epic Games\UE_5.8")
PING = {"ELEVENLABS_API_KEY": ("https://api.elevenlabs.io/v1/user", lambda k: {"xi-api-key": k}),
        "STABILITY_API_KEY": ("https://api.stability.ai/v1/user/account", lambda k: {"Authorization": f"Bearer {k}"})}


def sh(argv, timeout=20, cwd=None, stdin=None):
    """(exit code, output) or (None, why) when the program is missing."""
    exe = shutil.which(argv[0])
    if not exe:
        return None, f"`{argv[0]}` not on PATH"
    try:
        p = subprocess.run([exe, *argv[1:]], capture_output=True, text=True, timeout=timeout, cwd=cwd, input=stdin)
    except subprocess.TimeoutExpired:
        return None, f"`{argv[0]}` timed out after {timeout} s"
    except OSError as e:
        return None, str(e)
    return p.returncode, (p.stdout + p.stderr).strip()


def first(text):
    return (text or "").strip().splitlines()[0][:80] if (text or "").strip() else ""


class Result:
    def __init__(self, name, state, detail, required=False):
        self.name, self.state, self.detail, self.required = name, state, detail, required

    def line(self):
        if self.state == "CONNECTED":
            return f"CONNECTED {self.name} ({self.detail})"
        if self.state == "SKIPPED":
            return f"SKIPPED {self.name} ({self.detail})"
        return f"NOT CONNECTED {self.name} -> {self.detail}" + (" (required)" if self.required else "")


def ok(name, how):
    return Result(name, "CONNECTED", how)


def missing(name, fix):
    return Result(name, "NOT CONNECTED", fix)


def skipped(name, why):
    return Result(name, "SKIPPED", why)


def version_probe(name, argv, fix, pattern=None):
    rc, out = sh(argv)
    if rc == 0 and (pattern is None or re.search(pattern, out)):
        return ok(name, f"`{' '.join(argv)}`: {first(out)}")
    return missing(name, fix if rc is None else f"`{' '.join(argv)}` exited {rc}: {first(out)}; {fix}")


# ---------- probes ----------
def p_python():
    v = sys.version_info
    if v >= (3, 9):
        return ok("Python", f"python {v.major}.{v.minor}.{v.micro}")
    return missing("Python", "install Python 3.9 or newer (python.org) and put python3 on PATH")


def p_claude(agent):
    out = [version_probe("Claude Code CLI", ["claude", "--version"],
                         "install Claude Code: npm install -g @anthropic-ai/claude-code")]
    rc, text = sh(["claude", "auth", "status"])
    if rc == 0 and not re.search(r"not (logged|signed) in|logged out", text, re.I):
        out.append(ok("Claude Code login", "`claude auth status`"))
    else:
        out.append(missing("Claude Code login", "run `claude auth login`"))
    return out


def p_codex(agent):
    out = [version_probe("Codex CLI", ["codex", "--version"], "install Codex: brew install --cask codex "
                                                              "(Windows: npm install -g @openai/codex)")]
    rc, text = sh(["codex", "login", "status"])
    if rc == 0 and not re.search(r"not logged in|logged out", text, re.I):
        out.append(ok("Codex login", "`codex login status`: " + first(text)))
    else:
        out.append(missing("Codex login", "run `codex login`"))
    return out


def gh_cmd():
    return os.environ.get("KICKOFF_GH") or "gh"


def p_github(root):
    out = []
    g = gh_cmd()
    argv = [sys.executable, g] if g.endswith(".py") else [shutil.which(g) or g]
    rc, text = _run(argv + ["auth", "status"])
    out.append(ok("GitHub login", "`gh auth status`") if rc == 0 else
               missing("GitHub login", "install gh (cli.github.com) and run `gh auth login`"))
    rc, text = _run(argv + ["repo", "view", "--json", "viewerPermission"])
    perm = ""
    if rc == 0:
        try:
            perm = json.loads(text).get("viewerPermission", "")
        except ValueError:
            perm = ""
    out.append(ok("GitHub push access", f"viewerPermission={perm}") if perm in ("WRITE", "MAINTAIN", "ADMIN") else
               missing("GitHub push access", "ask the repo owner for write access (Settings > Collaborators)"))
    uses_lfs = False
    try:
        with open(os.path.join(root, ".gitattributes"), encoding="utf-8") as fh:
            uses_lfs = "filter=lfs" in fh.read()
    except OSError:
        pass
    r = version_probe("git-lfs", ["git", "lfs", "version"], "install Git LFS (git-lfs.com) then `git lfs install`")
    r.required = uses_lfs
    out.append(r)
    rc, text = _run([sys.executable, os.path.join(HERE, "install_git_hooks.py"), "--repo", root, "--check"])
    out.append(ok("git hooks (journal, LFS)", "install_git_hooks.py --check") if rc == 0 else
               missing("git hooks (journal, LFS)", "run `python3 tools/install_git_hooks.py`"))
    return out


def _run(argv):
    try:
        p = subprocess.run(argv, capture_output=True, text=True, timeout=30)
        return p.returncode, (p.stdout + p.stderr).strip()
    except (OSError, subprocess.SubprocessError) as e:
        return None, str(e)


def p_unreal():
    roots = [os.environ["UE_ROOT"]] if os.environ.get("UE_ROOT") else list(UE_DEFAULTS)
    for r in roots:
        try:
            with open(os.path.join(r, "Engine", "Build", "Build.version"), encoding="utf-8") as fh:
                v = json.load(fh)
        except (OSError, ValueError):
            continue
        ver = f"{v.get('MajorVersion')}.{v.get('MinorVersion')}.{v.get('PatchVersion')}"
        if ver == ENGINE:
            return ok(f"Unreal Engine {ENGINE}", f"{r}, Build.version {ver}")
        return missing(f"Unreal Engine {ENGINE}", f"{r} is {ver}; install {ENGINE} from the Epic launcher and set UE_ROOT")
    return missing(f"Unreal Engine {ENGINE}", f"install {ENGINE} from the Epic launcher and set UE_ROOT=<engine folder>")


def mcp_initialize_stdio(argv, timeout=5):
    req = json.dumps({"jsonrpc": "2.0", "id": 1, "method": "initialize",
                      "params": {"protocolVersion": "2025-06-18", "capabilities": {},
                                 "clientInfo": {"name": "connections", "version": "1"}}}) + "\n"
    rc, out = sh(argv, timeout=timeout, stdin=req)
    if rc is None:
        return False, out
    return '"result"' in out, first(out)


def http_get(url, headers):
    stub = os.environ.get("CONNECTIONS_HTTP_STUB")
    if stub:
        spec = importlib.util.spec_from_file_location("connections_http_stub", stub)
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)
        return mod.get(url, headers)
    import urllib.error
    import urllib.request
    try:
        with urllib.request.urlopen(urllib.request.Request(url, headers=headers), timeout=15) as r:  # noqa: S310
            return r.status
    except urllib.error.HTTPError as e:
        return e.code
    except OSError:
        return None


def p_mcp(root):
    import mcp_config
    if not os.path.isdir(os.path.join(root, "pipeline", "agent-ops")):
        root = ROOT   # --root names a bare git checkout (tests); the MCP config is the pipeline's own
    out = []
    probs = mcp_config.problems(root)
    fmt = "MCP config (Claude .mcp.json + Codex [mcp_servers] formats)"
    out.append(ok(fmt, "tools/mcp_config.py check: both formats agree") if not probs else
               missing(fmt, probs[0]))
    on = bool(mcp_config.gates(root).get("mcp_enabled"))
    servers = mcp_config.claude_servers(root) if not probs else {}
    for name in ("unreal-mcp", "gimp-mcp", "aseprite-mcp", "blender-mcp"):
        if not on:
            out.append(skipped(f"MCP server {name}", "off until kickoff: gates.json mcp_enabled is false"))
            continue
        s = servers.get(name) or {}
        if s.get("url"):
            st = http_get(s["url"], {"Accept": "application/json"})
            out.append(ok(f"MCP server {name}", f"{s['url']} answered HTTP {st}") if st else
                       missing(f"MCP server {name}", "start the editor and run ModelContextProtocol.StartServer"))
        else:
            good, why = mcp_initialize_stdio([s.get("command", name), *(s.get("args") or [])])
            out.append(ok(f"MCP server {name}", "answered MCP initialize") if good else
                       missing(f"MCP server {name}", f"install `{s.get('command', name)}` and put it on PATH ({why})"))
    return out


def p_tools():
    import assetgen
    spec = [("gimp", "GIMP 3", ["--version"], "install GIMP 3 (gimp.org); put gimp-console on PATH or set GIMP"),
            ("gimpcli", "GimpCLI", ["--version"], "install the team's GimpCLI and set GIMPCLI=<path>"),
            ("aseprite", "Aseprite CLI", ["--version"], "install Aseprite; set ASEPRITE=<path to aseprite>"),
            ("blender", "Blender headless", ["-b", "--version"], "install Blender (blender.org; the art generator, "
             "pipeline/art/blender/; without it art is a labelled placeholder that never ships); set BLENDER=<path>"),
            ("ffmpeg", "ffmpeg", ["-version"], "brew install ffmpeg (Windows: winget install Gyan.FFmpeg)"),
            ("sox", "sox", ["--version"], "brew install sox (Windows: winget install ChrisBagwell.SoX)"),
            ("obs", "obs-websocket (obs-cmd)", ["info"], "install OBS 28+ (obs-websocket built in) and obs-cmd; "
                                                       "set OBS_CMD=<path>")]
    out = []
    for tid, name, args, fix in spec:
        try:
            argv = assetgen.command(tid) + args
        except assetgen.ToolMissing:
            out.append(missing(name, fix))
            continue
        rc, text = _run(argv)
        out.append(ok(name, f"`{os.path.basename(argv[0])} {' '.join(args)}`: {first(text)}") if rc == 0 else
                   missing(name, f"`{os.path.basename(argv[0])} {' '.join(args)}` exited {rc}; {fix}"))
    try:
        rc, text = _run(assetgen.command("7zip") + ["i"])
        out.append(ok("7-Zip or zip step", "`7z i`") if rc == 0 else missing("7-Zip or zip step", "reinstall 7-Zip"))
    except assetgen.ToolMissing:
        buf = io.BytesIO()
        with zipfile.ZipFile(buf, "w") as z:
            z.writestr("probe.txt", "ok")
        good = zipfile.ZipFile(io.BytesIO(buf.getvalue())).read("probe.txt") == b"ok"
        out.append(ok("7-Zip or zip step", "no 7z; the Python zip step round-trips a test archive") if good else
                   missing("7-Zip or zip step", "install 7-Zip (7-zip.org)"))
    return out


def p_butler():
    out = [version_probe("butler", ["butler", "version"], "install butler (itch.io/docs/butler) on the packaging "
                                                          "and submission owner's machine")]
    target = os.environ.get("BUTLER_TARGET")
    if out[0].state != "CONNECTED":
        out.append(skipped("butler login", "butler not installed"))
    elif not target:
        out.append(missing("butler login", "set BUTLER_TARGET=<itch-user>/<game> so `butler status` can ask itch"))
    else:
        rc, text = sh(["butler", "status", target])
        out.append(ok("butler login", f"`butler status {target}`") if rc == 0 else
                   missing("butler login", "the submission owner runs `butler login` (a human step)"))
    return out


def p_keys(live):
    out = []
    for name, what in keys.KEYS.items():
        value, where = keys.lookup(name)
        label = f"API key {name} ({what})"
        if not value:
            out.append(missing(label, keys.how_to_set(name)))
            continue
        if not live:
            out.append(ok(label, f"present ({where}); auth not pinged (pass --live)"))
            continue
        url, hdr = PING[name]
        st = http_get(url, hdr(value))
        out.append(ok(label, f"present ({where}); live auth HTTP {st}") if st == 200 else
                   missing(label, f"present ({where}) but the live auth ping returned {st}; replace the key"))
    return out


def p_windows():
    if platform.system() != "Windows":
        return [skipped("Windows packaging host", "not a Windows machine; the packaging machine runs this check")]
    out = [version_probe("PowerShell", ["powershell", "-NoProfile", "-Command", "$PSVersionTable.PSVersion.ToString()"],
                         "install Windows PowerShell 5.1 or PowerShell 7")]
    vswhere = os.path.join(os.environ.get("ProgramFiles(x86)", r"C:\Program Files (x86)"),
                           "Microsoft Visual Studio", "Installer", "vswhere.exe")
    rc, text = _run([vswhere, "-latest", "-property", "installationPath"])
    out.append(ok("Visual Studio (C++ for packaging)", f"vswhere: {first(text)}") if rc == 0 and text else
               missing("Visual Studio (C++ for packaging)", "install Visual Studio 2022 with 'Game development with C++'"))
    return out


def check(root=ROOT, agent=None, role=None, live=False):
    res = [p_python()]
    for name, fn in (("claude", p_claude), ("codex", p_codex)):
        if agent and agent != name:
            res.append(skipped(f"{'Claude Code' if name == 'claude' else 'Codex'} CLI", f"not needed: --agent {agent}"))
            continue
        items = fn(agent)
        for r in items:
            r.required = agent == name
        res += items
    gh_items = p_github(root)
    for r in gh_items:
        if r.name != "git-lfs":
            r.required = True
    res += gh_items
    ue = p_unreal()
    ue.required = role in BUILD_ROLES
    res.append(ue)
    res += p_mcp(root)
    tools = p_tools()
    for r in tools:
        r.required = role == "qa-build" and r.name == "ffmpeg"
    res += tools
    res += p_butler()
    res += p_keys(live)
    res += p_windows()
    for r in res:
        if r.state != "NOT CONNECTED":
            r.required = False
    return res


def summary(res):
    c = sum(1 for r in res if r.state == "CONNECTED")
    m = sum(1 for r in res if r.state == "NOT CONNECTED")
    return f"{c} connected, {m} still need connecting"


def write_out(res, path, root=ROOT, journal_card="KICKOFF", journal=True):
    lines = [r.line() for r in res] + [summary(res)]
    os.makedirs(os.path.dirname(os.path.abspath(path)), exist_ok=True)
    with open(path, "w", encoding="utf-8") as fh:
        fh.write("\n".join(lines) + "\n")
    if journal:
        try:
            import journal as jr
            con = jr.connect()
            req = [r for r in res if r.required]
            jr.add(con, journal_card, "step", command="tools/connections.py", exit_code=1 if req else 0,
                   output_tail=jr.tail("\n".join(lines)), note="connection check", branch="", commit="")
            con.close()
        except Exception as e:  # never fail the check on the journal
            print(f"connections: journal not written ({e})", file=sys.stderr)
    return lines


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--agent", choices=("claude", "codex"))
    ap.add_argument("--role")
    ap.add_argument("--live", action="store_true", help="also send one free auth request per API key")
    ap.add_argument("--root", default=ROOT)
    ap.add_argument("--out", help="result file (default Saved/connections.txt; the status board shows it)")
    ap.add_argument("--no-journal", action="store_true")
    a = ap.parse_args(argv)
    res = check(a.root, a.agent, a.role, a.live)
    lines = write_out(res, a.out or os.path.join(a.root, "Saved", "connections.txt"), a.root,
                      journal=not a.no_journal)
    for ln in lines:
        print(ln)
    req = [r for r in res if r.required]
    if req:
        print("connections: required and missing: " + "; ".join(r.name for r in req))
    return 1 if req else 0


if __name__ == "__main__":
    sys.exit(main())
