"""Final-10 dry runs A and B: each adversarial fix with a passing case and a case broken on purpose. The honest-path
fixes run in tests/test_honest_jam.py (the walk) and its HonestSuiteIsHermetic class."""
import contextlib
import io
import json
import os
import shutil
import subprocess
import sys
import tempfile
import unittest
import unittest.mock
import zipfile

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, os.path.join(ROOT, "tools"))
sys.path.insert(0, HERE)
import bake_preset  # noqa: E402
import check_automation_report as car  # noqa: E402
import check_card  # noqa: E402
import check_pr  # noqa: E402
import ue_run  # noqa: E402

MANIFEST = json.load(open(os.path.join(ROOT, "docs", "feature-manifest.json"), encoding="utf-8"))
MV = MANIFEST["manifest_version"]
TUNING_H = ("#pragma once\nUSTRUCT()\nstruct FMotorTuning\n{\n\tGENERATED_BODY()\n\n"
            "\tUPROPERTY(EditAnywhere)\n\tfloat MoveSpeed = 350.0f;   // bake: CORE-01.move_speed\n\n"
            "\tUPROPERTY(EditAnywhere)\n\tint32 Seed = 20261112;   // bake: OWL-01.seed\n};\n")
SETTINGS_H = ("#pragma once\nUCLASS(Config = Game)\nclass UMBRELLAELLA_API UUmbrellaTuning final : public UDeveloperSettings\n"
              "{\n\tGENERATED_BODY()\npublic:\n\tUPROPERTY(Config)\n\tFMotorTuning Motor;\n};\n")


def write(path, text):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as fh:
        fh.write(text)


def git(root, *args):
    p = subprocess.run(["git", "-c", "user.email=t@t", "-c", "user.name=t", "-c", "core.hooksPath=/dev/null", *args],
                       cwd=root, capture_output=True, text=True)
    assert p.returncode == 0, p.stderr
    return p.stdout.strip()


def repo(with_git=False):
    root = tempfile.mkdtemp()
    write(os.path.join(root, "docs", "feature-manifest.json"), json.dumps(MANIFEST))
    write(os.path.join(root, "Source", "UmbrellaElla", "Public", "Motor", "MotorTuning.h"), TUNING_H)
    write(os.path.join(root, "Source", "UmbrellaElla", "Public", "Core", "UmbrellaTuning.h"), SETTINGS_H)
    if with_git:
        git(root, "init", "-q", "-b", "main")
        git(root, "add", "-A")
        git(root, "commit", "-q", "-m", "a")
    return root


def line(at="start", commit="abc1234", **vals):
    v = {"MotorTuning.MoveSpeed": "350.000000", "MotorTuning.Seed": "20261112"}
    v.update(vals)
    extra = " outcome=quit" if at == "end" else ""
    return (f"[2026.11.12-19.14.04:000][  1]LogUmbrellaElla: SMOKE_EFFECTIVE at={at}{extra} commit={commit} "
            f"workbench=0 platform=Windows manifest={MV} " + " ".join(f"{k}={x}" for k, x in v.items()))


def run_effective(root, text):
    log = os.path.join(root, "g.log")
    write(log, text)
    with contextlib.redirect_stdout(io.StringIO()) as out:
        rc = bake_preset.main(["--root", root, "effective", log])
    return rc, out.getvalue()


class GenericHookFields(unittest.TestCase):
    """A H1: the hook reports reflected `<Struct>.<Field>`; the tool maps each to its key from the marked line."""

    def setUp(self):
        self.root = repo()
        self.addCleanup(shutil.rmtree, self.root, True)

    def test_fields_map_to_keys(self):
        self.assertEqual(bake_preset.field_keys(self.root),
                         {"MotorTuning.MoveSpeed": "CORE-01.move_speed", "MotorTuning.Seed": "OWL-01.seed"})
        rc, out = run_effective(self.root, line() + "\n" + line("end") + "\n")
        self.assertEqual(rc, 0, out)
        self.assertIn("keys=2 lines=2", out)

    def test_a_drifted_field_names_its_key(self):
        rc, out = run_effective(self.root, line() + "\n" + line("end", **{"MotorTuning.MoveSpeed": "650"}) + "\n")
        self.assertEqual(rc, 1, out)
        self.assertIn("at=end outcome=quit: CORE-01.move_speed: the running game has 650", out)


