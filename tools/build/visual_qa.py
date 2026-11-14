#!/usr/bin/env python3
"""Whole-frame visual QA against Ricky's Other Realm study (visualqa lane, Josh Nov 13: THE visual priority). Stdlib only.

  visual_qa.py run [--out DIR] [--require-baseline] [--main-sha SHA]
                                               capture (journeys/visual_qa.txt in a real window) then judge: the gate
                                               step; with --require-baseline a missing baseline for main exits 2
  visual_qa.py capture [--out DIR]             only capture: DIR/vq_play.png, vq_dc_route.png, vq_keeper.png (+ others)
  visual_qa.py judge --shots DIR               judge captured screens; exit 0 PASS, 1 FAIL, 2 could not run
  visual_qa.py frame IMAGE [--screen ID]       judge one picture (a calibration frame, a hand capture)
  visual_qa.py calibrate                       known-good study must PASS, Josh's 15:50 frame must FAIL
  visual_qa.py baseline --shots DIR --sha SHA  store a judged run as main's baseline (logs/visual-baseline/<sha>.json)
  visual_qa.py composite --before A --after B --out P   study | before | after, one row (the per-round composite)

Each screen is put side by side with the study (study left, game right) and one Opus session (claude -p, image input,
no tools) scores it on a FIXED rubric. FAIL when any screen has a "broken to a player" item, the judge's own verdict is
FAIL, or its total is below main's cached baseline for that screen by more than BASELINE_SLACK. Every judge call is
recorded under pipeline/qa/visual/judge-records/<key>.json (key = sha256 of model, prompt and image bytes) and replayed
when the same call comes again, so tests and repeat runs spend nothing. VISUAL_QA_REPLAY_ONLY=1 refuses a live call.
"""
import argparse
import base64
import hashlib
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
import time

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
STUDY = os.path.join("pipeline", "art", "reference", "discord", "20261111-0318_Ricky_other-realm.png")
CALIBRATION = os.path.join("pipeline", "qa", "visual", "calibration")
KNOWN_GOOD = os.path.join(CALIBRATION, "known-good-other-realm.png")
KNOWN_BAD = os.path.join(CALIBRATION, "known-bad-josh-1550.png")
RECORDS = os.path.join("pipeline", "qa", "visual", "judge-records")
JOURNEY = os.path.join("tools", "build", "journeys", "visual_qa.txt")
MODEL = os.environ.get("VISUAL_QA_MODEL", "claude-opus-5-5")
# Gameplay screens judged against the study, with the capture each one reads.
SCREENS = {"play": "vq_play.png", "dc_route": "vq_dc_route.png", "keeper": "vq_keeper.png"}
# The fixed rubric: each item scored 0-10 by the judge (10 = matches the study on that point).
RUBRIC = [
    ("dark_backdrop", "a dark, near-black atmospheric backdrop like the study (not bright paper, not cream)"),
    ("wind_ribbons", "wind drawn as thin, flowing ash-blue #555e60 ribbons (never boxes, cards, panels or framed pictures)"),
    ("small_figures", "figures (the girl with the umbrella, enemies, the Keeper) small in the frame as in the study"),
    ("floating_islands", "ground drawn as dark floating islands / eroded platforms, not flat bars or blocks"),
    ("shot_colours", "shots read as gold #E9C46A streaks (player) and red streaks (enemy)"),
    ("no_placeholders", "no flat placeholder cubes, solid colour boxes or bars anywhere"),
    ("no_framed_art", "no framed, bordered, unkeyed (rectangle-backed), stretched or rotated pictures"),
]
SCORE_MAX = 10
# A total this far under main's baseline fails. Zero: the brief says FAIL on any screen worse than main (16:45 review).
BASELINE_SLACK = 0
COMPOSITE_W, COMPOSITE_H = 960, 540
EXIT_PASS, EXIT_FAIL, EXIT_ERROR = 0, 1, 2


