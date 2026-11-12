"""Final-9 dry runs A and B: each adversarial fix with a passing case and a case broken on purpose. The honest-path
fixes run in tests/test_honest_jam.py."""
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

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, os.path.join(ROOT, "tools"))
sys.path.insert(0, HERE)
import bake_preset  # noqa: E402
import check_card  # noqa: E402
import module_check  # noqa: E402
import test_ue_scripts as tus  # noqa: E402
import ue_run  # noqa: E402

# the frozen GDD 1.3 manifest: these rules use its ranged, tunable keys (GDD SH1.0 prints no ranges yet)
MANIFEST = json.load(open(os.path.join(ROOT, "tests", "fixtures", "gdd13", "docs", "feature-manifest.json"), encoding="utf-8"))
TUNING_H = ("#pragma once\nUSTRUCT()\nstruct FCore01Tuning\n{\n\tGENERATED_BODY()\n"
            "\tUPROPERTY(EditAnywhere) float MoveSpeed = 350.0f;   // bake: CORE-01.move_speed\n};\n")
FLAGS_CPP = "static const FFlag D[] = {\n\t{ EFeatureId::DEF_01, true },   // bake: DEF-01.enabled\n};\n"
RICHARD = ("| ID | Decision | Owner | Status |\n|---|---|---|---|\n"
           "| D-hp | Ship 200 HP. Overrides: {ids} | Richard | DECIDED 2026-11-15 ({who}) |\n")


def write(path, text):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as fh:
        fh.write(text)


def repo():
    root = tempfile.mkdtemp()
    write(os.path.join(root, "docs", "feature-manifest.json"), json.dumps(MANIFEST))
    shutil.copy(os.path.join(ROOT, "pipeline", "qa", "presets.json"), os.path.join(root, "x.json"))
    write(os.path.join(root, "Source", "UmbrellaElla", "Public", "Core01", "Core01Tuning.h"), TUNING_H)
    write(os.path.join(root, "Source", "UmbrellaElla", "Private", "Harness", "FeatureFlags.cpp"), FLAGS_CPP)
    return root


def eff(**keys):
    e = {"commit": "abc1234", "workbench": "0", "platform": "Windows", "manifest": MANIFEST["manifest_version"]}
    e.update({k.replace("__", ".").replace("_", "-", 1) if "__" in k else k: str(v) for k, v in keys.items()})
    return e