class EndOfRunRead(unittest.TestCase):
    """B H3: one at=start and at least one at=end line; a write after startup shows in the end line."""

    def setUp(self):
        self.root = repo()
        self.addCleanup(shutil.rmtree, self.root, True)

    def test_start_only_fails(self):
        rc, out = run_effective(self.root, line() + "\n")
        self.assertEqual(rc, 1, out)
        self.assertIn("no `SMOKE_EFFECTIVE at=end` line", out)

    def test_two_starts_fail(self):
        rc, out = run_effective(self.root, line() + "\n" + line() + "\n" + line("end") + "\n")
        self.assertEqual(rc, 1, out)
        self.assertIn("2 `SMOKE_EFFECTIVE at=start` line(s)", out)

    def test_check_pr_wants_the_end_line(self):
        ev = line().split("]")[-1].strip()
        self.assertTrue(any("at=end" in p for p in check_pr.effective_evidence_problems(ev, None, self.root)))
        ev2 = ev + "\n" + line("end").split("]")[-1].strip()
        self.assertFalse([p for p in check_pr.effective_evidence_problems(ev2, None, self.root) if "at=end" in p])


class StaticOneSource(unittest.TestCase):
    """B H3: GetMutableDefault, const_cast and non-const copies of a marked struct are second sources."""

    def setUp(self):
        self.root = repo()
        self.addCleanup(shutil.rmtree, self.root, True)
        self.cpp = os.path.join(self.root, "Source", "UmbrellaElla", "Private", "Motor", "PlayerMotorComponent.cpp")

    def probs(self, body):
        write(self.cpp, body)
        return bake_preset.one_source_problems(self.root, bake_preset.markers(self.root))

    def test_a_const_read_passes(self):
        self.assertEqual(self.probs("const FMotorTuning& T = GetDefault<UUmbrellaTuning>()->Motor;\n"
                                    "float S = GetDefault<UUmbrellaTuning>()->Motor.MoveSpeed;\n"), [])

    def test_copies_and_mutable_writes_fail(self):
        for body in ("FMotorTuning Tuning;\n", "FMotorTuning* P = &Other;\n",
                     "UUmbrellaTuning* T = GetMutableDefault<UUmbrellaTuning>();\n",
                     "auto* T = const_cast<UUmbrellaTuning*>(GetDefault<UUmbrellaTuning>());\n"):
            with self.subTest(body=body):
                self.assertTrue(self.probs(body), body)

    def test_workbench_block_and_tests_are_exempt(self):
        self.assertEqual(self.probs("#if UMBRELLAELLA_WORKBENCH\nFMotorTuning RunCopy;\n#endif\n"), [])
        write(os.path.join(self.root, "Source", "UmbrellaElla", "Private", "Tests", "Motor", "MoveTest.cpp"),
              "FMotorTuning T; T.Seed = 3;\n")
        probs = bake_preset.one_source_problems(self.root, bake_preset.markers(self.root))
        self.assertFalse([p for p in probs if "non-const" in p], probs)