def rel(path):
    return path if os.path.isabs(path) else os.path.join(ROOT, path)


def prompt_text(screen):
    items = "\n".join("- %s: %s" % (k, d) for k, d in RUBRIC)
    keys = ", ".join('"%s": <0-%d>' % (k, SCORE_MAX) for k, _ in RUBRIC)
    return (
        "You judge one game screen against an art target, as a whole frame.\n"
        "The image is two pictures side by side. LEFT: the target, Ricky's 'Other Realm' study. RIGHT: the game screen "
        "'%s' (ignore the HUD clock and title text on either side; ignore any text label printed on the study).\n"
        "Score the RIGHT picture against the LEFT on each item, 0 (nothing like the study, or the item is broken) to %d "
        "(as the study):\n%s\n"
        "Then list everything on the RIGHT that a player would call broken: placeholder cubes or solid boxes, flat "
        "colour bars or panels, pictures with a drawn frame or a rectangle background, stretched or rotated pictures, "
        "a missing player character, a blank or black frame. Do not list a mere style difference.\n"
        "Answer with ONE JSON object and nothing else:\n"
        '{"scores": {%s}, "broken": ["<short item>", ...], "verdict": "PASS" or "FAIL"}\n'
        "verdict FAIL when anything is broken or the frame is far from the study."
    ) % (screen, SCORE_MAX, items, keys)


def composite(study, shot, out):
    """Study | shot, each fit in COMPOSITE_W x COMPOSITE_H on black (ffmpeg)."""
    fit = ("scale=%d:%d:force_original_aspect_ratio=decrease,pad=%d:%d:(ow-iw)/2:(oh-ih)/2:color=black"
           % (COMPOSITE_W, COMPOSITE_H, COMPOSITE_W, COMPOSITE_H))
    cmd = ["ffmpeg", "-v", "error", "-y", "-i", study, "-i", shot, "-filter_complex",
           "[0]%s[a];[1]%s[b];[a][b]hstack=2" % (fit, fit), "-frames:v", "1", out]
    subprocess.run(cmd, check=True, capture_output=True)
    return out


def composite_round(study, before, after, out, width=640, height=360):
    """Study | before | after in one row, each fit in width x height (the committed per-round composite)."""
    fit = ("scale=%d:%d:force_original_aspect_ratio=decrease,pad=%d:%d:(ow-iw)/2:(oh-ih)/2:color=black"
           % (width, height, width, height))
    cmd = ["ffmpeg", "-v", "error", "-y", "-i", study, "-i", before, "-i", after, "-filter_complex",
           "[0]%s[a];[1]%s[b];[2]%s[c];[a][b][c]hstack=3" % (fit, fit, fit), "-frames:v", "1", out]
    subprocess.run(cmd, check=True, capture_output=True)
    return out


def record_key(prompt, image_bytes, model=MODEL):
    h = hashlib.sha256()
    for part in (model.encode(), b"\0", prompt.encode(), b"\0", image_bytes):
        h.update(part)
    return h.hexdigest()[:32]


def claude_image_call(prompt, image_bytes, model=MODEL):
    """One fresh claude -p session, image input via stream-json, no tools. Returns the answer text."""
    msg = {"type": "user", "message": {"role": "user", "content": [
        {"type": "image", "source": {"type": "base64", "media_type": "image/png",
                                      "data": base64.b64encode(image_bytes).decode()}},
        {"type": "text", "text": prompt}]}}
    env = {k: v for k, v in os.environ.items() if k not in ("CLAUDECODE", "CLAUDE_CODE_ENTRYPOINT")}
    p = subprocess.run(["claude", "-p", "--model", model, "--tools", "", "--input-format", "stream-json",
                        "--output-format", "stream-json", "--verbose"],
                       input=json.dumps(msg) + "\n", capture_output=True, text=True, env=env, timeout=600)
    text = ""
    for line in p.stdout.splitlines():
        try:
            ev = json.loads(line)
        except ValueError:
            continue
        if ev.get("type") == "result" and isinstance(ev.get("result"), str):
            text = ev["result"]
    if not text:
        raise RuntimeError("judge call returned nothing (exit %d): %s" % (p.returncode, (p.stderr or p.stdout)[-400:]))
    return text


