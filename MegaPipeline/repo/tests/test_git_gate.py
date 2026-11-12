"""Agent-agnostic gate guard (tools/git_gate.py + the hooks tools/install_git_hooks.py writes): an agent commit or
push that touches a gate path is refused whatever the agent (Claude Code, Codex, a stub), a human commit through the
JAM_HUMAN route passes, and CI (check_pr rule gate) fails the PR without the human's GATE EDIT line. Each check has
a passing case and a case broken on purpose."""
import json
import os
import shutil
import subprocess
import sys
import tempfile
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, os.path.join(ROOT, "tools"))
import check_pr  # noqa: E402
import git_gate  # noqa: E402

PY = sys.executable
AGENT_VARS = ("JAM_ROLE", "JAM_KICKOFF", "CLAUDECODE", "CODEX_SANDBOX", "CODEX_SANDBOX_NETWORK_DISABLED",
              "CODEX_THREAD_ID", "JAM_HUMAN")


def clean_env(**extra):
    e = {k: v for k, v in os.environ.items() if k not in AGENT_VARS}
    e.update(extra)
    return e


class Repo:
    """A repo with tools/git_gate.py, gates.json and the installed hooks, plus a bare origin."""

    def __init__(self):
        self.base = tempfile.mkdtemp()
        self.dir = os.path.join(self.base, "repo")
        os.makedirs(os.path.join(self.dir, "tools"))
        os.makedirs(os.path.join(self.dir, "pipeline", "agent-ops"))
        shutil.copy(os.path.join(ROOT, "tools", "git_gate.py"), os.path.join(self.dir, "tools"))
        shutil.copy(os.path.join(ROOT, "pipeline", "agent-ops", "gates.json"),
                    os.path.join(self.dir, "pipeline", "agent-ops"))
        self.write("docs/notes.md", "notes\n")
        self.git("init", "-q", "-b", "main")
        self.git("add", "-A")
        self.git("commit", "-q", "-m", "base", env=clean_env(JAM_HUMAN="Josh"), hooks=False)
        subprocess.run(["git", "init", "-q", "--bare", os.path.join(self.base, "origin.git")], check=True)
        self.git("remote", "add", "origin", os.path.join(self.base, "origin.git"))
        self.git("push", "-q", "origin", "main", hooks=False)

    def close(self):
        shutil.rmtree(self.base, ignore_errors=True)

    def write(self, rel, text):
        p = os.path.join(self.dir, rel)
        os.makedirs(os.path.dirname(p), exist_ok=True)
        with open(p, "a", encoding="utf-8") as fh:
            fh.write(text)

    def git(self, *args, env=None, hooks=True):
        pre = ["git", "-c", "user.email=t@t", "-c", "user.name=t"] + ([] if hooks else ["-c", "core.hooksPath=/dev/null"])
        return subprocess.run(pre + list(args), cwd=self.dir, capture_output=True, text=True, env=env or clean_env())

    def install(self):
        p = subprocess.run([PY, os.path.join(ROOT, "tools", "install_git_hooks.py"), "--repo", self.dir],
                           capture_output=True, text=True)
        assert p.returncode == 0, p.stderr

    def commit(self, rel, **env):
        self.write(rel, "change\n")
        self.git("add", "-A")
        return self.git("commit", "-q", "-m", f"edit {rel}", env=clean_env(**env))