class AnchoredLine(unittest.TestCase):
    """B M1, B M2, B M3: only the hook's own line counts, a key given twice fails, whole numbers are exact."""

    def setUp(self):
        self.root = repo()
        self.addCleanup(shutil.rmtree, self.root, True)

    def test_command_line_echo_does_not_count(self):
        forged = "[x][0]LogInit: Command Line: -SmokeMap=/Game/M " + line().split("]: ")[-1].split("]")[-1].strip()
        rc, out = run_effective(self.root, forged + "\n")
        self.assertEqual(rc, 1, out)
        self.assertIn("no SMOKE_EFFECTIVE line", out)
        rc, out = run_effective(self.root, forged + "\n" + line() + "\n" + line("end") + "\n")
        self.assertEqual(rc, 0, out)

    def test_a_key_twice_fails(self):
        rc, out = run_effective(self.root, line(**{"CORE-01.move_speed": "350"}) + "\n" + line("end") + "\n")
        self.assertEqual(rc, 1, out)
        self.assertIn("CORE-01.move_speed twice", out)
        e = ue_run.parse_effective("SMOKE_EFFECTIVE commit=a CORE-03.max_health=200 CORE-03.max_health=100")
        self.assertEqual(e["_dup"], "CORE-03.max_health")

    def test_the_seed_is_exact(self):
        self.assertTrue(bake_preset.same(20261112, 20261112.0))
        self.assertFalse(bake_preset.same(20261127, 20261112))
        self.assertTrue(bake_preset.same(0.65, 0.649999976))   # float32 print of 0.65
        rc, out = run_effective(self.root, line() + "\n" + line("end", **{"MotorTuning.Seed": "20261127"}) + "\n")
        self.assertEqual(rc, 1, out)
        self.assertIn("OWL-01.seed", out)


class BuiltCommitTree(unittest.TestCase):
    """B M6, A M6: the game is judged against the tree of the commit it was built from, not the checkout."""

    def test_built_commit_tree(self):
        root = repo(with_git=True)
        self.addCleanup(shutil.rmtree, root, True)
        a = git(root, "rev-parse", "HEAD")
        p = os.path.join(root, "Source", "UmbrellaElla", "Public", "Motor", "MotorTuning.h")
        with open(p) as fh:
            write(p, fh.read().replace("350.0f", "375.0f"))
        git(root, "commit", "-qam", "b")
        # a game built from a at 350 passes though the checkout (b) says 375
        rc, out = run_effective(root, line(commit=a[:12]) + "\n" + line("end", commit=a[:12]) + "\n")
        self.assertEqual(rc, 0, out)
        # broken on purpose: that game at 375 runs a value its own commit never had
        rc, out = run_effective(root, line(commit=a[:12], **{"MotorTuning.MoveSpeed": "375"}) + "\n"
                                + line("end", commit=a[:12], **{"MotorTuning.MoveSpeed": "375"}) + "\n")
        self.assertEqual(rc, 1, out)
        v = {"MotorTuning.MoveSpeed": "375"}
        rc, out = run_effective(root, line(commit="0123456789ab", **v) + "\n" + line("end", commit="0123456789ab", **v) + "\n")
        self.assertEqual(rc, 0, out)   # a clone behind the build: the checkout decides, and it says so
        self.assertIn("WARN: the game was built from 0123456789ab, which is not a commit in this clone", out)


class NearestAncestorBaseline(unittest.TestCase):
    """B H5: the baseline is the nearest ancestor commit's line, whatever order the lines were written in."""

    def test_backfill_line_never_wins(self):
        root = tempfile.mkdtemp()
        self.addCleanup(shutil.rmtree, root, True)
        git(root, "init", "-q", "-b", "main")
        write(os.path.join(root, "f"), "1")
        git(root, "add", "-A")
        git(root, "commit", "-qm", "A")
        a = git(root, "rev-parse", "HEAD")
        write(os.path.join(root, "f"), "2")
        git(root, "commit", "-qam", "B")
        b = git(root, "rev-parse", "HEAD")
        rec = os.path.join(root, "rec.txt")
        write(rec, f"DAILY {b[:12]} | h | Development | test=PASS(9/0/9)\nDAILY {a[:12]} | h | Development | test=PASS(7/0/7)\n")
        self.assertEqual(ue_run.ancestry_baseline(root, rec), 9)
        # broken on purpose: two tests vanish; against the nearest baseline the report fails
        report = {"tests": [{"fullTestPath": f"UmbrellaElla.A.T{i}", "state": "Success", "duration": 0.1} for i in range(7)]}
        self.assertTrue(car.evaluate(report, 9)["problems"])
        git(root, "checkout", "-q", a)
        self.assertEqual(ue_run.ancestry_baseline(root, rec), 7)


