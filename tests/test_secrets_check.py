"""Tests for tools/secrets_check.py. Each test plants one problem in a throwaway git repo and checks
the rule catches it (we break things on purpose to test the test), then checks the clean case.
Fake keys are assembled at run time, so no key-shaped text is ever committed."""
import json
import os
import shutil
import subprocess
import sys
import tempfile
import unittest
import io
from contextlib import redirect_stdout, redirect_stderr

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, os.path.join(ROOT, "tools"))
import secrets_check  # noqa: E402

FAKE = {
    "aws-access-key": "AKIA" + "Q7" * 8,
    "github-token": "ghp" + "_" + "a1B2" * 9,
    "api-key-sk": "sk" + "-ant-" + "x9Y8" * 6,
    "slack-token": "xox" + "b-" + "1234567890-abc",
    "google-api-key": "AI" + "za" + "B" * 35,
    "private-key": "-----BEGIN " + "RSA PRIVATE KEY-----",
}
GOOD_GITIGNORE = ".env\n.env.*\n!.env.example\n*.pem\n*.key\n"
AGENT_OPS = os.path.join(ROOT, "pipeline", "agent-ops")


class Repo:
    def __init__(self):
        self.dir = tempfile.mkdtemp()
        subprocess.run(["git", "init", "-q"], cwd=self.dir, check=True)
        os.makedirs(os.path.join(self.dir, "pipeline", "agent-ops"))
        for f in ("settings.json", "gates.json", "components.csv", "agent-tools.json"):
            shutil.copy(os.path.join(AGENT_OPS, f), os.path.join(self.dir, "pipeline", "agent-ops", f))

    def add(self, path, content):
        full = os.path.join(self.dir, path)
        os.makedirs(os.path.dirname(full), exist_ok=True)
        with open(full, "w", encoding="utf-8") as fh:
            fh.write(content if isinstance(content, str) else json.dumps(content, indent=2))
        subprocess.run(["git", "add", "-f", path], cwd=self.dir, check=True)

    def run(self, rules):
        return secrets_check.run(self.dir, rules)

    def close(self):
        shutil.rmtree(self.dir, ignore_errors=True)


class Base(unittest.TestCase):
    def setUp(self):
        self.r = Repo()

    def tearDown(self):
        self.r.close()


class SecretTests(Base):
    def test_each_pattern_caught(self):
        for name, value in FAKE.items():
            with self.subTest(name=name):
                self.r.add("docs/notes.md", f"line one\nkey = {value}\n")
                probs = self.r.run(["secret"])
                self.assertEqual([(p[0], p[1]) for p in probs], [("secret", "docs/notes.md:2")], probs)
                self.assertIn(name, probs[0][2])

    def test_clean_text_passes(self):
        self.r.add("docs/notes.md", "sk-short and AKIA alone and ghp_ prefix only\nskeleton-key-word\n")
        self.assertEqual(self.r.run(["secret"]), [])

    def test_lfs_pointer_and_binary_skipped(self):
        self.r.add("Art/a.png", "version https://git-lfs.github.com/spec/v1\n" + FAKE["aws-access-key"])
        with open(os.path.join(self.r.dir, "b.bin"), "wb") as fh:
            fh.write(b"\0\0" + FAKE["aws-access-key"].encode())
        subprocess.run(["git", "add", "b.bin"], cwd=self.r.dir, check=True)
        self.assertEqual(self.r.run(["secret"]), [])

    def test_redact(self):
        out = secrets_check.redact("use " + FAKE["github-token"] + " now")
        self.assertEqual(out, "use [REDACTED:github-token] now")


