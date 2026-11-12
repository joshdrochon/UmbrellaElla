"""Tests for pipeline/agent-ops/hook.py. Each test feeds the hook the JSON Claude Code would send
and checks the exit code (2 = blocked). The blocked cases are the gates broken on purpose."""
import json
import os
import shutil
import subprocess
import sys
import tempfile
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
HOOK = os.path.join(ROOT, "pipeline", "agent-ops", "hook.py")
sys.path.insert(0, os.path.join(ROOT, "pipeline", "agent-ops"))
import hook  # noqa: E402


class HookCase(unittest.TestCase):
    def setUp(self):
        self.proj = os.path.realpath(tempfile.mkdtemp())
        os.makedirs(os.path.join(self.proj, ".git"))
        with open(os.path.join(self.proj, ".git", "HEAD"), "w") as fh:
            fh.write("ref: refs/heads/ue-12-umbrella-lift\n")
        # AGENT_OPS_PLATFORM pins the platform so the suite gives the same answers on the Windows machine.
        self.env = dict(os.environ, CLAUDE_PROJECT_DIR=self.proj, JAM_ROLE="gameplay-dev", JAM_HOST="mac1", AGENT_OPS_PLATFORM="linux")

    def tearDown(self):
        shutil.rmtree(self.proj, ignore_errors=True)

    def run_hook(self, mode, payload, **env):
        payload.setdefault("cwd", self.proj)
        payload.setdefault("session_id", "s1")
        e = dict(self.env, **env)
        return subprocess.run([sys.executable, HOOK, mode], input=json.dumps(payload), capture_output=True, text=True, env=e, timeout=30)

    def edit(self, path, **env):
        return self.run_hook("guard", {"hook_event_name": "PreToolUse", "tool_name": "Edit", "tool_input": {"file_path": path}}, **env)

    def bash(self, command, **env):
        return self.run_hook("guard", {"hook_event_name": "PreToolUse", "tool_name": "Bash", "tool_input": {"command": command}}, **env)

    def log_lines(self):
        d = os.path.join(self.proj, "Saved", "agent-log")
        out = []
        for f in sorted(os.listdir(d)) if os.path.isdir(d) else []:
            if f.endswith(".jsonl"):
                with open(os.path.join(d, f)) as fh:
                    out += [json.loads(x) for x in fh if x.strip()]
        return out


