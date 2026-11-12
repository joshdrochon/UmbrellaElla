#!/usr/bin/env python3
"""Encounter gate. GDD SH1.0 (the current GDD): the state-driven Keeper fight is the encounter.json baseline preset;
E29 holds every GDD number it copies (numbers_from_gdd) to the manifest, and S1-S13 (tools/encounter_spec.py) check its
phases, targets, attacks, breaks and transitions. GDD 1.3 (history, and the frozen 1.3 data in tests/fixtures/gdd13):
one arena, one clockwork owl, one approved bolt on a timer (GDD 1.3 §7, §7B, §8), checked by the timeline rules E1-E29
below. Which applies is the manifest's GDD model (tools/tuning.py MODELS: `timeline`).

GDD SH1.0 state mode (data `"model": "state"`):
  E29 gdd        every attack names a manifest `feature` that is on; every numbers_from_gdd path resolves to a number
                 equal to its manifest key's approved value (tools/tuning.py rule: the start, while GDD SH1.0 prints no
                 range); a top-level timeline (patterns, phases, duration_sec) is GDD 1.3 history and fails
  E28 empty      no baseline preset, or one with no attacks or no numbers_from_gdd

Reads pipeline/level/encounter.json (the mirror of the DA_OwlPattern and DA_Phase assets) and
checks it against the rules in pipeline/checklists/level-sections.md. Stdlib only.
Thresholds live in this file (a gate file), not in the data the Level Designer edits.

Rules (id: what fails):
  E1 telegraph   TelegraphSec < 0.4 s, or no visual tell (pose or VFX). Sound alone fails (GDD §7).
                 Bolts and arcs need all three layers: pose, sound and VFX (a player watching the hero still gets it).
  E2 stages      ActiveSec <= 0, RecoverySec < 0, or ActiveSec shorter than the volleys and stagger need.
  E3 phases      not one `base` phase 0-100% and not intro/contest/desperation in order (GDD 1.3 §8: phases are
                 optional tuning presets), gaps or overlaps in 0-100%, desperation > 30% (pipeline default).
  E4 distinct    [2+ patterns] a phase that does not add or swap a pattern or space rule vs the phase before.
  E5 cue         [2+ phases] no single phase_change_cue, or a phase that sets its own cue.
  E6 intro       intro uses a bolt with count > 1, an arc, more than 1 gust, or [2+ patterns] overlapping attacks.
  E7 first-use   [2+ patterns] a pattern's first use overlaps another attack (teach before testing).
  E8 breather    [2+ patterns] a phase has no window >= 3.0 s with no attack in telegraph, active or flight.
                 With the one approved bolt the GDD sets the rhythm (E29), so E8, E19 and E26's breather part are off.
  E9 colour      amber on anything but a bolt tell, red on anything but the arc, or a bolt/arc without it.
  E10 readable   a projectile pattern without draw_on_top and directional_sprite.
  E11 spread     a lone angle (nearest-neighbour gap > 2x the median gap), a spread with spawn_offset_sec 0,
                 an aimed spread with an odd count and no odd_count_reason, volleys > 1 with seed step 0.
  E12 origin     origin_locked_during_telegraph is not true (owl drift must not move the fire point).
  E2 also       an arc without reach > 0, flight_sec > 0, flight_sec <= active_sec, or core_radius > 0.
  E13 safe-path  with the owl at the min and the max of its drift Y, and aimed bolts and arcs aimed at the
                 hero's high, middle and low spots, a hero-sized box can move (at hero speed) through every
                 simulated step of every attack cluster without touching a bolt or the arc.
                 The arc is an out-and-back loop: along the aim line reach x 4s(1-s), sideways
                 side x sin(2 pi s), s = time since launch / flight_sec. It is gone when it gets back.
  E14 coverage   [2+ patterns] a row (pos_high, pos_low, pos_far, ctl_rise, ctl_fall, ctl_horizontal; ctl_gust only once the
                 Gust row of pipeline/qa/test-map.md is merged, because the gust is P1) has no pattern used by
                 the end of phase 2. Always: a bolt claims a position its bolts never reach.
  E15 gust       a gust zone outside the hero zone, or one with no hero-sized lane above or below it.
  E16 end        end_event does not stop threats, the owl does not depart, no Survived card, quiet < 5 s.
                 (A story clue is optional: narrative is DEFERRED, NAR-01, GDD 1.3 §1.)
  E17 arena      owl zone not in the right half, hero and owl zones overlap, drift outside the arena.
  E18 doc        the generated block in pipeline/level/encounter.md differs from this data.
  E19 intensity  [2+ patterns] a phase's threat share (seconds with any attack in telegraph, active or flight / phase
                 length) is over 60%; density (attack-seconds per second, overlaps add up) of intro is over
                 contest's, or desperation's is over 1.3x contest's; or two peaks (clusters of 2+ attacks)
                 have no 3.0 s breather between them.
  E20 camping    after intro (in every phase of a one-phase encounter), a hero standing still on any point of a 5x5 grid over the hero zone (under the
                 altitude cap) is never hit by a bolt or arc in that phase, at either end of the owl's drift.
  E21 layering   [2+ patterns] contest has no cluster with an aimed bolt pattern and a non-aimed bolt pattern together
                 (aimed shots force a move, static shapes block a route).
  E22 tuning     hero speeds, hurtbox and bolt hitbox are not read from the Game Designer's tuning file
                 (arena.tuning_source), a copy of them sits in encounter.json, or the hurtbox is > 50% of
                 the body sprite area.
  E23 owl box    the owl hitbox is < 80% of the owl sprite area (auto-fire must land on what the player sees).
  E24 midpoint   [2+ patterns] no pattern makes its first appearance in the second half of contest (the midpoint turn).
  E25 recovery   [lift loss on: lowest lift tier < 1.0, SURV-04] at the lowest lift tier (the torn umbrella), climbing from the lowest hero spot to the highest
                 one under desperation's (or base's) cap (plus half the open rise ramp) takes longer than desperation's
                 longest breather. A hero knocked to the bottom must be able to climb back in one breather.
  E26 clock hit  a pattern without interruptible_sec (0 = a clock hit does not disrupt it), one over 1.0 s
                 ("briefly", GDD §5), or one > 0 without interrupt_replays_telegraph true (a clock hit pauses
                 the attack; if its telegraph was showing, the full telegraph plays again, so an interrupt never
                 shortens a telegraph already on screen). [2+ patterns] Also fails a phase whose breather drops
                 under 3.0 s when every interruptible attack runs late by interruptible_sec + telegraph_sec.
  E28 empty      the data has no patterns or no phases (an empty editor dump proves nothing).
  E27 wing hit   a gust without gust_strength_by_wing_tier (a list: 1.0 first, never rising, every value in
                 (0, 1]; [1.0] = wing hits cut), or a list longer than 1 without wing_tear_overlays (one
                 texture per damaged tier, so a weaker gust is visible).
  E30 baked      once pipeline/qa/baked.json exists, each value the game ships that this sim or feel_check reads
                 (tools/tuning.py SIM_KEYS) equals the data file value (dry run B H4)
  E29 gdd        GDD 1.3 approved numbers (docs/feature-manifest.json approved_parameters, held to the GDD by
                 manifest_check.py): every pattern names a manifest `feature` that is on (default_enabled); exactly
                 one OWL-01 base bolt, single and aimed, with telegraph_sec in the OWL-01.telegraph_delay range and
                 speed in the OWL-01.projectile_speed range; duration_sec in the END-01.survival_s range; seed =
                 OWL-01.seed (no range). The section 5A starts are provisional tuning, so any in-range value passes
                 (dry run A H4; bake_preset uses the same range). With only the base bolt: first telegraph at
                 OWL-01.initial_grace_s (no range), then one interval inside the OWL-01.cadence range to the end.
                 interruptible_sec > 0 needs COM-02 on; a wing-tier gust list longer than [1.0] needs COM-03 on.

Playtest log mode (--playtest CSV...; the log's owner is QA and Build):
  L1 header      columns are not exactly session,event,phase,pattern_id,explained,t_run_s,build.
  L2 event       event is not hit, death or survive.
  L3 pattern     a hit or death row has an empty pattern_id, or one that is not in encounter.json
                 (BOTTOM_EXIT is the one extra id: leaving through the bottom edge, GDD §2).
  L4 explained   a hit or death row has explained other than y or n.
  L5 row         phase not base/intro/contest/desperation, t_run_s not a number >= 0, empty session or build.
  L6 empty       a log has no hit, death or survive row (a header alone is not a playtest).
  The report prints hits, deaths and explained=n per pattern. explained=n is a bug against that pattern
  (fix the tell), not a log error, so it does not fail the check.

Envelope mode (--envelope "FEEL_ENVELOPE ..."; the line card 0.13's UmbrellaElla.Move.World.FeelEnvelope logs):
  V1 field       a field of the line is missing or not a number.
  V2 differs     a measured value is off the tuning file (feel.json `movement`, the numbers this sim uses) by
                 more than 5% (or 2 frames for the *_f fields). Fields: accel_f = frames from 0 to move_speed
                 (move_speed / move_accel x 60), fall = max fall cm/s, rise_intact and rise_critical = UP_OPEN rise
                 cm/s at full and lowest health (equal unless SURV-04 is on), blend_f = state blend frames. Then the game and the sim disagree: fix the
                 header default or feel.json in one tuning PR.

Wiring mode (--wiring [ROOT]; owner: Producer). No encounter card moves to doing until it prints 0 problem(s):
  W1 day0       pipeline/day0-cards.md has no `Owl data types` row naming UmbrellaElla.Owl, or no `Owl dump`
                row naming `encounter_check.py --data`.
  W2 test-map   pipeline/qa/test-map.md is missing an UmbrellaElla.Owl test name (the 2 phase tests only when
                 encounter.json has more than one phase).
  W3 log spec   pipeline/qa/playtests.md has no `Columns:` line equal to the L1 columns.
  W4 role row   AGENTS.md has no roles-table row for pipeline/roles/level-designer.md.
  W5 reviewer   pipeline/roles/game-designer.md does not name encounter_check.py (its review criteria).
  W6 presets    (with encounter_presets) AGENTS.md has no roles-table row for pipeline/roles/encounter-designer.md,
                 pipeline/day0-cards.md has no row naming `--ready` or `--playthrough`, or pipeline/qa/test-map.md
                 misses an encounter preset test (ENCOUNTER_TESTS).

Card mode (--card FILE...; an encounter card's text, owner: the card's reviewer; C6-C9 in tools/encounter_spec.py
apply when the card has an `Encounter phases:` line):
  C1 data gate  no pasted `encounter_check: 0 problem(s)` line.
  C2 coverage   no `Coverage signed: <name> <YYYY-MM-DD>` line.
  C3 art        no `Accent check: ... <name> <YYYY-MM-DD>` or `Motion check: ... <name> <YYYY-MM-DD>` line.
  C4 paper walk no `Paper walk: <link or #n>` line.
  C5 engine     an Owl test name (phase tests only with 2+ phases) is on no line with PASS, and on no `Not run` line with a card number (#n).

Tuning read from the tuning file (cm/s, GDD 1.3 §5A; worst case, so the sim never passes on a speed the hero lacks):
  sideways = move_speed x open_steer_multiplier; up = ascent_speed x the lowest lift tier (1.0 unless SURV-04);
  down = max_fall_speed; hurtbox = forgiveness.player_hurtbox_cm and bolt hitbox radius =
  forgiveness.bolt_hitbox_radius_cm, both fixed collider data, never derived from sprite size (GDD 1.3 7A, 7C).
  The body art box is only compared with the collider (E22 area share). Experiment arcs (off) scale their
  core_radius by bolt_hitbox_radius_cm / bolt_core_radius in the sim only.

Encounter presets (S1-S13, P1-P8, C6-C9): the whole fight as data in encounter.json `encounter_presets` (owner:
Encounter Designer). The rules are listed in tools/encounter_spec.py. Every check runs S1-S11 and S13 on every preset;
the GDD 1.3 baseline preset takes its numbers from the top level, so E29 still holds them to the manifest.
  --presets [--gdd REV] [--context C]   list the presets a context may load (C: ship, workbench, practice, gdd_picker;
                                        the GDD picker asks with the revision it picked and gdd_picker)
  --ready --preset ID                   S12: every hitbox, art and sound row the preset names exists; prints
                                        `encounter_ready: 0 problem(s) preset=ID` (the line an encounter card carries)
  --spec-hash ID/PHASE                  the phase's spec hash (critic verdicts carry it)
  --critic-packet ID/PHASE [--log L] [--video V]   the blind critic's whole input for one phase
  --playthrough LOG --preset ID         P1-P8 on the game's ENCOUNTER_EVT run log; prints
                                        `playthrough_check: <n> problem(s) preset=ID phases=...`

Usage:
  python3 tools/encounter_check.py                 # check; prints measured numbers
  python3 tools/encounter_check.py --write-md      # rewrite the generated block in encounter.md
  python3 tools/encounter_check.py --data F --md M # other files (tests, the editor dump)
  python3 tools/encounter_check.py --tuning F      # another tuning file (default: arena.tuning_source)
  python3 tools/encounter_check.py --playtest a.csv b.csv   # check playtest logs, per-pattern report
  python3 tools/encounter_check.py --envelope "FEEL_ENVELOPE accel_f=12 ..."   # game vs tuning file
  python3 tools/encounter_check.py --manifest F    # another feature manifest (default: docs/feature-manifest.json)
  python3 tools/encounter_check.py --wiring                 # are the engine cards, tests and docs filed?
  python3 tools/encounter_check.py --card card.md           # does an encounter card carry its lines?
Exit 0 = clean, 1 = problems.
"""
import argparse
import csv
import json
import math
import os
import re
import statistics
import sys

