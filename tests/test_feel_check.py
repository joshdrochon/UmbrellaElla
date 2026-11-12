"""GDD 1.3 frozen data (tests/fixtures/gdd13): these rules model the 1.3 timer arena; GDD SH1.0 data is checked in its own tests. Tests for tools/feel_check.py. Every rule is shown to pass a good input and fail an input
broken on purpose. Where a rule has a number, the good twin sits on the limit and the broken
one just past it, so loosening a limit breaks a test.

Fixtures: tests/fixtures/feel/ (good.json is a frozen copy of pipeline/feel/feel.json, so tuning
the live file never changes what these tests prove). The live file is also checked, last."""
import copy
import io
import json
import os
import sys
import unittest
from contextlib import redirect_stdout

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, os.path.join(ROOT, "tools"))
import feel_check  # noqa: E402

FIX = os.path.join(HERE, "fixtures", "feel")
with open(os.path.join(ROOT, "tests", "fixtures", "gdd13", "docs", "feature-manifest.json"), encoding="utf-8") as _fh:
    MANIFEST = json.load(_fh)


def manifest_with(**on):
    """Copy of the live manifest with some features switched on (keys use '-': pass them as **{"SURV-04": True})."""
    m = copy.deepcopy(MANIFEST)
    for f in m["features"]:
        if f["feature_id"] in on:
            f["default_enabled"] = on[f["feature_id"]]
    return m
with open(os.path.join(FIX, "good.json"), encoding="utf-8") as _fh:
    GOOD = json.load(_fh)


def ev(d, eid):
    return next(e for e in d["events"] if e["id"] == eid)


def cue(d, eid, kind):
    return next(c for c in ev(d, eid)["cues"] if c["kind"] == kind)


def setter(fn):
    """Wrap a mutation so it runs on a deep copy of the good fixture."""
    def run():
        d = copy.deepcopy(GOOD)
        fn(d)
        return d
    return run


def put(path, value):
    def fn(d):
        node = d
        for k in path[:-1]:
            node = node[k]
        node[path[-1]] = value
    return fn


def put_cue(eid, kind, key, value):
    def fn(d):
        cue(d, eid, kind)[key] = value
    return fn


def add_cue(eid, c):
    def fn(d):
        ev(d, eid)["cues"].append(c)
    return fn


SHAKE = {"rank": 3, "kind": "shake", "flag": "bExtraShake", "power": 1.0, "duration_s": 0.1,
         "amp_pct_h": 1.0, "direction": "away_from_source", "decay": "spring"}
RUMBLE = {"rank": 3, "kind": "rumble", "flag": "bExtraRumble", "power": 1.0, "duration_s": 0.1, "applies_if": "gamepad"}
STOP = {"rank": 3, "kind": "hitstop", "flag": "bExtraStop", "power": 1.0, "frames": 2}

