"""tools/journal.py, the journal hooks, the agent launcher and the git post-commit hook."""
import json
import os
import shutil
import signal
import sqlite3
import subprocess
import sys
import tempfile
import time
import unittest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "tools"))
import journal  # noqa: E402

JOURNAL = os.path.join(ROOT, "tools", "journal.py")
HOOK = os.path.join(ROOT, "pipeline", "agent-ops", "journal_hook.py")
TOKEN = "ghp_" + "a1b2c3d4e5" * 4


class Base(unittest.TestCase):
    def setUp(self):
        self.dir = tempfile.mkdtemp()
        self.db = os.path.join(self.dir, "journal.db")
        self.env = dict(os.environ, JOURNAL_DB=self.db, JAM_MACHINE="test-host")
        self.env.pop("JAM_CARD", None)
        self.env.pop("JAM_ROLE", None)

    def tearDown(self):
        shutil.rmtree(self.dir, ignore_errors=True)

    def j(self, *args, check=True, **kw):
        r = subprocess.run([sys.executable, JOURNAL, *args], env=self.env, capture_output=True, text=True,
                           cwd=kw.get("cwd", ROOT), input=kw.get("input"))
        if check and r.returncode not in kw.get("ok", (0,)):
            self.fail(f"journal {args} exit {r.returncode}: {r.stdout}{r.stderr}")
        return r

    def rows(self, card="UE-12"):
        con = sqlite3.connect(self.db)
        try:
            return con.execute('SELECT kind, command, exit_code, output_tail, note, next_step, branch, "commit"'
                               " FROM events WHERE card = ? ORDER BY id", (card,)).fetchall()
        finally:
            con.close()


