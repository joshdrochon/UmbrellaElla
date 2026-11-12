"""GDD 1.3 frozen data (tests/fixtures/gdd13): these rules model the 1.3 timer arena; GDD SH1.0 data is checked in its own tests. Tests for the owl hit-reaction rules (E26 clock, E27 wing), the wiring mode (W1-W5) and the encounter card
mode (C1-C5) of tools/encounter_check.py. Each failing case breaks the input on purpose."""
import copy
import json
import os
import shutil
import sys
import tempfile
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
for d in ("tools", os.path.join("pipeline", "level")):
    if os.path.exists(os.path.join(ROOT, d, "encounter_check.py")):
        sys.path.insert(0, os.path.join(ROOT, d))
        break
import encounter_check as ec  # noqa: E402

with open(os.path.join(ROOT, "tests", "fixtures", "gdd13", "pipeline", "level", "encounter.json"), encoding="utf-8") as fh:
    BASE = json.load(fh)
with open(os.path.join(ROOT, BASE["arena"]["tuning_source"]), encoding="utf-8") as fh:
    TUNING = json.load(fh)
FIX = os.path.join(ROOT, "pipeline", "level", "fixtures")

MULTI_PATH = os.path.join(ROOT, "tests", "fixtures", "level", "multi_pattern.json")
with open(MULTI_PATH, encoding="utf-8") as fh:
    MULTI = json.load(fh)
with open(os.path.join(ROOT, "tests", "fixtures", "gdd13", "docs", "feature-manifest.json"), encoding="utf-8") as fh:
    MANIFEST = json.load(fh)


def multi_tuning():
    """The live tuning file with the old B-era hero speeds (1920 x 1080 arena units) and lift loss, so the
    five-pattern fixture keeps proving the multi-pattern rules exactly as it did before GDD 1.3."""
    t = copy.deepcopy(TUNING)
    t["movement"].update(move_speed=422.4, open_steer_multiplier=100, ascent_speed=129.6, ascent_accel=324.0,
                         max_fall_speed=756.0, lift_by_tier={"intact": 1.0, "damaged": 0.85, "critical": 0.7})
    return t


def multi_manifest():
    """Live manifest with the fixture's features on: owl gust, arc, clock interrupt, wing hits, and the
    test-only OWL-90 (extra bolt patterns), with the fixture's old base-bolt numbers as approved."""
    m = copy.deepcopy(MANIFEST)
    for f in m["features"]:
        if f["feature_id"] in ("OWL-02", "OWL-04", "COM-02", "COM-03"):
            f["default_enabled"] = True
    extra = copy.deepcopy(next(f for f in m["features"] if f["feature_id"] == "OWL-01"))
    extra["feature_id"] = "OWL-90"
    m["features"].append(extra)
    v = m["approved_parameters"]["values"]
    v["END-01.survival_s"]["start"] = 150
    v["OWL-01.telegraph_delay"]["start"] = 0.8
    v["OWL-01.projectile_speed"]["start"] = 450
    return m


MULTI_TUNING, MULTI_MANIFEST = multi_tuning(), multi_manifest()


def rules(data):
    # Clock interrupts (COM-02) and wing hits (COM-03) are off in GDD 1.3; the fixture turns them on.
    return {r for r, _, _ in ec.check(data, None, MULTI_TUNING, manifest=MULTI_MANIFEST)[0]}