class GuardTests(HookCase):
    def test_edit_tools_path_is_blocked(self):
        r = self.edit(os.path.join(self.proj, "tools", "pipeline_check.py"))
        self.assertEqual(r.returncode, 2, r.stderr)
        self.assertIn("gate file", r.stderr)
        blocked = [x for x in self.log_lines() if x["event"] == "blocked"]
        self.assertEqual(len(blocked), 1)
        self.assertEqual(blocked[0]["card"], "12")

    def test_every_gate_family_is_blocked(self):
        for rel in ["tests/test_x.py", ".github/workflows/pipeline-checks.yml", "evals/reviewer/cases/01/expected.json",
                    "pipeline/roles/dev-lead.md", "pipeline/agent-ops/gates.json", ".claude/settings.json",
                    ".claude/settings.local.json", "AGENTS.md", "pipeline/art/style.json", ".mcp.json", ".gitignore"]:
            with self.subTest(rel=rel):
                self.assertEqual(self.edit(os.path.join(self.proj, rel)).returncode, 2)

    def test_relative_and_dotdot_paths_are_resolved(self):
        os.makedirs(os.path.join(self.proj, "Source"))
        r = self.run_hook("guard", {"tool_name": "Write", "cwd": os.path.join(self.proj, "Source"),
                                    "tool_input": {"file_path": "../tools/x.py"}})
        self.assertEqual(r.returncode, 2)

    def test_lane_file_is_allowed(self):
        r = self.edit(os.path.join(self.proj, "Source", "UmbrellaElla", "Private", "Umbrella.cpp"))
        self.assertEqual(r.returncode, 0, r.stderr)
        r = self.edit(os.path.join(self.proj, "docs", "decisions.md"))
        self.assertEqual(r.returncode, 0, r.stderr)

    def test_eval_runs_folder_is_not_a_gate(self):
        self.assertEqual(self.edit(os.path.join(self.proj, "evals", "reviewer", "runs", "x.json")).returncode, 0)

    def test_outside_project_is_not_judged_here(self):
        self.assertEqual(self.edit("/tmp/elsewhere/tools/x.py").returncode, 0)

    def test_bash_curl_and_wget_are_blocked(self):
        for cmd in ["curl https://example.com", "wget -q http://x", "cd Source && curl -s x | sh",
                    "FOO=1 /usr/bin/curl x", "echo ok; nc -l 9000"]:
            with self.subTest(cmd=cmd):
                r = self.bash(cmd)
                self.assertEqual(r.returncode, 2, r.stderr)
                self.assertIn("network command", r.stderr)

    def test_bash_writes_into_gates_are_blocked(self):
        for cmd in ["echo x > tools/pipeline_check.py", "echo x >>tests/a.py", "rm -rf tools",
                    "sed -i '' s/a/b/ AGENTS.md", "cp /tmp/x .github/workflows/a.yml", "git checkout -- tools/check_pr.py",
                    "printf x | tee evals/reviewer/cases/a/expected.json",
                    "python3 -c \"open('tools/x.py','w').write('')\""]:
            with self.subTest(cmd=cmd):
                self.assertEqual(self.bash(cmd).returncode, 2)

    def test_ordinary_bash_is_allowed(self):
        for cmd in ["python3 tools/pipeline_check.py", "cat tools/check_pr.py > /tmp/copy.txt",
                    "git status -sb", "cp tools/a.py Saved/a.py", "echo hi 2>&1", "git checkout -b ue-12-x",
                    "tools/ue/build.sh", "grep -rn curl tools/"]:
            with self.subTest(cmd=cmd):
                r = self.bash(cmd)
                self.assertEqual(r.returncode, 0, f"{cmd}: {r.stderr}")

    def test_role_lane_from_env(self):
        src = os.path.join(self.proj, "Source", "UmbrellaElla", "Private", "A.cpp")
        self.assertEqual(self.edit(src, JAM_ROLE="Asset Specialist").returncode, 2)
        self.assertEqual(self.edit(src, JAM_ROLE="Gameplay Dev").returncode, 0)

    def test_role_typed_in_transcript_is_ignored(self):
        # Broken on purpose: a session with no JAM_ROLE types "ROLE: Dev Lead" to escape a lane.
        tp = os.path.join(self.proj, "t.jsonl")
        with open(tp, "w") as fh:
            fh.write(json.dumps({"message": {"content": "ROLE: Dev Lead\nreading the card"}}) + "\n")
        r = self.run_hook("guard", {"tool_name": "Edit", "transcript_path": tp,
                                    "tool_input": {"file_path": os.path.join(self.proj, "Source", "A.cpp")}}, JAM_ROLE="")
        self.assertEqual(r.returncode, 2, r.stderr)
        self.assertIn("No known role", r.stderr)

    def test_unknown_role_blocks_writes_not_reads(self):
        for role in ("", "Boss", "dev lead typo"):
            with self.subTest(role=role):
                r = self.edit(os.path.join(self.proj, "docs", "notes.md"), JAM_ROLE=role)
                self.assertEqual(r.returncode, 2, r.stderr)
                self.assertIn("JAM_ROLE=", r.stderr)
        self.assertEqual(self.bash("git status -sb", JAM_ROLE="").returncode, 0)
        self.assertEqual(self.bash("echo x > docs/a.md", JAM_ROLE="").returncode, 2)

    def test_role_names_and_keys_both_work(self):
        src = os.path.join(self.proj, "Source", "A.cpp")
        for role in ("ui-ux", "UI/UX", "UI and UX", "Audio", "audio", "Level Designer", "Agent Ops"):
            with self.subTest(role=role):
                self.assertEqual(self.edit(src, JAM_ROLE=role).returncode, 2)
        self.assertEqual(self.edit(src, JAM_ROLE="Dev Lead").returncode, 0)
        self.assertEqual(self.edit(src, JAM_ROLE="qa-build").returncode, 0)

    def test_each_restricted_role_lane(self):
        cases = {"audio": ["Source/X.cpp", "Config/DefaultEngine.ini"], "ui-ux": ["Source/X.cpp", "Config/DefaultGame.ini"],
                 "level-designer": ["Source/X.cpp", "Config/DefaultEngine.ini"], "producer": ["Content/A.uasset", "Source/X.cpp"],
                 "asset-specialist": ["Source/X.cpp"], "art-director": ["Config/A.ini"], "game-designer": ["Source/X.cpp"],
                 "agent-ops": ["Content/A.uasset"]}
        for role, paths in cases.items():
            for rel in paths:
                with self.subTest(role=role, rel=rel):
                    r = self.edit(os.path.join(self.proj, rel), JAM_ROLE=role)
                    self.assertEqual(r.returncode, 2, r.stderr)
                    self.assertIn("lane", r.stderr)
            with self.subTest(role=role, rel="docs"):
                self.assertEqual(self.edit(os.path.join(self.proj, "docs", "x.md"), JAM_ROLE=role).returncode, 0)
        self.assertEqual(self.edit(os.path.join(self.proj, "Content", "Audio", "SW_A.uasset"), JAM_ROLE="audio").returncode, 0)

    def test_every_gates_role_is_known_and_has_a_role_card(self):
        g = hook.load_gates()
        for key in g["role_deny"]:
            self.assertIn(key, g["roles"])
        for key in g["roles"]:
            with self.subTest(role=key):
                self.assertTrue(os.path.exists(os.path.join(ROOT, "pipeline", "roles", key + ".md")), key)

    def test_subagent_gets_both_lanes(self):
        src = os.path.join(self.proj, "Source", "A.cpp")
        r = self.run_hook("guard", {"tool_name": "Edit", "agent_type": "asset-specialist", "tool_input": {"file_path": src}}, JAM_ROLE="dev-lead")
        self.assertEqual(r.returncode, 2, r.stderr)
        r = self.run_hook("guard", {"tool_name": "Edit", "agent_type": "dev-lead", "tool_input": {"file_path": src}}, JAM_ROLE="producer")
        self.assertEqual(r.returncode, 2, r.stderr)
        r = self.run_hook("guard", {"tool_name": "Edit", "agent_type": "gameplay-dev", "tool_input": {"file_path": src}}, JAM_ROLE="")
        self.assertEqual(r.returncode, 0, r.stderr)

    def test_guard_fails_closed_on_missing_gates_file(self):
        r = self.edit(os.path.join(self.proj, "Source", "a.cpp"), AGENT_OPS_GATES=os.path.join(self.proj, "nope.json"))
        self.assertNotIn(r.returncode, (0, 2))  # crash -> onFailure: block in settings.json


