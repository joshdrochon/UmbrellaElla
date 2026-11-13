"""Tests for tools/ue_run.py and the Mac scripts in tools/ue/*.sh that call it.

The scripts run against a fake engine (stub Build.sh / RunUAT.sh) and a fake packaged game in a
throwaway git repo, so no Unreal install is needed. Each check is shown passing on a good input and
failing on an input broken on purpose. The .ps1 twins call the same tools/ue_run.py subcommands;
PowerShell is not run here (test_ps1_parity only checks they call the same subcommands)."""
import io
import os
import re
import shutil
import stat
import subprocess
import sys
import tempfile
import unittest
from contextlib import redirect_stderr, redirect_stdout

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, os.path.join(ROOT, "tools"))
import ue_run  # noqa: E402
sys.path.insert(0, HERE)
import hermetic  # noqa: E402

PY = sys.executable
FAKE_SHOT = os.path.join(HERE, "fixtures", "fake_shot.py")   # the stand-in for the hook's -SmokeShot= capture


def quiet(fn, *a, **k):
    with redirect_stdout(io.StringIO()) as out:
        rc = fn(*a, **k)
    return rc, out.getvalue()


def write(path, text, exe=False):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w") as f:
        f.write(text)
    if exe:
        os.chmod(path, os.stat(path).st_mode | stat.S_IXUSR | stat.S_IXGRP | stat.S_IXOTH)


def read(path):
    with open(path) as f:
        return f.read()


def git(cwd, *args):
    subprocess.run(["git", "-c", "user.email=t@t", "-c", "user.name=t", *args], cwd=cwd, check=True,
                   capture_output=True)



def _root_with_shield():
    d = tempfile.mkdtemp()
    os.makedirs(os.path.join(d, "pipeline", "qa"))
    with open(os.path.join(d, "pipeline", "qa", "test-map.md"), "w") as fh:
        fh.write("| Shield | DEF-01, SURV-03 | `UmbrellaElla.Defense.FrontalArcCatches` | #50 | merged |\n")
    return d


ROOT_WITH_SHIELD = _root_with_shield()

class FakeRepo:
    """A git repo with tools/ue/*, tools/ue_run.py, a .uproject and a fake engine next to it."""

    def __init__(self):
        self.base = tempfile.mkdtemp()
        self.dir = os.path.join(self.base, "repo")
        os.makedirs(os.path.join(self.dir, "tools"))
        shutil.copytree(os.path.join(ROOT, "tools", "ue"), os.path.join(self.dir, "tools", "ue"))
        # every tool (smoke.sh runs bake_preset.py effective), and the data it reads
        for f in os.listdir(os.path.join(ROOT, "tools")):
            if f.endswith(".py"):
                shutil.copy(os.path.join(ROOT, "tools", f), os.path.join(self.dir, "tools", f))
        shutil.copy(os.path.join(ROOT, ".gitignore"), self.dir)
        for rel in ("docs/feature-manifest.json", "pipeline/qa/presets.json"):
            os.makedirs(os.path.dirname(os.path.join(self.dir, rel)), exist_ok=True)
            shutil.copy(os.path.join(ROOT, rel), os.path.join(self.dir, rel))
        # final-9 A C1: the test map with its rows at planned, so the jam's merged rows never reach the stub engine
        hermetic.write_planned_test_map(os.path.join(self.dir, "pipeline", "qa", "test-map.md"))
        write(os.path.join(self.dir, "UmbrellaElla.uproject"), "{}\n")
        write(os.path.join(self.dir, "Source", "UmbrellaElla.Target.cs"),
              'ProjectDefinitions.Add("UMBRELLAELLA_WORKBENCH=0");\n')
        # Past the Day-1 bootstrap (final-8 A H7): card 0.5's test pattern and card 0.6's smoke hook exist.
        # tests/test_honest_jam.py walks the bootstrap itself.
        write(os.path.join(self.dir, "Source", "UmbrellaElla", "Private", "Tests", "Meta", "SampleRuleTest.cpp"), "// 0.5\n")
        write(os.path.join(self.dir, "Source", "UmbrellaElla", "Private", "Smoke", "SmokeHook.cpp"), "// 0.6\n")
        git(self.dir, "init", "-q")
        git(self.dir, "add", "-A")
        git(self.dir, "commit", "-q", "-m", "init")
        self.engine = os.path.join(self.base, "UE")
        self.stub("Engine/Build/BatchFiles/Mac/Build.sh", 'echo "compiling $*"; exit "${STUB_RC:-0}"')
        self.stub("Engine/Build/BatchFiles/RunUAT.sh",
                  'touch "$UAT_CALLED"; [ -n "${STUB_SLEEP:-}" ] && sleep "$STUB_SLEEP"\n'
                  'for a in "$@"; do case "$a" in -archivedirectory=*) d="${a#-archivedirectory=}";; '
                  '-target=UmbrellaEllaWorkbench) wb=1;; esac; done\n'
                  '[ -n "${wb:-}" ] && [ -n "${UAT_TARGETS:-}" ] && echo workbench >> "$UAT_TARGETS"\n'
                  '[ -n "${wb:-}" ] && [ "${STUB_WB_RC:-0}" != 0 ] && { echo "LogCook: Error: workbench cook"; exit "$STUB_WB_RC"; }\n'
                  'mkdir -p "$d/Mac"; echo game > "$d/Mac/UmbrellaElla"; i=0\n'
                  'while [ "$i" -lt "${STUB_WARN:-0}" ]; do i=$((i + 1)); echo "LogCook: Warning: w$i"; done\n'
                  'echo "BUILD SUCCESSFUL"; exit "${STUB_RC:-0}"')
        # Fake editor: writes an automation report with STUB_TESTS tests in state STUB_STATE.
        # Fake editor. -run=DataValidation prints STUB_VALIDATE lines. Otherwise it writes an automation report
        # with STUB_TESTS tests in state STUB_STATE plus each name in STUB_NAMES (comma list), or only the
        # TEST_FILTER name when one test runs alone (state Fail if it equals STUB_ALONE_FAIL).
        # STUB_LEAVE=1 leaves a file in Saved/UmbrellaEllaTests.
        self.stub("Engine/Binaries/Mac/UnrealEditor.app/Contents/MacOS/UnrealEditor",
                  'R=; F=UmbrellaElla\n'
                  'for a in "$@"; do case "$a" in -ReportExportPath=*) R="${a#-ReportExportPath=}";;\n'
                  '  -run=DataValidation) printf "%b" "${STUB_VALIDATE:-}"; exit "${STUB_VALIDATE_RC:-0}";;\n'
                  '  "-ExecCmds=Automation RunTests "*) F="${a#-ExecCmds=Automation RunTests }"; F="${F%;Quit}";; esac; done\n'
                  '[ "${STUB_LEAVE:-0}" = "1" ] && mkdir -p "$PWD/Saved/UmbrellaEllaTests" && echo x > "$PWD/Saved/UmbrellaEllaTests/left.sav"\n'
                  'mkdir -p "$R"; n="${STUB_TESTS:-3}"; st="${STUB_STATE:-Success}"; t=""\n'
                  'one() { t="$t{\\"fullTestPath\\":\\"$1\\",\\"state\\":\\"$2\\",\\"duration\\":${3:-0.1}},"; }\n'
                  '[ "${STUB_SETTINGS:-0}" = "1" ] && mkdir -p "$PWD/Saved/Config/Mac" && echo "FullscreenMode=2" > "$PWD/Saved/Config/Mac/GameUserSettings.ini"\n'
                  'if [ "$F" != "UmbrellaElla" ]; then IFS=+ read -r -a FS <<< "$F"; for f in "${FS[@]}"; do s=Success\n'
                  '  [ "$f" = "${STUB_ALONE_FAIL:-}" ] && s=Fail; [ "${#FS[@]}" -gt 1 ] && [ "$f" = "${STUB_MULTI_FAIL:-}" ] && s=Fail; one "$f" "$s"; done\n'
                  'else for i in $(seq 1 "$n"); do one "UmbrellaElla.Area.T$i" "$st"; done\n'
                  '  IFS=, read -r -a X <<< "${STUB_NAMES:-}"; for x in ${X[@]+"${X[@]}"}; do d=0.1; case "$x" in *=*) d="${x#*=}";; esac; one "${x%%=*}" Success "$d"; done; fi\n'
                  'echo "{\\"tests\\":[${t%,}]}" > "$R/index.json"; exit 0')

    def stub(self, rel, body):
        write(os.path.join(self.engine, rel), "#!/usr/bin/env bash\n" + body + "\n", exe=True)

    def sh(self, script, *args, **env):
        # 300 s only catches a hung script: daily.sh with client tests takes ~11 s on a Mac and timed out at 60 s on a
        # busy GitHub runner (PR #8 run 43028983210) while the same commit passed an hour earlier
        e = dict(os.environ, UE_ROOT=self.engine, PYTHON=PY, UAT_CALLED=os.path.join(self.base, "uat_called"),
                 SETTINGS_INI=os.path.join(self.base, "gus", "GameUserSettings.ini"))   # never the real home folder
        e.pop("PROJECT", None)
        e.update({k: str(v) for k, v in env.items()})
        p = subprocess.run(["bash", os.path.join(self.dir, "tools", "ue", script), *args], cwd=self.dir, env=e,
                           capture_output=True, text=True, timeout=300)
        return p.returncode, p.stdout + p.stderr

    def uat_called(self):
        return os.path.exists(os.path.join(self.base, "uat_called"))

    def close(self):
        shutil.rmtree(self.base, ignore_errors=True)


WM_CLOSE_ONLY = ("the stub game closes on SIGTERM; on Windows ue_run closes the game with WM_CLOSE to its window, "
                 "and the windowless stub has none")


class UeRunUnitTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.mkdtemp()
        # These tests are about the log contract, not the art: the screenshot checks never block here, whatever art
        # the repo running them holds (tests/test_smoke_visual.py covers them with its own roots)
        self._art_bootstrap = ue_run.art_bootstrap
        ue_run.art_bootstrap = lambda root: True

    def tearDown(self):
        ue_run.art_bootstrap = self._art_bootstrap
        hermetic.rmtree(self.tmp, ignore_errors=True)

    def test_run_passes_exit_code_and_writes_log(self):
        log = os.path.join(self.tmp, "l.log")
        rc, _ = quiet(ue_run.run, [PY, "-c", "print('hello'); raise SystemExit(3)"], 30, log)
        self.assertEqual(rc, 3)
        self.assertIn("hello", read(log))

    def test_run_timeout_kills_and_returns_124(self):
        log = os.path.join(self.tmp, "l.log")
        rc, out = quiet(ue_run.run, [PY, "-c", "import time; time.sleep(30)"], 1, log)
        self.assertEqual(rc, ue_run.TIMEOUT_RC)
        self.assertIn("TIMEOUT", read(log))

    def test_run_returns_when_a_forked_child_keeps_the_pipe_open(self):
        # The Mac editor forks UnrealTraceServer, which holds the inherited stdout until its sponsor is reaped
        # (card 0.3 dry run): run() must return the command's code, not wait for the pipe's EOF.
        log = os.path.join(self.tmp, "l.log")
        child = ("import subprocess,sys; subprocess.Popen([sys.executable, '-c', 'import time; time.sleep(60)'], "
                 "start_new_session=True); print('parent done', flush=True); raise SystemExit(4)")
        old = os.environ.get("RUN_DRAIN_S")
        os.environ["RUN_DRAIN_S"] = "1"
        try:
            import time
            t0 = time.monotonic()
            rc, out = quiet(ue_run.run, [PY, "-c", child], 30, log)
            took = time.monotonic() - t0
        finally:
            if old is None:
                os.environ.pop("RUN_DRAIN_S", None)
            else:
                os.environ["RUN_DRAIN_S"] = old
        self.assertEqual(rc, 4)
        self.assertLess(took, 15)
        self.assertIn("parent done", read(log))
        self.assertIn("pipe still held open", read(log))

    def test_run_timeout_with_a_forked_child_still_returns_124(self):
        log = os.path.join(self.tmp, "l.log")
        child = ("import subprocess,sys,time; subprocess.Popen([sys.executable, '-c', 'import time; time.sleep(60)'], "
                 "start_new_session=True); time.sleep(30)")
        rc, out = quiet(ue_run.run, [PY, "-c", child], 1, log)
        self.assertEqual(rc, ue_run.TIMEOUT_RC)
        self.assertIn("TIMEOUT", read(log))

    def test_run_fast_command_is_not_timed_out(self):
        rc, _ = quiet(ue_run.run, [PY, "-c", "pass"], 30, os.path.join(self.tmp, "l.log"))
        self.assertEqual(rc, 0)

    def git_repo(self):
        d = os.path.join(self.tmp, "g")
        os.makedirs(d)
        git(d, "init", "-q")
        write(os.path.join(d, "a.txt"), "a\n")
        write(os.path.join(d, ".gitignore"), "Packaged/\n")
        git(d, "add", "-A")
        git(d, "commit", "-q", "-m", "init")
        return d

    def test_clean_tree(self):
        d = self.git_repo()
        self.assertEqual(quiet(ue_run.clean_tree, d, False)[0], 0)
        write(os.path.join(d, "Packaged", "x"), "ignored files don't count\n")
        self.assertEqual(quiet(ue_run.clean_tree, d, False)[0], 0)
        write(os.path.join(d, "a.txt"), "changed\n")
        self.assertEqual(quiet(ue_run.clean_tree, d, False)[0], 1)
        self.assertEqual(quiet(ue_run.clean_tree, d, True)[0], 0)

    def test_untracked_file_is_dirty(self):
        d = self.git_repo()
        write(os.path.join(d, "new.txt"), "x\n")
        self.assertEqual(quiet(ue_run.clean_tree, d, False)[0], 1)

    def test_build_info(self):
        d = self.git_repo()
        out = os.path.join(d, "Packaged")
        os.makedirs(os.path.join(out, "Windows"))
        quiet(ue_run.build_info, d, out, "Shipping")
        sha = subprocess.run(["git", "rev-parse", "HEAD"], cwd=d, capture_output=True, text=True).stdout.strip()
        for f in (os.path.join(out, "BUILD_INFO.txt"), os.path.join(out, "Windows", "BUILD_INFO.txt")):
            text = read(f)
            self.assertIn(f"commit={sha}", text)
            self.assertIn("config=Shipping", text)
            self.assertIn("dirty=no", text)
            self.assertRegex(text, r"date=\d{4}-\d\d-\d\dT")

    def test_build_info_copies_readme_and_licence(self):
        d = self.git_repo()
        write(os.path.join(d, "pipeline", "submission", "README.txt"), "Title: X\n")
        write(os.path.join(d, "pipeline", "submission", "LICENSE.txt"), "Copyright\n")
        out = os.path.join(d, "Packaged")
        os.makedirs(os.path.join(out, "Windows"))
        quiet(ue_run.build_info, d, out, "Development")
        for n in ("README.txt", "LICENSE.txt"):
            self.assertTrue(os.path.isfile(os.path.join(out, "Windows", n)), n)

    def test_build_info_without_readme_warns(self):
        d = self.git_repo()
        out = os.path.join(d, "Packaged")
        os.makedirs(out)
        self.assertIn("README.txt missing", quiet(ue_run.build_info, d, out, "Development")[1])
        self.assertFalse(os.path.exists(os.path.join(out, "README.txt")))

    def test_build_info_missing_folder_is_an_error(self):
        d = self.git_repo()
        with self.assertRaises(OSError):
            quiet(ue_run.build_info, d, os.path.join(d, "nope"), "Development")

    GOOD_LOG = ("LogInit: started\nLogUmbrellaElla: SMOKE_OK map=L_Graybox view=1920x1080 aspect=1.778 debugdraw=0 fps=60 worst_ms=20 commit=abc1234 input_vz=-120 input=ok gamepad=ok gp_vx=150 gp_attack_vz=-200 gp_shield_vz=-180 "
                "load_ms=800\n"
                "LogExit: done\n")

    # Red-team round 2, finding 30: the SMOKE_OK line must name the map and commit, and match them
    def test_smoke_line_without_map_or_commit_fails(self):
        for line in ("SMOKE_OK fps=60", "SMOKE_OK map=L_Graybox view=1920x1080 aspect=1.778 debugdraw=0 fps=60", "SMOKE_OK commit=abc1234"):
            with self.subTest(line=line):
                self.assertEqual(self.smoke("LogX: " + line + "\n")[0], 1)

    def test_smoke_expected_map_and_commit(self):
        log = os.path.join(self.tmp, "smoke.log")
        write(log, self.GOOD_LOG)
        self.assertEqual(quiet(ue_run.smoke_log, [log], 0, "/Game/UmbrellaElla/Maps/L_Graybox", "abc1234def")[0], 0)
        rc, out = quiet(ue_run.smoke_log, [log], 0, "L_StyleFrame", None)
        self.assertEqual(rc, 1, out)
        self.assertIn("expected L_StyleFrame", out)
        rc, out = quiet(ue_run.smoke_log, [log], 0, None, "fff0000")
        self.assertEqual(rc, 1, out)
        self.assertIn("built from fff0000", out)

    def smoke(self, text, rc=0, **kw):
        log = os.path.join(self.tmp, "smoke.log")
        write(log, text)
        return quiet(ue_run.smoke_log, [log], rc, **kw)

    def test_smoke_good_log_passes(self):
        rc, out = self.smoke(self.GOOD_LOG)
        self.assertEqual(rc, 0)
        self.assertIn("'Accessed None'=0", out)

    def test_smoke_gamepad_must_reach_move_attack_shield(self):
        """Card 0.6e: a controller that does not work in the package fails the smoke. Broken on purpose: no gamepad
        field, a stick that does not move Ella, a trigger that does not attack, a shield that does not hold."""
        for old, new, want in (("gamepad=ok ", "", "gamepad=<none>"), ("gp_vx=150", "gp_vx=0", "gp_vx=0"),
                               ("gp_attack_vz=-200", "gp_attack_vz=40", "gp_attack_vz=40"),
                               ("gp_shield_vz=-180", "gp_shield_vz=none", "gp_shield_vz=none")):
            with self.subTest(break_=want):
                rc, out = self.smoke(self.GOOD_LOG.replace(old, new), root=ROOT_WITH_SHIELD)
                self.assertEqual(rc, 1, out)
                self.assertIn(want, out)
        rc, out = self.smoke(self.GOOD_LOG.replace("gp_shield_vz=-180", "gp_shield_vz=none"))
        self.assertEqual(rc, 0, "before the MVP 10 shield merges, gp_shield_vz may read none\n" + out)
        rc, out = self.smoke(self.GOOD_LOG.replace("gamepad=ok ", ""), require_gamepad=False)
        self.assertEqual(rc, 0, "SMOKE_REQUIRE_GAMEPAD=0 skips it (only while QA-GP is planned)\n" + out)

    def test_smoke_each_bad_pattern_fails(self):
        for bad in ue_run.SMOKE_BAD:
            with self.subTest(bad=bad):
                rc, out = self.smoke(self.GOOD_LOG + f"LogX: Error: {bad} here\n")
                self.assertEqual(rc, 1)
                self.assertIn(f"'{bad}'=1", out)

    def test_smoke_counts_every_line(self):
        rc, out = self.smoke(self.GOOD_LOG + "Accessed None a\nAccessed None b\n")
        self.assertIn("'Accessed None'=2", out)

    def test_smoke_missing_ok_fails(self):
        self.assertEqual(self.smoke("LogInit: started\n")[0], 1)

    def test_smoke_nonzero_exit_fails(self):
        self.assertEqual(self.smoke(self.GOOD_LOG, rc=3)[0], 1)

    def test_smoke_reads_several_logs(self):
        a, b = os.path.join(self.tmp, "a.log"), os.path.join(self.tmp, "b.log")
        write(a, self.GOOD_LOG)
        write(b, "Fatal error!\n")
        self.assertEqual(quiet(ue_run.smoke_log, [a, b], 0)[0], 1)

    # Frame rate: fps on the SMOKE_OK line must reach --min-fps (default 55)
    def test_smoke_low_fps_fails(self):
        rc, out = self.smoke(self.GOOD_LOG.replace("fps=60", "fps=3"))
        self.assertEqual(rc, 1, out)
        self.assertIn("fps 3 is below the minimum 55", out)

    def test_smoke_missing_fps_fails_unless_off(self):
        log = os.path.join(self.tmp, "smoke.log")
        write(log, "SMOKE_OK map=L_Graybox view=1920x1080 aspect=1.778 debugdraw=0 worst_ms=20 commit=abc1234 input_vz=-120 input=ok gamepad=ok gp_vx=150 gp_attack_vz=-200 gp_shield_vz=-180 load_ms=800\n")
        self.assertEqual(quiet(ue_run.smoke_log, [log], 0)[0], 1)
        self.assertEqual(quiet(ue_run.smoke_log, [log], 0, min_fps=0)[0], 0)

    def test_smoke_fps_at_minimum_passes(self):
        self.assertEqual(self.smoke(self.GOOD_LOG.replace("fps=60", "fps=55.0"))[0], 0)

    def test_new_crash_markers_are_bad(self):
        for bad in ("Assertion failed: Foo", "=== Critical error: ===", "Unhandled Exception: EXCEPTION_ACCESS_VIOLATION",
                    "LogOutputDevice: Error: Ensure"):
            with self.subTest(bad=bad):
                rc, out = self.smoke(self.GOOD_LOG + "LogWindows: " + bad + "\n")
                self.assertEqual(rc, 1, out)

    # Display: resolution, window mode and the smallest UI text height
    DISPLAY_LOG = ("SMOKE_OK map=L_Title view=1280x720 aspect=1.778 debugdraw=0 fps=60 worst_ms=20 commit=abc1234 input=none res=1280x720 win=windowed textpx=19 "
                   "load_ms=800\n")

    def display(self, text, **k):
        log = os.path.join(self.tmp, "d.log")
        write(log, text)
        return quiet(ue_run.smoke_log, [log], 0, expect_res=k.get("res", "1280x720"),
                     expect_win=k.get("win", "windowed"), min_text_px=k.get("px", 18))

    def test_display_good_run_passes(self):
        self.assertEqual(self.display(self.DISPLAY_LOG)[0], 0)

    def test_display_small_text_fails(self):
        rc, out = self.display(self.DISPLAY_LOG.replace("textpx=19", "textpx=12"))
        self.assertEqual(rc, 1, out)
        self.assertIn("smallest UI text is 12 px, minimum is 18 px", out)

    def test_display_missing_textpx_fails(self):
        self.assertEqual(self.display(self.DISPLAY_LOG.replace(" textpx=19", ""))[0], 1)

    def test_display_wrong_resolution_or_mode_fails(self):
        self.assertEqual(self.display(self.DISPLAY_LOG, res="3840x2160")[0], 1)
        self.assertEqual(self.display(self.DISPLAY_LOG, win="fullscreen")[0], 1)

    # Crash folders: a new Saved/Crashes entry fails, an old one does not
    def test_crash_check(self):
        pkg = os.path.join(self.tmp, "Packaged")
        os.makedirs(os.path.join(pkg, "Windows", "UmbrellaElla", "Saved", "Crashes", "old-crash"))
        snap = os.path.join(self.tmp, "before.txt")
        self.assertEqual(ue_run.main(["crash-list", pkg, "--out", snap]), 0)
        self.assertEqual(quiet(ue_run.crash_check, snap, [pkg])[0], 0)
        os.makedirs(os.path.join(pkg, "Windows", "UmbrellaElla", "Saved", "Crashes", "UECC-new"))
        rc, out = quiet(ue_run.crash_check, snap, [pkg])
        self.assertEqual(rc, 1, out)
        self.assertIn("UECC-new", out)

    def test_crash_check_reads_a_saved_folder_root(self):
        saved = os.path.join(self.tmp, "LocalAppData", "UmbrellaElla", "Saved")
        os.makedirs(saved)
        snap = os.path.join(self.tmp, "before.txt")
        ue_run.main(["crash-list", saved, "--out", snap])
        os.makedirs(os.path.join(saved, "Crashes", "c1"))
        self.assertEqual(quiet(ue_run.crash_check, snap, [saved])[0], 1)

    # No-log "alive" smoke: running at N s, then closes with exit code 0
    def alive(self, body, seconds=0.5, close=5):
        return quiet(ue_run.alive, [PY, "-c", body], seconds, close, os.path.join(self.tmp, "a.log"))

    @unittest.skipIf(os.name == "nt", WM_CLOSE_ONLY)
    def test_alive_good_game_passes(self):
        rc, out = self.alive("import signal,sys,time; signal.signal(signal.SIGTERM, lambda *a: sys.exit(0)); time.sleep(30)")
        self.assertEqual(rc, 0, out)

    def test_alive_early_exit_fails(self):
        rc, out = self.alive("raise SystemExit(0)")
        self.assertEqual(rc, 1, out)
        self.assertIn("exited after", out)

    @unittest.skipIf(os.name == "nt", WM_CLOSE_ONLY)
    def test_alive_bad_close_code_fails(self):
        rc, out = self.alive("import signal,sys,time; signal.signal(signal.SIGTERM, lambda *a: sys.exit(3)); time.sleep(30)")
        self.assertEqual(rc, 1, out)

    def test_alive_ignores_close_times_out(self):
        rc, out = self.alive("import signal,time; signal.signal(signal.SIGTERM, signal.SIG_IGN); time.sleep(30)", close=1)
        self.assertEqual(rc, ue_run.TIMEOUT_RC, out)

    # Critic round: ordinary Error: lines and failed asset loads passed the smoke
    CRITIC_LINES = ("LogScript: Error: Script Msg: bad", "LogPaper2D: Error: missing flipbook",
                    "Warning: LogStreaming: Failed to load '/Game/X'")

    def test_smoke_any_error_line_or_failed_load_fails(self):
        for bad in self.CRITIC_LINES:
            with self.subTest(bad=bad):
                rc, out = self.smoke(self.GOOD_LOG + bad + "\n")
                self.assertEqual(rc, 1, out)
        rc, out = self.smoke(self.GOOD_LOG + "LogPaper2D: Error: missing flipbook\nLogX: Error: two\n")
        self.assertIn("'Error:'=2", out)

    def test_smoke_warning_without_error_still_passes(self):
        self.assertEqual(self.smoke(self.GOOD_LOG + "LogTemp: Warning: slow shader compile\n")[0], 0)

    def allow_files(self, allow_text, decisions_text="| D-new-audio | ... | open |\n"):
        af, df = os.path.join(self.tmp, "allow.txt"), os.path.join(self.tmp, "decisions.md")
        write(af, allow_text)
        write(df, decisions_text)
        return af, df

    def test_allowlisted_error_line_passes_only_with_a_decision_row(self):
        af, df = self.allow_files("# comment\nD-new-audio | LogAudio: Error: No default device\n")
        allow = ue_run.load_allow(af, df)
        log = os.path.join(self.tmp, "smoke.log")
        write(log, self.GOOD_LOG + "LogAudio: Error: No default device\n")
        self.assertEqual(quiet(ue_run.smoke_log, [log], 0, allow=allow)[0], 0)
        self.assertEqual(quiet(ue_run.smoke_log, [log], 0)[0], 1)
        for bad in ("LogAudio: Error: No default device\n", "D-nope | LogAudio: Error\n", "D-new-audio | (\n"):
            with self.subTest(allow=bad):
                af, df = self.allow_files(bad)
                with self.assertRaises(ValueError):
                    ue_run.load_allow(af, df)

    def test_allowlist_never_hides_a_crash_pattern(self):
        af, df = self.allow_files("D-new-audio | .*\n")
        log = os.path.join(self.tmp, "smoke.log")
        write(log, self.GOOD_LOG + "LogWindows: Error: Fatal error!\n")
        rc, out = quiet(ue_run.smoke_log, [log], 0, allow=ue_run.load_allow(af, df))
        self.assertEqual(rc, 1, out)
        self.assertIn("'Fatal error'=1", out)

    def test_cli_bad_allow_file_exits_2_and_shipped_file_is_valid(self):
        log = os.path.join(self.tmp, "smoke.log")
        write(log, self.GOOD_LOG)
        af, _ = self.allow_files("D-missing | x\n")
        with redirect_stdout(io.StringIO()), redirect_stderr(io.StringIO()):
            self.assertEqual(ue_run.main(["--root", self.tmp, "smoke-log", log, "--exit-code", "0", "--allow", af]), 2)
            self.assertEqual(ue_run.main(["smoke-log", log, "--exit-code", "0"]), 0)

    # Frame time: worst_ms on the SMOKE_OK line must be <= --max-frame-ms (default 33)
    def test_smoke_worst_frame_over_limit_fails(self):
        rc, out = self.smoke(self.GOOD_LOG.replace("worst_ms=20", "worst_ms=48.5"))
        self.assertEqual(rc, 1, out)
        self.assertIn("worst frame 48.5 ms is over the limit 33 ms", out)
        self.assertEqual(self.smoke(self.GOOD_LOG.replace("worst_ms=20", "worst_ms=33"))[0], 0)

    def test_smoke_missing_worst_frame_fails_unless_off(self):
        log = os.path.join(self.tmp, "smoke.log")
        write(log, self.GOOD_LOG.replace(" worst_ms=20", ""))
        self.assertEqual(quiet(ue_run.smoke_log, [log], 0)[0], 1)
        self.assertEqual(quiet(ue_run.smoke_log, [log], 0, max_frame_ms=0)[0], 0)

    # Input: the hook injects input and logs input=ok; input=none only on a map with no player
    def test_smoke_input_missing_or_none_on_gameplay_map_fails(self):
        for log in (self.GOOD_LOG.replace(" input=ok", ""), self.GOOD_LOG.replace("input=ok", "input=none"),
                    self.GOOD_LOG.replace("input=ok", "input=fail")):
            with self.subTest(log=log):
                rc, out = self.smoke(log)
                self.assertEqual(rc, 1, out)
                self.assertIn("log input=ok", out)

    def test_smoke_input_none_passes_on_title_and_when_off(self):
        title = self.GOOD_LOG.replace("map=L_Graybox", "map=/Game/UmbrellaElla/Maps/L_Title").replace("input=ok", "input=none")
        self.assertEqual(self.smoke(title)[0], 0)
        log = os.path.join(self.tmp, "smoke.log")
        write(log, self.GOOD_LOG.replace(" input=ok", ""))
        self.assertEqual(quiet(ue_run.smoke_log, [log], 0, require_input=False)[0], 0)

    def test_smoke_expected_section(self):
        log = os.path.join(self.tmp, "smoke.log")
        write(log, self.GOOD_LOG.replace("input=ok", "input=ok section=S5"))
        self.assertEqual(quiet(ue_run.smoke_log, [log], 0, expect_section="S5")[0], 0)
        self.assertEqual(quiet(ue_run.smoke_log, [log], 0, expect_section="S3")[0], 1)
        write(log, self.GOOD_LOG)
        self.assertEqual(quiet(ue_run.smoke_log, [log], 0, expect_section="S5")[0], 1)

    # Restart cycles: N SMOKE_CYCLE lines, same actor count and health after each
    def cycles(self, rows, want=5, log_text=None):
        log = os.path.join(self.tmp, "smoke.log")
        write(log, "".join(f"LogUmbrellaElla: SMOKE_CYCLE n={i} actors={a} health={h} load_ms=900\n" for i, (a, h) in enumerate(rows, 1))
              + (log_text or self.GOOD_LOG))
        return quiet(ue_run.smoke_log, [log], 0, restart_cycles=want)

    def test_restart_cycles_steady_passes(self):
        self.assertEqual(self.cycles([(12, 3)] * 5)[0], 0)

    def test_restart_cycles_too_few_or_drifting_fail(self):
        rc, out = self.cycles([(12, 3)] * 4)
        self.assertEqual(rc, 1, out)
        self.assertIn("expected 5", out)
        rc, out = self.cycles([(12, 3)] * 4 + [(13, 3)])
        self.assertEqual(rc, 1, out)
        self.assertIn("actor count drifted", out)
        rc, out = self.cycles([(12, 3)] * 4 + [(12, 2)])
        self.assertEqual(rc, 1, out)
        self.assertIn("health drifted", out)

    def test_restart_cycles_skipped_on_a_no_player_map(self):
        title = self.GOOD_LOG.replace("map=L_Graybox", "map=L_Title").replace("input=ok", "input=none")
        self.assertEqual(self.cycles([], log_text=title)[0], 0)

    # Desktop size for the display skip
    def test_desktop_res_override(self):
        self.assertEqual(ue_run.desktop_res({"SMOKE_DESKTOP_RES": "1920x1080"}), (1920, 1080))

    # Merge coverage: every first-parent commit needs a clean passing DAILY line
    def test_merge_check(self):
        d = self.git_repo()
        first = subprocess.run(["git", "rev-parse", "HEAD"], cwd=d, capture_output=True, text=True).stdout.strip()
        shas = []
        for i in range(2):
            write(os.path.join(d, f"m{i}.txt"), "x\n")
            git(d, "add", "-A")
            git(d, "commit", "-q", "-m", f"merge {i}")
            shas.append(subprocess.run(["git", "rev-parse", "HEAD"], cwd=d, capture_output=True, text=True).stdout.strip())
        rec = os.path.join(self.tmp, "rec.txt")
        ok = " | m | Development | clean-tree=PASS build=PASS test=PASS(1/0/1) package=PASS smoke=PASS(1 map(s)) | Not checked: none"
        write(rec, f"DAILY {shas[0][:7]}{ok}\nDAILY {shas[1][:7]}+dirty{ok}\n")
        rc, out = quiet(ue_run.merge_check, d, first, rec)
        self.assertEqual(rc, 1, out)
        self.assertIn(shas[1][:12], out)
        write(rec, f"DAILY {shas[0][:7]}{ok}\nDAILY {shas[1][:7]}{ok.replace('smoke=PASS', 'smoke=FAIL')}\n")
        self.assertEqual(quiet(ue_run.merge_check, d, first, rec)[0], 1)
        write(rec, f"DAILY {shas[0][:7]}{ok}\nDAILY {shas[1][:9]}{ok}\n")
        rc, out = quiet(ue_run.merge_check, d, first, rec)
        self.assertEqual(rc, 0, out)
        self.assertIn("2/2", out)

    # Map list for the per-map smoke
    def test_maps_reads_default_and_maps_to_cook(self):
        cfg = os.path.join(self.tmp, "Config")
        write(os.path.join(cfg, "DefaultEngine.ini"),
              "[/Script/EngineSettings.GameMapsSettings]\nGameDefaultMap=/Game/UmbrellaElla/Maps/L_Title.L_Title\n")
        write(os.path.join(cfg, "DefaultGame.ini"),
              '[/Script/UnrealEd.ProjectPackagingSettings]\n+MapsToCook=(FilePath="/Game/UmbrellaElla/Maps/L_Title")\n'
              '+MapsToCook=(FilePath="/Game/UmbrellaElla/Maps/L_Graybox")\n')
        default, ms = ue_run.maps(self.tmp)
        self.assertEqual(default, "/Game/UmbrellaElla/Maps/L_Title.L_Title")
        self.assertEqual([ue_run.short_map(m) for m in ms], ["L_Title", "L_Graybox"])
        self.assertEqual(ue_run.maps(os.path.join(self.tmp, "none")), (None, []))

    # Load time: load_ms on SMOKE_OK and each SMOKE_CYCLE must be <= --max-load-ms (default 10000)
    def test_workbench_check(self):
        d = tempfile.mkdtemp()
        try:
            self.assertTrue(ue_run.workbench_check(d))   # no submission target at all
            write(os.path.join(d, "Source", "UmbrellaElla.Target.cs"), 'ProjectDefinitions.Add("UMBRELLAELLA_WORKBENCH=0");\n')
            write(os.path.join(d, "Source", "UmbrellaEllaWorkbench.Target.cs"), 'ProjectDefinitions.Add("UMBRELLAELLA_WORKBENCH=1");\n')
            self.assertEqual(ue_run.workbench_check(d), [])
            bc = os.path.join(d, "Source", "UmbrellaElla", "UmbrellaElla.Build.cs")
            write(bc, 'PublicDefinitions.Add("UMBRELLAELLA_WORKBENCH=1");\n')
            self.assertTrue(any("Build.cs" in p for p in ue_run.workbench_check(d)))
            os.remove(bc)
            write(os.path.join(d, "Source", "UmbrellaElla", "Public", "Wb.h"), "#define UMBRELLAELLA_WORKBENCH 1\n")
            self.assertTrue(any("Wb.h" in p for p in ue_run.workbench_check(d)))
        finally:
            shutil.rmtree(d)

    def test_workbench_guard_is_exactly_the_switch(self):
        """Dry run B M5: an OR'ed guard compiles the workbench into the submission; only `#if UMBRELLAELLA_WORKBENCH`."""
        d = tempfile.mkdtemp()
        try:
            write(os.path.join(d, "Source", "UmbrellaElla.Target.cs"), 'ProjectDefinitions.Add("UMBRELLAELLA_WORKBENCH=0");\n')
            h = os.path.join(d, "Source", "UmbrellaElla", "Private", "Harness", "Panel.cpp")
            write(h, "#if UMBRELLAELLA_WORKBENCH  // panel\nvoid Panel();\n#endif\n")
            self.assertEqual(ue_run.workbench_check(d), [])
            for bad in ("#if UMBRELLAELLA_WORKBENCH || !UE_BUILD_SHIPPING", "#if !UE_BUILD_SHIPPING || UMBRELLAELLA_WORKBENCH",
                        "#elif UMBRELLAELLA_WORKBENCH || WITH_EDITOR", "#if (UMBRELLAELLA_WORKBENCH)"):
                with self.subTest(bad):
                    write(h, bad + "\nvoid Panel();\n#endif\n")
                    self.assertTrue(any("Panel.cpp:1" in p for p in ue_run.workbench_check(d)))
        finally:
            shutil.rmtree(d)

    def test_workbench_defined_guard_is_caught(self):
        """Dry run B H8: the macro is always defined (=0 in the submission), so defined()/#ifdef always compiles in."""
        d = tempfile.mkdtemp()
        try:
            write(os.path.join(d, "Source", "UmbrellaElla.Target.cs"), 'ProjectDefinitions.Add("UMBRELLAELLA_WORKBENCH=0");\n')
            panel = os.path.join(d, "Source", "UmbrellaElla", "Private", "Harness", "Panel.cpp")
            write(panel, "#if UMBRELLAELLA_WORKBENCH\nvoid Panel() {}\n#endif\n#if !UMBRELLAELLA_WORKBENCH\n#endif\n")
            self.assertEqual(ue_run.workbench_check(d), [])
            for bad in ("#if defined(UMBRELLAELLA_WORKBENCH)", "#ifdef UMBRELLAELLA_WORKBENCH",
                        "#  ifndef UMBRELLAELLA_WORKBENCH", "#if defined UMBRELLAELLA_WORKBENCH && WITH_EDITOR",
                        "#elif defined(UMBRELLAELLA_WORKBENCH)", "#if WITH_EDITOR || defined( UMBRELLAELLA_WORKBENCH )"):
                with self.subTest(bad=bad):
                    write(panel, bad + "\nvoid Panel() {}\n#endif\n")
                    got = ue_run.workbench_check(d)
                    self.assertTrue(any("Panel.cpp:1" in p and "always defined" in p for p in got), got)
        finally:
            shutil.rmtree(d)

    def test_smoke_expect_workbench(self):
        good = "SMOKE_OK map=L_Graybox view=1920x1080 aspect=1.778 debugdraw=0 fps=60 worst_ms=20 commit=abc input_vz=-120 input=ok gamepad=ok gp_vx=150 gp_attack_vz=-200 gp_shield_vz=-180 load_ms=800 workbench=0\n"
        self.assertEqual(self.smoke(good, expect_workbench="0")[0], 0)
        rc, out = self.smoke(good.replace("workbench=0", "workbench=1"), expect_workbench="0")
        self.assertEqual(rc, 1)
        self.assertIn("SMOKE_OK workbench=1, BUILD_INFO says 0", out)
        rc, out = self.smoke(good.replace(" workbench=0", ""), expect_workbench="0")
        self.assertIn("workbench=<none>", out)
        for line in ("LogWorkbench: Display: panel open", "WORKBENCH_ON debug=1", "TestPresetLoaded T-01"):
            with self.subTest(line=line):
                self.assertEqual(self.smoke(good + line + "\n", expect_workbench="0")[0], 1)
        self.assertEqual(self.smoke(good.replace("workbench=0", "workbench=1") + "WORKBENCH_ON debug=1\n",
                                    expect_workbench="1")[0], 0)   # the tester package may print it
        self.assertEqual(self.smoke(good + "WORKBENCH_ON debug=1\n")[0], 0)   # no BUILD_INFO value: not asked

    def test_smoke_load_time(self):
        rc, out = self.smoke(self.GOOD_LOG.replace("load_ms=800", "load_ms=12500"))
        self.assertEqual(rc, 1, out)
        self.assertIn("SMOKE_OK load took 12500 ms, over the limit 10000 ms", out)
        self.assertEqual(self.smoke(self.GOOD_LOG.replace("load_ms=800", "load_ms=10000"))[0], 0)
        log = os.path.join(self.tmp, "smoke.log")
        write(log, self.GOOD_LOG.replace(" load_ms=800", ""))
        rc, out = quiet(ue_run.smoke_log, [log], 0)
        self.assertEqual(rc, 1, out)
        self.assertIn("no numeric load_ms=", out)
        self.assertEqual(quiet(ue_run.smoke_log, [log], 0, max_load_ms=0)[0], 0)

    def test_restart_load_time_is_checked_per_cycle(self):
        log = os.path.join(self.tmp, "smoke.log")
        rows = "".join(f"SMOKE_CYCLE n={i} actors=12 health=3 load_ms={900 if i < 5 else 15000}\n" for i in range(1, 6))
        write(log, rows + self.GOOD_LOG)
        rc, out = quiet(ue_run.smoke_log, [log], 0, restart_cycles=5)
        self.assertEqual(rc, 1, out)
        self.assertIn("SMOKE_CYCLE n=5 load took 15000 ms", out)
        write(log, rows.replace(" load_ms=15000", "") + self.GOOD_LOG)
        rc, out = quiet(ue_run.smoke_log, [log], 0, restart_cycles=5)
        self.assertEqual(rc, 1, out)
        self.assertIn("SMOKE_CYCLE n=5 has no numeric load_ms=", out)

    # Merge coverage: a FAIL in any step that ran means the commit is not covered
    def merge_repo(self):
        d = self.git_repo()
        first = subprocess.run(["git", "rev-parse", "HEAD"], cwd=d, capture_output=True, text=True).stdout.strip()
        write(os.path.join(d, "m.txt"), "x\n")
        git(d, "add", "-A")
        git(d, "commit", "-q", "-m", "merge")
        sha = subprocess.run(["git", "rev-parse", "HEAD"], cwd=d, capture_output=True, text=True).stdout.strip()
        return d, first, sha

    MERGE_LINE = ("DAILY {sha} | m | Development | clean-tree=PASS build=PASS test=PASS(1/0/1) alone=PASS(0 new) "
                  "validate=PASS(err 0, warn 0) package=PASS(warn 0) smoke=PASS(1 map(s)) display=PASS(1 mode(s)) "
                  "client-test=PASS shipping-alive=NOT RUN | Not checked: none")

    def test_merge_check_any_failed_step_fails(self):
        d, first, sha = self.merge_repo()
        rec = os.path.join(self.tmp, "rec.txt")
        line = self.MERGE_LINE.format(sha=sha[:7])
        write(rec, line + "\n")
        self.assertEqual(quiet(ue_run.merge_check, d, first, rec)[0], 0)
        for good, bad in (("display=PASS(1 mode(s)) client-test=PASS", "display=FAIL(1280x720 windowed) client-test=not run"),
                          ("client-test=PASS", "client-test=FAIL")):
            with self.subTest(bad=bad):
                write(rec, line.replace(good, bad) + "\n")
                rc, out = quiet(ue_run.merge_check, d, first, rec)
                self.assertEqual(rc, 1, out)

    def test_merge_check_require_client_after_g1(self):
        d, first, sha = self.merge_repo()
        rec = os.path.join(self.tmp, "rec.txt")
        line = self.MERGE_LINE.format(sha=sha[:7]).replace("client-test=PASS", "client-test=NOT RUN")
        write(rec, line + "\n")
        self.assertEqual(quiet(ue_run.merge_check, d, first, rec)[0], 0)
        rc, out = quiet(ue_run.merge_check, d, first, rec, True)
        self.assertEqual(rc, 1, out)
        write(rec, self.MERGE_LINE.format(sha=sha[:7]) + "\n")
        self.assertEqual(quiet(ue_run.merge_check, d, first, rec, True)[0], 0)

    # Real-engine pipeline: every VERIFY tag in the engine-facing scripts is listed until it is removed
    def test_verify_tags(self):
        root = os.path.join(self.tmp, "r")
        write(os.path.join(root, "tools", "ue", "smoke.sh"), "run -abslog  # [" + "VERIFY]\n")
        write(os.path.join(root, "tools", "ue_run.py"), "x = 1\n")
        with redirect_stdout(io.StringIO()) as out:
            self.assertEqual(ue_run.main(["--root", root, "verify-tags"]), 1)
        self.assertIn("smoke.sh:1:", out.getvalue())
        write(os.path.join(root, "tools", "ue", "smoke.sh"), "run -abslog  # checked on 5.8.4, card 0.6\n")
        with redirect_stdout(io.StringIO()):
            self.assertEqual(ue_run.main(["--root", root, "verify-tags"]), 0)

    # Stress hand checks from G3: one STRESS line per commit, every field pass
    STRESS = ("STRESS {sha} | pause-restart pass | pause-quit pass | hold-alt-tab pass | two-runs pass | "
              "audio-switch pass (1.2 s) | gamepad not merged")

    def stress(self, line):
        d, _, sha = self.merge_repo()
        rec = os.path.join(self.tmp, "rec.txt")
        write(rec, (line.format(sha=sha[:7]) + "\n") if line else "DAILY x\n")
        return quiet(ue_run.stress_check, d, "HEAD", rec)

    def test_stress_check_good_line_passes(self):
        rc, out = self.stress(self.STRESS)
        self.assertEqual(rc, 0, out)
        hermetic.rmtree(self.tmp)
        os.makedirs(self.tmp)
        self.assertEqual(self.stress(self.STRESS.replace("gamepad not merged", "gamepad pass"))[0], 0)

    def test_stress_check_missing_blank_or_failed_field_fails(self):
        for bad, why in ((None, "no STRESS line"),
                         (self.STRESS.replace("two-runs pass", "two-runs"), "two-runs: blank"),
                         (self.STRESS.replace(" | pause-quit pass", ""), "pause-quit: blank"),
                         (self.STRESS.replace("hold-alt-tab pass", "hold-alt-tab fail"), "hold-alt-tab: fail"),
                         (self.STRESS.replace("(1.2 s)", "(3.5 s)"), "3.5 s to resume"),
                         (self.STRESS.replace(" (1.2 s)", ""), "no '(N s)'"),
                         (self.STRESS.replace("gamepad not merged", "gamepad fail"), "gamepad: fail")):
            with self.subTest(why=why):
                hermetic.rmtree(self.tmp, ignore_errors=True)
                os.makedirs(self.tmp)
                rc, out = self.stress(bad)
                self.assertEqual(rc, 1, out)
                self.assertIn(why, out)

    # Gap: crash-check passed silently when the watched folder was wrong or missing
    def test_crash_check_fails_when_no_watched_root_exists(self):
        snap = os.path.join(self.tmp, "before.txt")
        missing = os.path.join(self.tmp, "nonexistent")
        with redirect_stdout(io.StringIO()):
            self.assertEqual(ue_run.main(["crash-list", missing, "--out", snap]), 0)
            self.assertEqual(ue_run.main(["crash-check", "--before", snap, missing]), 2)
        rc, out = quiet(ue_run.crash_check, snap, [missing, os.path.join(self.tmp, "also-missing")])
        self.assertEqual(rc, 2, out)
        self.assertIn("none of the watched crash roots exists", out)
        rc, out = quiet(ue_run.crash_check, snap, [missing, self.tmp])   # one real root: checked as before
        self.assertEqual(rc, 0, out)
        self.assertIn("crash root missing", out)

    # Gap: tests could change save slots or GameUserSettings.ini outside the scratch folder
    def test_state_check_catches_changed_added_and_removed_files(self):
        gus = os.path.join(self.tmp, "Saved", "Config", "Windows", "GameUserSettings.ini")
        write(gus, "FullscreenMode=1\n")
        snap = os.path.join(self.tmp, "state.txt")
        self.assertEqual(ue_run.main(["--root", self.tmp, "state-list", "--out", snap]), 0)
        self.assertEqual(quiet(ue_run.state_check, self.tmp, snap)[0], 0)
        write(os.path.join(self.tmp, "Saved", "Logs", "x.log"), "logs don't count\n")
        self.assertEqual(quiet(ue_run.state_check, self.tmp, snap)[0], 0)
        for change, why in ((lambda: write(gus, "FullscreenMode=2\n"), "changed: "),
                            (lambda: write(os.path.join(self.tmp, "Saved", "SaveGames", "Slot0.sav"), "x"), "added: "),
                            (lambda: os.remove(gus), "removed: ")):
            with self.subTest(why=why):
                write(gus, "FullscreenMode=1\n")
                shutil.rmtree(os.path.join(self.tmp, "Saved", "SaveGames"), ignore_errors=True)
                change()
                rc, out = quiet(ue_run.state_check, self.tmp, snap)
                self.assertEqual(rc, 1, out)
                self.assertIn(why, out)

    # Gap: the full playthrough had no record line and no checker
    PLAY = ("PLAYTHROUGH {sha} | intro pass | contest pass | desperation pass | survived pass | fail-retry pass | "
            "fail-bottom pass | quit-play pass | quit-title pass | quit-pause pass")

    def hand(self, kind, line):
        d, _, sha = self.merge_repo()
        rec = os.path.join(self.tmp, "rec.txt")
        write(rec, (line.format(sha=sha[:7]) + "\n") if line else "DAILY x\n")
        with redirect_stdout(io.StringIO()) as out:
            rc = ue_run.main(["--root", d, kind + "-check", "--record", rec])
        return rc, out.getvalue()

    def test_playthrough_check(self):
        rc, out = self.hand("playthrough", self.PLAY)
        self.assertEqual(rc, 0, out)
        for bad, why in ((None, "no PLAYTHROUGH line"), (self.PLAY.replace(" | contest pass", ""), "contest: blank"),
                         (self.PLAY.replace("intro pass", "intro fail"), "intro: fail"),
                         (self.PLAY.replace("quit-pause pass", "quit-pause"), "quit-pause: blank"),
                         (self.PLAY.replace("survived pass", "survived skipped"), "survived: skipped"),
                         (self.PLAY.replace(" | fail-bottom pass", ""), "fail-bottom: blank")):
            with self.subTest(why=why):
                hermetic.rmtree(self.tmp, ignore_errors=True)
                os.makedirs(self.tmp)
                rc, out = self.hand("playthrough", bad)
                self.assertEqual(rc, 1, out)
                self.assertIn(why, out)

    # Gap: G1 and G2 could never record a plain Pass, since phases, survived and restart land by G3
    # Dry run A H1: G1 is MVP 1-6, 9, 11, so survived (MVP 6) and fail-retry (MVP 4-5) are due from G1
    # Final-7 A M1: n/a for survived or fail-retry fails at G1
    G1 = ("PLAYTHROUGH {sha} | intro n/a | contest n/a | desperation n/a | survived pass | fail-retry pass | "
          "fail-bottom pass | quit-play pass | quit-title pass | quit-pause pass")

    def hand_gate(self, line, gate):
        d, _, sha = self.merge_repo()
        rec = os.path.join(self.tmp, "rec.txt")
        write(rec, line.format(sha=sha[:7]) + "\n")
        with redirect_stdout(io.StringIO()) as out:
            rc = ue_run.main(["--root", d, "playthrough-check", "--record", rec, "--gate", gate])
        return rc, out.getvalue()

    def test_playthrough_check_is_gate_scoped(self):
        rc, out = self.hand_gate(self.G1, "G1")
        self.assertEqual(rc, 0, out)
        self.assertIn("G1: survived, fail-retry, fail-bottom, quit-play passed", out)
        # Final-7 A H1: GDD 1.3 section 12A puts the player screens on Nov 13, so both quits may be n/a at G1 only
        nomenu = self.G1.replace("quit-title pass", "quit-title n/a").replace("quit-pause pass", "quit-pause n/a")
        hermetic.rmtree(self.tmp, ignore_errors=True)
        os.makedirs(self.tmp)
        rc, out = self.hand_gate(nomenu, "G1")
        self.assertEqual(rc, 0, out)
        for line, gate, why in ((nomenu, "G2", "quit-title: n/a"), (nomenu.replace("quit-title n/a", "quit-title pass"), "G2", "quit-pause: n/a"),
                                (self.G1.replace("fail-bottom pass", "fail-bottom n/a"), "G1", "fail-bottom: n/a"),
                                (self.G1.replace("survived pass", "survived n/a"), "G1", "survived: n/a"),
                                (self.G1.replace("fail-retry pass", "fail-retry n/a"), "G2", "fail-retry: n/a"),
                                (self.G1.replace("intro n/a", "intro fail"), "G1", "intro: fail (not due at G1"),
                                (self.G1.replace(" | survived pass", ""), "G2", "survived: blank"),
                                (self.G1, "G3", "intro: n/a"), (self.G1.replace("survived pass", "survived n/a"), "G4", "survived: n/a")):
            with self.subTest(why=why):
                hermetic.rmtree(self.tmp, ignore_errors=True)
                os.makedirs(self.tmp)
                rc, out = self.hand_gate(line, gate)
                self.assertEqual(rc, 1, out)
                self.assertIn(why, out)

    # Gap: the Shipping boot time and clean quit had no checker
    SHIP = "SHIPPING {sha} | boot_s=12.5 | quit rc=0"

    def test_shipping_check(self):
        rc, out = self.hand("shipping", self.SHIP)
        self.assertEqual(rc, 0, out)
        for bad, why in ((None, "no SHIPPING line"), (self.SHIP.replace("12.5", "25"), "25 s, limit 20 s"),
                         (self.SHIP.replace("boot_s=12.5", "boot_s="), "boot_s: no number"),
                         (self.SHIP.replace("rc=0", "rc=3"), "quit: rc=3")):
            with self.subTest(why=why):
                hermetic.rmtree(self.tmp, ignore_errors=True)
                os.makedirs(self.tmp)
                rc, out = self.hand("shipping", bad)
                self.assertEqual(rc, 1, out)
                self.assertIn(why, out)

    @unittest.skipIf(os.name == "nt", WM_CLOSE_ONLY)
    def test_alive_boot_time(self):
        body = "import signal, sys, time; signal.signal(signal.SIGTERM, lambda *a: sys.exit(0)); time.sleep(30)"
        log = os.path.join(self.tmp, "a.log")
        orig = ue_run.window_up
        try:
            ue_run.window_up = lambda proc: True
            rc, out = quiet(ue_run.alive, [PY, "-c", body], 0.3, 5, log, 20)
            self.assertEqual(rc, 0, out)
            self.assertIn("boot_s=", out)
            ue_run.window_up = lambda proc: False
            rc, out = quiet(ue_run.alive, [PY, "-c", body], 0.3, 5, log, 0.5)
            self.assertEqual(rc, 1, out)
            self.assertIn("no window within 0.5 s", out)
            ue_run.window_up = lambda proc: None
            rc, out = quiet(ue_run.alive, [PY, "-c", body], 0.3, 5, log, 20)
            self.assertEqual(rc, 1, out)
            self.assertIn("boot_s=unknown", out)
        finally:
            ue_run.window_up = orig

    # Gap: fps limits measured on an unnamed machine
    def test_host_note(self):
        self.assertIn("REF_HOST not set", ue_run.host_note({}, "dev-pc"))
        self.assertIn("ran on dev-pc", ue_run.host_note({"REF_HOST": "old-laptop"}, "dev-pc"))
        self.assertIsNone(ue_run.host_note({"REF_HOST": "Old-Laptop"}, "old-laptop"))

    def test_display_modes_include_16_10_and_ultrawide(self):
        modes = ue_run.DISPLAY_MODES.split(",")
        self.assertIn("1280x800:windowed", modes)
        self.assertIn("2560x1080:windowed", modes)


