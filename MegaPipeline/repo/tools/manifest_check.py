#!/usr/bin/env python3
"""Feature manifest gate (docs/feature-manifest.json). GDD B section 5 and Appendix B are the spec. Stdlib only.

Checks:
  schema      every record has the fields below with the right types; status and priority from the manifest's
              own vocabulary lists, which must be exactly the GDD B status words
  unique      feature IDs are unique and look like CORE-01 / UMB-02 / ...
  resolve     every requires / conflicts entry is a feature ID or a module key (GDD B section 4); never itself
  events      every emits entry is in the event vocabulary
  gdd         every feature ID and QA ID cited in the current snapshot (docs/gdd/CURRENT) is in the manifest,
              and every manifest feature ID and test ID is cited in the snapshot; gdd_revision matches it
  authorized  implementation_authorized is true only for APPROVED_P0 / APPROVED_P1, or EXPERIMENT with a named
              ticket (#<n> or UE-<n>)
  flag        a CONFIRMED record has flag null; every other record has flag = its ID with '_' (UMB-02 -> UMB_02)
  params      build_parameters (e.g. camera_mode): a default that is one of its allowed values, and a status word
  presets     pipeline/qa/presets.json: preset IDs equal the T- IDs in the snapshot; enabled features exist and are
              implementation_authorized; BASE (T-01) has empty enable and disable lists (dry run B H6)
  gdd-status  each record's status equals the status word the snapshot states for it (the first status word in
              the last cell of the table row that starts with the ID; dry run B C1: a demoted or promoted
              record fails). A row that says OFF needs default_enabled false; "no implementation authority"
              needs implementation_authorized false. An ID with no stated status may not be authorized, on, or
              APPROVED_*/CONFIRMED. priority P0 goes with APPROVED_P0 and only with it
  p0-on       every APPROVED_P0 record has default_enabled true (GDD 1.3 section 5: the BASE preset loads all P0),
              unless a DECIDED row in docs/decisions.md says `Overrides: <ID>` (decided_overrides; bake_preset agrees)
  approved    approved_parameters equals the snapshot's section 5A tables: every 5A row maps to one key (PARAM_ROWS),
              and start, step, min and max match the printed row. A new 5A row with no mapping fails too. Every entry
              traces to a 5A row or one quoted GDD sentence (PROSE_ROWS), and holds no number the GDD does not print;
              any other key or field fails (final-8 B C2)

  pin         gdd_snapshots pins every docs/gdd/GDD-*.md by sha256 (line endings normalized); CURRENT names
              gdd_snapshot; --pins-from BASE.json (CI: the base branch's manifest) fails a changed or dropped pin
  rules-pin   rules_pdf pins docs/rules/*.pdf (the Official Rules, the top source for jam rules) by sha256: the file,
              or its Git LFS pointer's oid in a checkout without LFS, matches the pin, and the sha256 line in
              docs/rules/official-rules.md's header equals it. A changed PDF with no pin update fails
  off         default_enabled true needs implementation_authorized true and an APPROVED status (dry run B C1)
  overrides   a row with an `Overrides:` clause that is DECIDED but does not count (decided_overrides) fails
  grace       a 2 h grace default row (pipeline/human-checkpoints.md): Status exactly `DECIDED <date> (agent default
              after 2h grace; <role>; human may overturn)` with a GRACE_ROLES role, in the Open decisions table, linking
              the needs-human issue; never on a human-only kind (grace_kind) and never an Overrides row (P0 is the design owner's)

  --note FILE  checks one tester note (JSON, GDD B Appendix C; pipeline/templates/test-note.md) instead

Usage: python3 tools/manifest_check.py [--root PATH] [--manifest FILE] [--note FILE]
Exit 0 = clean, 1 = problems, 2 = unreadable input.
"""
import argparse
import hashlib
import json
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import gdd_impact  # noqa: E402

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MANIFEST = "docs/feature-manifest.json"
CURRENT = "docs/gdd/CURRENT"
PRESETS = "pipeline/qa/presets.json"
STATUSES = list(gdd_impact.STATUSES)
AUTHORIZED = {"APPROVED_P0", "APPROVED_P1"}
FIELDS = {  # field -> allowed types
    "feature_id": (str,), "name": (str,), "status": (str,), "owner": (str,), "priority": (str,),
    "default_enabled": (bool,), "requires": (list,), "conflicts": (list,), "parameters": (list,),
    "emits": (list,), "tests": (list,), "implementation_authorized": (bool,), "gdd_revision": (str,),
    "known_limitations": (list,), "flag": (str, type(None)), "ticket": (str, type(None)), "status_text": (str,),
}
# Optional: "sounds" = the pipeline/audio/sound-list.csv ids that are this feature's sounds. For an APPROVED_P0
# feature, audio_check.py reads its sound tiers from here, not from the sound row's own gdd cell (final-7 dry run B H2).
OPTIONAL_FIELDS = {"sounds": (list,)}
TICKET = re.compile(r"#\d+|\bUE-\d+(?:\.\d+[a-z]?)?\b")
QA_ID = re.compile(r"(?<![\w-])QA-\d{2}(?![\w-])")
PRESET_ID = re.compile(r"(?<![\w-])T-\d{2}(?![\w-])")
# GDD 1.3 section 5A row label -> approved_parameters key. A gate table: a new revision that adds or renames a
# 5A row fails until this map names it.
PARAM_ROWS = {
    "Horizontal maximum speed": "CORE-01.move_speed",
    "Horizontal acceleration": "CORE-01.move_accel",
    "Gravity magnitude": "CORE-02.gravity",
    "Maximum natural fall speed": "CORE-02.max_fall_speed",
    "UP_OPEN ascent target speed": "UMB-01.ascent_speed",
    "Acceleration toward ascent speed": "UMB-01.ascent_accel",
    "Open-horizontal steering multiplier": "CORE-01.open_steer_multiplier",
    "Optional dash speed (OFF)": "MOVE-03.dash_speed",
    "Optional dash duration (OFF)": "MOVE-03.dash_duration",
    "Player attack interval": "COM-01.cadence",
    "Player bolt travel speed": "COM-01.bolt_speed",
    "Owl bolt travel speed": "OWL-01.projectile_speed",
    "Owl warning duration": "OWL-01.telegraph_delay",
    "Owl attack interval": "OWL-01.cadence",
    "Player maximum health": "CORE-03.max_health",
    "Owl bolt damage": "CORE-03.bolt_damage",
    "Successful front absorption healing": "SURV-03.restore_amount",
    "Healing cooldown after success": "SURV-03.heal_cooldown_s",
    "Post-hit invulnerability": "CORE-03.invulnerability_s",
    "Shield frontal interception arc": "DEF-01.shield_arc_deg",
    "Wind upward velocity contribution": "WIND-01.gust_force",
    "Wind active interval": "WIND-01.active_s",
    "Wind wear when option enabled": "WIND-02.wind_wear",
    "Survival/departure timer": "END-01.survival_s",
    "Master audio volume": "FLOW-01.master_volume",
    "Animation playback (core loops)": "ANIM-01.fps",
    "Far background slide speed": "BG-01.far_speed",
    "Near background slide speed": "BG-01.near_speed",
    "Random seed: owl test fixture": "OWL-01.seed",
}
# Final-8 B C2: an approved value the 5A tables do not print traces to one GDD sentence instead. The sentence must be
# in the snapshot, its number is the start, and the entry has no range (the GDD prints none). Nothing else may be in
# approved_parameters.
PROSE_ROWS = {
    # GDD 1.3 (history; a key only counts when approved_parameters holds it)
    "OWL-01.initial_grace_s": r"allow a (" + r"[-+]?\d+(?:\.\d+)?" + r")-second configurable initial grace interval",
    # GDD SH1.0: its section 9 parameter tables are blank, so every approved start traces to one printed sentence
    # (D-new-sh10-param-ranges). One capture group each, the start; no range or step.
    "MOVE-21.rise_speed": 'rise / fall / free fall = (\\d+(?:\\.\\d+)?) / \\d+(?:\\.\\d+)? / \\d+(?:\\.\\d+)? units/s',
    "MOVE-21.fall_speed": 'rise / fall / free fall = \\d+(?:\\.\\d+)? / (\\d+(?:\\.\\d+)?) / \\d+(?:\\.\\d+)? units/s',
    "MOVE-21.free_fall_speed": 'rise / fall / free fall = \\d+(?:\\.\\d+)? / \\d+(?:\\.\\d+)? / (\\d+(?:\\.\\d+)?) units/s',
    "MOVE-21.horizontal_max_speed": 'horizontal maximum (\\d+(?:\\.\\d+)?) units/s',
    "MOVE-21.vertical_trim_pct": 'units/s; vertical trim (\\d+(?:\\.\\d+)?)%',
    "MOVE-21.hop_distance": 'Hop = (\\d+(?:\\.\\d+)?) units over',
    "MOVE-21.hop_duration_s": 'Hop = \\d+(?:\\.\\d+)? units over (\\d+(?:\\.\\d+)?)s',
    "MOVE-21.hop_cooldown_s": 'Hop = \\d+(?:\\.\\d+)? units over \\d+(?:\\.\\d+)?s, (\\d+(?:\\.\\d+)?)s cooldown',
    "MOVE-21.hop_protection_s": 's cooldown, (\\d+(?:\\.\\d+)?)s protection',
    "MOVE-21.dash_distance": 'Falling dash = (\\d+(?:\\.\\d+)?) units over',
    "MOVE-21.dash_duration_s": 'Falling dash = \\d+(?:\\.\\d+)? units over (\\d+(?:\\.\\d+)?)s',
    "MOVE-21.dash_cooldown_s": 'Falling dash = \\d+(?:\\.\\d+)? units over \\d+(?:\\.\\d+)?s, (\\d+(?:\\.\\d+)?)s cooldown',
    "MOVE-21.free_fall_dash_multiplier": 'free-fall dash distance ×(\\d+(?:\\.\\d+)?)',
    "MOVE-22.wind_acceleration": 'Wind response baseline: acceleration(\\d+(?:\\.\\d+)?)',
    "MOVE-22.wind_open_decay": 'open decay(\\d+(?:\\.\\d+)?), falling decay',
    "MOVE-22.wind_falling_decay": 'open decay\\d+(?:\\.\\d+)?, falling decay(\\d+(?:\\.\\d+)?)',
    "SURV-05.min_lift": 'Minimum lift(\\d+(?:\\.\\d+)?) and post-hit protection',
    "SURV-05.post_hit_protection_s": 'post-hit protection(\\d+(?:\\.\\d+)?)s remain',
    "UMB-05.absorb_range": 'forward range(\\d+(?:\\.\\d+)?) units',
    "UMB-05.absorb_cone_deg": 'full cone(\\d+(?:\\.\\d+)?)°, pull speed',
    "UMB-05.pull_speed": 'pull speed(\\d+(?:\\.\\d+)?), capture distance',
    "UMB-05.capture_distance": 'capture distance(\\d+(?:\\.\\d+)?)\\. Eligible',
    "UMB-05.heal_per_yellow": 'heals active health by(\\d+(?:\\.\\d+)?) \\+',
    "UMB-05.heal_per_recovery_rank": 'heals active health by\\d+(?:\\.\\d+)? \\+(\\d+(?:\\.\\d+)?) per applied',
    "COM-06.shots_per_s": 'Repeated distinct traveling shots: (\\d+(?:\\.\\d+)?) shots/s',
    "COM-06.damage": 'traveling shots: \\d+(?:\\.\\d+)? shots/s, damage (\\d+(?:\\.\\d+)?)',
    "COM-06.speed": 'shots/s, damage \\d+(?:\\.\\d+)?, speed (\\d+(?:\\.\\d+)?) units/s, range',
    "COM-06.range": 'shots/s, damage \\d+(?:\\.\\d+)?, speed \\d+(?:\\.\\d+)? units/s, range (\\d+(?:\\.\\d+)?)',
    "COM-07.ticks_per_s": 'Growing continuous beam: (\\d+(?:\\.\\d+)?) damage ticks/s',
    "COM-07.tick_damage": 'damage ticks/s at damage (\\d+(?:\\.\\d+)?)',
    "COM-07.growth_speed": 'growth (\\d+(?:\\.\\d+)?) units/s, maximum range',
    "COM-07.max_range": 'maximum range (\\d+(?:\\.\\d+)?), width',
    "COM-07.width": 'maximum range \\d+(?:\\.\\d+)?, width (\\d+(?:\\.\\d+)?)',
    "COM-08.separation": 'separated vertically by (\\d+(?:\\.\\d+)?) units',
    "COM-08.volleys_per_s": 'by \\d+(?:\\.\\d+)? units: (\\d+(?:\\.\\d+)?) volleys/s',
    "COM-08.damage": 'volleys/s, damage (\\d+(?:\\.\\d+)?) each',
    "COM-08.speed": 'damage \\d+(?:\\.\\d+)? each, speed (\\d+(?:\\.\\d+)?)',
    "COM-08.range": 'damage \\d+(?:\\.\\d+)? each, speed \\d+(?:\\.\\d+)?, range (\\d+(?:\\.\\d+)?)',
    "COM-09.shots_per_s": '\\| (\\d+(?:\\.\\d+)?) shots/s, damage 14',
    "COM-09.damage": 'shots/s, damage (\\d+(?:\\.\\d+)?), speed 1000',
    "COM-09.speed": 'damage 14, speed (\\d+(?:\\.\\d+)?)',
    "COM-09.range": 'speed 1000, range (\\d+(?:\\.\\d+)?)',
    "COM-09.size_multiplier": 'size multiplier (\\d+(?:\\.\\d+)?)',
    "FLOW-05.hp_multiplier_cap": 'Enemy and boss HP multiplier=min\\((\\d+(?:\\.\\d+)?)',
    "FLOW-05.hp_multiplier_step": 'HP multiplier=min\\(\\d+(?:\\.\\d+)?,1\\+(\\d+(?:\\.\\d+)?)C\\)',
    "FLOW-05.cadence_multiplier_cap": 'firing-cadence multiplier=min\\((\\d+(?:\\.\\d+)?)',
    "FLOW-05.cadence_multiplier_step": 'cadence multiplier=min\\(\\d+(?:\\.\\d+)?,1\\+(\\d+(?:\\.\\d+)?)C\\)',
    "FLOW-05.count_multiplier_cap": 'base count ×min\\((\\d+(?:\\.\\d+)?)',
    "FLOW-05.count_multiplier_step": 'base count ×min\\(\\d+(?:\\.\\d+)?,1\\+(\\d+(?:\\.\\d+)?)C\\)',
    "FLOW-06.final_hour_hp_multiplier": 'enemy/boss HP×(\\d+(?:\\.\\d+)?)',
    "FLOW-06.final_hour_cadence_multiplier": 'ordinary firing cadence×(\\d+(?:\\.\\d+)?)',
    "FLOW-06.final_hour_count_multiplier": 'eligible enemy-count target×(\\d+(?:\\.\\d+)?)',
    "FLOW-15.start_hits_per_life": 'Director’s Cut starts at (\\d+(?:\\.\\d+)?) hits per life',
    "FLOW-15.start_lives": 'Director’s Cut starts at \\d+(?:\\.\\d+)? hits per life and (\\d+(?:\\.\\d+)?) lives',
    "FLOW-15.max_hits_per_life": 'up to (\\d+(?:\\.\\d+)?) hits per life and',
    "FLOW-15.max_lives": 'up to \\d+(?:\\.\\d+)? hits per life and (\\d+(?:\\.\\d+)?) lives',
    "FLOW-15.level_cap": 'level cap(\\d+(?:\\.\\d+)?) gives',
    "FLOW-15.earned_points_at_cap": 'level cap\\d+(?:\\.\\d+)? gives(\\d+(?:\\.\\d+)?) earned stat points',
    "FLOW-15.xp_curve_base": 'advancing from current level L costs(\\d+(?:\\.\\d+)?) \\+floor',
    "FLOW-15.cumulative_xp_level_10": 'Cumulative XP is(\\d+(?:\\.\\d+)?) at level10',
    "FLOW-15.cumulative_xp_level_20": 'at level10,(\\d+(?:\\.\\d+)?) at20',
    "FLOW-15.cumulative_xp_level_30": 'at20,(\\d+(?:\\.\\d+)?) at30',
    "FLOW-15.cumulative_xp_level_62": 'at30 and(\\d+(?:\\.\\d+)?) at62',
    "FLOW-15.target_xp_per_run": 'assumes roughly(\\d+(?:\\.\\d+)?) credited XP per completed run',
    "FLOW-15.target_completed_runs": 'around(\\d+(?:\\.\\d+)?) completed Director’s Cut runs to reach level62',
    "FLOW-16.unlock_level_streamed": 'Streamed Blast at level(\\d+(?:\\.\\d+)?)',
    "FLOW-16.unlock_level_twin": 'Twin Stars at level(\\d+(?:\\.\\d+)?)',
    "FLOW-16.unlock_level_needle": 'Needle Spell at level(\\d+(?:\\.\\d+)?)\\. Unlock',
    "FLOW-19.xp_roadwarden": 'Roadwarden / Floodstrider / ordinary Courier =(\\d+(?:\\.\\d+)?)',
    "FLOW-19.xp_floodstrider": 'ordinary Courier =\\d+(?:\\.\\d+)? /(\\d+(?:\\.\\d+)?)',
    "FLOW-19.xp_courier": 'ordinary Courier =\\d+(?:\\.\\d+)? /\\d+(?:\\.\\d+)? /(\\d+(?:\\.\\d+)?) XP',
    "FLOW-19.xp_wings": 'wings / front / middle / rear / clock are(\\d+(?:\\.\\d+)?)',
    "FLOW-19.xp_front": 'clock are\\d+(?:\\.\\d+)? /(\\d+(?:\\.\\d+)?)',
    "FLOW-19.xp_middle": 'clock are\\d+(?:\\.\\d+)? /\\d+(?:\\.\\d+)? /(\\d+(?:\\.\\d+)?)',
    "FLOW-19.xp_rear": 'clock are\\d+(?:\\.\\d+)? /\\d+(?:\\.\\d+)? /\\d+(?:\\.\\d+)? /(\\d+(?:\\.\\d+)?)',
    "FLOW-19.xp_clock": 'clock are\\d+(?:\\.\\d+)? /\\d+(?:\\.\\d+)? /\\d+(?:\\.\\d+)? /\\d+(?:\\.\\d+)? /(\\d+(?:\\.\\d+)?)',
    "FLOW-24.chunk_length": 'Chunk length baseline(\\d+(?:\\.\\d+)?) units',
    "FLOW-33.projectile_damage": 'projectile and hostile gust damage is(\\d+(?:\\.\\d+)?) health',
    "FLOW-33.trap_damage": 'physical trap hits also start at(\\d+(?:\\.\\d+)?)',
    "FLOW-33.chain_damage": 'Chain-head damage is(\\d+(?:\\.\\d+)?)',
    "FLOW-33.talon_damage": 'and talon damage(\\d+(?:\\.\\d+)?)\\. This divides',
    "FLOW-33.old_damage_divisor": 'former incoming8/10/12 values by(\\d+(?:\\.\\d+)?)',
    "OWL-08.wings_hp": 'Shared wings (\\d+(?:\\.\\d+)?) HP',
    "OWL-08.front_hp": 'front / middle / rear (\\d+(?:\\.\\d+)?) / ',
    "OWL-08.middle_hp": 'front / middle / rear \\d+(?:\\.\\d+)? / (\\d+(?:\\.\\d+)?) / ',
    "OWL-08.rear_hp": 'front / middle / rear \\d+(?:\\.\\d+)? / \\d+(?:\\.\\d+)? / (\\d+(?:\\.\\d+)?);',
    "OWL-08.clock_hp": '; clock (\\d+(?:\\.\\d+)?) with protected',
    "OWL-08.clock_reserve_hp": 'protected 40% reserve \\((\\d+(?:\\.\\d+)?) HP\\)',
    "OWL-11.red_spacing_s": 'spacing(\\d+(?:\\.\\d+)?)s; wing/mechanism/clock spreads',
    "OWL-11.red_spread_wings_deg": 'spreads(\\d+(?:\\.\\d+)?)°/effective',
    "OWL-11.red_spread_mechanisms_deg": 'spreads\\d+(?:\\.\\d+)?°/effective(\\d+(?:\\.\\d+)?)°',
    "OWL-11.red_spread_clock_deg": 'spreads\\d+(?:\\.\\d+)?°/effective\\d+(?:\\.\\d+)?°/(\\d+(?:\\.\\d+)?)°',
    "OWL-11.red_speed_wings": 'speeds(\\d+(?:\\.\\d+)?)/\\d+(?:\\.\\d+)?/\\d+(?:\\.\\d+)?, normal interval',
    "OWL-11.red_speed_mechanisms": 'speeds\\d+(?:\\.\\d+)?/(\\d+(?:\\.\\d+)?)/\\d+(?:\\.\\d+)?, normal interval',
    "OWL-11.red_speed_clock": 'speeds\\d+(?:\\.\\d+)?/\\d+(?:\\.\\d+)?/(\\d+(?:\\.\\d+)?), normal interval',
    "OWL-11.red_interval_s": 'normal interval(\\d+(?:\\.\\d+)?)s\\.',
    "OWL-11.reduced_interval_s": 'interval×1\\.6 \\((\\d+(?:\\.\\d+)?) world seconds\\)',
    "OWL-13.yellow_speed_wings": 'speeds (\\d+(?:\\.\\d+)?) / \\d+(?:\\.\\d+)? / \\d+(?:\\.\\d+)? by act',
    "OWL-13.yellow_speed_mechanisms": 'speeds \\d+(?:\\.\\d+)? / (\\d+(?:\\.\\d+)?) / \\d+(?:\\.\\d+)? by act',
    "OWL-13.yellow_speed_clock": 'speeds \\d+(?:\\.\\d+)? / \\d+(?:\\.\\d+)? / (\\d+(?:\\.\\d+)?) by act',
    "OWL-13.yellow_interval_s": 'independent (\\d+(?:\\.\\d+)?)s cadence',
    "OWL-13.yellow_size": 's cadence, size (\\d+(?:\\.\\d+)?)×',
    "OWL-15.physical_interval_s": 'shared physical scheduler \\((\\d+(?:\\.\\d+)?)s from attack start\\)',
    "OWL-15.gust_warning_s": 'Lock altitude for a (\\d+(?:\\.\\d+)?)s warning',
    "OWL-16.gust_speed": 'front travels left at (\\d+(?:\\.\\d+)?) units/s',
    "OWL-16.gust_band_width": 'full band width (\\d+(?:\\.\\d+)?)',
    "OWL-16.gust_lifetime_s": 'full band width \\d+(?:\\.\\d+)?, lifetime (\\d+(?:\\.\\d+)?)s',
    "OWL-16.gust_push": 'damage1 health and push(\\d+(?:\\.\\d+)?)\\. It bypasses',
    "OWL-18.talon_reach": 'Trigger / lock: within (\\d+(?:\\.\\d+)?)-unit reach',
    "OWL-18.talon_warning_s": 'during warning or strike\\. Warning (\\d+(?:\\.\\d+)?)s',
    "OWL-19.talon_tip_width": 'actual tip width (\\d+(?:\\.\\d+)?) sweeps',
    "OWL-19.talon_strike_s": 'captured target over(\\d+(?:\\.\\d+)?)s',
    "OWL-20.talon_recovery_s": 'quiet recovery (\\d+(?:\\.\\d+)?)s; cooldown',
    "OWL-20.talon_cooldown_s": 's; cooldown (\\d+(?:\\.\\d+)?)s from commitment',
    "OWL-20.talon_rearm_exit": 'after leaving beyond (\\d+(?:\\.\\d+)?) units',
    "OWL-21.cast_warning_s": 'destination during (\\d+(?:\\.\\d+)?)s warning',
    "OWL-22.chain_reach": 'reach (\\d+(?:\\.\\d+)?) from its starting point',
    "OWL-22.chain_speed": 'straight-distance speed basis (\\d+(?:\\.\\d+)?) units/s',
    "OWL-22.chain_head_width": 'units/s, full width(\\d+(?:\\.\\d+)?)',
    "OWL-23.chain_return_s": 'harmless return home over (\\d+(?:\\.\\d+)?)s',
    "OWL-24.middle_offset": 'with ±(\\d+(?:\\.\\d+)?)-unit sine offset',
    "OWL-26.rear_pause_s": 'stops for a SAFE (\\d+(?:\\.\\d+)?)s midpoint',
    "OWL-28.repeat_wait_s": 'after its last shot wait (\\d+(?:\\.\\d+)?)s',
    "OWL-28.repeat_recovery_s": 'Keep at least (\\d+(?:\\.\\d+)?)s recovery after the repeat',
    "OWL-29.clock_open_s": 'Outer hits open clock for (\\d+(?:\\.\\d+)?)s',
    "OWL-29.clock_protect_recovery_s": 'open clock for \\d+(?:\\.\\d+)?s with (\\d+(?:\\.\\d+)?)s protection recovery',
    "OWL-29.final_exposure_s": 'Final cycle attempts (\\d+(?:\\.\\d+)?)s exposure',
    "OWL-29.final_exposure_cycle_s": 's exposure every (\\d+(?:\\.\\d+)?) unscaled',
    "OWL-30.break_stun_s": 'causes(\\d+(?:\\.\\d+)?)s electrical stun',
    "OWL-30.fire_pause_s": 'capped at(\\d+(?:\\.\\d+)?)s, freezes',
    "OWL-31.slow_s": 'when slow is enabled, start(\\d+(?:\\.\\d+)?)s at×',
    "OWL-31.slow_world_scale": 's at×(\\d+(?:\\.\\d+)?) with',
    "OWL-31.slow_cooldown_s": ' with(\\d+(?:\\.\\d+)?)s cooldown\\. A genuinely',
    "OWL-32.eye_window_s": 'exposes the eye for(\\d+(?:\\.\\d+)?)s only',
    "OWL-32.eye_cooldown_s": 'starts the(\\d+(?:\\.\\d+)?)s eye cooldown',
    "OWL-32.blackout_s": 's eye cooldown and(\\d+(?:\\.\\d+)?)s blackout',
    "OWL-35.departure_s": 'Living departure lasts roughly(\\d+(?:\\.\\d+)?)s',
    "COM-14.roadwarden_hp": 'adjustable baseline(\\d+(?:\\.\\d+)?) HP, patrol span300 at90',
    "COM-15.floodstrider_hp": 'Adjustable baseline(\\d+(?:\\.\\d+)?) HP, patrol span300 at60',
    "COM-16.courier_hp": 'Adjustable baseline(\\d+(?:\\.\\d+)?) HP, air patrol span400',
    "FLOW-37.slider_max": 'Music sliders, each from 0 to (\\d+(?:\\.\\d+)?)',
}
APPROVED_INFO = {"unit", "note"}   # descriptive fields; every number field must be printed by the GDD
PARAM_TABLE_HEADS = ("player movement parameter", "combat / health parameter", "encounter / art parameter")
NUM = r"[-+]?\d+(?:\.\d+)?"


