#!/usr/bin/env python3
"""Feel gate for THE LAST HOUR. Stdlib only; runs locally and in CI.

Checks pipeline/feel/feel.json (the data the DA_Feel asset is made from) against the
limits in docs/feel-spec.md, and its GDD 1.3 section 5A numbers against the approved start values in
docs/feature-manifest.json approved_parameters (manifest_check.py holds the manifest to the GDD tables).
The limits live in this file and the manifest, not in feel.json, so tuning the data cannot loosen the gate.

Usage:
  python3 tools/feel_check.py                      check feel.json
  python3 tools/feel_check.py --fields             print the DA_Feel fields (one bool + one power per cue)
  python3 tools/feel_check.py --ab FLAG            the A/B log has a signed on/off row for FLAG
  python3 tools/feel_check.py --gate G2 --build SHA  the latency log has a 240 fps row and a peak frame time for this gate and build
  python3 tools/feel_check.py --test-map           every engine test named in docs/feel-spec.md has a (world) row in pipeline/qa/test-map.md
  python3 tools/feel_check.py --test-map-rows      print the planned test-map rows to paste
  python3 tools/feel_check.py --arena              the arena log has a signed L_Graybox run (also run by --gate G2..G4)
Exit 0 = clean, 1 = problems found.
"""
import argparse
import csv
import json
import os
import re
import subprocess
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "tools"))
import tuning  # noqa: E402  the shared tunable/fixed rule and the baked-vs-sim check (dry run B H3, H4)
FEEL = os.path.join(ROOT, "pipeline", "feel", "feel.json")
AB_LOG = os.path.join(ROOT, "pipeline", "feel", "ab-log.csv")
LATENCY_LOG = os.path.join(ROOT, "pipeline", "feel", "latency-log.csv")
SPEC = os.path.join(ROOT, "docs", "feel-spec.md")
TEST_MAP = os.path.join(ROOT, "pipeline", "qa", "test-map.md")
ARENA_LOG = os.path.join(ROOT, "pipeline", "feel", "arena-log.csv")
JAM_BRIEF = os.path.join(ROOT, "docs", "jam-brief.md")
MANIFEST = os.path.join(ROOT, "docs", "feature-manifest.json")
DESIGN_OWNER_ROLE = "game design owner"   # docs/jam-brief.md People row that signs A/B rows
TEST_NAME_RE = re.compile(r"UmbrellaElla(?:\.\w+){2,}")   # same shape as check_automation_report.TEST_NAME
CVAR_PREFIX = "feel."             # every DA_Feel field is also a console variable in Development builds

# ---- Limits (docs/feel-spec.md). Changing one needs a measurement (AGENTS.md section 7). ----
# GDD 1.3 P0 feedback. Not required (dry run A M2): bolt_fire_manual (DEC-02: auto-fire, no manual fire),
# bolt_hit_wing and owl_condition_step (OWL-03 / COM-03 wing and condition effects are EXPERIMENT, off; the owl
# has no HP, GDD 1.3 section 7). They may stay as optional rows. bolt_hit_clock is P0: "Clock-hit visual cue ON".
REQUIRED_EVENTS = {
    "umbrella_open", "umbrella_close", "gust_catch", "bolt_fire",
    "bolt_hit_clock", "bolt_hit_body", "player_hit",
    "tier_damaged", "tier_critical", "owl_tell_bolts", "end_trigger",
    "shield_catch", "shield_heal",   # GDD 1.3 section 6: CatchSucceeded, and the 20 HP heal when the cooldown is ready
}
# GDD SH1.0 P0 feedback: the wings are a target (OWL-09), the casts and the gust are warned physical attacks
# (OWL-15, OWL-21), red has no timed prefire (OWL-12), and the clock HUD replaces the 1.3 wear tiers (SURV-05; the
# ANIM-04 condition states are cosmetic). shield_catch / shield_heal are the yellow absorb catch and heal (UMB-05).
REQUIRED_EVENTS_BY_GDD = {
    "1.3": REQUIRED_EVENTS,
    "SH1.0": {"umbrella_open", "umbrella_close", "gust_catch", "bolt_fire", "bolt_hit_clock", "bolt_hit_body",
              "bolt_hit_wing", "player_hit", "owl_tell_cast", "owl_tell_gust", "end_trigger", "shield_catch",
              "shield_heal"},
}
MVP_EVENTS = {"bolt_hit_clock"}   # GDD 1.3 section 7 (line 318): the clock-hit visual cue is ON in the P0 build
EVENT_KINDS = {"state", "fire", "owl_hit", "owl_state", "player_hit", "tell", "end"}
CUE_KINDS = {"sound", "particles", "squash", "shake", "hitstop", "flash", "pose", "nudge", "tween", "rumble", "overlay"}
VISUAL_KINDS = {"particles", "squash", "flash", "pose", "nudge", "tween", "overlay"}
# Optional owl condition row (owl_condition_step; OWL-03 / COM-03 experiments, off in GDD 1.3). When the row
# exists, hits add up into steps and each step swaps a lasting overlay on that part.
OWL_PARTS = {"clock", "wing"}
OWL_STEPS = (2, 5)                # overlay tiers per part
OWL_HITS_PER_STEP = (1, 20)
MVP_RANK = 2                      # ranks 1-2 are MVP: built first, need a sound and a visual
FLAG_RE = re.compile(r"^b[A-Z][A-Za-z0-9]*$")

HITSTOP_MAX_FRAMES = 6            # research: Celeste 3-6 f, Melee >= 3 f
HITSTOP_OWL_HIT_MAX = 3           # bolt hits: 0-3 f, never more (auto-fire stutter)
HITSTOP_OWL_HIT_MIN_COOLDOWN_S = 0.3
SHAKE_EVENTS = {"player_hit", "tier_critical", "end_trigger"}   # no shake on routine events
SHAKE_MAX_S = 0.2                 # Celeste DirectionalShake 0.1-0.2 s
SHAKE_MAX_AMP_PCT_H = 2.5         # research 2-3% of screen height; same cap as tools/ui_check.py MAX_SHAKE_AMP_PCT_H
SHAKE_DIRECTIONS = {"away_from_source", "toward_owl"}   # Celeste DirectionalShake: a direction, not a bool
# Shake spring, per frame at 60 fps from x = 1 (along direction), v = 0:
#   v += -elasticity * x; v *= (1 - drag); x += v.  The offset is forced to 0 at duration_s,
#   so |x| over the last 3 frames must already be small, or the cut shows as a pop.
SPRING_DRAG = (0.1, 0.5)
SPRING_ELASTICITY = (0.05, 0.6)
SPRING_END_MAX = 0.25             # |offset| / amplitude over the last 3 frames before the cut
RUMBLE_EVENTS = {"player_hit", "tier_critical"}   # Celeste pairs its big freezes with rumble
RUMBLE_MAX_S = 0.2
SQUASH_SCALE_BY = {"none", "fall_speed"}   # fall_speed: deviation x min(v / max_fall, 1)
# GDD 1.3 section 5A: "No per-state gravity multiplier exists"; fast fall (MOVE-02) is off.
FAST_FALL_KEY = re.compile(r"fast_?fall|dive|descent_mult|fall_mult|grav\w*_(?:mult|scale)|apex", re.I)
NUDGE_MAX_PX = 2                  # bolt fire kickback, render only
SQUASH_MAX_DEV = 0.4              # Celeste uses 0.4 on jumps; we stay at or under it
SQUASH_MIN_DEV = 0.1
SQUASH_MAX_RECOVER_S = 0.25       # Celeste jump stretch recovers in 0.23 s
FLASH_MAX_HZ = 3                  # WCAG 2.3.1 three-flash rule
PITCH_JITTER_MAX_PCT = 10
PARTICLES_MAX = 32
PARTICLES_FREQUENT_MAX = 8        # bolt fire and bolt hits happen many times a second
FREQUENT_KINDS = {"fire", "owl_hit"}
TELEGRAPH_MIN_S = 0.35            # research: never under 0.35 s
TELL_VISUAL_HOLD_KINDS = {"pose": "hold_s", "flash": "hold_s", "tween": "duration_s"}