class JournalTests(Base):
    def test_export_never_prints_the_raw_hostname(self):
        # dry run B M15: `journal.py export` put the raw hostname (a personal name) into PR bodies
        import socket
        self.env.pop("JAM_MACHINE")
        self.env.pop("JAM_HOST", None)
        self.j("start", "--role", "gameplay-dev", "--card", "UE-12")
        out = self.j("export", "--card", "UE-12").stdout
        self.assertRegex(out, r"machine=host-[0-9a-f]{6} ")
        self.assertNotIn(socket.gethostname(), out)
        self.env["JAM_HOST"] = "mac-1"
        self.j("step", "--card", "UE-12", "--cmd", "x", "--exit", "0")
        self.assertIn("machine=mac-1 ", self.j("export", "--card", "UE-12").stdout)

    def test_full_session_resume_and_export(self):
        self.j("start", "--role", "gameplay-dev", "--card", "ue-12")
        self.j("step", "--card", "12", "--cmd", "tools/ue/build.sh", "--exit", "0")
        self.j("checkpoint", "--card", "UE-12", "--note", "built", "--next", "run the Movement tests")
        self.j("step", "--card", "UE-12", "--cmd", "tools/ue/test.sh", "--exit", "1")
        out = self.j("resume", "--card", "UE-12").stdout
        self.assertIn("Last checkpoint", out)
        self.assertIn("note: built", out)
        self.assertIn("exit=1 tools/ue/test.sh", out)
        self.assertNotIn("tools/ue/build.sh", out.split("Since then")[1])  # steps before the checkpoint are not repeated
        self.assertIn("UNFINISHED next step: run the Movement tests", out)
        exp = self.j("export", "--card", "UE-12").stdout
        self.assertIn("journal.py export card=UE-12", exp)
        self.assertIn("| 0 | `tools/ue/build.sh` |", exp)
        self.assertIn("| 1 | `tools/ue/test.sh` |", exp)
        self.assertIn("Next step: run the Movement tests", exp)
        kinds = [r[0] for r in self.rows()]
        self.assertEqual(kinds, ["start", "step", "checkpoint", "step"])
        self.assertTrue(self.rows()[0][6])  # start records the branch
        self.assertRegex(self.rows()[0][7] or "", r"^[0-9a-f]{40}$")  # and the commit

    def test_end_clears_the_unfinished_step(self):
        self.j("start", "--card", "UE-12")
        self.j("checkpoint", "--card", "UE-12", "--note", "n", "--next", "x")
        self.j("end", "--card", "UE-12")
        out = self.j("resume", "--card", "UE-12").stdout
        self.assertNotIn("UNFINISHED", out)
        self.assertIn("ended", out)

    def test_checkpoint_without_next_carries_it_forward(self):
        self.j("checkpoint", "--card", "UE-12", "--note", "a", "--next", "package it")
        self.j("checkpoint", "--card", "UE-12", "--note", "b")
        self.assertEqual(self.rows()[-1][5], "package it")

    def test_no_card_is_a_usage_error(self):
        r = self.j("checkpoint", "--note", "x", check=False, cwd=self.dir)  # not a git repo, no JAM_CARD
        self.assertEqual(r.returncode, 2)
        self.assertIn("no card", r.stderr)

    def test_card_comes_from_jam_card(self):
        self.env["JAM_CARD"] = "UE-7"
        self.j("checkpoint", "--note", "x", "--next", "y")
        self.assertEqual(len(self.rows("UE-7")), 1)

    def test_unknown_card_resume_says_so(self):
        self.assertIn("no events for UE-99", self.j("resume", "--card", "UE-99").stdout)

    def test_secrets_are_redacted_everywhere(self):
        tf = os.path.join(self.dir, "tail.txt")
        with open(tf, "w") as fh:
            fh.write("\n".join(f"line {i}" for i in range(100)) + f"\ntoken {TOKEN}\n")
        self.j("step", "--card", "UE-12", "--cmd", f"export T={TOKEN}", "--exit", "0", "--tail-file", tf)
        self.j("checkpoint", "--card", "UE-12", "--note", f"used {TOKEN}", "--next", "rotate")
        with open(self.db, "rb") as fh:
            raw = fh.read()
        for suffix in ("-wal",):
            if os.path.exists(self.db + suffix):
                with open(self.db + suffix, "rb") as fh:
                    raw += fh.read()
        self.assertNotIn(TOKEN.encode(), raw)
        kind, cmd, _, tail, note, *_ = self.rows()[0]
        self.assertIn("[REDACTED:github-token]", cmd)
        self.assertIn("[REDACTED:github-token]", tail)
        self.assertEqual(len(tail.splitlines()), journal.TAIL_LINES)  # only the last 40 lines
        self.assertNotIn("line 59\n", tail + "\n")
        self.assertIn("[REDACTED:github-token]", self.rows()[1][4])

    def test_append_only(self):
        self.j("checkpoint", "--card", "UE-12", "--note", "x", "--next", "y")
        con = sqlite3.connect(self.db)
        try:
            for sql in ("UPDATE events SET note = 'changed'", "DELETE FROM events"):
                with self.assertRaises(sqlite3.DatabaseError):
                    con.execute(sql)
        finally:
            con.close()
        self.assertEqual(self.rows()[0][4], "x")

    def test_wal_mode(self):
        self.j("start", "--card", "UE-12")
        con = sqlite3.connect(self.db)
        try:
            self.assertEqual(con.execute("PRAGMA journal_mode").fetchone()[0], "wal")
        finally:
            con.close()

    def test_bad_kind_is_refused(self):
        con = journal.connect(self.db)
        try:
            with self.assertRaises(ValueError):
                journal.add(con, "UE-12", "finished")
            with self.assertRaises(sqlite3.IntegrityError):
                con.execute("INSERT INTO events (utc, card, kind) VALUES ('t', 'UE-12', 'bogus')")
        finally:
            con.close()

    def test_resume_warns_on_a_different_commit(self):
        con = journal.connect(self.db)
        try:
            journal.add(con, "UE-12", "checkpoint", note="n", next_step="x", branch="ue-12-a", commit="a" * 40)
            out = journal.resume_text(con, "UE-12", self.db, cur_commit="b" * 40, cur_branch="ue-12-a")
            self.assertIn("WARNING: current commit bbbbbbbbbbbb differs from the journaled aaaaaaaaaaaa", out)
            self.assertNotIn("current branch", out)
            same = journal.resume_text(con, "UE-12", self.db, cur_commit="a" * 40, cur_branch="ue-12-a")
            self.assertNotIn("WARNING", same)
        finally:
            con.close()