def read_json(path):
    with open(path, encoding="utf-8") as fh:
        return json.load(fh)


def current_snapshot(root=ROOT):
    """Repo path of the current GDD snapshot, from docs/gdd/CURRENT."""
    with open(os.path.join(root, CURRENT), encoding="utf-8") as fh:
        name = fh.read().strip()
    return "docs/gdd/" + name


SNAPSHOT_GLOB = re.compile(r"^GDD-[\w.]+\.md$")


def snapshot_sha256(path):
    """sha256 of a snapshot with line endings normalized (a Windows autocrlf checkout hashes the same)."""
    with open(path, "rb") as fh:
        return hashlib.sha256(fh.read().replace(b"\r\n", b"\n")).hexdigest()


def current_target_problems(cur, pins, root=ROOT):
    """Final-7 dry run B H1: whatever docs/gdd/CURRENT names is pinned, whatever its file name. It is
    docs/gdd/GDD-<rev>.md where <rev> is the file's own Revision, it has a pin, and no other pinned snapshot carries
    the same Revision: an edited copy of 1.3 under another name can never become the authority."""
    out = []
    name = cur[len("docs/gdd/"):]
    full = os.path.join(root, cur)
    if "/" in name or "\\" in name or not SNAPSHOT_GLOB.match(name):
        return [("pin", "docs/gdd/CURRENT", f"names {name!r}: CURRENT must name a docs/gdd/GDD-<revision>.md snapshot")]
    if not os.path.isfile(full):
        return [("pin", "docs/gdd/CURRENT", f"names {cur}, which does not exist")]
    with open(full, encoding="utf-8") as fh:
        rev = gdd_impact.revision(fh.read())
    if name != f"GDD-{rev}.md":
        out.append(("pin", "docs/gdd/CURRENT", f"names {name}, but that file's Revision is {rev}: the file is GDD-{rev}.md"))
    if cur not in pins:
        out.append(("pin", "docs/gdd/CURRENT", f"names {cur}, which has no sha256 pin in gdd_snapshots"))
    for path in sorted(pins):
        other = os.path.join(root, path)
        if path == cur or not os.path.isfile(other):
            continue
        with open(other, encoding="utf-8") as fh:
            if gdd_impact.revision(fh.read()) == rev:
                out.append(("pin", "docs/gdd/CURRENT", f"{cur} and {path} both carry Revision {rev}: a new "
                                                       "snapshot is a new revision (docs/gdd/README.md)"))
    return out