class McpTests(HookCase):
    def mcp(self, name, gates=None, **env):
        env.setdefault("JAM_ROLE", "level-designer")   # an mcp_roles role (pipeline/agent-ops/editor-mcp.md)
        if gates is not None:
            path = os.path.join(self.proj, "gates.json")
            with open(path, "w") as fh:
                json.dump(gates, fh)
            env["AGENT_OPS_GATES"] = path
        return self.run_hook("guard", {"hook_event_name": "PreToolUse", "tool_name": name, "tool_input": {"code": "x"}}, **env)

    def gates_with(self, allow, enabled=True):
        g = hook.load_gates()
        g["mcp_allow"] = allow
        g["mcp_enabled"] = enabled   # as after the kickoff PR
        return g

    def test_mcp_off_until_kickoff(self):
        r = self.mcp("mcp__unreal__spawn_actor", self.gates_with(["mcp__unreal__spawn_actor"], enabled=False))
        self.assertEqual(r.returncode, 2)
        self.assertIn("mcp_enabled", r.stderr)

    def test_mcp_only_for_editor_roles(self):
        g = self.gates_with(["mcp__unreal__spawn_actor"])
        for role in ("level-designer", "integrator", "art-director", "asset-specialist", "ui-ux"):
            with self.subTest(role=role):
                self.assertEqual(self.mcp("mcp__unreal__spawn_actor", g, JAM_ROLE=role).returncode, 0)
        for role in ("gameplay-dev", "technical-director", "producer", "dev-lead"):
            with self.subTest(role=role):
                r = self.mcp("mcp__unreal__spawn_actor", g, JAM_ROLE=role)
                self.assertEqual(r.returncode, 2)
                self.assertIn("mcp_roles", r.stderr)

    def test_mcp_needs_a_card_branch(self):
        g = self.gates_with(["mcp__unreal__spawn_actor"])
        for branch in ("main", "scratch-level"):
            with self.subTest(branch=branch):
                with open(os.path.join(self.proj, ".git", "HEAD"), "w") as fh:
                    fh.write(f"ref: refs/heads/{branch}\n")
                r = self.mcp("mcp__unreal__spawn_actor", g)
                self.assertEqual(r.returncode, 2)
                self.assertIn("card branch", r.stderr)

    def test_python_and_console_tools_ask(self):
        for name in ("mcp__unreal__run_python", "mcp__unreal__execute_console_command", "mcp__unreal__exec"):
            with self.subTest(name=name):
                r = self.mcp(name, self.gates_with([name]))  # asks even when allowlisted
                self.assertEqual(r.returncode, 0, r.stderr)
                out = json.loads(r.stdout)["hookSpecificOutput"]
                self.assertEqual(out["permissionDecision"], "ask")
        self.assertEqual(self.log_lines()[-1]["event"], "ask")

    def test_unlisted_mcp_tool_blocked_listed_allowed(self):
        r = self.mcp("mcp__unreal__spawn_actor", self.gates_with([]))
        self.assertEqual(r.returncode, 2)
        self.assertIn("mcp_allow", r.stderr)
        r = self.mcp("mcp__unreal__spawn_actor", self.gates_with(["mcp__unreal__spawn_actor"]))
        self.assertEqual((r.returncode, r.stdout.strip()), (0, ""))

    def test_mcp_with_no_role_blocked(self):
        r = self.mcp("mcp__unreal__spawn_actor", self.gates_with(["mcp__unreal__spawn_actor"]), JAM_ROLE="")
        self.assertEqual(r.returncode, 2)

    def test_shipped_gates_block_every_mcp_tool_until_0_4a(self):
        self.assertEqual(self.mcp("mcp__unreal__get_actors").returncode, 2)