class RuntimeEvidence(unittest.TestCase):
    """B C1, B H2, B H3: the packaged game's SMOKE_EFFECTIVE line decides, whatever the C++ spelling."""

    def setUp(self):
        self.root = repo()
        self.addCleanup(shutil.rmtree, self.root, True)

    def line(self, **over):
        e = {"commit": "abc1234", "workbench": "0", "platform": "Windows", "manifest": MANIFEST["manifest_version"],
             "CORE-01.move_speed": "350", "DEF-01.enabled": "1"}
        e.update(over)
        return e

    def test_live_values_equal_to_the_marked_ones_pass(self):
        self.assertEqual(bake_preset.effective_problems(self.root, self.line()), [])

    def test_a_marker_in_a_cpp_flag_table_is_read(self):
        # final-9 A M4: defaults, bake and check read .cpp markers too
        self.assertIn("DEF-01.enabled", bake_preset.markers(self.root))

    def test_include_switch_or_brace_init_ships_another_value(self):
        # broken on purpose: the static checks pass (one marked header), but the binary runs 650 (an #else include)
        probs = bake_preset.effective_problems(self.root, self.line(**{"CORE-01.move_speed": "650"}))
        self.assertTrue(any("CORE-01.move_speed: the running game has 650" in p for p in probs), probs)

    def test_a_p0_switched_off_in_code_or_by_a_manifest_requires(self):
        # broken on purpose: `if (Id == DEF_01) return false;` or requires += an OFF experiment: DEF-01 runs off
        probs = bake_preset.effective_problems(self.root, self.line(**{"DEF-01.enabled": "0"}))
        self.assertTrue(any("DEF-01" in p and "APPROVED_P0" in p for p in probs), probs)

    def test_a_marked_key_the_hook_does_not_report_fails(self):
        e = self.line()
        del e["CORE-01.move_speed"]
        probs = bake_preset.effective_problems(self.root, e)
        self.assertTrue(any("does not report it" in p for p in probs), probs)

    def test_g4_needs_every_required_key(self):
        probs = bake_preset.effective_problems(self.root, self.line(), complete=True)
        self.assertTrue(any("required at G4" in p for p in probs), probs)

    def test_the_baked_value_wins_once_baked(self):
        write(os.path.join(self.root, bake_preset.STAMP), json.dumps({"values": {"CORE-01.move_speed": 375}}))
        self.assertTrue(bake_preset.effective_problems(self.root, self.line()))
        self.assertEqual(bake_preset.effective_problems(self.root, self.line(**{"CORE-01.move_speed": "375"})), [])

    def test_no_compiled_commit_fails(self):
        probs = bake_preset.effective_problems(self.root, self.line(commit="unknown"))
        self.assertTrue(any("did not compile a commit" in p for p in probs), probs)

    def test_cli_needs_the_line_and_agrees_with_smoke_ok(self):
        log = os.path.join(self.root, "g.log")
        ok = ("LogUmbrellaElla: SMOKE_OK map=L_Graybox view=1920x1080 aspect=1.778 debugdraw=0 fps=60 worst_ms=20 commit=abc1234 input=ok gamepad=ok gp_vx=150 gp_attack_vz=-200 gp_shield_vz=-180 input_vz=-1 "
              "load_ms=10 workbench=0\n" + "".join(
                  f"LogUmbrellaElla: SMOKE_EFFECTIVE at={at} commit=abc1234 workbench=0 platform=Mac "
                  f"manifest={MANIFEST['manifest_version']} CORE-01.move_speed=350 DEF-01.enabled=1\n" for at in ("start", "end")))
        write(log, ok)
        with contextlib.redirect_stdout(io.StringIO()) as out:
            self.assertEqual(bake_preset.main(["--root", self.root, "effective", log]), 0, out.getvalue())
        write(log, ok.replace("commit=abc1234 workbench=0 platform=Mac", "commit=def5678 workbench=0 platform=Mac"))
        with contextlib.redirect_stdout(io.StringIO()) as out:
            self.assertEqual(bake_preset.main(["--root", self.root, "effective", log]), 1)
        self.assertIn("SMOKE_OK says commit=abc1234", out.getvalue())
        write(log, ok.split("\n")[0] + "\n")   # broken on purpose: no SMOKE_EFFECTIVE line
        with contextlib.redirect_stdout(io.StringIO()) as out:
            self.assertEqual(bake_preset.main(["--root", self.root, "effective", log]), 1)


class OnlyRichardTunes(unittest.TestCase):
    """B H1: a baked number other than the GDD start needs a DECIDED (<design owner>) row naming the key. GDD SH1.0's
    revision note makes Rick the design owner (D-new-sh10-design-owner); Richard no longer lifts a value."""

    def check(self, value, decisions=""):
        return bake_preset.safety_problems("T-01", {}, {"CORE-03.max_health": value}, MANIFEST, decisions)

    def test_start_value_passes(self):
        self.assertEqual(self.check(100), [])

    def test_an_in_range_value_alone_fails(self):
        self.assertTrue(any("only Rick (the design owner) tunes" in p for p in self.check(200)))

    def test_richards_row_naming_the_key_passes(self):
        self.assertEqual(self.check(200, RICHARD.format(ids="CORE-03.max_health", who="Rick")), [])
        self.assertTrue(self.check(200, RICHARD.format(ids="CORE-03.max_health", who="Richard")))

    def test_another_decider_or_the_feature_id_alone_lifts_nothing(self):
        self.assertTrue(self.check(200, RICHARD.format(ids="CORE-03.max_health", who="Gameplay Dev agent")))
        self.assertTrue(self.check(200, RICHARD.format(ids="CORE-03", who="Rick")))

    def test_a_key_override_never_lifts_its_feature(self):
        import manifest_check
        got = manifest_check.decided_overrides(RICHARD.format(ids="CORE-03.max_health", who="Rick"))
        self.assertEqual(got, {"CORE-03.max_health"})

    def test_percent_key_written_as_a_ratio_says_so(self):
        # final-9 A M5
        probs = bake_preset.safety_problems("T-01", {}, {"CORE-01.open_steer_multiplier": 1.0}, MANIFEST, "")
        self.assertTrue(any("written in percent" in p for p in probs), probs)