def pin_problems(manifest, root=ROOT, old_manifest=None):
    """GDD snapshots are pinned by sha256 in the manifest's gdd_snapshots (dry run B H9). Every docs/gdd/GDD-*.md is
    pinned and matches its pin, docs/gdd/CURRENT names the manifest's gdd_snapshot, and (with old_manifest, the
    base branch's manifest in CI) no existing pin changes or disappears: a merged snapshot is never edited."""
    out = []
    pins = manifest.get("gdd_snapshots")
    if not isinstance(pins, dict) or not pins:
        return [("pin", "gdd_snapshots", "the manifest pins no GDD snapshot ({path: sha256})")]
    cur = current_snapshot(root)
    if manifest.get("gdd_snapshot") != cur:
        out.append(("pin", "gdd_snapshot", f"manifest reads {manifest.get('gdd_snapshot')}, docs/gdd/CURRENT names {cur}"))
    out += current_target_problems(cur, pins, root)
    gdd_dir = os.path.join(root, "docs", "gdd")
    on_disk = {"docs/gdd/" + n for n in os.listdir(gdd_dir) if SNAPSHOT_GLOB.match(n)} if os.path.isdir(gdd_dir) else set()
    for path in sorted(on_disk - set(pins)):
        out.append(("pin", path, "snapshot has no sha256 pin in gdd_snapshots"))
    for path, want in sorted(pins.items()):
        full = os.path.join(root, path)
        if not os.path.isfile(full):
            out.append(("pin", path, "pinned snapshot is missing (snapshots are never deleted)"))
        elif snapshot_sha256(full) != want:
            out.append(("pin", path, "snapshot bytes differ from its pin: a merged snapshot is never edited; a new "
                                     "revision is a new file (docs/gdd/README.md)"))
    for path, want in sorted(((old_manifest or {}).get("gdd_snapshots") or {}).items()):
        if pins.get(path) != want:
            out.append(("pin", path, "the base branch pins this snapshot differently or at all: pins are append-only"))
    out += sound_pin_problems(manifest, old_manifest)
    return out


