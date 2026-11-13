import os, subprocess, sys, tempfile, unittest

TOOL = os.path.join(os.path.dirname(__file__), "..", "tools", "build", "gate_seen.py")


def run(*a):
    return subprocess.run([sys.executable, TOOL, *a], capture_output=True, text=True)


class GateSeen(unittest.TestCase):
    def test_held_head_is_refused_until_new_commits(self):
        with tempfile.TemporaryDirectory() as d:
            self.assertEqual(run("check", d, "lane", "aaa").returncode, 0)
            self.assertEqual(run("record", d, "lane", "aaa", "HOLD").returncode, 0)
            r = run("check", d, "lane", "aaa")
            self.assertEqual(r.returncode, 4)
            self.assertIn("GATE REFUSE", r.stdout)
            self.assertEqual(run("check", d, "lane", "bbb").returncode, 0)   # a new head is gated again

    def test_failed_head_is_refused_and_lanes_are_separate(self):
        with tempfile.TemporaryDirectory() as d:
            run("record", d, "one", "ccc", "FAIL")
            self.assertEqual(run("check", d, "one", "ccc").returncode, 4)
            self.assertEqual(run("check", d, "two", "ccc").returncode, 0)

    def test_bad_verdict_rejected(self):
        with tempfile.TemporaryDirectory() as d:
            self.assertEqual(run("record", d, "lane", "aaa", "PASS").returncode, 2)


if __name__ == "__main__":
    unittest.main()