class HumanSubmitTests(HookCase):
    """Official Rules 17: an entrant submits, never an AI agent. butler push / login are blocked for every role."""

    def test_butler_push_blocked_for_every_role(self):
        cmds = ["butler push Team_Game.zip team/game:windows-dev", "butler.exe push x.zip u/g:windows",
                "cd dist && butler push x.zip u/g:win", "butler login",
                "python3 -c \"import subprocess; subprocess.run(['butler', 'push', 'x.zip', 'u/g:w'])\""]
        for role in ("qa-build", "producer", "agent-ops"):
            for c in cmds:
                with self.subTest(role=role, cmd=c):
                    r = self.bash(c, JAM_ROLE=role)
                    self.assertEqual(r.returncode, 2, r.stderr)
                    self.assertIn("Official Rules 17", r.stderr)

    def test_other_butler_commands_pass(self):
        for c in ("butler -V", "butler status team/game:windows-dev", "echo pushed"):
            with self.subTest(cmd=c):
                self.assertEqual(self.bash(c, JAM_ROLE="qa-build").returncode, 0)


class AskTests(HookCase):
    """Push to main, merges, repo settings and bulk deletes need a human: guard answers "ask" (exit 0 + JSON)."""

    def decision(self, command, branch=None, **env):
        if branch:
            with open(os.path.join(self.proj, ".git", "HEAD"), "w") as fh:
                fh.write(f"ref: refs/heads/{branch}\n")
        r = self.bash(command, **env)
        if r.returncode == 2:
            return "block"
        self.assertEqual(r.returncode, 0, r.stderr)
        return json.loads(r.stdout)["hookSpecificOutput"]["permissionDecision"] if r.stdout.strip() else "allow"

    def test_push_to_main_or_forced_asks(self):
        for cmd in ["git push origin main", "git push origin HEAD:main", "git push origin ue-12-x:refs/heads/master",
                    "git push --force origin ue-12-x", "git push -f origin ue-12-x", "git push --force-with-lease",
                    "git push origin +ue-12-x", "git push origin :ue-3-old", "git push --delete origin ue-3-old",
                    "git -C . push origin main", "cd Source && git push origin main"]:
            with self.subTest(cmd=cmd):
                self.assertEqual(self.decision(cmd), "ask")
        self.assertEqual(self.log_lines()[-1]["event"], "ask")

    def test_push_with_no_refspec_asks_only_on_main(self):
        self.assertEqual(self.decision("git push", branch="main"), "ask")
        self.assertEqual(self.decision("git push origin HEAD", branch="main"), "ask")
        self.assertEqual(self.decision("git push", branch="ue-12-umbrella-lift"), "allow")
        self.assertEqual(self.decision("git push -u origin HEAD", branch="ue-12-umbrella-lift"), "allow")

    def test_card_branch_push_is_allowed(self):
        for cmd in ["git push -u origin ue-12-umbrella-lift", "git push origin ue-12-x:ue-12-x", "git status && git push origin ue-12-x"]:
            with self.subTest(cmd=cmd):
                self.assertEqual(self.decision(cmd), "allow")

    def test_gh_merge_release_api_settings_ask(self):
        for cmd in ["gh pr merge 5 --squash", "gh release create v1", "gh api repos/o/r/branches/main/protection",
                    "gh secret set X", "gh variable set PIPELINE_CLOCK", "gh repo edit --default-branch x", "FOO=1 gh pr merge 5"]:
            with self.subTest(cmd=cmd):
                self.assertEqual(self.decision(cmd), "ask")
        for cmd in ["gh pr create --fill", "gh pr view 5", "gh issue comment 4 -b ok", "gh pr review 5 --approve", "gh repo view"]:
            with self.subTest(cmd=cmd):
                self.assertEqual(self.decision(cmd), "allow")

    def test_bulk_delete_under_content_or_source_asks(self):
        for cmd in ["rm -rf Content", "rm -r Content/Maps", "rm -Rf Source/Game/Private", "rm Content/Maps/*.umap",
                    "rm -rf .", "rm -rf *", "git rm -r Content/Art", "git rm Source/*.cpp", "git clean -fdx",
                    "git clean -fd Content", "Remove-Item -Recurse -Force Content", "rm -rf ./Content/"]:
            with self.subTest(cmd=cmd):
                self.assertEqual(self.decision(cmd), "ask")

    def test_ordinary_deletes_are_allowed(self):
        for cmd in ["rm -f Saved/x.log", "rm Content/Maps/L_Old.umap", "rm -rf Saved/Logs", "rm -rf /tmp/x",
                    "rm -f *.log", "git rm --cached docs/x.md", "git clean -n", "rm -rf docs/old"]:
            with self.subTest(cmd=cmd):
                self.assertEqual(self.decision(cmd), "allow")

    def test_gate_and_lane_blocks_win_over_ask(self):
        self.assertEqual(self.decision("rm -rf tools"), "block")
        self.assertEqual(self.decision("rm -rf Content", JAM_ROLE="producer"), "block")


