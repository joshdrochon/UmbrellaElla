"""Ported from the pipeline's tests/test_build_gate.py (1ef10dc, 7fda47b): the two fixes UmbrellaElla's gate copies lacked."""
import os, subprocess, sys, tempfile, unittest
ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, os.path.join(ROOT, "tools", "build"))
import quality_gate


class PipelineCheckCanBlock(unittest.TestCase):
    def test_pipeline_check_problems_count_as_fail_lines(self):
        """pipeline_check prints `[kind] where: what`, never FAIL; with the FAIL pattern it could never block."""
        lines = ["[consistency] docs/x.md:3: path y does not exist", "lfs: 1 file(s)", "pipeline_check: 1 problem(s)"]
        self.assertEqual(quality_gate.fails(lines, quality_gate.FAIL_LINES["pipeline_check"]),
                         {"[consistency] docs/x.md: path y does not exist"})
        self.assertEqual(quality_gate.fails(lines), set())

    def test_pipeline_check_is_blocking(self):
        self.assertIn("pipeline_check", quality_gate.BLOCKING)


class NewCheckBaseline(unittest.TestCase):
    """A check main does not have yet: fails already in the game when it lands are not new; fails added by the merge are."""
    def git(self, d, *a):
        subprocess.run(["git", "-c", "user.name=t", "-c", "user.email=t@t", "-c", "core.hooksPath=/dev/null", *a], cwd=d, check=True, capture_output=True)

    def test_baseline_is_main_game_files_under_the_new_script(self):
        script = "import os\nfor l in open('Source/game.txt').read().split():\n    print('FAIL ' + l)\n"
        with tempfile.TemporaryDirectory() as d:
            for sub in ("tools", "docs", "tests", "Source", "Config"):
                os.makedirs(os.path.join(d, sub))
                open(os.path.join(d, sub, ".keep"), "w").close()
            open(os.path.join(d, "Source", "game.txt"), "w").write("old1 old2")
            self.git(d, "init", "-q"); self.git(d, "add", "-A"); self.git(d, "commit", "-qm", "main")
            base = subprocess.run(["git", "rev-parse", "HEAD"], cwd=d, capture_output=True, text=True).stdout.strip()
            open(os.path.join(d, "tools", "newcheck.py"), "w").write(script)
            open(os.path.join(d, "Source", "game.txt"), "w").write("old1 old2 added")
            self.git(d, "add", "-A"); self.git(d, "commit", "-qm", "merge")
            saved = (quality_gate.ROOT, dict(quality_gate.BLOCKING))
            quality_gate.ROOT, quality_gate.BLOCKING = d, {"newcheck": ["tools/newcheck.py"]}
            try:
                before = quality_gate.baseline_for_new_checks(base)["newcheck"]
                now = quality_gate.blocking_lines()["newcheck"]
            finally:
                quality_gate.ROOT, quality_gate.BLOCKING = saved[0], saved[1]
            self.assertEqual(before, {"FAIL old1", "FAIL old2"})
            self.assertEqual(sorted(now - before), ["FAIL added"])

    def test_gdd_check_is_blocking(self):
        self.assertIn("gdd_check", quality_gate.BLOCKING)


class FlowCheckStopsPackaging(unittest.TestCase):
    def test_flow_check_uses_its_own_exit_code(self):
        body = open(os.path.join(ROOT, "tools", "build", "prepackage.sh")).read()
        self.assertIn("ui_check.py flow-check", body)
        self.assertIn("[ $rc = 0 ] || fail=1", body)
        self.assertNotIn('"$SLOG" | tail -2 || fail=1', body)


if __name__ == "__main__":
    unittest.main()