class TextModeTests(unittest.TestCase):
    """--text: secrets in PR bodies, comment exports and package folders, which never pass through git."""
    def test_key_in_exported_text_and_package_folder_fails(self):
        with tempfile.TemporaryDirectory() as d:
            body = os.path.join(d, "prs.json")
            with open(body, "w") as f:
                f.write('[{"body": "token ' + FAKE["github-token"] + '"}]\n')
            pkg = os.path.join(d, "Package", "Game", "Saved")
            os.makedirs(pkg)
            with open(os.path.join(pkg, "notes.txt"), "w") as f:
                f.write("clean\n" + FAKE["github-token"] + "\n")
            got = secrets_check.check_text([body, os.path.join(d, "Package")])
            self.assertEqual(len(got), 2, got)
            self.assertEqual(secrets_check.main(["--text", body]), 1)
            self.assertEqual(len(secrets_check.check_text(["-"], io.StringIO(FAKE["github-token"]))), 1)

    def test_clean_text_passes_and_missing_path_fails(self):
        with tempfile.TemporaryDirectory() as d:
            ok = os.path.join(d, "prs.json")
            with open(ok, "w") as f:
                f.write('[{"body": "Part of #12. Evidence: PASS tests=4 failed=0"}]\n')
            self.assertEqual(secrets_check.check_text([ok]), [])
            self.assertEqual(secrets_check.main(["--text", ok]), 0)
            self.assertEqual(len(secrets_check.check_text([os.path.join(d, "nope.json")])), 1)


class SecretFileTests(Base):
    def test_secret_names_caught(self):
        for f in (".env", "Config/.env.local", "certs/server.pem", "deploy.key", "id_rsa", "a/id_ed25519.pub"):
            with self.subTest(f=f):
                self.assertEqual(secrets_check.check_secretfile([f])[0][0], "secretfile")

    def test_ok_names(self):
        self.assertEqual(secrets_check.check_secretfile([".env.example", "docs/keys.md", "Source/KeyBinding.cpp", "monkey.png"]), [])


class GitignoreTests(Base):
    def test_missing_entries_fail(self):
        self.r.add(".gitignore", "Saved/\n")
        self.assertEqual(len(self.r.run(["gitignore"])), 4)

    def test_good_gitignore_passes(self):
        self.r.add(".gitignore", GOOD_GITIGNORE)
        self.assertEqual(self.r.run(["gitignore"]), [])


class SettingsTests(Base):
    def copy_live(self):
        with open(os.path.join(AGENT_OPS, "settings.json")) as fh:
            self.r.add(".claude/settings.json", fh.read())

    def test_missing_settings_fail(self):
        probs = self.r.run(["settings"])
        self.assertEqual([p[1] for p in probs], [".claude/settings.json"])

    def test_exact_copy_passes(self):
        self.copy_live()
        self.assertEqual(self.r.run(["settings"]), [])

    def test_drift_fails(self):
        with open(os.path.join(AGENT_OPS, "settings.json")) as fh:
            live = json.load(fh)
        live["permissions"]["deny"].remove("Edit(./tools/**)")
        self.r.add(".claude/settings.json", live)
        self.assertIn("differs", self.r.run(["settings"])[0][2])

    def test_bad_json_fails(self):
        self.r.add(".claude/settings.json", "{ not json")
        self.assertIn("not valid JSON", self.r.run(["settings"])[0][2])

    def test_guard_matcher_without_mcp_fails(self):
        tpl_path = os.path.join(self.r.dir, "pipeline", "agent-ops", "settings.json")
        with open(tpl_path) as fh:
            tpl = json.load(fh)
        tpl["hooks"]["PreToolUse"][0]["matcher"] = "Edit|Write|MultiEdit|NotebookEdit|Bash|PowerShell"
        with open(tpl_path, "w") as fh:
            json.dump(tpl, fh)
        self.copy_live()
        msgs = [p[2] for p in self.r.run(["settings"]) if p[1] == "pipeline/agent-ops/settings.json"]
        self.assertEqual(msgs, ["PreToolUse guard matcher does not cover 'mcp__unreal__run_python'"])

    def test_template_missing_gate_deny_fails(self):
        tpl_path = os.path.join(self.r.dir, "pipeline", "agent-ops", "settings.json")
        with open(tpl_path) as fh:
            tpl = json.load(fh)
        tpl["permissions"]["deny"].remove("Edit(./evals/reviewer/cases/**)")
        tpl["permissions"]["disableBypassPermissionsMode"] = ""
        tpl["hooks"].pop("ConfigChange")
        with open(tpl_path, "w") as fh:
            json.dump(tpl, fh)
        self.copy_live()
        msgs = " | ".join(p[2] for p in self.r.run(["settings"]))
        self.assertIn("evals/reviewer/cases/**", msgs)
        self.assertIn("disableBypassPermissionsMode", msgs)
        self.assertIn("ConfigChange", msgs)


    def edit_template(self, fn):
        """Fresh copy of the shipped template, changed by fn, copied live; returns the template's problems."""
        tpl_path = os.path.join(self.r.dir, "pipeline", "agent-ops", "settings.json")
        shutil.copy(os.path.join(AGENT_OPS, "settings.json"), tpl_path)
        with open(tpl_path) as fh:
            tpl = json.load(fh)
        fn(tpl)
        with open(tpl_path, "w") as fh:
            json.dump(tpl, fh)
        self.copy_live()
        return [p[2] for p in self.r.run(["settings"]) if p[1] == "pipeline/agent-ops/settings.json"]

    def test_each_required_deny_and_ask_rule(self):
        for key, rule in [("deny", r) for r in secrets_check.REQUIRED_DENY] + [("ask", r) for r in secrets_check.REQUIRED_ASK]:
            with self.subTest(rule=rule):
                msgs = self.edit_template(lambda t: t["permissions"][key].remove(rule))
                self.assertEqual(msgs, [f"permissions.{key} lacks {rule}"])

    def test_unsandboxed_commands_fail(self):
        msgs = self.edit_template(lambda t: t["sandbox"].update(allowUnsandboxedCommands=True))
        self.assertEqual(msgs, ["sandbox.allowUnsandboxedCommands is not false"])

    def test_sandbox_exception_only_for_ubt(self):
        ubt = "/Users/Shared/Epic Games/UE_5.8/Engine/Build/BatchFiles/Mac/Build.sh"
        self.assertEqual(self.edit_template(lambda t: t["sandbox"].update(excludedCommands=[ubt])), [])
        msgs = self.edit_template(lambda t: t["sandbox"].update(excludedCommands=["git"]))
        self.assertIn("not the UBT path", msgs[0])
        msgs = self.edit_template(lambda t: t["sandbox"].update(excludedCommands=[ubt, "dotnet UnrealBuildTool.dll"]))
        self.assertIn("at most 1", msgs[0])
        msgs = self.edit_template(lambda t: t["sandbox"].update(enabled=False))
        self.assertEqual(msgs, ["sandbox.enabled is not true"])


