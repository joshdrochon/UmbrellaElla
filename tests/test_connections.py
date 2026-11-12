"""Connection check (tools/connections.py) with every probe stubbed (tests/fixtures/kickoff/stubbins.py): the
all-connected case, the some-missing case, secrets never printed, and one case per probe type broken on purpose."""
import json
import os
import shutil
import subprocess
import sys
import tempfile
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
FIX = os.path.join(HERE, "fixtures", "kickoff")
sys.path.insert(0, FIX)
import stubbins  # noqa: E402

PY = sys.executable
SECRETS = {"OPENAI_API_KEY": "fake-openai-SECRETVALUE0123456789abcdef", "ELEVENLABS_API_KEY": "fake-eleven-SECRET0123456789abcdef",
           "STABILITY_API_KEY": "fake-stability-SECRET0123456789"}


class Connections(unittest.TestCase):
    def setUp(self):
        self.d = tempfile.mkdtemp()
        self.addCleanup(shutil.rmtree, self.d, True)
        self.bin = os.path.join(self.d, "bin")
        stubbins.make(self.bin)
        self.path = stubbins.add_git(self.bin)
        self.ue = os.path.join(self.d, "UE_5.8")
        os.makedirs(os.path.join(self.ue, "Engine", "Build"))
        self.version("5.8.4")
        self.repo = os.path.join(self.d, "repo")
        subprocess.run(["git", "init", "-q", self.repo], check=True)
        subprocess.run([PY, os.path.join(ROOT, "tools", "install_git_hooks.py"), "--repo", self.repo],
                       capture_output=True, check=True)

    def version(self, v):
        major, minor, patch = v.split(".")
        with open(os.path.join(self.ue, "Engine", "Build", "Build.version"), "w") as fh:
            json.dump({"MajorVersion": int(major), "MinorVersion": int(minor), "PatchVersion": int(patch)}, fh)

    def env(self, **extra):
        e = {k: v for k, v in os.environ.items() if k not in SECRETS and k not in ("UE_ROOT", "BUTLER_TARGET")}
        e.update(stubbins.tool_env(self.bin))
        e.update(PATH=self.path, UE_ROOT=self.ue, KICKOFF_GH=stubbins.exe(self.bin, "gh"), BUTLER_TARGET="team/game",
                 FAKE_GH_STATE=os.path.join(self.d, "gh.json"), KEYS_NO_KEYCHAIN="1",
                 CONNECTIONS_HTTP_STUB=os.path.join(FIX, "http_stub.py"), JOURNAL_DB=os.path.join(self.d, "j.db"),
                 **SECRETS)
        e.update(extra)
        return {k: v for k, v in e.items() if v is not None}

    def run_check(self, *args, **extra):
        out = os.path.join(self.d, "connections.txt")
        p = subprocess.run([PY, os.path.join(ROOT, "tools", "connections.py"), "--root", self.repo, "--out", out,
                            *args], capture_output=True, text=True, env=self.env(**extra))
        with open(out, encoding="utf-8") as fh:
            saved = fh.read()
        return p.returncode, p.stdout + p.stderr, saved

    def line(self, out, name):
        hits = [ln for ln in out.splitlines() if f" {name} " in ln + " " or ln.endswith(f" {name}")]
        self.assertTrue(hits, f"no line for {name}:\n{out}")
        return hits[0]

    def test_all_connected(self):
        rc, out, saved = self.run_check("--agent", "codex")
        self.assertEqual(rc, 0, out)
        self.assertIn("0 still need connecting", out)
        self.assertNotIn("NOT CONNECTED", out)
        self.assertIn("SKIPPED MCP server gimp-mcp (off until kickoff", out)
        self.assertIn("SKIPPED Claude Code CLI (not needed: --agent codex)", out)
        self.assertIn("CONNECTED Codex login", out)
        self.assertIn("0 still need connecting", saved, "the status board reads this file")

    def test_some_missing(self):
        os.remove(stubbins.exe(self.bin, "codex"))
        os.remove(stubbins.exe(self.bin, "sox"))
        rc, out, _ = self.run_check("--agent", "codex", SOX=None)
        self.assertEqual(rc, 1, "codex is required for --agent codex")
        self.assertIn("NOT CONNECTED Codex CLI -> install Codex", out)
        self.assertIn("(required)", self.line(out, "Codex CLI"))
        self.assertRegex(out, r"NOT CONNECTED sox -> .*brew install sox")
        self.assertNotIn("(required)", self.line(out, "sox"), "sox has a fallback")
        self.assertRegex(out, r"\d+ connected, [1-9]\d* still need connecting")

    def test_secrets_never_printed(self):
        rc, out, saved = self.run_check("--agent", "codex", "--live")
        self.assertEqual(rc, 0, out)
        self.assertIn("live auth HTTP 200", out)
        for v in SECRETS.values():
            self.assertNotIn(v, out)
            self.assertNotIn(v, saved)
        import sqlite3
        con = sqlite3.connect(os.path.join(self.d, "j.db"))
        rows = " ".join(str(r) for r in con.execute("SELECT * FROM events"))
        con.close()
        self.assertIn("connection check", rows)
        for v in SECRETS.values():
            self.assertNotIn(v, rows)

    def test_each_probe_type_broken_on_purpose(self):
        cases = [
            ("agent CLI version", "Codex CLI", lambda: os.remove(stubbins.exe(self.bin, "codex")), {}),
            ("agent login", "Claude Code login", lambda: self.rewrite("claude", "sys.exit(1)"), {}),
            ("GitHub permission", "GitHub push access", lambda: None, {"FAKE_GH_PERMISSION": "READ"}),
            ("git hooks", "git hooks (gate guard, journal, LFS)",
             lambda: os.remove(os.path.join(self.repo, ".git", "hooks", "pre-commit")), {}),
            ("engine version", "Unreal Engine 5.8.4", lambda: self.version("5.8.2"), {}),
            ("app CLI", "Aseprite CLI", lambda: self.rewrite("aseprite", "sys.exit(3)"), {}),
            ("butler login", "butler login", lambda: None, {"BUTLER_TARGET": None}),
            ("API key presence", "API key ELEVENLABS_API_KEY", lambda: None, {"ELEVENLABS_API_KEY": None}),
            ("API key live ping", "API key STABILITY_API_KEY", lambda: None, {"STABILITY_API_KEY": "fake-revoked-key"}),
        ]
        for what, name, breaker, extra in cases:
            with self.subTest(probe=what):
                args = ("--live",) if "ping" in what else ()
                rc, out, _ = self.run_check(*args)
                self.assertTrue(self.line(out, name).startswith("CONNECTED"), f"{what} before the break:\n{out}")
                breaker()
                rc, out, _ = self.run_check(*args, **extra)
                self.assertTrue(self.line(out, name).startswith("NOT CONNECTED"), f"{what}:\n{out}")
                shutil.rmtree(self.d, True)
                self.setUp()

    def test_mcp_servers_probed_when_on(self):
        root = os.path.join(self.d, "mcproot")
        os.makedirs(os.path.join(root, "pipeline"))
        shutil.copytree(os.path.join(ROOT, "pipeline", "agent-ops"), os.path.join(root, "pipeline", "agent-ops"))
        g = os.path.join(root, "pipeline", "agent-ops", "gates.json")
        with open(g) as fh:
            gates = json.load(fh)
        gates["mcp_enabled"] = True
        with open(g, "w") as fh:
            json.dump(gates, fh)
        sys.path.insert(0, os.path.join(ROOT, "tools"))
        import connections
        old = os.environ.copy()
        os.environ.update(PATH=self.path, CONNECTIONS_HTTP_STUB=os.path.join(FIX, "http_stub.py"))
        try:
            res = {r.name: r for r in connections.p_mcp(root)}
            self.assertEqual(res["MCP server gimp-mcp"].state, "CONNECTED", res["MCP server gimp-mcp"].detail)
            self.assertEqual(res["MCP server unreal-mcp"].state, "CONNECTED")
            os.remove(stubbins.exe(self.bin, "aseprite-mcp"))   # broken on purpose: the server is gone
            res = {r.name: r for r in connections.p_mcp(root)}
            self.assertEqual(res["MCP server aseprite-mcp"].state, "NOT CONNECTED")
        finally:
            os.environ.clear()
            os.environ.update(old)

    def rewrite(self, name, body):
        stubbins.script(os.path.join(self.bin, name), f"import sys\n{body}", python=PY)


if __name__ == "__main__":
    unittest.main()
