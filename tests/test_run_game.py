"""tools/build/run_game.sh: every run keeps its own game log, refuses a stale editor module, and frame-checks its shot.

Why (screenfix, Nov 13): artella's capture came back black with only the HUD; the checkout had merged main but never
rebuilt, so the game ran the old 5 s shot, and the Mac editor's one shared rotating log left nothing to triage.
The editor here is a fake script, so the test runs without Unreal."""
import os
import shutil
import subprocess
import sys
import tempfile
import time
import unittest
from pathlib import Path

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(HERE)
sys.path.insert(0, os.path.join(REPO, "tools"))
from png import write_png  # noqa: E402

FAKE_EDITOR = """#!/usr/bin/env bash
cd "$(dirname "$1")"   # like the game: a relative -SmokeShot resolves against the project dir
LOG=""; SHOT=""
for a in "$@"; do case "$a" in -abslog=*) LOG="${a#-abslog=}";; -SmokeShot=*) SHOT="${a#-SmokeShot=}";; esac; done
echo "[0]LogUmbrellaElla: SMOKE_SHOT at_s=1.0 frames=30 w=160 h=90" > "$LOG"
echo "[0]LogUmbrellaElla: SMOKE_VIEW ella_in_frame=1 arena_in_frame=1" >> "$LOG"
echo "[0]LogUmbrellaElla: ARGS $*" >> "$LOG"
[ -n "$SHOT" ] && cp "$FAKE_SHOT_SRC" "$SHOT"
exit 0
"""


def frame_rows(w, h, fill, box=None):
    rows = [[fill + (255,) for _ in range(w)] for _ in range(h)]
    if box:
        x0, y0, x1, y1, c = box
        for y in range(y0, y1):
            for x in range(x0, x1):
                rows[y][x] = c + (255,)
    return rows


class RunGameTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.mkdtemp()
        self.root = os.path.join(self.tmp, "proj")
        os.makedirs(os.path.join(self.root, "tools", "build"))
        shutil.copy(os.path.join(REPO, "tools", "build", "run_game.sh"), os.path.join(self.root, "tools", "build"))
        for name in ("frame_check.py", "png.py"):
            shutil.copy(os.path.join(REPO, "tools", name), os.path.join(self.root, "tools"))
        os.makedirs(os.path.join(self.root, "Source", "UmbrellaElla"))
        self.src = os.path.join(self.root, "Source", "UmbrellaElla", "A.cpp")
        Path(self.src).write_text("// a\n")
        os.makedirs(os.path.join(self.root, "Binaries", "Mac"))
        self.dylib = os.path.join(self.root, "Binaries", "Mac", "libUnrealEditor-UmbrellaElla.dylib")
        Path(self.dylib).write_text("x")
        past = time.time() - 100
        os.utime(self.src, (past, past))
        self.ue = os.path.join(self.tmp, "ue")
        exe_dir = os.path.join(self.ue, "Engine", "Binaries", "Mac", "UnrealEditor.app", "Contents", "MacOS")
        os.makedirs(exe_dir)
        exe = os.path.join(exe_dir, "UnrealEditor")
        Path(exe).write_text(FAKE_EDITOR)
        os.chmod(exe, 0o755)

    def tearDown(self):
        shutil.rmtree(self.tmp)

    def run_game(self, shot_rows, *args):
        src = os.path.join(self.tmp, "src.png")
        write_png(src, 160, 90, shot_rows)
        env = dict(os.environ, UE_SLOT_HELD="1", UE_ROOT=self.ue, FAKE_SHOT_SRC=src)
        env.pop("RUN_RES", None)
        env.pop("RUN_STALE_OK", None)
        return subprocess.run(["bash", os.path.join(self.root, "tools", "build", "run_game.sh"), *args],
                              env=env, capture_output=True, text=True, timeout=60)

    def test_keeps_log_and_passes_a_frame_with_content(self):
        rows = frame_rows(160, 90, (60, 70, 90), (40, 20, 120, 70, (230, 200, 120)))
        r = self.run_game(rows, "-SmokeShot=Saved/shot.png", "-SmokeQuitAfter=5")
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        log_line = [l for l in r.stdout.splitlines() if l.startswith("run_game: log=")][0]
        log = log_line.split("=", 1)[1]
        self.assertTrue(log.startswith(os.path.join(self.root, "Saved", "Logs", "runs", "run-")), log)
        self.assertTrue(os.path.isfile(log))
        self.assertIn("-abslog=" + log, Path(log).read_text())
        self.assertIn("run_game: SMOKE_VIEW ella_in_frame=1", r.stdout)
        self.assertIn("run_game: frame_check: PASS", r.stdout)

    def test_black_shot_fails_frame_check(self):
        r = self.run_game(frame_rows(160, 90, (0, 0, 0)), "-SmokeShot=Saved/shot.png", "-SmokeQuitAfter=5")
        self.assertIn("run_game: frame_check: FAIL", r.stdout)

    def test_refuses_stale_module(self):
        future = time.time() + 100
        os.utime(self.src, (future, future))
        r = self.run_game(frame_rows(160, 90, (0, 0, 0)), "-SmokeQuitAfter=5")
        self.assertEqual(r.returncode, 3, r.stdout)
        self.assertIn("run_game: STALE Source/UmbrellaElla/A.cpp", r.stdout)
        self.assertFalse(os.path.isdir(os.path.join(self.root, "Saved", "Logs", "runs")) and
                         os.listdir(os.path.join(self.root, "Saved", "Logs", "runs")))


if __name__ == "__main__":
    unittest.main()
