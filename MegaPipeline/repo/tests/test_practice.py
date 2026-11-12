"""Practice mode (tools/practice.py): the .pipeline-practice marker lifts D39 in a test repo and hard-blocks the
submission, uploads and G4; on the team repo (origin RickTheBuilder/GameJam2026) it turns CI red. Each check has a
passing case and a case broken on purpose."""
import contextlib
import io
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
import check_card  # noqa: E402
import pipeline_check  # noqa: E402
import practice  # noqa: E402
import submission_check  # noqa: E402

PY = sys.executable
REAL = "https://github.com/RickTheBuilder/GameJam2026.git"


def repo(origin, marker):
    d = tempfile.mkdtemp()
    os.makedirs(os.path.join(d, "pipeline", "agent-ops"))
    shutil.copy(os.path.join(ROOT, "pipeline", "agent-ops", "gates.json"), os.path.join(d, "pipeline", "agent-ops"))
    subprocess.run(["git", "init", "-q", d], check=True)
    subprocess.run(["git", "-C", d, "remote", "add", "origin", origin], check=True)
    if marker:
        with open(os.path.join(d, practice.MARKER), "w") as fh:
            fh.write(practice.MARKER_TEXT)
    return d


class MarkerOnTheRealRepo(unittest.TestCase):
    def tearDown(self):
        for d in getattr(self, "dirs", []):
            shutil.rmtree(d, ignore_errors=True)

    def mk(self, origin, marker):
        d = repo(origin, marker)
        self.dirs = getattr(self, "dirs", []) + [d]
        return d

    def test_ci_fails_on_the_real_repo(self):
        env = {k: v for k, v in os.environ.items() if k != "GITHUB_REPOSITORY"}
        got = pipeline_check.practice_problems(self.mk(REAL, True))
        self.assertTrue(got and "team repo" in got[0][2], got)
        self.assertTrue(practice.marker_problems(self.mk("https://github.com/someone/practice-jam", True),
                                                 env=dict(env, GITHUB_REPOSITORY="RickTheBuilder/GameJam2026")),
                        "CI on the real repo sets GITHUB_REPOSITORY even when origin differs")

    def test_practice_repo_and_clean_real_repo_pass(self):
        env = {k: v for k, v in os.environ.items() if k != "GITHUB_REPOSITORY"}
        self.assertEqual(practice.marker_problems(self.mk("git@github.com:someone/jam-test.git", True), env=env), [])
        self.assertEqual(practice.marker_problems(self.mk(REAL, False), env=env), [])

    def test_slug_parser(self):
        self.assertEqual(practice.slug_of("git@github.com:RickTheBuilder/GameJam2026.git"), "rickthebuilder/gamejam2026")
        self.assertEqual(practice.slug_of(REAL), "rickthebuilder/gamejam2026")
        self.assertEqual(practice.slug_of("/tmp/origin.git"), "")

    def test_release_check_blocked_in_practice(self):
        d = self.mk("https://github.com/someone/jam-test", True)
        self.assertTrue(pipeline_check.practice_problems(d, release=True))
        self.assertEqual(pipeline_check.practice_problems(d, release=False), [])


class SubmissionBlocked(unittest.TestCase):
    def setUp(self):
        self.marker = os.path.join(ROOT, practice.MARKER)
        self.assertFalse(os.path.exists(self.marker), "the real repo never carries the marker")

    def run_main(self, args):
        buf = io.StringIO()
        with contextlib.redirect_stdout(buf):
            rc = submission_check.main(args)
        return rc, buf.getvalue()

    def with_marker(self):
        with open(self.marker, "w") as fh:
            fh.write(practice.MARKER_TEXT)
        self.addCleanup(os.remove, self.marker)

    def test_submission_checks_blocked_in_practice(self):
        self.with_marker()
        for args in (["zip", "x.zip"], ["zip", "x.zip", "--gate", "G4"], ["signoff", "CONTENT teen=yes"],
                     ["page"], ["declaration"], ["files", "--final"], ["devlog", "--day", "4", "--published"]):
            with self.subTest(args=args):
                rc, out = self.run_main(args)
                self.assertEqual(rc, 1)
                self.assertIn("PRACTICE:", out)

    def test_broken_on_purpose_same_commands_run_without_the_marker(self):
        rc, out = self.run_main(["zip", "missing.zip"])
        self.assertEqual(rc, 2, out)            # not blocked: it looked for the zip
        self.assertNotIn("PRACTICE", out)

    def test_gate_zips_and_measurements_still_run_in_practice(self):
        self.with_marker()
        for args in (["zip", "missing.zip", "--gate", "G1"], ["video", "missing.mp4"]):
            rc, out = self.run_main(args)
            self.assertNotIn("PRACTICE", out, args)

    def test_g4_record_fails_in_practice_only(self):
        rec = "Gate: G4 due 2026-11-15T12:00-08:00\n"
        self.assertFalse(any("PRACTICE" in p for p in check_card.gate_record_problems(rec)))
        self.with_marker()
        self.assertTrue(any("PRACTICE" in p for p in check_card.gate_record_problems(rec)))

    def test_assets_date_rule_lifted_in_practice(self):
        head = "asset_path,author,origin,tool,model_version,prompt,seed,input_images,date,licence,attribution\n"
        row = head + "Art/Sprites/a.png,Asset Specialist,made,Aseprite,,,,,2026-11-09,team,none\n"
        self.assertTrue(submission_check.assets_problems(row, "", ROOT))
        self.assertEqual(submission_check.assets_problems(row, "", ROOT, start=None), [])


class ButlerAndBoard(unittest.TestCase):
    def test_hook_blocks_every_butler_call_in_practice(self):
        proj = tempfile.mkdtemp()
        self.addCleanup(shutil.rmtree, proj, True)
        payload = {"hook_event_name": "PreToolUse", "tool_name": "Bash", "cwd": proj, "session_id": "t",
                   "tool_input": {"command": "butler status team/game"}}
        env = dict(os.environ, JAM_ROLE="qa-build", AGENT_OPS_PLATFORM="linux", CLAUDE_PROJECT_DIR=proj)
        hook = os.path.join(ROOT, "pipeline", "agent-ops", "hook.py")
        run = lambda: subprocess.run([PY, hook, "guard"], input=json.dumps(payload), capture_output=True, text=True,
                                     env=env)
        self.assertEqual(run().returncode, 0, "broken on purpose: outside practice `butler status` is allowed")
        open(os.path.join(proj, practice.MARKER), "w").close()
        r = run()
        self.assertEqual(r.returncode, 2)
        self.assertIn("Practice repo", r.stderr)

    def test_status_board_shows_practice(self):
        import status_board
        d = tempfile.mkdtemp()
        self.addCleanup(shutil.rmtree, d, True)
        os.makedirs(os.path.join(d, "pipeline", "templates"))
        os.makedirs(os.path.join(d, "docs"))
        shutil.copy(os.path.join(ROOT, "pipeline", "templates", "task-card.md"), os.path.join(d, "pipeline", "templates"))
        shutil.copy(os.path.join(ROOT, "tests", "fixtures", "status_board", "jam-brief.md"), os.path.join(d, "docs"))
        now = check_card.parse_time("2026-11-13T15:00-08:00")
        md, _, summary = status_board.build(d, now, "test")
        self.assertNotIn("PRACTICE", md)
        open(os.path.join(d, practice.MARKER), "w").close()
        md, _, summary = status_board.build(d, now, "test")
        self.assertIn("**PRACTICE** repo", md)
        self.assertTrue(summary.startswith("PRACTICE "))


if __name__ == "__main__":
    unittest.main()