# Threat spacing (docs/feel-spec.md section 8b). Bolts fly sideways, so their gap is vertical.
BOLT_GAP_HURTBOX_MULT = 2.5       # gap between two bolts >= 2.5x the player hurtbox height
SPACING_ARENA = "L_Graybox"
EFFECT_TYPES = {"gameplay", "cosmetic"}
# Systems that carry gameplay information are never culled (EFT_Gameplay).
GAMEPLAY_SYSTEM_PREFIXES = ("NS_HitSpark", "NS_WindLines")

LATENCY_TARGET_MS = 67            # 4 frames at 60 fps
LATENCY_FAIL_MS = 100             # Swink ~100 ms
PEAK_FRAME_MAX_MS = 33            # smoke contract: tools/ue/smoke.ps1 SMOKE_MAX_FRAME_MS default
PEAK_FRAME_TARGET_MS = 16.7       # 60 fps
GAME_SIDE_MAX_FRAMES = 1

# GDD 1.3 section 5A keys in feel.json movement -> manifest approved_parameters key. Each must sit in its dev
# range (the start is provisional tuning; pipeline/checklists/tuning.md bakes any in-range value). The GDD changes
# the range, never this file or feel.json alone.
GDD_KEYS = tuning.FEEL_MOVEMENT                                    # one map for the bake and both sims
GDD_FORGIVENESS_KEYS = tuning.FEEL_FORGIVENESS                     # GDD 1.3 section 6: 0.8 s
GDD_TELL_KEY = tuning.TELL_KEY                                     # owl_tell_bolts.telegraph_s (0.75 s)
LIFT_LOSS_FEATURE = "SURV-04"     # wear reduces lift: EXPERIMENT, off (DEC-05). Off = every tier 1.0.
GUST_FEATURE = "OWL-02"           # owl gust attack: PROPOSED, off. Off = no GUST_ pattern needed in the arena.
# key -> (min, max). [proposed] research ranges for the ENGINEERING_PROVISIONAL keys GDD 1.3 omits.
MOVEMENT_RANGES = {
    "stop_s": (0.08, 0.80), "state_blend_s": (0.15, 0.25), "sign_change_max_frames": (0, 2),
    "pose_max_frames": (0, 3),
}
MOVEMENT_TEXT_KEYS = {"owner", "asset", "units", "gdd_note", "engineering_provisional", "lift_by_tier", "steering"}
LIFT_CRITICAL_MIN = 0.5           # only with SURV-04 on: never unwinnable, critical keeps at least half the lift
FORGIVENESS_RANGES = {
    "toggle_buffer_s": (0.07, 0.13), "player_hurtbox_ratio": (0.5, 0.65),
    "projectile_hitbox_ratio": (0.7, 0.85), "bound_nudge_px": (0, 6),
}
AB_VERDICTS = {"keep", "cut", "tune"}
GATES = {"G1", "G2", "G3", "G4"}
SHA_RE = re.compile(r"^[0-9a-f]{7,40}$")
# Cues that may not leave feel.json without a signed A/B row with verdict "cut" (Vlambeer recoil practice).
CUT_NEEDS_AB = {"bBoltKick"}


def num(v):
    return isinstance(v, (int, float)) and not isinstance(v, bool)


def load_manifest(path=MANIFEST):
    try:
        with open(path, encoding="utf-8") as fh:
            return json.load(fh)
    except (OSError, ValueError):
        return None


def approved(manifest):
    return ((manifest or {}).get("approved_parameters") or {}).get("values") or {}


def feature_on(manifest, fid):
    for f in (manifest or {}).get("features", []):
        if f.get("feature_id") == fid:
            return f.get("default_enabled") is True
    return False


def gdd_value(p, where, v, rec, key, manifest=None):
    """v follows the shared tunable/fixed rule (tools/tuning.py, the same one tools/bake_preset.py and
    tools/encounter_check.py use; dry run B H3): a tunable key sits in its GDD 1.3 section 5A dev range and on its
    step; a key with no printed range (a fixed value) equals its start."""
    if not isinstance(rec, dict) or not num(rec.get("start")):
        p.append(("gdd", where, f"manifest approved_parameters has no {key}"))
        return
    if not num(v):
        p.append(("gdd", where, f"missing or not a number (GDD 1.3 approved {key} = {rec['start']})"))
        return
    why = tuning.value_problem({"approved_parameters": {"values": {key: rec}}}, key, v)
    if why:
        p.append(("gdd", where, why + "; change the GDD and the manifest approved_parameters first"))


def in_range(p, rule, where, v, lo, hi):
    if not num(v):
        p.append((rule, where, f"missing or not a number (want {lo}-{hi})"))
    elif not lo <= v <= hi:
        p.append((rule, where, f"{v} outside {lo}-{hi}"))


