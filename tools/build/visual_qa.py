#!/usr/bin/env python3
"""Whole-frame visual QA against Ricky's Other Realm study (visualqa lane, Josh Nov 13: THE visual priority). Stdlib only.

  visual_qa.py run [--out DIR] [--require-baseline] [--main-sha SHA]
                                               capture (journeys/visual_qa.txt in a real window) then judge: the gate
                                               step; with --require-baseline a missing baseline for main exits 2
  visual_qa.py capture [--out DIR]             only capture: DIR/vq_play.png, vq_dc_route.png, vq_keeper.png (+ others)
  visual_qa.py judge --shots DIR               judge captured screens; exit 0 PASS, 1 FAIL, 2 could not run
  visual_qa.py frame IMAGE [--screen ID]       judge one picture (a calibration frame, a hand capture)
  visual_qa.py calibrate                       known-good study must PASS, Josh's 15:50 frame must FAIL
  visual_qa.py run --gate [--out DIR] [--main-sha SHA]
                                               the merge gate (lead 17:32): needs main's baseline (exit 2 if missing),
                                               FAILs only on a regression against it, one summary line
  visual_qa.py baseline --shots DIR --sha SHA  store a judged run as main's baseline (logs/visual-baseline/<sha>.json)
  visual_qa.py baseline --from-main [--out DIR] [--sha SHA]
                                               bootstrap: capture this checkout (must be at main) and store its judged
                                               run as main's baseline even when main itself has broken items; once per sha
  visual_qa.py baseline --from-main --shots DIR --sha SHA
                                               no capture: store DIR (the gate's run of the tree that became main SHA,
                                               judge calls replayed, no spend) as main's baseline
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
# Judge noise, measured Nov 13 (status file; pipeline/qa/visual/noise/): the same frame judged 6 times (the stored run +
# 5 samples) on main b4c1fe79's and the owl merge 0d74b84a's three screens scored totals spread up to 6 points
# (main dc_route 23..29), and one run fell at most 3.5 under its frame's median (main play 20 vs 23.5).
# The gate compares one judged run with main's median when main's baseline has samples (GATE_TOTAL_SLACK = 4, the
# 3.5 rounded up), else with main's one stored run (GATE_TOTAL_SLACK_SINGLE = 6, the full spread).
GATE_TOTAL_SLACK = 4
GATE_TOTAL_SLACK_SINGLE = 6
# Extra judged runs of main's shots stored with every new baseline (the number the noise above was measured with).
BASELINE_SAMPLES = int(os.environ.get("VISUAL_QA_BASELINE_SAMPLES", "5"))
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


def judge_call(prompt, image_bytes, caller=None, records=None, sample=0):
    """The judge's answer text, from the record when this exact call was made before.
    sample > 0: an independent repeat of the same call (its own record), used to measure judge noise."""
    records = rel(records or RECORDS)
    key = record_key(prompt if not sample else "%s\0sample=%d" % (prompt, sample), image_bytes)
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


def judge_image(shot, screen, caller=None, records=None, keep=None, sample=0):
    """Judge one picture against the study. Returns the parsed result plus the composite path and replay flag."""
    tmp = tempfile.mkdtemp(prefix="visualqa_")
    try:
        comp = composite(rel(STUDY), shot, os.path.join(tmp, "composite.png"))
        with open(comp, "rb") as fh:
            image = fh.read()
        if keep:
            shutil.copyfile(comp, keep)
        answer, replayed = judge_call(prompt_text(screen), image, caller, records, sample)
    finally:
        shutil.rmtree(tmp, ignore_errors=True)
    result = parse_answer(answer)
    result.update(replayed=replayed, shot=os.path.relpath(shot, ROOT) if shot.startswith(ROOT) else shot)
    return result


# Paths whose change can change a captured frame. A main commit that touches none of them keeps its parent's baseline.
# pipeline/art reaches the frame only through generated Source (art_slots.py -> ArtSlotCatalog.inc), so it is not listed:
# the lead's approvals.json commits on main keep the baseline.
VISUAL_PATHS = ("Source", "Content", "Config", "Art", "UmbrellaElla.uproject")


def norm_item(text):
    """A 'broken to a player' item in a comparable form: lower case, letters and digits only, single spaces."""
    return " ".join(re.sub(r"[^a-z0-9#]+", " ", (text or "").lower()).split())


# Defect kinds for the gate's "already known on main" match (lead 19:50): the judge words one defect differently run to
# run ("thin flat white vertical line running from the top of the frame down to the player" vs "stray thin vertical
# white line from the top of the frame to the player"), so an item is matched by its kind, not its text. First rule
# that matches wins; an item no rule matches keeps its exact normalised text as its kind (no looser than before).
# Location words are not part of the key: the judge names one place three ways ("mid-right", "right middle",
# "right-centre"). Counts are: a second bar where main had one is still a new item.
DEFECT_KINDS = [
    ("line", r"\b(line|lines|thread|wire|hairline|seam)\b|\bvertical\b.*\bbar\b"),
    ("unkeyed", r"\bunkeyed\b|\b(rectangle|rectangular|square|box)\w* (background|backing|behind|halo)"
                r"|\bhard[ -]?(cut|edged?|cropped)\b|\b(rectangle|square)[ -]backed\b"),
    ("too_large", r"\b(huge|very large|too large|oversized|too big|drawn large|is large|large in the frame)\b"
                  r"|\bdominat"),
    ("stray_mark", r"\b(dot|disc|glyph|speck|blob)\b|\bsmall (white )?(box|rectangle)\b"),
    ("shots", r"\bshots?\b.*\b(bars?|dash|dashes)\b|\b(dash|dashes)\b|\b(instead of|not) streaks\b"),
    ("no_islands", r"\bno (clear |visible )?(floating |ground )?(islands?|platforms?)\b(?! art)"),
    ("bright_backdrop", r"\b(cream|paper|bright|white|beige)\b.*\b(backdrop|background|sky)\b"
                        r"|\b(backdrop|background)\b.*\b(cream|paper|bright|beige)\b"),
    ("framed", r"\b(framed|bordered|border|borders|bezel)\b|\b(drawn|picture|visible|heavy) frame\b"),
    ("stretched", r"\b(stretched|squashed|distorted)\b"),
    ("rotated", r"\b(rotated|tilted|sideways|upside down)\b"),
    ("bar", r"\b(bar|bars|band|strip|slab|plank)\b"),
    ("box", r"\b(cube|cubes|box|boxes|block|blocks|rectangle|rectangles)\b"),
    ("no_wind", r"\b(no|missing|absent|without|lacks?|lacking)\b.*\bwind\b|\bwind\b.*\b(missing|absent|not visible)\b"),
    ("player_missing", r"\b(player|girl|ella|character|heroine)\b.*\b(missing|absent|invisible|not visible|barely|"
                       r"hard to see|lost|hidden|faint)\b|\b(missing|no|invisible)\b.*\b(player|girl|ella|heroine)\b"),
    ("blank_frame", r"\b(blank|black|empty)\b.*\b(frame|screen)\b"),
]


def defect_kind(text):
    """The defect kind of one 'broken' item (DEFECT_KINDS), or its normalised text when no rule matches."""
    t = norm_item(text)
    for kind, pattern in DEFECT_KINDS:
        if re.search(pattern, t):
            return kind
    return t


def kind_counts(items):
    """{kind: count} for a list of broken items."""
    out = {}
    for b in items or []:
        k = defect_kind(b)
        out[k] = out.get(k, 0) + 1
    return out


def known_kinds(base_screen):
    """Main's known defects for one screen: per kind, the most items any one of main's judged runs listed (the stored
    run plus its recorded noise samples: the judge leaves a real defect out of some runs)."""
    runs = [(base_screen or {}).get("broken", [])] + [s.get("broken", []) for s in (base_screen or {}).get("samples", [])]
    known = {}
    for run in runs:
        for k, c in kind_counts(run).items():
            known[k] = max(known.get(k, 0), c)
    return known


def base_total(base_screen):
    """(main's total for the gate, slack): the median of main's judged runs when the baseline has samples, else its
    one stored run with the wider single-run slack. (None, 0) without a baseline."""
    base_screen = base_screen or {}
    if base_screen.get("total") is None:
        return None, 0
    totals = sorted([base_screen["total"]] + [x["total"] for x in base_screen.get("samples", [])])
    if len(totals) == 1:
        return totals[0], GATE_TOTAL_SLACK_SINGLE
    mid = len(totals) // 2
    median = totals[mid] if len(totals) % 2 else (totals[mid - 1] + totals[mid]) / 2.0
    return median, GATE_TOTAL_SLACK


def decide_gate(result, base_screen):
    """(passed, reasons) for the merge gate: only a regression against main's baseline screen fails. Pure.
    Regression = total below main's total by more than the measured judge noise (base_total), or more broken items of
    one defect kind than any of main's judged runs listed (known_kinds). Main's own broken items and the judge's FAIL
    verdict do not fail the gate. The reason line names the kind of each new item."""
    reasons = []
    base, slack = base_total(base_screen)
    if base is not None and result["total"] < base - slack:
        reasons.append("total %d below main's %g (slack %d)" % (result["total"], base, slack))
    left = known_kinds(base_screen)
    new = []
    for b in result["broken"]:
        k = defect_kind(b)
        if left.get(k, 0) > 0:
            left[k] -= 1
        else:
            new.append("%s [%s]" % (b, k))
    if new:
        reasons.append("new broken: " + "; ".join(new))
    return not reasons, reasons


def baseline_dir():
    return os.environ.get("VISUAL_BASELINE_DIR", os.path.join(ROOT, "..", "logs", "visual-baseline"))


def main_sha():
    p = subprocess.run(["git", "-C", ROOT, "rev-parse", "origin/main"], capture_output=True, text=True)
    return p.stdout.strip() if p.returncode == 0 else ""


def baseline_path(sha):
    return os.path.join(baseline_dir(), sha + ".json")


def _git(*args):
    p = subprocess.run(["git", "-C", ROOT] + list(args), capture_output=True, text=True)
    return p.stdout if p.returncode == 0 else None


def load_baseline(sha, walk=0):
    """Main's baseline for sha. With walk > 0, an ancestor's baseline also counts (up to walk first-parent commits back)
    when nothing between it and sha touches VISUAL_PATHS: a docs-only merge to main does not need a new capture."""
    if not sha:
        return None
    if os.path.exists(baseline_path(sha)):
        with open(baseline_path(sha), encoding="utf-8") as fh:
            return json.load(fh)
    if walk <= 0:
        return None
    for anc in (_git("rev-list", "--first-parent", "-n", str(walk + 1), sha) or "").split()[1:]:
        if not os.path.exists(baseline_path(anc)):
            continue
        changed = _git("diff", "--name-only", anc, sha, "--", *VISUAL_PATHS)
        if changed is None or changed.strip():
            return None   # a frame-changing commit since that baseline: it no longer stands for main
        with open(baseline_path(anc), encoding="utf-8") as fh:
            return json.load(fh)
    return None


def judge_shots(shots_dir, caller=None, records=None, baseline=None, composites_dir=None, gate=False):
    """Judge every gameplay screen in shots_dir. Returns (exit code, summary line, per-screen results).
    gate=True: a screen fails only on a regression against baseline (decide_gate)."""
    results, failed, missing = {}, [], []
    for screen, name in SCREENS.items():
        shot = os.path.join(shots_dir, name)
        if not os.path.exists(shot):
            missing.append(screen)
            continue
        keep = os.path.join(composites_dir, "judge_%s.png" % screen) if composites_dir else None
        res = judge_image(shot, screen, caller, records, keep)
        base_screen = (baseline or {}).get("screens", {}).get(screen, {})
        base = base_screen.get("total")
        ok, reasons = decide_gate(res, base_screen) if gate else decide(res, base)
        res.update(passed=ok, reasons=reasons, baseline_total=base)
        results[screen] = res
        if not ok:
            failed.append(screen)
    if missing:
        return EXIT_ERROR, "VISUAL_QA ERROR missing captures: %s (in %s)" % (", ".join(missing), shots_dir), results
    parts = " ".join("%s=%d/%d" % (s, r["total"], SCORE_MAX * len(RUBRIC)) for s, r in results.items())
    broken = sum(len(r["broken"]) for r in results.values())
    tag = "PASS" if not failed else "FAIL"
    line = "VISUAL_QA %s%s %s broken=%d baseline=%s%s" % (
        "GATE " if gate else "", tag, parts, broken, (baseline or {}).get("sha", "none")[:12] or "none",
        (" failed=" + ",".join(failed)) if failed else "")
    return (EXIT_PASS if not failed else EXIT_FAIL), line, results


def user_state_files(root=None):
    root = root or ROOT
    """The files a game run writes as player state: save slots and GameUserSettings.ini (tutorial seen)."""
    found = []
    saves = os.path.join(root, "Saved", "SaveGames")
    for base, _dirs, names in os.walk(saves):
        found += [os.path.join(base, n) for n in names]
    config = os.path.join(root, "Saved", "Config")
    if os.path.isdir(config):
        for plat in os.listdir(config):
            ini = os.path.join(config, plat, "GameUserSettings.ini")
            if os.path.isfile(ini):
                found.append(ini)
    return sorted(found)


def snapshot_user_state(root=None):
    snap = {}
    for path in user_state_files(root):
        with open(path, "rb") as fh:
            snap[path] = fh.read()
    return snap


def restore_user_state(snap, root=None):
    """Put player state back as it was before the run: a capture plays Director's Cut and earns points and the
    tutorial flag, and a later automation run in the same tree then starts on the purchase or tutorial screen
    (UmbrellaElla.Flow.World.LevelUpShowsAndResumes failed the gate that way, Nov 13)."""
    for path in user_state_files(root):
        if path not in snap:
            os.remove(path)
    for path, data in snap.items():
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, "wb") as fh:
            fh.write(data)


def capture(out_dir):
    """Run the visual QA journey in a real window through the engine slot. Returns the run's exit code.
    Player state (saves, GameUserSettings.ini) is restored after the run, so captures never change later tests."""
    os.makedirs(out_dir, exist_ok=True)
    env = dict(os.environ)
    env.setdefault("RUN_RES", "1280x720")
    cmd = [os.path.join(ROOT, "tools", "build", "ue_slot.sh"), os.path.join(ROOT, "tools", "build", "run_game.sh"),
           "-SmokeJourney=" + os.path.join(ROOT, JOURNEY), "-SmokeJourneyOut=" + os.path.abspath(out_dir)]
    snap = snapshot_user_state()
    try:
        return subprocess.run(cmd, cwd=ROOT, env=env).returncode
    finally:
        restore_user_state(snap)


def write_report(out_dir, line, results):
    with open(os.path.join(out_dir, "visual_qa.json"), "w", encoding="utf-8") as fh:
        json.dump({"summary": line, "model": MODEL, "screens": results}, fh, indent=1)


GATE_WALK = 50   # first-parent commits the gate looks back for a baseline with no frame-changing commit since


def missing_baseline_line(sha):
    return ("VISUAL_QA ERROR no baseline for main %s in %s: in a checkout at main, python3 tools/build/visual_qa.py "
            "baseline --from-main --sha %s" % (sha[:12] or "?", baseline_dir(), sha or "<main sha>"))


def cmd_judge(shots, caller=None, require_baseline=False, sha=None, gate=False):
    sha = sha or main_sha()
    baseline = load_baseline(sha, GATE_WALK if gate else 0)
    if (require_baseline or gate) and baseline is None:
        # The gate compares against main; without main's baseline the comparison cannot run (16:28 review).
        print(missing_baseline_line(sha))
        return EXIT_ERROR
    code, line, results = judge_shots(shots, caller, baseline=baseline, composites_dir=shots, gate=gate)
    write_report(shots, line, results)
    for screen, r in results.items():
        for reason in r["reasons"]:
            print("  %s: %s" % (screen, reason))
    print(line)
    return code


def cmd_baseline_from_main(out, sha="", caller=None, records=None, shots=""):
    """Bootstrap main's baseline: capture this checkout and store the judged run whatever its verdict (main is the
    reference the gate compares to, broken items included). Refuses a checkout that is not at main; skips a sha that
    already has one. Exit 0 stored or present, 2 could not run."""
    sha = sha or main_sha()
    if shots:
        if not sha:
            print("VISUAL_QA ERROR baseline --from-main --shots needs --sha")
            return EXIT_ERROR
        code, line, results = judge_shots(shots, caller, records)
        if code == EXIT_ERROR:
            print("visual_qa baseline NOT stored for %s: %s" % (sha[:12], line))
            return EXIT_ERROR
        attach_samples(results, measure_noise(shots, BASELINE_SAMPLES, caller, records))
        store_baseline(sha, line, results)
        print("visual_qa baseline %s (from the gate run %s): %s" % (sha[:12], shots, line))
        return EXIT_PASS
    head = (_git("rev-parse", "HEAD") or "").strip()
    if not sha or head != sha:
        print("VISUAL_QA ERROR baseline --from-main: this checkout is at %s, main is %s (check out main first)"
              % (head[:12] or "?", sha[:12] or "?"))
        return EXIT_ERROR
    if os.path.exists(baseline_path(sha)):
        print("visual_qa baseline %s: already stored (%s)" % (sha[:12], baseline_path(sha)))
        return EXIT_PASS
    code = capture(out)
    if code != 0 and not all(os.path.exists(os.path.join(out, n)) for n in SCREENS.values()):
        print("VISUAL_QA ERROR capture failed (exit %d), see %s" % (code, out))
        return EXIT_ERROR
    code, line, results = judge_shots(out, caller, records, composites_dir=out)
    if code == EXIT_ERROR:
        print("visual_qa baseline NOT stored for %s: %s" % (sha[:12], line))
        return EXIT_ERROR
    attach_samples(results, measure_noise(out, BASELINE_SAMPLES, caller, records))
    store_baseline(sha, line, results)
    print("visual_qa baseline %s (from main): %s" % (sha[:12], line))
    return EXIT_PASS


def store_baseline(sha, line, results):
    os.makedirs(baseline_dir(), exist_ok=True)
    tmp = baseline_path(sha) + ".tmp"
    with open(tmp, "w", encoding="utf-8") as fh:
        json.dump({"sha": sha, "summary": line, "screens": results}, fh, indent=1)
    os.replace(tmp, baseline_path(sha))


def measure_noise(shots_dir, n, caller=None, records=None, workers=3):
    """Judge every screen in shots_dir n more times (samples 1..n, each its own recorded call) on the SAME bytes.
    Returns {screen: {"totals": [...], "range": max-min, "kinds": {kind: [count per sample]}, "broken": [[...], ...]}}."""
    from concurrent.futures import ThreadPoolExecutor
    jobs = [(screen, k) for screen in SCREENS for k in range(1, n + 1)]
    with ThreadPoolExecutor(max_workers=workers) as pool:
        done = list(pool.map(lambda j: (j, judge_image(os.path.join(shots_dir, SCREENS[j[0]]), j[0], caller, records,
                                                         sample=j[1])), jobs))
    out = {}
    if n <= 0:
        return {}
    for (screen, _k), r in done:
        o = out.setdefault(screen, {"totals": [], "broken": []})
        o["totals"].append(r["total"])
        o["broken"].append(r["broken"])
    for o in out.values():
        o["range"] = max(o["totals"]) - min(o["totals"])
        kinds = sorted({kd for b in o["broken"] for kd in kind_counts(b)})
        o["kinds"] = {kd: [kind_counts(b).get(kd, 0) for b in o["broken"]] for kd in kinds}
    return out


def attach_samples(results, noise):
    """Put measured noise samples into a judged run's per-screen results (the baseline then knows every defect kind
    any of main's runs listed)."""
    for screen, o in noise.items():
        if screen in results:
            results[screen]["samples"] = [{"total": t, "broken": b} for t, b in zip(o["totals"], o["broken"])]
    return results


