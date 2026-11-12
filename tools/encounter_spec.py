#!/usr/bin/env python3
"""Encounter presets: the boss fight as a whole, as data (owner: Encounter Designer). Stdlib only.

pipeline/level/encounter.json `encounter_presets` holds one or more presets. Each one is the full fight: phases,
targets with HP, attacks (telegraph, effect, counterplay), phase transitions, pacing over the run and story beats.
Gameplay code reads the selected preset; nothing about the fight is hardcoded. The default preset is the GDD 1.3
baseline. GDD 1.3: it takes its numbers from the top-level patterns, phases and duration_sec (uses_top_level; E29
holds those to the manifest approved_parameters) and copies none. GDD SH1.0: the baseline holds its own numbers and
lists each GDD one in numbers_from_gdd (E29 holds those to the manifest). Every other preset is `proposed`: workbench, practice and the GDD picker
only, never shipped, until its decision row is DECIDED by its owner.
tools/encounter_check.py runs these rules on every check; this module has no command line of its own.

Rules (id: what fails; each FAIL line says what to change):
  S1 presets     no presets block, no default, a default that is not the one `baseline` preset, a status other than
                 baseline/proposed, a proposed preset with `ship` in selectable_in, an unknown selectable_in value,
                 no gdd_revision, or a proposed preset without a decision row in docs/decisions.md or an owner.
  S2 baseline    the baseline copies a number the top level owns (telegraph, first_at, cadence, timer seconds),
                 names a pattern the top level does not have, leaves a scheduled pattern out, or has other phase ids.
  S3 refs        a phase names an unknown target or attack; an attack's phases and the phase lists disagree;
                 cancelled_by, active_while or a sequence names an unknown target; a numbers_from_reference path
                 does not resolve; the reference file is missing.
  S4 reachable   no entry.full_run, a phase not reachable from it, an unknown next, a cycle, not exactly one
                 ends_fight phase, an ends_fight phase with a next, or another entry naming an unknown phase.
  S5 finishable  a phase without ends_when; a target it needs is not in the phase, has no HP, is optional, is not
                 vulnerable in that phase or has hit_share <= 0; HP targets with player shot_damage <= 0; a target
                 with a floor before the final phase that is not ended in the final phase.
  S6 telegraph   an attack telegraph shorter than the floor (the larger of encounter_check MIN_TELEGRAPH_SEC and the
                 manifest OWL-01.telegraph_delay min, the GDD minimum reaction time), with no visual (pose or VFX:
                 sound alone fails, GDD section 7) or with no `shows` text. A shot the GDD gives no timed prefire
                 (GDD SH1.0 OWL-12: red and yellow volleys) sets `no_prefire: <Rule ID>` and sec 0; it still needs
                 its visual and `shows`.
  S7 counterplay an attack with no counterplay, an unknown verb, a verb the preset's player cannot do
                 (player.verbs), or a verb listed both as counterplay and as not_counterplay.
  S8 pacing      fight_length_sec outside the manifest END-01.survival_s range; the estimated fight length
                 (HP / (shot damage / shot cadence x hit_share) per target, plus stuns and transitions; clock floor
                 gives the short and the long case) outside fight_length_sec.
  S9 cancel      an attack scheduled in a phase after its cancelled_by target broke; a break that cancels an attack
                 that does not name it; a break without new_attacks false or without in_flight.
  S10 transition a phase without transition_in, with new_attacks not false or a negative length; an attack whose
                 first_at falls inside the transition (it would fire while the phase changes); a cadence not longer
                 than the telegraph.
  S11 names      a target without a hitbox id; an attack without art or sound ids.
  S12 ready      (--ready only, and on every encounter card) a hitbox id not in pipeline/feel/hitboxes.json
                 entities, an art id not in pipeline/art/references.json elements, a sound id not in
                 pipeline/audio/sound-list.csv.
  S13 doc        the generated presets block in pipeline/level/encounter.md differs from this data.

Playthrough log (--playthrough LOG; the game's ENCOUNTER_EVT lines, card 0.31):
  ENCOUNTER_EVT t=<s> preset=<id> kind=<kind> phase=<id> [attack=<id>] [target=<id>]
  kinds: phase_start phase_end transition_start transition_end telegraph fire hit break end
  P1 line       a field is missing, t is not a number, an unknown kind, another preset.
  P2 order      phases do not start in the preset's order from the entry (entry=<id> on the first phase_start).
  P3 telegraph  a fire with no telegraph of that attack before it, or a lead shorter than the spec telegraph.
  P4 transition a telegraph or fire inside a transition or inside a break's stun.
  P5 schedule   an attack in a phase that does not list it, or after its cancelled_by target broke.
  P6 targets    breaks out of the phase's sequence; a phase that ends with a required target unbroken.
  P7 end        no end event (the run did not finish), or a full run's length outside fight_length_sec.
  P8 empty      no ENCOUNTER_EVT line.

Critic loop (card rules, encounter_check.py --card and tools/check_pr.py rule encounter):
  A card or PR that builds or tunes part of a fight carries `Encounter phases: <preset>/<phase>, ...`
  (or `Encounter phases: none (<why>)` when it changes encounter.json without changing a fight).
  C6 critic      for each listed phase the newest `ENCOUNTER CRITIC:` line is PASS, its spec= is the phase's current
                 spec hash (--spec-hash), and builder= and critic= are different sessions. Every verdict line records
                 its round's scores: playthrough=<problems> check=<problems> (the playthrough_check and
                 encounter_check counts of that round), and rounds go up line by line. There is no round cap: the
                 loop runs until the critic passes.
  C7 stuck       the newest STUCK_ROUNDS verdicts are FAIL rounds in a row with no improvement: the same biggest gap
                 and no better playthrough or check score than the round before. Only then the card waits for a
                 human (needs-human, `NEEDS HUMAN: <owner>`). A new gap or a better score keeps the loop going.
  C8 run log     no `playthrough_check: 0 problem(s) preset=<preset> phases=...` line covering each listed phase.
  C9 ready       no `encounter_ready: 0 problem(s) preset=<preset>` line (the S12 rows exist).
"""
import csv
import hashlib
import json
import os
import re

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
STATUSES = {"baseline", "proposed"}
CONTEXTS = ("ship", "workbench", "practice", "gdd_picker")
STUCK_ROUNDS = 3             # no round cap: escalate only after 3 FAIL rounds in a row with no improvement
VERBS = {   # counterplay verb -> the player verb it needs
    "move_off_line": "move", "leave_band": "move", "clear_curve": "move", "stay_clear_after_pause": "move",
    "leave_first_pattern": "move", "dont_drift_back": "move", "dodge": "move", "bait_then_leave": "move",
    "change_altitude": "rise", "shield": "shield", "absorb": "absorb", "catch": "catch", "dash": "dash",
    "shoot_target": "shoot",
}
PLAYER_VERBS = {"move", "rise", "fall", "shoot", "shield", "absorb", "catch", "dash"}
BASELINE_OWNED = ("telegraph", "first_at", "cadence_sec", "cadence_by_phase")
NO_PREFIRE_RULE = re.compile(r"(?:OWL|COM)-\d{2}")
EVT_KINDS = {"phase_start", "phase_end", "transition_start", "transition_end", "telegraph", "fire", "hit", "break",
             "end"}
