#!/usr/bin/env python3
"""Check automated-playtest run-log lines against the GDD rows (CAM-04, CAM-07, FLOW-25, FLOW-28, HAZ-16).

Run log lines (key=value, written by the scripted run in Source/UmbrellaElla/Private/Smoke):
  PLAYTEST_CAM04   profile=<v> health=full|min trim= entered=0|1 accel_t90= vx_peak= exit_edge=right|top|bottom|left|none
                   exit_t= exit_root_z= vert_disp= root_z_min= root_z_max= half_h= ride_s= qualified=0|1   (played path)
  PLAYTEST_CAM04T  profile=<v> rode=0|1 steady_vx= steady_vz= accel_t90= brake_t10= reacq_t90= decay_open_t10=
                   decay_fall_t10= drift_open= drift_fall=   (motor transients in the real current; -1 = never)
  PLAYTEST_FLOW25  drawn_width= usable_width= tol= lead_left_ok=0|1 lead_right_ok=0|1 stages_total= stages_covered=
  PLAYTEST_CAM07   case=ontime|late|missed reopen_root_z= min_root_z= min_clear= caught=0|1
                   required_current_active=0|1 challenge_clear=0|1   (played fold from RESET and reopen)
  PLAYTEST_FLOW28  health_before= health_after= max= threats= framing_settled=0|1 boss_began=0|1
  PLAYTEST_HAZ16   res=WxH debug=0|1 health=healthy|low attempts= useful_hits= damage= reset_s= warned=0|1
                   autoaim=0|1 invuln=0|1 teleport=0|1 boring=0|1 cleared=0|1
Every line ends relay=0|1. relay=1 lines come from -PlaytestWindRelay diagnosis runs (wind events re-sent with the
contract player id); they are printed as a projection and never count toward a row's verdict.
Usage: playtest_check.py LOG [--json]   exit 0 = every row passes, 1 = a row fails or has no measurement.
"""
import json
import re
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import playtest_calibration as CAL  # noqa: E402

ROWS = ("CAM-04", "CAM-07", "FLOW-25", "FLOW-28", "HAZ-16")
LINE = re.compile(r"PLAYTEST_(CAM04T|CAM04|CAM07|FLOW25|FLOW28|HAZ16)\b(.*)")
TRIMS = {"-1.00", "0.00", "1.00"}
TRANSIENTS = ("accel_t90", "brake_t10", "reacq_t90", "decay_open_t10", "decay_fall_t10")


def parse(text, relay=False):
    """Lines of one kind: relay=False keeps the game's own runs, relay=True only -PlaytestWindRelay diagnosis runs."""
    out = {}
    for m in LINE.finditer(text):
        kv = dict(p.split("=", 1) for p in m.group(2).split() if "=" in p)
        if (kv.get("relay") == "1") != relay:
            continue
        out.setdefault(m.group(1), []).append(kv)
    return out


def _f(kv, k):
    return float(kv[k])


def check_cam04(recs, transients=()):
    """Every supported profile (full and min health x trim -1/0/+1) must be carried out of the band's far edge by the
    real current, and the motor transients must be measured (all finite) with Ella riding."""
    errs = []
    seen = {(r.get("health"), r.get("trim")) for r in recs}
    for health in ("full", "min"):
        for trim in sorted(TRIMS):
            if (health, trim) not in seen:
                errs.append("no %s-health trim %s path" % (health, trim))
    for r in recs:
        tag = "%s/%s" % (r.get("profile"), r.get("health"))
        if r.get("entered") != "1":
            errs.append("%s: never rode the current" % tag)
        elif r.get("exit_edge") != "right":
            errs.append("%s: left the band by the %s at root z %s before its far edge" % (tag, r.get("exit_edge"), r.get("exit_root_z")))
        if r.get("qualified") != "1":
            errs.append("%s: not qualified" % tag)
    if not transients:
        errs.append("no transient measurement (CAM04T)")
    for t in transients:
        if t.get("rode") != "1":
            errs.append("transients: never rode the current")
        for k in TRANSIENTS:
            if _f(t, k) < 0:
                errs.append("transients: %s never reached" % k)
        for k, (lo, hi) in CAL.TRANSIENT_RANGES.items():
            if k in t and _f(t, k) >= 0 and not lo <= _f(t, k) <= hi:
                errs.append("transients: %s %.2f outside fixed range %.2f-%.2f (%s)" % (k, _f(t, k), lo, hi, CAL.PROFILE))
    return errs