# name -> (rule, good mutation, broken mutation). The good mutation sits on the limit.
CASES = {
    "hitstop_cap": ("hitstop", put_cue("player_hit", "hitstop", "frames", 6), put_cue("player_hit", "hitstop", "frames", 7)),
    "hitstop_bolt_hit_cap": ("hitstop", put_cue("bolt_hit_clock", "hitstop", "frames", 3), put_cue("bolt_hit_clock", "hitstop", "frames", 4)),
    "hitstop_bolt_hit_cooldown": ("hitstop", put_cue("bolt_hit_clock", "hitstop", "cooldown_s", 0.3), put_cue("bolt_hit_clock", "hitstop", "cooldown_s", 0.1)),
    "hitstop_never_on_fire": ("hitstop", add_cue("player_hit", dict(STOP)), add_cue("bolt_fire", dict(STOP))),
    "hitstop_stacking": ("hitstop", put(["global", "hitstop_stacking"], "max"), put(["global", "hitstop_stacking"], "sum")),
    "hitstop_skip_if_slowed": ("hitstop", put(["global", "hitstop_skip_if_slowed"], True), put(["global", "hitstop_skip_if_slowed"], False)),
    "hitstop_input_buffer": ("hitstop", put(["global", "hitstop_input_buffer_s"], 0.13), put(["global", "hitstop_input_buffer_s"], 0.2)),
    "shake_duration": ("shake", put_cue("player_hit", "shake", "duration_s", 0.2), put_cue("player_hit", "shake", "duration_s", 0.25)),
    "shake_amplitude": ("shake", put_cue("player_hit", "shake", "amp_pct_h", 2.5), put_cue("player_hit", "shake", "amp_pct_h", 2.6)),
    "shake_only_big_events": ("shake", add_cue("end_trigger", dict(SHAKE)), add_cue("bolt_hit_body", dict(SHAKE))),
    "shake_direction_enum": ("shake", put_cue("end_trigger", "shake", "direction", "away_from_source"), put_cue("player_hit", "shake", "direction", "random")),
    "shake_no_old_bool": ("shake", put_cue("player_hit", "shake", "direction", "toward_owl"), put_cue("player_hit", "shake", "directional", True)),
    "hitstop_hard_cut": ("hitstop", put_cue("player_hit", "hitstop", "frames", 5), put_cue("player_hit", "hitstop", "fade_out_ms", 30)),
    "tell_pose_hold": ("tell", put_cue("owl_tell_bolts", "pose", "hold_s", 0.75), put_cue("owl_tell_bolts", "pose", "hold_s", 0.74)),
    "tell_tween_hold": ("tell", put_cue("owl_tell_arc", "tween", "duration_s", 0.8), put_cue("owl_tell_arc", "tween", "duration_s", 0.5)),
    # 2.5 x (14.8 x 0.6) = 22.2: the good twin sits on it, the broken one just under.
    "spacing_bolt_gap": ("spacing", put(["threat_spacing", "bolt_gap_min_pct_h"], 22.2), put(["threat_spacing", "bolt_gap_min_pct_h"], 22.1)),
    # GDD 1.3: (650 / 980) / 2 s ramp + d / (650 / 900 x 100) <= 0.75 s tell -> d <= 30.2.
    "spacing_bolt_dodge": ("spacing", put(["threat_spacing", "bolt_dodge_max_pct_h"], 30.2), put(["threat_spacing", "bolt_dodge_max_pct_h"], 30.3)),
    "spacing_arena": ("spacing", put(["threat_spacing", "arena_map"], "L_Graybox"), put(["threat_spacing", "arena_map"], "L_Main")),
    "spacing_arena_patterns": ("spacing", put(["threat_spacing", "arena_patterns"], ["BOLT_Single"]),
                               put(["threat_spacing", "arena_patterns"], ["GUST_Wing"])),
    "spacing_no_gust_when_owl02_off": ("spacing", put(["threat_spacing", "arena_patterns"], ["BOLT_Single"]),
                                       put(["threat_spacing", "arena_patterns"], ["BOLT_Single", "GUST_Wing"])),
    "shake_spring": ("shake", put_cue("player_hit", "shake", "decay", "spring"), put_cue("player_hit", "shake", "decay", "linear")),
    "shake_off_option": ("shake", put(["global", "shake_off_option"], True), put(["global", "shake_off_option"], False)),
    "nudge_cap": ("shake", put_cue("bolt_fire", "nudge", "px", 2), put_cue("bolt_fire", "nudge", "px", 3)),
    "squash_recover": ("squash", put_cue("umbrella_open", "squash", "recover_s", 0.25), put_cue("umbrella_open", "squash", "recover_s", 0.3)),
    "squash_peak": ("squash", put_cue("umbrella_open", "squash", "scale", [1.4, 0.85]), put_cue("umbrella_open", "squash", "scale", [1.5, 0.85])),
    "squash_render_only": ("squash", put_cue("umbrella_open", "squash", "target", "render_only"), put_cue("umbrella_open", "squash", "target", "capsule")),
    "flash_rate": ("flash", put_cue("player_hit", "flash", "max_rate_hz", 3), put_cue("player_hit", "flash", "max_rate_hz", 4)),
    "ease_named_curve": ("ease", put_cue("umbrella_open", "squash", "ease", "spring"), put_cue("umbrella_open", "squash", "ease", "linear")),
    "ease_no_linear_curve": ("ease", put(["easing", "curves"], ["ease_out_quad", "ease_out_back", "ease_in_out_sine", "spring"]),
                             put(["easing", "curves"], ["ease_out_quad", "ease_out_back", "ease_in_out_sine", "spring", "linear"])),
    "event_flag": ("flag", put_cue("umbrella_open", "sound", "flag", "bOpenSound"), lambda d: ev(d, "umbrella_open").pop("flag")),
    "cue_flag": ("flag", put_cue("umbrella_open", "sound", "flag", "bOpenSound"), put_cue("umbrella_open", "sound", "flag", "")),
    "flag_unique": ("flag", put_cue("umbrella_close", "sound", "flag", "bCloseSound"), put_cue("umbrella_close", "sound", "flag", "bOpenSound")),
    "power_range": ("flag", put_cue("umbrella_open", "sound", "power", 1.0), put_cue("umbrella_open", "sound", "power", 1.5)),
    "mvp_sound": ("cues", put_cue("umbrella_open", "sound", "rank", 2), put_cue("umbrella_open", "sound", "rank", 3)),
    "mvp_visual": ("cues", put_cue("bolt_hit_body", "particles", "rank", 1),
                   lambda d: [c.update(rank=3) for c in ev(d, "bolt_hit_body")["cues"] if c["kind"] != "sound"]),
    "owl_hit_reaction": ("cues", put_cue("bolt_hit_wing", "flash", "frames", 1),
                         lambda d: ev(d, "bolt_hit_wing").update(cues=[c for c in ev(d, "bolt_hit_wing")["cues"] if c["kind"] != "flash"])),
    # owl_tell_arc: a shorter bolt tell would also break the dodge-spacing rule.
    "tell_min": ("tell", put(["events", 13, "telegraph_s"], 0.35), put(["events", 13, "telegraph_s"], 0.3)),
    "tell_sound": ("tell", put_cue("owl_tell_bolts", "sound", "rank", 1), put_cue("owl_tell_bolts", "sound", "rank", 2)),
    "vfx_known_system": ("vfx", put_cue("umbrella_open", "particles", "system", "NS_Puff"), put_cue("umbrella_open", "particles", "system", "NS_Nope")),
    "vfx_sprite_renderer": ("vfx", put(["vfx", "systems", "NS_Puff", "renderer"], "sprite"), put(["vfx", "systems", "NS_Puff", "renderer"], "ribbon")),
    "vfx_fixed_bounds": ("vfx", put(["vfx", "systems", "NS_Puff", "fixed_bounds"], True), put(["vfx", "systems", "NS_Puff", "fixed_bounds"], False)),
    "vfx_effect_type": ("vfx", put(["vfx", "systems", "NS_Puff", "effect_type"], "cosmetic"), put(["vfx", "systems", "NS_Puff", "effect_type"], "")),
    "vfx_pooled_frequent": ("vfx", put(["vfx", "systems", "NS_Muzzle", "pooled"], True), put(["vfx", "systems", "NS_Muzzle", "pooled"], False)),
    "vfx_hit_spark_family": ("vfx", put_cue("bolt_hit_body", "particles", "system", "NS_HitSpark"), put_cue("bolt_hit_body", "particles", "system", "NS_Puff")),
    "vfx_gameplay_type_sparks": ("vfx", put(["vfx", "systems", "NS_HitSpark_Body", "effect_type"], "gameplay"),
                                 put(["vfx", "systems", "NS_HitSpark_Body", "effect_type"], "cosmetic")),
    "vfx_gameplay_type_wind": ("vfx", put(["vfx", "systems", "NS_Puff", "effect_type"], "cosmetic"),
                               put(["vfx", "systems", "NS_WindLines", "effect_type"], "cosmetic")),
    "owl_overlay_per_part": ("owl", put_cue("owl_condition_step", "tween", "rank", 2),
                             lambda d: ev(d, "owl_condition_step").update(
                                 cues=[c for c in ev(d, "owl_condition_step")["cues"] if c.get("part") != "wing"])),
    "owl_overlay_mvp_rank": ("owl", lambda d: None,
                             lambda d: [c.update(rank=3) for c in ev(d, "owl_condition_step")["cues"] if c.get("part") == "clock"]),
    "owl_overlay_steps": ("owl", lambda d: [c.update(steps=5) for c in ev(d, "owl_condition_step")["cues"] if c["kind"] == "overlay"],
                          lambda d: [c.update(steps=1) for c in ev(d, "owl_condition_step")["cues"] if c["kind"] == "overlay"]),
    "owl_overlay_persists": ("owl", lambda d: None,
                             lambda d: [c.update(persist=False) for c in ev(d, "owl_condition_step")["cues"] if c["kind"] == "overlay"]),
    "owl_overlay_part": ("owl", lambda d: None,
                         lambda d: [c.update(part="body") for c in ev(d, "owl_condition_step")["cues"] if c.get("part") == "wing"]),
    "owl_hits_per_step": ("owl", put(["events", 15, "hits_per_step", "clock"], 1), put(["events", 15, "hits_per_step", "clock"], 0)),
    "owl_hits_per_step_both": ("owl", put(["events", 15, "hits_per_step", "wing"], 20), lambda d: ev(d, "owl_condition_step")["hits_per_step"].pop("wing")),
    "vfx_frequent_count": ("vfx", put_cue("bolt_fire", "particles", "count", 8), put_cue("bolt_fire", "particles", "count", 9)),
    "movement_range": ("movement", put(["movement", "stop_s"], 0.80), put(["movement", "stop_s"], 0.85)),
    "movement_no_fast_fall": ("movement", lambda d: None, put(["movement", "fast_fall_mult"], 1.4)),   # GDD 1.3 5A: REJECTED
    "movement_no_gravity_mult": ("movement", lambda d: None, put(["movement", "apex_gravity_mult"], 0.5)),   # GDD 1.3 5A
    "movement_old_pct_key": ("movement", lambda d: None, put(["movement", "open_rise_pct_h"], 12)),
    # SURV-04 off (DEC-05): no lift loss from wear.
    "movement_lift_tiers": ("gdd", put(["movement", "lift_by_tier", "critical"], 1.0), put(["movement", "lift_by_tier", "critical"], 0.7)),
    # GDD 1.3 section 5A start values, read from the manifest approved_parameters.
    # Dry run A H4: the start is provisional tuning; any in-range value passes (tuning.md bakes one), outside fails.
    "gdd_move_speed_tuned": ("gdd", put(["movement", "move_speed"], 375), put(["movement", "move_speed"], 140)),
    "gdd_move_speed_range": ("gdd", put(["movement", "move_speed"], 350), put(["movement", "move_speed"], 700)),
    "gdd_ascent_speed": ("gdd", put(["movement", "ascent_speed"], 300), put(["movement", "ascent_speed"], 108)),
    "gdd_max_fall": ("gdd", put(["movement", "max_fall_speed"], 650), lambda d: d["movement"].pop("max_fall_speed")),
    "gdd_iframes": ("gdd", put(["forgiveness", "iframes_s"], 1.2), put(["forgiveness", "iframes_s"], 2.5)),
    "gdd_bolt_tell": ("gdd", put(["events", 11, "telegraph_s"], 0.7), put(["events", 11, "telegraph_s"], 1.6)),
    "required_shield_catch": ("required", lambda d: None,
                              lambda d: d.update(events=[e for e in d["events"] if e["id"] != "shield_catch"])),
    "required_shield_heal": ("required", lambda d: None,
                             lambda d: d.update(events=[e for e in d["events"] if e["id"] != "shield_heal"])),
    "forgiveness_buffer": ("forgiveness", put(["forgiveness", "toggle_buffer_s"], 0.13), put(["forgiveness", "toggle_buffer_s"], 0.2)),
    # Dry run A H5: the collider is fixed data; missing it fails, and art that no longer lines up with it fails
    # the alignment check (fix the art), while the collider value itself never follows the art.
    "collider_present": ("forgiveness", lambda d: None, lambda d: d["forgiveness"].pop("player_hurtbox_cm")),
    "collider_bolt_present": ("forgiveness", lambda d: None, lambda d: d["forgiveness"].pop("bolt_hitbox_radius_cm")),
    "collider_alignment": ("spacing", lambda d: None, put(["threat_spacing", "player_body_h_pct_h"], 30)),
    # Dry run A M2/M3: rejected or off events are optional; the clock-hit cue is P0
    "optional_manual_fire": ("required", lambda d: d.update(events=[e for e in d["events"] if e["id"] not in
                             ("bolt_fire_manual", "bolt_hit_wing", "owl_condition_step")]),
                             lambda d: d.update(events=[e for e in d["events"] if e["id"] != "bolt_hit_clock"])),
    "clock_hit_is_mvp": ("required", lambda d: None,
                         lambda d: next(e for e in d["events"] if e["id"] == "bolt_hit_clock").update(mvp=False)),
    "forgiveness_hurtbox": ("forgiveness", put(["forgiveness", "player_hurtbox_ratio"], 0.65), put(["forgiveness", "player_hurtbox_ratio"], 0.8)),
    "forgiveness_projectile": ("forgiveness", put(["forgiveness", "projectile_hitbox_ratio"], 0.85), put(["forgiveness", "projectile_hitbox_ratio"], 0.9)),
    "latency_target": ("latency", put(["latency", "input_to_photon_target_ms"], 67), put(["latency", "input_to_photon_target_ms"], 80)),
    "latency_fail_line": ("latency", put(["latency", "input_to_photon_fail_ms"], 100), put(["latency", "input_to_photon_fail_ms"], 120)),
    "latency_game_side": ("latency", put(["latency", "game_side_input_frames"], 1), put(["latency", "game_side_input_frames"], 2)),
    "required_event": ("required", lambda d: None,
                       lambda d: d.update(events=[e for e in d["events"] if e["id"] != "shield_heal"])),
    "schema_section": ("schema", lambda d: None, lambda d: d.pop("vfx")),
    "spring_drag_range": ("shake", put(["global", "spring_drag"], 0.5), put(["global", "spring_drag"], 0.55)),
    "spring_elasticity_range": ("shake", put(["global", "spring_elasticity"], 0.6), put(["global", "spring_elasticity"], 0.65)),
    # 0.1 / 0.1 is in range but still at 0.59 of the amplitude in the last 3 frames of a 0.2 s shake.
    "spring_settles": ("shake", lambda d: d["global"].update(spring_drag=0.3, spring_elasticity=0.2),
                       lambda d: d["global"].update(spring_drag=0.1, spring_elasticity=0.1)),
    "spring_missing": ("shake", lambda d: None, lambda d: d["global"].pop("spring_drag")),
    "squash_scale_by": ("squash", put_cue("umbrella_close", "squash", "scale_by", "none"), put_cue("umbrella_close", "squash", "scale_by", "speed")),
    "rumble_events": ("rumble", add_cue("tier_critical", dict(RUMBLE)), add_cue("bolt_hit_body", dict(RUMBLE))),
    "rumble_gamepad_only": ("rumble", put_cue("player_hit", "rumble", "applies_if", "gamepad"), put_cue("player_hit", "rumble", "applies_if", "any")),
    "rumble_duration": ("rumble", put_cue("player_hit", "rumble", "duration_s", 0.2), put_cue("player_hit", "rumble", "duration_s", 0.25)),
}