class PreCommitHook(unittest.TestCase):
    def setUp(self):
        self.r = Repo()
        self.addCleanup(self.r.close)
        self.r.install()

    def test_agent_commit_to_a_gate_path_is_blocked(self):
        for var, val in (("JAM_ROLE", "gameplay-dev"), ("CODEX_SANDBOX", "seatbelt"), ("CLAUDECODE", "1")):
            with self.subTest(var=var):
                p = self.r.commit("tools/check_x.py", **{var: val})
                self.assertNotEqual(p.returncode, 0)
                self.assertIn("git_gate: BLOCKED", p.stderr)
                self.assertIn("tools/check_x.py", p.stderr)
                self.r.git("reset", "-q", "--hard", "HEAD", hooks=False)

    def test_agent_that_sets_jam_human_is_still_blocked(self):
        p = self.r.commit("AGENTS.md", JAM_ROLE="producer", JAM_HUMAN="Josh")
        self.assertNotEqual(p.returncode, 0)
        self.assertIn("JAM_ROLE is set", p.stderr)

    def test_unmarked_commit_is_blocked_and_the_human_route_passes(self):
        self.assertNotEqual(self.r.commit("tools/check_x.py").returncode, 0)
        p = self.r.git("commit", "-q", "-m", "human gate edit", env=clean_env(JAM_HUMAN="Josh"))
        self.assertEqual(p.returncode, 0, p.stderr)
        self.assertIn("changed by human Josh", p.stderr)

    def test_agent_commit_outside_gates_passes(self):
        p = self.r.commit("docs/notes.md", JAM_ROLE="gameplay-dev")
        self.assertEqual(p.returncode, 0, p.stderr)

    def test_editing_gates_json_in_the_same_commit_does_not_unlock(self):
        gates = os.path.join(self.r.dir, "pipeline", "agent-ops", "gates.json")
        with open(gates, encoding="utf-8") as fh:
            g = json.load(fh)
        g["gate_paths"] = []
        with open(gates, "w", encoding="utf-8") as fh:
            json.dump(g, fh)
        p = self.r.commit("tools/check_x.py", JAM_ROLE="gameplay-dev")
        self.assertNotEqual(p.returncode, 0, "the committed HEAD gate list decides, not the working tree")

    def test_broken_on_purpose_without_the_hook_the_commit_lands(self):
        os.remove(os.path.join(self.r.dir, ".git", "hooks", "pre-commit"))
        p = self.r.commit("tools/check_x.py", JAM_ROLE="gameplay-dev")
        self.assertEqual(p.returncode, 0, "no hook, no guard: the hook is what blocks it")


class PrePushHook(unittest.TestCase):
    def setUp(self):
        self.r = Repo()
        self.addCleanup(self.r.close)
        self.r.git("checkout", "-q", "-b", "ue-12-x")
        self.r.write("tools/check_x.py", "change\n")
        self.r.git("add", "-A")
        self.r.git("commit", "-q", "-m", "slipped past pre-commit", hooks=False)
        self.r.install()

    def test_agent_push_of_a_gate_commit_is_blocked(self):
        p = self.r.git("push", "origin", "ue-12-x", env=clean_env(JAM_KICKOFF="1"))
        self.assertNotEqual(p.returncode, 0)
        self.assertIn("git_gate: BLOCKED", p.stderr)

    def test_human_push_passes(self):
        p = self.r.git("push", "origin", "ue-12-x", env=clean_env(JAM_HUMAN="Josh"))
        self.assertEqual(p.returncode, 0, p.stderr)

    def test_hooks_chain_lfs_and_check_reports_current(self):
        p = subprocess.run([PY, os.path.join(ROOT, "tools", "install_git_hooks.py"), "--repo", self.r.dir, "--check"],
                           capture_output=True, text=True)
        self.assertEqual(p.returncode, 0, p.stdout)
        with open(os.path.join(self.r.dir, ".git", "hooks", "pre-push"), encoding="utf-8") as fh:
            self.assertIn('git lfs pre-push "$@"', fh.read())
        os.remove(os.path.join(self.r.dir, ".git", "hooks", "pre-push"))   # broken on purpose
        p = subprocess.run([PY, os.path.join(ROOT, "tools", "install_git_hooks.py"), "--repo", self.r.dir, "--check"],
                           capture_output=True, text=True)
        self.assertEqual(p.returncode, 1)


class DecideUnit(unittest.TestCase):
    GATES = {"gate_paths": ["tools/**", "AGENTS.md"], "agent_env": ["JAM_ROLE", "CODEX_SANDBOX"]}

    def test_rules(self):
        self.assertEqual(git_gate.decide(["docs/a.md"], {"JAM_ROLE": "x"}, self.GATES)[0], True)
        self.assertEqual(git_gate.decide(["tools/a.py"], {"JAM_HUMAN": "Ana"}, self.GATES)[0], True)
        self.assertEqual(git_gate.decide(["tools"], {}, self.GATES)[0], False)
        self.assertEqual(git_gate.decide(["AGENTS.md"], {"CODEX_SANDBOX": "seatbelt", "JAM_HUMAN": "Ana"},
                                         self.GATES)[0], False)