def check_cue(p, ev, cue, data, flags):
    eid, ekind = ev["id"], ev.get("kind")
    k = cue.get("kind")
    where = f"{eid}.{cue.get('flag', '?')}"
    if k not in CUE_KINDS:
        p.append(("schema", where, f"cue kind '{k}' not one of {sorted(CUE_KINDS)}"))
        return
    if not isinstance(cue.get("rank"), int) or isinstance(cue.get("rank"), bool) or cue["rank"] < 1:
        p.append(("schema", where, "rank must be an integer >= 1"))
    f = cue.get("flag")
    if not isinstance(f, str) or not FLAG_RE.match(f):
        p.append(("flag", where, "every cue needs an on/off flag named bSomething"))
    elif f in flags:
        p.append(("flag", where, f"flag {f} used twice"))
    else:
        flags.add(f)
    in_range(p, "flag", where + ".power", cue.get("power"), 0.0, 1.0)

    curves = set(data.get("easing", {}).get("curves", []))
    if k in ("squash", "tween", "overlay"):
        e = cue.get("ease")
        if e == "linear" or e not in curves:
            p.append(("ease", where, f"ease '{e}' must be a named curve from easing.curves, never linear"))
    if k == "squash" and cue.get("scale_by", "none") not in SQUASH_SCALE_BY:
        p.append(("squash", where, f"scale_by must be one of {sorted(SQUASH_SCALE_BY)}"))
    if k in ("squash", "nudge") and cue.get("target") != "render_only":
        p.append(("squash", where, "scale and nudge change the sprite only (target render_only); collision stays fixed"))

    if k == "sound":
        if not cue.get("asset"):
            p.append(("schema", where, "sound needs an asset"))
        in_range(p, "schema", where + ".pitch_jitter_pct", cue.get("pitch_jitter_pct", 0), 0, PITCH_JITTER_MAX_PCT)
    elif k == "hitstop":
        fr = cue.get("frames")
        cap = HITSTOP_OWL_HIT_MAX if ekind == "owl_hit" else HITSTOP_MAX_FRAMES
        if any(str(key).startswith("fade") for key in cue):
            p.append(("hitstop", where, "hit-stop is a hard cut for the jam; no fade keys"))
        if ekind == "fire":
            p.append(("hitstop", where, "no hit-stop on bolt fire"))
        elif not isinstance(fr, int) or isinstance(fr, bool) or not 0 <= fr <= cap:
            p.append(("hitstop", where, f"frames {fr} outside 0-{cap}"))
        if ekind == "owl_hit" and isinstance(fr, int) and fr > 0 and not (
                num(cue.get("cooldown_s")) and cue["cooldown_s"] >= HITSTOP_OWL_HIT_MIN_COOLDOWN_S):
            p.append(("hitstop", where, f"bolt-hit hit-stop needs cooldown_s >= {HITSTOP_OWL_HIT_MIN_COOLDOWN_S}"))
    elif k == "shake":
        if eid not in SHAKE_EVENTS:
            p.append(("shake", where, f"shake only on {sorted(SHAKE_EVENTS)}; use a nudge (<= {NUDGE_MAX_PX} px) or nothing"))
        in_range(p, "shake", where + ".duration_s", cue.get("duration_s"), 0.01, SHAKE_MAX_S)
        in_range(p, "shake", where + ".amp_pct_h", cue.get("amp_pct_h"), 0.1, SHAKE_MAX_AMP_PCT_H)
        if cue.get("direction") not in SHAKE_DIRECTIONS:
            p.append(("shake", where, f"direction must be one of {sorted(SHAKE_DIRECTIONS)}"))
        if "directional" in cue:
            p.append(("shake", where, "use direction, not the old directional bool"))
        if cue.get("decay") != "spring":
            p.append(("shake", where, "shake must decay as a damped spring (decay: spring)"))
    elif k == "rumble":
        if eid not in RUMBLE_EVENTS:
            p.append(("rumble", where, f"rumble only on {sorted(RUMBLE_EVENTS)}"))
        if cue.get("applies_if") != "gamepad":
            p.append(("rumble", where, "rumble needs applies_if: gamepad"))
        in_range(p, "rumble", where + ".duration_s", cue.get("duration_s"), 0.01, RUMBLE_MAX_S)
    elif k == "nudge":
        in_range(p, "shake", where + ".px", cue.get("px"), 0, NUDGE_MAX_PX)
    elif k == "squash":
        sc = cue.get("scale")
        if not (isinstance(sc, list) and len(sc) == 2 and all(num(x) for x in sc)):
            p.append(("squash", where, "scale must be [x, y]"))
        else:
            dev = max(abs(sc[0] - 1), abs(sc[1] - 1))
            if not SQUASH_MIN_DEV <= dev <= SQUASH_MAX_DEV + 1e-9:
                p.append(("squash", where, f"peak change {dev:.2f} outside {SQUASH_MIN_DEV}-{SQUASH_MAX_DEV}"))
        in_range(p, "squash", where + ".recover_s", cue.get("recover_s"), 0.05, SQUASH_MAX_RECOVER_S)
    elif k == "flash":
        in_range(p, "flash", where + ".max_rate_hz", cue.get("max_rate_hz"), 0.1, FLASH_MAX_HZ)
    elif k == "overlay":
        if cue.get("part") not in OWL_PARTS:
            p.append(("owl", where, f"overlay part must be one of {sorted(OWL_PARTS)}"))
        st = cue.get("steps")
        if not isinstance(st, int) or isinstance(st, bool) or not OWL_STEPS[0] <= st <= OWL_STEPS[1]:
            p.append(("owl", where, f"steps {st} outside {OWL_STEPS[0]}-{OWL_STEPS[1]}"))
        if cue.get("persist") is not True:
            p.append(("owl", where, "the overlay stays until the run restarts (persist: true): it shows condition, not a hit"))
    elif k == "pose" and ekind in ("state",):
        cap = data.get("movement", {}).get("pose_max_frames", 3)
        in_range(p, "schema", where + ".frames", cue.get("frames"), 0, cap)
    elif k == "particles":
        systems = data.get("vfx", {}).get("systems", {})
        s = cue.get("system")
        if s not in systems:
            p.append(("vfx", where, f"system '{s}' not in vfx.systems"))
        else:
            if ekind in FREQUENT_KINDS and not systems[s].get("pooled"):
                p.append(("vfx", where, f"{s} must be pooled: {eid} fires many times a second"))
            if ekind == "owl_hit":
                parent = data["vfx"].get("parent")
                if s != parent and systems[s].get("parent") != parent:
                    p.append(("vfx", where, f"owl hits use {parent} or a child override of it"))
        cap = PARTICLES_FREQUENT_MAX if ekind in FREQUENT_KINDS else PARTICLES_MAX
        in_range(p, "vfx", where + ".count", cue.get("count"), 1, cap)