MIN_TELEGRAPH_SEC = 0.4      # proposed: about 2x simple visual reaction (~190 ms)
MIN_BREATHER_SEC = 3.0       # proposed
MAX_DESPERATION_PCT = 30.0   # pipeline default for the optional desperation preset (GDD 1.3 §8 sets no split)
MAX_INTRO_GUSTS = 1          # pipeline default: the intro teaches one gust (only with OWL-02 on)
LONE_GAP_FACTOR = 2.0
MIN_END_QUIET_SEC = 5.0
MAX_THREAT_SHARE = 0.60      # proposed: no phase is attack-on for more than 60% of its time
DESP_VS_CONTEST_MAX = 1.3    # proposed: desperation is harder, not a wall
MAX_HURTBOX_AREA = 0.50      # hurtbox area / body sprite area
MIN_OWL_HITBOX_AREA = 0.80   # owl hitbox area / owl sprite area
MAX_INTERRUPT_SEC = 1.0      # proposed: clock hit "briefly disrupts" (COM-02, off in GDD 1.3)
CAMP_GRID = 5                # E20 probes a CAMP_GRID x CAMP_GRID grid of still-hero spots
TUNED_KEYS = ("hero_box", "hero_speed_x", "hero_speed_y", "hero_speed_up", "hero_speed_down", "bolt_radius",
              "projectile_hitbox_ratio", "rise_ramp_s", "lowest_lift")
PLAYTEST_COLUMNS = ["session", "event", "phase", "pattern_id", "explained", "t_run_s", "build"]
PLAYTEST_EVENTS = {"hit", "death", "survive"}
BOTTOM_EXIT = "BOTTOM_EXIT"
PHASE_IDS = ["intro", "contest", "desperation"]
BASE_PHASE = ["base"]        # GDD 1.3 §8: phases are optional tuning presets; one base phase is the baseline
PLAYTEST_PHASES = BASE_PHASE + PHASE_IDS
COVERAGE_ROWS = ["pos_high", "pos_low", "pos_far", "ctl_rise", "ctl_fall", "ctl_horizontal", "ctl_gust"]
P1_COVERAGE = {"ctl_gust": "gust"}   # coverage row -> test-map row that must be merged before it is required
TEST_MAP = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "pipeline", "qa", "test-map.md")
ENVELOPE_FIELDS = ("accel_f", "fall", "rise_intact", "rise_critical", "blend_f")  # no fast fall: GDD 1.3 §5A
ENVELOPE_PCT = 0.05
ENVELOPE_FRAMES = 2.0
PROJECTILE_KINDS = {"bolt", "arc"}
OWL_TESTS = ["UmbrellaElla.Owl.EveryPatternHasTelegraph", "UmbrellaElla.Owl.PhaseTableDistinct",
             "UmbrellaElla.Owl.World.OriginLockedDuringTelegraph", "UmbrellaElla.Owl.World.PhaseChangePlaysCue",
             "UmbrellaElla.Owl.World.NoDamageAfterEndTrigger"]
ENCOUNTER_TESTS = ["UmbrellaElla.Owl.PresetLoadsFromEncounterJson", "UmbrellaElla.Owl.World.NoAttackDuringTransition",
                   "UmbrellaElla.Owl.World.PlaythroughLogLines"]
OWL_PHASE_TESTS = {"UmbrellaElla.Owl.PhaseTableDistinct", "UmbrellaElla.Owl.World.PhaseChangePlaysCue"}  # 2+ phases only
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import tuning as tuning_mod  # noqa: E402  shared tunable/fixed rule (dry run B H3, H4)
import encounter_spec as spec_mod  # noqa: E402  encounter presets: the fight as a whole (S, P, C6-C9 rules)
MANIFEST = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "docs", "feature-manifest.json")
BASE_BOLT_FEATURE = "OWL-01"
INTERRUPT_FEATURE = "COM-02"     # clock hit disrupts owl attacks: EXPERIMENT, off
WING_FEATURE = "COM-03"          # wing hits weaken gusts: EXPERIMENT, off
OWL_CARDS = [("Owl data types", "UmbrellaElla.Owl"), ("Owl dump", "encounter_check.py --data")]
KIND_COLOR = {"bolt": "amber", "arc": "red", "gust": None}
BEGIN = "<!-- BEGIN GENERATED by encounter_check.py --write-md; do not edit by hand -->"
END = "<!-- END GENERATED -->"

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
DEFAULT_DATA = os.path.join(ROOT, "pipeline", "level", "encounter.json")
DEFAULT_MD = os.path.join(ROOT, "pipeline", "level", "encounter.md")


# ---------- P1 features (test-map rows) ----------

def merged_features(path=TEST_MAP):
    """Lower-case first-column labels of test-map rows whose Status is merged, e.g. {'gust', 'wear', '2'}.
    A P1 gate (gust coverage, gust and torn footage) applies only once its row is merged."""
    try:
        with open(path, encoding="utf-8") as fh:
            text = fh.read()
    except OSError:
        return set()
    out = set()
    for line in text.splitlines():
        cells = [c.strip() for c in line.strip().strip("|").split("|")]
        if line.strip().startswith("|") and len(cells) >= 4 and cells[-1].strip("` ").lower() == "merged":
            out.add(re.sub(r"\s*\(.*?\)", "", cells[0]).strip().lower())
    return out


# ---------- GDD 1.3 approved numbers (E29) ----------

def load_manifest(path=None):
    try:
        with open(path or MANIFEST, encoding="utf-8") as fh:
            return json.load(fh)
    except (OSError, ValueError):
        return None


def feature_on(manifest, fid):
    return any(f.get("feature_id") == fid and f.get("default_enabled") is True for f in (manifest or {}).get("features", []))


def approved_start(manifest, key):
    rec = (((manifest or {}).get("approved_parameters") or {}).get("values") or {}).get(key)
    return rec.get("start") if isinstance(rec, dict) else None


def approved_rec(manifest, key):
    rec = (((manifest or {}).get("approved_parameters") or {}).get("values") or {}).get(key)
    return rec if isinstance(rec, dict) else {}


def approved_ok(manifest, key, v):
    """(ok, wanted text) by the shared tunable/fixed rule (tools/tuning.py, also used by tools/bake_preset.py and
    tools/feel_check.py; dry run B H3): in the GDD 1.3 section 5A dev range and on its step, else equal to the
    fixed start."""
    rec = approved_rec(manifest, key)
    r = tuning_mod.rule(manifest, key)
    want = (f"inside the approved range {rec['min']}-{rec['max']} on step {rec['step']}" if r["kind"] == "tunable"
            else f"the fixed value {rec.get('start')}")
    if r["kind"] == "fixed" and r["start"] is None:
        return False, want
    return tuning_mod.value_problem(manifest, key, v) is None, want


