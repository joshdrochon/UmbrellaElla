"""Gate paths without a git-level guard (Josh, 12 Nov): tools/install_git_hooks.py installs no gate check, so an
agent's gate-path commit and push land locally, and CI (check_pr rule gate) fails the PR without the human's or
kickoff's GATE EDIT line. tools/git_gate.py stays a library for kickoff's tool route (apply --auto) and check_pr.
Each check has a passing case and a case broken on purpose."""
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


class NoGateHook(unittest.TestCase):
    """The installer writes post-commit (journal) and pre-push (Git LFS only); nothing checks gate paths locally."""

    def setUp(self):
        self.r = Repo()
        self.addCleanup(self.r.close)
        self.r.install()
        self.hooks = os.path.join(self.r.dir, ".git", "hooks")

    def tool(self, *a):
        return subprocess.run([PY, os.path.join(ROOT, "tools", "install_git_hooks.py"), "--repo", self.r.dir, *a],
                              capture_output=True, text=True)

    def read(self, name):
        with open(os.path.join(self.hooks, name), encoding="utf-8") as fh:
            return fh.read()

    def test_no_pre_commit_and_pre_push_is_lfs_only(self):
        self.assertFalse(os.path.exists(os.path.join(self.hooks, "pre-commit")))
        push = self.read("pre-push")
        self.assertIn('git lfs pre-push "$@"', push)
        self.assertNotIn("git_gate", push)
        self.assertEqual(self.tool("--check").returncode, 0)

    def test_an_agent_gate_commit_and_push_land_locally(self):
        """No local hook stops it: check_pr's gate rule on the PR does (CheckPrGateRule)."""
        self.r.git("checkout", "-q", "-b", "ue-12-x")
        p = self.r.commit("tools/check_x.py", JAM_ROLE="gameplay-dev")
        self.assertEqual(p.returncode, 0, p.stderr)
        p = self.r.git("push", "-q", "origin", "ue-12-x", env=clean_env(JAM_KICKOFF="1"))
        self.assertEqual(p.returncode, 0, p.stderr)

    def test_broken_on_purpose_a_missing_pre_push_fails_check(self):
        os.remove(os.path.join(self.hooks, "pre-push"))
        self.assertEqual(self.tool("--check").returncode, 1)
        self.assertEqual(self.tool().returncode, 0)
        self.assertEqual(self.tool("--check").returncode, 0)

    def test_an_old_gate_hook_is_removed_and_fails_check_until_then(self):
        old = "#!/bin/sh\n# jam-git-gate (tools/install_git_hooks.py)\nexit 1\n"
        for name in ("pre-commit", "pre-push"):
            with open(os.path.join(self.hooks, name), "w", encoding="utf-8") as fh:
                fh.write(old)
        p = self.tool("--check")
        self.assertEqual(p.returncode, 1, "broken on purpose: an old gate hook is still installed")
        self.assertIn("old gate hook", p.stdout)
        p = self.tool()
        self.assertEqual(p.returncode, 0, p.stderr)
        self.assertFalse(os.path.exists(os.path.join(self.hooks, "pre-commit")))
        self.assertNotIn("jam-git-gate", self.read("pre-push"))
        self.assertEqual(self.tool("--check").returncode, 0)

    def test_a_foreign_pre_commit_is_left_alone(self):
        with open(os.path.join(self.hooks, "pre-commit"), "w", encoding="utf-8") as fh:
            fh.write("#!/bin/sh\necho mine\n")
        self.assertEqual(self.tool().returncode, 0)
        self.assertEqual(self.tool("--check").returncode, 0)
        self.assertIn("echo mine", self.read("pre-commit"))