def check_event(p, ev, data, flags):
    eid = ev.get("id", "?")
    if ev.get("kind") not in EVENT_KINDS:
        p.append(("schema", eid, f"event kind '{ev.get('kind')}' not one of {sorted(EVENT_KINDS)}"))
    if not isinstance(ev.get("mvp"), bool):
        p.append(("schema", eid, "mvp must be true or false"))
    f = ev.get("flag")
    if not isinstance(f, str) or not FLAG_RE.match(f):
        p.append(("flag", eid, "every event needs an on/off flag named bSomething"))
    elif f in flags:
        p.append(("flag", eid, f"flag {f} used twice"))
    else:
        flags.add(f)
    cues = ev.get("cues")
    if not isinstance(cues, list) or not cues:
        p.append(("schema", eid, "needs a non-empty cues list"))
        return
    for c in cues:
        if isinstance(c, dict):
            check_cue(p, ev, c, data, flags)
        else:
            p.append(("schema", eid, "each cue is an object"))
    top = [c for c in cues if isinstance(c, dict) and isinstance(c.get("rank"), int) and c["rank"] <= MVP_RANK]
    if not any(c.get("kind") == "sound" for c in top):
        p.append(("cues", eid, f"needs a sound cue at rank <= {MVP_RANK}"))
    if not any(c.get("kind") in VISUAL_KINDS for c in top):
        p.append(("cues", eid, f"needs a visual cue at rank <= {MVP_RANK}"))
    if ev.get("kind") == "owl_hit" and not any(c.get("kind") in ("flash", "pose") for c in cues if isinstance(c, dict)):
        p.append(("cues", eid, "owl hits need a reaction flash or pose"))
    if ev.get("kind") == "owl_state":
        hps = ev.get("hits_per_step")
        parts = {c.get("part") for c in cues if isinstance(c, dict) and c.get("kind") == "overlay"
                 and isinstance(c.get("rank"), int) and c["rank"] <= MVP_RANK}
        for part in sorted(OWL_PARTS):
            if part not in parts:
                p.append(("owl", eid, f"needs a rank <= {MVP_RANK} overlay cue for the {part}"))
            v = hps.get(part) if isinstance(hps, dict) else None
            if not isinstance(v, int) or isinstance(v, bool) or not OWL_HITS_PER_STEP[0] <= v <= OWL_HITS_PER_STEP[1]:
                p.append(("owl", f"{eid}.hits_per_step.{part}",
                          f"{v} not an integer {OWL_HITS_PER_STEP[0]}-{OWL_HITS_PER_STEP[1]}"))
    if ev.get("kind") == "tell":
        in_range(p, "tell", eid + ".telegraph_s", ev.get("telegraph_s"), TELEGRAPH_MIN_S, 3.0)
        if not any(c.get("kind") == "sound" and c.get("rank") == 1 for c in cues if isinstance(c, dict)):
            p.append(("tell", eid, "every tell has a rank-1 sound"))
        tel = ev.get("telegraph_s")
        held = [c.get(TELL_VISUAL_HOLD_KINDS[c.get("kind")]) for c in cues
                if isinstance(c, dict) and c.get("kind") in TELL_VISUAL_HOLD_KINDS]
        if num(tel) and not any(num(h) and h >= tel - 1e-9 for h in held):
            p.append(("tell", eid, f"a pose or flash (hold_s) or tween (duration_s) must be held >= telegraph_s {tel}"))


def spring_tail(drag, elasticity, frames):
    """Largest |offset| (as a share of the amplitude) over the last 3 frames of a shake."""
    x, v, xs = 1.0, 0.0, [1.0]
    for _ in range(frames):
        v += -elasticity * x
        v *= 1 - drag
        x += v
        xs.append(x)
    return max(abs(t) for t in xs[-3:])


def check_spring(p, data):
    g = data["global"]
    d, e = g.get("spring_drag"), g.get("spring_elasticity")
    in_range(p, "shake", "global.spring_drag", d, *SPRING_DRAG)
    in_range(p, "shake", "global.spring_elasticity", e, *SPRING_ELASTICITY)
    if not (num(d) and num(e) and SPRING_DRAG[0] <= d <= SPRING_DRAG[1]
            and SPRING_ELASTICITY[0] <= e <= SPRING_ELASTICITY[1]):
        return
    fps = data.get("fps", 60)
    for ev in data.get("events", []):
        for c in ev.get("cues", []) if isinstance(ev, dict) else []:
            if isinstance(c, dict) and c.get("kind") == "shake" and num(c.get("duration_s")):
                n = max(3, round(c["duration_s"] * fps))
                tail = spring_tail(d, e, n)
                if tail > SPRING_END_MAX + 1e-9:
                    p.append(("shake", f"{ev.get('id')}.{c.get('flag')}",
                              f"spring still at {tail:.2f} of the amplitude when the shake ends at {n} f "
                              f"(max {SPRING_END_MAX}); raise spring_drag or spring_elasticity"))


def tell_s(data, eid):
    for ev in data.get("events", []):
        if isinstance(ev, dict) and ev.get("id") == eid:
            return ev.get("telegraph_s")
    return None


