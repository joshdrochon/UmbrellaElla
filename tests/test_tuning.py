"""tools/tuning.py: the one tunable/fixed rule the bake, feel_check and encounter_check share (dry run B H3, H4)."""
import copy
import json
import os
import shutil
import sys
import tempfile
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, os.path.join(ROOT, "tools"))
import tuning  # noqa: E402
import feel_check  # noqa: E402
import encounter_check  # noqa: E402


L13 = os.path.join(HERE, "fixtures", "gdd13")   # the GDD 1.3 manifest, feel.json and encounter.json, frozen


def load(rel, root=L13):
    with open(os.path.join(root, rel), encoding="utf-8") as fh:
        return json.load(fh)


class Tuning(unittest.TestCase):
    def setUp(self):
        self.man = load(tuning.MANIFEST)
        self.feel = load(tuning.FEEL)
        self.enc = load(tuning.ENCOUNTER)

    def test_rules(self):
        m = self.man
        self.assertEqual(tuning.rule(m, "CORE-01.move_speed")["kind"], "tunable")
        self.assertEqual(tuning.rule(m, "OWL-01.seed"), {"kind": "fixed", "start": 20261112, "unit": "integer"})
        self.assertEqual(tuning.rule(m, "OWL-01.collision_radius")["start"], None)
        self.assertIsNone(tuning.value_problem(m, "CORE-01.move_speed", 375))
        self.assertIsNone(tuning.value_problem(m, "OWL-01.cadence", 2.5))
        self.assertIsNone(tuning.value_problem(m, "COM-01.cadence", 0.2))
        self.assertIsNone(tuning.value_problem(m, "BG-01.near_speed", 1.3))   # float step 0.1
        for key, v in (("CORE-01.move_speed", 351.3), ("CORE-01.move_speed", 700), ("OWL-01.seed", 1),
                       ("OWL-01.initial_grace_s", 0), ("OWL-01.cadence", 2.6)):
            with self.subTest(key=key, v=v):
                self.assertIsNotNone(tuning.value_problem(m, key, v))
        self.assertIsNotNone(tuning.value_problem(m, "OWL-01.collision_radius", 400, current=12))
        self.assertIsNone(tuning.value_problem(m, "OWL-01.collision_radius", 12, current=12))

    def test_every_approved_start_is_on_its_own_rule(self):
        for key, rec in tuning.approved(self.man).items():
            with self.subTest(key):
                self.assertIsNone(tuning.value_problem(self.man, key, rec["start"]))

    def test_flags(self):
        self.assertIsNone(tuning.flag_problem(self.man, "DEF-01", True))
        self.assertIsNone(tuning.flag_problem(self.man, "SURV-04", False))
        self.assertIsNotNone(tuning.flag_problem(self.man, "SURV-04", True))
        self.assertIsNotNone(tuning.flag_problem(self.man, "MOVE-03", True))

    def test_sim_values_read_the_data_files(self):
        sim = tuning.sim_values(L13)
        self.assertEqual(set(sim), set(tuning.SIM_KEYS))
        for key in tuning.SIM_KEYS:
            with self.subTest(key):
                self.assertAlmostEqual(sim[key], tuning.approved(self.man)[key]["start"])

    def test_baked_vs_sim(self):
        sim = tuning.sim_values(L13)
        self.assertEqual(tuning.baked_vs_sim_problems(L13, baked=dict(sim)), [])
        self.assertEqual(tuning.baked_vs_sim_problems(L13, baked={}), [], "nothing baked yet")
        for key, v in (("OWL-01.cadence", 1.2), ("OWL-01.telegraph_delay", 0.3), ("OWL-01.projectile_speed", 900),
                       ("CORE-01.move_speed", 650), ("CORE-03.invulnerability_s", 0.5)):
            with self.subTest(key):   # broken on purpose: shipped number the sims never saw
                got = tuning.baked_vs_sim_problems(L13, baked=dict(sim, **{key: v}))
                self.assertTrue(any(g.startswith(key) for g in got), got)

    def test_cli_uses_the_stamp(self):
        root = tempfile.mkdtemp()
        try:
            for rel in (tuning.FEEL, tuning.ENCOUNTER, tuning.MANIFEST):
                os.makedirs(os.path.dirname(os.path.join(root, rel)), exist_ok=True)
                shutil.copy(os.path.join(L13, rel), os.path.join(root, rel))
            self.assertEqual(tuning.main(["--root", root]), 0)
            os.makedirs(os.path.join(root, "pipeline", "qa"), exist_ok=True)
            with open(os.path.join(root, tuning.STAMP), "w") as fh:
                json.dump({"values": {"OWL-01.cadence": 1.2}}, fh)
            self.assertEqual(tuning.main(["--root", root]), 1)
        finally:
            shutil.rmtree(root)

    def test_feel_check_and_encounter_check_use_the_step(self):
        """Off-step values fail the sims exactly as they fail the bake."""
        self.assertEqual([x for x in feel_check.check(self.feel, self.man) if x[0] == "gdd"], [])
        f = copy.deepcopy(self.feel)
        f["movement"]["move_speed"] = 351.3
        self.assertTrue(any(x[0] == "gdd" and "move_speed" in x[1] for x in feel_check.check(f, self.man)))
        ok, _ = encounter_check.approved_ok(self.man, "OWL-01.cadence", 2.6)
        self.assertFalse(ok)
        self.assertTrue(encounter_check.approved_ok(self.man, "OWL-01.cadence", 2.5)[0])
        self.assertFalse(encounter_check.approved_ok(self.man, "OWL-01.seed", 1)[0])


class StolenHour(unittest.TestCase):
    """GDD SH1.0: the four-state speeds and the Keeper preset numbers are what the sims read."""

    def test_model_follows_the_manifest(self):
        self.assertEqual(tuning.model(load(tuning.MANIFEST, ROOT))["feel_movement"]["rise_speed"], "MOVE-21.rise_speed")
        self.assertTrue(tuning.model(load(tuning.MANIFEST))["timeline"])

    def test_sim_values_are_the_gdd_starts(self):
        man = load(tuning.MANIFEST, ROOT)
        sim = tuning.sim_values(ROOT)
        self.assertEqual(set(sim), set(tuning.sim_keys(None, ROOT)))
        self.assertIn("OWL-08.clock_hp", sim)
        self.assertIn("SURV-05.post_hit_protection_s", sim)
        for key, v in sim.items():
            with self.subTest(key):
                self.assertAlmostEqual(v, tuning.approved(man)[key]["start"])
                self.assertEqual(tuning.rule(man, key)["kind"], "fixed", "GDD SH1.0 prints no dev ranges yet")
        self.assertEqual(tuning.baked_vs_sim_problems(ROOT, baked=dict(sim)), [])
        got = tuning.baked_vs_sim_problems(ROOT, baked=dict(sim, **{"OWL-08.clock_hp": 300}))
        self.assertTrue(any(g.startswith("OWL-08.clock_hp") for g in got), got)


if __name__ == "__main__":
    unittest.main()