PBEGIN = "<!-- BEGIN GENERATED PRESETS by encounter_check.py --write-md; do not edit by hand -->"
PEND = "<!-- END GENERATED PRESETS -->"
CRITIC = re.compile(r"^\W*ENCOUNTER CRITIC:\s*(?P<verdict>PASS|FAIL)\b(?P<rest>.*)$", re.M)
PHASES_LINE = re.compile(r"^\W*Encounter phases:\s*(?P<v>.+)$", re.M)
RUN_LINE = re.compile(r"playthrough_check: 0 problem\(s\) preset=(?P<preset>\S+) phases=(?P<phases>\S+)")
READY_LINE = re.compile(r"encounter_ready: 0 problem\(s\) preset=(?P<preset>\S+)")


def num(v):
    return isinstance(v, (int, float)) and not isinstance(v, bool)


def block(data):
    b = (data or {}).get("encounter_presets")
    return b if isinstance(b, dict) else None


def presets(data):
    b = block(data) or {}
    p = b.get("presets")
    return p if isinstance(p, dict) else {}


def _manifest_rec(manifest, key):
    rec = (((manifest or {}).get("approved_parameters") or {}).get("values") or {}).get(key)
    return rec if isinstance(rec, dict) else {}


def telegraph_floor(manifest, pipeline_min):
    gdd_min = _manifest_rec(manifest, "OWL-01.telegraph_delay").get("min")
    return max(pipeline_min, gdd_min) if num(gdd_min) else pipeline_min


def _decision_rows(root):
    try:
        with open(os.path.join(root, "docs", "decisions.md"), encoding="utf-8") as fh:
            text = fh.read()
    except OSError:
        return {}
    rows = {}
    for line in text.splitlines():
        cells = [c.strip() for c in line.strip().strip("|").split("|")]
        if line.startswith("|") and cells and re.fullmatch(r"D[\w-]+|DEC-\d+", cells[0]):
            rows[cells[0]] = cells
    return rows


# ---------- the view of a preset: the baseline is built from the top level ----------

def view(data, pid):
    """A preset with every number resolved. The baseline gets telegraph, schedule and timer from the top level."""
    p = json.loads(json.dumps(presets(data).get(pid) or {}))
    if not p.get("uses_top_level"):
        return p
    pats = data.get("patterns") or {}
    sched = [e for ph in data.get("phases") or [] for e in ph.get("schedule") or [] if isinstance(e, dict)]
    for a in p.get("attacks") or []:
        pat = pats.get(a.get("pattern")) or {}
        tell = pat.get("tell") or {}
        a["telegraph"] = {"sec": pat.get("telegraph_sec"), "pose": tell.get("pose"), "vfx": tell.get("vfx"),
                          "sound": tell.get("sound"), "shows": "the owl's windup and the amber clock flash"}
        ats = sorted(e["at"] for e in sched if e.get("pattern") == a.get("pattern") and num(e.get("at")))
        a["first_at"] = ats[0] if ats else None
        gaps = sorted({round(y - x, 6) for x, y in zip(ats, ats[1:])})
        a["cadence_sec"] = gaps[0] if gaps else None
        a.setdefault("phases", [ph.get("id") for ph in p.get("phases") or [] if a.get("id") in (ph.get("attacks") or [])])
    for ph in p.get("phases") or []:
        tr = ph.get("transition_in") or {}
        if tr.get("sec") == "first_schedule_at":
            firsts = [a.get("first_at") for a in p.get("attacks") or [] if num(a.get("first_at"))]
            tr["sec"] = min(firsts) if firsts else 0
        if (ph.get("ends_when") or {}).get("timer") == "duration_sec":
            ph["ends_when"] = {"timer": data.get("duration_sec")}
    p["fight_length_sec"] = {"min": data.get("duration_sec"), "max": data.get("duration_sec")}
    return p


def _by_id(items):
    return {x.get("id"): x for x in items or [] if isinstance(x, dict)}


def shot_dps(p, manifest):
    pl = p.get("player") or {}
    dmg, cad = pl.get("shot_damage"), pl.get("shot_cadence")
    if isinstance(cad, str):
        cad = _manifest_rec(manifest, cad).get("start")
    return (dmg / cad) if num(dmg) and num(cad) and cad > 0 else None


def estimate_length(p, manifest):
    """(short, long) seconds of a full run, or None when the preset ends on a timer only."""
    phases, targets = p.get("phases") or [], _by_id(p.get("targets"))
    dps = shot_dps(p, manifest)
    lo = hi = 0.0
    for ph in phases:
        tr = (ph.get("transition_in") or {}).get("sec")
        if num(tr):
            lo, hi = lo + tr, hi + tr
        ew = ph.get("ends_when") or {}
        if num(ew.get("timer")):
            lo, hi = lo + ew["timer"] - (tr if num(tr) else 0), hi + ew["timer"] - (tr if num(tr) else 0)
            continue
        need = list(ew.get("broken") or []) + ([ew["hp_zero"]] if ew.get("hp_zero") else [])
        for tid in need:
            t = targets.get(tid) or {}
            if not (dps and num(t.get("hp")) and num(t.get("hit_share")) and t["hit_share"] > 0):
                return None
            rate = dps * t["hit_share"]
            full = t["hp"] / rate
            floor = t.get("floor_pct_before_final")
            short = (t["hp"] * floor / 100.0) / rate if ph.get("ends_fight") and num(floor) else full
            lo, hi = lo + short, hi + full
            stun = (t.get("on_break") or {}).get("stun_sec")
            if num(stun) and ph.get("next"):
                lo, hi = lo + stun, hi + stun
    return lo, hi


