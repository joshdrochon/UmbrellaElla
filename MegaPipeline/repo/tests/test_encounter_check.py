"""GDD 1.3 frozen data (tests/fixtures/gdd13): these rules model the 1.3 timer arena; GDD SH1.0 data is checked in its own tests. Tests for the encounter gate (tools/encounter_check.py). Each test breaks an encounter on purpose and
asserts the rule catches it. GddBaseTests run on the repo's GDD 1.3 data (one bolt, 90 s); EncounterCheckTests
run the rules that compare several patterns on the five-pattern fixture with those features switched on."""
import copy
import json
import os
import sys
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
# The checker may move to tools/ (a gate file); look there first.
for d in ("tools", os.path.join("pipeline", "level")):
    if os.path.exists(os.path.join(ROOT, d, "encounter_check.py")):
        sys.path.insert(0, os.path.join(ROOT, d))
        break
import encounter_check as ec  # noqa: E402

DATA = os.path.join(ROOT, "tests", "fixtures", "gdd13", "pipeline", "level", "encounter.json")
MD = os.path.join(ROOT, "tests", "fixtures", "gdd13", "pipeline", "level", "encounter.md")
with open(DATA, encoding="utf-8") as fh:
    BASE = json.load(fh)
TUNING_PATH = os.path.join(ROOT, BASE["arena"]["tuning_source"])
with open(TUNING_PATH, encoding="utf-8") as fh:
    TUNING = json.load(fh)

MULTI_PATH = os.path.join(ROOT, "tests", "fixtures", "level", "multi_pattern.json")
with open(MULTI_PATH, encoding="utf-8") as fh:
    MULTI = json.load(fh)
MANIFEST_PATH = os.path.join(ROOT, "tests", "fixtures", "gdd13", "docs", "feature-manifest.json")
with open(MANIFEST_PATH, encoding="utf-8") as fh:
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


def rules(data, md=None, tuning=None):
    return {r for r, _, _ in ec.check(data, md, tuning or MULTI_TUNING, manifest=MULTI_MANIFEST)[0]}


def base_rules(data, md=None, manifest=None):
    return {r for r, _, _ in ec.check(data, md, manifest=manifest or MANIFEST)[0]}


class StolenHourKeeperTests(unittest.TestCase):
    """The repo encounter is GDD SH1.0: a state-driven Keeper fight in the baseline preset; E29 holds its numbers."""

    def setUp(self):
        with open(os.path.join(ROOT, "pipeline", "level", "encounter.json"), encoding="utf-8") as fh:
            self.d = json.load(fh)
        with open(os.path.join(ROOT, "docs", "feature-manifest.json"), encoding="utf-8") as fh:
            self.m = json.load(fh)
        self.p = self.d["encounter_presets"]["presets"][self.d["encounter_presets"]["default"]]

    def state_rules(self, d=None, m=None):
        return [(r, w) for r, w, _ in ec.check(d or self.d, None, manifest=m or self.m)[0]]

    def test_repo_keeper_fight_passes(self):
        self.assertEqual(self.state_rules(), [])
        self.assertEqual(ec.main([]), 0)
        self.assertEqual([p["id"] for p in self.p["phases"]], ["wings", "mechanisms", "clock"])

    def test_gdd_numbers_are_held_to_the_manifest(self):
        atk = {a["id"]: a for a in self.p["attacks"]}
        for path, mutate in (("attacks.TALON_Rake.effect.damage", lambda: atk["TALON_Rake"]["effect"].update(damage=12)),
                             ("attacks.RED_Fan.effect.damage", lambda: atk["RED_Fan"]["effect"].update(damage=8)),
                             ("targets.CLOCK.hp", lambda: self.p["targets"][-1].update(hp=300)),
                             ("attacks.GUST_Band.telegraph.sec", lambda: atk["GUST_Band"]["telegraph"].update(sec=1.0))):
            with self.subTest(path):
                self.setUp()
                atk = {a["id"]: a for a in self.p["attacks"]}
                mutate()
                self.assertIn(("E29", f"presets.GDD-SH1.0.{path}"), self.state_rules())

    def test_old_timeline_or_off_feature_fails(self):
        d = copy.deepcopy(self.d)
        d["patterns"] = BASE["patterns"]
        self.assertIn(("E29", "patterns"), self.state_rules(d))
        m = copy.deepcopy(self.m)
        next(f for f in m["features"] if f["feature_id"] == "OWL-16")["default_enabled"] = False
        self.assertIn(("E29", "presets.GDD-SH1.0.attacks.GUST_Band"), self.state_rules(m=m))
        # a GDD 1.3 timeline checked against the SH1.0 manifest says it is history
        self.assertIn("E29", {r for r, _, _ in ec.check(copy.deepcopy(BASE), None, TUNING, manifest=self.m)[0]})


