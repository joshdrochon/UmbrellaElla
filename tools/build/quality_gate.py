#!/usr/bin/env python3
"""Quality bars for a merge (Josh, Nov 12): art, audio, UI and story. Called by tools/build/gate.sh.

  quality_gate.py baseline OUT          run the blocking checks on the current tree (main) and save their FAIL lines
  quality_gate.py check BASE OUT        after the merge: compare with the baseline, judge the files changed since BASE

Art and audio are "replace a placeholder only on pass": a changed shipped image (Art/ outside Art/Source/) or art asset
under Content/*/Art must have its art_loop pass record (tools/art_loop.py record_problems: calibrated blind panel,
art_check, screen_check, art_ref_check on these bytes), unless it is a tracked placeholder (`_PH` in the file name).
A changed WAV under Audio/Source must pass tools/audio_check.py --scan and tools/audio_style_check.py, unless it is a
tracked placeholder take (provenance origin `placeholder: <reason>`, audio_check --placeholders). Anything below the
bar fails the merge with a message to keep it a tracked placeholder; gameplay never waits for it.
UI (tools/ui_check.py ci) and story (tools/story_check.py) are blocking: the merge may not add a FAIL line main lacks.
Exit 0 = pass, 1 = fail.
"""
import os, re, subprocess, sys
ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
sys.path.insert(0, os.path.join(ROOT, "tools"))
BLOCKING = {"ui_check": ["tools/ui_check.py", "ci"], "story_check": ["tools/story_check.py"],
            "bake_defaults": ["tools/bake_preset.py", "defaults"]}


def run(args):
    p = subprocess.run([sys.executable] + args, cwd=ROOT, capture_output=True, text=True)
    return p.returncode, (p.stdout + p.stderr).splitlines()


def fails(lines):
    # Line numbers are dropped so a fail that only moved (an include added above it) is not "new".
    return {re.sub(r":\d+(:\d+)?\b", "", l.strip()) for l in lines if re.match(r"\s*(FAIL|\[FAIL\]|ERROR)", l)}


def blocking_lines():
    out = {}
    for name, args in BLOCKING.items():
        _, lines = run(args)
        out[name] = fails(lines)
    return out


def main():
    if len(sys.argv) >= 3 and sys.argv[1] == "baseline":
        with open(sys.argv[2], "w") as fh:
            for name, ls in blocking_lines().items():
                for l in sorted(ls):
                    fh.write(f"{name}\t{l}\n")
        return 0
    if len(sys.argv) < 4 or sys.argv[1] != "check":
        print(__doc__); return 2
    base, basefile = sys.argv[2], sys.argv[3]
    before = {}
    if os.path.exists(basefile):
        for row in open(basefile):
            n, _, l = row.rstrip("\n").partition("\t"); before.setdefault(n, set()).add(l)
    problems = []
    for name, now in blocking_lines().items():
        new = sorted(now - before.get(name, set()))
        problems += [f"{name}: new {l}" for l in new]
        print(f"quality {name}: {'PASS' if not new else 'FAIL'} (new fail lines {len(new)}, already on main {len(now & before.get(name, set()))})")
    changed = subprocess.run(["git", "diff", "--name-only", f"{base}...HEAD"], cwd=ROOT, capture_output=True,
                             text=True).stdout.split()
    changed = [p for p in changed if os.path.isfile(os.path.join(ROOT, p))]
    # Art: ship only on pass.
    import art_loop, check_pr
    rh = check_pr.current_refs_hash(ROOT)
    art = [p for p in changed if (art_loop.shipped(p) or check_pr.ships_art(p)) and "_PH" not in os.path.basename(p)]
    bad_art = []
    for p in art:
        if art_loop.shipped(p):
            probs = art_loop.record_problems(ROOT, p, rh)
        else:  # an imported asset: some shipped image in the merge must carry a pass record
            probs = [] if any(art_loop.shipped(i) and not art_loop.record_problems(ROOT, i, rh) for i in changed) else ["no passing source image"]
        if probs:
            bad_art.append(p); problems.append(f"art below the bar (keep it a tracked _PH placeholder): {p}: {probs[0]}")
    print(f"quality art: {'PASS' if not bad_art else 'FAIL'} (shipped art changed {len(art)}, below bar {len(bad_art)})")
    # Audio: ship only on pass.
    wavs = [p for p in changed if p.startswith("Audio/Source/") and p.lower().endswith(".wav")]
    bad_audio = []
    if wavs:
        _, ph = run(["tools/audio_check.py", "--placeholders"])
        placeholders = {os.path.basename(m) for l in ph for m in re.findall(r"SW_\w+\.wav", l)}
        _, scan = run(["tools/audio_check.py", "--scan", "Audio/Source"])
        ids = sorted({os.path.basename(p).split("_")[1] for p in wavs if os.path.basename(p).count("_") >= 2})
        _, style = run(["tools/audio_style_check.py", "check", "Audio/Source", "--ids", ",".join(ids)])
        failed = " ".join(l for l in scan + style if l.startswith("FAIL"))
        for p in wavs:
            b = os.path.basename(p)
            if b in failed and b not in placeholders:
                bad_audio.append(p)
                why = next(l for l in scan + style if l.startswith("FAIL") and b in l)
                problems.append(f"audio below the bar (fix it or keep it a tracked placeholder take): {why}")
    print(f"quality audio: {'PASS' if not bad_audio else 'FAIL'} (takes changed {len(wavs)}, below bar {len(bad_audio)})")
    for p in problems:
        print("  " + p)
    print(f"quality_gate: {'PASS' if not problems else 'FAIL'} problems={len(problems)}")
    return 0 if not problems else 1


if __name__ == "__main__":
    sys.exit(main())
