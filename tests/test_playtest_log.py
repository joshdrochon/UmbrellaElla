"""Tests for the playtest-log mode of the encounter gate (encounter_check.py --playtest, rules L1-L6).
Each failing case breaks a log row on purpose; the fixture log proves a clean log passes."""
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

FIX = os.path.join(HERE, "fixtures", "level")
OK = os.path.join(FIX, "playtest_ok.csv")
BAD = os.path.join(FIX, "playtest_bad.csv")
# The several-pattern fixture (the pre-1.3 data) exercises per-pattern reports; the repo data is the GDD 1.3 base.
with open(os.path.join(FIX, "multi_pattern.json"), encoding="utf-8") as fh:
    DATA = json.load(fh)
with open(os.path.join(ROOT, "tests", "fixtures", "gdd13", "pipeline", "level", "encounter.json"), encoding="utf-8") as fh:
    BASE = json.load(fh)
HEADER = ",".join(ec.PLAYTEST_COLUMNS)


class PlaytestLogTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.mkdtemp()

    def tearDown(self):
        shutil.rmtree(self.tmp)

    def log(self, *rows, header=HEADER):
        path = os.path.join(self.tmp, "log.csv")
        with open(path, "w", encoding="utf-8") as fh:
            fh.write("\n".join([header, *rows]) + "\n")
        return path

    def rules(self, *rows, header=HEADER):
        return {r for r, _, _ in ec.check_playtest(DATA, [self.log(*rows, header=header)])[0]}

    # passing cases
    def test_fixture_log_passes(self):
        problems, report = ec.check_playtest(DATA, [OK])
        self.assertEqual(problems, [])
        self.assertIn("BOLT_Fan3 | 1 | 0 | 1  <- bug against this pattern: fix the tell", report)
        self.assertIn("BOLT_Aimed2 | 0 | 1 | 0", report)

    # L6: a header with no rows is not a playtest (dry run 1)
    def test_header_only_log_fails(self):
        self.assertEqual(self.rules(), {"L6"})
        self.assertEqual(ec.main(["--playtest", self.log()]), 1)

    def test_one_survive_row_passes(self):
        self.assertEqual(self.rules("s1,survive,desperation,,,61.0,abc1234"), set())

    def test_cli_passes_on_fixture(self):
        self.assertEqual(ec.main(["--playtest", OK, "--data", os.path.join(FIX, "multi_pattern.json")]), 0)

    def test_gdd13_base_log(self):
        # GDD 1.3: one BOLT_Single, phase `base`; an old pattern id cannot be blamed any more
        ok = self.log("s1,hit,base,BOLT_Single,y,12.4,abc1234", "s1,survive,base,,,90.0,abc1234")
        self.assertEqual(ec.check_playtest(BASE, [ok])[0], [])
        bad = self.log("s1,hit,base,BOLT_Fan3,y,12.4,abc1234")
        self.assertIn("L3", {r for r, _, _ in ec.check_playtest(BASE, [bad])[0]})

    def test_stolen_hour_log_names_keeper_attacks_and_phases(self):
        with open(os.path.join(ROOT, "pipeline", "level", "encounter.json"), encoding="utf-8") as fh:
            sh = json.load(fh)
        ok = self.log("s1,hit,wings,RED_Fan,y,12.4,abc1234", "s1,hit,mechanisms,TALON_Rake,n,40.0,abc1234")
        self.assertEqual(ec.check_playtest(sh, [ok])[0], [])
        bad = self.log("s1,hit,base,BOLT_Single,y,12.4,abc1234")
        self.assertIn("L3", {r for r, _, _ in ec.check_playtest(sh, [bad])[0]})

    def test_bottom_exit_death_passes(self):
        self.assertEqual(self.rules("s1,death,intro,BOTTOM_EXIT,y,20,abc1234"), set())

    def test_survive_row_needs_no_pattern(self):
        self.assertEqual(self.rules("s1,survive,desperation,,,150,abc1234"), set())

    # failing cases
    def test_cli_fails_on_bad_fixture(self):
        self.assertEqual(ec.main(["--playtest", BAD, "--data", os.path.join(FIX, "multi_pattern.json")]), 1)
        got = {r for r, _, _ in ec.check_playtest(DATA, [BAD])[0]}
        self.assertEqual(got, {"L2", "L3", "L4", "L5"})

    def test_old_platformer_header_fails(self):
        self.assertEqual(self.rules("s1,death,S1,SPOT_S1_A,spike,1,2,3,4,abc",
                                    header="session,event,section,spot,cause,x,z,t_run_s,t_section_s,build"), {"L1"})

    def test_death_without_pattern_fails(self):
        self.assertIn("L3", self.rules("s1,death,contest,,y,60,abc1234"))

    def test_hit_without_pattern_fails(self):
        self.assertIn("L3", self.rules("s1,hit,contest,,n,60,abc1234"))

    def test_unknown_pattern_fails(self):
        self.assertIn("L3", self.rules("s1,death,contest,BOLT_Laser,y,60,abc1234"))

    def test_cut_pattern_fails(self):
        # A pattern cut from encounter.json (the P2 arc) cannot be blamed any more.
        data = json.loads(json.dumps(DATA))
        del data["patterns"]["ARC_Return"]
        path = self.log("s1,death,desperation,ARC_Return,y,120,abc1234")
        self.assertIn("L3", {r for r, _, _ in ec.check_playtest(data, [path])[0]})

    def test_explained_must_be_y_or_n(self):
        self.assertIn("L4", self.rules("s1,hit,contest,BOLT_Fan3,,60,abc1234"))

    def test_unknown_event_fails(self):
        self.assertIn("L2", self.rules("s1,clear,contest,BOLT_Fan3,y,60,abc1234"))

    def test_bad_phase_fails(self):
        self.assertIn("L5", self.rules("s1,hit,section2,BOLT_Fan3,y,60,abc1234"))

    def test_bad_time_fails(self):
        self.assertIn("L5", self.rules("s1,hit,contest,BOLT_Fan3,y,soon,abc1234"))

    def test_missing_build_fails(self):
        self.assertIn("L5", self.rules("s1,hit,contest,BOLT_Fan3,y,60,"))

    def test_short_row_fails(self):
        self.assertIn("L5", self.rules("s1,hit,contest"))

    def test_unexplained_hit_is_reported_not_failed(self):
        path = self.log("s1,hit,contest,GUST_Wing,n,60,abc1234", "s1,hit,contest,GUST_Wing,n,70,abc1234")
        problems, report = ec.check_playtest(DATA, [path])
        self.assertEqual(problems, [])
        self.assertIn("GUST_Wing | 2 | 0 | 2  <- bug against this pattern: fix the tell", report)


if __name__ == "__main__":
    unittest.main()