class MachineRecords(unittest.TestCase):
    """B H4, B H5, A H4: gate lines are the machine's records."""

    DAILY = ("DAILY abc1234 | rick-pc/Windows 11 | Development | clean-tree=PASS build=PASS test=PASS(7/0/7) "
             "validate=PASS(err 0, warn 0) package=PASS(warn 0) smoke=PASS(1 map(s), repeat 5/5) display=PASS(1 mode(s)) "
             "settings=PASS(garbage ini) client-test=NOT RUN | Not checked: client-test (CLIENT_TESTS=1 not set)")

    def lines(self, daily=None, launched="yes", sha="b" * 64):
        return {"build": "abc1234 | T_G.zip | Development", "repeat boots": daily or self.DAILY,
                "jam-page test upload (g1 on)": f"https://x | sha256={sha} | re-downloaded and launched: {launched}"}

    def setUp(self):
        # final-11 A H5: hermetic; card 0.0's filled People table names the real packaging machine, not rick-pc
        patch = unittest.mock.patch.object(check_card, "packaging_machine", lambda root=None: "RICK-PC")
        patch.start()
        self.addCleanup(patch.stop)

    def test_the_recorded_daily_line_passes(self):
        got = check_card.machine_record_problems(self.lines(launched="no"), "G1", [self.DAILY])
        self.assertEqual(got, [])

    def test_an_edited_or_invented_daily_line_fails(self):
        for typed in (self.DAILY.replace("7/0/7", "7/1/8"), self.DAILY.replace(" client-test=NOT RUN", ""),
                      self.DAILY.split(" | Not checked")[0]):
            with self.subTest(typed=typed[-40:]):
                got = check_card.machine_record_problems(self.lines(typed, launched="no"), "G1", [self.DAILY])
                self.assertTrue(any("not a line of the machine record" in p for p in got), got)

    def test_no_records_fails(self):
        self.assertTrue(check_card.machine_record_problems(self.lines(), "G1", []))

    def test_launched_yes_needs_a_windows_launch_line_for_the_zip(self):
        got = check_card.machine_record_problems(self.lines(), "G1", [self.DAILY])
        self.assertTrue(any("LAUNCH" in p for p in got), got)
        mac = f"LAUNCH {'b' * 64} | zip=T_G.zip | SMOKE_EFFECTIVE commit=abc1234 workbench=0 platform=Mac"
        got = check_card.machine_record_problems(self.lines(), "G1", [self.DAILY, mac])
        self.assertTrue(any("platform=Mac" in p for p in got), got)

    def test_a_zip_not_on_disk_fails(self):
        ln = self.lines(launched="no")
        ln["gate checks"] = f"PASS: /no/such/G1-abc1234/T_G.zip config=Development platform=Win64 commit=abc1234 sha256={'b' * 64}"
        got = check_card.machine_record_problems(ln, "G1", [self.DAILY])
        self.assertTrue(any("not on this machine" in p for p in got), got)


