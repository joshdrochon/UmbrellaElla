"""Tests for tools/ue_slot.py: at most UE_SLOTS engine runs at once on a machine, however many sessions run.
Broken on purpose: a slot that is never taken (all run at once), a dead owner that blocks forever."""
import os
import shutil
import subprocess
import sys
import tempfile
import time
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
SLOT = os.path.join(ROOT, "tools", "ue_slot.py")
JOB = "import sys,time; open(sys.argv[1],'a').write('%f %f\\n' % (time.time(), (time.sleep(1.5), time.time())[1]))"


class Slots(unittest.TestCase):
    def setUp(self):
        self.d = tempfile.mkdtemp(prefix="ueslot-")
        self.addCleanup(shutil.rmtree, self.d, True)
        self.log = os.path.join(self.d, "spans")
        self.env = dict(os.environ, UE_SLOT_DIR=os.path.join(self.d, "slots"), UE_SLOT_POLL="0.2")
        self.env.pop("UE_SLOT_HELD", None)

    def run_many(self, n, **env):
        procs = [subprocess.Popen([sys.executable, SLOT, "run", "--", sys.executable, "-c", JOB, self.log],
                                  env=dict(self.env, **env), stderr=subprocess.DEVNULL) for _ in range(n)]
        for p in procs:
            self.assertEqual(p.wait(timeout=60), 0)
        with open(self.log) as fh:
            spans = [tuple(map(float, ln.split())) for ln in fh if ln.strip()]
        return max(sum(1 for a, b in spans if a <= t < b) for t, _ in spans)

    def test_two_slots_cap_four_runs_at_two(self):
        self.assertEqual(self.run_many(4, UE_SLOTS="2"), 2)

    def test_slots_off_runs_all_at_once(self):
        self.assertEqual(self.run_many(3, UE_SLOTS="0"), 3)

    def test_held_slot_never_waits_for_a_second(self):
        self.assertEqual(self.run_many(2, UE_SLOTS="1", UE_SLOT_HELD="/x"), 2)

    def test_dead_owner_is_taken_over(self):
        slots = os.path.join(self.d, "slots", "slot1")
        os.makedirs(slots)
        p = subprocess.Popen([sys.executable, "-c", "pass"])
        p.wait()
        with open(os.path.join(slots, "owner"), "w") as fh:
            fh.write(f"{p.pid} /gone\n")
        old = time.time() - 60
        os.utime(slots, (old, old))
        start = time.time()
        self.assertEqual(self.run_many(1, UE_SLOTS="1"), 1)
        self.assertLess(time.time() - start, 20)


if __name__ == "__main__":
    unittest.main()
