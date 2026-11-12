"""tools/kickoff.py for a first-timer: no options = version, connection check, then start with the agent found.
Every failure is one plain line that says what to type next. Run records for A/B tests. Each case has a pair
broken on purpose."""
import os
import shutil
import sqlite3
import subprocess
import sys
import tempfile
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.join(HERE, "fixtures", "kickoff"))
sys.path.insert(0, os.path.join(ROOT, "tools"))
import kickoff  # noqa: E402
import kickoff_sandbox as ks  # noqa: E402
import stubbins  # noqa: E402
import test_honest_jam as thj  # noqa: E402  the filled People table

AFTER_START = "2026-11-12T15:00Z"


def one_line(test, out):
    lines = [ln for ln in out.strip().splitlines() if ln.strip()]
    test.assertEqual(len(lines), 1, out)
    test.assertNotIn("Traceback", out)
    return lines[0]


@unittest.skipIf(shutil.which("git") is None, "needs git")
class NoFlags(unittest.TestCase):
    def setUp(self):
        self.sb = ks.KickoffSandbox(thj.PEOPLE)
        self.addCleanup(self.sb.close)
        self.bin = os.path.join(self.sb.base, "bin")

    def path(self, skip=()):
        shutil.rmtree(self.bin, ignore_errors=True)
        shutil.rmtree(self.bin + "-sys", ignore_errors=True)
        stubbins.make(self.bin, skip=skip)
        if os.name != "nt":   # Windows: system_path keeps the host PATH (git, python) minus the hidden programs
            os.symlink(shutil.which("git"), os.path.join(self.bin, "git"))
            os.symlink(sys.executable, os.path.join(self.bin, "python3"))
        return os.pathsep.join([self.bin, stubbins.system_path(self.bin + "-sys", hide=skip)])

    def test_only_codex_installed_checks_then_starts(self):
        rc, out = self.sb.kickoff(PATH=self.path(skip=("claude",)), KICKOFF_SKIP_CHECK="0")
        self.assertEqual(rc, 3, out)                     # pre-jam, not practice: it got past the check to the D39 line
        lines = out.strip().splitlines()
        self.assertRegex(lines[0], r"^kickoff: pipeline \d[\w.]*\+[0-9a-f]{7}(-dirty)? \| GDD SH1\.0 ")
        self.assertIn("kickoff: using codex (the only agent installed)", out)
        self.assertIn("CONNECTED Codex CLI", out)       # the full connection check ran
        self.assertIn("--practice", lines[-1])
        self.assertNotIn(kickoff.QUESTION.strip(), out)
        rc, out = self.sb.kickoff(PATH=self.path(skip=("claude",)), KICKOFF_SKIP_CHECK="0", KICKOFF_NOW=AFTER_START,
                                  STUB_DAY0_ONLY="0.2")
        self.assertEqual(rc, 0, "after the jam start the same no-option run goes ahead\n" + out)
        self.assertIn("RUN #", out)

    def test_both_installed_asks_one_question(self):
        rc, out = self.sb.kickoff(PATH=self.path(), KICKOFF_SKIP_CHECK="0", stdin_text="codex\n")
        self.assertEqual(rc, 3, out)
        self.assertIn(kickoff.QUESTION.strip(), out)
        self.assertIn("SKIPPED Claude Code CLI", out)   # the answer picked codex
        # broken on purpose: no usable answer is one line with the two commands to type
        rc, out = self.sb.kickoff(PATH=self.path(), KICKOFF_SKIP_CHECK="0", stdin_text="maybe\n")
        self.assertEqual(rc, 2, out)
        self.assertIn(f"{kickoff.me()} --agent codex", out.strip().splitlines()[-1])

    def test_neither_installed(self):
        rc, out = self.sb.kickoff(PATH=self.path(skip=("claude", "codex")))
        self.assertEqual(rc, 2, out)
        line = out.strip().splitlines()[-1]
        self.assertIn("npm install -g @openai/codex", line)
        self.assertIn(f"then run {kickoff.me()} again", line)

    def test_missing_connection_is_named_with_the_next_step(self):
        if os.name == "nt":
            # git for Windows runs git-lfs from its own install folder, so no PATH hides it: a read-only GitHub login is
            # the required item missing instead
            rc, out = self.sb.kickoff(PATH=self.path(skip=("claude",)), KICKOFF_SKIP_CHECK="0",
                                      FAKE_GH_PERMISSION="READ")
        else:
            rc, out = self.sb.kickoff(PATH=self.path(skip=("claude", "git-lfs")), KICKOFF_SKIP_CHECK="0")
        self.assertEqual(rc, 4, out)
        self.assertIn("NOT CONNECTED", out)
        self.assertIn(f"then run {kickoff.me()} again", out.strip().splitlines()[-1])