def check_flow25(recs):
    errs = []
    for r in recs:
        if abs(_f(r, "drawn_width") - _f(r, "usable_width")) > _f(r, "tol"):
            errs.append("drawn wind width differs from usable width")
        if r.get("lead_left_ok") != "1" or r.get("lead_right_ok") != "1":
            errs.append("camera lead fails in a direction")
        if int(r["stages_covered"]) != int(r["stages_total"]):
            errs.append("route stage without background")
    return errs


def check_cam07(recs):
    """On-time and late reopenings must be caught by a real current with the body above the floor. The missed case
    (below the band) is reported, not gated: it is the HAZ-07 assist's job."""
    errs = []
    cases = {r.get("case"): r for r in recs}
    for case in ("ontime", "late"):
        r = cases.get(case)
        if r is None:
            errs.append("no %s reopen case" % case)
            continue
        if r.get("caught") != "1":
            errs.append("%s reopen at root z %s: no current caught her" % (case, r.get("reopen_root_z")))
        if _f(r, "min_clear") <= 0:
            errs.append("%s reopen: body reached the floor (clearance %s)" % (case, r.get("min_clear")))
    for r in recs:
        if r.get("challenge_clear") != "1" and r.get("required_current_active") != "1":
            errs.append("required current gone before challenge clear")
    return errs


def check_flow28(recs):
    errs = []
    for r in recs:
        after, before, mx = int(r["health_after"]), int(r["health_before"]), int(r["max"])
        if after > before or after > mx:
            errs.append("free heal at checkpoint/boss arrival")
        if r.get("boss_began") == "1" and (int(r["threats"]) != 0 or r.get("framing_settled") != "1"):
            errs.append("boss began with threats or unsettled framing")
        if r.get("boss_began") != "1":
            errs.append("boss did not begin")
    return errs


def check_haz16(recs):
    errs = []
    res = {r.get("res") for r in recs}
    if not {"1280x720", "1920x1080"} <= res:
        errs.append("need runs at 1280x720 and 1920x1080")
    if not {"healthy", "low"} <= {r.get("health") for r in recs}:
        errs.append("need healthy and low health runs")
    for r in recs:
        if r.get("debug") != "0":
            errs.append("debug draw on")
        if "1" in (r.get("autoaim"), r.get("invuln"), r.get("teleport")):
            errs.append("autoaim/invulnerability/teleport cannot pass fairness")
        if r.get("boring") == "1":
            errs.append("rejected as boring")
        if r.get("cleared") != "1":
            errs.append("room not cleared")
    return errs


CHECKS = {"CAM04": check_cam04, "FLOW25": check_flow25, "CAM07": check_cam07, "FLOW28": check_flow28,
          "HAZ16": check_haz16}


def evaluate(text, relay=False):
    """Verdict per row from the game's own runs. relay=True judges the diagnosis runs instead (a projection, never a pass)."""
    recs = parse(text, relay)
    result = {}
    for key, fn in CHECKS.items():
        row = key[:-2] + "-" + key[-2:]
        if key not in recs:
            result[row] = {"pass": False, "errors": ["no measurement (NOT RUN)"]}
            continue
        unmeasured = sorted({r["not_measured"] for r in recs[key] if r.get("not_measured")})
        try:
            errs = ["NOT MEASURED: %s" % u for u in unmeasured]
            errs += fn(recs[key], recs.get("CAM04T", [])) if key == "CAM04" else fn(recs[key])
        except (KeyError, ValueError) as e:
            errs = ["malformed line: %s" % e]
        result[row] = {"pass": not errs, "errors": errs}
    return result


def main(argv):
    if not argv:
        print(__doc__)
        return 2
    text = open(argv[0], errors="replace").read()
    result = evaluate(text)
    projected = evaluate(text, relay=True) if parse(text, relay=True) else {}
    if "--json" in argv:
        print(json.dumps({"rows": result, "projected_with_wind_relay": projected}, indent=1))
    else:
        for row, v in result.items():
            print("%-8s %s %s" % (row, "PASS" if v["pass"] else "FAIL", "; ".join(v["errors"])))
        for row, v in projected.items():
            print("  projected with wind relay (diagnosis, not a verdict) %-8s %s %s"
                  % (row, "pass" if v["pass"] else "fail", "; ".join(v["errors"])))
    return 0 if all(v["pass"] for v in result.values()) else 1


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
