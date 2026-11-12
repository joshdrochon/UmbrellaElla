"""tools/bake_preset.py: the approved workbench preset is baked into the shipped defaults (D-new-workbench-debug).
A good bake and check pass; an unbaked value, a missing marker, an unauthorized flag change and a gate record
naming another preset each fail. Fixture repos are built in a temp folder."""
import contextlib
import io
import json
import os
import shutil
import sys
import tempfile
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "tools"))
import bake_preset as bp  # noqa: E402

MANIFEST = {
    "manifest_version": "B1.0-m1",
    "gdd_revision": "1.3",   # the 1.3 feel / sim model (tools/tuning.py MODELS): CORE-01.move_speed is a sim key
    "features": [
        {"feature_id": "CORE-01", "status": "CONFIRMED", "flag": None, "default_enabled": True,
         "implementation_authorized": False, "parameters": ["move_speed"]},
        {"feature_id": "UMB-03", "status": "APPROVED_P1", "flag": "UMB_03", "default_enabled": False,
         "implementation_authorized": True, "parameters": ["catch_window"]},
        {"feature_id": "WIND-01", "status": "PROPOSED", "flag": "WIND_01", "default_enabled": False,
         "implementation_authorized": False, "parameters": ["gust_force"]},
        {"feature_id": "COM-01", "status": "APPROVED_P0", "flag": "COM_01", "default_enabled": True,
         "implementation_authorized": True, "parameters": ["cadence"]},
    ],
    "approved_parameters": {"values": {"COM-01.cadence": {"start": 0.65, "step": 0.05, "min": 0.2, "max": 1.5, "unit": "s"},
                                       "CORE-01.move_speed": {"start": 350, "step": 10, "min": 150, "max": 650},
                                       "UMB-03.catch_window": {"start": 0.2, "step": 0.05, "min": 0.1, "max": 0.4},
                                       "OWL-01.seed": {"start": 20261112, "unit": "integer"}}},
}
DECIDED_T03 = ("| ID | Decision | Owner | Status |\n|---|---|---|---|\n"
               "| D-ship | Ship the SHIELD preset T-03 and COM-01 off. Overrides: T-03, COM-01 | Richard | DECIDED 2026-11-15 (Rick) |\n")
# Names T-03 and COM-01 but overrides nothing (like D-new-p0-signoff or DEC-03): lifts no rule (dry run B H3)
DECIDED_MENTION = ("| ID | Decision | Owner | Status |\n|---|---|---|---|\n"
                   "| DEC-03 | Shield heals; T-03 tests it; COM-01 is P0 | Richard | DECIDED 2026-11-10 (Rick) |\n")
# final-9 B H1: the fixture's tuned numbers (640, 0.25, and the 600 in source) are Richard's, by key
DECIDED_TUNE = ("| D-tune | Ship the tuned move speed and catch window. Overrides: CORE-01.move_speed, UMB-03.catch_window "
                "| Richard | DECIDED 2026-11-15 (Rick) |\n")
DECIDED_T03 = DECIDED_T03 + DECIDED_TUNE
DECIDED_MENTION = DECIDED_MENTION + DECIDED_TUNE
PRESETS = {"presets": [{"id": "T-01"}, {"id": "T-03"}]}
MOVE_H = ("#pragma once\nUSTRUCT()\nstruct FEllaMovementTuning\n{\n"
          "\tUPROPERTY(EditAnywhere) float MoveSpeed = 600.f;   // bake: CORE-01.move_speed\n};\n")
CATCH_H = ("#pragma once\nstruct FCatchTuning\n{\n\tfloat CatchWindow = 0.2f;   // bake: UMB-03.catch_window\n};\n")
FLAGS_H = ("static const FFlagDefault Defaults[] = {\n"
           "\t{ EFeatureId::UMB_03, false },   // bake: UMB-03.enabled\n"
           "\t{ EFeatureId::WIND_01, false },   // bake: WIND-01.enabled\n"
           "\t{ EFeatureId::COM_01, true },   // bake: COM-01.enabled\n};\n")