def check_spacing(p, data, manifest):
    """Owl threats leave room for the hurtbox, and a dodge fits inside the tell.
    Movement is in cm/s; spacing is % of the fixture arena (manifest fixtures.arena_cm). GDD 1.3: gravity ramps the
    fall and the gust is left sideways. GDD SH1.0: the fall is a state speed (MOVE-21) and the hostile gust is a
    horizontal band left by changing altitude (OWL-16), with direct steering off (MOVE-07)."""
    m = tuning.model(manifest)
    ts, mv, fg = data["threat_spacing"], data["movement"], data["forgiveness"]
    gust_feature = m["gust_feature"]
    gust_on = feature_on(manifest, gust_feature)
    if ts.get("arena_map") != SPACING_ARENA:
        p.append(("spacing", "threat_spacing.arena_map", f"tune feel in {SPACING_ARENA}"))
    pats = ts.get("arena_patterns")
    if not (isinstance(pats, list) and any(str(x).startswith(m["bolt_prefix"]) for x in pats)):
        p.append(("spacing", "threat_spacing.arena_patterns", f"the tuning arena runs the {m['bolt_prefix']} pattern"))
    elif gust_on and not any(str(x).startswith("GUST_") for x in pats):
        p.append(("spacing", "threat_spacing.arena_patterns", f"{gust_feature} is on: the tuning arena also runs a GUST_ pattern"))
    elif not gust_on and any(str(x).startswith("GUST_") for x in pats):
        p.append(("spacing", "threat_spacing.arena_patterns", f"GUST_ pattern listed but {gust_feature} (owl gust) is off"))
    gust_k = "gust_w_pct_w" if m["gravity"] else "gust_band_pct_h"
    keys = ("player_body_w_pct_w", "player_body_h_pct_h", "bolt_gap_min_pct_h", "bolt_dodge_max_pct_h", gust_k)
    for k in keys:
        in_range(p, "spacing", f"threat_spacing.{k}", ts.get(k), 0.1, 100)
    arena = (((manifest or {}).get("approved_parameters") or {}).get("fixtures") or {}).get("arena_cm")
    if not (isinstance(arena, list) and len(arena) == 2 and all(num(x) and x > 0 for x in arena)):
        p.append(("spacing", "manifest.approved_parameters.fixtures.arena_cm", "needs [width, height] in cm"))
        return
    hb = fg.get("player_hurtbox_cm") if isinstance(fg.get("player_hurtbox_cm"), dict) else {}
    motion = ([mv.get("max_fall_speed"), mv.get("gravity"), mv.get("move_speed"), mv.get("move_accel"),
               mv.get("open_steer_multiplier")] if m["gravity"] else [mv.get("fall_speed")])
    need = [ts.get(k) for k in keys] + [hb.get("w"), hb.get("h")] + motion
    if not all(num(x) and x > 0 for x in need):
        return
    body_w, body_h, gap, dodge, gust_w = need[:5]
    # The collider is fixed data, never body art x ratio (GDD 1.3 7A, 7C; GDD SH1.0 CORE-05). Spacing is % of the arena.
    hurt_w, hurt_h = hb["w"] / arena[0] * 100.0, hb["h"] / arena[1] * 100.0
    for k, art, have in (("w", body_w, hurt_w), ("h", body_h, hurt_h)):
        lo, hi = FORGIVENESS_RANGES["player_hurtbox_ratio"]
        if not lo - 1e-3 <= have / art <= hi + 1e-3:
            p.append(("spacing", f"forgiveness.player_hurtbox_cm.{k}",
                      f"collider is {have / art:.0%} of the body art box (alignment target {lo:.0%}-{hi:.0%}): "
                      "align the art's scale, pivot or offset; a collider change is a separate approved change"))
    if gap < BOLT_GAP_HURTBOX_MULT * hurt_h - 1e-9:
        p.append(("spacing", "threat_spacing.bolt_gap_min_pct_h",
                  f"{gap} < {BOLT_GAP_HURTBOX_MULT}x hurtbox height {hurt_h:.1f}"))
    t_bolt, t_gust = tell_s(data, m["tell_event"]), tell_s(data, "owl_tell_gust")
    fall = mv["max_fall_speed"] if m["gravity"] else mv["fall_speed"]
    fall_pct = fall / arena[1] * 100.0
    if num(t_bolt):
        # GDD 1.3: the natural fall (one gravity rule) ramps to max fall; GDD SH1.0: the fall state speed applies at once
        t = (mv["max_fall_speed"] / mv["gravity"] / 2 if m["gravity"] else 0.0) + dodge / fall_pct
        if t > t_bolt + 1e-9:
            p.append(("spacing", "threat_spacing.bolt_dodge_max_pct_h",
                      f"dodge takes {t:.2f} s falling, longer than the {t_bolt} s {m['tell_event']} tell"))
    if not gust_on:
        return
    if not num(t_gust):
        p.append(("spacing", f"threat_spacing.{gust_k}", "gust size needs owl_tell_gust.telegraph_s"))
    elif m["gravity"]:
        side_pct = mv["move_speed"] * mv["open_steer_multiplier"] / 100.0 / arena[0] * 100.0
        t = mv["move_speed"] / mv["move_accel"] / 2 + (gust_w / 2 + hurt_w / 2) / side_pct
        if t > t_gust + 1e-9:
            p.append(("spacing", "threat_spacing.gust_w_pct_w",
                      f"leaving the gust from its centre takes {t:.2f} s, longer than the {t_gust} s gust tell"))
    else:
        t = (gust_w / 2 + hurt_h / 2) / fall_pct
        if t > t_gust + 1e-9:
            p.append(("spacing", "threat_spacing.gust_band_pct_h",
                      f"falling out of the warned band from its centre takes {t:.2f} s, longer than the {t_gust} s gust tell"))