RULES_DIR = "docs/rules"
RULES_TEXT = "docs/rules/official-rules.md"
LFS_OID = re.compile(rb"^version https://git-lfs\.github\.com/spec/v1\s*\noid sha256:([0-9a-f]{64})\s*\n")


def file_sha256(path):
    """sha256 of the real bytes, or the oid of a Git LFS pointer (CI checks out with lfs: false)."""
    with open(path, "rb") as fh:
        raw = fh.read()
    m = LFS_OID.match(raw)
    return m.group(1).decode() if m and len(raw) < 1024 else hashlib.sha256(raw).hexdigest()


def rules_pin_problems(manifest, root=ROOT):
    """The Official Rules PDF is pinned by sha256 in rules_pdf, like a GDD snapshot: every docs/rules/*.pdf has a pin
    that matches, and the extracted text's header names the same sha256 (Official Rules prevail; docs/references.md)."""
    pins = manifest.get("rules_pdf")
    if not isinstance(pins, dict) or not pins:
        return [("rules-pin", "rules_pdf", "the manifest pins no Official Rules PDF ({path: sha256})")]
    out = []
    rdir = os.path.join(root, RULES_DIR)
    on_disk = {RULES_DIR + "/" + n for n in os.listdir(rdir) if n.lower().endswith(".pdf")} if os.path.isdir(rdir) else set()
    for path in sorted(on_disk - set(pins)):
        out.append(("rules-pin", path, "rules PDF has no sha256 pin in rules_pdf"))
    try:
        with open(os.path.join(root, RULES_TEXT), encoding="utf-8") as fh:
            header = fh.read(4000)
    except OSError:
        header = None
        out.append(("rules-pin", RULES_TEXT, "missing: the extracted text with its read-only header"))
    for path, want in sorted(pins.items()):
        full = os.path.join(root, path)
        if not os.path.isfile(full):
            out.append(("rules-pin", path, "pinned rules PDF is missing"))
        elif file_sha256(full) != want:
            out.append(("rules-pin", path, "PDF bytes differ from its pin: a new rules version is a human PR that "
                                           "moves the pin and the official-rules.md header together"))
        if header is not None and not re.search(r"(?m)^- sha256: " + re.escape(str(want)) + r"\s*$", header):
            out.append(("rules-pin", RULES_TEXT, f"header sha256 line is not the pin of {path}"))
    return out