COM_H = "struct FAttackTuning\n{\n\tfloat Cadence = 0.65f;   // bake: COM-01.cadence\n};\n"
EXPORT = {"kind": "workbench_config", "preset": "T-01", "commit": "abc1234", "manifest_version": "B1.0-m1",
          "flags": {"UMB-03": True, "WIND-01": False, "COM-01": True},
          "params": {"CORE-01.move_speed": 640, "UMB-03.catch_window": 0.25, "COM-01.cadence": 0.65}}


def write(path, text):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as fh:
        fh.write(text)


def read(path):
    with open(path, encoding="utf-8") as fh:
        return fh.read()


class BakeTests(unittest.TestCase):
    def setUp(self):
        self.root = tempfile.mkdtemp()
        write(os.path.join(self.root, bp.MANIFEST), bp.dump_json(MANIFEST))
        write(os.path.join(self.root, bp.PRESETS), bp.dump_json(PRESETS))
        write(os.path.join(self.root, bp.DECISIONS), "| ID | Decision | Owner | Status |\n|---|---|---|---|\n" + DECIDED_TUNE)
        self.move = os.path.join(self.root, "Source/UmbrellaElla/Public/Move/EllaMovementTuning.h")
        write(self.move, MOVE_H)
        write(os.path.join(self.root, "Source/UmbrellaElla/Public/Catch/CatchTuning.h"), CATCH_H)
        write(os.path.join(self.root, "Source/UmbrellaElla/Private/Harness/FlagDefaults.h"), FLAGS_H)
        write(os.path.join(self.root, "Source/UmbrellaElla/Public/Attack/AttackTuning.h"), COM_H)

    def tearDown(self):
        shutil.rmtree(self.root)

    def export(self, **change):
        e = json.loads(json.dumps(EXPORT))
        e.update(change)
        path = os.path.join(self.root, "Saved/Workbench/config.json")
        write(path, json.dumps(e))
        return path

    def run_cli(self, *args):
        with contextlib.redirect_stdout(io.StringIO()) as out:
            rc = bp.main(["--root", self.root, *args])
        return rc, out.getvalue()

    def test_good_bake_writes_defaults_manifest_and_stamp_and_check_passes(self):
        rc, out = self.run_cli("bake", self.export())
        self.assertEqual(rc, 0, out)
        self.assertIn("+\tUPROPERTY(EditAnywhere) float MoveSpeed = 640.0f;", out)  # the PR diff
        self.assertIn("float MoveSpeed = 640.0f;   // bake: CORE-01.move_speed", read(self.move))
        flags = read(os.path.join(self.root, "Source/UmbrellaElla/Private/Harness/FlagDefaults.h"))
        self.assertIn("{ EFeatureId::UMB_03, true },", flags)
        m = json.loads(read(os.path.join(self.root, bp.MANIFEST)))
        self.assertTrue(m["features"][1]["default_enabled"])
        stamp = json.loads(read(os.path.join(self.root, bp.STAMP)))
        self.assertEqual(stamp["preset"], "T-01")
        rc, out = self.run_cli("check", "--preset", "T-01")
        self.assertEqual(rc, 0, out)
        self.assertIn("bake_preset check: PASS preset=T-01 values=6", out)

    def test_an_unchanged_value_keeps_its_spelling(self):
        # final-10 A M7: a bake that leaves 600 at 600 does not rewrite `600.f` as `600.0f` (no Source/ diff)
        rc, out = self.run_cli("bake", self.export(params=dict(EXPORT["params"], **{"CORE-01.move_speed": 600})))
        self.assertEqual(rc, 0, out)
        self.assertEqual(read(self.move), MOVE_H)
        self.assertNotIn("EllaMovementTuning.h", out)
        # broken on purpose: a changed value is still written in the literal's style
        rc, out = self.run_cli("bake", self.export())
        self.assertIn("float MoveSpeed = 640.0f;", read(self.move))

    def test_dry_run_writes_nothing(self):
        rc, out = self.run_cli("bake", self.export(), "--dry-run")
        self.assertEqual(rc, 0, out)
        self.assertIn("-\tUPROPERTY(EditAnywhere) float MoveSpeed = 600.f;", out)
        self.assertEqual(read(self.move), MOVE_H)
        self.assertFalse(os.path.exists(os.path.join(self.root, bp.STAMP)))

    def test_unbaked_value_fails_the_check(self):
        self.assertEqual(self.run_cli("bake", self.export())[0], 0)
        write(self.move, MOVE_H.replace("600.f", "700.f"))  # a hand edit after the bake: broken on purpose
        rc, out = self.run_cli("check")
        self.assertEqual(rc, 1, out)
        self.assertIn("CORE-01.move_speed", out)
        self.assertIn("unbaked value", out)

    def test_flag_default_changed_after_bake_fails(self):
        self.assertEqual(self.run_cli("bake", self.export())[0], 0)
        mp = os.path.join(self.root, bp.MANIFEST)
        m = json.loads(read(mp))
        m["features"][1]["default_enabled"] = False  # flipped by hand after the bake: broken on purpose
        write(mp, bp.dump_json(m))
        rc, out = self.run_cli("check")
        self.assertEqual(rc, 1, out)
        self.assertIn("UMB-03.enabled: manifest default_enabled=False", out)

    def test_new_marked_key_after_bake_is_checked_as_a_default_until_g4(self):
        """Final-7 A H4: a feature coded after the first bake (G2) no longer turns CI red; its default passes the
        defaults rules, and G4 (--complete / --record) still needs it baked."""
        self.assertEqual(self.run_cli("bake", self.export())[0], 0)
        wind = os.path.join(self.root, "Source/UmbrellaElla/Public/Wind/WindTuning.h")
        write(wind, "float GustForce = 300.f; // bake: WIND-01.gust_force\n")
        rc, out = self.run_cli("check")
        self.assertEqual(rc, 0, out)
        self.assertIn("not baked yet (checked as a default; bake before G4): WIND-01.gust_force", out)
        rc, out = self.run_cli("check", "--complete")
        self.assertEqual(rc, 1, out)
        self.assertIn("WIND-01.gust_force: marked", out)
        write(wind, "float GustForce = true; // bake: WIND-01.gust_force\n")   # broken on purpose: not a number
        rc, out = self.run_cli("check")
        self.assertEqual(rc, 1, out)
        self.assertIn("a parameter default is a number", out)

    def test_unapproved_flag_never_ships_on(self):
        """Dry run B C1: even when the manifest default says on, the bake ships an unauthorized flag off."""
        mp = os.path.join(self.root, bp.MANIFEST)
        m = json.loads(read(mp))
        m["features"][2]["default_enabled"] = True  # WIND-01, PROPOSED: broken on purpose
        write(mp, bp.dump_json(m))
        rc, out = self.run_cli("bake", self.export(flags={"UMB-03": True, "WIND-01": True, "COM-01": True}))
        self.assertEqual(rc, 1, out)
        self.assertIn("flag WIND-01=on", out)
        rc, out = self.run_cli("bake", self.export(flags={"UMB-03": True, "WIND-01": False, "COM-01": True}))
        self.assertEqual(rc, 0, out)

    def test_tuning_rules_shared_with_the_sims(self):
        """Dry run B H3: off-step, a fixed approved value, and a fixed key with no approved entry all fail."""
        real = json.loads(read(os.path.join(os.path.dirname(os.path.abspath(__file__)),   # the frozen 1.3 manifest
                                            "fixtures", "gdd13", "docs", "feature-manifest.json")))
        sp = lambda params, current=None: bp.safety_problems("T-01", {}, params, real, "", current)
        self.assertEqual(sp({"CORE-01.move_speed": 350, "OWL-01.cadence": 3.0, "OWL-01.seed": 20261112,
                             "OWL-01.initial_grace_s": 2.0}), [])
        for params in ({"CORE-01.move_speed": 351.3}, {"OWL-01.seed": 1}, {"OWL-01.initial_grace_s": 0},
                       {"CORE-01.move_speed": 9999}):
            with self.subTest(params):
                self.assertTrue(sp(params))
        self.assertTrue(sp({"OWL-01.collision_radius": 400}, {"OWL-01.collision_radius": 12}))
        self.assertTrue(sp({"OWL-05.clock_extent": 0.01}, {"OWL-05.clock_extent": 40}))
        self.assertEqual(sp({"OWL-01.collision_radius": 12}, {"OWL-01.collision_radius": 12}), [])
        # CLI: an unapproved key (no approved entry) cannot be changed by the bake
        mp = os.path.join(self.root, bp.MANIFEST)
        m = json.loads(read(mp))
        del m["approved_parameters"]["values"]["UMB-03.catch_window"]
        write(mp, bp.dump_json(m))
        rc, out = self.run_cli("bake", self.export())
        self.assertEqual(rc, 1, out)
        self.assertIn("UMB-03.catch_window=0.25 differs from 0.2", out)

    def test_baked_value_must_equal_what_the_sims_check(self):
        """Dry run B H4: the shipped number equals feel.json, so the envelope ran on it."""
        feel = os.path.join(self.root, "pipeline/feel/feel.json")
        write(feel, json.dumps({"movement": {"move_speed": 350}}))
        rc, out = self.run_cli("bake", self.export())
        self.assertEqual(rc, 1, out)
        self.assertIn("sim: CORE-01.move_speed: baked 640, but the sims check 350", out)
        write(feel, json.dumps({"movement": {"move_speed": 640}}))
        self.assertEqual(self.run_cli("bake", self.export())[0], 0)
        self.assertEqual(self.run_cli("check")[0], 0)
        write(feel, json.dumps({"movement": {"move_speed": 350}}))  # sim data moved after the bake
        rc, out = self.run_cli("check")
        self.assertEqual(rc, 1, out)
        self.assertIn("sim: CORE-01.move_speed", out)

    def test_defaults_before_the_first_bake(self):
        """Dry run B M4: every C++ default already follows the rules before anything is baked."""
        rc, out = self.run_cli("defaults")
        self.assertEqual(rc, 0, out)
        write(self.move, MOVE_H.replace("600.f", "9999.0f"))   # broken on purpose
        rc, out = self.run_cli("defaults")
        self.assertEqual(rc, 1, out)
        self.assertIn("CORE-01.move_speed=9999", out)
        write(self.move, MOVE_H)
        write(os.path.join(self.root, "Source/UmbrellaElla/Private/Harness/FlagDefaults.h"),
              FLAGS_H.replace("WIND_01, false", "WIND_01, true"))   # broken on purpose: unapproved on
        rc, out = self.run_cli("defaults")
        self.assertEqual(rc, 1, out)
        self.assertIn("flag WIND-01=on", out)
        shutil.rmtree(os.path.join(self.root, "Source"))
        self.assertEqual(self.run_cli("defaults")[0], 0, "no Source/ yet")

    def test_flag_or_parameter_without_marker_fails_at_g4(self):
        """Dry run B H4: a P0 flag or tuning value with no `// bake:` marker shipped unchecked. Final-7 A H4: the
        first bake runs before every P0 is coded, so it lists the missing markers; G4 fails on them."""
        write(os.path.join(self.root, "Source/UmbrellaElla/Public/Attack/AttackTuning.h"),
              "struct FAttackTuning\n{\n\tfloat Cadence = 5.f;\n};\n")   # marker removed: broken on purpose
        e = self.export(params={"CORE-01.move_speed": 640, "UMB-03.catch_window": 0.25})
        rc, out = self.run_cli("bake", e)
        self.assertEqual(rc, 0, out)
        self.assertIn("not marked yet (required at G4; bake again once it is coded): COM-01.cadence", out)
        self.assertEqual(self.run_cli("check")[0], 0)
        rc, out = self.run_cli("check", "--complete")
        self.assertEqual(rc, 1, out)
        self.assertIn("COM-01.cadence: no `// bake: COM-01.cadence` marker", out)
        rec = os.path.join(self.root, "g4.md")
        write(rec, "Baked preset: T-01\n")
        rc, out = self.run_cli("check", "--record", rec)   # the G4 record mode is complete too
        self.assertEqual(rc, 1, out)
        self.assertIn("COM-01.cadence: no `// bake: COM-01.cadence` marker", out)
        # a marked default the export leaves out is still refused (the export lists every marked key)
        write(os.path.join(self.root, "Source/UmbrellaElla/Public/Attack/AttackTuning.h"), COM_H)
        rc, out = self.run_cli("bake", e)
        self.assertEqual(rc, 1, out)
        self.assertIn("COM-01.cadence: marked", out)

    def test_marker_shape(self):
        """Final-7 B H3, M2: a numeric flag literal, and a literal inside an expression, ship a value nobody checked."""
        flags = os.path.join(self.root, "Source/UmbrellaElla/Private/Harness/FlagDefaults.h")
        self.assertEqual(self.run_cli("defaults")[0], 0)
        for name, path, text, why in (
                ("P0 off as 0", flags, FLAGS_H.replace("COM_01, true", "COM_01, 0"), "sets the flag to 0"),
                ("experiment on as 1", flags, FLAGS_H.replace("WIND_01, false", "WIND_01, 1"), "sets the flag to 1"),
                ("expression", self.move, MOVE_H.replace("= 600.f;", "= 2 * 350.f;"), "part of an expression"),
                ("expression after", self.move, MOVE_H.replace("= 600.f;", "= 350.f * 2;"), "part of an expression"),
                ("call argument", self.move, MOVE_H.replace("= 600.f;", "= FMath::Max(1.f, 600.f);"), "is an argument")):
            with self.subTest(name):
                write(path, text)
                rc, out = self.run_cli("defaults")
                self.assertEqual(rc, 1, out)
                self.assertIn(why, out)
                write(path, MOVE_H if path == self.move else FLAGS_H)
        self.assertEqual(self.run_cli("defaults")[0], 0)
        # after the bake, check catches the same shapes
        self.assertEqual(self.run_cli("bake", self.export())[0], 0)
        write(self.move, read(self.move).replace("= 640.0f;", "= 2 * 640.0f;"))
        rc, out = self.run_cli("check")
        self.assertEqual(rc, 1, out)
        self.assertIn("part of an expression", out)

    def test_ini_override_of_a_baked_default_fails(self):
        """Final-7 B H5: `UUmbrellaTuning` is UCLASS(Config=Game), so a DefaultGame.ini section beats the C++ default."""
        ini = os.path.join(self.root, "Config", "DefaultGame.ini")
        write(ini, "[/Script/EngineSettings.GeneralProjectSettings]\nProjectName=Umbrella\n")
        self.assertEqual(self.run_cli("defaults")[0], 0)
        self.assertEqual(self.run_cli("bake", self.export())[0], 0)
        self.assertEqual(self.run_cli("check")[0], 0)
        for name, path, text in (
                ("Project Settings edit", ini, "[/Script/UmbrellaElla.UmbrellaTuning]\nMovement=(MoveSpeed=900.0)\n"),
                ("platform ini", os.path.join(self.root, "Config", "Windows", "WindowsGame.ini"),
                 "[ /Script/UmbrellaElla.UmbrellaTuning ]\nOwl=(Cadence=0.5)\n")):
            with self.subTest(name):
                write(path, text)   # broken on purpose
                for args in (("check",), ("check", "--complete"), ("defaults",)):
                    rc, out = self.run_cli(*args)
                    self.assertEqual(rc, 1, (args, out))
                    self.assertIn("overrides the baked C++ default", out)
                os.remove(path)
        # another Config class in a marked header counts too
        write(os.path.join(self.root, "Source/UmbrellaElla/Public/Owl/OwlSettings.h"),
              "UCLASS(Config=Game)\nclass UMBRELLAELLA_API UOwlSettings : public UObject\n{\n};\n"
              "float Cadence = 0.65f; // bake: COM-01.cadence\n")
        write(ini, "[/Script/UmbrellaElla.OwlSettings]\nCadence=0.2\n")
        self.assertIn("OwlSettings", "\n".join(bp.ini_override_problems(self.root)))

    def test_defaults_follow_the_manifest_flag_and_the_sims(self):
        """Final-7 B H3, H4: before the bake, a flag differs from its manifest default, or a number differs from what
        the fairness sim and the feel envelope check."""
        flags = os.path.join(self.root, "Source/UmbrellaElla/Private/Harness/FlagDefaults.h")
        write(flags, FLAGS_H.replace("UMB_03, false", "UMB_03, true"))   # authorized, but not the manifest default
        rc, out = self.run_cli("defaults")
        self.assertEqual(rc, 1, out)
        self.assertIn("UMB-03.enabled: the C++ default is true, the manifest default_enabled is false", out)
        write(flags, FLAGS_H)
        feel = os.path.join(self.root, "pipeline/feel/feel.json")
        write(feel, json.dumps({"movement": {"move_speed": 350}}))
        write(self.move, MOVE_H.replace("600.f", "350.f"))
        self.assertEqual(self.run_cli("defaults")[0], 0)
        write(self.move, MOVE_H.replace("600.f", "150.f"))   # broken on purpose: in range, but not what the sims check
        rc, out = self.run_cli("defaults")
        self.assertEqual(rc, 1, out)
        self.assertIn("sim: CORE-01.move_speed: baked 150.0, but the sims check 350", out)

    def test_flags_match_manifest_is_a_required_test(self):
        """Dry run B H4: the in-engine guard named by card 0.27 is in the test map, so the daily build needs it."""
        root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        row = next(ln for ln in read(os.path.join(root, "pipeline", "qa", "test-map.md")).splitlines()
                   if ln.startswith("| QA-10 |"))
        self.assertIn("`UmbrellaElla.Harness.FlagsMatchManifest`", row)

    def test_qa_base_marker_is_parsed(self):
        """Dry run B H2: the QA-BASE flag key could not be matched, so a full export never baked."""
        m = bp.MARKER.search("\t{ EFeatureId::QA_BASE, true },   // bake: QA-BASE.enabled")
        self.assertIsNotNone(m)
        self.assertEqual(m.group("key"), "QA-BASE.enabled")
        self.assertIsNone(bp.MARKER.search("{ X, true }, // bake: QA-BASEX.enabled"))

    def test_mismatched_preset_in_gate_record_fails(self):
        self.assertEqual(self.run_cli("bake", self.export())[0], 0)
        rec = os.path.join(self.root, "g4.md")
        write(rec, "Gate: G4 | due x\nBaked preset: T-03 | approved by Rick #90\n")
        rc, out = self.run_cli("check", "--record", rec)
        self.assertEqual(rc, 1, out)
        self.assertIn("approves preset T-03, but pipeline/qa/baked.json has T-01", out)
        write(rec, "Gate: G4 | due x\nBaked preset: T-01 | approved by Rick #90\n")
        self.assertEqual(self.run_cli("check", "--record", rec)[0], 0)
        write(rec, "Gate: G4 | due x\n")
        self.assertEqual(self.run_cli("check", "--record", rec)[0], 1)

    def test_no_stamp_fails_the_check(self):
        rc, out = self.run_cli("check")
        self.assertEqual(rc, 1, out)
        self.assertIn("nothing is baked", out)

    def test_value_without_marker_is_refused(self):
        os.remove(self.move)
        rc, out = self.run_cli("bake", self.export())
        self.assertEqual(rc, 1, out)
        self.assertIn("no `// bake: CORE-01.move_speed` marker", out)
        self.assertFalse(os.path.exists(os.path.join(self.root, bp.STAMP)))

    def test_marked_key_missing_from_export_is_refused(self):
        e = self.export(params={"CORE-01.move_speed": 640})
        rc, out = self.run_cli("bake", e)
        self.assertEqual(rc, 1, out)
        self.assertIn("UMB-03.catch_window: marked", out)

    def test_unauthorized_flag_change_is_refused(self):
        rc, out = self.run_cli("bake", self.export(flags={"UMB-03": True, "WIND-01": True}))
        self.assertEqual(rc, 1, out)
        self.assertIn("WIND-01=on differs from its manifest default", out)

    def test_wrong_preset_or_manifest_version_is_refused(self):
        self.assertEqual(self.run_cli("bake", self.export(preset="T-09"))[0], 1)
        rc, out = self.run_cli("bake", self.export(manifest_version="B0.9-m1"))
        self.assertEqual(rc, 1, out)
        self.assertIn("export again", out)

    def test_validate_shape(self):
        self.assertEqual(self.run_cli("validate", self.export(), "--shape-only")[0], 0)
        self.assertEqual(self.run_cli("validate", self.export())[0], 0)
        self.assertEqual(self.run_cli("validate", self.export(kind="note"), "--shape-only")[0], 1)
        self.assertEqual(self.run_cli("validate", self.export(params={"x": "fast"}), "--shape-only")[0], 1)

    # GDD 1.3 safety rules: approved ranges, APPROVED_P0 never off, T-01 ships (dry runs A H2, B H2)
    def test_out_of_range_param_is_refused(self):
        rc, out = self.run_cli("validate", self.export(params={"CORE-01.move_speed": 999, "UMB-03.catch_window": 0.25}))
        self.assertEqual(rc, 1, out)
        self.assertIn("CORE-01.move_speed=999 is outside the approved range 150-650", out)
        self.assertEqual(self.run_cli("validate", self.export(params={"CORE-01.move_speed": 650}))[0], 0)  # edge passes

    def test_p0_flag_off_is_refused_unless_decided(self):
        off = {"UMB-03": True, "WIND-01": False, "COM-01": False}
        rc, out = self.run_cli("validate", self.export(flags=off))
        self.assertEqual(rc, 1, out)
        self.assertIn("COM-01=off, but COM-01 is APPROVED_P0", out)
        self.assertEqual(self.run_cli("validate", self.export(flags={"COM-01": True}))[0], 0)
        write(os.path.join(self.root, bp.DECISIONS), DECIDED_T03)
        self.assertEqual(self.run_cli("validate", self.export(flags=off))[0], 0, "a DECIDED row naming COM-01 lifts the rule")
        write(os.path.join(self.root, bp.DECISIONS), DECIDED_T03.replace("DECIDED 2026-11-15 (Rick)", "open"))
        self.assertEqual(self.run_cli("validate", self.export(flags=off))[0], 1, "an open row does not")
        write(os.path.join(self.root, bp.DECISIONS), DECIDED_MENTION)
        self.assertEqual(self.run_cli("validate", self.export(flags=off))[0], 1, "naming COM-01 without Overrides does not")
        self.assertEqual(self.run_cli("bake", self.export(preset="T-03"))[0], 1, "naming T-03 without Overrides does not")

    def test_non_base_preset_is_refused_unless_decided(self):
        rc, out = self.run_cli("bake", self.export(preset="T-03"))
        self.assertEqual(rc, 1, out)
        self.assertIn("preset T-03 is not T-01", out)
        write(os.path.join(self.root, bp.DECISIONS), DECIDED_T03)
        self.assertEqual(self.run_cli("bake", self.export(preset="T-03"))[0], 0)
        self.assertEqual(self.run_cli("check", "--preset", "T-03")[0], 0)

    def test_check_rejects_a_hand_edited_stamp(self):
        self.assertEqual(self.run_cli("bake", self.export())[0], 0)
        sp = os.path.join(self.root, bp.STAMP)
        st = json.loads(read(sp))
        st["values"]["CORE-01.move_speed"] = 5000  # broken on purpose
        write(sp, bp.dump_json(st))
        write(self.move, MOVE_H.replace("600.f", "5000.f"))
        rc, out = self.run_cli("check")
        self.assertEqual(rc, 1, out)
        self.assertIn("outside the approved range", out)

    def test_ci_runs_the_bake_check_once_baked(self):
        # dry run B M6: tuning PRs after the bake must not drift silently until G4
        wf = read(os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), ".github", "workflows",
                               "pipeline-checks.yml"))
        self.assertRegex(wf, r"if \[ -f pipeline/qa/baked\.json \]; then python3 tools/bake_preset\.py check;")

    def test_literal_style_is_kept(self):
        self.assertEqual(bp.format_literal("600.f", 640), "640.0f")
        self.assertEqual(bp.format_literal("3", 4), "4")
        self.assertEqual(bp.format_literal("3", 4.5), "4.5")
        self.assertEqual(bp.format_literal("false", True), "true")


if __name__ == "__main__":
    unittest.main()