def check_gdd(data, ents, manifest, P, single):
    """E29: the encounter uses only enabled features and the GDD 1.3 approved base-bolt numbers."""
    if manifest is None:
        P("E29", "docs/feature-manifest.json", "cannot read the manifest (features and approved_parameters)")
        return
    pats = data["patterns"]
    known = {f.get("feature_id") for f in manifest.get("features", [])}
    close = lambda a, b: isinstance(a, (int, float)) and not isinstance(a, bool) and b is not None and abs(a - b) <= 1e-6
    base = []
    for pid, p in pats.items():
        fid = p.get("feature")
        if fid not in known:
            P("E29", f"patterns.{pid}", f"needs `feature`: the manifest feature ID it builds (got {fid!r}); "
              f"GDD 1.3 approves one base bolt ({BASE_BOLT_FEATURE})")
        elif not feature_on(manifest, fid):
            P("E29", f"patterns.{pid}", f"{fid} is off in the manifest (default_enabled false): the pattern needs that "
              "feature approved and on, through a DECIDED decision row and a manifest PR")
        if fid == BASE_BOLT_FEATURE:
            base.append(pid)
        isec = p.get("interruptible_sec")
        if isinstance(isec, (int, float)) and not isinstance(isec, bool) and isec > 0 and not feature_on(manifest, INTERRUPT_FEATURE):
            P("E29", f"patterns.{pid}", f"interruptible_sec {isec} > 0, but {INTERRUPT_FEATURE} (clock hit disrupts attacks) is off: use 0")
        tiers = p.get("gust_strength_by_wing_tier")
        if isinstance(tiers, list) and len(tiers) > 1 and not feature_on(manifest, WING_FEATURE):
            P("E29", f"patterns.{pid}", f"wing tiers {tiers}, but {WING_FEATURE} (wing hits weaken gusts) is off: use [1.0]")
    if len(base) != 1:
        P("E29", "patterns", f"needs exactly one {BASE_BOLT_FEATURE} base bolt, has {len(base)}")
    ok, want = approved_ok(manifest, "END-01.survival_s", data.get("duration_sec"))
    if not ok:
        P("E29", "duration_sec", f"{data.get('duration_sec')} s, GDD 1.3 END-01.survival_s must be {want} s")
    seed = approved_start(manifest, "OWL-01.seed")
    if data.get("seed") != seed:
        P("E29", "seed", f"{data.get('seed')!r}, GDD 1.3 fixed owl test seed is {seed}")
    if len(base) != 1:
        return
    pid = base[0]
    b = pats[pid]
    ok, want = approved_ok(manifest, "OWL-01.telegraph_delay", b.get("telegraph_sec"))
    if not ok:
        P("E29", f"patterns.{pid}", f"telegraph_sec {b.get('telegraph_sec')}, GDD 1.3 owl warning must be {want} s")
    ok, want = approved_ok(manifest, "OWL-01.projectile_speed", b.get("speed"))
    if not ok:
        P("E29", f"patterns.{pid}", f"speed {b.get('speed')}, GDD 1.3 owl bolt speed must be {want} cm/s")
    if b.get("kind") != "bolt" or b.get("aimed") is not True or b.get("angles_deg") != [0] or b.get("volleys", 1) != 1:
        P("E29", f"patterns.{pid}", "the base bolt is one straight bolt aimed at the snapshot position "
          "(kind bolt, aimed true, angles_deg [0], volleys 1)")
    if not single:
        return
    grace, cad = approved_start(manifest, "OWL-01.initial_grace_s"), approved_start(manifest, "OWL-01.cadence")
    ats = [e["at"] for e in ents if e["pid"] == pid]
    if not ats or grace is None or cad is None:
        P("E29", f"patterns.{pid}", "not scheduled, or the manifest has no OWL-01 grace and cadence")
        return
    if not close(ats[0], grace):
        P("E29", f"schedule.{pid}", f"first telegraph at {ats[0]:.2f} s, GDD 1.3 grace is {grace} s")
    gaps = [round(y - x, 6) for x, y in zip(ats, ats[1:])]
    if gaps:
        ok, want = approved_ok(manifest, "OWL-01.cadence", gaps[0])
        if not ok:
            P("E29", f"schedule.{pid}", f"{gaps[0]:.2f} s between telegraphs, GDD 1.3 owl attack interval must be {want} s")
        cad = gaps[0]
    for (x, y), g in zip(zip(ats, ats[1:]), gaps):
        if not close(g, cad):
            P("E29", f"schedule.{pid}@{y:.2f}s", f"{g:.2f} s after the last one; the owl attack interval is one value ({cad} s)")
            break
    if ats[-1] < data["duration_sec"] - cad - 1e-6 or ats[-1] >= data["duration_sec"]:
        P("E29", f"schedule.{pid}", f"last telegraph at {ats[-1]:.2f} s: the bolts must run every {cad} s until "
          f"the {data['duration_sec']} s end")


def check_state(data, manifest, P):
    """GDD SH1.0 state mode: E28 and E29 on the baseline preset (the S rules run in encounter_spec.check)."""
    if manifest is None:
        P("E29", "docs/feature-manifest.json", "cannot read the manifest (features and approved_parameters)")
        return []
    if tuning_mod.model(manifest)["timeline"]:
        P("E29", "model", f"the manifest is GDD {manifest.get('gdd_revision')}, a timer timeline model: a state-model "
          "encounter.json needs a GDD with a state-driven fight (tools/tuning.py MODELS)")
    for k in ("patterns", "phases", "duration_sec", "seed"):
        if k in data:
            P("E29", k, "a top-level timeline is GDD 1.3 history: GDD SH1.0's fight is the baseline preset; delete it "
              "(the 1.3 data lives in tests/fixtures/gdd13/encounter.json)")
    b = spec_mod.block(data) or {}
    pid = b.get("default")
    p = spec_mod.presets(data).get(pid) if pid else None
    if not isinstance(p, dict) or not p.get("attacks") or not p.get("numbers_from_gdd"):
        P("E28", "encounter_presets", "no baseline preset with attacks and numbers_from_gdd: nothing to check")
        return []
    known = {f.get("feature_id") for f in manifest.get("features", [])}
    for a in p.get("attacks") or []:
        fid = a.get("feature")
        if fid not in known:
            P("E29", f"presets.{pid}.attacks.{a.get('id')}", f"needs `feature`: the manifest Rule ID it builds (got {fid!r})")
        elif not feature_on(manifest, fid):
            P("E29", f"presets.{pid}.attacks.{a.get('id')}", f"{fid} is off in the manifest (default_enabled false)")
    for path, key in sorted((p.get("numbers_from_gdd") or {}).items()):
        v = tuning_mod._path(p, path)
        if not approved_rec(manifest, key):
            P("E29", f"presets.{pid}.{path}", f"names {key}, which is not in the manifest approved_parameters")
            continue
        ok, want = approved_ok(manifest, key, v)
        if not ok:
            P("E29", f"presets.{pid}.{path}", f"{v!r}, GDD {manifest.get('gdd_revision')} {key} must be {want}")
    return [f"preset {pid}: {len(p.get('numbers_from_gdd'))} GDD numbers held to the manifest (E29)"]


# ---------- envelope (V1-V2): the game's measured movement vs the tuning file ----------

def envelope_expected(tuning):
    mv, fps = tuning["movement"], tuning.get("fps", 60)
    tiers = mv["lift_by_tier"]
    return {
        "accel_f": mv["move_speed"] / mv["move_accel"] * fps,
        "fall": mv["max_fall_speed"],
        "rise_intact": mv["ascent_speed"] * tiers["intact"],
        "rise_critical": mv["ascent_speed"] * min(tiers.values()),
        "blend_f": mv["state_blend_s"] * fps,
    }


def check_envelope(line, tuning):
    """line: the FEEL_ENVELOPE line from card 0.13's test. Returns problems (rule, field, msg)."""
    problems = []
    if "FEEL_ENVELOPE" not in (line or ""):
        return [("V1", "line", "not a FEEL_ENVELOPE line")]
    got = dict(re.findall(r"\b(\w+)=(\S+)", line))
    try:
        want = envelope_expected(tuning)
    except (KeyError, TypeError, ValueError) as exc:
        return [("V1", "tuning", f"tuning file is missing a movement field: {exc}")]
    for k in ENVELOPE_FIELDS:
        try:
            v = float(got[k])
        except (KeyError, ValueError):
            problems.append(("V1", k, f"missing or not a number: {got.get(k)!r}"))
            continue
        w = want[k]
        tol = ENVELOPE_FRAMES if k.endswith("_f") else abs(w) * ENVELOPE_PCT
        if abs(v - w) > tol + 1e-9:
            problems.append(("V2", k, f"game measured {v:g}, tuning file gives {w:g} (tolerance {tol:g})"))
    return problems


# ---------- tuning link (E22) ----------

def load_tuning(data, path=None):
    """Return (tuning dict or None, problem text or None)."""
    path = path or data.get("arena", {}).get("tuning_source")
    if not path:
        return None, "arena.tuning_source is missing"
    if not os.path.isabs(path):
        path = os.path.join(ROOT, path)
    try:
        with open(path, encoding="utf-8") as fh:
            return json.load(fh), None
    except (OSError, ValueError) as exc:
        return None, f"cannot read tuning file {path}: {exc}"


def derive(arena, tuning):
    """Hero and bolt sizes and speeds from the tuning file. Raises KeyError/TypeError on a missing field."""
    w, h = arena["width"], arena["height"]
    mv, fg, ts = tuning["movement"], tuning["forgiveness"], tuning["threat_spacing"]
    body_w, body_h = ts["player_body_w_pct_w"] / 100.0 * w, ts["player_body_h_pct_h"] / 100.0 * h
    # The collider is its own data (GDD 1.3 sections 7A, 7C: hitbox extent never reads sprite dimensions); the
    # body art box is only compared with it (alignment), never used to size it (dry run A H5).
    hb = fg["player_hurtbox_cm"]
    hero_w, hero_h = float(hb["w"]), float(hb["h"])
    bolt_r = float(fg["bolt_hitbox_radius_cm"])
    return {
        "body": {"w": body_w, "h": body_h},
        "hero_box": {"w": hero_w, "h": hero_h},
        "hurtbox_area_share": hero_w * hero_h / (body_w * body_h),
        "hero_speed_x": mv["move_speed"] * mv["open_steer_multiplier"] / 100.0,
        "hero_speed_up": mv["ascent_speed"] * min(mv["lift_by_tier"].values()),
        "hero_speed_down": mv["max_fall_speed"],
        "lowest_lift": min(mv["lift_by_tier"].values()),
        "bolt_radius": bolt_r,
        "projectile_hitbox_ratio": bolt_r / arena["bolt_core_radius"],
        "rise_ramp_s": mv["ascent_speed"] / mv["ascent_accel"],
    }


def with_tuning(data, tuning):
    """Copy of data whose arena holds the derived values. Returns (data, problem text or None)."""
    out = dict(data)
    out["arena"] = dict(data["arena"])
    try:
        out["arena"].update(derive(data["arena"], tuning))
    except (KeyError, TypeError, AttributeError, ValueError) as exc:
        return None, f"tuning file is missing a field the sim needs: {exc}"
    return out, None


# ---------- timeline ----------