class McpTests(Base):
    def vet(self, name, kind="mcp-server"):
        with open(os.path.join(self.r.dir, "pipeline", "agent-ops", "components.csv"), "a") as fh:
            fh.write(f"{name},{kind},test,1,MIT,TD human\n")

    def test_no_mcp_json_passes(self):
        self.assertEqual(self.r.run(["mcp"]), [])

    def test_loopback_vetted_server_passes(self):
        self.vet("unreal")
        self.r.add(".mcp.json", {"mcpServers": {"unreal": {"type": "http", "url": "http://127.0.0.1:8000/mcp",
                                                           "headers": {"Authorization": "${UE_MCP_TOKEN}"}}}})
        self.assertEqual(self.r.run(["mcp"]), [])

    def test_remote_url_fails(self):
        self.vet("unreal")
        self.r.add(".mcp.json", {"mcpServers": {"unreal": {"url": "http://0.0.0.0:8000/mcp"}}})
        self.assertIn("not loopback", self.r.run(["mcp"])[0][2])

    def test_unlisted_or_unvetted_server_fails(self):
        self.r.add(".mcp.json", {"mcpServers": {"unreal-mcp": {"url": "http://127.0.0.1:8000/mcp"}}})
        self.assertIn("no vetted", self.r.run(["mcp"])[0][2])  # the shipped row is vetted_by TBD

    def test_literal_secret_value_fails(self):
        self.vet("tool")
        self.r.add(".mcp.json", {"mcpServers": {"tool": {"command": "x", "env": {"API_KEY": "abc123"}}}})
        self.assertIn("literal value", self.r.run(["mcp"])[0][2])


CLEAN_COMPONENTS = ("# notes are skipped\nname,kind,source,version,licence,vetted_by\n"
                    "Unreal Engine,engine,Epic Games Launcher,5.8.4,Unreal Engine EULA,TD human\n")


