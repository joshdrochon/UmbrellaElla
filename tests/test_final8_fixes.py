"""Final-8 dry runs: each adversarial fix has a passing case and a case that breaks the code on purpose to prove
the check catches it. The honest paths for every fix are walked end to end in tests/test_honest_jam.py."""
import json
import os
import shutil
import sys
import tempfile
import unittest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "tools"))
import bake_preset as bp  # noqa: E402
import check_card  # noqa: E402
import check_pr  # noqa: E402
import export_package  # noqa: E402
import gdd_impact  # noqa: E402
import manifest_check  # noqa: E402
import module_check  # noqa: E402
import ue_run  # noqa: E402

TUNING_H = ("#pragma once\nUSTRUCT()\nstruct FMoveTuning\n{\n\tGENERATED_BODY()\n"
            "\tUPROPERTY() float MoveSpeed = 350.f;   // bake: CORE-01.move_speed\n};\n")
FLAGS_H = "static const FFlagDefault Defaults[] = {\n\t{ EFeatureId::UMB_02, true },   // bake: UMB-02.enabled\n};\n"


def write(path, text):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as fh:
        fh.write(text)


class Src(unittest.TestCase):
    def setUp(self):
        self.root = tempfile.mkdtemp()

    def tearDown(self):
        shutil.rmtree(self.root, ignore_errors=True)

    def put(self, rel, text):
        write(os.path.join(self.root, rel), text)

    def found(self):
        return bp.markers(self.root)


class BakeBranches(Src):
    """B C1: a `// bake:` marker under a workbench #if or #else is rejected (one branch ships)."""

    def test_markers_outside_any_branch_pass(self):
        self.put("Source/G/Public/MoveTuning.h", TUNING_H)
        self.put("Source/G/Public/Flags.h", "#ifndef FLAGS_H\n#define FLAGS_H\n" + FLAGS_H + "#endif\n")   # include guard
        self.assertEqual(bp.branch_problems(self.root, self.found()), [])

    def test_marker_in_workbench_if_with_other_value_in_else_fails(self):
        self.put("Source/G/Public/MoveTuning.h", TUNING_H.replace(
            "\tUPROPERTY() float MoveSpeed = 350.f;   // bake: CORE-01.move_speed\n",
            "#if UMBRELLAELLA_WORKBENCH\n\tUPROPERTY() float MoveSpeed = 350.f;   // bake: CORE-01.move_speed\n"
            "#else\n\tUPROPERTY() float MoveSpeed = 9000.f;\n#endif\n"))
        p = bp.branch_problems(self.root, self.found())
        self.assertTrue(any("CORE-01.move_speed" in x and "preprocessor branch" in x for x in p), p)

    def test_marked_flag_in_else_of_a_negated_guard_fails(self):
        self.put("Source/G/Public/Flags.h", "static const FFlagDefault Defaults[] = {\n#if !UMBRELLAELLA_WORKBENCH\n"
                 "\t{ EFeatureId::UMB_02, false },\n#else\n\t{ EFeatureId::UMB_02, true },   // bake: UMB-02.enabled\n"
                 "#endif\n};\n")
        p = bp.branch_problems(self.root, self.found())
        self.assertTrue(any("UMB-02.enabled" in x for x in p), p)
        # the unmarked literal for the same flag is a second write too
        self.assertTrue(any("UMB-02.enabled" in x for x in bp.one_source_problems(self.root, self.found())))