@unittest.skipIf(shutil.which("git") is None, "needs git")
class PlainErrors(unittest.TestCase):
    def setUp(self):
        self.sb = ks.KickoffSandbox(thj.PEOPLE)
        self.addCleanup(self.sb.close)

    def test_bad_option(self):
        rc, out = self.sb.kickoff("--agnet", "codex")
        self.assertEqual(rc, 2)
        self.assertIn(f"Type {kickoff.me()} with no options", one_line(self, out))

    def test_inside_an_agent_session(self):
        rc, out = self.sb.kickoff("--agent", "codex", CLAUDECODE="1")
        self.assertEqual(rc, 2)
        self.assertIn("Open a new plain terminal window", one_line(self, out))

    def test_missing_prompt_file(self):
        rc, out = self.sb.kickoff("--agent", "codex", "--prompt-file", "nope.txt")
        self.assertEqual(rc, 2)
        self.assertIn("cannot read the prompt file nope.txt", one_line(self, out))

    def test_practice_on_a_branch(self):
        self.sb.git("checkout", "-q", "-b", "side")
        rc, out = self.sb.kickoff("--agent", "codex", "--practice")
        self.assertEqual(rc, 2)
        self.assertIn("git checkout main", one_line(self, out))

    def test_unexpected_error_is_one_line(self):
        rc, out = self.sb.kickoff("--agent", "codex", KICKOFF_NOW="not-a-time")
        self.assertEqual(rc, 2)
        self.assertIn(f"{kickoff.me()} --check", one_line(self, out))
        rc, out = self.sb.kickoff("--agent", "codex", KICKOFF_NOW="not-a-time", KICKOFF_DEBUG="1")
        self.assertIn("Traceback", out)   # the debug switch shows it, for whoever fixes the pipeline

    def test_pipeline_not_installed(self):
        agents = os.path.join(self.sb.repo, "AGENTS.md")
        with open(agents, encoding="utf-8") as fh:
            text = fh.read()
        with open(agents, "w", encoding="utf-8") as fh:
            fh.write(text.replace(kickoff.AGENTS_SECTION, "Other"))
        rc, out = self.sb.kickoff("--agent", "codex")
        self.assertEqual(rc, 2)
        line = one_line(self, out)
        self.assertIn("not fully installed", line)
        self.assertIn("git pull origin main", line)
        with open(agents, "w", encoding="utf-8") as fh:
            fh.write(text)
        os.remove(os.path.join(self.sb.repo, "tools", "connections.py"))
        rc, out = self.sb.kickoff("--agent", "codex")
        self.assertIn("tools/connections.py", one_line(self, out))

    def test_check_prints_the_version_first(self):
        rc, out = self.sb.kickoff("--agent", "codex", "--check")
        self.assertRegex(out.splitlines()[0], r"^kickoff: pipeline \S+ \| GDD SH1\.0 .*\| agent codex$")
        self.assertRegex(out.splitlines()[1], r"^kickoff: team art: \d+ image\(s\) from Assets/, Mockups/ on the art "
                                              r"references")

    def test_check_counts_team_art_and_fails_on_an_unreadable_image(self):
        sys.path.insert(0, os.path.join(ROOT, "tools"))
        from png import write_png
        rows = [[(30 + x, 20, 10 + y, 255) for x in range(16)] for y in range(16)]
        for rel in ("Assets/Team Drop/new-idea.png", "Assets/Old - obsolete/old.png"):
            os.makedirs(os.path.dirname(os.path.join(self.sb.repo, rel)), exist_ok=True)
            write_png(os.path.join(self.sb.repo, rel), 16, 16, rows)
        rc, out = self.sb.kickoff("--agent", "codex", "--check")
        line = next(ln for ln in out.splitlines() if ln.startswith("kickoff: team art:"))
        self.assertIn("1 joined automatically", line)
        self.assertIn("1 in obsolete folders skipped", line)
        # broken on purpose: a file that is not the picture its name says fails the check, by name
        with open(os.path.join(self.sb.repo, "Assets/Team Drop/broken.png"), "wb") as fh:
            fh.write(b"not a png")
        rc, out = self.sb.kickoff("--agent", "codex", "--check")
        self.assertNotEqual(rc, 0, out)
        self.assertIn("kickoff: team art: FAIL 1 image(s) cannot be read (Assets/Team Drop/broken.png)", out)
        self.assertIn("kickoff: team art Assets/Team Drop/broken.png cannot be read (not a PNG", out)

    def test_wrapper_without_kickoff_py(self):
        d = tempfile.mkdtemp()
        self.addCleanup(shutil.rmtree, d, True)
        shutil.copy(os.path.join(ROOT, "tools", "kickoff.sh"), d)
        p = subprocess.run(["sh", os.path.join(d, "kickoff.sh")], capture_output=True, text=True)
        self.assertEqual(p.returncode, 2)
        self.assertIn("git pull origin main", one_line(self, p.stdout + p.stderr))