class LaunchBinding(unittest.TestCase):
    """B H1, B H2, A M2: the LAUNCH line names the zip member it smoked; the gate record re-hashes it."""

    def setUp(self):
        self.d = tempfile.mkdtemp()
        self.addCleanup(shutil.rmtree, self.d, True)
        self.exe = os.path.join(self.d, "dl", "UmbrellaElla.exe")
        write(self.exe, "good build\n")
        self.zip = os.path.join(self.d, "T.zip")
        with zipfile.ZipFile(self.zip, "w") as z:
            z.write(self.exe, "UmbrellaElla.exe")
        self.log = os.path.join(self.d, "g.log")
        write(self.log, line() + "\n" + line("end") + "\n[x]LogUmbrellaElla: SMOKE_OK map=L_Graybox view=1920x1080 aspect=1.778 debugdraw=0 fps=60\n")
        self.rec = os.path.join(self.d, "rec.txt")

    def record(self, exe):
        with contextlib.redirect_stdout(io.StringIO()) as out:
            rc = ue_run.launch_record(self.d, self.zip, [self.log], self.rec, exe)
        return rc, out.getvalue()

    def test_the_zip_member_passes_and_another_exe_fails(self):
        rc, out = self.record(self.exe)
        self.assertEqual(rc, 0, out)
        self.assertIn("exe=UmbrellaElla.exe exe_sha256=", out)
        other = os.path.join(self.d, "Packaged", "UmbrellaElla.exe")
        write(other, "another build\n")
        rc, out = self.record(other)
        self.assertEqual(rc, 1, out)
        self.assertIn("is not a file of T.zip", out)

    def problems(self, text, daily="DAILY abc1234 | RICK-PC/Windows 10 | x"):
        hit = check_card.LAUNCH_LINE.match(text)
        self.assertTrue(hit, text)
        return check_card.launch_line_problems(hit, self.zip, daily, "", None, self.d, None, "G1", bake_preset, ue_run)

    def test_gate_record_rehashes_the_member(self):
        self.record(self.exe)
        good = open(self.rec).read().strip()
        base = [p for p in self.problems(good) if "not a commit" not in p]
        self.assertEqual(base, [])
        # broken on purpose: a hand-made line (no exe fields), a tampered exe hash, workbench=1, the packaging host
        bad = good.replace(" exe=UmbrellaElla.exe", "").split(" exe_sha256=")[0] + " commit=" + good.split(" commit=", 1)[1]
        self.assertTrue(any("not written by" in p for p in self.problems(bad)))
        h = good.split("exe_sha256=")[1][:64]
        self.assertTrue(any("is not that file" in p for p in self.problems(good.replace(h, "0" * 64))))
        self.assertTrue(any("workbench=1 build" in p for p in self.problems(good.replace("workbench=0", "workbench=1"))))
        node = good.split("host=")[1].split("/")[0]
        self.assertTrue(any("packaging machine itself" in p
                            for p in self.problems(good, daily=f"DAILY abc1234 | {node}/Windows 10 | x")))


class GateRecordReruns(unittest.TestCase):
    """A H5, A M3, A M5: the DAILY host, merge-check and the UI line are re-derived, not trusted."""

    def test_daily_host(self):
        # final-11 A H5: hermetic; card 0.0's filled People table names the real packaging machine
        with unittest.mock.patch.object(check_card, "packaging_machine", lambda root=None: "RICK-PC"):
            self.assertEqual(check_card.daily_host_problems("DAILY abc | RICK-PC/Windows 10 | x", ROOT), [])
        self.assertTrue(check_card.daily_host_problems("DAILY abc | Joans-MBP.home/Darwin 23.6.0 | x", ROOT))
        self.assertIsNone(check_card.DAILY_MAC_FALLBACK)   # Josh's pending decision: Win64 only today

    def test_merge_check_and_ui_rerun(self):
        root = repo(with_git=True)
        self.addCleanup(shutil.rmtree, root, True)
        git(root, "tag", "jam-start")
        write(os.path.join(root, "x"), "1")
        # the title Quit button (ui_check quit, U15): without it even G1's plain `ui_check ci` fails
        write(os.path.join(root, "Source", "UmbrellaElla", "Private", "UI", "TitleMenu.cpp"),
              "void UTitleMenu::OnQuit() { UKismetSystemLibrary::QuitGame(this, nullptr, EQuitPreference::Quit, false); }\n")
        git(root, "add", "-A")
        git(root, "commit", "-qm", "UE-1")
        sha = git(root, "rev-parse", "HEAD")
        lines = {"build": f"{sha[:12]} | T.zip | Development"}
        good = [f"DAILY {sha[:12]} | RICK-PC/Windows 10 | Development | package=PASS smoke=PASS(1 map(s))"]
        out = check_card.machine_record_problems(lines, "G1", good, root)
        self.assertFalse([p for p in out if "merge-check" in p], out)
        self.assertFalse([p for p in out if "ui_check" in p], out)
        out = check_card.machine_record_problems(lines, "G1", ["PLAYTHROUGH 0000000 | x"], root)
        self.assertTrue([p for p in out if "merge-check" in p], out)
        out = check_card.machine_record_problems(lines, "G2", good, root)
        self.assertTrue([p for p in out if "ui_check ci --release" in p], out)