class SecretPathTests(HookCase):
    def test_credential_folders_are_blocked(self):
        for cmd in ["cat ~/.ssh/id_rsa", "cat $HOME/.aws/credentials", "cat \"${HOME}/.config/gh/hosts.yml\"",
                    "tar czf /tmp/x.tgz ~/.ssh", "Get-Content $env:USERPROFILE\\.ssh\\id_ed25519",
                    "cp /home/someone/.aws/config Saved/x", "ls ~/.ssh && echo ok"]:
            with self.subTest(cmd=cmd):
                r = self.bash(cmd)
                self.assertEqual(r.returncode, 2, r.stderr)
                self.assertIn("credentials", r.stderr)

    def test_lookalikes_are_allowed(self):
        for cmd in ["gh auth status", "git push -u origin ue-12-x", "cat docs/ssh-notes.md", "ls ~/.sshconfig-notes",
                    "grep -rn aws docs"]:
            with self.subTest(cmd=cmd):
                self.assertEqual(self.bash(cmd).returncode, 0, cmd)


class LogAndConfigTests(HookCase):
    def test_post_tool_use_appends_hashed_record(self):
        r = self.run_hook("log", {"hook_event_name": "PostToolUse", "tool_name": "Bash", "tool_input": {"command": "ls"}})
        self.assertEqual(r.returncode, 0, r.stderr)
        rec = self.log_lines()[-1]
        self.assertEqual((rec["event"], rec["tool"], rec["card"], rec["host"]), ("tool", "Bash", "12", "mac1"))
        self.assertNotIn("build", rec)
        self.assertEqual(len(rec["args_sha256"]), 16)
        self.assertNotIn("ls", json.dumps(rec.get("command", "")))

    def test_prompt_and_stop_tokens(self):
        self.run_hook("log", {"hook_event_name": "UserPromptSubmit", "prompt": "build card 12"})
        tp = os.path.join(self.proj, "t.jsonl")
        with open(tp, "w") as fh:
            for i in range(2):
                fh.write(json.dumps({"message": {"id": f"m{i}", "usage": {"input_tokens": 10, "output_tokens": 5}}}) + "\n")
            fh.write(json.dumps({"message": {"id": "m1", "usage": {"input_tokens": 10, "output_tokens": 5}}}) + "\n")
        self.run_hook("log", {"hook_event_name": "Stop", "transcript_path": tp})
        recs = self.log_lines()
        self.assertEqual(recs[0]["prompt"], "build card 12")
        self.assertEqual(recs[1]["tokens"]["input"], 20)  # duplicate message id counted once

    def build(self, ev, cmd="tools/ue/build.sh", **resp):
        r = self.run_hook("log", {"hook_event_name": ev, "tool_name": "Bash", "tool_input": {"command": cmd}, "tool_response": resp})
        self.assertEqual(r.returncode, 0, r.stderr)
        return self.log_lines()[-1]

    def test_build_results_logged(self):
        rec = self.build("PostToolUse", stdout="Result: Succeeded")
        self.assertEqual((rec["build"], rec["build_ok"], rec["error_sha256"]), (True, True, None))
        a = self.build("PostToolUseFailure", stderr="Foo.cpp(12): error C2065: x undeclared")
        b = self.build("PostToolUse", cmd="./tools/ue/build.sh Game", exit_code=1, stderr="Foo.cpp(40): error C2065: x undeclared")
        c = self.build("PostToolUse", cmd="tools\\ue\\build.ps1", exit_code=1, stderr="Bar.cpp(1): error C1083: no file")
        self.assertFalse(a["build_ok"] or b["build_ok"] or c["build_ok"])
        self.assertEqual(a["error_sha256"], b["error_sha256"])  # same error, other line number
        self.assertNotEqual(a["error_sha256"], c["error_sha256"])
        self.assertNotIn("build", self.build("PostToolUse", cmd="echo tools/ue/build.shx"))

    def test_log_feeds_prompt_log_attempts(self):
        # End to end: the hook's own records make prompt_log.py attempts stop the card.
        sys.path.insert(0, os.path.join(ROOT, "tools"))
        import prompt_log
        import io
        from contextlib import redirect_stdout
        logdir = os.path.join(self.proj, "Saved", "agent-log")
        self.build("PostToolUseFailure", stderr="A.cpp(3): error C2065")
        with redirect_stdout(io.StringIO()):
            self.assertEqual(prompt_log.main(["attempts", "--card", "12", "--log", logdir]), 0)
        self.build("PostToolUseFailure", stderr="A.cpp(9): error C2065")
        with redirect_stdout(io.StringIO()):
            self.assertEqual(prompt_log.main(["attempts", "--card", "12", "--log", logdir]), 1)

    def test_config_change_project_settings_blocked_and_logged(self):
        r = self.run_hook("config", {"hook_event_name": "ConfigChange", "source": "project_settings",
                                     "file_path": os.path.join(self.proj, ".claude", "settings.json")})
        self.assertEqual(r.returncode, 2)
        self.assertTrue(self.log_lines()[-1]["blocked"])

    def test_config_change_user_settings_logged_not_blocked(self):
        r = self.run_hook("config", {"hook_event_name": "ConfigChange", "source": "user_settings"})
        self.assertEqual(r.returncode, 0)
        self.assertFalse(self.log_lines()[-1]["blocked"])