class InstallProblem(unittest.TestCase):
    def test_not_a_repo_and_not_at_the_root(self):
        d = tempfile.mkdtemp()
        self.addCleanup(shutil.rmtree, d, True)
        self.assertIn("git clone", kickoff.install_problem(d))
        subprocess.run(["git", "init", "-q", d], check=True)
        sub = os.path.join(d, "pipeline-copy")
        os.makedirs(sub)
        line = kickoff.install_problem(sub)
        self.assertIn("must sit at the repo root", line)
        self.assertIn("robocopy" if os.name == "nt" else "cp -R", line)
        self.assertIsNone(kickoff.install_problem(ROOT))


@unittest.skipIf(shutil.which("git") is None, "needs git")
class RunRecord(unittest.TestCase):
    def test_practice_run_records_prompt_version_agent_model_gdd(self):
        sb = ks.KickoffSandbox(thj.PEOPLE)
        self.addCleanup(sb.close)
        rc, out = sb.kickoff("--agent", "claude", "--practice", "--prompt", "Keep the owl slow.",
                             STUB_DAY0_ONLY="0.7")
        self.assertEqual(rc, 0, out)
        self.assertIn("RUN #1: pipeline ", out)
        con = sqlite3.connect(os.path.join(sb.base, "journal.db"))
        try:
            kind, agent, model, ver, commit, gdd, prompt = con.execute(
                "SELECT kind, agent, model, pipeline_version, pipeline_commit, gdd_revision, prompt FROM runs").fetchone()
            prompts = [r[0] for r in con.execute("SELECT prompt FROM run_prompts WHERE run_id = 1")]
            outs = [r[0] for r in con.execute("SELECT kind FROM run_outcomes WHERE run_id = 1")]
        finally:
            con.close()
        self.assertEqual((kind, agent, prompt), ("practice", "claude", "Keep the owl slow."))
        self.assertIn("producer=claude-", model)
        self.assertEqual(commit[:7], ver.split("+")[1][:7])
        self.assertTrue(gdd.startswith("SH1.0 "))
        self.assertTrue(prompts and all("Tester prompt for this run" in p and "Keep the owl slow." in p
                                        for p in prompts), prompts)
        self.assertIn("session", outs)
        self.assertEqual(outs[-1], "end")


if __name__ == "__main__":
    unittest.main()