def spec_hash(data, pid, phase_id):
    """12 hex of the phase's spec: the phase, the attacks and targets it uses, the player and the pacing window."""
    p = view(data, pid)
    ph = _by_id(p.get("phases")).get(phase_id)
    if ph is None:
        return None
    atk, tgt = _by_id(p.get("attacks")), _by_id(p.get("targets"))
    sub = {"preset": pid, "status": p.get("status"), "phase": ph, "player": p.get("player"),
           "fight_length_sec": p.get("fight_length_sec"),
           "attacks": [atk.get(a) for a in ph.get("attacks") or []],
           "targets": [tgt.get(t) for t in ph.get("targets") or []]}
    raw = json.dumps(sub, sort_keys=True, separators=(",", ":")).encode()
    return hashlib.sha256(raw).hexdigest()[:12]


# ---------- S1-S11, S13 ----------

def _resolve(p, path):
    cur = p
    for part in path.split("."):
        if isinstance(cur, dict) and part in cur:
            cur = cur[part]
        elif isinstance(cur, list):
            cur = _by_id(cur).get(part)
            if cur is None:
                return False
        else:
            return False
    return True


def check(data, md_text=None, manifest=None, root=ROOT, pipeline_min_telegraph=0.4):
    """(problems [(rule, where, msg)], numbers [str])."""
    probs, nums = [], []
    P = lambda rule, where, msg: probs.append((rule, where, msg))
    b = block(data)
    if b is None:
        P("S1", "encounter_presets", "missing: add the encounter_presets block with the GDD baseline preset as "
          "default (pipeline/roles/encounter-designer.md)")
        return probs, nums
    ps = presets(data)
    base = [k for k, v in ps.items() if isinstance(v, dict) and v.get("status") == "baseline"]
    if b.get("default") not in ps:
        P("S1", "encounter_presets.default", f"{b.get('default')!r} is not a preset: set it to the baseline preset id")
    elif (ps[b["default"]] or {}).get("status") != "baseline":
        P("S1", "encounter_presets.default", f"{b['default']} is {ps[b['default']].get('status')}: only the baseline "
          "preset ships; a proposed preset becomes the default only after its decision row is DECIDED and the GDD "
          "and manifest change")
    if len(base) != 1:
        P("S1", "encounter_presets", f"{len(base)} baseline presets: exactly one (the GDD baseline)")
    rows = _decision_rows(root)
    floor = telegraph_floor(manifest, pipeline_min_telegraph)
    surv = _manifest_rec(manifest, "END-01.survival_s")
    for pid, raw in ps.items():
        where = f"presets.{pid}"
        if not isinstance(raw, dict):
            P("S1", where, "not an object")
            continue
        st = raw.get("status")
        if st not in STATUSES:
            P("S1", where, f"status {st!r}: use baseline or proposed")
        if not raw.get("gdd_revision"):
            P("S1", where, "no gdd_revision: name the GDD revision the preset is built on")
        sel = raw.get("selectable_in") or []
        for s in sel:
            if s not in CONTEXTS:
                P("S1", where, f"selectable_in {s!r}: use {', '.join(CONTEXTS)}")
        if st == "proposed":
            if "ship" in sel:
                P("S1", where, "a proposed preset never ships: drop `ship` from selectable_in")
            did = raw.get("decision")
            if not did or did not in rows:
                P("S1", where, f"decision {did!r} has no row in docs/decisions.md: add a row (owner "
                  f"{raw.get('owner') or '<design owner>'}) that asks whether this fight replaces the baseline")
            if not raw.get("owner"):
                P("S1", where, "no owner: name the human who decides (the game design owner)")
            ref = raw.get("reference")
            if ref and not os.path.exists(os.path.join(root, ref)):
                P("S3", where, f"reference {ref} does not exist: add the source description there")
            for path in raw.get("numbers_from_reference") or []:
                if not _resolve(raw, path):
                    P("S3", where, f"numbers_from_reference {path!r} names no field: fix the path")
        if raw.get("uses_top_level"):
            _check_baseline(data, pid, raw, P)
        p = view(data, pid)
        _check_preset(pid, p, P, floor)
        fl = p.get("fight_length_sec") or {}
        if not (num(fl.get("min")) and num(fl.get("max")) and fl["min"] <= fl["max"]):
            P("S8", where, "fight_length_sec needs min <= max in seconds (the target fight length)")
        else:
            if num(surv.get("min")) and num(surv.get("max")) and not (surv["min"] <= fl["min"] and fl["max"] <= surv["max"]):
                P("S8", where, f"fight_length_sec {fl['min']}-{fl['max']} s is outside END-01.survival_s "
                  f"{surv['min']}-{surv['max']} s (GDD 1.3 section 5A): keep the fight inside the approved range")
            est = estimate_length(p, manifest)
            if est is None and not raw.get("uses_top_level"):
                P("S8", where, "cannot estimate the fight length: every target a phase needs needs hp and hit_share, "
                  "and player needs shot_damage and shot_cadence")
            elif est is not None:
                lo, hi = est
                nums.append(f"preset {pid}: estimated length {lo:.0f}-{hi:.0f} s (target {fl['min']}-{fl['max']} s)")
                if lo < fl["min"] - 1e-6 or hi > fl["max"] + 1e-6:
                    P("S8", where, f"estimated length {lo:.0f}-{hi:.0f} s is outside the target {fl['min']}-{fl['max']} s: "
                      "change target HP, hit_share or shot damage, or the target window")
        feats = raw.get("needs_features") or []
        if feats:
            st_by = {f.get("feature_id"): f.get("status") for f in (manifest or {}).get("features", [])}
            nums.append(f"preset {pid}: needs " + ", ".join(f"{f} {st_by.get(f, 'unknown')}" for f in feats))
    if md_text is not None:
        want = render(data, manifest)
        m = re.search(re.escape(PBEGIN) + r"\n(.*?)" + re.escape(PEND), md_text, re.S)
        if not m:
            P("S13", "encounter.md", "no generated presets block: add the markers and run "
              "`python3 tools/encounter_check.py --write-md`")
        elif m.group(1) != want:
            P("S13", "encounter.md", "the presets block differs from encounter.json: run "
              "`python3 tools/encounter_check.py --write-md`")
    return probs, nums