class CheckPrGateRule(unittest.TestCase):
    """CI backstop: on a card PR a gate-path change passes only through kickoff's tool route, read from git (the
    repo-backed cases are in ApplyGatePatch). A person's GATE EDIT line in the body passes only on a PR with no card."""
    CARD = {"title": "[UE-0.3] Skeleton", "body": "### Human who runs and merges this\n\nJosh\n"}

    def probs(self, evidence, changed=("tools/ue/test.sh", "Source/A.cpp"), card=CARD, task="Part of #4"):
        s = {"Evidence": evidence, "What changed": "", "Task": task}
        return check_pr.gate_problems(s, list(changed), ROOT, card)

    def test_card_pr_human_line_alone_fails(self):
        self.assertTrue(self.probs("GATE EDIT: by=Josh tools/ue/test.sh\n"))
        self.assertTrue(self.probs("GATE EDIT: by=Josh tools/ue/test.sh\n", card=None), "the Task link makes it a card PR")
        self.assertTrue(self.probs("GATE EDIT: by=kickoff tools/ue/test.sh\n"), "a body line is not the git record")

    def test_no_card_pr_takes_a_person_line(self):
        self.assertEqual(self.probs("GATE EDIT: by=Josh tools/ue/test.sh\n", card=None, task=""), [])
        self.assertTrue(self.probs("all good\n", card=None, task=""))
        self.assertTrue(self.probs("GATE EDIT: by=agent tools/ue/test.sh\n", card=None, task=""))

    def test_no_gate_path_needs_nothing(self):
        self.assertEqual(self.probs("", changed=("Source/A.cpp",)), [])


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

    CARD = {"title": "[UE-0.4d] Art dump", "body": LANE + "`tools/ue/art_dump.py`\n"}

    def wt_git(self, *args, env=None):
        return subprocess.run(["git", "-c", "user.email=t@t", "-c", "user.name=t", "-c", "core.hooksPath=/dev/null",
                               *args], cwd=self.wt, capture_output=True, text=True, env=env or clean_env()).stdout.strip()

    def gate(self, evidence=""):
        """check_pr rule gate on the card's branch: base = main, head = the worktree HEAD (the git record)."""
        s = {"Task": "Part of #9. Card ID: UE-0.4d", "Evidence": evidence, "What changed": ""}
        base, head = self.wt_git("rev-parse", "main"), self.wt_git("rev-parse", "HEAD")
        changed = self.wt_git("diff", "--name-only", f"{base}..{head}").split()
        return check_pr.gate_problems(s, changed, self.r.dir, self.CARD, head, base)

    def test_agent_commit_with_a_human_gate_edit_line_fails(self):
        os.makedirs(os.path.join(self.wt, "tools", "ue"))
        with open(os.path.join(self.wt, "tools", "ue", "art_dump.py"), "w") as fh:
            fh.write("print('dump')\n")
        self.wt_git("add", "-A")
        self.wt_git("commit", "-q", "-m", "UE-0.4d: art dump\n\nGATE EDIT: by=Josh tools/ue/art_dump.py",
                    env=clean_env(JAM_ROLE="technical-director"))
        got = self.gate("GATE EDIT: by=Josh tools/ue/art_dump.py\n")
        self.assertTrue(got, "an agent's own gate commit plus a by=Josh line must fail")
        self.assertTrue(any("not kickoff's gate commit" in p for p in got), got)
        self.assertTrue(any("by=Josh" in p and "card PR" in p for p in got), got)

    def test_kickoff_route_passes_and_a_later_agent_commit_fails(self):
        meta = os.path.join(self.r.dir, ".pipeline", "gate-patches", "UE-0.4d", "meta.json")
        with open(meta) as fh:
            m = json.load(fh)
        with open(meta, "w") as fh:
            json.dump(dict(m, lanes=["tools/ue/art_dump.py"]), fh)
        rc, lines = self.apply(by="kickoff", no_pr=True)
        self.assertEqual(rc, 0, lines)
        self.assertEqual(self.gate(), [], "kickoff's gate commit (trailer by=kickoff) passes with no body line")
        with open(os.path.join(self.wt, "tools", "ue", "art_dump.py"), "a") as fh:
            fh.write("import os\n")
        self.wt_git("commit", "-q", "-am", "UE-0.4d: tweak", env=clean_env(JAM_ROLE="technical-director"))
        got = self.gate("GATE EDIT: by=kickoff tools/ue/art_dump.py\n")
        self.assertTrue(got and "not kickoff's gate commit" in got[0], "broken on purpose: an agent edit after it")

    def test_a_kickoff_trailer_outside_the_lane_fails_the_recheck(self):
        os.makedirs(os.path.join(self.wt, "tools", "ue"))
        with open(os.path.join(self.wt, "tools", "kickoff_extra.py"), "w") as fh:
            fh.write("x = 1\n")
        self.wt_git("add", "-A")
        self.wt_git("commit", "-q", "-m", "forged\n\nGATE EDIT: by=kickoff tools/kickoff_extra.py")
        got = self.gate()
        self.assertTrue(got and "re-check" in got[0], got)

    def test_pr_body_gets_the_line_under_evidence(self):
        body = "## Task\nx\n\n## Evidence\nbuild ok\n"
        got = git_gate.with_gate_line(body, "GATE EDIT: by=Josh tools/a.py")
        self.assertEqual(check_pr.GATE_EDIT.search(got).group("by"), "Josh")
        self.assertLess(got.index("## Evidence"), got.index("GATE EDIT"))
        self.assertIn("## Evidence\nGATE EDIT", git_gate.with_gate_line("## Task\nx\n", "GATE EDIT: by=Josh t"))


if __name__ == "__main__":
    unittest.main()