class RunTests(Base):
    def test_run_streams_and_records_exit_code(self):
        r = self.j("run", "--card", "UE-12", "--", sys.executable, "-c",
                   f"print('hello'); print('{TOKEN}'); raise SystemExit(3)", ok=(3,))
        self.assertEqual(r.returncode, 3)
        self.assertIn("hello", r.stdout)  # streamed to the terminal
        rows = self.rows()
        self.assertEqual(rows[-1][2], 3)
        self.assertIn("hello", rows[-1][3])
        self.assertIn("[REDACTED:github-token]", rows[-1][3])
        exp = self.j("export", "--card", "UE-12").stdout
        self.assertIn("| 3 |", exp)
        out = self.j("resume", "--card", "UE-12").stdout
        self.assertIn("exit=3", out)
        self.assertNotIn("INTERRUPTED", out)

    @unittest.skipUnless(hasattr(os, "killpg"), "needs process groups (Mac/Linux)")
    def test_resume_after_kill_mid_run(self):
        self.j("checkpoint", "--card", "UE-12", "--note", "before the build", "--next", "finish the build")
        child = (f"import time; print('compiling 1/3', flush=True); print('{TOKEN}', flush=True);"
                 " time.sleep(60)")
        p = subprocess.Popen([sys.executable, JOURNAL, "run", "--card", "UE-12", "--", sys.executable, "-c", child],
                             env=self.env, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True,
                             start_new_session=True)
        try:
            self.assertIn("compiling 1/3", p.stdout.readline())
            p.stdout.readline()
        finally:
            os.killpg(p.pid, signal.SIGKILL)
            p.wait(10)
            p.stdout.close()
        out = self.j("resume", "--card", "UE-12").stdout
        self.assertIn("note: before the build", out)
        self.assertIn("INTERRUPTED (never finished)", out)
        self.assertIn("compiling 1/3", out)  # the run log tail survives the kill
        self.assertNotIn(TOKEN, out)
        self.assertIn("UNFINISHED next step: finish the build", out)
        self.assertIn("| interrupted |", self.j("export", "--card", "UE-12").stdout)
        # the database is still healthy and takes new events
        self.j("step", "--card", "UE-12", "--cmd", "tools/ue/build.sh", "--exit", "0")
        con = sqlite3.connect(self.db)
        try:
            self.assertEqual(con.execute("PRAGMA integrity_check").fetchone()[0], "ok")
        finally:
            con.close()

    def test_run_without_command_is_usage_error(self):
        self.assertEqual(self.j("run", "--card", "UE-12", "--", check=False).returncode, 2)


class HookTests(Base):
    def hook(self, mode, payload=None):
        return subprocess.run([sys.executable, HOOK, mode], env=self.env, input=json.dumps(payload or {}),
                              capture_output=True, text=True, cwd=ROOT)

    def test_session_start_resumes_jam_card(self):
        self.env["JAM_CARD"] = "UE-12"
        self.j("checkpoint", "--card", "UE-12", "--note", "n", "--next", "do the thing")
        r = self.hook("session-start", {"hook_event_name": "SessionStart"})
        self.assertEqual(r.returncode, 0)
        self.assertIn("UNFINISHED next step: do the thing", r.stdout)

    def test_session_start_warns_without_jam_card(self):
        r = self.hook("session-start")
        self.assertEqual(r.returncode, 0)
        self.assertIn("WARNING: JAM_CARD is not set", r.stdout)

    def test_bash_step_success_and_failure(self):
        self.env["JAM_CARD"] = "UE-12"
        self.hook("bash", {"hook_event_name": "PostToolUse", "tool_name": "Bash",
                           "tool_input": {"command": "tools/ue/build.sh"},
                           "tool_response": {"stdout": "Build OK " + TOKEN, "stderr": ""}})
        self.hook("bash", {"hook_event_name": "PostToolUseFailure", "tool_name": "Bash",
                           "tool_input": {"command": "tools/ue/test.sh"}, "error": "Exit code 4\nFAILED"})
        self.hook("bash", {"hook_event_name": "PostToolUse", "tool_input": {"command": "python3 tools/journal.py export"}})
        rows = self.rows()
        self.assertEqual([(r[1], r[2]) for r in rows], [("tools/ue/build.sh", 0), ("tools/ue/test.sh", 4)])
        self.assertIn("[REDACTED:github-token]", rows[0][3])

    def test_stop_checkpoints_only_after_new_steps(self):
        self.env["JAM_CARD"] = "UE-12"
        self.j("checkpoint", "--card", "UE-12", "--note", "mine", "--next", "keep going")
        self.hook("stop")
        self.assertEqual(len(self.rows()), 1)  # nothing new: no checkpoint
        self.j("step", "--card", "UE-12", "--cmd", "ls", "--exit", "0")
        self.hook("stop")
        self.hook("stop")
        rows = self.rows()
        self.assertEqual([r[0] for r in rows], ["checkpoint", "step", "checkpoint"])
        self.assertEqual(rows[-1][5], "keep going")
        self.assertIn("last note: mine", rows[-1][4])

    def test_hook_never_blocks(self):
        blocker = os.path.join(self.dir, "a-file")
        open(blocker, "w").close()
        self.env["JOURNAL_DB"] = os.path.join(blocker, "sub", "journal.db")  # cannot be created
        self.env["JAM_CARD"] = "UE-12"
        self.assertEqual(self.hook("bash", {"tool_input": {"command": "ls"}}).returncode, 0)

    def test_settings_template_wires_the_journal_hooks(self):
        with open(os.path.join(ROOT, "pipeline", "agent-ops", "settings.json"), encoding="utf-8") as fh:
            hooks = json.load(fh)["hooks"]

        def cmds(event, matcher=None):
            return [h["command"] for e in hooks.get(event, []) if matcher is None or e.get("matcher") == matcher
                    for h in e["hooks"]]
        self.assertTrue(any("journal_hook.py\" session-start" in c for c in cmds("SessionStart")))
        self.assertTrue(any("journal_hook.py\" bash" in c for c in cmds("PostToolUse", "Bash")))
        self.assertTrue(any("journal_hook.py\" bash" in c for c in cmds("PostToolUseFailure", "Bash")))
        self.assertTrue(any("journal_hook.py\" stop" in c for c in cmds("Stop")))
        self.assertTrue(any("hook.py\" guard" in c for c in cmds("PreToolUse")))  # the guard is still there