def _check_baseline(data, pid, raw, P):
    where = f"presets.{pid}"
    pats = data.get("patterns") or {}
    used = {e.get("pattern") for ph in data.get("phases") or [] for e in ph.get("schedule") or [] if isinstance(e, dict)}
    named = set()
    for a in raw.get("attacks") or []:
        for k in BASELINE_OWNED:
            if k in a:
                P("S2", f"{where}.attacks.{a.get('id')}", f"copies {k}: the baseline reads it from the top-level pattern "
                  "and schedule (approved_parameters, E29); delete it here")
        if a.get("pattern") not in pats:
            P("S2", f"{where}.attacks.{a.get('id')}", f"pattern {a.get('pattern')!r} is not a top-level pattern")
        named.add(a.get("pattern"))
    for missing in sorted(used - named):
        P("S2", where, f"scheduled pattern {missing} has no attack row: add one with its counterplay, art and sound")
    top = [ph.get("id") for ph in data.get("phases") or []]
    mine = [ph.get("id") for ph in raw.get("phases") or []]
    if top != mine:
        P("S2", where, f"phases {mine} differ from the top-level phases {top}: the baseline mirrors them")
    for ph in raw.get("phases") or []:
        t = (ph.get("ends_when") or {}).get("timer")
        if t is not None and t != "duration_sec":
            P("S2", f"{where}.phases.{ph.get('id')}", "ends_when.timer copies a number: write \"duration_sec\"")


def _check_preset(pid, p, P, floor):
    where = f"presets.{pid}"
    phases, atk, tgt = p.get("phases") or [], _by_id(p.get("attacks")), _by_id(p.get("targets"))
    ph_by = _by_id(phases)
    verbs = set((p.get("player") or {}).get("verbs") or [])
    for v in sorted(verbs - PLAYER_VERBS):
        P("S7", f"{where}.player", f"unknown player verb {v!r}: use {', '.join(sorted(PLAYER_VERBS))}")
    # S4 reachable
    entry = (p.get("entry") or {})
    start = entry.get("full_run")
    if start not in ph_by:
        P("S4", f"{where}.entry", f"full_run {start!r} is not a phase: name the phase a full run starts in")
    for k, v in entry.items():
        if k != "full_run" and v not in ph_by:
            P("S4", f"{where}.entry", f"{k} {v!r} is not a phase")
    seen, cur, order = set(), start, []
    while cur in ph_by and cur not in seen:
        seen.add(cur)
        order.append(cur)
        nxt = ph_by[cur].get("next")
        if nxt is not None and nxt not in ph_by:
            P("S4", f"{where}.phases.{cur}", f"next {nxt!r} is not a phase")
        cur = nxt
    if cur in seen:
        P("S4", f"{where}.phases.{cur}", "the phase order loops back: the fight could never end; fix `next`")
    for ph in phases:
        if ph.get("id") not in seen and start in ph_by:
            P("S4", f"{where}.phases.{ph.get('id')}", "not reachable from entry.full_run: link it with `next` or delete it")
    enders = [ph.get("id") for ph in phases if ph.get("ends_fight")]
    if len(enders) != 1:
        P("S4", where, f"{len(enders)} ends_fight phases: exactly one phase ends the fight")
    for ph in phases:
        if ph.get("ends_fight") and ph.get("next") is not None:
            P("S4", f"{where}.phases.{ph.get('id')}", "ends the fight but has a next phase: set next to null")
    if order and enders and order[-1] != enders[0]:
        P("S4", where, f"the full run ends in {order[-1]}, not in the ends_fight phase {enders[0]}")
    # S3, S5, S9, S10, S11
    broken_before = set()
    pl = p.get("player") or {}
    for ph in [ph_by[x] for x in order] + [ph for ph in phases if ph.get("id") not in seen]:
        pw = f"{where}.phases.{ph.get('id')}"
        for t in ph.get("targets") or []:
            if t not in tgt:
                P("S3", pw, f"target {t!r} is not in targets")
        for a in ph.get("attacks") or []:
            if a not in atk:
                P("S3", pw, f"attack {a!r} is not in attacks")
                continue
            if ph.get("id") not in (atk[a].get("phases") or []):
                P("S3", pw, f"attack {a} does not list this phase in its phases")
            cb = atk[a].get("cancelled_by")
            if cb in broken_before:
                P("S9", pw, f"attack {a} is scheduled after {cb} broke, and breaking {cb} cancels it: take it out of "
                  "this phase")
        seq = ph.get("sequence")
        if seq is not None and [t for t in ph.get("targets") or [] if t in seq] != list(seq):
            P("S3", pw, "sequence must list the phase's targets in the same order")
        for t in seq or []:
            if t not in tgt:
                P("S3", pw, f"sequence names unknown target {t!r}")
        ew = ph.get("ends_when")
        if not isinstance(ew, dict) or not (ew.get("broken") or ew.get("hp_zero") or num(ew.get("timer"))):
            P("S5", pw, "no ends_when: use {\"broken\": [targets]}, {\"hp_zero\": target} or {\"timer\": seconds}")
            ew = {}
        need = list(ew.get("broken") or []) + ([ew["hp_zero"]] if ew.get("hp_zero") else [])
        for tid in need:
            t = tgt.get(tid)
            if t is None or tid not in (ph.get("targets") or []):
                P("S5", pw, f"ends when {tid} breaks, but {tid} is not a target of this phase")
                continue
            if not num(t.get("hp")) or t["hp"] <= 0:
                P("S5", pw, f"{tid} has no HP > 0: the phase cannot be finished")
            if t.get("optional"):
                P("S5", pw, f"{tid} is optional and cannot be what ends the phase")
            if ph.get("id") not in (t.get("vulnerable_in") or []):
                P("S5", pw, f"{tid} is not vulnerable in this phase: add the phase to its vulnerable_in")
            if not num(t.get("hit_share")) or t["hit_share"] <= 0:
                P("S5", pw, f"{tid} needs hit_share > 0 (the share of shots that land while it is open)")
            if not num(pl.get("shot_damage")) or pl["shot_damage"] <= 0:
                P("S5", pw, "HP targets need player.shot_damage > 0")
        tr = ph.get("transition_in")
        if not isinstance(tr, dict):
            P("S10", pw, "no transition_in: give its length (sec), new_attacks false and in_flight")
            tr = {}
        else:
            if tr.get("new_attacks") is not False:
                P("S10", pw, "transition_in.new_attacks must be false: no attack starts while the phase changes")
            if not num(tr.get("sec")) or tr["sec"] < 0:
                P("S10", pw, "transition_in.sec must be a number of seconds >= 0")
            if tr.get("in_flight") not in ("none", "dangerous", "cleared"):
                P("S10", pw, "transition_in.in_flight: none, dangerous or cleared (what shots already flying do)")
        for a in ph.get("attacks") or []:
            fa = (atk.get(a) or {}).get("first_at")
            if num(tr.get("sec")) and num(fa) and fa < tr["sec"]:
                P("S10", pw, f"{a} first_at {fa} s is inside the {tr['sec']} s transition: start it at {tr['sec']} s or later")
        for tid in ew.get("broken") or []:
            broken_before.add(tid)
        if ew.get("hp_zero"):
            broken_before.add(ew["hp_zero"])
    for tid, t in tgt.items():
        tw = f"{where}.targets.{tid}"
        if not t.get("hitbox"):
            P("S11", tw, "no hitbox id: name its collider in pipeline/feel/hitboxes.json (Gameplay Dev)")
        for ph in t.get("vulnerable_in") or []:
            if ph not in ph_by:
                P("S3", tw, f"vulnerable_in names unknown phase {ph!r}")
        fl = t.get("floor_pct_before_final")
        if fl is not None:
            final = [ph.get("id") for ph in phases if (ph.get("ends_when") or {}).get("hp_zero") == tid and ph.get("ends_fight")]
            if not (num(fl) and 0 < fl < 100) or not final:
                P("S5", tw, "floor_pct_before_final needs 0-100 and the final phase ending on hp_zero of this target")
        ob = t.get("on_break")
        if ob is not None:
            for a in ob.get("cancels") or []:
                if a not in atk or atk[a].get("cancelled_by") != tid:
                    P("S9", tw, f"on_break cancels {a}, but {a} does not name cancelled_by {tid}")
            if ob.get("new_attacks") is not False:
                P("S9", tw, "on_break.new_attacks must be false: no new attack starts during the break or stun")
            if ob.get("in_flight") not in ("dangerous", "cleared"):
                P("S9", tw, "on_break.in_flight: dangerous or cleared (what shots already flying do)")
    for aid, a in atk.items():
        aw = f"{where}.attacks.{aid}"
        for ph in a.get("phases") or []:
            if ph not in ph_by or aid not in (ph_by[ph].get("attacks") or []):
                P("S3", aw, f"phases lists {ph!r}, but that phase does not list {aid}")
        for k in ("cancelled_by", "active_while"):
            if a.get(k) is not None and a[k] not in tgt:
                P("S3", aw, f"{k} {a[k]!r} is not a target")
        te = a.get("telegraph") or {}
        sec = te.get("sec")
        if te.get("no_prefire") is not None:
            # GDD SH1.0 OWL-12: "Red cue / response: no separate timed prefire delay." A shot with no prefire still
            # shows its launch posture and lane (pose or vfx, and shows) and names the Rule ID that removes the delay.
            if not (isinstance(te["no_prefire"], str) and NO_PREFIRE_RULE.fullmatch(te["no_prefire"])) or sec != 0:
                P("S6", aw, "no_prefire needs telegraph sec 0 and the Rule ID that removes the timed prefire (OWL-12)")
        elif not num(sec) or sec < floor - 1e-9:
            P("S6", aw, f"telegraph {sec} s is under the {floor:g} s floor (GDD minimum reaction time): lengthen it")
        if not (te.get("pose") or te.get("vfx")):
            P("S6", aw, "telegraph has no visual (pose or vfx); sound alone fails (GDD section 7)")
        if not te.get("shows"):
            P("S6", aw, "telegraph.shows is empty: say what the player sees before it hits")
        cad = [a["cadence_sec"]] if num(a.get("cadence_sec")) else list((a.get("cadence_by_phase") or {}).values())
        for c in cad:
            if num(c) and num(sec) and c <= sec:
                P("S10", aw, f"cadence {c} s is not longer than its {sec} s telegraph: casts would overlap their warning")
        cp = a.get("counterplay") or []
        if not cp:
            P("S7", aw, "no counterplay: say what the player does to avoid or answer it")
        mine = set()
        for c in cp:
            v = c.get("verb") if isinstance(c, dict) else None
            mine.add(v)
            if v not in VERBS:
                P("S7", aw, f"counterplay verb {v!r} is unknown: use {', '.join(sorted(VERBS))}")
            elif VERBS[v] not in verbs:
                P("S7", aw, f"counterplay {v} needs the player verb {VERBS[v]}, which this preset's player lacks")
        for c in a.get("not_counterplay") or []:
            if isinstance(c, dict) and c.get("verb") in mine:
                P("S7", aw, f"{c.get('verb')} is listed as counterplay and as not counterplay")
        if not a.get("art"):
            P("S11", aw, "no art ids: name its element rows in pipeline/art/references.json (Art Director)")
        if not a.get("sound"):
            P("S11", aw, "no sound ids: name its rows in pipeline/audio/sound-list.csv (Audio)")