def check(data, manifest=None):
    """Return a list of (rule, where, message). Empty = pass.
    manifest: the feature manifest dict; None = read docs/feature-manifest.json."""
    p = []
    if manifest is None:
        manifest = load_manifest()
    if manifest is None:
        return [("gdd", "docs/feature-manifest.json", "cannot read the manifest (approved_parameters)")]
    if not isinstance(data, dict):
        return [("schema", "feel.json", "top level must be an object")]
    for key in ("global", "latency", "movement", "forgiveness", "threat_spacing", "easing", "vfx", "events"):
        if key not in data:
            p.append(("schema", key, "missing section"))
    if p:
        return p

    g = data["global"]
    in_range(p, "shake", "global.ShakePower", g.get("ShakePower"), 0.0, 1.0)
    if g.get("shake_off_option") is not True:
        p.append(("shake", "global.shake_off_option", "players must be able to turn shake off"))
    if g.get("hitstop_stacking") != "max":
        p.append(("hitstop", "global.hitstop_stacking", "two hit-stops on one frame take the longer one, never the sum (max)"))
    if g.get("hitstop_skip_if_slowed") is not True:
        p.append(("hitstop", "global.hitstop_skip_if_slowed", "skip hit-stop while time is already slowed"))
    in_range(p, "hitstop", "global.hitstop_input_buffer_s", g.get("hitstop_input_buffer_s"), 0.07, 0.13)
    check_spring(p, data)

    lat = data["latency"]
    in_range(p, "latency", "latency.game_side_input_frames", lat.get("game_side_input_frames"), 0, GAME_SIDE_MAX_FRAMES)
    in_range(p, "latency", "latency.first_visible_change_frames", lat.get("first_visible_change_frames"), 0, 1)
    in_range(p, "latency", "latency.input_to_photon_target_ms", lat.get("input_to_photon_target_ms"), 1, LATENCY_TARGET_MS)
    in_range(p, "latency", "latency.input_to_photon_fail_ms", lat.get("input_to_photon_fail_ms"), 1, LATENCY_FAIL_MS)

    mv = data["movement"]
    vals = approved(manifest)
    m = tuning.model(manifest)
    gdd_keys = m["feel_movement"]
    for k, key in gdd_keys.items():
        gdd_value(p, f"movement.{k}", mv.get(k), vals.get(key), key)
    for k, (lo, hi) in MOVEMENT_RANGES.items():
        in_range(p, "movement", f"movement.{k}", mv.get(k), lo, hi)
    for k in mv:
        if k in gdd_keys or k in MOVEMENT_RANGES or k in MOVEMENT_TEXT_KEYS:
            continue
        if m["fast_fall_rejected"] and FAST_FALL_KEY.search(k):
            p.append(("movement", f"movement.{k}", "REJECTED in GDD 1.3 section 5A: no per-state gravity multiplier "
                                                   "and no fast fall; one gravity rule whenever lift is off"))
        elif not (m["lift_key"] and k == "lift_min"):
            p.append(("movement", f"movement.{k}", f"not a GDD {manifest.get('gdd_revision')} movement key or a listed "
                                                   "engineering key (the old % of screen keys are gone)"))
    if m["lift_key"]:
        # GDD SH1.0 SURV-05 / FLOW-33: lift = min_lift + (1 - min_lift) x clamp(active health / capacity)
        gdd_value(p, "movement.lift_min", mv.get("lift_min"), vals.get(m["lift_key"]), m["lift_key"])
        if "lift_by_tier" in mv:
            p.append(("gdd", "movement.lift_by_tier", "GDD SH1.0 lift follows active health continuously (SURV-05): use "
                                                       "lift_min, not health tiers"))
    lift = mv.get("lift_by_tier", {})
    tiers = [lift.get(t) for t in ("intact", "damaged", "critical")] if isinstance(lift, dict) else [None]
    if m["lift_key"]:
        pass
    elif not all(num(t) for t in tiers):
        p.append(("movement", "movement.lift_by_tier", "needs intact, damaged and critical numbers"))
    elif not feature_on(manifest, LIFT_LOSS_FEATURE):
        if any(abs(t - 1.0) > 1e-9 for t in tiers):
            p.append(("gdd", "movement.lift_by_tier", f"damage does not reduce lift (GDD 1.3 SURV-02, DEC-05): every tier "
                                                      f"is 1.0 while {LIFT_LOSS_FEATURE} is off"))
    elif not (1.0 >= tiers[0] >= tiers[1] >= tiers[2] >= LIFT_CRITICAL_MIN):
        p.append(("movement", "movement.lift_by_tier", f"must fall with integrity, 1.0 to >= {LIFT_CRITICAL_MIN}"))

    fg = data["forgiveness"]
    hb = fg.get("player_hurtbox_cm")
    if not (isinstance(hb, dict) and num(hb.get("w")) and num(hb.get("h")) and hb["w"] > 0 and hb["h"] > 0):
        p.append(("forgiveness", "forgiveness.player_hurtbox_cm", "needs {w, h} in cm: the gameplay collider is "
                                                                 "fixed data, never sized from the sprite (GDD 1.3 7A, 7C)"))
    if not (num(fg.get("bolt_hitbox_radius_cm")) and fg["bolt_hitbox_radius_cm"] > 0):
        p.append(("forgiveness", "forgiveness.bolt_hitbox_radius_cm", "needs a radius in cm (fixed collider data)"))
    for k, (lo, hi) in FORGIVENESS_RANGES.items():
        in_range(p, "forgiveness", f"forgiveness.{k}", fg.get(k), lo, hi)
    for k, key in m["feel_forgiveness"].items():
        gdd_value(p, f"forgiveness.{k}", fg.get(k), vals.get(key), key)
    t_bolt = tell_s(data, m["tell_event"])
    if num(t_bolt):
        gdd_value(p, f"{m['tell_event']}.telegraph_s", t_bolt, vals.get(m["tell_key"]), m["tell_key"])

    check_spacing(p, data, manifest)

    ez = data["easing"]
    if "linear" in ez.get("curves", []):
        p.append(("ease", "easing.curves", "linear is not a feel curve (only clock_hand_rotation may be linear)"))
    if ez.get("linear_allowed_for", []) not in ([], ["clock_hand_rotation"]):
        p.append(("ease", "easing.linear_allowed_for", "only clock_hand_rotation may be linear"))

    vfx = data["vfx"]
    systems = vfx.get("systems", {})
    if vfx.get("parent") not in systems:
        p.append(("vfx", "vfx.parent", "the parent hit-spark system must be in vfx.systems"))
    for name, s in systems.items():
        w = f"vfx.{name}"
        if s.get("renderer") != "sprite":
            p.append(("vfx", w, "sprite renderer only"))
        if s.get("fixed_bounds") is not True:
            p.append(("vfx", w, "fixed bounds required"))
        if s.get("effect_type") not in EFFECT_TYPES:
            p.append(("vfx", w, f"effect_type must be one of {sorted(EFFECT_TYPES)}"))
        elif name.startswith(GAMEPLAY_SYSTEM_PREFIXES) and s["effect_type"] != "gameplay":
            p.append(("vfx", w, "hit sparks and wind lines carry gameplay information: effect_type gameplay (never culled)"))
        if "parent" in s and s["parent"] not in systems:
            p.append(("vfx", w, f"parent {s['parent']} not in vfx.systems"))

    flags = set()
    ids = set()
    events = data["events"] if isinstance(data["events"], list) else []
    for ev in events:
        if not isinstance(ev, dict) or "id" not in ev:
            p.append(("schema", "events", "each event is an object with an id"))
            continue
        if ev["id"] in ids:
            p.append(("schema", ev["id"], "event id used twice"))
        ids.add(ev["id"])
        check_event(p, ev, data, flags)
    required = REQUIRED_EVENTS_BY_GDD.get((manifest or {}).get("gdd_revision"), REQUIRED_EVENTS_BY_GDD[tuning.LATEST])
    for missing in sorted(required - ids):
        p.append(("required", missing, "required event has no row"))
    for ev in data.get("events", []):
        if isinstance(ev, dict) and ev.get("id") in MVP_EVENTS and ev.get("mvp") is not True:
            p.append(("required", ev["id"], "is P0 in GDD 1.3 (clock-hit visual cue ON): set mvp true"))
    return p


def fields(data):
    """DA_Feel fields: one bool per event and cue, one float power per cue. Each field is also
    the console variable `feel.<Field>` in Development builds, so an A/B flip needs no re-cook."""
    g = data["global"]
    out = [f"float ShakePower = {g.get('ShakePower', 1.0)}    // cvar {CVAR_PREFIX}ShakePower",
           f"float SpringDrag = {g.get('spring_drag')}    // cvar {CVAR_PREFIX}SpringDrag",
           f"float SpringElasticity = {g.get('spring_elasticity')}    // cvar {CVAR_PREFIX}SpringElasticity"]
    for ev in data.get("events", []):
        out.append(f"bool {ev['flag']} = true    // {ev['id']}; cvar {CVAR_PREFIX}{ev['flag']}")
        for c in ev.get("cues", []):
            power = c["flag"][1:] + "Power"
            out.append(f"bool {c['flag']} = true    // {ev['id']} {c['kind']} rank {c['rank']}; cvar {CVAR_PREFIX}{c['flag']}")
            out.append(f"float {power} = {c.get('power', 1.0)}    // cvar {CVAR_PREFIX}{power}")
    return out


def read_rows(path):
    with open(path, newline="", encoding="utf-8") as fh:
        return list(csv.DictReader(fh))


def flag_owners(data):
    """flag -> id of the event that owns it."""
    out = {}
    for ev in data["events"]:
        out[ev["flag"]] = ev["id"]
        for c in ev["cues"]:
            out[c["flag"]] = ev["id"]
    return out


def cue_info(data, flag):
    """(event, cue) for a cue flag; (event, None) for an event flag; (None, None) if unknown."""
    for ev in data["events"]:
        if ev["flag"] == flag:
            return ev, None
        for c in ev["cues"]:
            if c["flag"] == flag:
                return ev, c
    return None, None