class FeelRuleTests(unittest.TestCase):
    def test_good_fixture_passes(self):
        self.assertEqual(feel_check.check(GOOD, MANIFEST), [])

    def test_every_rule_passes_good_and_fails_broken(self):
        for name, (rule, good, bad) in CASES.items():
            with self.subTest(name=name):
                ok = feel_check.check(setter(good)(), MANIFEST)
                self.assertEqual(ok, [], f"{name}: good twin should pass")
                broken = feel_check.check(setter(bad)(), MANIFEST)
                self.assertIn(rule, [r for r, _, _ in broken], f"{name}: broken input should fail rule {rule}")

    def test_tell_index_points_at_owl_tell_arc(self):
        # tell_min edits events[13] by index; guard against the fixture order changing.
        self.assertEqual(GOOD["events"][13]["id"], "owl_tell_arc")
        self.assertEqual(GOOD["events"][15]["id"], "owl_condition_step")
        self.assertEqual(GOOD["events"][11]["id"], "owl_tell_bolts")

    def test_lift_loss_rule_applies_only_with_surv04_on(self):
        m = manifest_with(**{"SURV-04": True})
        for crit, ok in ((1.0, True), (0.5, True), (0.4, False)):
            with self.subTest(critical=crit):
                d = copy.deepcopy(GOOD)
                d["movement"]["lift_by_tier"].update(damaged=max(crit, 0.5), critical=crit)
                rules = [r for r, _, _ in feel_check.check(d, m)]
                self.assertEqual(rules == [], ok, rules)

    def test_gust_spacing_applies_only_with_owl02_on(self):
        m = manifest_with(**{"OWL-02": True})
        d = copy.deepcopy(GOOD)
        self.assertIn("spacing", [r for r, _, _ in feel_check.check(d, m)])   # OWL-02 on: arena needs a GUST_
        d["threat_spacing"]["arena_patterns"] = ["BOLT_Single", "GUST_Wing"]
        # 350 / 1800 / 2 + (w / 2 + 1.65) / 21.875 <= 1.0 s gust tell -> w <= 36.1.
        d["threat_spacing"]["gust_w_pct_w"] = 36.1
        self.assertEqual(feel_check.check(d, m), [])
        d["threat_spacing"]["gust_w_pct_w"] = 36.3
        self.assertIn("spacing", [r for r, _, _ in feel_check.check(d, m)])
        d["threat_spacing"]["gust_w_pct_w"] = 36.1
        d["events"] = [e for e in d["events"] if e["id"] != "owl_tell_gust"]
        self.assertIn("gust size needs", " ".join(w for _, _, w in feel_check.check(d, m)))
        # OWL-02 off: a 60% gust is not checked at all.
        d = copy.deepcopy(GOOD)
        d["threat_spacing"]["gust_w_pct_w"] = 60
        self.assertEqual(feel_check.check(d, MANIFEST), [])

    def test_pre_gdd13_movement_fails(self):
        # The B-era block (% of screen, lift loss, apex gravity multiplier, 1.2 s i-frames) must not pass.
        d = copy.deepcopy(GOOD)
        d["movement"] = {"closed_max_fall_pct_h": 70, "open_rise_pct_h": 12, "apex_gravity_mult": 0.5,
                         "lift_by_tier": {"intact": 1.0, "damaged": 0.85, "critical": 0.7},
                         "stop_s": 0.2, "state_blend_s": 0.2, "sign_change_max_frames": 2, "pose_max_frames": 3}
        d["forgiveness"]["iframes_s"] = 1.2
        rules = {r for r, _, _ in feel_check.check(d, MANIFEST)}
        self.assertTrue({"gdd", "movement"} <= rules, rules)

    def test_unreadable_manifest_fails(self):
        self.assertEqual([r for r, _, _ in feel_check.check(GOOD, {})][:1], ["gdd"])

    def test_shake_cap_matches_ui_lane(self):
        # Two lanes cap the same shake; one number, or a teammate gets two answers.
        import re
        with open(os.path.join(ROOT, "tools", "ui_check.py"), encoding="utf-8") as fh:
            m = re.search(r"^MAX_SHAKE_AMP_PCT_H\s*=\s*([0-9.]+)", fh.read(), re.M)
        self.assertIsNotNone(m, "tools/ui_check.py has no MAX_SHAKE_AMP_PCT_H")
        self.assertEqual(float(m.group(1)), feel_check.SHAKE_MAX_AMP_PCT_H)

    def test_every_required_event_present_and_every_rule_covered(self):
        ids = {e["id"] for e in GOOD["events"]}
        self.assertTrue(feel_check.REQUIRED_EVENTS <= ids)
        rules = {"hitstop", "shake", "squash", "flash", "ease", "flag", "cues", "tell", "vfx",
                 "movement", "forgiveness", "latency", "required", "schema", "spacing", "rumble", "owl", "gdd"}
        self.assertEqual(rules, {r for r, _, _ in CASES.values()})

    def test_fields_lists_one_bool_and_one_power_per_cue(self):
        out = feel_check.fields(GOOD)
        n_cues = sum(len(e["cues"]) for e in GOOD["events"])
        bools = [line for line in out if line.startswith("bool ")]
        powers = [line for line in out if line.startswith("float ") and "Power" in line]
        self.assertEqual(len(bools), n_cues + len(GOOD["events"]))
        self.assertEqual(len(powers), n_cues + 1)  # + ShakePower

    def test_every_field_is_a_console_variable(self):
        # The A/B check flips a cvar in one running build (docs/feel-spec.md section 1.5).
        for line in feel_check.fields(GOOD):
            name = line.split()[1]
            with self.subTest(field=name):
                self.assertIn(f"cvar feel.{name}", line)

    def test_spring_settles_on_live_defaults(self):
        self.assertLessEqual(feel_check.spring_tail(0.3, 0.2, 12), feel_check.SPRING_END_MAX)
        self.assertGreater(feel_check.spring_tail(0.1, 0.1, 12), feel_check.SPRING_END_MAX)