def sound_pin_problems(manifest, old_manifest=None):
    """Final-7 dry run B H2: an APPROVED_P0 feature's `sounds` never lose an id against the base branch, so its
    sounds cannot be cut by editing the manifest instead of the sound list (a cut is an Overrides decision)."""
    if not old_manifest:
        return []
    new = {f.get("feature_id"): f for f in manifest.get("features") or [] if isinstance(f, dict)}
    new_gdd = manifest.get("gdd_revision") != old_manifest.get("gdd_revision")
    out = []
    for f in old_manifest.get("features") or []:
        if not isinstance(f, dict) or f.get("status") != "APPROVED_P0":
            continue
        if new_gdd and f.get("feature_id") not in new:
            continue   # a new GDD revision removed the feature itself (gdd_impact.py lists it); its sounds go with it
        gone = sorted(set(f.get("sounds") or []) - set((new.get(f.get("feature_id")) or {}).get("sounds") or []))
        if gone:
            out.append(("sounds", f.get("feature_id"), f"drops sound(s) {', '.join(gone)} that the base branch lists: "
                                                      "an APPROVED_P0 feature's sounds are append-only"))
    return out


def load_manifest(root=ROOT, path=None):
    return read_json(path or os.path.join(root, MANIFEST))


def problems(manifest, snapshot_text, presets=None, decisions_text=""):
    out = []
    overridden = decided_overrides(decisions_text)
    if manifest.get("statuses") != STATUSES:
        out.append(("schema", "statuses", f"must be exactly the GDD B words {STATUSES}"))
    prios = manifest.get("priorities") or []
    modules = set((manifest.get("modules") or {}).keys())
    events = set(manifest.get("events") or [])
    feats = manifest.get("features")
    if not isinstance(feats, list) or not feats:
        return out + [("schema", "features", "no feature records")]
    rev = gdd_impact.revision(snapshot_text)
    if manifest.get("gdd_revision") != rev:
        out.append(("gdd", "gdd_revision", f"manifest is for {manifest.get('gdd_revision')}, current snapshot is {rev}"))
    ids, seen = set(), set()
    for f in feats:
        if isinstance(f, dict) and isinstance(f.get("feature_id"), str):
            ids.add(f["feature_id"])
    for i, f in enumerate(feats):
        if not isinstance(f, dict):
            out.append(("schema", f"features[{i}]", "not an object"))
            continue
        fid = f.get("feature_id") if isinstance(f.get("feature_id"), str) else f"features[{i}]"
        for k, types in FIELDS.items():
            if k not in f:
                out.append(("schema", fid, f"missing field '{k}'"))
            elif not isinstance(f[k], types):
                out.append(("schema", fid, f"'{k}' has the wrong type ({type(f[k]).__name__})"))
        for k, types in OPTIONAL_FIELDS.items():
            if k in f and not (isinstance(f[k], types) and all(isinstance(x, str) and x for x in f[k])):
                out.append(("schema", fid, f"'{k}' must be a list of sound-list ids"))
        if not gdd_impact.FEATURE_ID.fullmatch(fid):
            out.append(("unique", fid, "feature_id is not like CORE-01 / UMB-02"))
        if fid in seen:
            out.append(("unique", fid, "duplicate feature_id"))
        seen.add(fid)
        status = f.get("status")
        if status not in STATUSES:
            out.append(("schema", fid, f"status '{status}' is not one of {STATUSES}"))
        if f.get("priority") not in prios:
            out.append(("schema", fid, f"priority '{f.get('priority')}' is not in the manifest priorities list"))
        if f.get("gdd_revision") != manifest.get("gdd_revision"):
            out.append(("gdd", fid, f"gdd_revision {f.get('gdd_revision')} differs from the manifest's {manifest.get('gdd_revision')}"))
        for k in ("requires", "conflicts"):
            for r in f.get(k) or []:
                if r == fid:
                    out.append(("resolve", fid, f"{k} names itself"))
                elif r not in ids and r not in modules:
                    out.append(("resolve", fid, f"{k} entry '{r}' is not a feature ID or a module key"))
        for e in f.get("emits") or []:
            if e not in events:
                out.append(("events", fid, f"emits '{e}', which is not in the event vocabulary"))
        if f.get("implementation_authorized") is True:
            ok = status in AUTHORIZED or (status == "EXPERIMENT" and TICKET.search(f.get("ticket") or ""))
            if not ok:
                out.append(("authorized", fid, f"implementation_authorized is true but status is {status}"
                                               + (" with no named ticket" if status == "EXPERIMENT" else "")
                                               + "; only APPROVED_P0/P1, or EXPERIMENT with a ticket"))
        if f.get("default_enabled") is not False and not (f.get("implementation_authorized") is True
                                                          and status in AUTHORIZED | {"CONFIRMED"}):
            out.append(("off", fid, f"default_enabled is {f.get('default_enabled')!r}, but {fid} is {status} with "
                                    f"implementation_authorized {f.get('implementation_authorized')!r}: an unapproved "
                                    "feature is always off (D-new-unstated-status; dry run B C1)"))
        want_flag = None if status == "CONFIRMED" else fid.replace("-", "_")
        if "flag" in f and f.get("flag") != want_flag:
            out.append(("flag", fid, f"flag must be {want_flag!r} for a {status} feature (got {f.get('flag')!r})"))
    cited = {m.group(0) for m in gdd_impact.FEATURE_ID.finditer(gdd_impact.cited_body(snapshot_text))}
    for x in sorted(cited - ids):
        out.append(("gdd", x, "cited in the current GDD snapshot but has no manifest record"))
    for x in sorted(ids - cited):
        out.append(("gdd", x, "in the manifest but not cited in the current GDD snapshot"))
    qa_gdd = {m.group(0) for m in QA_ID.finditer(gdd_impact.cited_body(snapshot_text))}
    qa_man = {t for f in feats if isinstance(f, dict) for t in (f.get("tests") or [])}
    for x in sorted(qa_gdd - qa_man):
        out.append(("gdd", x, "QA test in the current GDD snapshot that no manifest record lists in tests"))
    for x in sorted(qa_man - qa_gdd):
        out.append(("gdd", x, "test listed in the manifest but not in the current GDD snapshot"))
    for name, bp in (manifest.get("build_parameters") or {}).items():
        if not isinstance(bp, dict) or bp.get("default") not in (bp.get("allowed") or []):
            out.append(("schema", f"build_parameters.{name}", "needs 'allowed' values and a 'default' among them"))
        elif bp.get("status") not in STATUSES:
            out.append(("schema", f"build_parameters.{name}", f"status '{bp.get('status')}' is not one of {STATUSES}"))
    out += gdd_status_problems(feats, snapshot_text, overridden)
    out += idless_problems(manifest, snapshot_text, ids)
    for f in feats:
        if isinstance(f, dict) and f.get("status") == "APPROVED_P0" and f.get("default_enabled") is not True \
                and f.get("feature_id") not in overridden:
            out.append(("p0-on", f.get("feature_id"), "APPROVED_P0 but default_enabled is not true; the BASE preset "
                                                      "loads every P0 feature (GDD 1.3 section 5), unless a DECIDED "
                                                      "row says 'Overrides: <ID>'"))
    out += approved_problems(manifest, snapshot_text)
    out += override_problems(decisions_text)
    out += grace_problems(decisions_text)
    if presets is not None:
        out += preset_problems(presets, snapshot_text, ids, feats)
    return out