class ComponentTests(Base):
    def components(self, text):
        with open(os.path.join(self.r.dir, "pipeline", "agent-ops", "components.csv"), "w") as fh:
            fh.write(text)

    def test_clean_inventory_passes(self):
        self.components(CLEAN_COMPONENTS)
        self.assertEqual(self.r.run(["components"]), [])

    def test_tbd_or_empty_vetted_by_fails(self):
        for who in ("TBD", "", " TBD "):
            with self.subTest(who=repr(who)):
                self.components(CLEAN_COMPONENTS + f"Paper2D,engine-plugin,engine,5.8.4,EULA,{who}\n")
                probs = self.r.run(["components"])
                self.assertEqual([p[1] for p in probs], ["pipeline/agent-ops/components.csv:4"], probs)
                self.assertIn("vetted_by", probs[0][2])

    def test_verify_tag_fails(self):
        self.components(CLEAN_COMPONENTS + "unreal,mcp-server,editor plugin [VERIFY name],5.8.4,EULA,TD human\n")
        probs = self.r.run(["components"])
        self.assertEqual(len(probs), 1, probs)
        self.assertIn("[VERIFY]", probs[0][2])

    def test_shipped_inventory_still_fails(self):
        # The repo's rows are TBD until card 0.4a: the rule must say so on its own.
        msgs = " | ".join(p[2] for p in self.r.run(["components"]))
        self.assertIn("vetted_by 'TBD'", msgs)
        self.assertIn("[VERIFY]", msgs)

    def build_version(self, major, minor, patch):
        path = os.path.join(self.r.dir, "Build.version")
        with open(path, "w") as fh:
            json.dump({"MajorVersion": major, "MinorVersion": minor, "PatchVersion": patch, "Changelist": 0}, fh)
        return path

    def test_engine_version_matches_installed_build(self):
        self.components(CLEAN_COMPONENTS + "Paper2D,engine-plugin,built into Unreal Engine,5.8.4,EULA,TD human\n"
                        "Other,engine-plugin,Fab,1.2.0,MIT,TD human\n")
        self.assertEqual(secrets_check.run(self.r.dir, ["components"], build_version=self.build_version(5, 8, 4)), [])
        probs = secrets_check.run(self.r.dir, ["components"], build_version=self.build_version(5, 8, 3))
        self.assertEqual([p[1] for p in probs], ["pipeline/agent-ops/components.csv:3", "pipeline/agent-ops/components.csv:4"], probs)
        self.assertIn("installed engine 5.8.3", probs[0][2])
        probs = secrets_check.run(self.r.dir, ["components"], build_version=os.path.join(self.r.dir, "nope"))
        self.assertIn("cannot read Build.version", probs[0][2])

    def test_unvetted_plugin_fails_vetted_passes(self):
        self.components(CLEAN_COMPONENTS)
        self.r.add("Game.uproject", {"Plugins": [{"Name": "Paper2D", "Enabled": True}, {"Name": "Off", "Enabled": False}]})
        probs = self.r.run(["components"])
        self.assertEqual(len(probs), 1)
        self.assertIn("Paper2D", probs[0][2])
        with open(os.path.join(self.r.dir, "pipeline", "agent-ops", "components.csv"), "a") as fh:
            fh.write("Paper2D,engine-plugin,engine,5.8.4,EULA,TD human\n")
        self.assertEqual(self.r.run(["components"]), [])