class BakeOneSource(Src):
    """B H3: any C++ write of a baked member outside its marked line fails; B H2: any config override fails."""

    def setUp(self):
        super().setUp()
        self.put("Source/G/Public/MoveTuning.h", TUNING_H)

    def test_reads_and_comparisons_pass(self):
        self.put("Source/G/Private/Move.cpp", "float F(const FMoveTuning& T) { return T.MoveSpeed >= 1.f ? T.MoveSpeed : 0.f; }\n"
                 "bool B(const FMoveTuning& T) { return T.MoveSpeed == 350.f; }\n")
        self.assertEqual(bp.one_source_problems(self.root, self.found()), [])

    def test_per_run_copy_inside_the_workbench_branch_passes(self):
        self.put("Source/G/Private/Harness.cpp", "#if UMBRELLAELLA_WORKBENCH\nvoid Apply(FMoveTuning& Run, float V) "
                 "{ Run.MoveSpeed = V; }\n#endif\n")
        self.assertEqual(bp.one_source_problems(self.root, self.found()), [])

    def test_writes_fail(self):
        for name, body in {"cpp assign": "AElla::AElla() { Tuning.MoveSpeed = 2.f; }\n",
                           "compound": "void X(FMoveTuning& T) { T.MoveSpeed *= 2; }\n",
                           "init list": "AElla::AElla() : MoveSpeed(9000.f) {}\n",
                           "workbench else": "#if UMBRELLAELLA_WORKBENCH\nvoid A() {}\n#else\nvoid A(FMoveTuning& T) "
                                             "{ T.MoveSpeed = 9000.f; }\n#endif\n"}.items():
            with self.subTest(name):
                self.put("Source/G/Private/Ella.cpp", body)
                p = bp.one_source_problems(self.root, self.found())
                self.assertTrue(any("CORE-01.move_speed" in x and "writes MoveSpeed" in x for x in p), p)

    def test_config_override_through_any_class_fails(self):
        self.put("Source/G/Public/EllaGameMode.h", "UCLASS(Config=Game)\nclass AEllaGameMode : public AGameModeBase\n{\n"
                 "\tUPROPERTY(Config) FMoveTuning Tuning;\n};\n")
        self.put("Config/DefaultGame.ini", "[/Script/EngineSettings.GeneralProjectSettings]\nProjectName=UmbrellaElla\n")
        self.assertEqual(bp.ini_override_problems(self.root), [])
        self.put("Config/DefaultGame.ini", "[/Script/UmbrellaElla.EllaGameMode]\nTuning=(MoveSpeed=9000.0)\n")
        p = bp.ini_override_problems(self.root)
        self.assertTrue(any("EllaGameMode" in x for x in p), p)
        self.assertTrue(any("sets MoveSpeed" in x for x in p), p)
        # a baked member named in a section the class scan cannot see
        self.put("Config/DefaultGame.ini", "[/Script/UmbrellaElla.SomethingElse]\nMoveSpeed=9000\n")
        self.assertTrue(any("sets MoveSpeed" in x for x in bp.ini_override_problems(self.root)))


class ApprovedTracesToGdd(unittest.TestCase):
    """B C2: every approved_parameters entry traces to a GDD 5A row or a quoted GDD sentence; anything else fails."""

    def setUp(self):
        with open(os.path.join(ROOT, "docs", "feature-manifest.json"), encoding="utf-8") as fh:
            self.man = json.load(fh)
        self.snap = gdd_impact.read(os.path.join(ROOT, manifest_check.current_snapshot(ROOT)))

    def probs(self):
        return manifest_check.approved_problems(self.man, self.snap)

    def test_the_repo_manifest_passes(self):
        self.assertEqual(self.probs(), [])

    def test_breaks(self):
        vals = self.man["approved_parameters"]["values"]
        for name, edit, want in (
                # GDD SH1.0: every start traces to one printed sentence (PROSE_ROWS); none has a range yet
                ("clock HP changed", lambda: vals["OWL-08.clock_hp"].update(start=300), "OWL-08.clock_hp.start"),
                ("rise speed range", lambda: vals["MOVE-21.rise_speed"].update(min=60, max=240, step=10), "MOVE-21.rise_speed"),
                ("red interval range", lambda: vals["OWL-11.red_interval_s"].update(min=1, max=2, step=0.05), "OWL-11.red_interval_s"),
                ("invented key", lambda: vals.update({"MOVE-21.gravity": {"start": 980}}), "MOVE-21.gravity")):
            with self.subTest(name):
                self.setUp()
                vals = self.man["approved_parameters"]["values"]
                edit()
                p = self.probs()
                self.assertTrue(any(want in where for _, where, _ in p), p)