def cmd_noise(shots, n, out="", baseline_sha=""):
    """Measure judge noise on shots; with baseline_sha, also store the samples in that stored baseline (its shots must
    be these shots: the stored run's shot names are checked)."""
    if baseline_sha:
        if not os.path.exists(baseline_path(baseline_sha)):
            print("VISUAL_QA ERROR no stored baseline %s" % baseline_sha[:12])
            return EXIT_ERROR
    res = measure_noise(shots, n)
    for screen, o in res.items():
        print("%s totals=%s range=%d kinds=%s" % (screen, o["totals"], o["range"],
                                                  {k: v for k, v in o["kinds"].items()}))
    worst = max(o["range"] for o in res.values())
    print("VISUAL_QA NOISE n=%d max_range=%d (shots %s)" % (n, worst, shots))
    if out:
        with open(out, "w", encoding="utf-8") as fh:
            json.dump({"shots": shots, "n": n, "model": MODEL, "max_range": worst, "screens": res}, fh, indent=1)
    if baseline_sha:
        with open(baseline_path(baseline_sha), encoding="utf-8") as fh:
            base = json.load(fh)
        attach_samples(base["screens"], res)
        store_baseline(baseline_sha, base.get("summary", ""), base["screens"])
        print("visual_qa baseline %s: %d noise samples per screen stored" % (baseline_sha[:12], n))
    return EXIT_PASS


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
            p.add_argument("--gate", action="store_true")
            p.add_argument("--main-sha", default="")
    p = sub.add_parser("judge")
    p.add_argument("--shots", required=True)
    p.add_argument("--require-baseline", action="store_true")
    p.add_argument("--main-sha", default="")
    p = sub.add_parser("frame")
    p.add_argument("image")
    p.add_argument("--screen", default="play")
    sub.add_parser("calibrate")
    p = sub.add_parser("noise")
    p.add_argument("--shots", required=True)
    p.add_argument("--n", type=int, default=5)
    p.add_argument("--out", default="")
    p.add_argument("--baseline-sha", default="")
    p = sub.add_parser("composite")
    p.add_argument("--before", required=True)
    p.add_argument("--after", required=True)
    p.add_argument("--out", required=True)
    p = sub.add_parser("baseline")
    p.add_argument("--shots", default="")
    p.add_argument("--from-main", action="store_true")
    p.add_argument("--out", default=os.path.join(ROOT, "Saved", "VisualQA", "baseline-" + time.strftime("%Y%m%d-%H%M%S")))
    p.add_argument("--sha", default="")
    args = ap.parse_args(argv)
    try:
        if args.cmd == "capture":
            return EXIT_PASS if capture(args.out) == 0 else EXIT_ERROR
        if args.cmd == "run":
            if args.gate and load_baseline(args.main_sha or main_sha(), GATE_WALK) is None:
                print(missing_baseline_line(args.main_sha or main_sha()))
                return EXIT_ERROR
            if args.require_baseline and load_baseline(args.main_sha or main_sha()) is None:
                return cmd_judge(args.out, require_baseline=True, sha=args.main_sha)
            code = capture(args.out)
            if code != 0 and not all(os.path.exists(os.path.join(args.out, n)) for n in SCREENS.values()):
                print("VISUAL_QA ERROR capture failed (exit %d), see %s" % (code, args.out))
                return EXIT_ERROR
            return cmd_judge(args.out, require_baseline=args.require_baseline, sha=args.main_sha, gate=args.gate)
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
        if args.cmd == "noise":
            return cmd_noise(args.shots, args.n, args.out, args.baseline_sha)
        if args.cmd == "composite":
            print(composite_round(rel(STUDY), args.before, args.after, args.out))
            return EXIT_PASS
        if args.cmd == "baseline" and args.from_main:
            return cmd_baseline_from_main(args.out, args.sha, shots=args.shots)
        if args.cmd == "baseline":
            if not args.shots:
                print("VISUAL_QA ERROR baseline needs --shots DIR or --from-main")
                return EXIT_ERROR
            sha = args.sha or main_sha()
            code, line, results = judge_shots(args.shots)
            if code != EXIT_PASS:
                # A failing or incomplete run never becomes main's baseline (16:45 review).
                print("visual_qa baseline NOT stored for %s: %s" % (sha[:12], line))
                return code
            attach_samples(results, measure_noise(args.shots, BASELINE_SAMPLES))
            store_baseline(sha, line, results)
            print("visual_qa baseline %s: %s" % (sha[:12], line))
            return EXIT_PASS
    except (RuntimeError, ValueError, OSError, subprocess.SubprocessError) as exc:
        print("VISUAL_QA ERROR %s" % exc)
        return EXIT_ERROR
    return EXIT_ERROR


if __name__ == "__main__":
    sys.exit(main())
