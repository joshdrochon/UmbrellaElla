"""visualqa item 3 (lead order Nov 13 21:49, Josh's mouse lag): offscreen captures run at t.MaxFPS 30, and a 30 fps
capture still scores like an uncapped one (pipeline/qa/visual/noise/fps30-cc2a51b4.json, the same tip both ways)."""
import json
import os
import stat
import subprocess
import sys
import tempfile
import unittest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "tools", "build"))
import visual_qa  # noqa: E402

RUN_GAME = os.path.join(ROOT, "tools", "build", "run_game.sh")
FIXTURE = os.path.join(ROOT, "pipeline", "qa", "visual", "noise", "fps30-cc2a51b4.json")
CAP_ARG = "-ini:Engine:[ConsoleVariables]:t.MaxFPS=30"


def launch_args(env_extra):
    """The editor arguments run_game.sh passes, with a stub editor that prints them (no engine, no slot)."""
    with tempfile.TemporaryDirectory() as ue:
        exe_dir = os.path.join(ue, "Engine", "Binaries", "Mac", "UnrealEditor.app", "Contents", "MacOS")
        os.makedirs(exe_dir)
        exe = os.path.join(exe_dir, "UnrealEditor")
        with open(exe, "w") as fh:
            fh.write('#!/bin/sh\nfor a in "$@"; do echo "ARG $a"; done\n')
        os.chmod(exe, os.stat(exe).st_mode | stat.S_IEXEC)
        env = dict(os.environ, UE_ROOT=ue, UE_SLOT_HELD="1", RUN_STALE_OK="1")
        env.pop("RUN_RES", None)
        env.pop("RUN_MAXFPS", None)
        env.update(env_extra)
        out = subprocess.run(["bash", RUN_GAME], env=env, capture_output=True, text=True).stdout
    return [line[4:] for line in out.splitlines() if line.startswith("ARG ")]


class CaptureFrameCap(unittest.TestCase):
    def test_offscreen_capture_is_capped_at_30(self):
        self.assertIn(CAP_ARG, launch_args({"RUN_RES": "1280x720"}))

    def test_cap_can_be_lifted_or_changed(self):
        self.assertFalse(any("t.MaxFPS" in a for a in launch_args({"RUN_RES": "1280x720", "RUN_MAXFPS": "0"})))
        self.assertIn("-ini:Engine:[ConsoleVariables]:t.MaxFPS=20", launch_args({"RUN_RES": "1280x720", "RUN_MAXFPS": "20"}))

    def test_small_window_runs_unchanged(self):
        # The 640x360 window path (playtests) keeps its old arguments.
        self.assertFalse(any("t.MaxFPS" in a for a in launch_args({})))


class CappedScoresMatch(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        with open(FIXTURE, encoding="utf-8") as fh:
            cls.d = json.load(fh)

    def test_gate_rule_passes_capped_pair_against_uncapped(self):
        # The gate's own rule (two captures, a regression must show in both) with the uncapped run as 'main'.
        for screen, base in self.d["uncapped"].items():
            ok, reasons = visual_qa.confirm_gate(self.d["capped_first"][screen], self.d["capped_recheck"][screen], base)
            self.assertTrue(ok, "%s: %s" % (screen, reasons))

    def test_recapture_totals_within_judge_noise(self):
        # Measured judge noise on one frame: up to 3.5 under its median (GATE_TOTAL_SLACK 4).
        for screen, base in self.d["uncapped"].items():
            self.assertLessEqual(abs(self.d["capped_recheck"][screen]["total"] - base["total"]), visual_qa.GATE_TOTAL_SLACK, screen)

    def test_the_low_capture_was_content_not_frame_rate(self):
        # The one low capped total (play 24) is the capture that had the Keeper's salmon gust band mid-frame.
        first = self.d["capped_first"]["play"]
        self.assertTrue(any("salmon" in b for b in first["broken"]))
        self.assertFalse(any("salmon" in b for b in self.d["capped_recheck"]["play"]["broken"]))


if __name__ == "__main__":
    unittest.main()