def idless_problems(manifest, snapshot_text, ids):
    """Rows the GDD prints with a placeholder instead of a Rule ID (GDD SH1.0: 7 APPROVED_P0 note and prompt rows,
    5 OPEN template rows). None may be dropped silently (Ricky's import audit, 2026-11-12): each APPROVED_P0 one has
    an approved_without_id entry, in GDD order, whose `starts` begins its text and whose `carried_by` names the
    feature (or QA scenarios) that builds it; each OPEN one has an open_without_id entry. Template rows are not
    features, so neither list makes a feature record."""
    rows = gdd_impact.idless_rows(snapshot_text)
    approved = [r for r in rows if r[2] == "APPROVED_P0"]
    opened = [r for r in rows if r[2] != "APPROVED_P0"]
    have = manifest.get("approved_without_id")
    if not rows and have in (None, []):
        return []
    out = []
    have = have if isinstance(have, list) else []
    if len(have) != len(approved):
        out.append(("idless", "approved_without_id", f"has {len(have)} entries, the GDD prints {len(approved)} "
                                                     "APPROVED_P0 rows without a Rule ID: list every one"))
    for i, (cell, text, _) in enumerate(approved):
        e = have[i] if i < len(have) and isinstance(have[i], dict) else {}
        where = f"approved_without_id[{i}]"
        if not text.startswith(str(e.get("starts") or "\0")):
            out.append(("idless", where, f"does not start the GDD row {cell} '{text[:50]}...' (GDD order)"))
        if e.get("status") != "APPROVED_P0":
            out.append(("idless", where, "status must be APPROVED_P0, as the GDD prints it"))
        carried = re.findall(r"(?<![\w-])(?:" + gdd_impact.FEATURE_RE + r"|QA-\d{2})(?![\w-])", str(e.get("carried_by") or ""))
        if not carried or any(c not in ids and not c.startswith("QA-") for c in carried):
            out.append(("idless", where, f"carried_by '{e.get('carried_by')}' names no manifest feature (or QA scenario) "
                                         "that builds this row"))
    op = manifest.get("open_without_id")
    if len(op if isinstance(op, list) else []) != len(opened):
        out.append(("idless", "open_without_id", f"has {len(op) if isinstance(op, list) else 0} entries, the GDD "
                                                 f"prints {len(opened)} OPEN rows without a Rule ID"))
    return out


def stated_status(cell):
    """The first GDD status word in a status cell ('EXPERIMENT / OFF for special effects' -> EXPERIMENT)."""
    hits = [(m.start(), w) for w in STATUSES for m in [re.search(r"\b" + w + r"\b", cell, re.I)] if m]
    return min(hits)[1] if hits else None


def gdd_status_problems(feats, snapshot_text, overridden=()):
    """Each record's status, on/off and authority must be the one the GDD snapshot states (dry run B C1)."""
    out = []
    stated = gdd_impact.snapshot_statuses(snapshot_text)
    for f in feats:
        if not isinstance(f, dict) or not isinstance(f.get("feature_id"), str):
            continue
        fid, status = f["feature_id"], f.get("status")
        cell = stated.get(fid)
        if cell is None:
            if status in AUTHORIZED or status == "CONFIRMED" or f.get("implementation_authorized") is True \
                    or f.get("default_enabled") is True:
                out.append(("gdd-status", fid, f"the GDD states no status for {fid}, so it may not be {status}, on "
                                               "or implementation_authorized (D-new-unstated-status)"))
        else:
            want = stated_status(cell)
            if status != want:
                out.append(("gdd-status", fid, f"status {status} differs from the GDD's '{cell}' ({want}); change "
                                               "the GDD revision first (docs/gdd/README.md)"))
            if re.search(r"\bOFF\b", cell) and f.get("default_enabled") is not False:  # Overrides never lift OFF
                out.append(("gdd-status", fid, f"the GDD says '{cell}', but default_enabled is not false"))
            if re.search(r"no implementation authority", cell, re.I) and f.get("implementation_authorized") is not False:
                out.append(("gdd-status", fid, f"the GDD says '{cell}', but implementation_authorized is not false"))
        if (f.get("priority") == "P0") != (status == "APPROVED_P0"):
            out.append(("gdd-status", fid, f"priority {f.get('priority')} with status {status}: P0 goes with "
                                           "APPROVED_P0 and only with it"))
    return out


OVERRIDES = re.compile(r"\bOverrides:\s*((?:(?:(?:" + gdd_impact.FEATURE_RE + r")(?:\.[a-z]\w*)?|T-\d{2})"
                       r"(?:\s*,\s*|\s+and\s+|\s*)?)+)")
DECISIONS = "docs/decisions.md"
# The person whose GDD revision sets feature statuses. GDD SH1.0 revision note (2026-11-12): "Rick approves all filled
# requirements as APPROVED_P0, priority P0" (GDD 1.3 section 14 named Richard; SH1.0 credits list Richard as Producer).
# Every ID an Overrides clause can lift is an APPROVED_P0 feature or a preset, so the design owner is the only valid
# decider (D-new-sh10-design-owner).
DESIGN_OWNER = "Rick"
# The Status cell of a counted row: exactly `DECIDED <YYYY-MM-DD> (<name>)` at its start (docs/decisions.md rules).
DECIDED_STATUS = re.compile(r"DECIDED (\d{4}-\d{2}-\d{2}) \(([A-Z][\w .'-]*)\)(?=$|[\s.;,])")
NO_OWNER = re.compile(r"^(?:|[-\u2013\u2014]+|none|tbd|n/?a|\?+|unassigned)$", re.I)


def table_cells(line):
    return [c.strip() for c in line.strip().strip("|").split("|")]


def override_rows(decisions_text):
    """[(row cells by header name, raw line)] for rows of a table whose header has Owner and Status columns."""
    out, head = [], None
    for ln in (decisions_text or "").splitlines():
        if not ln.strip().startswith("|"):
            head = None
            continue
        cells = table_cells(ln)
        if head is None:
            head = [c.lower() for c in cells]
            continue
        if all(set(c) <= set("-: ") for c in cells):
            continue
        if "owner" in head and "status" in head and len(cells) == len(head):
            out.append((dict(zip(head, cells)), ln))
    return out


