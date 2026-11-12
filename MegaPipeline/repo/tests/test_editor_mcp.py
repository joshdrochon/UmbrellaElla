"""tools/editor_mcp.py: the shipped config passes (off until kickoff); each break on purpose fails."""
import json
import os
import shutil
import sys
import tempfile
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, os.path.join(ROOT, "tools"))
import editor_mcp as em  # noqa: E402


class EditorMcpCheck(unittest.TestCase):
    def setUp(self):
        self.root = tempfile.mkdtemp()
        shutil.copytree(os.path.join(ROOT, "pipeline", "agent-ops"), os.path.join(self.root, "pipeline", "agent-ops"),
                        ignore=shutil.ignore_patterns("__pycache__"))

    def tearDown(self):
        shutil.rmtree(self.root)

    def edit_json(self, rel, fn):
        p = os.path.join(self.root, rel)
        with open(p) as fh:
            d = json.load(fh)
        fn(d)
        with open(p, "w") as fh:
            json.dump(d, fh)

    def write(self, rel, text):
        with open(os.path.join(self.root, rel), "w") as fh:
            fh.write(text)

    def enable(self):
        self.edit_json(em.GATES, lambda g: g.update(mcp_enabled=True))
        with open(os.path.join(self.root, em.TEMPLATE)) as fh:
            servers = json.load(fh)["mcpServers"]
        self.write(em.MCP_JSON, json.dumps({"mcpServers": servers}))
        doc = os.path.join(self.root, em.DOC)
        with open(doc) as fh:
            text = fh.read()
        self.write(em.DOC, text.replace("Kickoff record: TBD", "Kickoff record: enabled by=Rick "
                                        "at=2026-11-11T21:30-08:00 link=https://github.com/o/r/issues/40#c1"))

    def test_shipped_config_passes(self):
        self.assertEqual(em.problems(ROOT), [])
        self.assertEqual(em.problems(self.root), [])

    def test_enabled_at_kickoff_passes(self):
        self.enable()
        self.assertEqual(em.problems(self.root), [])

    def test_broken_on_purpose(self):
        cases = {
            "non-loopback url": lambda: self.edit_json(em.TEMPLATE, lambda t: t["mcpServers"]["unreal-mcp"].update(
                url="http://10.0.0.5:8000/mcp")),
            "stdio server": lambda: self.edit_json(em.TEMPLATE, lambda t: t["mcpServers"]["unreal-mcp"].update(
                type="stdio", command="npx")),
            "literal header": lambda: self.edit_json(em.TEMPLATE, lambda t: t["mcpServers"]["unreal-mcp"].update(
                headers={"Authorization": "Bearer abc"})),
            "unknown server": lambda: self.edit_json(em.TEMPLATE, lambda t: t["mcpServers"].update(
                other={"type": "http", "url": "http://127.0.0.1:9000/mcp"})),
            "extra role": lambda: self.edit_json(em.GATES, lambda g: g["mcp_roles"].append("gameplay-dev")),
            "missing role": lambda: self.edit_json(em.GATES, lambda g: g["mcp_roles"].remove("ui-ux")),
            "not a bool": lambda: self.edit_json(em.GATES, lambda g: g.update(mcp_enabled="yes")),
            "mcp tool on a non-editor role": lambda: self.edit_json(em.AGENT_TOOLS, lambda a: a["agents"].update(
                producer="Read, mcp__unreal-mcp__spawn_actor")),
            "auto-approve servers": lambda: self.edit_json(em.SETTINGS, lambda s: s.update(enableAllProjectMcpServers=True)),
            ".mcp.json while off": lambda: self.write(em.MCP_JSON, "{}"),
        }
        for name, breaker in cases.items():
            with self.subTest(name=name):
                self.tearDown()
                self.setUp()
                breaker()
                self.assertTrue(em.problems(self.root), name)

    def test_enabled_without_kickoff_record_or_matching_config_fails(self):
        self.enable()
        self.write(em.MCP_JSON, json.dumps({"mcpServers": {"unreal-mcp": {"type": "http", "url": "http://127.0.0.1:8001/mcp"}}}))
        self.assertTrue(any("differ" in p for p in em.problems(self.root)))
        self.tearDown()
        self.setUp()
        self.enable()
        doc = os.path.join(self.root, em.DOC)
        with open(doc) as fh:
            text = fh.read()
        self.write(em.DOC, text.split("Kickoff record:")[0] + "Kickoff record: TBD\n")
        self.assertTrue(any("Kickoff record" in p for p in em.problems(self.root)))
        os.remove(os.path.join(self.root, em.MCP_JSON))
        self.assertTrue(any("no .mcp.json" in p for p in em.problems(self.root)))

    def test_cli_exit_codes(self):
        self.assertEqual(em.main(["check", "--root", self.root]), 0)
        os.remove(os.path.join(self.root, em.TEMPLATE))
        self.assertEqual(em.main(["check", "--root", self.root]), 2)


if __name__ == "__main__":
    unittest.main()