def git_commit_exists(sha):
    """True if sha names a commit in this repo."""
    try:
        r = subprocess.run(["git", "rev-parse", "--verify", "--quiet", f"{sha}^{{commit}}"],
                           cwd=ROOT, capture_output=True, text=True)
    except OSError:
        return False
    return r.returncode == 0


def people(brief_text):
    """[(role, [names], confirmed)] from the docs/jam-brief.md People table (check_card.py parsing)."""
    if os.path.join(ROOT, "tools") not in sys.path:
        sys.path.insert(0, os.path.join(ROOT, "tools"))
    import check_card  # noqa: E402  (shared People parsing; never copied)
    out = []
    for r in check_card.table_rows(check_card.section(brief_text, "People")):
        if len(r) >= 3:
            out.append((r[0], check_card.person_names(r[1]), r[2].strip().lower() == "yes" and "(proposed" not in r[1]))
    return out


def design_owners(brief_text):
    """Lower-case names in the confirmed 'Game design owner' People row."""
    return {n for role, names, ok in people(brief_text) if ok and role.lower().startswith(DESIGN_OWNER_ROLE) for n in names}


def humans(brief_text):
    """Every confirmed person in the People table."""
    return {n for _, names, ok in people(brief_text) if ok for n in names}


def read_text(path):
    try:
        with open(path, encoding="utf-8") as fh:
            return fh.read()
    except OSError:
        return ""


def signer_problem(flag, who, signers):
    if not signers:
        return ("ab", flag, "docs/jam-brief.md People has no confirmed 'Game design owner'; card 0.0 fills it")
    if who.lower().lstrip("@") not in signers:
        return ("ab", flag, f"signed_by '{who}' is not the game design owner in docs/jam-brief.md People; agents never sign")
    return None


def ab_problems(flag, rows, owner, signers=frozenset(), commit_exists=git_commit_exists):
    p = []
    for r in rows:
        if owner and (r.get("event") or "").strip() != owner:
            p.append(("ab", flag, f"event column is '{(r.get('event') or '').strip()}'; {flag} belongs to {owner}"))
        if not (r.get("on_note") or "").strip() or not (r.get("off_note") or "").strip():
            p.append(("ab", flag, "on_note and off_note both need what the player did or said"))
        if (r.get("verdict") or "").strip() not in AB_VERDICTS:
            p.append(("ab", flag, f"verdict must be one of {sorted(AB_VERDICTS)}"))
        who = (r.get("signed_by") or "").strip()
        if not who:
            p.append(("ab", flag, "signed_by is empty (the game design owner signs)"))
        else:
            bad = signer_problem(flag, who, signers)
            if bad:
                p.append(bad)
        sha = (r.get("build_sha") or "").strip().lower()
        if not SHA_RE.match(sha):
            p.append(("ab", flag, "build_sha must be a commit sha"))
        elif not commit_exists(sha):
            p.append(("ab", flag, f"build_sha {sha} is not a commit in this repo"))
    return p


def check_ab(data, flag, path, signers=frozenset(), commit_exists=git_commit_exists):
    """A feel card is done when its flag has an on/off row in the A/B log, signed by the game design owner."""
    owners = flag_owners(data)
    if flag not in owners:
        return [("ab", flag, "flag is not in feel.json")]
    all_rows = read_rows(path)
    rows = [r for r in all_rows if (r.get("flag") or "").strip() == flag]
    if rows:
        return ab_problems(flag, rows, owners[flag], signers, commit_exists)
    # One row per event covers its MVP cues: a rank 1-2 cue may lean on its event flag's row.
    ev, c = cue_info(data, flag)
    if c is not None and isinstance(c.get("rank"), int) and c["rank"] <= MVP_RANK:
        ev_rows = [r for r in all_rows if (r.get("flag") or "").strip() == ev["flag"]]
        if ev_rows:
            return ab_problems(ev["flag"], ev_rows, ev["id"], signers, commit_exists)
        return [("ab", flag, f"no on/off row for {flag} or its event flag {ev['flag']} in {os.path.relpath(path, ROOT)}")]
    why = "rank 3+ cues need their own row" if c is not None else "event flags need their own row"
    return [("ab", flag, f"no on/off row in {os.path.relpath(path, ROOT)} ({why})")]


def check_protected(data, path, signers=frozenset(), commit_exists=git_commit_exists):
    """A CUT_NEEDS_AB cue left feel.json: there must be a signed A/B row with verdict cut."""
    owners = flag_owners(data)
    p = []
    for flag in sorted(CUT_NEEDS_AB - set(owners)):
        rows = [r for r in read_rows(path) if (r.get("flag") or "").strip() == flag]
        cut = [r for r in rows if (r.get("verdict") or "").strip() == "cut"]
        if not cut:
            p.append(("ab", flag, "removed from feel.json without a signed A/B row with verdict cut"))
        else:
            p += ab_problems(flag, cut, None, signers, commit_exists)
    return p


def spec_test_names(spec_text):
    """Every UmbrellaElla.* engine test named in the feel spec."""
    return sorted(set(TEST_NAME_RE.findall(spec_text)))


def check_test_map(spec_text, map_text):
    """Each engine test the feel spec names has a row in the test map, so the daily build can require it
    once its card merges (check_automation_report.py --test-map)."""
    names = spec_test_names(spec_text)
    if not names:
        return [("testmap", "docs/feel-spec.md", "names no UmbrellaElla.* engine test")]
    rows = [ln for ln in map_text.splitlines() if ln.strip().startswith("|")]
    p = []
    for n in names:
        hits = [ln for ln in rows if n in TEST_NAME_RE.findall(ln)]
        if not hits:
            p.append(("testmap", n, "named in docs/feel-spec.md but has no row in pipeline/qa/test-map.md"))
        elif ".World." not in n and not any(re.search(re.escape(n) + r"`?\s*\(world\)", ln) for ln in hits):
            p.append(("testmap", n, "spawns actors: mark it (world) in the test map, or the 1 s rule-test limit fails it"))
    return p


def test_map_rows(spec_text):
    """The planned test-map rows for every engine test the feel spec names, ready to paste."""
    out = []
    for n in spec_test_names(spec_text):
        mark = "" if ".World." in n else " (world)"
        out.append(f"| Feel | – | `{n}`{mark} | | planned |")
    return out