@unittest.skipIf(os.name == "nt", "POSIX launcher; tools/agent.ps1 is its Windows twin")
class LauncherTests(Base):
    def test_launcher_sets_env_and_journals(self):
        r = subprocess.run(["sh", os.path.join(ROOT, "tools", "agent.sh"), "gameplay-dev", "UE-12", sys.executable,
                            "-c", "import os; print('ENV', os.environ['JAM_ROLE'], os.environ['JAM_CARD'], os.environ['JAM_HOST']); raise SystemExit(5)"],
                           env=self.env, capture_output=True, text=True, cwd=ROOT)
        self.assertEqual(r.returncode, 5, r.stderr)
        self.assertIn("ENV gameplay-dev UE-12 ", r.stdout)
        self.assertRegex(r.stdout, r"ENV gameplay-dev UE-12 \S+")  # dry run B M14: JAM_HOST is always set
        rows = self.rows()
        self.assertEqual(rows[0][0], "start")
        self.assertEqual(rows[-1][0], "checkpoint")
        self.assertIn("exited 5", rows[-1][4])

    def test_launcher_refuses_unknown_role(self):
        r = subprocess.run(["sh", os.path.join(ROOT, "tools", "agent.sh"), "wizard", "UE-12", "true"],
                           env=self.env, capture_output=True, text=True, cwd=ROOT)
        self.assertEqual(r.returncode, 2)
        self.assertIn("unknown role", r.stderr)
        self.assertFalse(os.path.exists(self.db))

    def test_launcher_needs_three_arguments(self):
        r = subprocess.run(["sh", os.path.join(ROOT, "tools", "agent.sh"), "gameplay-dev"], env=self.env,
                           capture_output=True, text=True)
        self.assertEqual(r.returncode, 2)

    def test_powershell_twin_has_same_steps(self):
        with open(os.path.join(ROOT, "tools", "agent.ps1"), encoding="utf-8") as fh:
            ps = fh.read()
        for need in ("JAM_ROLE", "JAM_CARD", "JAM_HOST", "journal.py", " start ", " resume ", " checkpoint ", "gates.json"):
            self.assertIn(need, ps)


@unittest.skipUnless(shutil.which("git") and os.name != "nt", "needs git and sh")
class GitHookTests(Base):
    def setUp(self):
        super().setUp()
        self.repo = os.path.join(self.dir, "repo")
        os.makedirs(os.path.join(self.repo, "tools"))
        for f in ("journal.py", "secrets_check.py"):
            shutil.copy(os.path.join(ROOT, "tools", f), os.path.join(self.repo, "tools", f))
        self.git("init", "-q", "-b", "main")
        self.git("config", "user.email", "t@example.com")
        self.git("config", "user.name", "t")
        self.git("config", "commit.gpgsign", "false")

    def git(self, *a):
        return subprocess.run(["git", *a], cwd=self.repo, env=self.env, capture_output=True, text=True, check=True)

    def install(self, *a):
        return subprocess.run([sys.executable, os.path.join(ROOT, "tools", "install_git_hooks.py"), "--repo", self.repo, *a],
                              capture_output=True, text=True)

    def test_post_commit_journals_each_commit(self):
        self.assertEqual(self.install().returncode, 0)
        self.assertEqual(self.install("--check").returncode, 0)
        self.git("checkout", "-q", "-b", "ue-12-umbrella")
        self.git("add", "-A")
        self.git("commit", "-q", "-m", "UE-12: first")
        rows = self.rows()
        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0][1], "git commit")
        self.assertIn("UE-12: first", rows[0][4])
        self.assertEqual(rows[0][6], "ue-12-umbrella")

    def test_commit_without_card_is_not_blocked(self):
        self.install()
        self.git("add", "-A")
        r = self.git("commit", "-q", "-m", "no card branch")
        self.assertEqual(r.returncode, 0)
        self.assertFalse(os.path.exists(self.db) and self.rows())

    def test_foreign_hook_is_left_alone(self):
        path = os.path.join(self.repo, ".git", "hooks", "post-commit")
        with open(path, "w") as fh:
            fh.write("#!/bin/sh\necho mine\n")
        self.assertEqual(self.install().returncode, 1)
        with open(path) as fh:
            self.assertIn("echo mine", fh.read())
        self.assertEqual(self.install("--check").returncode, 1)