def judge_call(prompt, image_bytes, caller=None, records=None):
    """The judge's answer text, from the record when this exact call was made before."""
    records = rel(records or RECORDS)
    key = record_key(prompt, image_bytes)
    path = os.path.join(records, key + ".json")
    if os.path.exists(path):
        with open(path, encoding="utf-8") as fh:
            return json.load(fh)["answer"], True
    if os.environ.get("VISUAL_QA_REPLAY_ONLY") == "1":
        raise RuntimeError("no recorded judge call %s and VISUAL_QA_REPLAY_ONLY=1" % key)
    answer = (caller or claude_image_call)(prompt, image_bytes)
    os.makedirs(records, exist_ok=True)
    with open(path, "w", encoding="utf-8") as fh:
        json.dump({"model": MODEL, "key": key, "at": time.strftime("%Y-%m-%dT%H:%M:%S"), "answer": answer}, fh, indent=1)
    return answer, False


def parse_answer(text):
    """{"scores": {item: int}, "broken": [str], "verdict": "PASS"|"FAIL", "total": int}; ValueError on a bad answer."""
    m = re.search(r"\{.*\}", text or "", re.S)
    if not m:
        raise ValueError("no JSON object in the judge answer")
    data = json.loads(m.group(0))
    scores = data.get("scores")
    if not isinstance(scores, dict):
        raise ValueError("answer has no scores object")
    out = {}
    for key, _ in RUBRIC:
        v = scores.get(key)
        if isinstance(v, bool) or not isinstance(v, (int, float)) or not 0 <= v <= SCORE_MAX:
            raise ValueError("score %s missing or out of 0-%d: %r" % (key, SCORE_MAX, v))
        out[key] = int(round(v))
    broken = data.get("broken", [])
    if not isinstance(broken, list) or not all(isinstance(b, str) for b in broken):
        raise ValueError("broken must be a list of strings")
    verdict = str(data.get("verdict", "")).upper()
    if verdict not in ("PASS", "FAIL"):
        raise ValueError("verdict must be PASS or FAIL")
    return {"scores": out, "broken": [b.strip() for b in broken if b.strip()], "verdict": verdict,
            "total": sum(out.values())}


def decide(result, baseline_total=None):
    """(passed, reasons) for one judged screen against main's baseline total (None = no baseline). Pure."""
    reasons = []
    if result["broken"]:
        reasons.append("broken: " + "; ".join(result["broken"]))
    if result["verdict"] != "PASS":
        reasons.append("judge verdict FAIL")
    if baseline_total is not None and result["total"] < baseline_total - BASELINE_SLACK:
        reasons.append("total %d below main's %d" % (result["total"], baseline_total))
    return not reasons, reasons


def judge_image(shot, screen, caller=None, records=None, keep=None):
    """Judge one picture against the study. Returns the parsed result plus the composite path and replay flag."""
    tmp = tempfile.mkdtemp(prefix="visualqa_")
    try:
        comp = composite(rel(STUDY), shot, os.path.join(tmp, "composite.png"))
        with open(comp, "rb") as fh:
            image = fh.read()
        if keep:
            shutil.copyfile(comp, keep)
        answer, replayed = judge_call(prompt_text(screen), image, caller, records)
    finally:
        shutil.rmtree(tmp, ignore_errors=True)
    result = parse_answer(answer)
    result.update(replayed=replayed, shot=os.path.relpath(shot, ROOT) if shot.startswith(ROOT) else shot)
    return result


def baseline_dir():
    return os.environ.get("VISUAL_BASELINE_DIR", os.path.join(ROOT, "..", "logs", "visual-baseline"))