@unittest.skipIf(os.name == "nt", "runs the Mac tools/ue/package.sh on a bash RunUAT.sh stub; Windows packages with "
                                  "package.ps1 (tests/test_honest_jam.py test_17 holds its commit stamp)")
class PackageStampsTheCommitAtBuildStart(unittest.TestCase):
    """B H5: the binary's commit is stamped before BuildCookRun, and a HEAD that moves during it fails."""

    def setUp(self):
        self.r = tus.FakeRepo()
        self.addCleanup(self.r.close)

    def test_commit_passed_to_the_build_and_written_to_build_info(self):
        env_file = os.path.join(self.r.base, "env.txt")
        self.r.stub("Engine/Build/BatchFiles/RunUAT.sh",
                    'for a in "$@"; do case "$a" in -archivedirectory=*) d="${a#-archivedirectory=}";; esac; done\n'
                    f'mkdir -p "$d/Mac"; echo game > "$d/Mac/UmbrellaElla"; echo "$UMBRELLAELLA_BUILD_COMMIT" > "{env_file}"\n'
                    'echo "BUILD SUCCESSFUL"; exit 0')
        head = subprocess.run(["git", "rev-parse", "HEAD"], cwd=self.r.dir, capture_output=True, text=True).stdout.strip()
        rc, out = self.r.sh("package.sh")
        self.assertEqual(rc, 0, out)
        self.assertEqual(open(env_file).read().strip(), head)
        self.assertIn(f"commit={head}", open(os.path.join(self.r.dir, "Packaged", "BUILD_INFO.txt")).read())
        self.assertIn("platform=Mac", out)

    def test_a_commit_during_packaging_fails(self):
        # broken on purpose: a `git pull` lands while the 40-minute package runs
        self.r.stub("Engine/Build/BatchFiles/RunUAT.sh",
                    'for a in "$@"; do case "$a" in -archivedirectory=*) d="${a#-archivedirectory=}";; esac; done\n'
                    'mkdir -p "$d/Mac"; echo game > "$d/Mac/UmbrellaElla"\n'
                    'git -c user.email=t@t -c user.name=t commit -q --allow-empty -m pulled\n'
                    'echo "BUILD SUCCESSFUL"; exit 0')
        rc, out = self.r.sh("package.sh")
        self.assertEqual(rc, 1, out)
        self.assertIn("HEAD moved", out)
        self.assertFalse(os.path.exists(os.path.join(self.r.dir, "Packaged", "BUILD_INFO.txt")))


class WorkbenchCheckReadsPlugins(unittest.TestCase):
    """B H6 and B M4."""

    def setUp(self):
        self.root = tempfile.mkdtemp()
        self.addCleanup(shutil.rmtree, self.root, True)
        write(os.path.join(self.root, "Source", "UmbrellaElla.Target.cs"),
              'ProjectDefinitions.Add("UMBRELLAELLA_WORKBENCH=0");\n')

    def test_clean_tree_and_plugin_pass(self):
        write(os.path.join(self.root, "Plugins", "DevTools", "Source", "DevTools", "DevTools.Build.cs"),
              'PublicDependencyModuleNames.Add("Core");\n')
        self.assertEqual(ue_run.workbench_check(self.root), [])

    def test_a_plugin_that_defines_the_switch_fails(self):
        write(os.path.join(self.root, "Plugins", "DevTools", "Source", "DevTools", "DevTools.Build.cs"),
              'PublicDefinitions.Add("UMBRELLAELLA_WORKBENCH=1");\n')
        write(os.path.join(self.root, "Plugins", "DevTools", "Source", "DevTools", "Wb.h"), "#define UMBRELLAELLA_WORKBENCH 1\n")
        got = ue_run.workbench_check(self.root)
        self.assertEqual(len(got), 2, got)

    def test_a_commented_define_and_a_built_value_fail(self):
        write(os.path.join(self.root, "Source", "UmbrellaElla.Target.cs"),
              '// Submission: UMBRELLAELLA_WORKBENCH=0\n'
              'ProjectDefinitions.Add("UMBRELLAELLA_WORKBENCH=" + (bWithWorkbench ? "1" : "0"));\n')
        self.assertTrue(ue_run.workbench_check(self.root))