SIGNERS = {"mara"}                       # tests/fixtures/feel/brief-people.md: confirmed Game design owner


def commit_ok(sha):
    return True


def commit_missing(sha):
    return False


def ab(flag, name, signers=SIGNERS, commit_exists=commit_ok, data=None):
    return feel_check.check_ab(data or GOOD, flag, os.path.join(FIX, name), signers, commit_exists)


def brief(name):
    with open(os.path.join(FIX, name), encoding="utf-8") as fh:
        return fh.read()


class FeelLogTests(unittest.TestCase):
    def test_ab_row_passes(self):
        self.assertEqual(ab("bOpenSquash", "ab-good.csv"), [])

    def test_design_owner_read_from_people(self):
        self.assertEqual(feel_check.design_owners(brief("brief-people.md")), {"mara"})
        self.assertEqual(feel_check.humans(brief("brief-people.md")), {"mara", "theo"})   # Dee is only proposed

    def test_people_not_filled_gives_no_signer(self):
        self.assertEqual(feel_check.design_owners(brief("brief-tbd.md")), set())
        self.assertEqual(feel_check.humans(brief("brief-tbd.md")), set())

    def test_ab_agent_signature_fails(self):
        p = ab("bOpenSquash", "ab-agent.csv")
        self.assertIn("not the game design owner", " ".join(m for _, _, m in p))

    def test_ab_other_teammate_signature_fails(self):
        p = ab("bOpenSquash", "ab-good.csv", signers={"theo"})
        self.assertIn("not the game design owner", " ".join(m for _, _, m in p))

    def test_ab_no_confirmed_owner_fails(self):
        p = ab("bOpenSquash", "ab-good.csv", signers=set())
        self.assertIn("no confirmed 'Game design owner'", " ".join(m for _, _, m in p))

    def test_ab_unknown_commit_fails(self):
        p = ab("bOpenSquash", "ab-good.csv", commit_exists=commit_missing)
        self.assertIn("not a commit in this repo", " ".join(m for _, _, m in p))

    def test_git_commit_exists_on_head_and_not_on_junk(self):
        import subprocess
        try:
            head = subprocess.run(["git", "rev-parse", "HEAD"], cwd=ROOT, capture_output=True, text=True, check=True).stdout.strip()
        except (OSError, subprocess.CalledProcessError):
            self.skipTest("no git repo here")
        self.assertTrue(feel_check.git_commit_exists(head))
        self.assertFalse(feel_check.git_commit_exists("0000000000000000000000000000000000000000"))

    def test_arena_row_passes(self):
        self.assertEqual(feel_check.check_arena(GOOD, os.path.join(FIX, "arena-good.csv"), {"mara", "theo"}, commit_ok), [])

    def test_arena_empty_log_fails(self):
        p = feel_check.check_arena(GOOD, feel_check.ARENA_LOG, {"theo"}, commit_ok)
        self.assertIn("no L_Graybox run logged", " ".join(m for _, _, m in p))

    def test_arena_bad_row_fails_each_way(self):
        p = feel_check.check_arena(GOOD, os.path.join(FIX, "arena-bad.csv"), {"theo"}, commit_ok)
        msgs = " ".join(m for _, _, m in p)
        for want in ("map must be L_Graybox", "gate must be", "patterns must list", "cues_on", "note", "commit sha", "an agent cannot play"):
            self.assertIn(want, msgs)

    def test_arena_needs_confirmed_people_and_real_commit(self):
        good = os.path.join(FIX, "arena-good.csv")
        self.assertIn("card 0.0", " ".join(m for _, _, m in feel_check.check_arena(GOOD, good, set(), commit_ok)))
        self.assertIn("not a commit", " ".join(m for _, _, m in feel_check.check_arena(GOOD, good, {"theo"}, commit_missing)))

    def test_arena_patterns_follow_feel_json(self):
        d = copy.deepcopy(GOOD)
        d["threat_spacing"]["arena_patterns"] = ["BOLT_Fan3", "GUST_Wing", "BOLT_Arc"]
        p = feel_check.check_arena(d, os.path.join(FIX, "arena-good.csv"), {"theo"}, commit_ok)
        self.assertIn("patterns must list", " ".join(m for _, _, m in p))

    def test_ab_missing_row_fails(self):
        self.assertTrue(ab("bCloseSquash", "ab-good.csv"))

    def test_ab_unknown_flag_fails(self):
        self.assertTrue(ab("bNoSuchFlag", "ab-good.csv"))

    def test_ab_unsigned_bad_row_fails(self):
        p = ab("bOpenSquash", "ab-bad.csv")
        msgs = " ".join(m for _, _, m in p)
        self.assertIn("signed_by", msgs)
        self.assertIn("verdict", msgs)
        self.assertIn("off_note", msgs)

    def test_ab_event_column_must_match_flag_owner(self):
        p = ab("bOpenSquash", "ab-wrong-event.csv")
        self.assertIn("belongs to umbrella_open", " ".join(m for _, _, m in p))

    def test_ab_event_row_covers_its_mvp_cues(self):
        self.assertEqual(ab("bOpenFeel", "ab-event.csv"), [])
        self.assertEqual(ab("bOpenSquash", "ab-event.csv"), [])   # rank 1
        self.assertEqual(ab("bOpenPose", "ab-event.csv"), [])     # rank 2

    def test_ab_rank3_cue_needs_its_own_row(self):
        p = ab("bOpenPuff", "ab-event.csv")
        self.assertIn("rank 3+", " ".join(m for _, _, m in p))

    def test_ab_event_row_for_other_event_does_not_cover(self):
        self.assertTrue(ab("bCloseSquash", "ab-event.csv"))

    def test_ab_bad_event_row_fails_its_cues(self):
        p = ab("bOpenSquash", "ab-event-bad.csv")
        msgs = " ".join(m for _, _, m in p)
        self.assertIn("signed_by", msgs)
        self.assertIn("off_note", msgs)

    def test_protected_cue_present_passes(self):
        self.assertEqual(feel_check.check_protected(GOOD, os.path.join(FIX, "ab-good.csv"), SIGNERS, commit_ok), [])

    def test_protected_cue_removed_without_cut_row_fails(self):
        d = copy.deepcopy(GOOD)
        ev(d, "bolt_fire")["cues"] = [c for c in ev(d, "bolt_fire")["cues"] if c["flag"] != "bBoltKick"]
        p = feel_check.check_protected(d, os.path.join(FIX, "ab-good.csv"), SIGNERS, commit_ok)
        self.assertEqual([f for _, f, _ in p], ["bBoltKick"])

    def test_protected_cue_removed_with_signed_cut_row_passes(self):
        d = copy.deepcopy(GOOD)
        ev(d, "bolt_fire")["cues"] = [c for c in ev(d, "bolt_fire")["cues"] if c["flag"] != "bBoltKick"]
        self.assertEqual(feel_check.check_protected(d, os.path.join(FIX, "ab-cut-kick.csv"), SIGNERS, commit_ok), [])

    def test_gate_latency_row_passes(self):
        self.assertEqual(feel_check.check_gate("G2", "1a2b3c4d", os.path.join(FIX, "latency-good.csv")), [])

    def test_gate_over_target_passes_with_note(self):
        buf = io.StringIO()
        with redirect_stdout(buf):
            p = feel_check.check_gate("G3", "5e6f7a8b", os.path.join(FIX, "latency-good.csv"))
        self.assertEqual(p, [])
        self.assertIn("over the 67 ms target", buf.getvalue())

    def test_gate_missing_build_fails(self):
        self.assertTrue(feel_check.check_gate("G2", "deadbeef", os.path.join(FIX, "latency-good.csv")))

    def test_gate_bad_row_fails_each_way(self):
        p = feel_check.check_gate("G2", "1a2b3c4d", os.path.join(FIX, "latency-bad.csv"))
        msgs = " ".join(m for _, _, m in p)
        for want in ("fail line", "240 fps", "presses", "measured_by", "smoke budget", "peak_bolts"):
            self.assertIn(want, msgs)

    def test_gate_peak_frame_on_limit_passes_and_missing_fails(self):
        # latency-good G2 row has peak_frame_ms = 33, exactly the smoke budget.
        self.assertEqual(feel_check.check_gate("G2", "1a2b3c4d", os.path.join(FIX, "latency-good.csv")), [])
        p = feel_check.check_gate("G2", "1a2b3c4d", os.path.join(FIX, "latency-noperf.csv"))
        self.assertIn("peak_frame_ms", " ".join(m for _, _, m in p))

    def test_peak_frame_budget_matches_smoke_contract(self):
        with open(os.path.join(ROOT, "tools", "ue", "smoke.ps1"), encoding="utf-8") as fh:
            src = fh.read()
        self.assertIn(f'else {{ "{feel_check.PEAK_FRAME_MAX_MS}" }}', src)

    def test_gate_short_build_fails(self):
        for bad in ("1", "1a2b3c", "", "XYZ1234", "1a2b3c4d-dirty"):
            with self.subTest(build=bad):
                p = feel_check.check_gate("G2", bad, os.path.join(FIX, "latency-good.csv"))
                self.assertIn("not a commit sha", " ".join(m for _, _, m in p))

    def test_gate_build_prefix_matches_either_way(self):
        good = os.path.join(FIX, "latency-good.csv")
        self.assertEqual(feel_check.check_gate("G2", "1a2b3c4", good), [])           # short form of the row
        self.assertEqual(feel_check.check_gate("G2", "1a2b3c4d9999", good), [])      # longer form of the row
        self.assertTrue(feel_check.check_gate("G2", "1a2b3c5", good))                # different sha


