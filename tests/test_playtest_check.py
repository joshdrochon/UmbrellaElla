import importlib.util, pathlib, unittest
p = pathlib.Path(__file__).resolve().parents[1] / "tools/build/playtest_check.py"
s = importlib.util.spec_from_file_location("playtest_check", p)
pc = importlib.util.module_from_spec(s); s.loader.exec_module(pc)

GOOD = """
PLAYTEST_CAM04 profile=v2 health=full trim=0.00 entered=1 exit_edge=right exit_root_z=290 qualified=1
PLAYTEST_CAM04 profile=v2 health=full trim=1.00 entered=1 exit_edge=right exit_root_z=300 qualified=1
PLAYTEST_CAM04 profile=v2 health=full trim=-1.00 entered=1 exit_edge=right exit_root_z=280 qualified=1
PLAYTEST_CAM04 profile=v2 health=min trim=0.00 entered=1 exit_edge=right exit_root_z=275 qualified=1
PLAYTEST_CAM04 profile=v2 health=min trim=1.00 entered=1 exit_edge=right exit_root_z=278 qualified=1
PLAYTEST_CAM04 profile=v2 health=min trim=-1.00 entered=1 exit_edge=right exit_root_z=272 qualified=1
PLAYTEST_CAM04T profile=v2 rode=1 accel_t90=0.43 brake_t10=1.53 reacq_t90=0.42 decay_open_t10=1.53 decay_fall_t10=0.20
PLAYTEST_FLOW25 drawn_width=200 usable_width=198 tol=5 lead_left_ok=1 lead_right_ok=1 stages_total=4 stages_covered=4
PLAYTEST_CAM07 case=ontime reopen_root_z=270 min_root_z=270 min_clear=102 caught=1 required_current_active=1 challenge_clear=0
PLAYTEST_CAM07 case=late reopen_root_z=210 min_root_z=210 min_clear=42 caught=1 required_current_active=1 challenge_clear=0
PLAYTEST_CAM07 case=missed reopen_root_z=150 min_root_z=150 min_clear=-18 caught=0 required_current_active=1 challenge_clear=0
PLAYTEST_FLOW28 health_before=6 health_after=6 max=10 threats=0 framing_settled=1 boss_began=1
PLAYTEST_HAZ16 res=1280x720 debug=0 health=healthy autoaim=0 invuln=0 teleport=0 boring=0 cleared=1
PLAYTEST_HAZ16 res=1920x1080 debug=0 health=low autoaim=0 invuln=0 teleport=0 boring=0 cleared=1
"""