@unittest.skipUnless(shutil.which("bash") and shutil.which("git"), "needs bash and git")
@unittest.skipIf(os.name == "nt", "runs the Mac tools/ue/*.sh scripts on #! bash stubs; Windows uses the .ps1 twins "
                 "(Ps1ParityTests)")
class MacScriptTests(unittest.TestCase):
    def setUp(self):
        self.r = FakeRepo()

    def tearDown(self):
        self.r.close()

    def test_build_passes_and_fails_with_engine(self):
        self.assertEqual(self.r.sh("build.sh")[0], 0)
        self.assertEqual(self.r.sh("build.sh", STUB_RC=5)[0], 5)

    def test_build_timeout(self):
        self.r.stub("Engine/Build/BatchFiles/Mac/Build.sh", "sleep 30")
        rc, out = self.r.sh("build.sh", UE_TIMEOUT=1)
        self.assertEqual(rc, 124, out)

    def test_package_clean_tree_writes_build_info(self):
        rc, out = self.r.sh("package.sh")
        self.assertEqual(rc, 0, out)
        info = read(os.path.join(self.r.dir, "Packaged", "Mac", "BUILD_INFO.txt"))
        self.assertIn("config=Development", info)
        self.assertIn("dirty=no", info)

    def test_package_submission_target_has_workbench_off(self):
        rc, out = self.r.sh("package.sh")
        self.assertEqual(rc, 0, out)
        self.assertIn("workbench-check: PASS", out)
        info = read(os.path.join(self.r.dir, "Packaged", "Mac", "BUILD_INFO.txt"))
        self.assertIn("target=UmbrellaElla\n", info)
        self.assertIn("workbench=0", info)

    def test_package_fails_when_the_submission_target_turns_the_workbench_on(self):
        write(os.path.join(self.r.dir, "Source", "UmbrellaElla.Target.cs"),
              'ProjectDefinitions.Add("UMBRELLAELLA_WORKBENCH=1");\n')   # broken on purpose
        git(self.r.dir, "commit", "-qam", "wb on")
        rc, out = self.r.sh("package.sh")
        self.assertEqual(rc, 1, out)
        self.assertIn("UMBRELLAELLA_WORKBENCH=1", out)
        self.assertFalse(self.r.uat_called(), "UAT must not run when the submission target has the workbench on")

    def test_package_workbench_tester_target(self):
        rc, out = self.r.sh("package.sh", "--workbench")
        self.assertEqual(rc, 0, out)
        info = read(os.path.join(self.r.dir, "Packaged-Workbench", "BUILD_INFO.txt"))
        self.assertIn("target=UmbrellaEllaWorkbench", info)
        self.assertIn("workbench=1", info)
        self.assertEqual(self.r.sh("package.sh", "--workbench", SHIPPING=1)[0], 2)

    def test_smoke_reads_workbench_from_build_info(self):
        ok = 'echo "SMOKE_OK map=L_Graybox view=1920x1080 aspect=1.778 debugdraw=0 fps=60 worst_ms=20 commit=abc1234 input_vz=-120 input=ok gamepad=ok gp_vx=150 gp_attack_vz=-200 gp_shield_vz=-180 load_ms=800 workbench=0" > "$L"'
        exe = self.game(ok + "; exit 0")
        write(os.path.join(os.path.dirname(exe), "BUILD_INFO.txt"), "commit=abc1234ffff\nconfig=Development\nworkbench=0\n")
        self.assertEqual(self.r.sh("smoke.sh", exe)[0], 0)
        exe = self.game(ok + '; echo "LogWorkbench: WORKBENCH_ON debug=0" >> "$L"; exit 0')
        rc, out = self.r.sh("smoke.sh", exe)
        self.assertEqual(rc, 1, out)
        self.assertIn("workbench line(s)", out)

    def test_smoke_output_pastes_into_a_pr_as_is(self):
        # Final-7 A H2: smoke.sh prints the game's SMOKE_OK log line, so the whole output passes check_pr
        import check_pr
        line = "[2026.11.12-10.00.00:000][  0]LogUmbrellaElla: SMOKE_OK map=L_Graybox view=1920x1080 aspect=1.778 debugdraw=0 fps=60 worst_ms=20 commit=abc1234 input_vz=-120 input=ok gamepad=ok gp_vx=150 gp_attack_vz=-200 gp_shield_vz=-180 load_ms=800 workbench=0"
        exe = self.game(f'echo "{line}" > "$L"; exit 0')
        write(os.path.join(os.path.dirname(exe), "BUILD_INFO.txt"), "commit=abc1234ffff\nconfig=Development\nworkbench=0\n")
        rc, out = self.r.sh("smoke.sh", exe)
        self.assertEqual(rc, 0, out)
        self.assertIn("\n" + line + "\n", "\n" + out)
        sys.path.insert(0, HERE)
        import test_check_pr
        good = test_check_pr.GOOD
        body = good.replace("PASS  tests=14 failed=0  commit=abc1234",
                            "PASS  tests=14 failed=0  commit=abc1234\npackage exit: 0  commit=abc1234  dirty=no  log: x\n" + out)
        self.assertEqual(check_pr.problems(body, changed=["Config/DefaultGame.ini"]), [])
        # broken on purpose: the summary line alone (what smoke printed before) is not the game's line
        body = body.replace(line, "")
        self.assertTrue(check_pr.problems(body, changed=["Config/DefaultGame.ini"]))

    def test_package_shipping_config(self):
        self.assertEqual(self.r.sh("package.sh", SHIPPING=1)[0], 0)
        self.assertIn("config=Shipping", read(os.path.join(self.r.dir, "Packaged", "BUILD_INFO.txt")))

    def test_package_refuses_dirty_tree(self):
        write(os.path.join(self.r.dir, "UmbrellaElla.uproject"), '{"changed": 1}\n')
        rc, out = self.r.sh("package.sh")
        self.assertEqual(rc, 1, out)
        self.assertIn("uncommitted", out)
        self.assertFalse(self.r.uat_called(), "UAT must not run on a dirty tree")

    def test_package_allow_dirty(self):
        write(os.path.join(self.r.dir, "UmbrellaElla.uproject"), '{"changed": 1}\n')
        rc, out = self.r.sh("package.sh", "--allow-dirty")
        self.assertEqual(rc, 0, out)
        self.assertIn("dirty=yes", read(os.path.join(self.r.dir, "Packaged", "BUILD_INFO.txt")))

    def test_package_and_build_lines_carry_the_commit(self):
        # Final-7 B H7, M8: check_pr reads commit= and dirty= from these lines
        head = subprocess.run(["git", "rev-parse", "HEAD"], cwd=self.r.dir, capture_output=True, text=True).stdout.strip()
        rc, out = self.r.sh("package.sh")
        self.assertEqual(rc, 0, out)
        self.assertRegex(out, r"package exit: 0  commit=[0-9a-f]{40}  dirty=no  target=UmbrellaElla ")
        rc, out = self.r.sh("build.sh", NONUNITY=1)
        self.assertRegex(out, r"build exit: 0  mode=nonunity  commit=[0-9a-f]{40}  warnings:")
        self.assertIn("commit=" + head, out)
        write(os.path.join(self.r.dir, "UmbrellaElla.uproject"), '{"changed": 1}\n')   # broken on purpose: dirty tree
        rc, out = self.r.sh("package.sh", "--allow-dirty")
        self.assertIn("dirty=yes", out)

    def test_workbench_package_never_shares_the_submission_folder(self):
        # Final-7 A M7: a tester package then a submission package leaves no workbench=1 BUILD_INFO in Packaged/
        self.assertEqual(self.r.sh("package.sh", "--workbench")[0], 0)
        stale = os.path.join(self.r.dir, "Packaged", "stale.txt")
        write(stale, "from an older run\n")
        rc, out = self.r.sh("package.sh")
        self.assertEqual(rc, 0, out)
        self.assertFalse(os.path.exists(stale), "the submission folder is emptied before each package")
        for d, _, files in os.walk(os.path.join(self.r.dir, "Packaged")):
            if "BUILD_INFO.txt" in files:
                self.assertIn("workbench=0", read(os.path.join(d, "BUILD_INFO.txt")))
        self.assertIn("workbench=1", read(os.path.join(self.r.dir, "Packaged-Workbench", "BUILD_INFO.txt")))

    def test_package_failure_writes_no_build_info(self):
        self.assertEqual(self.r.sh("package.sh", STUB_RC=4)[0], 4)
        self.assertFalse(os.path.exists(os.path.join(self.r.dir, "Packaged", "BUILD_INFO.txt")))

    def test_package_cook_error_fails(self):
        self.r.stub("Engine/Build/BatchFiles/RunUAT.sh", 'echo "LogCook: Error: missing asset"; exit 0')
        self.assertEqual(self.r.sh("package.sh")[0], 1)

    def test_package_timeout(self):
        rc, out = self.r.sh("package.sh", UE_TIMEOUT=1, STUB_SLEEP=30)
        self.assertEqual(rc, 124, out)

    # final-9 B C1: a game with the smoke hook also logs SMOKE_EFFECTIVE (no marked keys in this FakeRepo); NO_EFFECTIVE=1
    # leaves it out on purpose
    EFFECTIVE = ("trap '[ -n \"$L\" ] && [ -f \"$L\" ] && [ \"${NO_EFFECTIVE:-0}\" != 1 ] && for at in start end; do "
                 "echo \"LogUmbrellaElla: SMOKE_EFFECTIVE at=$at commit=${EFF_COMMIT:-abc1234} workbench=0 platform=Mac\" "
                 ">> \"$L\"; done' EXIT\n")

    def game(self, body):
        exe = os.path.join(self.r.base, "Game")
        write(exe, "#!/usr/bin/env bash\n" + self.EFFECTIVE +
                   'for a in "$@"; do case "$a" in -abslog=*) L="${a#-abslog=}";; esac; done\n' + body + "\n", exe=True)
        return exe

    def test_smoke_good_game_passes(self):
        exe = self.game('echo "LogUmbrellaElla: SMOKE_OK map=L_Graybox view=1920x1080 aspect=1.778 debugdraw=0 fps=60 worst_ms=20 commit=abc1234 input_vz=-120 input=ok gamepad=ok gp_vx=150 gp_attack_vz=-200 gp_shield_vz=-180 load_ms=800" > "$L"; exit 0')
        rc, out = self.r.sh("smoke.sh", exe)
        self.assertEqual(rc, 0, out)
        self.assertIn("SMOKE_OK=yes", out)

    def test_smoke_checks_build_info_commit_and_map(self):
        exe = self.game('echo "LogUmbrellaElla: SMOKE_OK map=L_Graybox view=1920x1080 aspect=1.778 debugdraw=0 fps=60 worst_ms=20 commit=abc1234 input_vz=-120 input=ok gamepad=ok gp_vx=150 gp_attack_vz=-200 gp_shield_vz=-180 load_ms=800" > "$L"; exit 0')
        write(os.path.join(os.path.dirname(exe), "BUILD_INFO.txt"), "commit=abc1234ffff\nconfig=Development\n")
        self.assertEqual(self.r.sh("smoke.sh", exe, SMOKE_MAP="L_Graybox")[0], 0)
        self.assertEqual(self.r.sh("smoke.sh", exe, SMOKE_MAP="L_Other")[0], 1)
        write(os.path.join(os.path.dirname(exe), "BUILD_INFO.txt"), "commit=9999999\nconfig=Development\n")
        rc, out = self.r.sh("smoke.sh", exe)
        self.assertEqual(rc, 1, out)
        self.assertIn("built from 9999999", out)

    def test_smoke_accessed_none_fails(self):
        exe = self.game('printf "Accessed None trying to read X\\nSMOKE_OK\\n" > "$L"; exit 0')
        rc, out = self.r.sh("smoke.sh", exe)
        self.assertEqual(rc, 1, out)
        self.assertIn("'Accessed None'=1", out)

    def test_smoke_crash_exit_code_fails(self):
        exe = self.game('echo "SMOKE_OK" > "$L"; exit 3')
        self.assertEqual(self.r.sh("smoke.sh", exe)[0], 1)

    def test_smoke_hang_fails(self):
        exe = self.game("sleep 30")
        rc, out = self.r.sh("smoke.sh", exe, SMOKE_TIMEOUT=1)
        self.assertEqual(rc, 1, out)
        self.assertIn("exit=124", out)

    def test_smoke_needs_an_exe(self):
        self.assertEqual(self.r.sh("smoke.sh")[0], 2)

    # Fake smoke hook that follows the contract in tools/ue_run.py. Env knobs break one field on purpose.
    DISPLAY_GAME = ('X=; Y=; W=windowed; M=L_Graybox; S=; C=0; R=; SHOT=; NOLOCK=; DD=0\n'
                    'for a in "$@"; do case "$a" in -ResX=*) X="${a#-ResX=}";; -ResY=*) Y="${a#-ResY=}";; '
                    '-SmokeShot=*) SHOT="${a#-SmokeShot=}";; -SmokeNoAspectLock) NOLOCK=--no-lock;; -SmokeDebugDraw) DD=1;; '
                    '-ReportExportPath=*) R="${a#-ReportExportPath=}";; '
                    '-fullscreen) W=fullscreen;; -SmokeMap=*) M="${a#-SmokeMap=}"; M="${M##*/}";; '
                    '-SmokeSection=*) S=" section=${a#-SmokeSection=}";; -SmokeRestartCycles=*) C="${a#-SmokeRestartCycles=}";; '
                    '-SmokeCrash) mkdir -p "$(dirname "$0")/UmbrellaElla/Saved/Crashes/forced$$";; '
                    'esac; done\n'
                    'if [ -n "${CRASH_ON_RUN:-}" ]; then k=$(( $(cat "$RUNS" 2>/dev/null || echo 0) + 1 )); echo "$k" > "$RUNS"; '
                    '[ "$k" = "$CRASH_ON_RUN" ] && mkdir -p "$(dirname "$0")/UmbrellaElla/Saved/Crashes/r$k"; fi\n'
                    '[ "${BREAK_ON_BAD_INI:-0}" = 1 ] && grep -q banana "$SETTINGS_INI" 2>/dev/null && exit 3\n'
                    # Packaged client-test mode: a report with one flow test, then CLIENT_LINE in the log.
                    'if [ -n "$R" ]; then mkdir -p "$R"; echo "{\\"tests\\":[{\\"fullTestPath\\":'
                    '\\"UmbrellaElla.Flow.TitleToPlayToSurvived\\",\\"state\\":\\"Success\\",\\"duration\\":${CLIENT_DUR:-38.2}}]}" '
                    '> "$R/index.json"; [ -n "$L" ] && echo "LogAutomation: done ${CLIENT_LINE:-}" > "$L"; '
                    '[ -n "${CLIENT_CRASH_INTO:-}" ] && mkdir -p "$CLIENT_CRASH_INTO/Saved/Crashes/c$$"; exit "${CLIENT_RC:-0}"; fi\n'
                    ': > "$L"; for i in $(seq 1 "$C"); do a=12; [ "$i" = "$C" ] && a=$((12 + ${DRIFT:-0})); '
                    'echo "LogUmbrellaElla: SMOKE_CYCLE n=$i actors=$a health=3 load_ms=${CYCLE_LOAD:-900}" >> "$L"; done\n'
                    # the view: the largest 16:9 box in the window (camera aspect lock), the whole window without it
                    'GX=${X:-1920}; GY=${Y:-1080}; if [ -n "$NOLOCK" ]; then VW=$GX; VH=$GY; '
                    'elif [ $((GX * 9)) -gt $((GY * 16)) ]; then VW=$(( (GY * 16 + 8) / 9 )); VH=$GY; '
                    'else VW=$GX; VH=$(( (GX * 9 + 8) / 16 )); fi\n'
                    'ASP=$(awk "BEGIN{printf \\"%.3f\\", $VW/$VH}")\n'
                    'if [ -n "$SHOT" ]; then python3 "' + FAKE_SHOT + '" "$SHOT" "$GX" "$GY" $NOLOCK ${SHOT_ARGS:-}; '
                    'echo "LogUmbrellaElla: SMOKE_SHOT at_s=5 w=$GX h=$GY" >> "$L"; fi\n'
                    'echo "LogUmbrellaElla: SMOKE_OK map=$M view=${VW}x${VH} aspect=$ASP debugdraw=$DD fps=${FPS:-60} worst_ms=${WORST:-20} commit=abc1234 '
                    'input_vz=${INPUT_VZ:--120} input=${INPUT:-ok} gamepad=${GAMEPAD:-ok} gp_vx=150 gp_attack_vz=-200 gp_shield_vz=-180 res=${GX}x${GY} win=$W textpx=${TEXTPX:-20} load_ms=${LOAD:-800}$S" >> "$L"\n'
                    '[ -n "${EXTRA_LINE:-}" ] && echo "$EXTRA_LINE" >> "$L"\n'
                    '[ -n "${CRASH_INTO:-}" ] && mkdir -p "$CRASH_INTO/Saved/Crashes/c$$"; exit 0')

    def test_smoke_display_run_passes_and_small_text_fails(self):
        exe = self.game(self.DISPLAY_GAME)
        rc, out = self.r.sh("smoke.sh", exe, SMOKE_RES="1280x720", SMOKE_WINDOW="windowed")
        self.assertEqual(rc, 0, out)
        self.assertIn("res=1280x720", out)
        rc, out = self.r.sh("smoke.sh", exe, SMOKE_RES="3840x2160", SMOKE_WINDOW="fullscreen", TEXTPX=12)
        self.assertEqual(rc, 1, out)
        self.assertIn("smallest UI text is 12 px", out)

    def test_smoke_low_fps_fails(self):
        exe = self.game(self.DISPLAY_GAME)
        rc, out = self.r.sh("smoke.sh", exe, FPS=3)
        self.assertEqual(rc, 1, out)
        self.assertIn("below the minimum 55", out)
        self.assertEqual(self.r.sh("smoke.sh", exe, FPS=3, SMOKE_MIN_FPS=0)[0], 0)

    def test_smoke_new_crash_folder_fails(self):
        exe = self.game(self.DISPLAY_GAME)
        rc, out = self.r.sh("smoke.sh", exe, CRASH_INTO=os.path.join(self.r.base, "UmbrellaElla"))
        self.assertEqual(rc, 1, out)
        self.assertIn("new crash folder", out)

    def test_smoke_alive_mode(self):
        exe = self.game('trap "exit 0" TERM; sleep 30 & wait')
        rc, out = self.r.sh("smoke.sh", exe, SMOKE_MODE="alive")
        self.assertEqual(rc, 0, out)
        self.assertIn("alive at 15", out)

    # Contract fields through the real script
    def test_smoke_script_restart_cycles_and_drift(self):
        exe = self.game(self.DISPLAY_GAME)
        rc, out = self.r.sh("smoke.sh", exe, SMOKE_RESTART_CYCLES=5)
        self.assertEqual(rc, 0, out)
        rc, out = self.r.sh("smoke.sh", exe, SMOKE_RESTART_CYCLES=5, DRIFT=1)
        self.assertEqual(rc, 1, out)
        self.assertIn("actor count drifted", out)

    def test_smoke_script_input_and_section(self):
        exe = self.game(self.DISPLAY_GAME)
        rc, out = self.r.sh("smoke.sh", exe, INPUT="none")
        self.assertEqual(rc, 1, out)
        self.assertEqual(self.r.sh("smoke.sh", exe, INPUT="none", SMOKE_REQUIRE_INPUT=0)[0], 0)
        rc, out = self.r.sh("smoke.sh", exe, SMOKE_SECTION="S5")
        self.assertEqual(rc, 0, out)
        self.assertIn("section=S5", out)

    def test_smoke_script_error_line_and_slow_frame_fail(self):
        exe = self.game(self.DISPLAY_GAME)
        rc, out = self.r.sh("smoke.sh", exe, EXTRA_LINE="LogScript: Error: Script Msg: bad")
        self.assertEqual(rc, 1, out)
        self.assertIn("'Error:'=1", out)
        rc, out = self.r.sh("smoke.sh", exe, WORST=50)
        self.assertEqual(rc, 1, out)
        self.assertIn("worst frame 50 ms", out)

    # The daily graph: one command, stops at the first failing step
    def daily(self, **env):
        exe = self.game(self.DISPLAY_GAME)
        env.setdefault("SMOKE_DESKTOP_RES", "3840x2160")
        return self.r.sh("daily.sh", SMOKE_EXE=exe, **env)

    def test_daily_all_green_writes_one_record(self):
        rc, out = self.daily()
        self.assertEqual(rc, 0, out)
        rec = read(os.path.join(self.r.dir, "Saved", "Logs", "pipeline", "daily-records.txt")).splitlines()
        self.assertEqual(len(rec), 1)
        for part in ("clean-tree=PASS", "build=PASS", "test=PASS(3/0/3)", "alone=PASS(0 new)",
                     "validate=PASS(err 0, warn 0)", "package=PASS(warn 0)", "smoke=PASS", "real-engine pipeline (",
                     "display=PASS(5 mode(s))", "shuffle=NOT RUN", "settings=PASS(garbage ini)", "client-test=NOT RUN", "shipping-alive=NOT RUN", "map list",
                     "restart cycles (SMOKE_RESTART_CYCLES not set)"):
            self.assertIn(part, rec[0])
        self.assertNotIn("section", rec[0])  # one arena, no section smoke (D-new-cut5)

    def add_workbench_target(self):
        write(os.path.join(self.r.dir, "Source", "UmbrellaEllaWorkbench.Target.cs"),
              'ProjectDefinitions.Add("UMBRELLAELLA_WORKBENCH=1");\n')
        git(self.r.dir, "add", "-A")
        git(self.r.dir, "commit", "-q", "-m", "workbench target")

    def test_daily_without_workbench_target_lists_it(self):
        rc, out = self.daily()
        self.assertEqual(rc, 0, out)
        line = next(ln for ln in out.splitlines() if ln.startswith("DAILY "))
        self.assertIn("workbench=NOT RUN", line)
        self.assertIn("workbench package (no Source/UmbrellaEllaWorkbench.Target.cs yet)", line)
        self.assertEqual(ue_run.not_checked_kind("workbench package (no Source/UmbrellaEllaWorkbench.Target.cs yet)"),
                         "workbench")

    def test_daily_packages_the_tester_build_after_the_smoke(self):
        self.add_workbench_target()
        targets = os.path.join(self.r.base, "targets.txt")
        rc, out = self.daily(UAT_TARGETS=targets)
        self.assertEqual(rc, 0, out)
        line = next(ln for ln in out.splitlines() if ln.startswith("DAILY "))
        self.assertIn("workbench=PASS(warn 0)", line)
        self.assertLess(line.index("smoke=PASS"), line.index("workbench=PASS"))
        self.assertEqual(read(targets).split(), ["workbench"], "one tester package, after the Development one")
        self.assertTrue(os.path.isfile(os.path.join(self.r.dir, "Packaged-Workbench", "Mac", "UmbrellaElla")))
        self.assertTrue(ue_run.good_daily(line))

    def test_daily_workbench_failure_fails_the_line(self):
        self.add_workbench_target()
        rc, out = self.daily(STUB_WB_RC=3)
        self.assertNotEqual(rc, 0, out)
        line = next(ln for ln in out.splitlines() if ln.startswith("DAILY "))
        self.assertIn("workbench=FAIL", line)
        self.assertIn("package=PASS", line)
        self.assertIn("smoke=PASS", line)
        self.assertFalse(ue_run.good_daily(line), "a failed tester package fails the DAILY line")

    def test_daily_smoke_failure_never_packages_the_workbench(self):
        self.add_workbench_target()
        targets = os.path.join(self.r.base, "targets.txt")
        rc, out = self.daily(UAT_TARGETS=targets, WORST=50)   # the smoke fails: worst frame over 33 ms
        self.assertNotEqual(rc, 0, out)
        self.assertIn("workbench=not run", out)
        self.assertFalse(os.path.exists(targets))

    def test_daily_build_is_non_unity(self):
        rc, out = self.daily()
        self.assertEqual(rc, 0, out)
        line = [ln for ln in out.splitlines() if ln.startswith("compiling ")]
        self.assertTrue(line, out)
        for flag in ("-DisableUnity", "-NoPCH", "-NoSharedPCH"):
            self.assertIn(flag, line[0])
        ps1 = read(os.path.join(ROOT, "tools", "ue_run.py"))
        self.assertIn('script("build", ["-NonUnity"], "build")', ps1)

    def test_daily_failing_tests_never_package(self):
        rc, out = self.daily(STUB_STATE="Fail")
        self.assertNotEqual(rc, 0, out)
        self.assertFalse(self.r.uat_called(), "package must not run after a failed test step")
        self.assertIn("test=FAIL(0/3/3) alone=not run shuffle=not run validate=not run package=not run smoke=not run", out)

    def test_daily_build_failure_stops_everything(self):
        rc, out = self.daily(STUB_RC=5)
        self.assertEqual(rc, 5, out)
        self.assertIn("build=FAIL test=not run", out)

    def test_daily_baseline_comes_from_the_last_record(self):
        self.assertEqual(self.daily()[0], 0)
        rc, out = self.daily(STUB_TESTS=2)
        self.assertNotEqual(rc, 0, out)
        self.assertIn("2 tests ran, baseline is 3", out)

    def test_daily_smokes_every_cooked_map(self):
        write(os.path.join(self.r.dir, "Config", "DefaultEngine.ini"), "GameDefaultMap=/Game/UmbrellaElla/Maps/L_Graybox.L_Graybox\n")
        write(os.path.join(self.r.dir, "Config", "DefaultGame.ini"), '+MapsToCook=(FilePath="/Game/UmbrellaElla/Maps/L_S3")\n')
        git(self.r.dir, "add", "-A")
        git(self.r.dir, "commit", "-q", "-m", "config")
        rc, out = self.daily(SMOKE_DISPLAY_MODES="1280x720:windowed")
        self.assertEqual(rc, 0, out)
        self.assertIn("smoke=PASS(2 map(s))", out)
        self.assertIn("SMOKE_GAME_MAP=/Game/UmbrellaElla/Maps/L_S3", out)

    def test_daily_skips_display_modes_bigger_than_the_monitor(self):
        rc, out = self.daily(SMOKE_DESKTOP_RES="1920x1080")
        self.assertEqual(rc, 0, out)
        self.assertIn("display=PASS(3 mode(s))", out)
        self.assertIn("display 3840x2160 fullscreen (monitor 1920x1080)", out)
        self.assertIn("display 2560x1080 windowed (monitor 1920x1080)", out)
        self.assertNotIn("display-3840x2160", out)
        rc, out = self.daily(SMOKE_DESKTOP_RES="800x600")
        self.assertEqual(rc, 1, out)
        self.assertIn("display=FAIL(no mode fits the monitor)", out)

    def test_daily_cycles_and_no_sections(self):
        rc, out = self.daily(SMOKE_SECTIONS="S4,S5", SMOKE_RESTART_CYCLES=5, SMOKE_DISPLAY_MODES="1280x720:windowed")
        self.assertEqual(rc, 0, out)
        self.assertIn("smoke=PASS(no map list)", out)
        self.assertNotIn("restart cycles (", out)
        rc, out = self.daily(SMOKE_RESTART_CYCLES=5, DRIFT=1, SMOKE_DISPLAY_MODES="1280x720:windowed")
        self.assertEqual(rc, 1, out)
        self.assertIn("smoke=FAIL", out)

    def test_daily_input_off_is_listed(self):
        rc, out = self.daily(SMOKE_REQUIRE_INPUT=0, INPUT="none", SMOKE_DISPLAY_MODES="1280x720:windowed")
        self.assertEqual(rc, 0, out)
        self.assertIn("input (SMOKE_REQUIRE_INPUT=0)", out)

    def test_daily_shipping_alive(self):
        good = os.path.join(self.r.base, "Ship")
        write(good, '#!/usr/bin/env bash\ntrap "exit 0" TERM; sleep 30 & wait\n', exe=True)
        rc, out = self.daily(SHIPPING_EXE=good, SMOKE_ALIVE_SECONDS=1, SMOKE_MAX_BOOT_S=0,
                             SMOKE_DISPLAY_MODES="1280x720:windowed")
        self.assertEqual(rc, 0, out)
        self.assertIn("shipping-alive=PASS", out)
        write(good, "#!/usr/bin/env bash\nexit 3\n", exe=True)
        rc, out = self.daily(SHIPPING_EXE=good, SMOKE_ALIVE_SECONDS=1, SMOKE_DISPLAY_MODES="1280x720:windowed")
        self.assertEqual(rc, 1, out)
        self.assertIn("shipping-alive=FAIL", out)

    def test_daily_dirty_run_is_marked(self):
        write(os.path.join(self.r.dir, "UmbrellaElla.uproject"), '{"changed": 1}\n')
        rc, out = self.r.sh("daily.sh", "--allow-dirty", SMOKE_EXE=self.game(self.DISPLAY_GAME),
                            SMOKE_DESKTOP_RES="3840x2160", SMOKE_DISPLAY_MODES="1280x720:windowed")
        self.assertEqual(rc, 0, out)
        self.assertRegex(out, r"DAILY [0-9a-f]+\+dirty ")

    def test_daily_refuses_dirty_tree(self):
        write(os.path.join(self.r.dir, "UmbrellaElla.uproject"), '{"changed": 1}\n')
        rc, out = self.daily()
        self.assertEqual(rc, 1, out)
        self.assertIn("clean-tree=FAIL build=not run", out)

    # Gap: the 1 s rule-test limit failed the required flow and content tests
    def test_daily_world_marked_flow_tests_are_not_held_to_one_second(self):
        rc, out = self.daily(STUB_NAMES="UmbrellaElla.Flow.TitleToPlayToSurvived=38.2,UmbrellaElla.Content.AllMapsLoad=6.5",
                             SMOKE_DISPLAY_MODES="1280x720:windowed")
        self.assertEqual(rc, 0, out)
        self.assertIn("test=PASS(5/0/5)", out)
        rc, out = self.daily(STUB_NAMES="UmbrellaElla.Flow.TitleToPlayToSurvived=38.2,UmbrellaElla.Move.Slow=1.5",
                             SMOKE_DISPLAY_MODES="1280x720:windowed")
        self.assertEqual(rc, 1, out)
        self.assertIn("UmbrellaElla.Move.Slow (1.50 s)", out)

    # Gap: the packaged client-test step only read the report
    def client(self, **env):
        return self.daily(CLIENT_TESTS=1, SMOKE_DISPLAY_MODES="1280x720:windowed", **env)

    def test_daily_client_test_with_a_30s_flow_test_passes(self):
        rc, out = self.client()
        self.assertEqual(rc, 0, out)
        self.assertIn("client-test=PASS", out)

    def test_daily_client_test_fails_on_crash_line_exit_code_or_crash_folder(self):
        for env, why in (({"CLIENT_LINE": "LogWindows: Fatal error: boom"}, "'Fatal error'"),
                         ({"CLIENT_LINE": "LogScript: Error: Script Msg: bad"}, "'Error:'"),
                         ({"CLIENT_RC": 3}, "exit code 3"),
                         ({"CLIENT_CRASH_INTO": os.path.join(self.r.base, "UmbrellaElla")}, "new crash folder")):
            with self.subTest(why=why):
                rc, out = self.client(**env)
                self.assertEqual(rc, 1, out)
                self.assertIn("client-test=FAIL", out)
                self.assertIn(why, out)

    # Gap: tests were checked alone only at gates. Daily runs each newly merged test-map test alone once.
    def merged_map(self):
        write(os.path.join(self.r.dir, "pipeline", "qa", "test-map.md"),
              "| MVP | Required tests | Card | Status |\n|---|---|---|---|\n"
              "| 1 | `UmbrellaElla.Move.A`, `UmbrellaElla.Move.B` | #1 | merged |\n")
        git(self.r.dir, "add", "-A")
        git(self.r.dir, "commit", "-q", "-m", "map")
        return {"STUB_NAMES": "UmbrellaElla.Move.A,UmbrellaElla.Move.B", "SMOKE_DISPLAY_MODES": "1280x720:windowed"}

    def test_daily_runs_new_merged_tests_alone_once(self):
        env = self.merged_map()
        rc, out = self.daily(**env)
        self.assertEqual(rc, 0, out)
        self.assertIn("alone=PASS(2 new)", out)
        self.assertIn("TEST_FILTER=UmbrellaElla.Move.B", out)
        rc, out = self.daily(**env)
        self.assertEqual(rc, 0, out)
        self.assertIn("alone=PASS(0 new)", out)

    def test_daily_test_failing_alone_stops_the_build(self):
        env = self.merged_map()
        rc, out = self.daily(STUB_ALONE_FAIL="UmbrellaElla.Move.B", **env)
        self.assertEqual(rc, 1, out)
        self.assertIn("alone=FAIL(UmbrellaElla.Move.B) shuffle=not run validate=not run package=not run", out)
        rc, out = self.daily(ALONE_NEW=0, **env)
        self.assertEqual(rc, 0, out)
        self.assertIn("alone=NOT RUN", out)
        self.assertIn("alone (ALONE_NEW=0)", out)

    # Gap: no asset or data validation ran
    def test_daily_validation_error_stops_before_package(self):
        rc, out = self.daily(STUB_VALIDATE="LogDataValidation: Error: /Game/X has a bad reference\n",
                             SMOKE_DISPLAY_MODES="1280x720:windowed")
        self.assertEqual(rc, 1, out)
        self.assertIn("validate=FAIL(err 1, warn 0) package=not run", out)
        self.assertFalse(self.r.uat_called())
        rc, out = self.daily(STUB_VALIDATE="LogDataValidation: Warning: /Game/Y unused\n",
                             SMOKE_DISPLAY_MODES="1280x720:windowed")
        self.assertEqual(rc, 0, out)
        self.assertIn("validate=PASS(err 0, warn 1)", out)

    def test_validate_nonzero_exit_fails(self):
        self.assertEqual(self.r.sh("validate.sh")[0], 0)
        rc, out = self.r.sh("validate.sh", STUB_VALIDATE_RC=1)
        self.assertEqual(rc, 1, out)

    # Gap: the cook warning count was recorded but never gated
    def test_daily_cook_warnings_may_not_rise_without_a_decision(self):
        write(os.path.join(self.r.dir, "docs", "decisions.md"), "| D-new-cookwarn | accept 2 warnings | open |\n")
        git(self.r.dir, "add", "-A")
        git(self.r.dir, "commit", "-q", "-m", "decisions")
        modes = {"SMOKE_DISPLAY_MODES": "1280x720:windowed"}
        rc, out = self.daily(STUB_WARN=1, **modes)
        self.assertEqual(rc, 0, out)
        self.assertIn("package=PASS(warn 1)", out)
        rc, out = self.daily(STUB_WARN=2, **modes)
        self.assertEqual(rc, 1, out)
        self.assertIn("package=FAIL(warn 2, up from 1) smoke=not run", out)
        rc, out = self.daily(STUB_WARN=2, COOK_WARN_DECISION="D-nope", **modes)
        self.assertEqual(rc, 1, out)
        rc, out = self.daily(STUB_WARN=2, COOK_WARN_DECISION="D-new-cookwarn", **modes)
        self.assertEqual(rc, 0, out)
        self.assertIn("package=PASS(warn 2, up from 1 by D-new-cookwarn)", out)
        self.assertEqual(self.daily(STUB_WARN=1, **modes)[0], 0)

    # Gap: no rule that tests clean up what they write
    def test_test_script_fails_on_left_files_and_resets_old_ones(self):
        rc, out = self.r.sh("test.sh", STUB_LEAVE=1)
        self.assertEqual(rc, 1, out)
        self.assertIn("tests left file(s)", out)
        rc, out = self.r.sh("test.sh")
        self.assertEqual(rc, 0, out)
        self.assertIn("reset: removed 1 leftover file(s)", out)

    def test_smoke_script_slow_load_fails(self):
        exe = self.game(self.DISPLAY_GAME)
        rc, out = self.r.sh("smoke.sh", exe, LOAD=12000)
        self.assertEqual(rc, 1, out)
        self.assertIn("load took 12000 ms", out)
        self.assertEqual(self.r.sh("smoke.sh", exe, LOAD=12000, SMOKE_MAX_LOAD_MS=0)[0], 0)

    # Gap: tests could change settings or save slots outside Saved/UmbrellaEllaTests
    def test_test_script_fails_when_tests_change_settings(self):
        rc, out = self.r.sh("test.sh")
        self.assertEqual(rc, 0, out)
        self.assertIn("user state: 0 changed", out)
        rc, out = self.r.sh("test.sh", STUB_SETTINGS=1)
        self.assertEqual(rc, 1, out)
        self.assertIn("added: Saved/Config/Mac/GameUserSettings.ini", out)

    # Gap: tests never ran in a shuffled order
    def test_daily_shuffle_runs_merged_tests_in_seeded_order(self):
        env = self.merged_map()
        rc, out = self.daily(SHUFFLE_SEED=7, **env)
        self.assertEqual(rc, 0, out)
        self.assertIn("shuffle=PASS(seed 7, 2 tests)", out)
        self.assertIn("shuffle: seed=7 order=", out)
        rc, out = self.daily(SHUFFLE_SEED=7, STUB_MULTI_FAIL="UmbrellaElla.Move.A", **env)
        self.assertEqual(rc, 1, out)
        self.assertIn("shuffle=FAIL(seed 7, 2 tests) validate=not run", out)

    # Gap: one smoke per map missed a crash that shows up in 1 of N boots
    def test_daily_smoke_repeat_catches_an_intermittent_crash(self):
        runs = os.path.join(self.r.base, "runs.txt")
        modes = {"SMOKE_DISPLAY_MODES": "1280x720:windowed", "RUNS": runs}
        rc, out = self.daily(SMOKE_REPEAT=5, **modes)
        self.assertEqual(rc, 0, out)
        self.assertIn("smoke=PASS(no map list, repeat 5/5)", out)
        rc, out = self.daily(SMOKE_REPEAT=5, CRASH_ON_RUN=3, **modes)
        self.assertEqual(rc, 1, out)
        self.assertIn("smoke=FAIL(no map list, repeat 2/5)", out)

    # Gap: a crash forced on purpose must be caught (card 0.6 proves the real one)
    def test_smoke_forced_crash_is_caught(self):
        exe = self.game(self.DISPLAY_GAME)
        self.assertEqual(self.r.sh("smoke.sh", exe)[0], 0)
        rc, out = self.r.sh("smoke.sh", exe, SMOKE_FORCE_CRASH=1)
        self.assertEqual(rc, 1, out)
        self.assertIn("new crash folder", out)

    # Gap: no boot with a broken or old GameUserSettings.ini
    def test_daily_settings_garbage_and_old_ini_restore_the_real_one(self):
        ini = os.path.join(self.r.base, "gus", "GameUserSettings.ini")
        write(ini, "real settings\n")
        old = os.path.join(self.r.base, "G2-GameUserSettings.ini")
        write(old, "[/Script/Engine.GameUserSettings]\nFullscreenMode=1\n")
        modes = {"SMOKE_DISPLAY_MODES": "1280x720:windowed"}
        rc, out = self.daily(SETTINGS_OLD_INI=old, **modes)
        self.assertEqual(rc, 0, out)
        self.assertIn("settings=PASS(garbage+old ini)", out)
        self.assertEqual(read(ini), "real settings\n")
        rc, out = self.daily(BREAK_ON_BAD_INI=1, **modes)
        self.assertEqual(rc, 1, out)
        self.assertIn("settings=FAIL(garbage ini) client-test=not run", out)
        self.assertIn("settings old-ini (SETTINGS_OLD_INI not set", out)
        self.assertEqual(read(ini), "real settings\n")

    # Gap: the Shipping check was optional; from Day 3 it is required and timed
    def test_daily_shipping_required_and_boot_time(self):
        modes = {"SMOKE_DISPLAY_MODES": "1280x720:windowed"}
        rc, out = self.daily(SHIPPING_REQUIRED=1, **modes)
        self.assertEqual(rc, 1, out)
        self.assertIn("shipping-alive=FAIL(SHIPPING_EXE not set)", out)
        good = os.path.join(self.r.base, "Ship")
        write(good, '#!/usr/bin/env bash\ntrap "exit 0" TERM; sleep 30 & wait\n', exe=True)
        rc, out = self.daily(SHIPPING_EXE=good, SMOKE_ALIVE_SECONDS=1, **modes)   # default limit 20 s
        if os.name != "nt":
            self.assertEqual(rc, 1, out)
            self.assertIn("boot_s=unknown", out)

    def test_daily_lists_the_reference_host(self):
        rc, out = self.daily(SMOKE_DISPLAY_MODES="1280x720:windowed")
        self.assertIn("reference host (REF_HOST not set", out)
        import platform
        rc, out = self.daily(SMOKE_DISPLAY_MODES="1280x720:windowed", REF_HOST=platform.node())
        self.assertEqual(rc, 0, out)
        self.assertNotIn("reference host", out)
        self.assertNotIn("fps on reference host", out)