class CheckPrGateRule(unittest.TestCase):
    """CI backstop: a PR that changes a gate path needs the card human's GATE EDIT line."""
    CARD = {"title": "[UE-0.3] Skeleton", "body": "### Human who runs and merges this\n\nJosh\n"}

    def probs(self, evidence, changed=("tools/ue/test.sh", "Source/A.cpp")):
        s = {"Evidence": evidence, "What changed": ""}
        return check_pr.gate_problems(s, list(changed), ROOT, self.CARD)

    def test_human_line_passes(self):
        self.assertEqual(self.probs("GATE EDIT: by=Josh tools/ue/test.sh\n"), [])

    def test_broken_no_line_or_wrong_human_fails(self):
        self.assertTrue(self.probs("all good\n"))
        got = self.probs("GATE EDIT: by=Rick tools/ue/test.sh\n")
        self.assertTrue(got and "not the card's Human Josh" in got[0], got)
        self.assertTrue(self.probs("GATE EDIT: by=agent tools/ue/test.sh\n"))

    def test_no_gate_path_needs_nothing(self):
        self.assertEqual(self.probs("", changed=("Source/A.cpp",)), [])

    def test_the_td_human_may_sign_another_cards_gate_patch(self):
        card = {"title": "[UE-0.7] Palette", "body": "### Human who runs and merges this\n\nRick (sign-off: guardrails)\n"}
        s = {"Evidence": "GATE EDIT: by=Josh pipeline/art/style.json\n", "What changed": ""}
        self.assertEqual(check_pr.td_human(ROOT), "Josh")   # docs/jam-brief.md People: the TD human seat
        self.assertEqual(check_pr.gate_problems(s, ["pipeline/art/style.json"], ROOT, card), [])
        s["Evidence"] = "GATE EDIT: by=Ana pipeline/art/style.json\n"   # broken on purpose: neither Rick nor the TD
        self.assertTrue(check_pr.gate_problems(s, ["pipeline/art/style.json"], ROOT, card))


LANE = "### File lane, do-not-touch paths, binary files to lock\n\nLane: "


class ToolRoute(unittest.TestCase):
    """No person applies a gate patch: kickoff's tool route (git_gate.py apply --auto, GATE EDIT: by=kickoff) and the
    same checks in CI (check_pr rule gate). Each passes clean and fails broken on purpose."""
    GATES = {"gate_paths": ["tools/**", ".github/**"], "mcp_enabled": False, "native_windows_shell": "block",
             "mcp_ask_words": ["exec"], "mcp_allow": [], "mcp_roles": ["ui-ux"], "role_deny": {"audio": ["Source/**"]}}

    def probs(self, paths, lanes, new):
        old = json.dumps(self.GATES)
        return git_gate.auto_problems(paths, lanes, lambda p: old, lambda p: json.dumps(new))

    def test_lane_core_and_loosening(self):
        lanes = ["pipeline/agent-ops/gates.json", ".github/CODEOWNERS", "tools/ue/"]
        self.assertEqual(self.probs([".github/CODEOWNERS", "tools/ue/x.py"], lanes, self.GATES), [])
        self.assertTrue(self.probs(["tools/other.py"], lanes, self.GATES))            # outside the lane
        self.assertTrue(self.probs(["tools/git_gate.py"], ["tools/**"], self.GATES))  # a guardrail enforcer
        self.assertTrue(self.probs(["tools/ue/x.py"], [], self.GATES))                 # no lane known
        g = "pipeline/agent-ops/gates.json"
        tighter = dict(self.GATES, gate_paths=self.GATES["gate_paths"] + ["docs/**"], mcp_allow=["get_actors"])
        self.assertEqual(self.probs([g], lanes, tighter), [])
        for broken in (dict(self.GATES, gate_paths=["tools/**"]), dict(self.GATES, mcp_enabled=True),
                       dict(self.GATES, native_windows_shell="allow"), dict(self.GATES, mcp_roles=["ui-ux", "audio"]),
                       dict(self.GATES, role_deny={"audio": []}), dict(self.GATES, mcp_allow=["exec_python"]),
                       {k: v for k, v in self.GATES.items() if k != "role_deny"}):
            self.assertTrue(self.probs([g], lanes, broken), broken)

    def test_check_pr_rechecks_a_kickoff_line(self):
        base = subprocess.run(["git", "rev-parse", "HEAD"], cwd=ROOT, capture_output=True, text=True).stdout.strip()
        card = {"title": "[UE-0.0] People", "body": LANE + "`.github/CODEOWNERS`\n"}
        s = {"Evidence": "GATE EDIT: by=kickoff .github/CODEOWNERS\n", "What changed": ""}
        self.assertEqual(check_pr.gate_problems(s, [".github/CODEOWNERS"], ROOT, card, None, base), [])
        other = {"title": "[UE-0.16] Clock", "body": LANE + "`.github/workflows/clock.yml`\n"}
        self.assertTrue(check_pr.gate_problems(s, [".github/CODEOWNERS"], ROOT, other, None, base))   # not its lane
        self.assertTrue(check_pr.gate_problems(s, [".github/CODEOWNERS"], ROOT, card, None, None))   # no base
        self.assertTrue(check_pr.gate_problems({"Evidence": "", "What changed": ""}, ["./.github/CODEOWNERS"], ROOT,
                                               card, None, base), "a dot path is still a gate path")