class NoPlayerMapsAreData(unittest.TestCase):
    """A H2: the list comes from pipeline/qa/no-player-maps.txt; GameDefaultMap is never exempt."""

    def test_list_is_read_from_the_file(self):
        root = tempfile.mkdtemp()
        self.addCleanup(shutil.rmtree, root, True)
        write(os.path.join(root, ue_run.NO_PLAYER_FILE), "# c\nL_Title | x | y\nL_StyleFrame | 0.10a | z\n")
        self.assertEqual(ue_run.no_player_maps(root), "L_Title,L_StyleFrame")
        log = os.path.join(root, "g.log")
        write(log, "SMOKE_OK map=L_StyleFrame view=1920x1080 aspect=1.778 debugdraw=0 fps=60 worst_ms=20 commit=abc input=none load_ms=10\n")
        with contextlib.redirect_stdout(io.StringIO()):
            self.assertEqual(ue_run.smoke_log([log], 0, no_player_maps=ue_run.no_player_maps(root), root=root), 0)
        # broken on purpose: the map the game boots is listed; it always has Ella
        write(os.path.join(root, "Config", "DefaultEngine.ini"),
              "GameDefaultMap=/Game/UmbrellaElla/Maps/L_StyleFrame.L_StyleFrame\n")
        with contextlib.redirect_stdout(io.StringIO()):
            self.assertEqual(ue_run.smoke_log([log], 0, no_player_maps=ue_run.no_player_maps(root), root=root), 1)


class RuleKAndActors(unittest.TestCase):
    """A M8: an actor inherits Blueprintable; card 0.8 gives the GameMode a BP child, so K skips it."""

    def run_k(self, spec):
        root = tempfile.mkdtemp()
        self.addCleanup(shutil.rmtree, root, True)
        write(os.path.join(root, "Source", "UmbrellaElla", "UmbrellaElla.Build.cs"),
              'public class UmbrellaElla : ModuleRules { public UmbrellaElla(ReadOnlyTargetRules T) : base(T) { '
              'PublicDependencyModuleNames.AddRange(new string[] { "Core", "CoreUObject", "Engine" }); } }\n')
        write(os.path.join(root, "Source", "UmbrellaElla", "Public", "Core", "UmbrellaGameMode.h"),
              f'#pragma once\n#include "GameFramework/GameModeBase.h"\n#include "UmbrellaGameMode.generated.h"\n'
              f'UCLASS({spec})\nclass UMBRELLAELLA_API AUmbrellaGameMode : public AGameModeBase\n{{\n\tGENERATED_BODY()\n}};\n')
        return [p for p in module_check.check(root, with_k=True) if "[K]" in str(p) or "final" in str(p)]

    def test_actor_without_final_passes_k(self):
        self.assertEqual(self.run_k(""), [])

    def test_not_blueprintable_actor_must_be_final(self):
        self.assertEqual(len(self.run_k("NotBlueprintable")), 1)


class FootageFinalAlone(unittest.TestCase):
    """A M10: card 0.24 runs `footage --final` as written; it reads the footage, never exits 2."""

    def test_final_without_day_runs(self):
        p = subprocess.run([sys.executable, os.path.join(ROOT, "tools", "submission_check.py"), "footage", "--final"],
                           capture_output=True, text=True)
        self.assertIn(p.returncode, (0, 1), p.stdout + p.stderr)
        p = subprocess.run([sys.executable, os.path.join(ROOT, "tools", "submission_check.py"), "footage"],
                           capture_output=True, text=True)
        self.assertEqual(p.returncode, 2)


if __name__ == "__main__":
    unittest.main()