OLD_MAP_MARKER = "UmbrellaElla.Hazard.SpikesDamageOnce"   # a row only the old 5-section platformer map has


class FeelTestMapTests(unittest.TestCase):
    def read(self, name):
        with open(os.path.join(FIX, name), encoding="utf-8") as fh:
            return fh.read()

    def test_all_spec_tests_in_map_passes(self):
        self.assertEqual(feel_check.check_test_map(self.read("spec-tests.md"), self.read("test-map-good.md")), [])

    def test_missing_row_fails_and_prose_does_not_count(self):
        p = feel_check.check_test_map(self.read("spec-tests.md"), self.read("test-map-missing.md"))
        self.assertEqual([w for _, w, _ in p], ["UmbrellaElla.Move.World.FeelEnvelope"])

    def test_row_without_world_mark_fails(self):
        p = feel_check.check_test_map(self.read("spec-tests.md"), self.read("test-map-noworld.md"))
        self.assertEqual([w for _, w, _ in p], ["UmbrellaElla.Feel.HitStopFrames"])
        self.assertIn("(world)", p[0][2])

    def test_printed_rows_pass_the_check(self):
        with open(feel_check.SPEC, encoding="utf-8") as fh:
            live = fh.read()
        for spec in (self.read("spec-tests.md"), live):
            rows = "\n".join(["| MVP | Required tests | Card | Status |", "|---|---|---|---|"] + feel_check.test_map_rows(spec))
            self.assertEqual(feel_check.check_test_map(spec, rows), [])

    def test_printed_rows_are_planned_and_unique(self):
        rows = feel_check.test_map_rows(self.read("spec-tests.md"))
        self.assertEqual(rows, ["| Feel | – | `UmbrellaElla.Feel.HitStopFrames` (world) | | planned |",
                                "| Feel | – | `UmbrellaElla.Move.World.FeelEnvelope` | | planned |"])

    def test_spec_with_no_tests_fails(self):
        self.assertTrue(feel_check.check_test_map("no tests here", self.read("test-map-good.md")))

    def test_live_spec_names_the_engine_tests(self):
        with open(feel_check.SPEC, encoding="utf-8") as fh:
            names = feel_check.spec_test_names(fh.read())
        for want in ("UmbrellaElla.Feel.HitStopFrames", "UmbrellaElla.Feel.SquashCurve", "UmbrellaElla.Feel.InputSameTick",
                     "UmbrellaElla.Move.World.FeelEnvelope", "UmbrellaElla.Feel.ToggleBuffer", "UmbrellaElla.Feel.Hitboxes",
                     "UmbrellaElla.Feel.ShakeCurve", "UmbrellaElla.Feel.ToggleAtRuntime", "UmbrellaElla.Feel.OwlConditionSteps"):
            self.assertIn(want, names)
        # The UI lane owns its shake-off test row; naming it here in full would demand a second row.
        self.assertNotIn("UmbrellaElla.UI.World.ShakeOffZeroesShake", names)

    def test_live_spec_tests_all_have_test_map_rows(self):
        # pipeline/qa/test-map.md carries a (world) row for every engine test docs/feel-spec.md names.
        # Until the test-map pass lands, the map still lists only the old platformer tests: skip, by name, so CI
        # stays green. The moment one feel row lands, or the old rows go, this test enforces every row.
        with open(feel_check.SPEC, encoding="utf-8") as fh:
            spec = fh.read()
        with open(feel_check.TEST_MAP, encoding="utf-8") as fh:
            tmap = fh.read()
        names = feel_check.spec_test_names(spec)
        if OLD_MAP_MARKER in tmap and not any(n in tmap for n in names):
            self.skipTest(f"pipeline/qa/test-map.md is still the old platformer map ({OLD_MAP_MARKER}); "
                          "paste `python3 tools/feel_check.py --test-map-rows` there")
        p = feel_check.check_test_map(spec, tmap)
        self.assertEqual(p, [], "\n".join(f"{w}: {m}" for _, w, m in p))


