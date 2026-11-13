"""Ported from the pipeline's tests/test_build_gate.py (1ef10dc, 7fda47b): the two fixes UmbrellaElla's gate copies lacked."""
import os, sys, unittest
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


class FlowCheckStopsPackaging(unittest.TestCase):
    def test_flow_check_uses_its_own_exit_code(self):
        body = open(os.path.join(ROOT, "tools", "build", "prepackage.sh")).read()
        self.assertIn("ui_check.py flow-check", body)
        self.assertIn("[ $rc = 0 ] || fail=1", body)
        self.assertNotIn('"$SLOG" | tail -2 || fail=1', body)


if __name__ == "__main__":
    unittest.main()