class Ps1ParityTests(unittest.TestCase):
    """PowerShell is not installed on every machine, so check by text that each .ps1 uses the same
    ue_run.py subcommands and switches as its .sh twin."""

    def uses(self, path):
        text = read(path)
        found = set(re.findall(r"\b(run|alive|clean-tree|build-info|smoke-log|crash-list|crash-check|daily|state-list|"
                               r"state-check)\b(?= )", text))
        found |= {flag for flag in ("--max-load-ms", "UmbrellaEllaTests", "cook warnings:", "-run=DataValidation",
                                    "validate: errors=", "leftover file(s)") if flag in text}
        found |= {flag for flag in ("--timeout", "--allow-dirty", "SMOKE_OK", "-SmokeQuitAfter=15", "--min-fps",
                                    "--expect-res", "--expect-win", "--min-text-px", "-SmokeMap=", "-ResX=",
                                    "--max-rule-seconds", "--shell", "--max-frame-ms", "--no-input-check",
                                    "--no-player-maps", "--expect-section", "--restart-cycles", "-SmokeSection=",
                                    "-SmokeRestartCycles=", "SMOKE_ALIVE_SECONDS", "--max-boot-s", "-SmokeCrash",
                                    "SMOKE_MAX_BOOT_S", "SMOKE_FORCE_CRASH", "workbench-check", "--expect-workbench",
                                    "--workbench", "UmbrellaEllaWorkbench") if flag in text}
        return found

    def test_each_script_has_a_twin_with_the_same_steps(self):
        ue = os.path.join(ROOT, "tools", "ue")
        for name in ("build", "package", "test", "smoke", "daily", "validate"):
            with self.subTest(script=name):
                sh = self.uses(os.path.join(ue, name + ".sh"))
                ps = self.uses(os.path.join(ue, name + ".ps1"))
                self.assertEqual(sh - {"SMOKE_OK"}, ps - {"SMOKE_OK"})


if __name__ == "__main__":
    unittest.main()