def phase_bounds(data, ph):
    d = data["duration_sec"]
    return ph["start_pct"] / 100.0 * d, ph["end_pct"] / 100.0 * d


def hero_zone(data, ph):
    z = dict(data["arena"]["hero_zone"])
    cap = ph.get("altitude_cap_y")
    if cap is not None:
        z["y1"] = min(z["y1"], cap)
    return z


def bolt_bullets(data, pat, at, origin_y, aim):
    """Yield (spawn_t, x0, y0, vx, vy) for one scheduled bolt entry."""
    a = data["arena"]
    ox = a["owl_fire_x"]
    if pat.get("aimed"):
        base = math.degrees(math.atan2(aim[1] - origin_y, aim[0] - ox))
    else:
        base = pat.get("base_angle_deg", 180.0)
    out = []
    for v in range(pat.get("volleys", 1)):
        for i, off in enumerate(pat["angles_deg"]):
            ang = math.radians(base + pat.get("seed_offset_deg", 0.0) + v * pat.get("seed_angle_step_deg", 0.0) + off)
            t = at + pat["telegraph_sec"] + v * pat.get("volley_gap_sec", 0.0) + i * pat.get("spawn_offset_sec", 0.0)
            out.append((t, ox, origin_y, pat["speed"] * math.cos(ang), pat["speed"] * math.sin(ang)))
    return out


def arc_path(data, pat, at, origin_y, aim):
    """(spawn_t, flight_sec, pos(u) for u seconds after launch, vmax) for one arc entry."""
    ox = data["arena"]["owl_fire_x"]
    if pat.get("aimed", True):
        dx, dy = aim[0] - ox, aim[1] - origin_y
    else:
        b = math.radians(pat.get("base_angle_deg", 180.0))
        dx, dy = math.cos(b), math.sin(b)
    n = math.hypot(dx, dy) or 1.0
    ux, uy = dx / n, dy / n
    reach, side, f = pat["reach"], pat.get("side", 0.0), pat["flight_sec"]

    def pos(u):
        s = u / f
        along, off = reach * 4.0 * s * (1.0 - s), side * math.sin(2.0 * math.pi * s)
        return ox + ux * along - uy * off, origin_y + uy * along + ux * off
    return at + pat["telegraph_sec"], f, pos, math.hypot(4.0 * reach / f, 2.0 * math.pi * side / f)


def projectiles(data, pat, at, origin_y, aim):
    """List of (spawn_t, expire_t, pos(u), radius, speed) for one bolt or arc entry."""
    a = data["arena"]
    if pat["kind"] == "bolt":
        return [(t, float("inf"), (lambda u, x0=x0, y0=y0, vx=vx, vy=vy: (x0 + vx * u, y0 + vy * u)),
                 a["bolt_radius"], math.hypot(vx, vy))
                for (t, x0, y0, vx, vy) in bolt_bullets(data, pat, at, origin_y, aim)]
    if pat["kind"] == "arc":
        st, f, pos, vmax = arc_path(data, pat, at, origin_y, aim)
        return [(st, st + f, pos, pat["core_radius"] * a["projectile_hitbox_ratio"], vmax)]
    return []


def arc_ok(pat):
    try:
        return pat["reach"] > 0 and 0 < pat["flight_sec"] <= pat["active_sec"] and pat["core_radius"] > 0
    except (KeyError, TypeError):
        return False


def slab_exit(x0, y0, vx, vy, rect):
    """Time after spawn when the point leaves rect (x0,y0 inside or not); 0 if it never enters."""
    t_in, t_out = 0.0, float("inf")
    for p, v, lo, hi in ((x0, vx, rect[0], rect[1]), (y0, vy, rect[2], rect[3])):
        if abs(v) < 1e-9:
            if p < lo or p > hi:
                return 0.0
            continue
        t1, t2 = (lo - p) / v, (hi - p) / v
        t_in, t_out = max(t_in, min(t1, t2)), min(t_out, max(t1, t2))
    return t_out if t_out > t_in else 0.0


def threat_rect(data, zone):
    a = data["arena"]
    hw, hh, r = a["hero_box"]["w"] / 2.0, a["hero_box"]["h"] / 2.0, a["bolt_radius"]
    return (zone["x0"] - hw - r, zone["x1"] + hw + r, zone["y0"] - hh - r, zone["y1"] + hh + r)


def entries(data):
    """Absolute schedule: list of dicts with phase, at, pattern id, window end (for the worst case)."""
    out = []
    a = data["arena"]
    for ph in data["phases"]:
        p0, _ = phase_bounds(data, ph)
        zone = hero_zone(data, ph)
        for e in ph["schedule"]:
            pid = e["pattern"]
            pat = data["patterns"].get(pid)
            at = p0 + e["at"]
            if pat is None:
                out.append({"phase": ph["id"], "at": at, "pid": pid, "end": at, "missing": True})
                continue
            end = at + pat["telegraph_sec"] + pat["active_sec"]
            if pat["kind"] == "arc" and arc_ok(pat):
                end = max(end, at + pat["telegraph_sec"] + pat["flight_sec"])
            if pat["kind"] == "bolt":
                rect = threat_rect(data, zone)
                for dy in a["owl_drift_y"]:
                    for aim in aim_points(data, zone):
                        for (t, x0, y0, vx, vy) in bolt_bullets(data, pat, at, dy, aim):
                            end = max(end, t + slab_exit(x0, y0, vx, vy, rect))
            out.append({"phase": ph["id"], "at": at, "pid": pid, "end": end})
    return sorted(out, key=lambda e: (e["at"], e["pid"]))


def aim_points(data, zone):
    hh = data["arena"]["hero_box"]["h"] / 2.0
    cx = (zone["x0"] + zone["x1"]) / 2.0
    return [(cx, zone["y1"] - hh), (cx, (zone["y0"] + zone["y1"]) / 2.0), (cx, zone["y0"] + hh)]


def clusters(ents):
    out = []
    for e in ents:
        if out and e["at"] < out[-1]["end"]:
            out[-1]["items"].append(e)
            out[-1]["end"] = max(out[-1]["end"], e["end"])
        else:
            out.append({"at": e["at"], "end": e["end"], "items": [e]})
    return out


def longest_gap(data, ph, ents):
    p0, p1 = phase_bounds(data, ph)
    cur, best = p0, 0.0
    for e in sorted((e for e in ents if e["end"] > p0 and e["at"] < p1), key=lambda e: e["at"]):
        best = max(best, min(e["at"], p1) - cur)
        cur = max(cur, e["end"])
    return max(best, p1 - cur)


# ---------- safe path simulation (bit rows) ----------