class FeelCliTests(unittest.TestCase):
    def run_cli(self, *args):
        buf = io.StringIO()
        with redirect_stdout(buf):
            code = feel_check.main(list(args))
        return code, buf.getvalue()

    def test_live_feel_json_passes(self):
        code, out = self.run_cli()
        self.assertEqual(code, 0, out)

    def test_cli_fails_on_broken_file(self):
        import tempfile
        d = copy.deepcopy(GOOD)
        cue(d, "player_hit", "hitstop")["frames"] = 9
        with tempfile.NamedTemporaryFile("w", suffix=".json", delete=False) as fh:
            json.dump(d, fh)
        try:
            code, out = self.run_cli("--feel", fh.name)
        finally:
            os.unlink(fh.name)
        self.assertEqual(code, 1)
        self.assertIn("[hitstop]", out)

    def test_cli_gate_short_build_exits_1(self):
        code, out = self.run_cli("--gate", "G2", "--build", "1",
                                 "--latency-log", os.path.join(FIX, "latency-good.csv"))
        self.assertEqual(code, 1, out)
        self.assertIn("not a commit sha", out)

    def test_cli_test_map_missing_row_exits_1(self):
        code, out = self.run_cli("--test-map", os.path.join(FIX, "test-map-missing.md"),
                                 "--spec", os.path.join(FIX, "spec-tests.md"))
        self.assertEqual(code, 1, out)
        self.assertIn("[testmap] UmbrellaElla.Move.World.FeelEnvelope", out)

    def test_cli_test_map_good_exits_0(self):
        code, out = self.run_cli("--test-map", os.path.join(FIX, "test-map-good.md"),
                                 "--spec", os.path.join(FIX, "spec-tests.md"))
        self.assertEqual(code, 0, out)

    def test_cli_test_map_rows_prints_rows(self):
        code, out = self.run_cli("--test-map-rows", "--spec", os.path.join(FIX, "spec-tests.md"))
        self.assertEqual(code, 0, out)
        self.assertIn("| Feel | – | `UmbrellaElla.Feel.HitStopFrames` (world) | | planned |", out)

    def test_cli_arena_on_empty_log_exits_1(self):
        code, out = self.run_cli("--arena", "--brief", os.path.join(FIX, "brief-people.md"))
        self.assertEqual(code, 1, out)
        self.assertIn("[arena]", out)

    def test_cli_gate_g2_runs_arena(self):
        code, out = self.run_cli("--gate", "G2", "--build", "1a2b3c4d",
                                 "--latency-log", os.path.join(FIX, "latency-good.csv"),
                                 "--brief", os.path.join(FIX, "brief-people.md"))
        self.assertEqual(code, 1, out)
        self.assertIn("no L_Graybox run logged", out)

    def test_cli_ab_agent_signer_exits_1(self):
        code, out = self.run_cli("--ab", "bOpenSquash", "--ab-log", os.path.join(FIX, "ab-agent.csv"),
                                 "--brief", os.path.join(FIX, "brief-people.md"))
        self.assertEqual(code, 1, out)
        self.assertIn("agents never sign", out)

    def test_cli_gate_needs_build(self):
        code, out = self.run_cli("--gate", "G2")
        self.assertEqual(code, 1)
        self.assertIn("--build", out)