def main_sha():
    p = subprocess.run(["git", "-C", ROOT, "rev-parse", "origin/main"], capture_output=True, text=True)
    return p.stdout.strip() if p.returncode == 0 else ""


def load_baseline(sha):
    path = os.path.join(baseline_dir(), sha + ".json") if sha else ""
    if path and os.path.exists(path):
        with open(path, encoding="utf-8") as fh:
            return json.load(fh)
    return None


def judge_shots(shots_dir, caller=None, records=None, baseline=None, composites_dir=None):
    """Judge every gameplay screen in shots_dir. Returns (exit code, summary line, per-screen results)."""
    results, failed, missing = {}, [], []
    for screen, name in SCREENS.items():
        shot = os.path.join(shots_dir, name)
        if not os.path.exists(shot):
            missing.append(screen)
            continue
        keep = os.path.join(composites_dir, "judge_%s.png" % screen) if composites_dir else None
        res = judge_image(shot, screen, caller, records, keep)
        base = (baseline or {}).get("screens", {}).get(screen, {}).get("total")
        ok, reasons = decide(res, base)
        res.update(passed=ok, reasons=reasons, baseline_total=base)
        results[screen] = res
        if not ok:
            failed.append(screen)
    if missing:
        return EXIT_ERROR, "VISUAL_QA ERROR missing captures: %s (in %s)" % (", ".join(missing), shots_dir), results
    parts = " ".join("%s=%d/%d" % (s, r["total"], SCORE_MAX * len(RUBRIC)) for s, r in results.items())
    broken = sum(len(r["broken"]) for r in results.values())
    tag = "PASS" if not failed else "FAIL"
    line = "VISUAL_QA %s %s broken=%d baseline=%s%s" % (
        tag, parts, broken, (baseline or {}).get("sha", "none")[:12] or "none",
        (" failed=" + ",".join(failed)) if failed else "")
    return (EXIT_PASS if not failed else EXIT_FAIL), line, results


def capture(out_dir):
    """Run the visual QA journey in a real window through the engine slot. Returns the run's exit code."""
    os.makedirs(out_dir, exist_ok=True)
    env = dict(os.environ)
    env.setdefault("RUN_RES", "1280x720")
    cmd = [os.path.join(ROOT, "tools", "build", "ue_slot.sh"), os.path.join(ROOT, "tools", "build", "run_game.sh"),
           "-SmokeJourney=" + os.path.join(ROOT, JOURNEY), "-SmokeJourneyOut=" + os.path.abspath(out_dir)]
    return subprocess.run(cmd, cwd=ROOT, env=env).returncode


def write_report(out_dir, line, results):
    with open(os.path.join(out_dir, "visual_qa.json"), "w", encoding="utf-8") as fh:
        json.dump({"summary": line, "model": MODEL, "screens": results}, fh, indent=1)


def cmd_judge(shots, caller=None, require_baseline=False, sha=None):
    sha = sha or main_sha()
    baseline = load_baseline(sha)
    if require_baseline and baseline is None:
        # The gate compares against main; without main's baseline the comparison cannot run (16:28 review).
        print("VISUAL_QA ERROR no baseline for main %s in %s: python3 tools/build/visual_qa.py baseline --shots <main run> --sha %s"
              % (sha[:12] or "?", baseline_dir(), sha or "<main sha>"))
        return EXIT_ERROR
    code, line, results = judge_shots(shots, caller, baseline=baseline, composites_dir=shots)
    write_report(shots, line, results)
    for screen, r in results.items():
        for reason in r["reasons"]:
            print("  %s: %s" % (screen, reason))
    print(line)
    return code