class InlineCodeTests(HookCase):
    """Interpreter one-liners slip past a command-name check. Each case below passed the hook before this rule."""

    def ask_of(self, r):
        return json.loads(r.stdout)["hookSpecificOutput"]["permissionDecision"] if r.stdout.strip() else None

    def test_perl_glob_delete_under_content_asks(self):
        r = self.bash("perl -e 'unlink glob q(Content/*)'", JAM_ROLE="asset-specialist")
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertEqual(self.ask_of(r), "ask", r.stdout)
        self.assertEqual(self.log_lines()[-1]["event"], "ask")

    def test_python_and_node_deletes_under_source_ask(self):
        for cmd in ["python3 -c 'import shutil; shutil.rmtree(\"Source/UmbrellaElla\")'",
                    "node -e \"require('fs').rmSync('Source/X', {recursive: true})\""]:
            with self.subTest(cmd=cmd):
                self.assertEqual(self.ask_of(self.bash(cmd)), "ask")

    def test_python_network_fetch_is_blocked(self):
        for cmd in ['python3 -c "import urllib.request; urllib.request.urlopen(\'https://example.com/x\')"',
                    "cd Source && python3 -I -c 'import socket; socket.create_connection((\"1.2.3.4\", 80))'",
                    "perl -MLWP::Simple -e 'getstore(q(http://x), q(y))'",
                    "node -e \"require('https').get('https://x')\""]:
            with self.subTest(cmd=cmd):
                r = self.bash(cmd)
                self.assertEqual(r.returncode, 2, r.stderr)
                self.assertIn("network", r.stderr)

    def test_python_write_to_gate_file_is_blocked(self):
        r = self.bash("python3 -c \"import os; os.remove('tools/pipeline_check.py')\"")
        self.assertEqual(r.returncode, 2, r.stderr)
        self.assertIn("gate file", r.stderr)

    def test_harmless_one_liners_pass(self):
        # Reading a gate file, printing, and running a tools/ script stay allowed.
        for cmd in ["python3 -c 'print(1)'", "python3 -c \"import json; print(json.load(open('tools/x.json')))\"",
                    "python3 tools/pipeline_check.py", "perl -e 'print 2'"]:
            with self.subTest(cmd=cmd):
                r = self.bash(cmd)
                self.assertEqual(r.returncode, 0, r.stderr)
                self.assertIsNone(self.ask_of(r), r.stdout)


