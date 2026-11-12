#!/usr/bin/env python3
"""Arena audio take fixer: trim lead silence, EQ toward the family centroid, normalise to the family loudness,
limit to -1.5 dBFS, fade the last 20 ms, stereo where the sound list wants it. Usage: arena_audio_fix.py <wav>...
Re-measures with tools/audio_style_check.py and iterates the gain. Requires ffmpeg."""
import json, os, subprocess, sys, tempfile
HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, "..", "..", ".."))
sys.path.insert(0, os.path.join(ROOT, "tools"))
import audio_style_check as asc  # noqa: E402

STYLE = json.load(open(os.path.join(ROOT, "pipeline/audio/style.json")))
STEREO = {"FailSting", "SurvivedSting", "MusicTitle"}
PEAK_DB = -1.5


def family(sid):
    for k, v in STYLE["families"].items():
        if sid in v["members"]:
            return v
    raise SystemExit("no family for " + sid)


def measure(p):
    r = subprocess.run([sys.executable, os.path.join(ROOT, "tools/audio_style_check.py"), "measure", p, "--json"],
                       capture_output=True, text=True, check=True)
    return json.loads(r.stdout)


def render(src, dst, sid, gain_db, eq):
    dur = float(subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", src],
                               capture_output=True, text=True).stdout)
    af = ["silenceremove=start_periods=1:start_threshold=-42dB:start_silence=0.002"]
    af += eq
    af += ["volume=%.2fdB" % gain_db, "alimiter=limit=%.3f:attack=1:release=20:level=disabled" % (10 ** (PEAK_DB / 20))]
    af += ["areverse", "afade=t=in:d=0.05:curve=qsin", "areverse"]
    ch = ["-ac", "2"] if sid in STEREO else ["-ac", "1"]
    subprocess.run(["ffmpeg", "-y", "-v", "error", "-i", src, "-af", ",".join(af)] + ch + ["-c:a", "pcm_s16le", dst], check=True)


SPECTRAL = ("centroid_hz", "low_share", "high_share", "crest_db")
GRID = [[]] + [
    [f for f in (("highpass=f=%d" % hp) if hp else "", ("lowpass=f=%d" % lp) if lp else "",
                 ("treble=g=%d:f=2500" % tr) if tr else "", ("bass=g=%d:f=200" % bs) if bs else "") if f]
    for hp in (0, 100, 200, 300, 500, 800) for lp in (0, 6000, 3500, 2000, 1000)
    for tr in (0, 6, 12) for bs in (0, 6)]


def violation(m, ranges):
    v = 0.0
    for k in SPECTRAL:
        if k in ranges and k in m:
            lo, hi = ranges[k]
            span = max(hi - lo, 1e-9)
            if m[k] < lo:
                v += (lo - m[k]) / span
            elif m[k] > hi:
                v += (m[k] - hi) / span
    return v


def best_eq(orig, sid, ranges):
    best = (1e9, [])
    tmp = tempfile.mktemp(suffix=".wav")
    for eq in GRID:
        render(orig, tmp, sid, 0.0, eq)
        v = violation(measure(tmp), ranges)
        if v < best[0] - 1e-9:
            best = (v, eq)
        if v == 0:
            break
    os.remove(tmp)
    return best[1]


def fix(path, eq):
    sid = os.path.basename(path).split("_")[1]
    fam = family(sid)
    lo, hi = fam["ranges"]["lufs"]
    target = lo + (hi - lo) * 0.45
    os.makedirs("/tmp/arena_orig", exist_ok=True)
    orig = os.path.join("/tmp/arena_orig", os.path.basename(path))
    if not os.path.exists(orig):
        os.replace(path, orig)
    if eq == ["auto"]:
        eq = best_eq(orig, sid, fam["ranges"])
        print("eq", eq)
    gain = 0.0
    tmp = tempfile.mktemp(suffix=".wav")
    for _ in range(6):
        render(orig, tmp, sid, gain, eq)
        m = measure(tmp)
        if abs(m["lufs"] - target) < 1.0:
            break
        gain += target - m["lufs"]
    os.replace(tmp, path)
    print(path, {k: round(v, 1) for k, v in m.items()})


def main():
    eq = []
    args = sys.argv[1:]
    if args and args[0].startswith("--rms="):
        t = dict(kv.split(":") for kv in args[0][6:].split(","))
        rms_stage(args[1:], {k: float(v) for k, v in t.items()})
        return
    if args and args[0] == "--auto":
        eq = ["auto"]
        args = args[1:]
    elif args and args[0].startswith("--eq="):
        eq = [a for a in args[0][5:].split(";") if a]
        args = args[1:]
    for p in args:
        fix(p, eq)


def rms_stage(paths, targets):
    """Second pass in place: trim, 80 ms end fade, gain each take to its group's common RMS (audio_check groups)."""
    import re
    scan = subprocess.run([sys.executable, os.path.join(ROOT, "tools/audio_check.py"), "--scan", "Audio/Source"],
                          capture_output=True, text=True, cwd=ROOT).stdout
    for p in paths:
        m = re.search(re.escape(p) + r": peak [-\d.inf]+ dBFS, rms ([-\d.]+) dB \((\w+)\)", scan)
        if not m:
            continue
        rms, group = float(m.group(1)), m.group(2)
        gain = targets.get(group, rms) - rms
        sid = os.path.basename(p).split("_")[1]
        tmp = tempfile.mktemp(suffix=".wav")
        af = ["silenceremove=start_periods=1:start_threshold=-35dB:start_silence=0.002", "volume=%.2fdB" % gain,
              "alimiter=limit=%.3f:attack=1:release=20:level=disabled" % (10 ** (PEAK_DB / 20)),
              "areverse", "afade=t=in:d=0.08:curve=qsin", "areverse"]
        subprocess.run(["ffmpeg", "-y", "-v", "error", "-i", p, "-af", ",".join(af), "-ac", "2" if sid in STEREO else "1",
                        "-c:a", "pcm_s16le", tmp], check=True)
        os.replace(tmp, p)
        print("rms", p, group, "gain %.1f" % gain)


if __name__ == "__main__":
    main()