def simulate(data, cluster, zone, drift_y, aim, bands):
    a = data["arena"]
    hw, hh, r, cell = a["hero_box"]["w"] / 2.0, a["hero_box"]["h"] / 2.0, a["bolt_radius"], a["sim_cell"]
    cx0, cy0 = zone["x0"] + hw, zone["y0"] + hh
    nx = int((zone["x1"] - hw - cx0) // cell) + 1
    ny = int((zone["y1"] - hh - cy0) // cell) + 1
    if nx < 1 or ny < 1:
        return "hero zone smaller than the hero box"
    sx, su, sd = a["hero_speed_x"], a["hero_speed_up"], a["hero_speed_down"]
    full = (1 << nx) - 1
    bullets = []
    for e in cluster["items"]:
        pat = data["patterns"].get(e["pid"])
        if pat and (pat["kind"] == "bolt" or (pat["kind"] == "arc" and arc_ok(pat))):
            bullets += [(b, e["pid"]) for b in projectiles(data, pat, e["at"], drift_y, aim)]
    if not bullets:
        return None
    # Step so no projectile jumps over a hero footprint, and no hero axis moves more than one cell per step.
    dt = min([cell / max(sx, su, sd)] + [(min(hw, hh) + b[3]) / max(b[4], 1e-9) for b, _ in bullets])
    moved = lambda speed, n: int(speed * n * dt // cell) - int(speed * (n - 1) * dt // cell)
    step = 0
    full_zone = a["hero_zone"]  # coverage thirds use the full hero zone, not the capped one
    fx = full_zone["x0"] + (full_zone["x1"] - full_zone["x0"]) / 3.0
    third = (full_zone["y1"] - full_zone["y0"]) / 3.0
    reach = None
    t = cluster["at"]
    while t <= cluster["end"] + dt:
        rows = [0] * ny
        for (st, xt, pos, r, _), pid in bullets:
            if t < st or t > xt:
                continue
            bx, by = pos(t - st)
            if zone["x0"] <= bx <= zone["x1"] and zone["y0"] <= by <= zone["y1"]:
                if by >= full_zone["y1"] - third:
                    bands.setdefault(pid, set()).add("pos_high")
                if by <= full_zone["y0"] + third:
                    bands.setdefault(pid, set()).add("pos_low")
                if bx <= fx:
                    bands.setdefault(pid, set()).add("pos_far")
            ilo = max(0, math.floor((bx - hw - r - cx0) / cell))
            ihi = min(nx - 1, math.ceil((bx + hw + r - cx0) / cell))
            jlo = max(0, math.floor((by - hh - r - cy0) / cell))
            jhi = min(ny - 1, math.ceil((by + hh + r - cy0) / cell))
            if ilo > ihi or jlo > jhi:
                continue
            m = ((1 << (ihi - ilo + 1)) - 1) << ilo
            for j in range(jlo, jhi + 1):
                rows[j] |= m
        safe = [full & ~row for row in rows]
        if reach is None:
            # The hero starts where the aimed bolts aim (the aim point), not anywhere it likes.
            i0 = min(nx - 1, max(0, round((aim[0] - cx0) / cell)))
            j0 = min(ny - 1, max(0, round((aim[1] - cy0) / cell)))
            reach = [(1 << i0) & safe[j] if j == j0 else 0 for j in range(ny)]
        else:
            step += 1
            kx, ku, kd = moved(sx, step), moved(su, step), moved(sd, step)
            grown = []
            for row in reach:
                g = row
                for _ in range(kx):
                    g |= (g << 1) | (g >> 1)
                grown.append(g & full)
            reach = []
            for j in range(ny):
                g = 0
                # row j is reached from below (k < j, rising) or from above (k > j, falling)
                for k in range(max(0, j - ku), min(ny, j + kd + 1)):
                    g |= grown[k]
                reach.append(g & safe[j])
        if not any(reach):
            return f"no hero-sized safe path at t={t:.2f} s"
        t += dt
    return None


# ---------- pacing helpers ----------

def busy_time(ents, t0, t1):
    """Seconds in [t0, t1] with at least one attack in telegraph, active or flight."""
    total, cur = 0.0, t0
    for e in sorted(ents, key=lambda e: e["at"]):
        s, f = max(e["at"], cur), min(e["end"], t1)
        if f > s:
            total += f - s
            cur = f
    return total


def longest_window(ents, t0, t1):
    """Longest stretch in [t0, t1] with no attack."""
    if t1 <= t0:
        return 0.0
    cur, best = t0, 0.0
    for e in sorted((e for e in ents if e["end"] > t0 and e["at"] < t1), key=lambda e: e["at"]):
        best = max(best, min(e["at"], t1) - cur)
        cur = max(cur, e["end"])
    return max(best, t1 - cur)


def camp_spots(data, zone, n=CAMP_GRID):
    """n x n grid of hero centres over the zone; corners and (for odd n) the centre are on it."""
    hw, hh = data["arena"]["hero_box"]["w"] / 2.0, data["arena"]["hero_box"]["h"] / 2.0
    xl, xr, yb, yt = zone["x0"] + hw, zone["x1"] - hw, zone["y0"] + hh, zone["y1"] - hh
    out = []
    for j in range(n):
        for i in range(n):
            out.append((f"grid({i},{j})", (xl + (xr - xl) * i / (n - 1), yb + (yt - yb) * j / (n - 1))))
    return out


def spot_hit(data, pat, at, drift_y, spot):
    """True if any bolt or arc of this entry (aimed ones aim at the spot) touches a still hero at spot."""
    a = data["arena"]
    hw, hh = a["hero_box"]["w"] / 2.0, a["hero_box"]["h"] / 2.0
    if pat["kind"] == "bolt":
        r = a["bolt_radius"]
        rect = (spot[0] - hw - r, spot[0] + hw + r, spot[1] - hh - r, spot[1] + hh + r)
        return any(slab_exit(x0, y0, vx, vy, rect) > 0 for (_, x0, y0, vx, vy) in bolt_bullets(data, pat, at, drift_y, spot))
    if pat["kind"] == "arc" and arc_ok(pat):
        for st, xt, pos, r, v in projectiles(data, pat, at, drift_y, spot):
            du = min(hw, hh, r) / max(v, 1e-9)
            u = 0.0
            while u <= xt - st:
                x, y = pos(u)
                if abs(x - spot[0]) <= hw + r and abs(y - spot[1]) <= hh + r:
                    return True
                u += du
    return False


# ---------- checks ----------

def check(data, md_text=None, tuning=None, merged=None, manifest=None):
    """tuning: the tuning dict; None = load arena.tuning_source from the repo.
    merged: merged test-map row labels; None = read pipeline/qa/test-map.md.
    manifest: the feature manifest dict; None = read docs/feature-manifest.json."""
    problems, numbers, bands = [], [], {}
    P = lambda rule, where, msg: problems.append((rule, where, msg))
    if data.get("model") == "state":
        numbers += check_state(data, load_manifest() if manifest is None else manifest, P)
        return problems, numbers
    man = load_manifest() if manifest is None else manifest
    if man and not tuning_mod.model(man)["timeline"]:
        P("E29", "model", f"this is a timer timeline (GDD 1.3 history), but the manifest is GDD {man.get('gdd_revision')}, "
          "whose fight is state-driven: use the encounter.json baseline preset (`\"model\": \"state\"`)")
    merged = merged_features() if merged is None else merged
    if not data.get("patterns") or not data.get("phases"):
        P("E28", "patterns" if not data.get("patterns") else "phases", "no patterns or no phases: nothing to check")
        return problems, numbers

    # E22 tuning link: speeds and boxes come from the Game Designer's file, never a copy here
    for k in TUNED_KEYS:
        if k in data.get("arena", {}):
            P("E22", f"arena.{k}", "copy of a tuning value; delete it, the checker reads it from arena.tuning_source")
    err = None
    if tuning is None:
        tuning, err = load_tuning(data)
    if err is None:
        data, err = with_tuning(data, tuning)
    if err:
        P("E22", "arena.tuning_source", err)
        return problems, numbers
    pats, phases, a = data["patterns"], data["phases"], data["arena"]
    manifest = load_manifest() if manifest is None else manifest
    used = {e.get("pattern") for ph in phases for e in ph.get("schedule", []) if e.get("pattern") in pats}
    multi = len(used) > 1          # rules about mixing patterns apply only when 2+ patterns are scheduled
    numbers.append(f"tuning: hurtbox {a['hero_box']['w']:.0f}x{a['hero_box']['h']:.0f} "
                   f"({a['hurtbox_area_share'] * 100:.0f}% of body area), speed x {a['hero_speed_x']:.0f} "
                   f"up {a['hero_speed_up']:.0f} down {a['hero_speed_down']:.0f} cm/s, bolt hitbox r {a['bolt_radius']:.1f}")
    if a["hurtbox_area_share"] > MAX_HURTBOX_AREA + 1e-9:
        P("E22", "tuning.forgiveness.player_hurtbox_cm",
          f"hurtbox is {a['hurtbox_area_share'] * 100:.0f}% of the body art area > {MAX_HURTBOX_AREA * 100:.0f}%: "
          "align the art (scale, pivot, offset); a collider change is a separate approved change")

    # E23 owl hitbox
    osp, ohb = a.get("owl_sprite"), a.get("owl_hitbox")
    if not (osp and ohb):
        P("E23", "arena", "needs owl_sprite and owl_hitbox {w, h}")
    elif ohb["w"] * ohb["h"] < MIN_OWL_HITBOX_AREA * osp["w"] * osp["h"] - 1e-9:
        P("E23", "arena.owl_hitbox", f"owl hitbox is {ohb['w'] * ohb['h'] / (osp['w'] * osp['h']) * 100:.0f}% "
          f"of the owl sprite area < {MIN_OWL_HITBOX_AREA * 100:.0f}%")

    # E17 arena
    w = a["width"]
    oz, hz = a["owl_zone"], a["hero_zone"]
    if oz["x0"] < w / 2.0:
        P("E17", "arena.owl_zone", f"owl zone starts at x={oz['x0']}, left of the middle ({w / 2.0})")
    if hz["x1"] > oz["x0"]:
        P("E17", "arena", "hero zone and owl zone overlap")
    if not (oz["x0"] <= a["owl_fire_x"] <= oz["x1"]):
        P("E17", "arena.owl_fire_x", "fire point is outside the owl zone")
    if min(a["owl_drift_y"]) < 0 or max(a["owl_drift_y"]) > a["height"]:
        P("E17", "arena.owl_drift_y", "drift goes outside the arena")

    for pid, p in pats.items():
        where = f"patterns.{pid}"
        kind = p.get("kind")
        if kind not in KIND_COLOR:
            P("E1", where, f"unknown kind {kind!r}")
            continue
        tell = p.get("tell", {})
        if p.get("telegraph_sec", 0) < MIN_TELEGRAPH_SEC:
            P("E1", where, f"telegraph_sec {p.get('telegraph_sec', 0)} < {MIN_TELEGRAPH_SEC}")
        if not (tell.get("pose") or tell.get("vfx")):
            P("E1", where, "no visual tell (pose or vfx); sound alone is not enough")
        elif kind in PROJECTILE_KINDS and not (tell.get("pose") and tell.get("sound") and tell.get("vfx")):
            P("E1", where, "a ranged attack needs a layered tell: pose, sound and vfx all set")
        if p.get("active_sec", 0) <= 0 or p.get("recovery_sec", -1) < 0:
            P("E2", where, "needs active_sec > 0 and recovery_sec >= 0")
        if p.get("color") != KIND_COLOR[kind]:
            P("E9", where, f"{kind} must use colour {KIND_COLOR[kind]!r}, has {p.get('color')!r}")
        if kind in PROJECTILE_KINDS and not (p.get("draw_on_top") and p.get("directional_sprite")):
            P("E10", where, "projectile needs draw_on_top and directional_sprite")
        if p.get("origin_locked_during_telegraph") is not True:
            P("E12", where, "origin_locked_during_telegraph must be true")
        isec = p.get("interruptible_sec")
        if not isinstance(isec, (int, float)) or isinstance(isec, bool) or isec < 0:
            P("E26", where, "needs interruptible_sec >= 0 (0 = a clock hit does not disrupt it)")
        elif isec > MAX_INTERRUPT_SEC + 1e-9:
            P("E26", where, f"interruptible_sec {isec} > {MAX_INTERRUPT_SEC} (GDD §5: briefly)")
        elif isec > 0 and p.get("interrupt_replays_telegraph") is not True:
            P("E26", where, "an interruptible pattern needs interrupt_replays_telegraph true "
              "(an interrupt never shortens a telegraph already showing)")
        if kind == "gust":
            tiers = p.get("gust_strength_by_wing_tier")
            if (not isinstance(tiers, list) or not tiers
                    or any(not isinstance(v, (int, float)) or isinstance(v, bool) for v in tiers)):
                P("E27", where, "needs gust_strength_by_wing_tier, a list of numbers ([1.0] = wing hits cut)")
            elif abs(tiers[0] - 1.0) > 1e-9 or any(not (0 < v <= 1.0) for v in tiers) \
                    or any(b > x + 1e-9 for x, b in zip(tiers, tiers[1:])):
                P("E27", where, "gust_strength_by_wing_tier must start at 1.0, never rise, and stay in (0, 1]")
            elif len(tiers) > 1:
                ov = p.get("wing_tear_overlays")
                if not isinstance(ov, list) or len(ov) != len(tiers) - 1 or not all(str(o).strip() for o in ov):
                    P("E27", where, f"needs wing_tear_overlays: {len(tiers) - 1} texture name(s), one per damaged "
                      "tier (the player must see the wing tear)")
        if kind == "bolt":
            ang = sorted(p.get("angles_deg", []))
            n, vol = len(ang), p.get("volleys", 1)
            if n == 0:
                P("E11", where, "no angles")
                continue
            need = (vol - 1) * p.get("volley_gap_sec", 0.0) + (n - 1) * p.get("spawn_offset_sec", 0.0)
            if p["active_sec"] + 1e-9 < need:
                P("E2", where, f"active_sec {p['active_sec']} shorter than volleys + stagger ({need:.2f})")
            if n > 1:
                gaps = [b - x for x, b in zip(ang, ang[1:])]
                med = statistics.median(gaps)
                for i, x in enumerate(ang):
                    near = min(gaps[i - 1] if i > 0 else float("inf"), gaps[i] if i < n - 1 else float("inf"))
                    if near > LONE_GAP_FACTOR * med + 1e-9:
                        P("E11", where, f"angle {x} is a lone bullet outside the group")
                if p.get("spawn_offset_sec", 0) <= 0:
                    P("E11", where, "spread needs spawn_offset_sec > 0 (staggered spawns)")
                if p.get("aimed") and n % 2 == 1 and not p.get("odd_count_reason"):
                    P("E11", where, "aimed spread has an odd count; make it even or write odd_count_reason")
            if vol > 1 and not p.get("seed_angle_step_deg"):
                P("E11", where, "volleys > 1 need seed_angle_step_deg != 0")
        if kind == "arc" and not arc_ok(p):
            P("E2", where, "arc needs reach > 0, 0 < flight_sec <= active_sec and core_radius > 0")
        if kind == "gust":
            g = p.get("zone")
            if not g or g["x0"] < hz["x0"] or g["x1"] > hz["x1"] or g["y0"] < hz["y0"] or g["y1"] > hz["y1"]:
                P("E15", where, "gust zone missing or outside the hero zone")
            elif max(g["y0"] - hz["y0"], hz["y1"] - g["y1"]) < a["hero_box"]["h"]:
                P("E15", where, "no hero-sized lane above or below the gust (cannot choose to avoid it)")

    # E3 phases (GDD 1.3 §8: optional presets; one base phase or the three presets)
    ids = [ph["id"] for ph in phases]
    if ids not in (PHASE_IDS, BASE_PHASE):
        P("E3", "phases", f"phases must be {BASE_PHASE} or {PHASE_IDS} in order, got {ids}")
    edge = 0
    for ph in phases:
        if ph["start_pct"] != edge or ph["end_pct"] <= ph["start_pct"]:
            P("E3", f"phases.{ph['id']}", f"must start at {edge}% and end after it")
        edge = ph["end_pct"]
    if edge != 100:
        P("E3", "phases", f"last phase ends at {edge}%, not 100%")
    desp = [ph for ph in phases if ph["id"] == "desperation"]
    if desp and desp[0]["end_pct"] - desp[0]["start_pct"] > MAX_DESPERATION_PCT:
        P("E3", "phases.desperation", f"desperation is {desp[0]['end_pct'] - desp[0]['start_pct']}% > {MAX_DESPERATION_PCT}%")

    # E4 distinct, E5 cue
    prev = None
    for ph in phases:
        cur = {("p", e["pattern"]) for e in ph["schedule"]} | {("s", s) for s in ph.get("space_rules", [])}
        if multi and prev is not None and not (cur - prev):
            P("E4", f"phases.{ph['id']}", "adds or swaps no pattern or space rule (speed alone is not a new phase)")
        prev = cur
        if "cue" in ph or "phase_change_cue" in ph:
            P("E5", f"phases.{ph['id']}", "phases may not set their own cue; one phase_change_cue for all")
        if ph.get("altitude_cap_y") is not None and "altitude_cap" not in ph.get("space_rules", []):
            P("E4", f"phases.{ph['id']}", "altitude_cap_y set without the altitude_cap space rule")
    if len(phases) > 1 and not data.get("phase_change_cue"):
        P("E5", "phase_change_cue", "missing (needed with more than one phase)")

    ents = entries(data)
    for e in ents:
        if e.get("missing"):
            P("E3", f"phases.{e['phase']}", f"schedule names unknown pattern {e['pid']}")
    ents = [e for e in ents if not e.get("missing")]

    # E6 intro
    intro = [e for e in ents if e["phase"] == "intro"]
    gusts = 0
    for e in intro:
        p = pats[e["pid"]]
        if p["kind"] == "arc" or (p["kind"] == "bolt" and len(p["angles_deg"]) * p.get("volleys", 1) > 1):
            P("E6", f"phases.intro.{e['pid']}", "intro uses only single bolts and one gust")
        gusts += p["kind"] == "gust"
    if gusts > MAX_INTRO_GUSTS:
        P("E6", "phases.intro", f"{gusts} gusts > {MAX_INTRO_GUSTS}")
    for x, y in zip(intro, intro[1:]) if multi else []:
        if y["at"] < x["end"]:
            P("E6", "phases.intro", f"{x['pid']} and {y['pid']} overlap at {y['at']:.1f} s (one attack at a time)")

    # E29 GDD 1.3 approved numbers
    check_gdd(data, ents, manifest, P, single=not multi)

    # E7 first use alone
    seen = set() if multi else set(used)
    for e in ents:
        if e["pid"] in seen:
            continue
        seen.add(e["pid"])
        for o in ents:
            if o is not e and o["at"] < e["end"] and e["at"] < o["end"]:
                P("E7", f"{e['phase']}.{e['pid']}", f"first use overlaps {o['pid']} at {max(e['at'], o['at']):.1f} s")
                break

    # E8 breather
    for ph in phases:
        g = longest_gap(data, ph, ents)
        numbers.append(f"breather {ph['id']}: {g:.1f} s")
        if multi and g < MIN_BREATHER_SEC:
            P("E8", f"phases.{ph['id']}", f"longest window with no attack {g:.1f} s < {MIN_BREATHER_SEC} s")

    # E26 clock interrupts: every interruptible attack late by its pause plus a replayed telegraph
    late = []
    for e in ents:
        pat = pats.get(e["pid"], {})
        isec = pat.get("interruptible_sec")
        ok = isinstance(isec, (int, float)) and not isinstance(isec, bool) and isec > 0
        late.append(dict(e, end=e["end"] + (isec + pat.get("telegraph_sec", 0) if ok else 0.0)))
    for ph in phases:
        g = longest_gap(data, ph, late)
        numbers.append(f"breather {ph['id']} with clock interrupts: {g:.1f} s")
        if multi and g < MIN_BREATHER_SEC:
            P("E26", f"phases.{ph['id']}", f"with clock interrupts the longest breather is {g:.1f} s "
              f"< {MIN_BREATHER_SEC} s; shorten interruptible_sec or widen a gap")

    # E13 safe path
    by_phase = {ph["id"]: ph for ph in phases}
    for c in clusters(ents):
        zone = hero_zone(data, by_phase[c["items"][0]["phase"]])
        for dy in a["owl_drift_y"]:
            for aim in aim_points(data, zone):
                err = simulate(data, c, zone, dy, aim, bands)
                if err:
                    names = "+".join(sorted({e["pid"] for e in c["items"]}))
                    P("E13", f"{c['items'][0]['phase']}@{c['at']:.1f}s {names}",
                      f"owl drift y={dy}, aim y={aim[1]:.0f}: {err}")
                    break
            else:
                continue
            break
    if any(pats[e["pid"]]["kind"] == "arc" for e in ents):
        numbers.append("note: arcs are simulated as an out-and-back loop on the data; the real curve is "
                       "[VERIFY in engine: UmbrellaElla.Owl.World.SafePathAtDriftExtremes]")

    # E14 coverage
    early = {e["pid"] for e in ents if e["phase"] in ("intro", "contest")}
    for row in COVERAGE_ROWS if multi else []:
        if row in P1_COVERAGE and P1_COVERAGE[row] not in merged:
            continue
        if not any(row in pats[pid].get("covers", []) for pid in early):
            P("E14", f"coverage.{row}", "no pattern used by the end of phase 2 covers this row")
    for pid, p in pats.items():
        if p.get("kind") in PROJECTILE_KINDS and pid in {e["pid"] for e in ents}:
            for row in p.get("covers", []):
                if row.startswith("pos_") and row not in bands.get(pid, set()):
                    P("E14", f"patterns.{pid}", f"claims {row} but no bolt reaches that third of the hero zone")

    # E19 intensity: share = time with any attack on; density = attack-seconds per second (overlaps add up)
    share, dens = {}, {}
    for ph in phases:
        p0, p1 = phase_bounds(data, ph)
        n = ph["id"]
        span = max(p1 - p0, 1e-9)
        share[n] = busy_time(ents, p0, p1) / span
        dens[n] = sum(max(0.0, min(e["end"], p1) - max(e["at"], p0)) for e in ents) / span
        numbers.append(f"intensity {n}: share {share[n] * 100:.0f}%, density {dens[n]:.2f}")
        if multi and share[n] > MAX_THREAT_SHARE + 1e-9:
            P("E19", f"phases.{n}", f"threat share {share[n] * 100:.0f}% > {MAX_THREAT_SHARE * 100:.0f}% (constant pressure)")
    if multi and {"intro", "contest", "desperation"} <= set(dens):
        if dens["intro"] > dens["contest"] + 1e-9:
            P("E19", "phases.intro", "intro is denser than contest (the ramp goes down)")
        if dens["desperation"] > DESP_VS_CONTEST_MAX * dens["contest"] + 1e-9:
            P("E19", "phases.desperation", f"desperation density is {dens['desperation'] / max(dens['contest'], 1e-9):.2f}x "
              f"contest > {DESP_VS_CONTEST_MAX}x")
    peaks = [c for c in clusters(ents) if len(c["items"]) >= 2] if multi else []
    for x, y in zip(peaks, peaks[1:]):
        g = longest_window(ents, x["end"], y["at"])
        if g < MIN_BREATHER_SEC:
            P("E19", f"peaks@{x['at']:.1f}s+{y['at']:.1f}s", f"only {g:.1f} s of calm between two peaks < {MIN_BREATHER_SEC} s")

    # E20 camping: a still hero anywhere on the grid gets hit in every phase after intro
    for ph in phases[1:] if len(phases) > 1 else phases:
        zone = hero_zone(data, ph)
        pe = [e for e in ents if e["phase"] == ph["id"] and pats[e["pid"]]["kind"] in PROJECTILE_KINDS]
        for name, spot in camp_spots(data, zone):
            for dy in a["owl_drift_y"]:
                if not any(spot_hit(data, pats[e["pid"]], e["at"], dy, spot) for e in pe):
                    P("E20", f"phases.{ph['id']}", f"a hero standing still at {name} {tuple(round(v) for v in spot)} "
                      f"is never hit (owl drift y={dy}); camping there wins")
                    break

    # E21 layering in contest
    def layered(c):
        k = {pats[e["pid"]].get("aimed", False) for e in c["items"] if pats[e["pid"]]["kind"] == "bolt"}
        return k == {True, False}
    if multi and not any(layered(c) for c in clusters(ents) if c["items"][0]["phase"] == "contest"):
        P("E21", "phases.contest", "no cluster layers an aimed bolt pattern with a non-aimed one")

    # E24 midpoint turn
    con = [ph for ph in phases if ph["id"] == "contest"]
    if multi and con:
        c0, c1 = phase_bounds(data, con[0])
        mid = (c0 + c1) / 2.0
        firsts = {}
        for e in ents:
            firsts.setdefault(e["pid"], e["at"])
        late = sorted(pid for pid, t in firsts.items() if mid <= t < c1)
        numbers.append(f"contest midpoint {mid:.1f} s: new pattern(s) {', '.join(late) or 'none'}")
        if not late:
            P("E24", "phases.contest", f"no pattern makes its first appearance between the midpoint ({mid:.1f} s) and the end ({c1:.1f} s)")

    # E25 recovery: the torn umbrella can still climb back from the bottom within one breather.
    # Only with lift loss on (SURV-04; GDD 1.3 §6: "If worn umbrella reduces lift, require a test").
    last = desp or [ph for ph in phases if ph["id"] == "base"]
    if last and a["lowest_lift"] < 1.0 - 1e-9:
        zone = hero_zone(data, last[0])
        climb = (zone["y1"] - zone["y0"]) - a["hero_box"]["h"]
        need = max(climb, 0.0) / max(a["hero_speed_up"], 1e-9) + a["rise_ramp_s"] / 2.0
        have = longest_gap(data, last[0], ents)
        numbers.append(f"recovery {last[0]['id']}: bottom-to-cap climb {climb:.0f} uu at the lowest lift takes "
                       f"{need:.1f} s; longest breather {have:.1f} s")
        if need > have + 1e-9:
            P("E25", f"phases.{last[0]['id']}", f"climbing back from the bottom takes {need:.1f} s at the lowest lift tier, "
              f"longer than the longest breather ({have:.1f} s); lower the cap or widen a breather")

    # E16 end event
    ev = data.get("end_event", {})
    if not (ev.get("stop_threats") and ev.get("owl_departs") and ev.get("survived_card")):
        P("E16", "end_event", "needs stop_threats, owl_departs and survived_card")
    if ev.get("quiet_sec", 0) < MIN_END_QUIET_SEC:
        P("E16", "end_event", f"quiet_sec {ev.get('quiet_sec', 0)} < {MIN_END_QUIET_SEC}")

    if desp:
        numbers.append(f"desperation share: {desp[0]['end_pct'] - desp[0]['start_pct']}% of {data['duration_sec']} s")

    # E18 doc
    if md_text is not None:
        m = re.search(re.escape(BEGIN) + r"\n(.*?)" + re.escape(END), md_text, re.S)
        if not m or m.group(1) != render(data, ents):
            P("E18", "pipeline/level/encounter.md", "generated block is stale; run with --write-md")
    return problems, numbers


# ---------- markdown ----------

def render(data, ents=None):
    ents = ents if ents is not None else [e for e in entries(data) if not e.get("missing")]
    pats = data["patterns"]
    cue = data.get("phase_change_cue")
    lines = [f"Encounter length: {data['duration_sec']} s ({data.get('duration_status', '')}). "
             + (f"Phase-change cue: `{cue}` (same every run)." if cue else "One phase, no phase-change cue.")
             + (f" Seed: {data['seed']}." if "seed" in data else ""),
             f"End clue: {data.get('end_event', {}).get('clue') or '- (optional; narrative is DEFERRED)'}.", "",
             "### Phases", "", "| Phase | % of timer | Seconds | Patterns | Space rules | Longest breather |",
             "|---|---|---|---|---|---|"]
    for ph in data["phases"]:
        p0, p1 = phase_bounds(data, ph)
        used = sorted({e["pattern"] for e in ph["schedule"]})
        lines.append(f"| {ph['id']} | {ph['start_pct']}-{ph['end_pct']} | {p0:.1f}-{p1:.1f} | {', '.join(used)} | "
                     f"{', '.join(ph.get('space_rules', [])) or '-'} | {longest_gap(data, ph, ents):.1f} s |")
    lines += ["", "### Patterns", "",
              "| ID | Feature | Kind | Colour | Telegraph / active / recovery s | Count x volleys | Angles | Aimed | Speed | Stagger s | Seed step | Clock-hit pause s | Tell (pose / sound / VFX) |",
              "|---|---|---|---|---|---|---|---|---|---|---|---|---|"]
    for pid, p in pats.items():
        t = p.get("tell", {})
        cnt = f"{len(p.get('angles_deg', []))} x {p.get('volleys', 1)}" if p["kind"] == "bolt" else "-"
        shape = p.get("angles_deg", "-")
        if p["kind"] == "arc":
            cnt = "1 x 1"
            shape = f"loop: reach {p.get('reach', '-')}, side {p.get('side', '-')}, back in {p.get('flight_sec', '-')} s"
        lines.append(f"| {pid} | {p.get('feature') or '-'} | {p['kind']} | {p.get('color') or '-'} | {p['telegraph_sec']} / {p['active_sec']} / {p['recovery_sec']} | "
                     f"{cnt} | {shape} | {'yes' if p.get('aimed') else 'no'} | {p.get('speed', '-')} | "
                     f"{p.get('spawn_offset_sec', '-')} | {p.get('seed_angle_step_deg', '-')} | "
                     f"{p.get('interruptible_sec', '-')} | {t.get('pose') or '-'} / {t.get('sound') or '-'} / {t.get('vfx') or '-'} |")
    wings = [f"{pid}: gust strength by wing tier {p.get('gust_strength_by_wing_tier')}, "
             f"tear overlays {p.get('wing_tear_overlays') or '-'}" for pid, p in pats.items() if p["kind"] == "gust"]
    if wings:
        lines += [""] + ["Wing hits (E27): " + w + "." for w in wings]
    early = {e["pid"] for e in ents if e["phase"] in ("intro", "contest", "base")}
    ids = list(pats)
    lines += ["", "### Coverage (with 2+ patterns, rows must have an X in a pattern used by the end of contest)", "",
              "| Row | " + " | ".join(ids) + " |", "|---|" + "---|" * len(ids)]
    for row in COVERAGE_ROWS:
        cells = [("X" if pid in early else "x (late)") if row in pats[pid].get("covers", []) else "" for pid in ids]
        lines.append(f"| {row} | " + " | ".join(cells) + " |")
    return "\n".join(lines) + "\n"


def write_md(data, md_path):
    with open(md_path, encoding="utf-8") as fh:
        text = fh.read()
    block = BEGIN + "\n" + render(data) + END
    pat = re.compile(re.escape(BEGIN) + r".*?" + re.escape(END), re.S)
    if not pat.search(text):
        raise SystemExit(f"{md_path}: generated markers not found")
    with open(md_path, "w", encoding="utf-8") as fh:
        fh.write(pat.sub(lambda _: block, text))


# ---------- playtest log (L1-L5) ----------

def check_playtest(data, paths):
    """Returns (problems, report lines). problems: (rule, 'file:line', msg)."""
    problems, stats = [], {}
    known = set(data.get("patterns", {})) | {BOTTOM_EXIT}
    phases_ok = set(PLAYTEST_PHASES)
    if data.get("model") == "state":   # GDD SH1.0: the baseline preset's attacks and phases (wings, mechanisms, clock)
        p = spec_mod.presets(data).get((spec_mod.block(data) or {}).get("default")) or {}
        known |= {a.get("id") for a in p.get("attacks") or []}
        phases_ok |= {ph.get("id") for ph in p.get("phases") or []}
    for path in paths:
        with open(path, encoding="utf-8", newline="") as fh:
            rows = list(csv.reader(fh))
        name = os.path.basename(path)
        if not rows or [c.strip() for c in rows[0]] != PLAYTEST_COLUMNS:
            problems.append(("L1", f"{name}:1", f"header must be {','.join(PLAYTEST_COLUMNS)}"))
            continue
        for n, raw in enumerate(rows[1:], start=2):
            if not any(c.strip() for c in raw):
                continue
            where = f"{name}:{n}"
            if len(raw) != len(PLAYTEST_COLUMNS):
                problems.append(("L5", where, f"{len(raw)} columns, need {len(PLAYTEST_COLUMNS)}"))
                continue
            r = dict(zip(PLAYTEST_COLUMNS, (c.strip() for c in raw)))
            ev = r["event"]
            if ev not in PLAYTEST_EVENTS:
                problems.append(("L2", where, f"event {ev!r} is not hit, death or survive"))
                continue
            if r["phase"] not in phases_ok:
                problems.append(("L5", where, f"phase {r['phase']!r} is not one of {sorted(phases_ok)}"))
            try:
                if float(r["t_run_s"]) < 0:
                    raise ValueError
            except ValueError:
                problems.append(("L5", where, f"t_run_s {r['t_run_s']!r} is not a number >= 0"))
            if not r["session"] or not r["build"]:
                problems.append(("L5", where, "session and build must be set"))
            if ev == "survive":
                continue
            pid = r["pattern_id"]
            if not pid:
                problems.append(("L3", where, f"{ev} row has no pattern_id (what hit them?)"))
                continue
            if pid not in known:
                problems.append(("L3", where, f"pattern_id {pid!r} is not in encounter.json (or {BOTTOM_EXIT})"))
                continue
            if r["explained"] not in ("y", "n"):
                problems.append(("L4", where, f"explained {r['explained']!r} must be y or n"))
                continue
            s = stats.setdefault(pid, {"hit": 0, "death": 0, "n": 0})
            s[ev] += 1
            s["n"] += r["explained"] == "n"
        if not any(len(raw) == len(PLAYTEST_COLUMNS) and raw[1].strip() in PLAYTEST_EVENTS for raw in rows[1:]):
            problems.append(("L6", f"{name}:2", "no hit, death or survive row: an empty log is not a playtest"))
    report = ["pattern_id | hits | deaths | explained=n"]
    for pid in sorted(stats):
        s = stats[pid]
        flag = "  <- bug against this pattern: fix the tell" if s["n"] else ""
        report.append(f"{pid} | {s['hit']} | {s['death']} | {s['n']}{flag}")
    return problems, report


# ---------- wiring (W1-W5) and card (C1-C5) ----------

def _read(root, rel):
    path = os.path.join(root, rel)
    if not os.path.exists(path):
        return ""
    with open(path, encoding="utf-8") as fh:
        return fh.read()


def owl_tests(data=None):
    """Owl engine tests an encounter needs: the phase tests only when it has more than one phase."""
    if data is None:
        try:
            with open(DEFAULT_DATA, encoding="utf-8") as fh:
                data = json.load(fh)
        except (OSError, ValueError):
            data = {}
    multi_phase = len(data.get("phases") or []) > 1
    return [t for t in OWL_TESTS if multi_phase or t not in OWL_PHASE_TESTS]


def check_wiring(root=ROOT):
    """Are the cards, tests and docs the encounter rules depend on filed? Returns problems."""
    problems = []
    P = lambda rule, where, msg: problems.append((rule, where, msg))
    rows = [l for l in _read(root, "pipeline/day0-cards.md").splitlines() if l.startswith("|")]
    for name, must in OWL_CARDS:
        if not any(name in l and must in l for l in rows):
            P("W1", "pipeline/day0-cards.md", f"no row for the {name!r} card whose Done when names {must!r}")
    tmap = _read(root, "pipeline/qa/test-map.md")
    try:
        enc = json.loads(_read(root, "pipeline/level/encounter.json") or "{}")
    except ValueError:
        enc = {}
    for t in owl_tests(enc):
        if t not in tmap:
            P("W2", "pipeline/qa/test-map.md", f"{t} is not listed")
    want = ",".join(PLAYTEST_COLUMNS)
    cols = re.findall(r"Columns:\s*`([^`]*)`", _read(root, "pipeline/qa/playtests.md"))
    if want not in [c.replace(" ", "") for c in cols]:
        P("W3", "pipeline/qa/playtests.md", f"needs Columns: `{want}` (has {cols or 'none'})")
    if not any(l.startswith("|") and "pipeline/roles/level-designer.md" in l
               for l in _read(root, "AGENTS.md").splitlines()):
        P("W4", "AGENTS.md", "roles table has no row for pipeline/roles/level-designer.md")
    if "encounter_check.py" not in _read(root, "pipeline/roles/game-designer.md"):
        P("W5", "pipeline/roles/game-designer.md", "does not name encounter_check.py as its review criteria")
    if spec_mod.block(enc) is not None:
        if not any(l.startswith("|") and "pipeline/roles/encounter-designer.md" in l
                   for l in _read(root, "AGENTS.md").splitlines()):
            P("W6", "AGENTS.md", "roles table has no row for pipeline/roles/encounter-designer.md")
        for must in ("encounter_check.py --ready", "encounter_check.py --playthrough"):
            if not any(must in l for l in rows):
                P("W6", "pipeline/day0-cards.md", f"no row whose Done when names {must!r}")
        for t in ENCOUNTER_TESTS:
            if t not in tmap:
                P("W6", "pipeline/qa/test-map.md", f"{t} is not listed")
    return problems


SIGNED = r"\S.*\s\d{4}-\d{2}-\d{2}\s*$"


def check_card_text(text, data=None):
    """Lines an encounter card must carry before review. Returns problems (rule, where, msg).
    data: the encounter (None = pipeline/level/encounter.json); it decides whether the phase tests apply."""
    problems = []
    P = lambda rule, msg: problems.append((rule, "card", msg))
    lines = text.splitlines()
    has = lambda rx: any(re.search(rx, l) for l in lines)
    if not has(r"encounter_check: 0 problem\(s\)"):
        P("C1", "no pasted `encounter_check: 0 problem(s)` line")
    if not has(r"^\W*Coverage signed: (?!<)" + SIGNED):
        P("C2", "no `Coverage signed: <name> <YYYY-MM-DD>` line")
    for label in ("Accent check", "Motion check"):
        if not has(r"^\W*" + label + r": (?!<)" + SIGNED):
            P("C3", f"no `{label}: ... <name> <YYYY-MM-DD>` line (Art Director)")
    if not has(r"^\W*Paper walk: (https?://\S+|#\d+)"):
        P("C4", "no `Paper walk: <link or #n>` line")
    for t in owl_tests(data):
        mine = [l for l in lines if t in l]
        ok = any(re.search(r"\bPASS\b", l) for l in mine) or \
            any("Not run" in l and re.search(r"#\d+", l) for l in mine)
        if not ok:
            P("C5", f"{t}: no PASS line and no `Not run` line with the building card's number (#n)")
    if data is None:
        try:
            with open(DEFAULT_DATA, encoding="utf-8") as fh:
                data = json.load(fh)
        except (OSError, ValueError):
            data = {}
    problems += spec_mod.card_problems(text, data, ROOT)
    return problems


def _split(arg):
    pid, _, phase = (arg or "").partition("/")
    return pid, phase


def _spec_modes(args, data):
    """The preset modes of main(); None when none was asked for."""
    if args.presets:
        lines = spec_mod.list_lines(data, args.gdd, args.context)
        for line in lines:
            print(line)
        print(f"encounter_presets: {len(lines)} preset(s)")
        return 0 if lines else 1
    if args.spec_hash:
        pid, phase = _split(args.spec_hash)
        h = spec_mod.spec_hash(data, pid, phase)
        if h is None:
            print(f"FAIL S3 {args.spec_hash}: no such preset phase")
            return 1
        print(f"encounter_spec preset={pid} phase={phase} spec={h}")
        return 0
    if args.critic_packet:
        pid, phase = _split(args.critic_packet)
        text = spec_mod.critic_packet(data, pid, phase, args.log, args.video)
        if text is None:
            print(f"FAIL S3 {args.critic_packet}: no such preset phase")
            return 1
        print(text, end="")
        return 0
    if args.ready:
        pid = args.preset or (spec_mod.block(data) or {}).get("default")
        probs = spec_mod.ready_problems(data, pid, ROOT)
        for rule, where, msg in probs:
            print(f"FAIL {rule} {where}: {msg}")
        print(f"encounter_ready: {len(probs)} problem(s) preset={pid}")
        return 1 if probs else 0
    if args.playthrough:
        pid = args.preset or (spec_mod.block(data) or {}).get("default")
        with open(args.playthrough, encoding="utf-8", errors="replace") as fh:
            probs, summary = spec_mod.check_playthrough(data, pid, fh.read().splitlines())
        for rule, where, msg in probs:
            print(f"FAIL {rule} {where}: {msg}")
        print(f"playthrough_check: {len(probs)} problem(s) {summary or 'preset=' + str(pid)}")
        return 1 if probs else 0
    return None


def _report(problems, label):
    for rule, where, msg in problems:
        print(f"FAIL {rule} {where}: {msg}")
    print(f"{label}: {len(problems)} problem(s)")
    return 1 if problems else 0


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--data", default=DEFAULT_DATA)
    ap.add_argument("--md", default=DEFAULT_MD)
    ap.add_argument("--tuning", default=None, help="tuning file (default: arena.tuning_source)")
    ap.add_argument("--write-md", action="store_true")
    ap.add_argument("--playtest", nargs="+", metavar="CSV", help="check playtest logs instead of the encounter")
    ap.add_argument("--wiring", nargs="?", const=ROOT, metavar="ROOT", help="check the engine cards and docs are filed")
    ap.add_argument("--card", nargs="+", metavar="FILE", help="check encounter card text for its required lines")
    ap.add_argument("--envelope", metavar="LINE", help="compare card 0.13's FEEL_ENVELOPE line with the tuning file")
    ap.add_argument("--manifest", default=None, help="feature manifest (default: docs/feature-manifest.json)")
    ap.add_argument("--presets", action="store_true", help="list the encounter presets a context may load")
    ap.add_argument("--gdd", default=None, help="with --presets: only presets built on this GDD revision")
    ap.add_argument("--context", default=None, choices=spec_mod.CONTEXTS, help="with --presets: only presets this "
                                                                                 "context may load")
    ap.add_argument("--preset", default=None, help="the preset --ready and --playthrough check")
    ap.add_argument("--ready", action="store_true", help="S12: the preset's hitbox, art and sound rows exist")
    ap.add_argument("--spec-hash", metavar="ID/PHASE", help="print one phase's spec hash")
    ap.add_argument("--critic-packet", metavar="ID/PHASE", help="print the blind critic's input for one phase")
    ap.add_argument("--log", default=None, help="with --critic-packet: the run log the critic reads")
    ap.add_argument("--video", default=None, help="with --critic-packet: the capture the critic watches")
    ap.add_argument("--playthrough", metavar="LOG", help="P1-P8 on the game's ENCOUNTER_EVT run log (--preset)")
    args = ap.parse_args(argv)
    if args.wiring:
        return _report(check_wiring(args.wiring), "wiring_check")
    if args.card:
        probs = []
        for path in args.card:
            with open(path, encoding="utf-8") as fh:
                probs += [(r, os.path.basename(path), m) for r, _, m in check_card_text(fh.read())]
        return _report(probs, "card_check")
    with open(args.data, encoding="utf-8") as fh:
        data = json.load(fh)
    spec_args = _spec_modes(args, data)
    if spec_args is not None:
        return spec_args
    if args.envelope is not None:
        tuning, err = load_tuning(data, args.tuning)
        if err:
            return _report([("V1", "tuning", err)], "envelope_check")
        return _report(check_envelope(args.envelope, tuning), "envelope_check")
    if args.playtest:
        problems, report = check_playtest(data, args.playtest)
        for line in report:
            print(line)
        for rule, where, msg in problems:
            print(f"FAIL {rule} {where}: {msg}")
        print(f"playtest_check: {len(problems)} problem(s)")
        return 1 if problems else 0
    state = data.get("model") == "state"
    tuning, err = (None, None) if state else load_tuning(data, args.tuning)
    if args.write_md:
        if err:
            raise SystemExit(f"FAIL E22: {err}")
        if not state:
            merged, err = with_tuning(data, tuning)
            if err:
                raise SystemExit(f"FAIL E22: {err}")
            write_md(merged, args.md)
        if spec_mod.block(data) is not None:
            spec_mod.write_md(data, args.md, load_manifest(args.manifest))
    md_text = ""
    if os.path.exists(args.md):
        with open(args.md, encoding="utf-8") as fh:
            md_text = fh.read()
    manifest = load_manifest(args.manifest)
    problems, numbers = check(data, md_text, tuning, manifest=manifest if manifest is not None else {})
    # E30: once baked, the shipped numbers are the ones this sim checked (tools/tuning.py; dry run B H4)
    problems += [("E30", tuning_mod.STAMP, x) for x in tuning_mod.baked_vs_sim_problems(ROOT, feel=tuning, enc=data,
                                                                                         manifest=manifest or None)]
    # S1-S11, S13: the encounter presets (tools/encounter_spec.py). An editor dump (--data) has no presets block.
    if spec_mod.block(data) is not None or os.path.abspath(args.data) == os.path.abspath(DEFAULT_DATA):
        sp, snums = spec_mod.check(data, md_text, manifest if manifest is not None else {}, ROOT, MIN_TELEGRAPH_SEC)
        problems += sp
        numbers = list(numbers) + snums
    for n in numbers:
        print(n)
    for rule, where, msg in problems:
        print(f"FAIL {rule} {where}: {msg}")
    print(f"encounter_check: {len(problems)} problem(s)")
    return 1 if problems else 0


if __name__ == "__main__":
    sys.exit(main())