class AgentTests(Base):
    def setUp(self):
        super().setUp()
        with open(os.path.join(AGENT_OPS, "gates.json")) as fh:
            self.roles = sorted(json.load(fh)["roles"])
        for role in self.roles:
            self.r.add(f".claude/agents/{role}.md", secrets_check.agent_stub(self.r.dir, role))

    def agent(self, name, tools_line):
        fm = f"---\nname: {name}\ndescription: x\n" + (f"tools: {tools_line}\n" if tools_line is not None else "") + "---\nbody\n"
        self.r.add(f".claude/agents/{name}.md", fm)

    def test_stub_for_every_role_passes(self):
        self.assertEqual(len(self.roles), 15)   # 13 + Encounter Designer + Story
        self.assertEqual(self.r.run(["agents"]), [])

    def test_missing_tools_line_fails(self):
        self.agent("gameplay-dev", None)
        self.assertEqual([p[2][:13] for p in self.r.run(["agents"])], ["no tools: lin"])

    def test_web_tool_fails(self):
        self.agent("gameplay-dev", "Read, Grep, Glob, Bash, Edit, Write, WebFetch")
        msgs = " | ".join(p[2] for p in self.r.run(["agents"]))
        self.assertIn("web tools", msgs)

    def test_matching_line_passes(self):
        self.agent("gameplay-dev", "Read, Grep, Glob, Bash, Edit, Write")
        self.assertEqual(self.r.run(["agents"]), [])

    def test_missing_agent_file_fails(self):
        os.remove(os.path.join(self.r.dir, ".claude", "agents", "audio.md"))
        probs = self.r.run(["agents"])
        self.assertEqual([p[1] for p in probs], [".claude/agents/audio.md"], probs)
        self.assertIn("--agent-stub audio", probs[0][2])

    def test_no_agents_folder_fails_for_every_role(self):
        shutil.rmtree(os.path.join(self.r.dir, ".claude", "agents"))
        self.assertEqual(len(self.r.run(["agents"])), 15)

    def test_role_lists_must_agree(self):
        path = os.path.join(self.r.dir, "pipeline", "agent-ops", "agent-tools.json")
        with open(path) as fh:
            spec = json.load(fh)
        spec["agents"].pop("ui-ux")
        spec["agents"]["boss"] = "Read"
        with open(path, "w") as fh:
            json.dump(spec, fh)
        msgs = " | ".join(p[2] for p in self.r.run(["agents"]) if p[1].endswith("agent-tools.json"))
        self.assertIn("role 'ui-ux'", msgs)
        self.assertIn("'boss' is not a role", msgs)

    def test_stub_cli(self):
        buf = io.StringIO()
        with redirect_stdout(buf):
            self.assertEqual(secrets_check.main(["--root", self.r.dir, "--agent-stub", "audio"]), 0)
        self.assertIn("tools: Read, Grep, Glob, Bash, Edit, Write", buf.getvalue())
        self.assertIn("pipeline/roles/audio.md", buf.getvalue())
        with redirect_stdout(io.StringIO()), redirect_stderr(io.StringIO()):
            self.assertEqual(secrets_check.main(["--root", self.r.dir, "--agent-stub", "boss"]), 2)


class InstallTests(Base):
    """--install is card 0.17 in one command: settings copy plus one stub per role, then rules settings and agents."""

    def cli(self, *args):
        buf = io.StringIO()
        with redirect_stdout(buf), redirect_stderr(io.StringIO()):
            rc = secrets_check.main(["--root", self.r.dir] + list(args))
        return rc, buf.getvalue()

    def test_install_makes_settings_and_agents_pass(self):
        self.assertTrue(self.r.run(["settings", "agents"]))  # before: missing settings, 15 missing stubs
        rc, out = self.cli("--install")
        self.assertEqual(rc, 0, out)
        self.assertEqual(out.count("wrote .claude/agents/"), 15)
        self.assertEqual(self.r.run(["settings", "agents"]), [])

    def test_install_overwrites_a_stub_with_no_tools_line(self):
        self.r.add(".claude/agents/producer.md", "---\nname: producer\n---\nold stub\n")
        self.assertEqual(self.cli("--install")[0], 0)
        self.assertEqual(self.r.run(["agents"]), [])

    def test_install_reports_a_broken_template(self):
        # Broken on purpose: the template lost its sandbox, so the installed copy still fails rule settings.
        path = os.path.join(self.r.dir, "pipeline", "agent-ops", "settings.json")
        with open(path) as fh:
            tpl = json.load(fh)
        tpl["sandbox"]["enabled"] = False
        with open(path, "w") as fh:
            json.dump(tpl, fh)
        rc, out = self.cli("--install")
        self.assertEqual(rc, 1, out)
        self.assertIn("sandbox.enabled is not true", out)

    def test_install_refuses_invalid_json_template(self):
        with open(os.path.join(self.r.dir, "pipeline", "agent-ops", "settings.json"), "w") as fh:
            fh.write("{not json")
        self.assertEqual(self.cli("--install")[0], 2)
        self.assertFalse(os.path.exists(os.path.join(self.r.dir, ".claude", "settings.json")))


class CliTests(unittest.TestCase):
    def test_unknown_rule_exits_2(self):
        self.assertEqual(secrets_check.main(["--rules", "nope"]), 2)

    def test_this_repo_has_no_tracked_secrets(self):
        probs = secrets_check.run(ROOT, ["secret", "secretfile"])
        self.assertEqual(probs, [], probs)


if __name__ == "__main__":
    unittest.main()