class GddBaseTests(unittest.TestCase):
    """The repo encounter is GDD 1.3 §5A/§7B: 90 s, one aimed BOLT_Single, 2.0 s grace, 0.75 s warning every 3.0 s."""
    def setUp(self):
        self.d = copy.deepcopy(BASE)
        self.b = self.d["patterns"]["BOLT_Single"]
        self.sched = self.d["phases"][0]["schedule"]

    def test_repo_data_and_doc_pass(self):
        with open(MD, encoding="utf-8") as fh:
            self.assertEqual(ec.check(self.d, fh.read(), manifest=MANIFEST)[0], [])

    def test_pre_gdd13_encounter_fails_e29(self):
        # The old 150 s, five-pattern file (BOLT_Single 0.8 s / 450) against the live manifest.
        got = [(r, w) for r, w, _ in ec.check(copy.deepcopy(MULTI), tuning=MULTI_TUNING)[0] if r == "E29"]
        where = {w for _, w in got}
        self.assertIn("patterns.GUST_Wing", where)   # OWL-02 off
        self.assertIn("patterns.ARC_Return", where)  # OWL-04 off
        self.assertTrue(any("BOLT_Single" in w for w in where), where)

    def test_base_bolt_numbers_must_equal_approved(self):
        for key, bad in (("telegraph_sec", 1.6), ("telegraph_sec", 0.2), ("speed", 950), ("aimed", False),
                         ("angles_deg", [-5, 5])):
            with self.subTest(key=key):
                d = copy.deepcopy(self.d)
                d["patterns"]["BOLT_Single"][key] = bad
                self.assertIn("E29", base_rules(d))

    def test_duration_and_seed_must_equal_approved(self):
        d = copy.deepcopy(self.d)
        d["duration_sec"] = 300   # outside the approved 30-240 s
        self.assertIn("E29", base_rules(d))
        d = copy.deepcopy(self.d)
        del d["seed"]
        self.assertIn("E29", base_rules(d))

    def test_cadence_grace_and_end(self):
        cases = {"cadence": lambda s: s[5].update(at=s[5]["at"] - 0.5),
                 "grace": lambda s: [e.update(at=e["at"] + 1) for e in s[:-1]],
                 "stops early": lambda s: s.pop()}
        for name, fn in cases.items():
            with self.subTest(name=name):
                d = copy.deepcopy(self.d)
                fn(d["phases"][0]["schedule"])
                self.assertIn("E29", base_rules(d))

    def test_in_range_tuning_passes(self):
        # Dry run A H4: an approved in-range tuning (tuning.md, bake_preset) keeps E29 green
        for key, ok in (("telegraph_sec", 0.8), ("speed", 450)):
            with self.subTest(key=key):
                d = copy.deepcopy(self.d)
                d["patterns"]["BOLT_Single"][key] = ok
                self.assertNotIn("E29", base_rules(d))
        self.assertEqual(ec.approved_ok(MANIFEST, "OWL-01.cadence", 2.5)[0], True)
        self.assertEqual(ec.approved_ok(MANIFEST, "OWL-01.cadence", 1.0)[0], False)
        self.assertEqual(ec.approved_ok(MANIFEST, "OWL-01.seed", 20261113)[0], False)  # no range: fixed value

    def test_approved_change_in_the_manifest_moves_the_gate(self):
        # A new approved range (GDD revision -> manifest) is the only way to move the bolt outside it.
        m = copy.deepcopy(MANIFEST)
        m["approved_parameters"]["values"]["OWL-01.telegraph_delay"]["max"] = 1.8
        self.b["telegraph_sec"] = 1.6
        self.assertNotIn("E29", base_rules(self.d, manifest=m))
        self.assertIn("E29", base_rules(self.d))

    def test_pattern_needs_an_enabled_feature(self):
        self.b.pop("feature")
        self.assertIn("E29", base_rules(self.d))

    def test_gust_needs_owl02_on(self):
        self.d["patterns"]["GUST_Wing"] = copy.deepcopy(MULTI["patterns"]["GUST_Wing"])
        self.d["patterns"]["GUST_Wing"].update(interruptible_sec=0, gust_strength_by_wing_tier=[1.0])
        msgs = lambda m=None: [w for r, w, _ in ec.check(self.d, manifest=m)[0] if r == "E29"]
        self.assertIn("patterns.GUST_Wing", msgs())
        m = copy.deepcopy(MANIFEST)
        next(f for f in m["features"] if f["feature_id"] == "OWL-02")["default_enabled"] = True
        self.assertNotIn("patterns.GUST_Wing", msgs(m))

    def test_clock_interrupt_needs_com02_on(self):
        self.b["interruptible_sec"] = 0.5
        self.b["interrupt_replays_telegraph"] = True
        self.assertIn("E29", base_rules(self.d))
        m = copy.deepcopy(MANIFEST)
        next(f for f in m["features"] if f["feature_id"] == "COM-02")["default_enabled"] = True
        self.assertNotIn("E29", base_rules(self.d, manifest=m))

    def test_multi_pattern_rules_are_silent_with_one_bolt(self):
        # The one approved bolt has a 2.0 s gap, 98% threat share and no pos_far coverage: E8, E19, E14 rows and
        # E26 would all fire if they applied. They apply only once 2+ patterns are scheduled.
        probs, numbers = ec.check(self.d, manifest=MANIFEST)
        self.assertEqual(probs, [])
        self.assertIn("breather base: 2.0 s", numbers)
        self.assertTrue(any(n.startswith("intensity base: share 98%") for n in numbers), numbers)

    def test_one_phase_needs_no_cue_and_base_is_the_only_single_phase(self):
        self.assertIsNone(self.d["phase_change_cue"])
        self.d["phases"][0]["id"] = "intro"
        self.assertIn("E3", base_rules(self.d))

    def test_three_presets_with_one_bolt_still_need_their_cue(self):
        s = self.sched
        self.d["phases"] = [{"id": i, "start_pct": a, "end_pct": b, "space_rules": [], "altitude_cap_y": None,
                             "schedule": [{"at": e["at"] - a * 0.9, "pattern": "BOLT_Single"} for e in s if a * 0.9 <= e["at"] < b * 0.9]}
                            for i, a, b in (("intro", 0, 25), ("contest", 25, 70), ("desperation", 70, 100))]
        self.assertNotIn("E4", base_rules(self.d))   # one pattern: E4 off
        self.assertIn("E5", base_rules(self.d))      # 2+ phases: one phase_change_cue
        self.d["phase_change_cue"] = "SFX_PhaseChime"
        self.assertEqual(base_rules(self.d), set())

    def test_owl_phase_tests_only_with_phases(self):
        self.assertNotIn("UmbrellaElla.Owl.World.PhaseChangePlaysCue", ec.owl_tests(self.d))
        self.assertEqual(ec.owl_tests(MULTI), ec.OWL_TESTS)
        card = "\n".join(f"{t} PASS" for t in ec.owl_tests(self.d))
        self.assertNotIn("C5", {r for r, _, _ in ec.check_card_text(card, self.d)})
        self.assertIn("C5", {r for r, _, _ in ec.check_card_text(card, MULTI)})

    def test_playtest_accepts_base_phase(self):
        import tempfile
        with tempfile.NamedTemporaryFile("w", suffix=".csv", delete=False) as fh:
            fh.write("session,event,phase,pattern_id,explained,t_run_s,build\n"
                     "s1,hit,base,BOLT_Single,y,12.5,abc1234\ns1,hit,boss,BOLT_Single,y,13,abc1234\n")
        try:
            got = [(r, w) for r, w, _ in ec.check_playtest(self.d, [fh.name])[0]]
        finally:
            os.unlink(fh.name)
        self.assertEqual([r for r, _ in got], ["L5"])
        self.assertTrue(got[0][1].endswith(":3"))

    # Envelope (V1-V2): card 0.13's measured line against the tuning file (cm/s, GDD 1.3 §5A)
    GOOD_ENV = "FEEL_ENVELOPE accel_f=12 fall=650 rise_intact=300 rise_critical=300 blend_f=12 commit=abc1234"

    def test_envelope_matching_tuning_passes(self):
        self.assertEqual(ec.check_envelope(self.GOOD_ENV, TUNING), [])
        self.assertEqual(ec.main(["--data", DATA, "--envelope", self.GOOD_ENV]), 0)

    def test_envelope_lift_loss_fails(self):
        # A game that loses lift with wear (0.7 at critical) is wrong under GDD 1.3 DEC-05.
        bad = self.GOOD_ENV.replace("rise_critical=300", "rise_critical=210")
        self.assertEqual([(r, f) for r, f, _ in ec.check_envelope(bad, TUNING)], [("V2", "rise_critical")])
        self.assertEqual(ec.main(["--data", DATA, "--envelope", bad]), 1)

    def test_envelope_off_by_more_than_5_percent_fails(self):
        self.assertEqual(ec.check_envelope(self.GOOD_ENV.replace("fall=650", "fall=680"), TUNING), [])
        bad = self.GOOD_ENV.replace("fall=650", "fall=700")
        self.assertEqual([(r, f) for r, f, _ in ec.check_envelope(bad, TUNING)], [("V2", "fall")])

    def test_envelope_frames_use_2_frame_tolerance(self):
        # 350 / 1800 x 60 = 11.7 frames.
        self.assertEqual(ec.check_envelope(self.GOOD_ENV.replace("accel_f=12", "accel_f=13.6"), TUNING), [])
        self.assertEqual(len(ec.check_envelope(self.GOOD_ENV.replace("accel_f=12", "accel_f=14"), TUNING)), 1)

    def test_envelope_missing_field_fails(self):
        self.assertIn("V1", {r for r, _, _ in ec.check_envelope(self.GOOD_ENV.replace("blend_f=12 ", ""), TUNING)})
        self.assertIn("V1", {r for r, _, _ in ec.check_envelope("all good", TUNING)})
        old = "FEEL_ENVELOPE closed_accel_f=6 open_accel_f=24 fall=70 rise_intact=12 rise_critical=8.4 blend_f=12"
        self.assertIn("V1", {r for r, _, _ in ec.check_envelope(old, TUNING)})

    def test_main_exit_code(self):
        self.assertEqual(ec.main(["--data", DATA, "--md", MD, "--manifest", MANIFEST_PATH]), 0)
        self.assertEqual(ec.main(["--data", MULTI_PATH, "--md", MD, "--manifest", MANIFEST_PATH]), 1)

    def test_stale_doc_fails(self):
        with open(MD, encoding="utf-8") as fh:
            md = fh.read()
        self.assertEqual(base_rules(self.d, md), set())
        self.b["recovery_sec"] = 1.5
        self.assertEqual(base_rules(self.d, md), {"E18"})

    def test_cli_tuning_flag(self):
        self.assertEqual(ec.main(["--data", DATA, "--md", MD, "--tuning", TUNING_PATH, "--manifest", MANIFEST_PATH]), 0)