class NativeWindowsTests(HookCase):
    """No Bash sandbox on native Windows, so every shell call is blocked there (gates.json native_windows_shell)."""

    def test_shell_blocked_on_native_windows(self):
        for tool in ("Bash", "PowerShell"):
            with self.subTest(tool=tool):
                r = self.run_hook("guard", {"tool_name": tool, "tool_input": {"command": "git status"}}, AGENT_OPS_PLATFORM="win32")
                self.assertEqual(r.returncode, 2, r.stderr)
                self.assertIn("WSL", r.stderr)

    def test_edit_on_native_windows_still_follows_lanes(self):
        r = self.run_hook("guard", {"tool_name": "Edit", "tool_input": {"file_path": os.path.join(self.proj, "docs", "x.md")}},
                          AGENT_OPS_PLATFORM="win32")
        self.assertEqual(r.returncode, 0, r.stderr)

    def test_linux_and_wsl_pass(self):
        self.assertEqual(self.bash("git status", AGENT_OPS_PLATFORM="linux").returncode, 0)

    def test_allow_setting_lets_shell_run(self):
        gates = hook.load_gates()
        gates["native_windows_shell"] = "allow"
        path = os.path.join(self.proj, "gates.json")
        with open(path, "w") as fh:
            json.dump(gates, fh)
        r = self.bash("git status", AGENT_OPS_PLATFORM="win32", AGENT_OPS_GATES=path)
        self.assertEqual(r.returncode, 0, r.stderr)

    def test_shipped_gates_block(self):
        self.assertEqual(hook.load_gates().get("native_windows_shell"), "block")


class GlobTests(unittest.TestCase):
    def test_globs(self):
        self.assertTrue(hook.glob_to_re("tools/**").match("tools/ue/build.sh"))
        self.assertFalse(hook.glob_to_re("tools/**").match("toolsx/a"))
        self.assertTrue(hook.match_any("tools", ["tools/**"]))
        self.assertTrue(hook.glob_to_re("**/*.key").match("a/b/c.key"))
        self.assertTrue(hook.glob_to_re("**/*.key").match("c.key"))
        self.assertFalse(hook.glob_to_re("AGENTS.md").match("docs/AGENTS.md"))

    def test_card_from_branch(self):
        self.assertEqual(hook.card_of("ue-0.4a-mcp"), "0.4a")
        self.assertIsNone(hook.card_of("main"))


class TemplateTests(unittest.TestCase):
    def test_settings_template_is_valid_and_covers_gates(self):
        with open(os.path.join(ROOT, "pipeline", "agent-ops", "settings.json")) as fh:
            tpl = json.load(fh)
        deny = set(tpl["permissions"]["deny"])
        for g in hook.load_gates()["gate_paths"]:
            self.assertIn(f"Edit(./{g})", deny)
        self.assertEqual(tpl["permissions"]["disableBypassPermissionsMode"], "disable")
        import re
        matcher = tpl["hooks"]["PreToolUse"][0]["matcher"]
        for tool in ("Edit", "Write", "Bash", "PowerShell", "mcp__unreal__run_python"):
            self.assertTrue(re.fullmatch(matcher, tool), tool)
        for p in hook.load_gates()["secret_read_paths"]:
            self.assertIn(f"Read({p}/**)", deny)


if __name__ == "__main__":
    unittest.main()