# ---------- S12 readiness ----------

def ready_problems(data, pid, root=ROOT):
    probs = []
    p = view(data, pid)
    if not p:
        return [("S12", "encounter_presets", f"no preset {pid!r}")]
    try:
        with open(os.path.join(root, "pipeline", "feel", "hitboxes.json"), encoding="utf-8") as fh:
            boxes = {e.get("id") for e in json.load(fh).get("entities") or [] if isinstance(e, dict)}
    except (OSError, ValueError):
        boxes = set()
    refs_path = os.path.join(root, "pipeline", "art", "references.json")
    try:
        with open(refs_path, encoding="utf-8") as fh:
            elems = set((json.load(fh).get("elements") or {}).keys())
    except (OSError, ValueError, AttributeError):
        elems = None
    try:
        with open(os.path.join(root, "pipeline", "audio", "sound-list.csv"), encoding="utf-8", newline="") as fh:
            sounds = {r.get("id") for r in csv.DictReader(fh)}
    except OSError:
        sounds = set()
    where = f"presets.{pid}"
    for t in p.get("targets") or []:
        if t.get("hitbox") and t["hitbox"] not in boxes:
            probs.append(("S12", f"{where}.targets.{t.get('id')}", f"hitbox {t['hitbox']} is not an entity in "
                          "pipeline/feel/hitboxes.json: ask Gameplay Dev for its collider row (card 0.28)"))
    for a in p.get("attacks") or []:
        for e in a.get("art") or []:
            if elems is None:
                probs.append(("S12", f"{where}.attacks.{a.get('id')}", "pipeline/art/references.json is missing: the "
                              "art rows cannot be checked (Art Director)"))
                break
            if e not in elems:
                probs.append(("S12", f"{where}.attacks.{a.get('id')}", f"art {e} is not an element in "
                              "pipeline/art/references.json: ask the Art Director for the row and its references"))
        for s in a.get("sound") or []:
            if s not in sounds:
                probs.append(("S12", f"{where}.attacks.{a.get('id')}", f"sound {s} is not a row in "
                              "pipeline/audio/sound-list.csv: ask Audio for the row (telegraph, launch, hit)"))
    return probs


# ---------- selection (workbench, practice, GDD picker) ----------