def override_row_problem(row, line):
    """Why a row with an Overrides clause lifts nothing, or None when it counts (dry run B H1). A row counts only
    with: Status exactly `DECIDED <date> (<name>)`, a named Owner, no SUPERSEDED anywhere, and the design owner
    (DESIGN_OWNER) as the decider."""
    if GRACE_STATUS.match(row.get("status", "")):
        return ("it is a 2h grace default: a grace default never overrides a P0 or lifts a P0 rule; only "
                f"'DECIDED <date> ({DESIGN_OWNER})' does (pipeline/human-checkpoints.md)")
    m = DECIDED_STATUS.match(row.get("status", ""))
    if not m:
        return "its Status is not exactly 'DECIDED <YYYY-MM-DD> (<name>)'"
    if re.search(r"superseded", line, re.I):
        return "it is SUPERSEDED"
    if NO_OWNER.match(row.get("owner", "").strip()):
        return "it has no named Owner"
    if m.group(2).strip() != DESIGN_OWNER:
        return f"it was decided by {m.group(2).strip()}, not {DESIGN_OWNER} (the design owner approves P0 and presets)"
    return None


def override_ids(line):
    out = set()
    for m in OVERRIDES.finditer(line):
        # a parameter key (`CORE-03.max_health`) is one ID: it lifts the start rule for that key, never its feature
        out |= set(re.findall(r"(?<![\w-])(?:(?:" + gdd_impact.FEATURE_RE + r")(?:\.[a-z]\w*)?|T-\d{2})(?![\w-])",
                              m.group(1)))
    return out


def decided_overrides(decisions_text):
    """IDs a counted decision row overrides with an `Overrides: DEF-01, T-03` clause (dry run B H1, H3).

    Only these IDs lift the P0-on rule (here and in tools/bake_preset.py) and the BASE-ships rule (bake_preset,
    check_card G4). They never lift the GDD's OFF rule or the unapproved-is-off rule. A row counts only in a table
    with Owner and Status columns (the Open decisions table; the Settled table has no Owner), and only when
    override_row_problem() finds nothing. A row that only names an ID (D-new-p0-signoff lists every P0) lifts nothing."""
    out = set()
    for row, ln in override_rows(decisions_text):
        if override_ids(ln) and override_row_problem(row, ln) is None:
            out |= override_ids(ln)
    return out


def override_problems(decisions_text):
    """A row that writes an Overrides clause but does not count is a problem, so a near-miss is never silent."""
    out = []
    for ln in (decisions_text or "").splitlines():
        if not ln.strip().startswith("|") or not override_ids(ln):
            continue
        row = next((r for r, raw in override_rows(decisions_text) if raw == ln), None)
        why = "it is not a row of a table with Owner and Status columns" if row is None else override_row_problem(row, ln)
        if why is not None and not (row is not None and not row.get("status", "").upper().startswith("DECIDED")):
            out.append(("overrides", ln.strip()[:60], f"has 'Overrides:' but lifts nothing: {why}"))
    return out


# The 2 h grace default (pipeline/human-checkpoints.md, Grace default). A needs-human item no human answered in
# GRACE_HOURS goes to a Hard calls director session; it records the call as a row with this exact Status.
GRACE_HOURS = 2
GRACE_ROLES = ("Producer", "Technical Director", "Producer for Richard", "Producer for Rick")
GRACE_STATUS = re.compile(r"DECIDED (\d{4}-\d{2}-\d{2}) \(agent default after 2h grace; (" + "|".join(GRACE_ROLES)
                          + r"); human may overturn\)(?=$|[\s.;,])")
GRACE_MARK = re.compile(r"agent default after|\b2 ?h grace\b", re.I)
# Kinds that stay human-only however long they wait (pipeline/human-checkpoints.md, "Never a grace default").
# Matched on the ask's <what> (check_card --needs-human) and on a grace row's question and Status cells.
GRACE_HUMAN_ONLY = (
    ("final submission or upload, Official Rules section 17",
     re.compile(r"\bsubmi|\bupload|\bbutler\b|\bjam form\b|\bitch\b|\bG4\b", re.I)),
    ("physical work: Windows packaging or launch, playtests, the editor check",
     re.compile(r"packag|\blaunch|playtest|play the build|editor check|\.uasset|\.umap|daily\.ps1|by ear|"
                r"audio mix|\bstart (?:an |the )?(?:agent )?session", re.I)),
    ("changing guardrails: gate_paths, tools, tests, CI, hooks, role cards, model tiers",
     re.compile(r"gate[_ ]paths?|gates\.json|\btools/|\btests?/|\bCI\b|\.github|workflow|\bhooks?\b|hook\.py|"
                r"role cards?|pipeline/roles|model[- ]tiers?|AGENTS\.md|CLAUDE\.md|\.claude/|\.mcp\.json|mcp_enabled|"
                r"editor MCP|\bsecret|REVERT_TOKEN", re.I)),
    ("deleting someone else's work", re.compile(r"\bdelet|\brm -|\bgit rm\b", re.I)),
    ("a P0 override or a P0 rule: only DECIDED (<design owner>)",
     re.compile(r"\bOverrides:|\bP0\b|APPROVED_P0|never[- ]cut", re.I)),
    ("a hitbox or collider change: only the design owner (GDD 1.3 7C; GDD SH1.0 CORE-05: cosmetic swaps never alter hitboxes)",
     re.compile(r"hitbox change|collider change|change (?:a |the )?(?:hitbox|collider)", re.I)),
    ("an approved_parameters range: only the GDD and its design owner",
     re.compile(r"approved_parameters|\b5A\b|outside (?:the |a |its )?(?:approved |GDD )?range", re.I)),
    ("story canon (a PROPOSED story bible row, the title, the owl's name): only the design owner confirms",
     re.compile(r"story canon|story bible|\bcanon\b|STORY CONFIRM|\bowl'?s name\b|game(?:'s)? title", re.I)),
)


def grace_kind(text):
    """The human-only kind `text` falls in (never a grace default), or None when a grace default may answer it."""
    for kind, rx in GRACE_HUMAN_ONLY:
        if rx.search(text or ""):
            return kind
    return None


GRACE_LINK = re.compile(r"(?<![\w/])#\d+\b|https?://\S+/issues/\d+")


def grace_problems(decisions_text):
    """A row that records a 2 h grace default must be exactly that, and only on a kind a grace default may decide."""
    out = []
    rows = {raw: r for r, raw in override_rows(decisions_text)}
    for ln in (decisions_text or "").splitlines():
        if not ln.strip().startswith("|") or not GRACE_MARK.search(ln):
            continue
        where = ln.strip()[:60]
        row = rows.get(ln)
        if row is None:
            out.append(("grace", where, "a grace default row belongs in the Open decisions table (Owner and Status)"))
            continue
        status = row.get("status", "")
        if not GRACE_STATUS.match(status):
            out.append(("grace", where, "Status is not exactly 'DECIDED <YYYY-MM-DD> (agent default after 2h grace; "
                                        f"<{' | '.join(GRACE_ROLES)}>; human may overturn)'"))
            continue
        if not GRACE_LINK.search(ln):
            out.append(("grace", where, "a grace default links its needs-human issue (#<n> or the issue URL)"))
        question = row.get("decision needed", row.get("decision", ""))
        kind = grace_kind(question + " " + GRACE_STATUS.sub("", status))
        if kind:
            out.append(("grace", where, f"human-only, never a grace default: {kind} (pipeline/human-checkpoints.md)"))
    return out


def read_decisions(root=ROOT):
    try:
        with open(os.path.join(root, DECISIONS), encoding="utf-8") as fh:
            return fh.read()
    except OSError:
        return ""


PLACEHOLDER_LABEL = re.compile(r"^\[.*\]$")   # a template row such as "[exact mapped label]" is not a parameter


def section_5a_tables(snapshot_text):
    """How many parameter tables (PARAM_TABLE_HEADS) the snapshot prints, filled or not."""
    return sum(1 for line in gdd_impact.body(snapshot_text).splitlines() if line.strip().startswith("|")
               and line.strip().strip("|").split("|")[0].strip().lower() in PARAM_TABLE_HEADS)