class StolenHourFeel(unittest.TestCase):
    """GDD SH1.0: four state speeds (MOVE-21), lift falls with active health to SURV-05.min_lift, the gust is P0."""

    def setUp(self):
        with open(os.path.join(ROOT, "pipeline", "feel", "feel.json"), encoding="utf-8") as fh:
            self.d = json.load(fh)
        with open(os.path.join(ROOT, "docs", "feature-manifest.json"), encoding="utf-8") as fh:
            self.m = json.load(fh)

    def test_live_data_passes_and_breaks_fail(self):
        self.assertEqual(feel_check.check(self.d, self.m), [])
        for key, v, rule in (("rise_speed", 300, "gdd"), ("free_fall_speed", 650, "gdd"), ("lift_min", 1.0, "gdd"),
                             ("gravity", 980, "movement")):
            d = copy.deepcopy(self.d)
            d["movement"][key] = v
            with self.subTest(key):
                self.assertIn(rule, [r for r, _, _ in feel_check.check(d, self.m)])
        d = copy.deepcopy(self.d)
        d["forgiveness"]["iframes_s"] = 0.8
        self.assertIn("gdd", [r for r, _, _ in feel_check.check(d, self.m)], "post-hit protection is 0.65 s")
        d = copy.deepcopy(self.d)
        d["threat_spacing"]["arena_patterns"] = ["RED_Fan"]
        self.assertIn("spacing", [r for r, _, _ in feel_check.check(d, self.m)], "OWL-16 on: the arena runs the gust")


if __name__ == "__main__":
    unittest.main()