def presets_for(data, gdd_revision=None, context=None):
    """[(id, preset)] a context may load. The GDD picker asks with the revision it picked and context gdd_picker."""
    out = []
    for pid, p in presets(data).items():
        if not isinstance(p, dict):
            continue
        if gdd_revision and str(p.get("gdd_revision")) != str(gdd_revision):
            continue
        if context and context not in (p.get("selectable_in") or []):
            continue
        out.append((pid, p))
    return out


def list_lines(data, gdd_revision=None, context=None):
    b = block(data) or {}
    lines = []
    for pid, p in presets_for(data, gdd_revision, context):
        phases = [ph.get("id") for ph in p.get("phases") or []]
        lines.append(f"preset={pid} status={p.get('status')} gdd={p.get('gdd_revision')} "
                     f"default={'yes' if b.get('default') == pid else 'no'} selectable={','.join(p.get('selectable_in') or [])} "
                     f"decision={p.get('decision') or '-'} owner={p.get('owner') or '-'} phases={','.join(phases)}")
    return lines


# ---------- encounter.md presets block ----------

def render(data, manifest=None):
    b = block(data) or {}
    lines = [f"Default preset: `{b.get('default')}`. Select another in a workbench or practice build with "
             f"`{(b.get('select') or {}).get('workbench_cvar', '-')}`; list them with "
             f"`{(b.get('select') or {}).get('list', '-')}`.", ""]
    for pid in presets(data):
        p = view(data, pid)
        lines += [f"### Preset {pid} ({p.get('status')})", "", p.get("title", ""), ""]
        if p.get("status") == "proposed":
            lines += [f"PROPOSED, not the GDD baseline. Decision `{p.get('decision')}`, owner {p.get('owner')}. "
                      f"Selectable in: {', '.join(p.get('selectable_in') or [])}. Needs features: "
                      f"{', '.join(p.get('needs_features') or []) or '-'}. Not in the manifest yet: "
                      f"{', '.join(p.get('unmapped_mechanics') or []) or '-'}.", ""]
            fromref = set(p.get("numbers_from_reference") or [])
            lines += [f"Numbers from the reference: {', '.join(sorted(fromref)) or '-'}; every other number is a "
                      "pipeline proposal.", ""]
        est = estimate_length(p, manifest)
        fl = p.get("fight_length_sec") or {}
        lines += [f"Entry: {', '.join(f'{k} -> {v}' for k, v in (p.get('entry') or {}).items())}. Target length "
                  f"{fl.get('min')}-{fl.get('max')} s" + (f"; estimated {est[0]:.0f}-{est[1]:.0f} s." if est else "."), ""]
        lines += ["| Phase | Targets | Attacks | Ends when | Transition in | Next |", "|---|---|---|---|---|---|"]
        for ph in p.get("phases") or []:
            tr = ph.get("transition_in") or {}
            ew = ph.get("ends_when") or {}
            ends = (f"broken: {', '.join(ew['broken'])}" if ew.get("broken") else
                    f"{ew['hp_zero']} at 0 HP" if ew.get("hp_zero") else f"timer {ew.get('timer')} s")
            lines.append(f"| {ph.get('id')} | {', '.join(ph.get('targets') or []) or '-'} | {', '.join(ph.get('attacks') or [])} | "
                         f"{ends} | {tr.get('sec')} s, no new attacks, in flight: {tr.get('in_flight')} | "
                         f"{ph.get('next') or 'end of fight'} |")
        lines += ["", "| Target | HP | Hitbox | Vulnerable in | Hit share | On break |", "|---|---|---|---|---|---|"]
        for t in p.get("targets") or []:
            ob = t.get("on_break") or {}
            brk = "; ".join(x for x in [
                f"cancels {', '.join(ob['cancels'])}" if ob.get("cancels") else "",
                f"stun {ob['stun_sec']} s" if ob.get("stun_sec") else "",
                f"exposes {ob['exposes']}" if ob.get("exposes") else "",
                "clears threats" if ob.get("clears_threats") else "",
                f"in flight: {ob['in_flight']}" if ob.get("in_flight") else ""] if x) or "-"
            hp = t.get("hp") if t.get("hp") is not None else "-"
            if t.get("floor_pct_before_final"):
                hp = f"{hp} (keeps {t['floor_pct_before_final']}% until the final phase)"
            lines.append(f"| {t.get('id')}{' (optional)' if t.get('optional') else ''} | {hp} | {t.get('hitbox')} | "
                         f"{', '.join(t.get('vulnerable_in') or [])} | {t.get('hit_share', '-')} | {brk} |")
        lines += ["", "| Attack | Phases | Telegraph s | Shows | Effect | Counterplay | Art | Sound |",
                  "|---|---|---|---|---|---|---|---|"]
        for a in p.get("attacks") or []:
            te = a.get("telegraph") or {}
            eff = a.get("effect") or {}
            eff_t = ", ".join(f"{k} {v}" for k, v in eff.items() if not isinstance(v, (list, dict))) or "-"
            cp = "; ".join(c.get("verb", "") for c in a.get("counterplay") or [])
            lines.append(f"| {a.get('id')} | {', '.join(a.get('phases') or [])} | {te.get('sec')} | {te.get('shows', '-')} | "
                         f"{eff_t} | {cp} | {', '.join(a.get('art') or [])} | {', '.join(a.get('sound') or [])} |")
        end = p.get("end") or {}
        lines += ["", f"End: {end.get('story_beat', '-')}.", ""]
    return "\n".join(lines).rstrip("\n") + "\n"


def write_md(data, md_path, manifest=None):
    with open(md_path, encoding="utf-8") as fh:
        text = fh.read()
    blk = PBEGIN + "\n" + render(data, manifest) + PEND
    pat = re.compile(re.escape(PBEGIN) + r".*?" + re.escape(PEND), re.S)
    text = pat.sub(lambda _: blk, text) if pat.search(text) else text.rstrip("\n") + "\n\n## Encounter presets\n\n" + blk + "\n"
    with open(md_path, "w", encoding="utf-8") as fh:
        fh.write(text)


# ---------- critic packet ----------