class GateDailyRule(unittest.TestCase):
    """A C1 / B H1: the gate rule reads DAILY steps and Not checked entries by name, per gate."""
    LINE = ("DAILY 1a2b3c4 | h/Windows 11 | Development | clean-tree=PASS build=PASS test=PASS(40/0/40) "
            "validate=PASS(err 0, warn 0) package=PASS(warn 0) smoke=PASS(1 map(s), repeat 5/5) display=PASS(3 mode(s)) "
            "settings=PASS(garbage ini) client-test=NOT RUN shipping-alive=NOT RUN | Not checked: "
            "restart cycles (SMOKE_RESTART_CYCLES not set), client-test (CLIENT_TESTS=1 not set), "
            "shipping-alive (SHIPPING_EXE not set; Shipping smoke only if D-new-smoke picks it)")

    def test_every_entry_daily_writes_is_registered(self):
        import re
        with open(os.path.join(ROOT, "tools", "ue_run.py"), encoding="utf-8") as fh:
            src = fh.read()
        literal = re.findall(r'not_checked\.(?:append|insert)\((?:0, )?"([^"{]+)"\)', src)
        self.assertGreater(len(literal), 8)
        for e in literal:
            self.assertIsNotNone(ue_run.not_checked_kind(e), e)

    def test_g1_default_switches_pass(self):
        self.assertEqual(check_card.daily_gate_problems(self.LINE, "G1"), [])
        self.assertEqual(check_card.daily_switch_due(self.LINE, "G1"), [])

    def test_breaks(self):
        self.assertTrue(check_card.daily_switch_due(self.LINE, "G2"))           # client tests due at G2
        self.assertEqual(len(check_card.daily_switch_due(self.LINE, "G3")), 2)  # and restart cycles at G3
        typed = self.LINE.replace("Not checked: ", "Not checked: smoke on Win64, ")
        self.assertTrue(any("not one" in p for p in check_card.daily_gate_problems(typed, "G1")))
        boot = self.LINE.replace("Not checked: ", "Not checked: smoke contract (bootstrap: no smoke hook before card "
                                                  "0.6; alive run only), ")
        self.assertTrue(check_card.daily_gate_problems(boot, "G1"))
        self.assertTrue(check_card.daily_gate_problems(self.LINE.replace("display=PASS(3 mode(s))", "display=NOT RUN"), "G1"))


class PrVerdicts(unittest.TestCase):
    """A H1 / A H3 at the line level (the whole PRs are in tests/test_honest_jam.py)."""

    def test_failure_lines_fail_and_planted_needs_a_card_that_asks(self):
        ev = "smoke: exit=0 SMOKE_OK=yes 'Error:'=0\ncrash folders: 0 new\n"
        self.assertEqual(check_pr.run_verdict_problems(ev, True), [])
        for bad in ("FAIL: 1 'Error:' line(s)\n", "crash folders: 1 new\n", "smoke: exit=0 SMOKE_OK=yes 'Error:'=1\n"):
            with self.subTest(bad):
                self.assertTrue(check_pr.run_verdict_problems(ev + bad, True))
        self.assertTrue(check_pr.run_verdict_problems("", True))   # SMOKE_OK pasted without the run's verdict
        planted = "PLANTED FAIL: x\nFAIL: 1 'Error:' line(s)\n\nPASS\n"
        self.assertEqual(check_pr.without_planted(planted).strip(), "PASS")


class RuleMAndMarkers(Src):
    """Rule M does not read a `// bake:` marker as gated behaviour; code that names the feature still needs its flag."""

    def test_marker_only_passes_code_fails(self):
        gated = {"UMB-01": "UMB_01"}
        ok = "struct FLift\n{\n\tfloat AscentSpeed = 300.f;   // bake: UMB-01.ascent_speed\n};\n"
        self.assertEqual(module_check.feature_flag_findings("Source/G/Public/Lift.h", ok, gated), [])
        bad = ok + "void Lift() { if (Mode == EFeatureId::UMB_01) {} }\n"
        self.assertTrue(module_check.feature_flag_findings("Source/G/Public/Lift.h", bad, gated))


class JamFilesNotOrphans(unittest.TestCase):
    """A H6: game files are not package docs; a new pipeline doc with no mapping is still an orphan."""

    def test_game_roots_skipped_pipeline_doc_still_mapped(self):
        docs = export_package.doc_set(["Art/Source/Anchors/ella.sprite.json", "Content/UmbrellaElla/UI/ST_UI.csv",
                                       "scratch/notes.txt", "Samples/Workbench/README.md", "pipeline/new-rule.md"])
        self.assertEqual(docs, ["pipeline/new-rule.md"])


if __name__ == "__main__":
    unittest.main()
