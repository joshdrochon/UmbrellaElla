#!/usr/bin/env python3
"""Check automated-playtest run-log lines against the GDD rows (CAM-04, CAM-07, FLOW-25, FLOW-28, HAZ-16).

Run log lines (key=value, written by the scripted run in Source/UmbrellaElla/Private/Smoke):
  PLAYTEST_CAM04   profile=<v> health=full|min lift_min= lift_max= vert_disp= env_min= env_max= qualified=0|1
  PLAYTEST_FLOW25  drawn_width= usable_width= tol= lead_left_ok=0|1 lead_right_ok=0|1 stages_total= stages_covered=
  PLAYTEST_CAM07   decision_height= reopen_height= required_current_active=0|1 challenge_clear=0|1
  PLAYTEST_FLOW28  health_before= health_after= max= threats= framing_settled=0|1 boss_began=0|1
  PLAYTEST_HAZ16   res=WxH debug=0|1 health=healthy|low attempts= useful_hits= damage= reset_s= warned=0|1
                   autoaim=0|1 invuln=0|1 teleport=0|1 boring=0|1 cleared=0|1
Usage: playtest_check.py LOG [--json]   exit 0 = every row passes, 1 = a row fails or has no measurement.
"""
import json
import re
import sys

ROWS = ("CAM-04", "CAM-07", "FLOW-25", "FLOW-28", "HAZ-16")
LINE = re.compile(r"PLAYTEST_(CAM04|CAM07|FLOW25|FLOW28|HAZ16)\b(.*)")


def parse(text):
    out = {}
    for m in LINE.finditer(text):
        kv = dict(p.split("=", 1) for p in m.group(2).split() if "=" in p)
        out.setdefault(m.group(1), []).append(kv)
    return out


def _f(kv, k):
    return float(kv[k])


def check_cam04(recs):
    errs = []
    if not any(r.get("health") == "full" for r in recs) or not any(r.get("health") == "min" for r in recs):
        errs.append("need full and min health measurements")
    for r in recs:
        if r.get("qualified") != "1":
            errs.append("profile %s not qualified" % r.get("profile"))
        if not _f(r, "env_min") <= _f(r, "vert_disp") <= _f(r, "env_max"):
            errs.append("vertical displacement outside envelope")
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
    errs = []
    for r in recs:
        if _f(r, "decision_height") < _f(r, "reopen_height"):
            errs.append("not enough height to reopen")
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


def evaluate(text):
    recs = parse(text)
    result = {}
    for key, fn in CHECKS.items():
        row = key[:-2] + "-" + key[-2:]
        if key not in recs:
            result[row] = {"pass": False, "errors": ["no measurement (NOT RUN)"]}
            continue
        try:
            errs = fn(recs[key])
        except (KeyError, ValueError) as e:
            errs = ["malformed line: %s" % e]
        result[row] = {"pass": not errs, "errors": errs}
    return result


def main(argv):
    if not argv:
        print(__doc__)
        return 2
    result = evaluate(open(argv[0], errors="replace").read())
    if "--json" in argv:
        print(json.dumps(result, indent=1))
    else:
        for row, v in result.items():
            print("%-8s %s %s" % (row, "PASS" if v["pass"] else "FAIL", "; ".join(v["errors"])))
    return 0 if all(v["pass"] for v in result.values()) else 1


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