def section_5a_rows(snapshot_text):
    """{row label: {start, step, min, max}} from the snapshot's section 5A parameter tables (missing keys = not printed).
    A bracketed template row ("[exact mapped label]", GDD SH1.0 section 9) is a blank, not a row."""
    rows, on = {}, False
    for line in gdd_impact.body(snapshot_text).splitlines():
        cells = [c.strip() for c in line.strip().strip("|").split("|")] if line.strip().startswith("|") else None
        if cells is None:
            on = on and not line.startswith("#")
            continue
        if cells[0].lower() in PARAM_TABLE_HEADS:
            on = True
            continue
        if not on or len(cells) < 3 or set(cells[0]) <= set("-: ") or PLACEHOLDER_LABEL.match(cells[0]):
            continue
        got = {}
        m = re.match(r"^\s*(" + NUM + r")", cells[1])
        if m:
            got["start"] = float(m.group(1))
        m = re.search(r"step\s+(" + NUM + r")", cells[1])
        if m:
            got["step"] = float(m.group(1))
        m = re.match(r"^\s*(" + NUM + r")\s*%?\s*-\s*(" + NUM + r")", cells[2])
        if m:
            got["min"], got["max"] = float(m.group(1)), float(m.group(2))
        rows[cells[0]] = got
    return rows


def approved_problems(manifest, snapshot_text):
    """approved_parameters must equal the GDD section 5A tables (GDD 1.3 is the design source; the manifest mirrors it)."""
    out = []
    rows = section_5a_rows(snapshot_text)
    if not rows and not section_5a_tables(snapshot_text):
        return [("approved", "GDD section 5A", "no parameter tables found in the current snapshot")]
    vals = (manifest.get("approved_parameters") or {}).get("values") or {}
    for label, want in rows.items():
        key = PARAM_ROWS.get(label)
        if key is None:
            out.append(("approved", label, "section 5A row has no approved_parameters key in manifest_check.PARAM_ROWS"))
            continue
        have = vals.get(key)
        if not isinstance(have, dict):
            out.append(("approved", key, f"missing; GDD section 5A row '{label}' prints {want}"))
            continue
        for k, v in want.items():
            h = have.get(k)
            if isinstance(h, bool) or not isinstance(h, (int, float)) or abs(float(h) - v) > 1e-9:
                out.append(("approved", f"{key}.{k}", f"manifest has {h!r}, GDD section 5A '{label}' prints {v:g}"))
        for k in sorted(set(have) - set(want) - APPROVED_INFO):
            out.append(("approved", f"{key}.{k}", f"manifest has {k}={have[k]!r}, but GDD section 5A '{label}' prints no "
                                                  f"{k}: every approved number comes from the GDD (final-8 B C2)"))
    body = gdd_impact.body(snapshot_text)
    for key, rx in PROSE_ROWS.items():
        have = vals.get(key)
        if have is None:
            continue
        m = re.search(rx, body)
        if not m:
            out.append(("approved", key, "the GDD sentence it traces to is not in the current snapshot "
                                         f"(manifest_check.PROSE_ROWS: {rx!r})"))
            continue
        if not isinstance(have, dict) or set(have) - {"start"} - APPROVED_INFO:
            out.append(("approved", key, f"the GDD prints only a start ({m.group(0)!r}); the entry may hold start, unit "
                                         "and note, never a range (final-8 B C2)"))
        elif isinstance(have.get("start"), bool) or not isinstance(have.get("start"), (int, float)) \
                or abs(float(have["start"]) - float(m.group(1))) > 1e-9:
            out.append(("approved", f"{key}.start", f"manifest has {have.get('start')!r}, the GDD says {m.group(0)!r}"))
    traced = set(PARAM_ROWS.get(label) for label in rows) | set(PROSE_ROWS)
    for key in sorted(set(vals) - traced):
        out.append(("approved", key, "is in approved_parameters but traces to no GDD section 5A row "
                                     "(manifest_check.PARAM_ROWS) or GDD sentence (PROSE_ROWS): only the GDD approves "
                                     "a value (final-8 B C2)"))
    return out


BASE_PRESET = "T-01"


def preset_problems(presets, snapshot_text, ids, feats=()):
    out = []
    recs = {f.get("feature_id"): f for f in feats if isinstance(f, dict)}
    got = [p.get("id") for p in presets.get("presets", [])]
    want = sorted({m.group(0) for m in PRESET_ID.finditer(gdd_impact.body(snapshot_text))})
    if sorted(got) != want or len(set(got)) != len(got):
        out.append(("presets", PRESETS, f"preset IDs {sorted(got)} must be the snapshot's {want}, once each"))
    for p in presets.get("presets", []):
        for k in ("enable", "disable"):
            for fid in p.get(k, []):
                if fid not in ids:
                    out.append(("presets", p.get("id"), f"{k} names {fid}, which is not in the manifest"))
                elif k == "enable" and recs and not recs.get(fid, {}).get("implementation_authorized"):
                    out.append(("presets", p.get("id"), f"enable names {fid}, which is not implementation_authorized "
                                                        "(a preset never turns on unapproved work)"))
        if p.get("id") == BASE_PRESET and (p.get("enable") or p.get("disable")):
            out.append(("presets", BASE_PRESET, "BASE changes nothing: enable and disable must be empty (GDD 1.3 "
                                                "section 5: BASE loads every P0 feature and leaves experiments off)"))
    return out


NOTE_FIELDS = {"commit": r"^[0-9a-f]{7,40}$", "gdd_revision": r"^\S+$", "test_id": r"^(?:QA|T)-\d{2}$",
               "preset": r"^T-\d{2}$", "seed": r"^-?\d+$", "date": r"^\d{4}-\d{2}-\d{2}$",
               "what_changed": r"\S", "observed": r"\S", "decision": r"^(?:keep|revise|remove|retest)$",
               "owner": r"\S", "rationale": r"\S"}
RATINGS = ("fun", "fairness", "readability", "responsiveness")


def note_problems(note):
    """One tester note (GDD B Appendix C) as JSON."""
    out = []
    for k, pat in NOTE_FIELDS.items():
        v = note.get(k)
        if v is None or not re.search(pat, str(v)):
            out.append(("note", k, f"missing or malformed (want {pat})"))
    r = note.get("ratings") or {}
    for k in RATINGS:
        if not isinstance(r.get(k), int) or not 1 <= r[k] <= 5:
            out.append(("note", f"ratings.{k}", "must be a whole number 1-5"))
    if isinstance(note.get("what_changed"), list):
        out.append(("note", "what_changed", "name the ONE variable changed, not a list"))
    return out


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--root", default=ROOT)
    ap.add_argument("--manifest")
    ap.add_argument("--note")
    ap.add_argument("--pin", metavar="SNAPSHOT", help="print the sha256 pin for a new snapshot (docs/gdd/README.md)")
    ap.add_argument("--pins-from", help="the base branch's manifest (CI): its snapshot pins must be unchanged")
    a = ap.parse_args(argv)
    if a.pin:
        print(f'"{a.pin}": "{snapshot_sha256(os.path.join(a.root, a.pin))}"')
        return 0
    try:
        if a.note:
            p = note_problems(read_json(a.note))
        else:
            snap = gdd_impact.read(os.path.join(a.root, current_snapshot(a.root)))
            presets_path = os.path.join(a.root, PRESETS)
            presets = read_json(presets_path) if os.path.exists(presets_path) else None
            man = load_manifest(a.root, a.manifest)
            p = problems(man, snap, presets, read_decisions(a.root))
            p += pin_problems(man, a.root, read_json(a.pins_from) if a.pins_from else None)
            p += rules_pin_problems(man, a.root)
    except (OSError, ValueError) as e:
        print(f"manifest_check: cannot read input: {e}")
        return 2
    for kind, where, why in p:
        print(f"[{kind}] {where}: {why}")
    print(f"manifest_check: {len(p)} problem(s)")
    return 1 if p else 0


if __name__ == "__main__":
    sys.exit(main())