class TargetsPassTheCommit(unittest.TestCase):
    """A M10: every Target.cs passes UMBRELLAELLA_BUILD_COMMIT once one does."""

    def test_targets(self):
        root = tempfile.mkdtemp()
        self.addCleanup(shutil.rmtree, root, True)
        stamp = 'ProjectDefinitions.Add("UMBRELLAELLA_BUILD_COMMIT=\\"" + x + "\\"");\n'
        write(os.path.join(root, "Source", "UmbrellaElla.Target.cs"), 'ProjectDefinitions.Add("UMBRELLAELLA_WORKBENCH=0");\n' + stamp)
        write(os.path.join(root, "Source", "UmbrellaEllaEditor.Target.cs"), 'ProjectDefinitions.Add("UMBRELLAELLA_WORKBENCH=1");\n')
        self.assertTrue(any("UmbrellaEllaEditor.Target.cs does not define" in p for p in ue_run.workbench_check(root)))
        write(os.path.join(root, "Source", "UmbrellaEllaEditor.Target.cs"),
              'ProjectDefinitions.Add("UMBRELLAELLA_WORKBENCH=1");\n' + stamp)
        self.assertEqual(ue_run.workbench_check(root), [])


class WorldTestsByDefault(unittest.TestCase):
    """A H4: a `(world)` test-map mark counts in plain test.sh (--world-map), not only with --test-map."""

    def test_world_map(self):
        d = tempfile.mkdtemp()
        self.addCleanup(shutil.rmtree, d, True)
        rep = os.path.join(d, "index.json")
        write(rep, json.dumps({"tests": [{"fullTestPath": "UmbrellaElla.Flow.TitleToPlayToSurvived", "state": "Success",
                                          "duration": 31.0}]}))
        tm = os.path.join(ROOT, "pipeline", "qa", "test-map.md")
        with contextlib.redirect_stdout(io.StringIO()):
            self.assertEqual(car.main([rep, "--world-map", tm, "--commit", "abc1234"]), 0)
            self.assertEqual(car.main([rep, "--commit", "abc1234"]), 1)   # broken on purpose: no marks read
        self.assertIn('--world-map "$WMAP"', open(os.path.join(ROOT, "tools", "ue", "test.sh")).read())
        self.assertIn('"--world-map", $WMap', open(os.path.join(ROOT, "tools", "ue", "test.ps1")).read())


class RevertNeedsItsInverse(unittest.TestCase):
    """A H3: `Revert of:` waives evidence only with a base and an exact inverse diff."""

    def test_no_base_fails(self):
        import lane_guard
        body = lane_guard.revert_body("a" * 40, "UE-21: lift", "b" * 40, ["Source/x.h"], "21", "Josh")
        probs = check_pr.problems(body, ["Source/x.h"], None, ROOT, None, None)
        self.assertTrue(any("needs the PR base" in p for p in probs), probs)
        self.assertFalse([p for p in probs if "section" in p or "Journal" in p or "Task" in p], probs)


if __name__ == "__main__":
    unittest.main()
