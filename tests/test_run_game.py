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

    def write_modules(self, name):
        Path(os.path.join(self.root, "Binaries", "Mac", "UnrealEditor.modules")).write_text(
            '{\n\t"BuildId": "1",\n\t"Modules": \n\t{\n\t\t"UmbrellaElla": "%s",\n'
            '\t\t"UmbrellaEllaEditor": "libUnrealEditor-UmbrellaEllaEditor-0004.dylib"\n\t}\n}' % name)

    def hot_reload_layout(self, suffixed_fresh):
        """The gate at 23:03, Nov 13: UBT linked -0004 (a full editor was open), mapped .modules to it, and left the base
        dylib older than the sources."""
        old = time.time() - 200
        os.utime(self.dylib, (old, old))
        suffixed = os.path.join(self.root, "Binaries", "Mac", "libUnrealEditor-UmbrellaElla-0004.dylib")
        Path(suffixed).write_text("y")
        t = time.time() if suffixed_fresh else old
        os.utime(suffixed, (t, t))
        self.write_modules("libUnrealEditor-UmbrellaElla-0004.dylib")

    def test_hot_reload_build_is_not_stale(self):
        # Old run_game.sh checked the base dylib only and failed this with STALE.
        self.hot_reload_layout(suffixed_fresh=True)
        r = self.run_game(frame_rows(160, 90, (0, 0, 0)), "-SmokeQuitAfter=5")
        self.assertNotIn("STALE", r.stdout)
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)

    def test_hot_reload_module_older_than_source_is_stale(self):
        self.hot_reload_layout(suffixed_fresh=False)
        r = self.run_game(frame_rows(160, 90, (0, 0, 0)), "-SmokeQuitAfter=5")
        self.assertEqual(r.returncode, 3, r.stdout)
        self.assertIn("libUnrealEditor-UmbrellaElla-0004.dylib", r.stdout)

    def test_base_layout_modules_file_uses_base_dylib(self):
        self.write_modules("libUnrealEditor-UmbrellaElla.dylib")
        r = self.run_game(frame_rows(160, 90, (0, 0, 0)), "-SmokeQuitAfter=5")
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        future = time.time() + 100
        os.utime(self.src, (future, future))
        r = self.run_game(frame_rows(160, 90, (0, 0, 0)), "-SmokeQuitAfter=5")
        self.assertEqual(r.returncode, 3, r.stdout)

    def test_modules_naming_a_missing_file_is_stale(self):
        self.write_modules("libUnrealEditor-UmbrellaElla-0009.dylib")
        r = self.run_game(frame_rows(160, 90, (0, 0, 0)), "-SmokeQuitAfter=5")
        self.assertEqual(r.returncode, 3, r.stdout)
        self.assertIn("no module libUnrealEditor-UmbrellaElla-0009.dylib", r.stdout)


class BuildShTest(unittest.TestCase):
    """tools/ue/build.sh passes -NoHotReload, so an open editor on another checkout cannot make UBT write -NNNN names."""

    def setUp(self):
        self.tmp = tempfile.mkdtemp()
        root = os.path.join(self.tmp, "proj")
        os.makedirs(os.path.join(root, "tools", "ue"))
        for name in ("build.sh", "common.sh"):
            shutil.copy(os.path.join(REPO, "tools", "ue", name), os.path.join(root, "tools", "ue"))
        Path(os.path.join(root, "UmbrellaElla.uproject")).write_text("{}")
        # Stand-in for tools/ue_run.py: record the UBT command line in the log.
        Path(os.path.join(root, "tools", "ue_run.py")).write_text(
            "import sys\na = sys.argv\nlog = a[a.index('--log') + 1]\nopen(log, 'w').write(' '.join(a[a.index('--') + 1:]))\n")
        os.makedirs(os.path.join(self.tmp, "ue", "Engine"))
        self.root = root

    def tearDown(self):
        shutil.rmtree(self.tmp)

    def ubt_args(self, **env):
        e = dict(os.environ, UE_ROOT=os.path.join(self.tmp, "ue"), PYTHON=sys.executable, **env)
        e.pop("PROJECT", None)
        r = subprocess.run(["bash", os.path.join(self.root, "tools", "ue", "build.sh")], env=e,
                           capture_output=True, text=True, timeout=60)
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        log = r.stdout.split("log: ", 1)[1].strip()
        return Path(log).read_text().split()

    def test_passes_no_hot_reload(self):
        args = self.ubt_args()
        self.assertIn("UmbrellaEllaEditor", args)
        self.assertIn("-NoHotReload", args)
        self.assertIn("-NoHotReload", self.ubt_args(NONUNITY="1"))

    def test_opt_out_keeps_ubt_default(self):
        self.assertNotIn("-NoHotReload", self.ubt_args(UE_HOT_RELOAD="1"))


if __name__ == "__main__":
    unittest.main()