def critic_packet(data, pid, phase_id, log=None, video=None):
    p = view(data, pid)
    ph = _by_id(p.get("phases")).get(phase_id)
    if ph is None:
        return None
    h = spec_hash(data, pid, phase_id)
    atk, tgt = _by_id(p.get("attacks")), _by_id(p.get("targets"))
    out = [f"# Encounter critic packet: {pid} / {phase_id} (spec={h})", "",
           "You are the critic, in a fresh session. You did not build this. Read only this packet, the reference "
           "below, the run log and the capture. Do not open the PR body, the card's journal, the builder's notes or "
           "the diff: you judge what the build does, not what anyone says it does.", "",
           "## Judge against", f"- The spec below (pipeline/level/encounter.json, preset {pid}, phase {phase_id}).",
           f"- The reference: {p.get('reference') or 'GDD ' + str(p.get('gdd_revision'))}.",
           "- The team's goal: bring the pipeline build closer to the demonstrated fight.", "",
           "## Inputs", f"- Run log: {log or '<the playthrough log the build wrote>'} "
           f"(`python3 tools/encounter_check.py --playthrough <log>` must print 0 problem(s) first).",
           f"- Capture: {video or '<the full-run video of this phase>'}", "",
           "## Phase", f"- Targets: {', '.join(ph.get('targets') or []) or '-'}; ends when "
           f"{json.dumps(ph.get('ends_when'))}; next: {ph.get('next') or 'end of fight'}.",
           f"- Transition in: {json.dumps(ph.get('transition_in'))}."]
    for t in ph.get("targets") or []:
        out.append(f"- Target {t}: {json.dumps(tgt.get(t), sort_keys=True)}")
    for a in ph.get("attacks") or []:
        out.append(f"- Attack {a}: {json.dumps(atk.get(a), sort_keys=True)}")
    out += ["", "## Questions (answer each yes or no from the capture, then the verdict)",
            "1. Does every attack show its telegraph long enough to react, before it can hurt?",
            "2. Can a player tell from the screen what each counterplay is, and does it work?",
            "3. Do targets take damage and break as specified, and does each break do what its on_break says?",
            "4. Does the phase start and end as specified, with no attack starting during a transition or stun?",
            "5. Is this phase closer to the reference than a plain bolt-dodging round would be?", "",
            "## Verdict: one line, binary, the biggest gap only",
            f"ENCOUNTER CRITIC: PASS preset={pid} phase={phase_id} round=<n> spec={h} builder=<session> "
            "critic=<your session> capture=<path or #n> playthrough=<n> check=<n> gap=none",
            f"ENCOUNTER CRITIC: FAIL preset={pid} phase={phase_id} round=<n> spec={h} builder=<session> "
            "critic=<your session> capture=<path or #n> playthrough=<n> check=<n> "
            "gap=<the one biggest gap, as a fix the builder can make>",
            "", "Put the round's scores on the line before gap=: playthrough=<problems from playthrough_check> "
            "check=<problems from encounter_check>. Keep gap= last.",
            f"No round cap: the builder fixes the gap and the loop runs again until PASS. Only {STUCK_ROUNDS} FAIL "
            "rounds in a row with the same gap and no better score mean it is stuck: label the card needs-human and "
            f"post `NEEDS HUMAN: {p.get('owner') or 'game design owner'} <the gap> <link> <YYYY-MM-DDTHH:MMZ>`."]
    return "\n".join(out) + "\n"


# ---------- C6-C9 card and PR lines ----------

def card_phases(text):
    """[(preset, phase)] from `Encounter phases:` lines; [] for none; None when there is no such line."""
    found = None
    for m in PHASES_LINE.finditer(text or ""):
        v = m.group("v").strip()
        found = found or []
        if v.lower().startswith("none"):
            continue
        for item in re.split(r"[,\s]+", v):
            if "/" in item:
                a, _, b = item.strip("`").partition("/")
                found.append((a, b))
    return found


def _int(v):
    try:
        return int(v)
    except (TypeError, ValueError):
        return None


def _norm_gap(g):
    return re.sub(r"\s+", " ", (g or "").strip().lower().rstrip("."))


def stuck(verdicts):
    """True when the newest STUCK_ROUNDS verdicts are FAIL rounds in a row with no improvement: the same biggest gap
    and neither score (playthrough=, check= problem counts) better than the round before."""
    tail = verdicts[-STUCK_ROUNDS:]
    if len(tail) < STUCK_ROUNDS or any(v != "FAIL" for v, _ in tail):
        return False
    for (_, a), (_, b) in zip(tail, tail[1:]):
        if _norm_gap(a.get("gap")) != _norm_gap(b.get("gap")):
            return False
        if _int(b.get("playthrough")) < _int(a.get("playthrough")) or _int(b.get("check")) < _int(a.get("check")):
            return False
    return True


def card_problems(text, data, root=ROOT):
    """C6-C9 for a card or PR text that lists `Encounter phases:`. Returns (rule, where, msg)."""
    probs = []
    P = lambda rule, msg: probs.append((rule, "card", msg))
    phases = card_phases(text)
    if not phases:
        return probs
    verdicts = {}
    for m in CRITIC.finditer(text):
        head, _, gap = m.group("rest").partition(" gap=")
        kv = dict(re.findall(r"(\w+)=(\S+)", head))
        kv["gap"] = gap.strip()
        verdicts.setdefault((kv.get("preset"), kv.get("phase")), []).append((m.group("verdict"), kv))
    for pid, phid in phases:
        key = f"{pid}/{phid}"
        cur = spec_hash(data, pid, phid)
        if cur is None:
            P("C6", f"{key}: no such preset phase in pipeline/level/encounter.json")
            continue
        vs = verdicts.get((pid, phid), [])
        if not vs:
            P("C6", f"{key}: no `ENCOUNTER CRITIC:` line. Run the blind critic (`python3 tools/encounter_check.py "
              f"--critic-packet {key}`) in a fresh session and paste its verdict")
            continue
        rounds_ok = True
        prev = 0
        for v, kv in vs:
            rnd, pt, ck = _int(kv.get("round")), _int(kv.get("playthrough")), _int(kv.get("check"))
            if rnd is None or rnd <= prev:
                P("C6", f"{key}: round={kv.get('round')} must be a number above the round before ({prev}): one line "
                  "per round, in order")
                rounds_ok = False
                break
            if pt is None or ck is None:
                P("C6", f"{key}: round {rnd} has no playthrough=<n> check=<n> scores: record each round's "
                  "playthrough_check and encounter_check problem counts on its verdict line")
                rounds_ok = False
                break
            prev = rnd
        if not rounds_ok:
            continue
        last_v, last = vs[-1]
        if last_v != "PASS":
            if stuck(vs):
                P("C7", f"{key}: {STUCK_ROUNDS} FAIL rounds in a row with the same gap ({last.get('gap') or '?'}) and "
                  "no better playthrough or check score. Stuck: label the card needs-human and post "
                  f"`NEEDS HUMAN: <owner> {last.get('gap') or '<gap>'} <link> <time>`; the card stays open")
            else:
                P("C6", f"{key}: the newest critic verdict is FAIL (gap={last.get('gap') or '?'}): fix that gap, re-run "
                  "the playthrough and the critic (no round cap; the loop runs until PASS)")
            continue
        if last.get("spec") != cur:
            P("C6", f"{key}: the PASS is for spec={last.get('spec')}, the phase is now spec={cur}: the spec changed "
              "after the critic passed it; run the critic again")
        if not last.get("builder") or not last.get("critic") or last.get("builder") == last.get("critic"):
            P("C6", f"{key}: builder= and critic= must name two different sessions (the critic is blind and separate)")
    runs = [(m.group("preset"), set(m.group("phases").split(","))) for m in RUN_LINE.finditer(text)]
    for pid, phid in phases:
        if not any(r == pid and phid in ps for r, ps in runs):
            P("C8", f"{pid}/{phid}: no `playthrough_check: 0 problem(s) preset={pid} phases=...{phid}...` line "
              "(the automated run log of a full run through this phase)")
    for pid in sorted({pid for pid, _ in phases}):
        if not any(m.group("preset") == pid for m in READY_LINE.finditer(text)):
            P("C9", f"{pid}: no `encounter_ready: 0 problem(s) preset={pid}` line (`python3 tools/encounter_check.py "
              f"--ready --preset {pid}`: every hitbox, art and sound row exists)")
    return probs