class RunRecords(Base):
    """Run records for A/B tests: the exact prompt, the pipeline version, agent, model and GDD revision."""

    def start(self, prompt="Make the owl slower.", agent="codex", model="producer=gpt-x"):
        con = journal.connect(self.db)
        try:
            rid = journal.start_run(con, "kickoff", agent, model, prompt, "parallel=2")
            journal.add_run_prompt(con, rid, "UE-0.8", "integrator", "gpt-x", "ROLE: integrator ...\n" + prompt)
            journal.add_run_outcome(con, rid, "session", exit_code=0, card="UE-0.8")
            journal.add_run_outcome(con, rid, "end", outcome="idle", note="1 session(s)")
            return rid
        finally:
            con.close()

    def test_record_holds_prompt_version_agent_model_and_gdd(self):
        rid = self.start()
        con = journal.connect(self.db)
        try:
            run = journal.get_run(con, rid)
        finally:
            con.close()
        self.assertEqual(run["prompt"], "Make the owl slower.")
        self.assertEqual(run["prompt_sha256"], journal.sha256("Make the owl slower."))
        self.assertEqual((run["agent"], run["model"]), ("codex", "producer=gpt-x"))
        self.assertEqual(run["pipeline_commit"], journal.git("rev-parse", "HEAD", cwd=ROOT))
        self.assertTrue(run["pipeline_version"].startswith(journal.pipeline_version(ROOT)["version"] + "+"))
        self.assertTrue(run["gdd_revision"].startswith("SH1.0 (GDD-SH1.0.md sha256 "), run["gdd_revision"])
        self.assertEqual(len(run["prompts"]), 1)

    def test_runs_are_append_only_and_secrets_redacted(self):
        rid = self.start(prompt="use " + TOKEN)
        con = sqlite3.connect(self.db)
        try:
            self.assertNotIn(TOKEN, con.execute("SELECT prompt FROM runs").fetchone()[0])
            for sql in ("UPDATE runs SET agent = 'x'", "DELETE FROM runs", "DELETE FROM run_prompts",
                        "UPDATE run_outcomes SET outcome = 'pass'"):
                with self.subTest(sql=sql), self.assertRaises(sqlite3.DatabaseError):
                    con.execute(sql)
        finally:
            con.close()
        self.assertTrue(rid)

    def test_compare_same_and_different_inputs(self):
        a, b = self.start(), self.start()
        self.j("run-outcome", "--run", str(b), "--outcome", "fail", "--note", "owl clipped the clock")
        out = self.j("compare", str(a), str(b)).stdout
        self.assertIn(f"compare run {a} vs run {b}", out)
        self.assertRegex(out, r"pipeline version\s+\|.*\| yes")
        self.assertRegex(out, r"tester prompt sha256\s+\|.*\| yes")
        self.assertIn("fail (tester: owl clipped the clock)", out)
        self.assertIn("an A/B of luck alone", out)
        # broken on purpose: a different prompt and agent are not a like-for-like A/B
        c = self.start(prompt="Make the owl faster.", agent="claude")
        out = self.j("compare", str(a), str(c)).stdout
        self.assertRegex(out, r"tester prompt sha256\s+\|.*\| NO")
        self.assertRegex(out, r"agent\s+\|.*\| NO")
        self.assertIn("inputs differ", out)
        self.assertEqual(self.j("compare", str(a), "999", ok=(2,)).returncode, 2)
        self.assertEqual(self.j("run-outcome", "--run", "999", "--outcome", "pass", ok=(2,)).returncode, 2)
        self.assertIn(f"{c} | ", self.j("runs").stdout)

    def test_version_command(self):
        out = self.j("version").stdout.strip()
        self.assertRegex(out, r"^pipeline \d[\w.]*\+[0-9a-f]{7}(-dirty)?$")


if __name__ == "__main__":
    unittest.main()