class HitReactionTests(unittest.TestCase):
    def setUp(self):
        self.d = copy.deepcopy(MULTI)
        self.p = self.d["patterns"]

    def test_repo_data_passes_e26_e27(self):
        self.assertFalse({"E26", "E27"} & rules(self.d))

    def test_missing_interruptible_sec_fails(self):
        del self.p["BOLT_Fan3"]["interruptible_sec"]
        self.assertIn("E26", rules(self.d))

    def test_interrupt_too_long_fails(self):
        self.p["BOLT_Single"]["interruptible_sec"] = 1.5
        self.assertIn("E26", rules(self.d))

    def test_interrupt_at_limit_passes(self):
        self.p["ARC_Return"]["interruptible_sec"] = 1.0
        self.p["ARC_Return"]["interrupt_replays_telegraph"] = True
        self.assertNotIn("E26", rules(self.d))

    def test_interrupt_that_skips_the_telegraph_fails(self):
        self.p["BOLT_Aimed2"]["interrupt_replays_telegraph"] = False
        self.assertIn("E26", rules(self.d))

    def test_zero_interrupt_needs_no_replay_flag(self):
        self.p["BOLT_Single"]["interruptible_sec"] = 0
        self.p["BOLT_Single"].pop("interrupt_replays_telegraph")
        self.assertNotIn("E26", rules(self.d))

    def test_interrupts_that_eat_the_breather_fail(self):
        # intro: one bolt every 7.5 s leaves a 3.7 s window; a 1.0 s pause plus a replayed telegraph leaves 1.9 s
        self.d["phases"][0]["schedule"] = [{"at": t, "pattern": "BOLT_Single"} for t in (2, 9.5, 17, 24.5, 32)]
        self.p["BOLT_Single"]["interruptible_sec"] = 0
        self.assertFalse({"E8", "E26"} & rules(self.d))
        self.p["BOLT_Single"]["interruptible_sec"] = 1.0
        self.assertIn("E26", rules(self.d))

    def test_missing_wing_tiers_fails(self):
        del self.p["GUST_Wing"]["gust_strength_by_wing_tier"]
        self.assertIn("E27", rules(self.d))

    def test_rising_wing_tiers_fail(self):
        self.p["GUST_Wing"]["gust_strength_by_wing_tier"] = [1.0, 0.6, 0.8]
        self.assertIn("E27", rules(self.d))

    def test_tiers_not_starting_at_one_fail(self):
        self.p["GUST_Wing"]["gust_strength_by_wing_tier"] = [0.9, 0.8, 0.6]
        self.assertIn("E27", rules(self.d))

    def test_zero_strength_tier_fails(self):
        self.p["GUST_Wing"]["gust_strength_by_wing_tier"] = [1.0, 0.5, 0.0]
        self.assertIn("E27", rules(self.d))

    def test_tiers_without_tear_overlays_fail(self):
        self.p["GUST_Wing"]["wing_tear_overlays"] = ["T_Owl_WingTear_1"]
        self.assertIn("E27", rules(self.d))

    def test_wing_hits_cut_passes(self):
        self.p["GUST_Wing"]["gust_strength_by_wing_tier"] = [1.0]
        del self.p["GUST_Wing"]["wing_tear_overlays"]
        self.assertNotIn("E27", rules(self.d))

    def test_doc_shows_clock_pause_and_wing_tiers(self):
        md = ec.render(ec.with_tuning(self.d, MULTI_TUNING)[0])
        self.assertIn("Clock-hit pause s", md)
        self.assertIn("Wing hits (E27)", md)


GOOD = {
    "pipeline/day0-cards.md": "| 0.20 | Owl data types + 5 Owl tests | Gameplay Dev | Dev Lead | x | 0.3 | "
                              "`UmbrellaElla.Owl.*` PASS |\n"
                              "| 0.21 | Owl dump + eval cameras | Integrator | Dev Lead | x | 0.20 | "
                              "`encounter_check.py --data <dump>` prints 0 problem(s) |\n",
    "pipeline/qa/test-map.md": "\n".join(f"| Owl | `{t}` | 0.20 | planned |" for t in ec.OWL_TESTS) + "\n",
    "pipeline/qa/playtests.md": "Columns: `" + ",".join(ec.PLAYTEST_COLUMNS) + "`.\n",
    "AGENTS.md": "| Level Designer | Arena zones, owl patterns and phase data | `pipeline/roles/level-designer.md` |\n",
    "pipeline/roles/game-designer.md": "Review encounter cards against `encounter_check.py` output.\n",
}


class WiringTests(unittest.TestCase):
    def setUp(self):
        self.root = tempfile.mkdtemp()
        self.write(GOOD)

    def tearDown(self):
        shutil.rmtree(self.root)

    def write(self, files):
        for rel, text in files.items():
            path = os.path.join(self.root, rel)
            os.makedirs(os.path.dirname(path), exist_ok=True)
            with open(path, "w", encoding="utf-8") as fh:
                fh.write(text)

    def rules(self):
        return {r for r, _, _ in ec.check_wiring(self.root)}

    def test_all_filed_passes(self):
        self.assertEqual(ec.check_wiring(self.root), [])
        self.assertEqual(ec.main(["--wiring", self.root]), 0)

    def test_missing_dump_card_fails(self):
        self.write({"pipeline/day0-cards.md": GOOD["pipeline/day0-cards.md"].splitlines()[0] + "\n"})
        self.assertIn("W1", self.rules())

    def test_owl_name_outside_a_table_row_fails(self):
        self.write({"pipeline/day0-cards.md": "Owl data types: UmbrellaElla.Owl (requested). Owl dump: "
                                              "encounter_check.py --data (requested)\n"})
        self.assertIn("W1", self.rules())

    def test_missing_test_name_fails(self):
        self.write({"pipeline/qa/test-map.md": GOOD["pipeline/qa/test-map.md"].replace(ec.OWL_TESTS[-1], "x")})
        self.assertIn("W2", self.rules())

    def test_old_platformer_log_columns_fail(self):
        self.write({"pipeline/qa/playtests.md":
                    "Columns: `session,event,section,spot,cause,x,z,t_run_s,t_section_s,build`.\n"})
        self.assertIn("W3", self.rules())

    def test_missing_role_row_fails(self):
        self.write({"AGENTS.md": "| Game Designer | Balance | `pipeline/roles/game-designer.md` |\n"})
        self.assertIn("W4", self.rules())

    def test_old_reviewer_criteria_fail(self):
        self.write({"pipeline/roles/game-designer.md": "Section difficulty: each section's new element.\n"})
        self.assertIn("W5", self.rules())

    def test_missing_files_fail_not_crash(self):
        empty = tempfile.mkdtemp()
        try:
            self.assertEqual({r for r, _, _ in ec.check_wiring(empty)}, {"W1", "W2", "W3", "W4", "W5"})
        finally:
            shutil.rmtree(empty)


