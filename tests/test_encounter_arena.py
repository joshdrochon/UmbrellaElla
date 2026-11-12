"""GDD 1.3 frozen data (tests/fixtures/gdd13): these rules model the 1.3 timer arena; GDD SH1.0 data is checked in its own tests. Tests for the arc sim (E2, E13, E14), the camping grid (E20) and torn-umbrella recovery (E25) in
tools/encounter_check.py. Each failing case breaks data on purpose. The arc, gust and lift-loss rules need
features GDD 1.3 keeps off, so they run on the five-pattern fixture with those features on."""
import copy
import json
import os
import sys
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
    # The old collider at 1920 x 1080 scale (60% of the body box, 80% of the 17.5 bolt core), as fixed data
    t["forgiveness"].update(player_hurtbox_cm={"w": 63.36, "h": 95.904}, bolt_hitbox_radius_cm=14.0)
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


def problems(data, tuning=None):
    return ec.check(data, None, tuning or MULTI_TUNING, manifest=MULTI_MANIFEST)[0]


def rules(data, tuning=None):
    return {r for r, _, _ in problems(data, tuning)}


class ArenaTests(unittest.TestCase):
    def setUp(self):
        self.d = copy.deepcopy(MULTI)
        self.p = self.d["patterns"]
        self.ph = {ph["id"]: ph for ph in self.d["phases"]}
        self.arc = self.p["ARC_Return"]

    # passing case
    def test_fixture_passes_new_rules(self):
        self.assertEqual(rules(self.d), set())

    def test_repo_base_encounter_passes_camping_and_safe_path(self):
        # GDD 1.3: one aimed bolt every 3 s hits a still hero anywhere, and a moving hero always has a path.
        got = {r for r, _, _ in ec.check(copy.deepcopy(BASE))[0]}
        self.assertFalse(got & {"E13", "E14", "E20", "E25"}, got)

    def test_base_encounter_with_a_static_bolt_lets_hero_camp(self):
        d = copy.deepcopy(BASE)
        d["patterns"]["BOLT_Single"].update(aimed=False, base_angle_deg=180)
        self.assertIn("E20", {r for r, _, _ in ec.check(d, manifest=MANIFEST)[0]})

    # arc path shape
    def test_arc_goes_out_and_comes_back(self):
        merged, _ = ec.with_tuning(self.d, MULTI_TUNING)
        st, f, pos, _ = ec.arc_path(merged, self.arc, 0.0, 500.0, (500.0, 500.0))
        self.assertAlmostEqual(st, self.arc["telegraph_sec"])
        x0, y0 = pos(0.0)
        xm, ym = pos(f / 2.0)
        x1, y1 = pos(f)
        ox = merged["arena"]["owl_fire_x"]
        self.assertAlmostEqual((x0, y0), (ox, 500.0))
        self.assertAlmostEqual(xm, ox - self.arc["reach"], places=6)  # aimed left along y=500
        self.assertAlmostEqual(x1, ox, places=6)
        self.assertAlmostEqual(y1, 500.0, places=6)

    # E2 arc fields
    def test_arc_without_reach_fails(self):
        del self.arc["reach"]
        self.assertIn("E2", rules(self.d))

    def test_arc_flight_longer_than_active_fails(self):
        self.arc["flight_sec"] = self.arc["active_sec"] + 0.5
        self.assertIn("E2", rules(self.d))

    # E13 the arc is in the safe-path sim
    def test_huge_arc_blocks_safe_path(self):
        self.arc["core_radius"] = 700
        got = [w for r, w, _ in problems(self.d) if r == "E13"]
        self.assertTrue(any("ARC_Return" in w for w in got), got)

    # E14 the arc's position claim is measured
    def test_short_arc_cannot_claim_far(self):
        self.arc["reach"] = 300
        msgs = [m for r, w, m in problems(self.d) if r == "E14" and "ARC_Return" in w]
        self.assertTrue(any("pos_far" in m for m in msgs), msgs)

    # E20 grid
    def test_grid_has_corners_centre_and_mid_edges(self):
        merged, _ = ec.with_tuning(self.d, MULTI_TUNING)
        zone = ec.hero_zone(merged, self.ph["contest"])
        spots = dict(ec.camp_spots(merged, zone))
        self.assertEqual(len(spots), 25)
        hw, hh = merged["arena"]["hero_box"]["w"] / 2.0, merged["arena"]["hero_box"]["h"] / 2.0
        self.assertAlmostEqual(spots["grid(0,0)"][0], zone["x0"] + hw)
        self.assertAlmostEqual(spots["grid(4,4)"][1], zone["y1"] - hh)
        self.assertAlmostEqual(spots["grid(2,4)"][0], (zone["x0"] + zone["x1"]) / 2.0)

    def test_grid_respects_altitude_cap(self):
        merged, _ = ec.with_tuning(self.d, MULTI_TUNING)
        zone = ec.hero_zone(merged, self.ph["desperation"])
        top = max(y for _, (_, y) in ec.camp_spots(merged, zone))
        self.assertLessEqual(top, self.ph["desperation"]["altitude_cap_y"])

    def test_mid_edge_camping_is_caught(self):
        # A static fan that hits every corner and the centre at both drift ends (the old 5-spot probe
        # passes) but leaves mid-edge and quarter spots safe.
        self.p["STATIC"] = dict(self.p["BOLT_Single"], feature="OWL-90", aimed=False, base_angle_deg=180, covers=[],
                                angles_deg=[-63, -36, -24, -12, 9, 12, 24, 39, 64])
        con = self.ph["contest"]
        con["schedule"] = [e for e in con["schedule"] if not self.p[e["pattern"]].get("aimed")]
        con["schedule"].append({"at": 20, "pattern": "STATIC"})
        where = [m for r, _, m in problems(self.d) if r == "E20"]
        self.assertTrue(where)
        for legacy in ("grid(0,0)", "grid(4,0)", "grid(0,4)", "grid(4,4)", "grid(2,2)"):
            self.assertFalse(any(legacy in m for m in where), legacy)

    # E25 recovery with the torn umbrella
    def test_no_cap_means_no_recovery_in_one_breather(self):
        self.ph["desperation"]["altitude_cap_y"] = None
        self.assertIn("E25", rules(self.d))

    def test_weaker_critical_lift_fails(self):
        t = copy.deepcopy(MULTI_TUNING)
        t["movement"]["lift_by_tier"]["critical"] = 0.5
        self.assertIn("E25", rules(self.d, t))

    def test_short_breather_fails(self):
        for e in self.ph["desperation"]["schedule"]:
            if e["pattern"] == "BOLT_Fan3" and e["at"] == 31:
                e["at"] = 30
        self.assertIn("E25", rules(self.d))

    def test_no_lift_loss_turns_e25_off(self):
        # GDD 1.3 DEC-05: no lift loss in the baseline, so the torn-umbrella climb rule does not apply.
        t = copy.deepcopy(MULTI_TUNING)
        t["movement"]["lift_by_tier"] = {"intact": 1.0, "damaged": 1.0, "critical": 1.0}
        self.ph["desperation"]["altitude_cap_y"] = None
        self.assertNotIn("E25", rules(self.d, t))

    def test_ramp_copy_in_encounter_fails(self):
        self.d["arena"]["rise_ramp_s"] = 0.1
        self.assertIn("E22", rules(self.d))


if __name__ == "__main__":
    unittest.main()