class ClaudeHookBlocksNoVerify(unittest.TestCase):
    def guard(self, command, proj):
        payload = {"hook_event_name": "PreToolUse", "tool_name": "Bash", "cwd": proj, "session_id": "t",
                   "tool_input": {"command": command}}
        env = dict(os.environ, JAM_ROLE="gameplay-dev", AGENT_OPS_PLATFORM="linux", CLAUDE_PROJECT_DIR=proj)
        return subprocess.run([PY, os.path.join(ROOT, "pipeline", "agent-ops", "hook.py"), "guard"],
                              input=json.dumps(payload), capture_output=True, text=True, env=env)

    def test_no_verify_blocked_plain_commit_allowed(self):
        proj = tempfile.mkdtemp()
        self.addCleanup(shutil.rmtree, proj, True)
        self.assertEqual(self.guard("git commit --no-verify -m x", proj).returncode, 2)
        self.assertEqual(self.guard("git -c core.hooksPath=/dev/null commit -m x", proj).returncode, 2)
        self.assertEqual(self.guard("git commit -m 'UE-1: x'", proj).returncode, 0)


class ApplyGatePatch(unittest.TestCase):
    """Agents own gate-path work: a session's gate.patch is applied by the TD human with one command
    (`git_gate.py apply UE-<id>`), which commits it through the human route. Broken on purpose: an agent session,
    no y, a patch that does not apply."""

    def setUp(self):
        self.r = Repo()
        self.addCleanup(self.r.close)
        self.r.install()
        self.wt = os.path.join(self.r.dir, ".pipeline", "worktrees", "ue-0.4d-art-dump")
        self.r.write(".gitignore", ".pipeline/\n")
        self.r.git("add", "-A")
        self.r.git("commit", "-q", "-m", "ignore", env=clean_env(JAM_HUMAN="Josh"))
        self.r.git("worktree", "add", "-q", "-b", "ue-0.4d-art-dump", self.wt, hooks=False)
        d = os.path.join(self.r.dir, ".pipeline", "gate-patches", "UE-0.4d")
        os.makedirs(d)
        self.patch = os.path.join(d, "gate.patch")
        with open(self.patch, "w") as fh:
            fh.write("diff --git a/tools/ue/art_dump.py b/tools/ue/art_dump.py\nnew file mode 100644\n--- /dev/null\n"
                     "+++ b/tools/ue/art_dump.py\n@@ -0,0 +1 @@\n+print('dump')\n")
        with open(os.path.join(d, "meta.json"), "w") as fh:
            json.dump({"card": "UE-0.4d", "issue": 9, "branch": "ue-0.4d-art-dump", "worktree": self.wt}, fh)
        self.env = clean_env(GIT_AUTHOR_NAME="Josh", GIT_AUTHOR_EMAIL="j@j", GIT_COMMITTER_NAME="Josh",
                             GIT_COMMITTER_EMAIL="j@j")

    def apply(self, **kw):
        kw.setdefault("env", self.env)
        return git_gate.apply_patch("UE-0.4d", kw.pop("by", "Josh"), root=self.r.dir, **kw)

    def test_the_human_applies_it_in_one_command(self):
        rc, lines = self.apply(yes=True, no_pr=True)
        self.assertEqual(rc, 0, lines)
        self.assertTrue(os.path.isfile(os.path.join(self.wt, "tools", "ue", "art_dump.py")))
        msg = subprocess.run(["git", "log", "-1", "--format=%B"], cwd=self.wt, capture_output=True, text=True).stdout
        self.assertIn("GATE EDIT: by=Josh tools/ue/art_dump.py", msg)
        self.assertIn("GATE EDIT: by=Josh tools/ue/art_dump.py", "\n".join(lines))

    def test_an_agent_session_cannot_apply_it(self):
        rc, lines = self.apply(yes=True, no_pr=True, env=dict(self.env, JAM_ROLE="technical-director"))
        self.assertEqual(rc, 1)
        self.assertIn("BLOCKED", lines[0])
        self.assertFalse(os.path.exists(os.path.join(self.wt, "tools", "ue", "art_dump.py")))

    def test_no_y_and_a_stale_patch_change_nothing(self):
        rc, _ = self.apply(no_pr=True, ask=lambda q: "n")
        self.assertEqual(rc, 1)
        self.assertFalse(os.path.exists(os.path.join(self.wt, "tools", "ue", "art_dump.py")))
        with open(self.patch, "w") as fh:
            fh.write("diff --git a/tools/x.py b/tools/x.py\n--- a/tools/x.py\n+++ b/tools/x.py\n@@ -1 +1 @@\n-a\n+b\n")
        rc, lines = self.apply(yes=True, no_pr=True)
        self.assertEqual(rc, 1)
        self.assertIn("does not apply", lines[-1])
        self.assertIn("tools/x.py", lines[-1].split("git said:")[1], "git's reason (stderr) is on the line")

    def test_kickoff_applies_it_through_the_tool_checks(self):
        meta = os.path.join(self.r.dir, ".pipeline", "gate-patches", "UE-0.4d", "meta.json")
        with open(meta) as fh:
            m = json.load(fh)
        rc, lines = self.apply(by="kickoff", no_pr=True)
        self.assertEqual(rc, 1, "broken on purpose: no lane in meta.json, the tools cannot decide")
        self.assertIn("lane is unknown", lines[-1])
        with open(meta, "w") as fh:
            json.dump(dict(m, lanes=["pipeline/art/style.json"]), fh)
        rc, lines = self.apply(by="kickoff", no_pr=True)
        self.assertEqual(rc, 1, "broken on purpose: tools/ue/art_dump.py is outside this lane")
        self.assertIn("outside the card's File lane", lines[-1])
        with open(meta, "w") as fh:
            json.dump(dict(m, lanes=["tools/ue/art_dump.py", "pipeline/art/style.json"]), fh)
        rc, lines = self.apply(by="kickoff", no_pr=True, ask=lambda q: self.fail("the tool route never asks"))
        self.assertEqual(rc, 0, lines)
        msg = subprocess.run(["git", "log", "-1", "--format=%B"], cwd=self.wt, capture_output=True, text=True).stdout
        self.assertIn("GATE EDIT: by=kickoff tools/ue/art_dump.py", msg)

    def test_pr_body_gets_the_line_under_evidence(self):
        body = "## Task\nx\n\n## Evidence\nbuild ok\n"
        got = git_gate.with_gate_line(body, "GATE EDIT: by=Josh tools/a.py")
        self.assertEqual(check_pr.GATE_EDIT.search(got).group("by"), "Josh")
        self.assertLess(got.index("## Evidence"), got.index("GATE EDIT"))
        self.assertIn("## Evidence\nGATE EDIT", git_gate.with_gate_line("## Task\nx\n", "GATE EDIT: by=Josh t"))


if __name__ == "__main__":
    unittest.main()