class T(unittest.TestCase):
    def test_good(self):
        r = pc.evaluate(GOOD)
        self.assertTrue(all(v["pass"] for v in r.values()), r)

    def test_missing_is_fail(self):
        self.assertFalse(pc.evaluate("")["CAM-04"]["pass"])

    def test_free_heal_fails(self):
        r = pc.evaluate(GOOD.replace("health_after=6", "health_after=8"))
        self.assertFalse(r["FLOW-28"]["pass"])

    def test_current_gone_early_fails(self):
        r = pc.evaluate(GOOD.replace("required_current_active=1", "required_current_active=0"))
        self.assertFalse(r["CAM-07"]["pass"])

    def test_persist_dead_ticks_fail_even_when_cleared(self):
        line = "PLAYTEST_CAM07 case=persist samples=80 samples_live=0 required_current_active=0 challenge_clear=1"
        self.assertFalse(pc.evaluate(GOOD + line)["CAM-07"]["pass"])
        ok = "PLAYTEST_CAM07 case=persist samples=80 samples_live=80 required_current_active=1 challenge_clear=1"
        self.assertTrue(pc.evaluate(GOOD + ok)["CAM-07"]["pass"])

    def test_teleport_fails(self):
        r = pc.evaluate(GOOD.replace("teleport=0", "teleport=1", 1))
        self.assertFalse(r["HAZ-16"]["pass"])

    def test_missing_background_fails(self):
        r = pc.evaluate(GOOD.replace("stages_covered=4", "stages_covered=3"))
        self.assertFalse(r["FLOW-25"]["pass"])

    def test_path_leaving_band_top_fails(self):
        bad = GOOD.replace("trim=1.00 entered=1 exit_edge=right exit_root_z=300 qualified=1",
                           "trim=1.00 entered=1 exit_edge=top exit_root_z=331 qualified=0")
        r = pc.evaluate(bad)
        self.assertFalse(r["CAM-04"]["pass"])
        self.assertTrue(any("by the top" in e for e in r["CAM-04"]["errors"]), r)

    def test_never_rode_fails(self):
        r = pc.evaluate(GOOD.replace("health=min trim=0.00 entered=1", "health=min trim=0.00 entered=0"))
        self.assertFalse(r["CAM-04"]["pass"])

    def test_missing_trim_profile_fails(self):
        lines = [l for l in GOOD.splitlines() if "health=min trim=-1.00" not in l]
        r = pc.evaluate("\n".join(lines))
        self.assertIn("no min-health trim -1.00 path", r["CAM-04"]["errors"])

    def test_missing_transients_fails(self):
        lines = [l for l in GOOD.splitlines() if "CAM04T" not in l]
        self.assertIn("no transient measurement (CAM04T)", pc.evaluate("\n".join(lines))["CAM-04"]["errors"])

    def test_transient_never_reached_fails(self):
        r = pc.evaluate(GOOD.replace("brake_t10=1.53", "brake_t10=-1.00"))
        self.assertFalse(r["CAM-04"]["pass"])

    def test_late_reopen_not_caught_fails(self):
        r = pc.evaluate(GOOD.replace("case=late reopen_root_z=210 min_root_z=210 min_clear=42 caught=1",
                                     "case=late reopen_root_z=210 min_root_z=210 min_clear=42 caught=0"))
        self.assertFalse(r["CAM-07"]["pass"])

    def test_reopen_into_floor_fails(self):
        r = pc.evaluate(GOOD.replace("min_clear=102", "min_clear=-3"))
        self.assertFalse(r["CAM-07"]["pass"])

    def test_missed_case_is_reported_not_gated(self):
        self.assertTrue(pc.evaluate(GOOD)["CAM-07"]["pass"])

    def test_missing_ontime_case_fails(self):
        lines = [l for l in GOOD.splitlines() if "case=ontime" not in l]
        self.assertIn("no ontime reopen case", pc.evaluate("\n".join(lines))["CAM-07"]["errors"])


    def test_relay_lines_never_count(self):
        relay = "\n".join(l + " relay=1" for l in GOOD.strip().splitlines())
        self.assertFalse(pc.evaluate(relay)["CAM-04"]["pass"])
        self.assertTrue(all(v["pass"] for v in pc.evaluate(relay, relay=True).values()))

    def test_relay_line_does_not_rescue_a_failing_row(self):
        bad = GOOD.replace("health=min trim=0.00 entered=1", "health=min trim=0.00 entered=0")
        extra = "PLAYTEST_CAM04 profile=v2 health=min trim=0.00 entered=1 exit_edge=right qualified=1 relay=1"
        self.assertFalse(pc.evaluate(bad + extra)["CAM-04"]["pass"])

    def test_not_measured_is_not_a_pass(self):
        r = pc.evaluate(GOOD.replace("boss_began=1", "boss_began=1 not_measured=route_not_finished_in_time"))
        self.assertFalse(r["FLOW-28"]["pass"])
        self.assertIn("NOT MEASURED", r["FLOW-28"]["errors"][0])

    def test_transient_outside_fixed_range_fails(self):
        r = pc.evaluate(GOOD.replace("accel_t90=0.43", "accel_t90=2.50"))
        self.assertFalse(r["CAM-04"]["pass"])
        self.assertIn("fixed range", "; ".join(r["CAM-04"]["errors"]))

    def test_transient_range_is_not_the_run_own_value(self):
        # a slow motor cannot pass by being measured slow: ranges are the frozen mill_lower_v2 numbers
        r = pc.evaluate(GOOD.replace("brake_t10=1.53", "brake_t10=9.00"))
        self.assertFalse(r["CAM-04"]["pass"])

    def test_negative_steady_velocity_is_judged_not_skipped(self):
        r = pc.evaluate(GOOD.replace("rode=1 accel_t90=0.43", "rode=1 steady_vz=-5.00 accel_t90=0.43"))
        self.assertFalse(r["CAM-04"]["pass"])
        self.assertIn("steady_vz", "; ".join(r["CAM-04"]["errors"]))

    def test_v2_recorded_and_v1_kept_as_history(self):
        cal = pc.CAL
        self.assertEqual(cal.PROFILE, "mill_lower_v2")
        self.assertIn("mill_lower_v1", cal.PROFILES)
        self.assertEqual(cal.PROFILES["mill_lower_v1"]["steady_vz"], (115.0, 125.0))
        lo, hi = cal.TRANSIENT_RANGES["steady_vz"]
        self.assertTrue(lo <= -54.0 <= hi)  # the windfix motor pulls toward z 230

    def test_recorded_run_cam04_passes_v2(self):
        log = pathlib.Path(__file__).resolve().parents[1] / "docs/build/playtest-logs/run-2026-11-12g.log"
        self.assertEqual(pc.evaluate(log.read_text())["CAM-04"]["errors"], [])


if __name__ == "__main__":
    unittest.main()