class PlaythroughPhaseTests(unittest.TestCase):
    """tools/ue_run.py PLAYTHROUGH: phase fields are due only when encounter.json uses the phase presets."""

    def root_with(self, data):
        root = tempfile.mkdtemp()
        self.addCleanup(shutil.rmtree, root)
        if data is not None:
            os.makedirs(os.path.join(root, "pipeline", "level"))
            with open(os.path.join(root, "pipeline", "level", "encounter.json"), "w", encoding="utf-8") as fh:
                json.dump(data, fh)
        return root

    def test_base_phase_needs_no_phase_fields(self):
        sys.path.insert(0, os.path.join(ROOT, "tools"))
        import ue_run
        line = "PLAYTHROUGH abc1234 | survived pass | fail-retry pass | fail-bottom pass | quit-play pass | quit-title pass | quit-pause pass"
        self.assertEqual(ue_run.playthrough_problems(line, root=self.root_with(BASE)), [])
        self.assertIn("contest: blank (a blank field is not a pass)",
                      ue_run.playthrough_problems(line, root=self.root_with(MULTI)))
        self.assertIn("intro: blank (a blank field is not a pass)",
                      ue_run.playthrough_problems(line, root=self.root_with(None)))   # unreadable: strict


class LoggerFormatTests(unittest.TestCase):
    """The fixture is what the logger card must write: the Columns line of playtests.md, one row per event."""

    def test_logger_fixture_passes_playtest_mode(self):
        path = os.path.join(FIX, "logger_output.csv")
        # The logger fixture logs the five-pattern preset fixture's patterns.
        self.assertEqual(ec.check_playtest(MULTI, [path])[0], [])
        self.assertEqual(ec.main(["--data", MULTI_PATH, "--playtest", path]), 0)
        self.assertIn("L3", {r for r, _, _ in ec.check_playtest(BASE, [path])[0]})   # BOLT_Fan3 is not a GDD 1.3 pattern

    def test_logger_fixture_header_is_the_spec_line(self):
        with open(os.path.join(FIX, "logger_output.csv"), encoding="utf-8") as fh:
            self.assertEqual(fh.readline().strip(), ",".join(ec.PLAYTEST_COLUMNS))

    def test_old_logger_format_fails(self):
        tmp = tempfile.mkdtemp()
        try:
            path = os.path.join(tmp, "old.csv")
            with open(path, "w", encoding="utf-8") as fh:
                fh.write("session,event,section,spot,cause,x,z,t_run_s,t_section_s,build\n"
                         "s01,death,S2,SPOT_S2_1,spike,10,20,61.0,12.0,abc1234\n")
            self.assertIn("L1", {r for r, _, _ in ec.check_playtest(BASE, [path])[0]})
        finally:
            shutil.rmtree(tmp)


class CardTests(unittest.TestCase):
    def setUp(self):
        with open(os.path.join(FIX, "card_ok.md"), encoding="utf-8") as fh:
            self.text = fh.read()

    def rules(self, text):
        return {r for r, _, _ in ec.check_card_text(text)}

    def drop(self, needle):
        return "\n".join(l for l in self.text.splitlines() if needle not in l)

    def test_good_card_passes(self):
        self.assertEqual(ec.check_card_text(self.text), [])
        self.assertEqual(ec.main(["--card", os.path.join(FIX, "card_ok.md")]), 0)

    def test_no_data_gate_paste_fails(self):
        self.assertIn("C1", self.rules(self.drop("encounter_check: 0 problem(s)")))

    def test_no_coverage_line_fails(self):
        self.assertIn("C2", self.rules(self.drop("Coverage signed:")))

    def test_coverage_placeholder_fails(self):
        self.assertIn("C2", self.rules(self.text.replace("Coverage signed: Sam Lee 2026-11-20",
                                                         "Coverage signed: <name> <date>")))

    def test_coverage_without_date_fails(self):
        self.assertIn("C2", self.rules(self.text.replace("Coverage signed: Sam Lee 2026-11-20",
                                                         "Coverage signed: Sam Lee")))

    def test_no_motion_check_fails(self):
        self.assertIn("C3", self.rules(self.drop("Motion check:")))

    def test_no_accent_check_fails(self):
        self.assertIn("C3", self.rules(self.drop("Accent check:")))

    def test_no_paper_walk_fails(self):
        self.assertIn("C4", self.rules(self.drop("Paper walk:")))

    def test_paper_walk_without_link_fails(self):
        self.assertIn("C4", self.rules(self.text.replace("Paper walk: #41", "Paper walk: done")))

    def test_engine_test_missing_fails(self):
        self.assertIn("C5", self.rules(self.drop(ec.OWL_TESTS[0])))

    def test_not_run_without_card_number_fails(self):
        bad = self.text.replace(f"Not run: `{ec.OWL_TESTS[2]}` (#20)", f"Not run: `{ec.OWL_TESTS[2]}`")
        self.assertIn("C5", self.rules(bad))


if __name__ == "__main__":
    unittest.main()