# ---------- P1-P8 playthrough log ----------

def check_playthrough(data, pid, lines):
    """(problems, summary). lines: the log's text lines; only ENCOUNTER_EVT lines are read."""
    probs = []
    P = lambda rule, where, msg: probs.append((rule, where, msg))
    p = view(data, pid)
    if not p:
        return [("P1", "log", f"no preset {pid!r} in encounter.json")], ""
    ph_by, atk, tgt = _by_id(p.get("phases")), _by_id(p.get("attacks")), _by_id(p.get("targets"))
    evts = []
    for n, line in enumerate(lines, 1):
        i = line.find("ENCOUNTER_EVT")
        if i < 0:
            continue
        kv = dict(re.findall(r"(\w+)=(\S+)", line[i:]))
        where = f"line {n}"
        try:
            t = float(kv.get("t", ""))
        except ValueError:
            P("P1", where, "t is not a number")
            continue
        if kv.get("kind") not in EVT_KINDS:
            P("P1", where, f"unknown kind {kv.get('kind')!r}")
            continue
        if kv.get("preset") != pid:
            P("P1", where, f"preset {kv.get('preset')!r}, checking {pid}")
            continue
        if kv["kind"] != "end" and not kv.get("phase"):
            P("P1", where, "no phase=")
            continue
        evts.append((t, n, kv))
    if not evts:
        return [("P8", "log", "no ENCOUNTER_EVT line: the run logged nothing")], ""
    starts = [kv for _, _, kv in evts if kv["kind"] == "phase_start"]
    entry = (starts[0].get("entry") if starts else None) or "full_run"
    first = (p.get("entry") or {}).get(entry)
    want, cur = [], first
    while cur in ph_by and cur not in want:
        want.append(cur)
        cur = ph_by[cur].get("next")
    got = [kv.get("phase") for kv in starts]
    if got != want[:len(got)]:
        P("P2", "log", f"phases started {got}, the preset's order from {entry} is {want}")
    windows, tele, broken, cur_phase, t0, t_end = [], {}, {}, None, None, None
    open_tr = None
    for t, n, kv in evts:
        k, where = kv["kind"], f"line {n}"
        if k == "phase_start":
            cur_phase, t0 = kv["phase"], (t0 if t0 is not None else t)
        elif k == "transition_start":
            open_tr = t
        elif k == "transition_end":
            if open_tr is not None:
                windows.append((open_tr, t, "transition"))
            open_tr = None
        elif k == "break":
            tid = kv.get("target")
            broken[tid] = t
            stun = ((tgt.get(tid) or {}).get("on_break") or {}).get("stun_sec")
            if num(stun) and stun > 0:
                windows.append((t, t + stun, f"{tid} stun"))
            seq = (ph_by.get(kv["phase"]) or {}).get("sequence") or []
            if tid in seq:
                done = [x for x in seq if x in broken]
                if done != seq[:len(done)]:
                    P("P6", where, f"{tid} broke out of order: the sequence is {seq}")
        elif k in ("telegraph", "fire"):
            aid = kv.get("attack")
            a = atk.get(aid)
            if a is None:
                P("P5", where, f"unknown attack {aid!r}")
                continue
            if aid not in ((ph_by.get(kv["phase"]) or {}).get("attacks") or []):
                P("P5", where, f"{aid} in phase {kv['phase']}, which does not list it")
            cb = a.get("cancelled_by")
            if cb in broken and broken[cb] < t:
                P("P5", where, f"{aid} after {cb} broke at t={broken[cb]:g}: breaking it cancels this attack")
            inside = [w for w in windows if w[0] <= t < w[1]] + ([(open_tr, t, "transition")] if open_tr is not None else [])
            if inside:
                P("P4", where, f"{aid} {k} at t={t:g} inside the {inside[0][2]} that started at t={inside[0][0]:g}")
            if k == "telegraph":
                tele[aid] = t
            else:
                need = (a.get("telegraph") or {}).get("sec")
                if aid not in tele:
                    P("P3", where, f"{aid} fired with no telegraph before it")
                elif num(need) and t - tele[aid] < need - 1e-6:
                    P("P3", where, f"{aid} fired {t - tele[aid]:.2f} s after its telegraph; the spec is {need} s")
                tele.pop(aid, None)
        elif k == "phase_end":
            ew = (ph_by.get(kv["phase"]) or {}).get("ends_when") or {}
            for tid in list(ew.get("broken") or []) + ([ew["hp_zero"]] if ew.get("hp_zero") else []):
                if tid not in broken:
                    P("P6", where, f"phase {kv['phase']} ended with {tid} not broken")
        elif k == "end":
            t_end = t
    fl = p.get("fight_length_sec") or {}
    length = (t_end - t0) if t_end is not None and t0 is not None else None
    if t_end is None:
        P("P7", "log", "no end event: the run did not finish the fight")
    elif entry == "full_run" and num(fl.get("min")) and num(fl.get("max")) and not fl["min"] <= length <= fl["max"]:
        P("P7", "log", f"full run took {length:.1f} s, the target is {fl['min']}-{fl['max']} s")
    summary = (f"preset={pid} phases={','.join(got) or '-'} entry={entry} "
               f"length={'%.1fs' % length if length is not None else '-'}")
    return probs, summary