def check_arena(data, path, people_names, commit_exists=git_commit_exists):
    """Feel was tuned in the arena with real threats: one signed L_Graybox run with the arena patterns and cues on."""
    try:
        rows = read_rows(path)
    except OSError as e:
        return [("arena", path, str(e))]
    want = set(data.get("threat_spacing", {}).get("arena_patterns", []))
    p = []
    for i, r in enumerate(rows, 2):
        w = f"{os.path.basename(path)}:{i}"
        bad = []
        if (r.get("map") or "").strip() != SPACING_ARENA:
            bad.append(f"map must be {SPACING_ARENA}")
        if (r.get("gate") or "").strip() not in GATES:
            bad.append(f"gate must be one of {sorted(GATES)}")
        got = {x.strip() for x in (r.get("patterns") or "").split(";") if x.strip()}
        if not want or not want <= got:
            bad.append(f"patterns must list {sorted(want)} (threat_spacing.arena_patterns), ';' between")
        if (r.get("cues_on") or "").strip().lower() != "yes":
            bad.append("cues_on must be yes (played with the feel cues on)")
        if not (r.get("note") or "").strip():
            bad.append("note needs what the player did or said")
        sha = (r.get("build_sha") or "").strip().lower()
        if not SHA_RE.match(sha):
            bad.append("build_sha must be a commit sha")
        elif not commit_exists(sha):
            bad.append(f"build_sha {sha} is not a commit in this repo")
        who = (r.get("played_by") or "").strip().lower().lstrip("@")
        if not people_names:
            bad.append("docs/jam-brief.md People has no confirmed person yet; card 0.0 fills it")
        elif who not in people_names:
            bad.append(f"played_by '{who}' is not a confirmed person in docs/jam-brief.md People; an agent cannot play")
        p += [("arena", w, b) for b in bad]
    if not rows:
        p.append(("arena", os.path.relpath(path, ROOT) if path.startswith(ROOT) else path,
                  f"no {SPACING_ARENA} run logged; needed before G2 (docs/feel-spec.md section 8b)"))
    return p


def check_gate(gate, build, path):
    """A gate build has a 240 fps key-to-screen latency row under the fail line."""
    if gate not in GATES:
        return [("gate", gate, f"gate must be one of {sorted(GATES)}")]
    build = (build or "").strip().lower()
    if not SHA_RE.match(build):
        return [("gate", gate, f"--build '{build}' is not a commit sha (7-40 hex characters)")]

    def same(sha):
        sha = (sha or "").strip().lower()
        return bool(SHA_RE.match(sha)) and (sha.startswith(build) or build.startswith(sha))
    rows = [r for r in read_rows(path) if r.get("gate") == gate and same(r.get("build_sha"))]
    if not rows:
        return [("gate", gate, f"no latency row for build {build} in {os.path.relpath(path, ROOT)}")]
    p = []
    for r in rows:
        try:
            med, presses = float(r["median_ms"]), int(r["presses"])
        except (KeyError, TypeError, ValueError):
            p.append(("gate", gate, "median_ms and presses must be numbers"))
            continue
        if "240" not in (r.get("method") or ""):
            p.append(("gate", gate, "method must be a 240 fps (or faster) capture"))
        if presses < 10:
            p.append(("gate", gate, f"{presses} presses; measure at least 10"))
        if med > LATENCY_FAIL_MS:
            p.append(("gate", gate, f"median {med:.0f} ms > fail line {LATENCY_FAIL_MS} ms"))
        elif med > LATENCY_TARGET_MS:
            print(f"note [gate] {gate}: median {med:.0f} ms is over the {LATENCY_TARGET_MS} ms target (passes; open a TD card)")
        if not (r.get("measured_by") or "").strip():
            p.append(("gate", gate, "measured_by is empty"))
        try:
            peak, bolts = float(r["peak_frame_ms"]), int(r["peak_bolts"])
        except (KeyError, TypeError, ValueError):
            p.append(("gate", gate, "peak_frame_ms and peak_bolts must be numbers (stat unit at peak bullet count)"))
            continue
        if bolts < 1:
            p.append(("gate", gate, "peak_bolts must be the live bolt count at the capture (>= 1)"))
        if peak > PEAK_FRAME_MAX_MS:
            p.append(("gate", gate, f"peak frame {peak:.1f} ms > smoke budget {PEAK_FRAME_MAX_MS} ms"))
        elif peak > PEAK_FRAME_TARGET_MS:
            print(f"note [gate] {gate}: peak frame {peak:.1f} ms is over {PEAK_FRAME_TARGET_MS} ms (60 fps); passes")
    return p


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--feel", default=FEEL)
    ap.add_argument("--fields", action="store_true")
    ap.add_argument("--ab", metavar="FLAG")
    ap.add_argument("--ab-log", default=AB_LOG)
    ap.add_argument("--gate", choices=sorted(GATES))
    ap.add_argument("--build", default="")
    ap.add_argument("--latency-log", default=LATENCY_LOG)
    ap.add_argument("--test-map", nargs="?", const=TEST_MAP, metavar="FILE",
                    help="every engine test in --spec has a row in this test map")
    ap.add_argument("--spec", default=SPEC)
    ap.add_argument("--test-map-rows", action="store_true", help="print the planned test-map rows to paste")
    ap.add_argument("--arena", action="store_true", help="the arena log has a signed L_Graybox run")
    ap.add_argument("--arena-log", default=ARENA_LOG)
    ap.add_argument("--brief", default=JAM_BRIEF, help="docs/jam-brief.md (People table: who signs and plays)")
    a = ap.parse_args(argv)
    if a.test_map_rows:
        print("\n".join(test_map_rows(read_text(a.spec))))
        return 0
    try:
        with open(a.feel, encoding="utf-8") as fh:
            data = json.load(fh)
    except (OSError, ValueError) as e:
        print(f"[schema] {a.feel}: {e}")
        print("feel_check: 1 problem(s)")
        return 1
    problems = check(data)
    problems += [("baked", tuning.STAMP, x) for x in tuning.baked_vs_sim_problems(ROOT, feel=data)]
    brief = read_text(a.brief)
    if not problems and a.fields:
        print("\n".join(fields(data)))
    if not problems:
        problems += check_protected(data, a.ab_log, design_owners(brief))
    if not problems and a.ab:
        problems += check_ab(data, a.ab, a.ab_log, design_owners(brief))
    if not problems and (a.arena or a.gate in ("G2", "G3", "G4")):
        problems += check_arena(data, a.arena_log, humans(brief))
    if a.gate:
        if not a.build:
            problems.append(("gate", a.gate, "--gate needs --build SHA"))
        else:
            problems += check_gate(a.gate, a.build, a.latency_log)
    if a.test_map:
        try:
            with open(a.spec, encoding="utf-8") as fh:
                spec_text = fh.read()
            with open(a.test_map, encoding="utf-8") as fh:
                map_text = fh.read()
            problems += check_test_map(spec_text, map_text)
        except OSError as e:
            problems.append(("testmap", a.test_map, str(e)))
    for rule, where, why in problems:
        print(f"[{rule}] {where}: {why}")
    n = len(data.get("events", [])) if isinstance(data, dict) else 0
    print(f"feel_check: {n} event(s), {len(problems)} problem(s)")
    return 1 if problems else 0


if __name__ == "__main__":
    sys.exit(main())