class EncounterCheckTests(unittest.TestCase):
    def setUp(self):
        self.d = copy.deepcopy(MULTI)
        self.p = self.d["patterns"]
        self.ph = {ph["id"]: ph for ph in self.d["phases"]}

    def assertCaught(self, rule, tuning=None):
        self.assertIn(rule, rules(self.d, tuning=tuning))

    def contest(self):
        return self.ph["contest"]["schedule"]

    # passing case
    def test_fixture_passes_with_its_features_on(self):
        self.assertEqual(rules(self.d), set())

    # E1 telegraph
    def test_short_telegraph_fails(self):
        self.p["BOLT_Fan3"]["telegraph_sec"] = 0.3
        self.assertCaught("E1")

    def test_telegraph_at_threshold_passes(self):
        self.p["BOLT_Fan3"]["telegraph_sec"] = 0.4
        self.assertNotIn("E1", rules(self.d))

    def test_sound_only_tell_fails(self):
        self.p["GUST_Wing"]["tell"] = {"pose": "", "sound": "SFX_GustWindup", "vfx": ""}
        self.assertCaught("E1")

    # E2 stages
    def test_active_shorter_than_volleys_fails(self):
        self.p["BOLT_Aimed2"]["active_sec"] = 0.5
        self.assertCaught("E2")

    def test_negative_recovery_fails(self):
        self.p["GUST_Wing"]["recovery_sec"] = -1
        self.assertCaught("E2")

    # E3 phases
    def test_phase_gap_fails(self):
        self.ph["contest"]["start_pct"] = 30
        self.assertCaught("E3")

    def test_long_desperation_fails(self):
        self.ph["contest"]["end_pct"] = 60
        self.ph["desperation"]["start_pct"] = 60
        self.assertCaught("E3")

    def test_unknown_pattern_fails(self):
        self.ph["intro"]["schedule"].append({"at": 36, "pattern": "BOLT_Nope"})
        self.assertCaught("E3")

    # E4 distinct
    def test_phase_same_as_before_fails(self):
        self.ph["desperation"]["schedule"] = copy.deepcopy(self.ph["contest"]["schedule"])
        self.ph["desperation"]["space_rules"] = []
        self.ph["desperation"]["altitude_cap_y"] = None
        self.assertCaught("E4")

    def test_space_rule_alone_makes_phase_distinct(self):
        self.ph["desperation"]["schedule"] = copy.deepcopy(self.ph["contest"]["schedule"])[:6]
        self.assertNotIn("E4", rules(self.d))

    # E5 cue
    def test_per_phase_cue_fails(self):
        self.ph["contest"]["cue"] = "SFX_Other"
        self.assertCaught("E5")

    def test_missing_cue_fails(self):
        self.d["phase_change_cue"] = ""
        self.assertCaught("E5")

    # E6 intro
    def test_intro_spread_fails(self):
        self.ph["intro"]["schedule"][1]["pattern"] = "BOLT_Fan3"
        self.assertCaught("E6")

    def test_intro_two_gusts_fails(self):
        self.ph["intro"]["schedule"][2]["pattern"] = "GUST_Wing"
        self.assertCaught("E6")

    def test_intro_overlap_fails(self):
        self.ph["intro"]["schedule"][1]["at"] = 4
        self.assertCaught("E6")

    # E7 first use alone
    def test_first_use_overlap_fails(self):
        self.ph["contest"]["schedule"][0] = {"at": 16, "pattern": "BOLT_Fan3"}
        self.assertCaught("E7")

    # E8 breather
    def test_no_breather_fails(self):
        self.ph["contest"]["schedule"] = [{"at": t, "pattern": "BOLT_Single"} for t in range(0, 66, 3)]
        self.ph["contest"]["schedule"][0] = {"at": 0, "pattern": "BOLT_Fan3"}
        self.assertCaught("E8")

    # E9 colour
    def test_amber_on_gust_fails(self):
        self.p["GUST_Wing"]["color"] = "amber"
        self.assertCaught("E9")

    def test_red_on_bolt_fails(self):
        self.p["BOLT_Single"]["color"] = "red"
        self.assertCaught("E9")

    # E10 readable
    def test_projectile_not_on_top_fails(self):
        self.p["ARC_Return"]["draw_on_top"] = False
        self.assertCaught("E10")

    # E11 spread fairness
    def test_lone_bullet_fails(self):
        self.p["BOLT_Fan3"]["angles_deg"] = [-6, 0, 6, 40]
        self.assertCaught("E11")

    def test_spread_without_stagger_fails(self):
        self.p["BOLT_Fan3"]["spawn_offset_sec"] = 0
        self.assertCaught("E11")

    def test_aimed_odd_spread_fails(self):
        self.p["BOLT_Aimed2"]["angles_deg"] = [-10, 0, 10]
        self.assertCaught("E11")

    def test_aimed_odd_spread_with_reason_passes_e11(self):
        self.p["BOLT_Aimed2"]["angles_deg"] = [-10, 0, 10]
        self.p["BOLT_Aimed2"]["odd_count_reason"] = "centre bolt forces a move; decision row D-x"
        self.assertNotIn("E11", rules(self.d))

    def test_fixed_seed_volleys_fail(self):
        self.p["BOLT_Fan3"]["seed_angle_step_deg"] = 0
        self.assertCaught("E11")

    # E12 origin locked
    def test_origin_not_locked_fails(self):
        self.p["BOLT_Single"]["origin_locked_during_telegraph"] = False
        self.assertCaught("E12")

    # E13 safe path
    def test_wall_of_bolts_fails(self):
        self.p["BOLT_Fan3"]["angles_deg"] = list(range(-40, 41, 2))
        self.assertCaught("E13")

    def fast(self):
        """Tuning with a 4x faster hero, so a test isolates drift or cap logic from travel time."""
        t = copy.deepcopy(MULTI_TUNING)
        for k in ("move_speed", "ascent_speed", "max_fall_speed"):
            t["movement"][k] *= 4.0
        return t

    def wall(self, pid="BOLT_Fan3", angles=range(-60, 61, 2)):
        """A dense one-volley fan: no hero-sized gap between bolts."""
        self.p[pid].update({"angles_deg": list(angles), "spawn_offset_sec": 0.001, "volleys": 1,
                            "active_sec": 1.0, "seed_angle_step_deg": 0, "base_angle_deg": 180})

    def test_safe_only_at_one_drift_end_fails(self):
        # A +-60 deg fan covers every hero spot when the owl is at y=700, but leaves the top corner when it is at y=150.
        self.wall()
        self.ph["desperation"].update({"altitude_cap_y": None, "space_rules": ["no_recovery_ledge"]})
        self.d["arena"]["owl_drift_y"] = [150, 150]
        self.assertNotIn("E13", rules(self.d, tuning=self.fast()))
        self.d["arena"]["owl_drift_y"] = [150, 700]
        self.assertIn("E13", rules(self.d, tuning=self.fast()))

    def test_altitude_cap_shrinks_safe_space(self):
        # A fan that sweeps everything below the owl. Safe above it; not once desperation caps altitude below it.
        self.wall(angles=range(0, 81, 2))  # positive offsets turn downward from base 180
        self.d["arena"]["owl_drift_y"] = [700, 700]
        self.ph["desperation"]["altitude_cap_y"] = None
        self.ph["desperation"]["space_rules"] = ["no_recovery_ledge"]
        self.assertNotIn("E13", rules(self.d, tuning=self.fast()))
        self.ph["desperation"]["altitude_cap_y"] = 650
        self.ph["desperation"]["space_rules"] = ["altitude_cap"]
        self.assertIn("E13", rules(self.d, tuning=self.fast()))

    # E14 coverage
    def test_empty_coverage_row_fails(self):
        self.p["GUST_Wing"]["covers"] = ["ctl_rise"]
        self.assertIn("E14", {r for r, _, _ in ec.check(self.d, None, MULTI_TUNING, {"gust"}, MULTI_MANIFEST)[0]})

    # The gust is P1: its coverage row applies only once the Gust test-map row is merged (dry run 1, H1)
    def test_bolts_only_encounter_passes_before_gust_merges(self):
        self.p["GUST_Wing"]["covers"] = ["ctl_rise"]
        self.assertNotIn("E14", {r for r, _, _ in ec.check(self.d, None, MULTI_TUNING, set(), MULTI_MANIFEST)[0]})

    def test_merged_features_reads_test_map(self):
        import tempfile
        with tempfile.NamedTemporaryFile("w", suffix=".md", delete=False) as fh:
            fh.write("| MVP | Required tests | Card | Status |\n|---|---|---|---|\n"
                     "| Gust (P1) | `UmbrellaElla.Gust.World.X` | #40 | merged |\n| Wear (P1) | `UmbrellaElla.Y.Z` | | planned |\n")
        try:
            self.assertEqual(ec.merged_features(fh.name), {"gust"})
        finally:
            os.unlink(fh.name)

    # E28: an empty dump proves nothing (dry run 2, H3)
    def test_empty_dump_fails(self):
        self.assertEqual(rules({"patterns": {}, "phases": []}), {"E28"})

    def test_late_only_coverage_fails(self):
        for k in ("BOLT_Fan3", "BOLT_Aimed2"):
            self.p[k]["covers"] = [c for c in self.p[k]["covers"] if c != "pos_far"]
        self.p["ARC_Return"]["covers"].append("pos_far")
        self.assertCaught("E14")

    def test_false_position_claim_fails(self):
        # Fan fired level from the low drift end never reaches the top third.
        self.p["BOLT_Fan3"]["covers"].append("pos_high")
        self.p["BOLT_Fan3"]["base_angle_deg"] = 200
        self.assertCaught("E14")

    # E15 gust
    def test_gust_without_avoid_lane_fails(self):
        self.p["GUST_Wing"]["zone"] = {"x0": 300, "x1": 900, "y0": 100, "y1": 990}
        self.assertCaught("E15")

    # E16 end event
    def test_end_event_without_card_fails(self):
        self.d["end_event"]["survived_card"] = ""
        self.assertCaught("E16")

    def test_end_quiet_short_fails(self):
        self.d["end_event"]["quiet_sec"] = 2
        self.assertCaught("E16")

    # E17 arena
    def test_owl_on_left_half_fails(self):
        self.d["arena"]["owl_zone"]["x0"] = 900
        self.assertCaught("E17")

    # E1 layered tell for ranged attacks
    def test_bolt_without_sound_fails(self):
        self.p["BOLT_Fan3"]["tell"]["sound"] = ""
        self.assertCaught("E1")

    def test_arc_without_vfx_fails(self):
        self.p["ARC_Return"]["tell"]["vfx"] = ""
        self.assertCaught("E1")

    def test_gust_with_pose_only_passes_e1(self):
        self.p["GUST_Wing"]["tell"] = {"pose": "Owl_WingRaise", "sound": "", "vfx": ""}
        self.assertNotIn("E1", rules(self.d))

    # E16: the story clue is optional (narrative DEFERRED, NAR-01, GDD 1.3 §1)
    def test_end_event_without_clue_passes(self):
        self.d["end_event"]["clue"] = "  "
        self.assertNotIn("E16", rules(self.d))

    # E19 intensity
    def test_constant_pressure_fails(self):
        self.ph["contest"]["schedule"] = [{"at": t, "pattern": "BOLT_Single"} for t in range(0, 66, 3)]
        self.assertCaught("E19")

    def test_desperation_wall_fails(self):
        self.ph["desperation"]["schedule"] += [{"at": t, "pattern": "BOLT_Single"} for t in (6, 24, 26, 41, 43)]
        self.assertCaught("E19")

    def test_intro_denser_than_contest_fails(self):
        self.ph["contest"]["schedule"] = [{"at": 2, "pattern": "BOLT_Fan3"}, {"at": 30, "pattern": "BOLT_Aimed2"}]
        self.assertCaught("E19")

    def test_peaks_without_breather_fail(self):
        for e in self.ph["desperation"]["schedule"]:
            if e["at"] == 19:
                e["at"] = 18
        self.assertCaught("E19")

    def test_peaks_with_breather_pass(self):
        self.assertNotIn("E19", rules(self.d))

    # E20 corner camping
    def test_static_shapes_only_lets_hero_camp(self):
        self.ph["contest"]["schedule"] = [e for e in self.contest() if not self.p[e["pattern"]].get("aimed")]
        self.assertCaught("E20")

    def test_aimed_bolt_hits_every_still_spot(self):
        self.assertNotIn("E20", rules(self.d))

    # E21 layering
    def test_contest_without_layered_cluster_fails(self):
        self.ph["contest"]["schedule"] = [e for e in self.contest() if not (e["at"] == 48 and e["pattern"] == "BOLT_Single")]
        self.assertCaught("E21")

    # E22 tuning link
    def test_copied_speed_fails(self):
        self.d["arena"]["hero_speed_x"] = 300
        self.assertCaught("E22")

    def test_missing_tuning_source_fails(self):
        del self.d["arena"]["tuning_source"]
        self.assertEqual({r for r, _, _ in ec.check(self.d, manifest=MULTI_MANIFEST)[0]}, {"E22"})

    def test_tuning_missing_field_fails(self):
        t = copy.deepcopy(MULTI_TUNING)
        del t["movement"]["ascent_speed"]
        self.assertCaught("E22", tuning=t)

    def test_big_hurtbox_fails(self):
        t = copy.deepcopy(MULTI_TUNING)
        t["forgiveness"]["player_hurtbox_cm"] = {"w": 79.2, "h": 119.9}  # 56% of the body art area
        self.assertCaught("E22", tuning=t)

    def test_collider_is_data_not_sprite(self):
        """Dry run A H5: changing the body art box never changes the sim's collider (GDD 1.3 7A, 7C)."""
        a = ec.derive(self.d["arena"], MULTI_TUNING)
        t = copy.deepcopy(MULTI_TUNING)
        t["threat_spacing"]["player_body_w_pct_w"] *= 1.1
        t["threat_spacing"]["player_body_h_pct_h"] *= 1.1
        b = ec.derive(self.d["arena"], t)
        self.assertEqual(a["hero_box"], b["hero_box"])
        self.assertEqual(a["bolt_radius"], b["bolt_radius"])
        self.assertEqual(a["hero_box"], {"w": 63.36, "h": 95.904})
        arena = dict(self.d["arena"], bolt_core_radius=30)   # bigger bolt art, same collider
        self.assertEqual(ec.derive(arena, MULTI_TUNING)["bolt_radius"], 14.0)
        live = ec.derive(BASE["arena"], TUNING)   # the live feel.json collider
        self.assertEqual((live["hero_box"], live["bolt_radius"]), ({"w": 52.8, "h": 79.9}, 12.0))
        # broken on purpose: a tuning file with no collider data is refused
        t = copy.deepcopy(MULTI_TUNING)
        del t["forgiveness"]["player_hurtbox_cm"]
        self.assertCaught("E22", tuning=t)

    def test_sim_uses_tuning_speeds(self):
        # The hero starts at the aim point, so the speeds matter: the real data passes at real speeds,
        # and fails once the tuning file says the hero is 10x slower.
        self.assertNotIn("E13", rules(self.d, tuning=MULTI_TUNING))
        t = copy.deepcopy(MULTI_TUNING)
        for k in ("move_speed", "ascent_speed", "max_fall_speed"):
            t["movement"][k] /= 10.0
        self.assertCaught("E13", tuning=t)

    # E23 owl hitbox
    def test_small_owl_hitbox_fails(self):
        self.d["arena"]["owl_hitbox"] = {"w": 200, "h": 300}
        self.assertCaught("E23")

    # E24 midpoint turn
    def test_no_new_pattern_after_midpoint_fails(self):
        for e in self.contest():
            if e["pattern"] == "BOLT_Aimed2":
                e["at"] = 20
        self.assertCaught("E24")

if __name__ == "__main__":
    unittest.main()
