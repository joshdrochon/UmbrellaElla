"""lane_precheck.sh finds the areas folder from a lane worktree's own copy, not only from the main checkout (Nov 13)."""
import os, shutil, subprocess, tempfile, time, unittest

HERE = os.path.dirname(os.path.abspath(__file__))
SCRIPT = os.path.join(HERE, "..", "tools", "build", "lane_precheck.sh")


def git(cwd, *a):
    subprocess.run(["git", *a], cwd=cwd, check=True, capture_output=True)


class LanePrecheckPaths(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.mkdtemp()
        self.addCleanup(shutil.rmtree, self.tmp, True)
        self.main = os.path.join(self.tmp, "UmbrellaElla")
        self.areas = os.path.join(self.tmp, "UmbrellaElla-areas")
        os.makedirs(os.path.join(self.main, "tools", "build"))
        os.makedirs(os.path.join(self.areas, "logs"))
        shutil.copy(SCRIPT, os.path.join(self.main, "tools", "build", "lane_precheck.sh"))
        git(self.main, "init", "-q", "-b", "main")
        git(self.main, "add", "-A")
        git(self.main, "-c", "user.name=t", "-c", "user.email=t@t", "commit", "-q", "-m", "init")
        self.wt = os.path.join(self.areas, "lane")
        git(self.main, "worktree", "add", "-q", "-b", "area/lane", self.wt)

    def run_copy(self, root, *args):
        return subprocess.run(["bash", os.path.join(root, "tools", "build", "lane_precheck.sh"), "lane", *args],
                              cwd=root, capture_output=True, text=True, env={**os.environ, "PRECHECK_FAST": "1"})

    def test_worktree_copy_finds_the_lane(self):
        r = self.run_copy(self.wt)
        self.assertIn("PRECHECK", r.stdout)
        self.assertNotIn("no worktree", r.stdout)

    def test_main_copy_finds_the_lane(self):
        r = self.run_copy(self.main)
        self.assertNotIn("no worktree", r.stdout)

    def test_background_mode_writes_a_result_file(self):
        r = self.run_copy(self.wt, "--bg")
        self.assertIn("poll", r.stdout)
        res = os.path.join(self.areas, "logs", "precheck-lane.result")
        for _ in range(600):
            if os.path.exists(res) and open(res).readline().startswith("PRECHECK"):
                break
            time.sleep(0.1)
        self.assertTrue(open(res).readline().startswith("PRECHECK"))


if __name__ == "__main__":
    unittest.main()