def cmd_calibrate(caller=None):
    good = judge_image(rel(KNOWN_GOOD), "known-good", caller)
    bad = judge_image(rel(KNOWN_BAD), "known-bad", caller)
    good_ok, _ = decide(good)
    bad_ok, bad_reasons = decide(bad)
    print("known-good %s total=%d broken=%d" % ("PASS" if good_ok else "FAIL", good["total"], len(good["broken"])))
    print("known-bad  %s total=%d (%s)" % ("PASS" if bad_ok else "FAIL", bad["total"], "; ".join(bad_reasons)))
    ok = good_ok and not bad_ok
    print("VISUAL_QA CALIBRATION %s" % ("PASS" if ok else "FAIL"))
    return EXIT_PASS if ok else EXIT_FAIL


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)
    for name in ("run", "capture"):
        p = sub.add_parser(name)
        p.add_argument("--out", default=os.path.join(ROOT, "Saved", "VisualQA", time.strftime("%Y%m%d-%H%M%S")))
        if name == "run":
            p.add_argument("--require-baseline", action="store_true")
            p.add_argument("--main-sha", default="")
    p = sub.add_parser("judge")
    p.add_argument("--shots", required=True)
    p.add_argument("--require-baseline", action="store_true")
    p.add_argument("--main-sha", default="")
    p = sub.add_parser("frame")
    p.add_argument("image")
    p.add_argument("--screen", default="play")
    sub.add_parser("calibrate")
    p = sub.add_parser("composite")
    p.add_argument("--before", required=True)
    p.add_argument("--after", required=True)
    p.add_argument("--out", required=True)
    p = sub.add_parser("baseline")
    p.add_argument("--shots", required=True)
    p.add_argument("--sha", default="")
    args = ap.parse_args(argv)
    try:
        if args.cmd == "capture":
            return EXIT_PASS if capture(args.out) == 0 else EXIT_ERROR
        if args.cmd == "run":
            if args.require_baseline and load_baseline(args.main_sha or main_sha()) is None:
                return cmd_judge(args.out, require_baseline=True, sha=args.main_sha)
            code = capture(args.out)
            if code != 0 and not all(os.path.exists(os.path.join(args.out, n)) for n in SCREENS.values()):
                print("VISUAL_QA ERROR capture failed (exit %d), see %s" % (code, args.out))
                return EXIT_ERROR
            return cmd_judge(args.out, require_baseline=args.require_baseline, sha=args.main_sha)
        if args.cmd == "judge":
            return cmd_judge(args.shots, require_baseline=args.require_baseline, sha=args.main_sha)
        if args.cmd == "frame":
            r = judge_image(os.path.abspath(args.image), args.screen)
            ok, reasons = decide(r)
            print(json.dumps(r, indent=1))
            print("VISUAL_QA %s %s=%d %s" % ("PASS" if ok else "FAIL", args.screen, r["total"], "; ".join(reasons)))
            return EXIT_PASS if ok else EXIT_FAIL
        if args.cmd == "calibrate":
            return cmd_calibrate()
        if args.cmd == "composite":
            print(composite_round(rel(STUDY), args.before, args.after, args.out))
            return EXIT_PASS
        if args.cmd == "baseline":
            sha = args.sha or main_sha()
            code, line, results = judge_shots(args.shots)
            if code != EXIT_PASS:
                # A failing or incomplete run never becomes main's baseline (16:45 review).
                print("visual_qa baseline NOT stored for %s: %s" % (sha[:12], line))
                return code
            os.makedirs(baseline_dir(), exist_ok=True)
            with open(os.path.join(baseline_dir(), sha + ".json"), "w", encoding="utf-8") as fh:
                json.dump({"sha": sha, "summary": line, "screens": results}, fh, indent=1)
            print("visual_qa baseline %s: %s" % (sha[:12], line))
            return EXIT_PASS
    except (RuntimeError, ValueError, OSError, subprocess.SubprocessError) as exc:
        print("VISUAL_QA ERROR %s" % exc)
        return EXIT_ERROR
    return EXIT_ERROR


if __name__ == "__main__":
    sys.exit(main())
