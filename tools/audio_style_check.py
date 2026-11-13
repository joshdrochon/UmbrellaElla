#!/usr/bin/env python3
"""Audio quality bar, measured. Stdlib only. Target: pipeline/audio/style.json (prose: pipeline/audio/style-target.md).

Every take SW_<Id>_<NN>.wav belongs to the style family that lists <Id> in style.json. Each family sets ranges for the
numbers below; a take outside any range of its family fails. These numbers catch a take that is off the bar in a way
anyone can measure (too dry, too bright, too soft, no punch, wrong tempo). They never prove a take is good: that is the
critic's verdict (tools/audio_loop.py). Both must pass.

Measured (style.json "metrics" has the exact definitions):
  lufs         integrated loudness, BS.1770 K-weighting, 400 ms gated blocks (ungated under 0.4 s)
  centroid_hz  spectral centroid (brightness);  low_share / high_share: energy below 250 Hz / above 4 kHz
  crest_db     peak to RMS (punch);  attack_ms: 10-90% rise at the onset (transient sharpness; one-shots)
  decay_s      reverb tail: 2 x the -5 to -35 dB fall of the envelope after its peak (an RT60 estimate; one-shots)
  seconds      length;  tempo_bpm and lra_db (loudness range) for music stems
Music stems (style.json "music"): every stem's tempo is inside the shared range, the stems agree within
stem_tempo_tol_bpm and their lengths within stem_length_tol_s, because they are layers that start on the bar.

Usage:
  audio_style_check.py check DIR [--ids A,B] [--fail-lfs-pointer]   every take under DIR (Audio/Source); prints one
                       PASS/FAIL line per take and `audio_style check: PASS files=<n> commit=<sha> dirty=<yes|no>`
  audio_style_check.py measure WAV [--json]                          the numbers for one file
  audio_style_check.py prompt ID [--extra "..."]                     the generation prompt for sound ID (assetgen uses it)
Exit 0 = pass, 1 = fail, 2 = usage or input error.
"""
import argparse
import cmath
import json
import math
import os
import re
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, HERE)
import audio_check  # noqa: E402

DEFAULT_STYLE = os.path.join(ROOT, "pipeline", "audio", "style.json")
NAME = re.compile(r"^SW_([A-Z][A-Za-z0-9]*)_(\d{2})(_PH)?\.wav$")
ONESHOT_ONLY = ("attack_ms", "decay_s")
STEM_ONLY = ("tempo_bpm", "lra_db")


def load_style(path=DEFAULT_STYLE):
    with open(path, encoding="utf-8") as f:
        return json.load(f)


# ---------------------------------------------------------------- DSP (pure Python)

def biquad(x, b, a):
    b0, b1, b2 = (v / a[0] for v in b)
    a1, a2 = a[1] / a[0], a[2] / a[0]
    y, x1, x2, y1, y2 = [0.0] * len(x), 0.0, 0.0, 0.0, 0.0
    for i, v in enumerate(x):
        o = b0 * v + b1 * x1 + b2 * x2 - a1 * y1 - a2 * y2
        x2, x1, y2, y1 = x1, v, y1, o
        y[i] = o
    return y


def k_weight(x, rate):
    """ITU-R BS.1770 K-weighting: the high shelf, then the high pass, designed for any sample rate (at 48 kHz these
    are the standard's own coefficients)."""
    g, q, fc = 3.99984385397, 0.7071752369554193, 1681.9744509555319
    k = math.tan(math.pi * fc / rate)
    vh = 10 ** (g / 20)
    vb = vh ** 0.4996667741545416
    a0 = 1 + k / q + k * k
    shelf = ([(vh + vb * k / q + k * k) / a0, 2 * (k * k - vh) / a0, (vh - vb * k / q + k * k) / a0],
             [1.0, 2 * (k * k - 1) / a0, (1 - k / q + k * k) / a0])
    q, fc = 0.5003270373238773, 38.13547087602444
    k = math.tan(math.pi * fc / rate)
    a0 = 1 + k / q + k * k
    hp = ([1.0, -2.0, 1.0], [1.0, 2 * (k * k - 1) / a0, (1 - k / q + k * k) / a0])
    return biquad(biquad(x, *shelf), *hp)


def _loud(ms):
    return -0.691 + 10 * math.log10(ms) if ms > 0 else -math.inf


def block_loudness(kw, rate, block_s, step_s):
    n, bl, st = len(kw[0]), int(block_s * rate), max(1, int(step_s * rate))
    sq = [[v * v for v in c] for c in kw]
    cums = []
    for c in sq:
        acc, cum = 0.0, [0.0]
        for v in c:
            acc += v
            cum.append(acc)
        cums.append(cum)
    out = []
    for s in range(0, n - bl + 1, st):
        out.append(sum((cum[s + bl] - cum[s]) / bl for cum in cums))
    return out


def lufs(chans, rate):
    kw = [k_weight(c, rate) for c in chans]
    n = len(kw[0])
    if n < int(0.4 * rate):
        return _loud(sum(sum(v * v for v in c) / max(n, 1) for c in kw))
    blocks = [b for b in block_loudness(kw, rate, 0.4, 0.1) if _loud(b) > -70]
    if not blocks:
        return -math.inf
    rel = _loud(sum(blocks) / len(blocks)) - 10
    gated = [b for b in blocks if _loud(b) > rel]
    return _loud(sum(gated) / len(gated)) if gated else -math.inf


def lra(chans, rate):
    if len(chans[0]) < 3 * rate:
        return None
    kw = [k_weight(c, rate) for c in chans]
    st = [_loud(b) for b in block_loudness(kw, rate, 3.0, 1.0)]
    st = [v for v in st if v > -70]
    if not st:
        return None
    mean = 10 * math.log10(sum(10 ** (v / 10) for v in st) / len(st))
    st = sorted(v for v in st if v > mean - 20)
    if len(st) < 2:
        return 0.0
    pick = lambda p: st[min(len(st) - 1, int(round(p * (len(st) - 1))))]  # noqa: E731
    return pick(0.95) - pick(0.10)


def fft(a):
    n = len(a)
    if n == 1:
        return a
    ev, od = fft(a[0::2]), fft(a[1::2])
    tw = [cmath.exp(-2j * math.pi * k / n) * od[k] for k in range(n // 2)]
    return [ev[k] + tw[k] for k in range(n // 2)] + [ev[k] - tw[k] for k in range(n // 2)]


def spectrum(mono, rate, frames=24):
    """Mean power spectrum over up to `frames` Hann windows across the file: (freqs, power)."""
    n = 1
    while n * 2 <= min(4096, len(mono)):
        n *= 2
    if n < 64:
        return [], []
    hann = [0.5 - 0.5 * math.cos(2 * math.pi * i / (n - 1)) for i in range(n)]
    starts = sorted({int(i * (len(mono) - n) / max(frames - 1, 1)) for i in range(frames)})
    power = [0.0] * (n // 2)
    for s in starts:
        spec = fft([mono[s + i] * hann[i] for i in range(n)])
        for k in range(1, n // 2):
            power[k] += abs(spec[k]) ** 2
    return [k * rate / n for k in range(n // 2)], power


def envelope(mono, rate, win_ms, rms=True):
    w = max(1, int(rate * win_ms / 1000))
    out = []
    for s in range(0, len(mono) - w + 1, w):
        seg = mono[s:s + w]
        out.append(math.sqrt(sum(v * v for v in seg) / w) if rms else max(abs(v) for v in seg))
    return out


def attack_ms(mono, rate):
    env = envelope(mono, rate, 1, rms=False)
    if not env or max(env) <= 0:
        return None
    top = max(env)
    lo = next(i for i, v in enumerate(env) if v >= 0.1 * top)
    hi = next(i for i, v in enumerate(env) if v >= 0.9 * top)
    return float(hi - lo)


def decay_s(mono, rate):
    env = [audio_check.dbfs(v) for v in envelope(mono, rate, 10)]
    if not env:
        return None
    p = max(range(len(env)), key=lambda i: env[i])
    top = env[p]
    t1 = next((i for i in range(p, len(env)) if env[i] <= top - 5), None)
    if t1 is None:
        return math.inf
    t2 = next((i for i in range(t1, len(env)) if env[i] <= top - 35), None)
    if t2 is not None:
        return 2 * (t2 - t1) * 0.010
    drop = (top - 5) - env[-1]
    return math.inf if drop <= 0.5 else 2 * (len(env) - 1 - t1) * 0.010 * 30 / drop


def tempo_bpm(mono, rate, lo=50.0, hi=200.0):
    hop = max(1, int(rate * 0.005))
    eng = [sum(v * v for v in mono[s:s + hop]) for s in range(0, len(mono) - hop + 1, hop)]
    loge = [math.log10(e + 1e-10) for e in eng]
    onset = [max(0.0, loge[i] - loge[i - 1]) for i in range(1, len(loge))]
    if len(onset) < 4:
        return None
    m = sum(onset) / len(onset)
    onset = [v - m for v in onset]
    fps = rate / hop
    lags = range(max(1, int(fps * 60 / hi)), min(len(onset) - 1, int(fps * 60 / lo)) + 1)
    if not lags:
        return None
    ac = {L: sum(onset[i] * onset[i + L] for i in range(len(onset) - L)) / (len(onset) - L) for L in lags}
    best = max(ac, key=ac.get)
    if ac[best] <= 0:
        return None
    lag = float(best)
    if best - 1 in ac and best + 1 in ac:
        y0, y1, y2 = ac[best - 1], ac[best], ac[best + 1]
        den = y0 - 2 * y1 + y2
        if den:
            lag += 0.5 * (y0 - y2) / den
    return 60.0 * fps / lag


def measure_chans(chans, rate, stem=False):
    n = len(chans[0]) if chans else 0
    mono = [sum(c[i] for c in chans) / len(chans) for i in range(n)] if len(chans) > 1 else list(chans[0])
    peak = max((abs(v) for c in chans for v in c), default=0.0)
    out = {"seconds": n / rate if rate else 0.0}
    if peak <= 0:
        return dict(out, silent=True)
    gate = peak * 10 ** (-40 / 20)
    first = next(i for i, v in enumerate(mono) if abs(v) >= gate)
    last = n - 1 - next(i for i, v in enumerate(reversed(mono)) if abs(v) >= gate)
    act = mono[first:last + 1]
    rms = math.sqrt(sum(v * v for c in chans for v in c[first:last + 1]) / (len(chans) * len(act)))
    out["crest_db"] = audio_check.dbfs(peak) - audio_check.dbfs(rms)
    out["lufs"] = lufs(chans, rate)
    freqs, power = spectrum(act, rate)
    tot = sum(power)
    if tot > 0:
        out["centroid_hz"] = sum(f * p for f, p in zip(freqs, power)) / tot
        out["low_share"] = sum(p for f, p in zip(freqs, power) if f < 250) / tot
        out["high_share"] = sum(p for f, p in zip(freqs, power) if f > 4000) / tot
    out["attack_ms"] = attack_ms(mono, rate)
    out["decay_s"] = decay_s(mono, rate)
    if stem:
        out["tempo_bpm"] = tempo_bpm(mono, rate)
        out["lra_db"] = lra(chans, rate)
    return out


def measure_file(path, stem=False):
    info, chans = audio_check.read_wav(path)
    return measure_chans(chans, info["rate"], stem)


def spectrogram_grid(mono, rate, cols=240, rows=120, fmin=40.0, fmax=16000.0):
    """dB grid[col][row] (row 0 = lowest band). Rows whose lower edge is under 500 Hz use a 4096-sample window
    (11.7 Hz bins at 48 kHz), the rest 1024; every window is centred on its column; bins start at 1 (no DC)."""
    fmax = min(fmax, rate / 2 - 1)
    edges = [fmin * (fmax / fmin) ** (r / rows) for r in range(rows + 1)]
    n = len(mono)
    low_rows = sum(1 for r in range(rows) if edges[r] < 500.0)
    sizes = [1024] + ([4096] if low_rows else [])
    hanns = {z: [0.5 - 0.5 * math.cos(2 * math.pi * i / (z - 1)) for i in range(z)] for z in sizes}
    grid = []
    for c in range(cols):
        centre = c * (n - 1) / max(cols - 1, 1)
        mags = {}
        for z in sizes:
            s = int(round(centre - z / 2))
            seg = [mono[s + i] if 0 <= s + i < n else 0.0 for i in range(z)]
            h = hanns[z]
            spec = fft([seg[i] * h[i] for i in range(z)])
            mags[z] = [abs(v) ** 2 for v in spec[:z // 2]]
        col = []
        for r in range(rows):
            z = 4096 if edges[r] < 500.0 else 1024
            lo = max(1, int(edges[r] * z / rate))
            hi = max(lo + 1, int(edges[r + 1] * z / rate))
            p = sum(mags[z][lo:hi]) / max(hi - lo, 1)
            col.append(10 * math.log10(p + 1e-12))
        grid.append(col)
    return grid


def spectrogram_png(wav, out, cols=240, rows=120, fmin=40.0, fmax=16000.0):
    """A log-frequency spectrogram (time left to right, pitch bottom to top, dark = loud) for the critic packet."""
    import png
    info, chans = audio_check.read_wav(wav)
    rate, n = info["rate"], len(chans[0])
    mono = [sum(c[i] for c in chans) / len(chans) for i in range(n)]
    grid = spectrogram_grid(mono, rate, cols, rows, fmin, fmax)
    top = max(max(c) for c in grid)
    pix = []
    for r in reversed(range(rows)):
        line = []
        for c in range(cols):
            v = max(0.0, min(1.0, (grid[c][r] - (top - 80)) / 80))
            g = int(235 - 225 * v)
            line.append((g, g, g, 255))
        pix.append(line)
    png.write_png(out, cols, rows, pix)


# ---------------------------------------------------------------- target

def family_of(sid, style):
    fams = audio_check.style_families(style).get(sid) or []
    return fams[0] if len(fams) == 1 else None


def applies(metric, kind, stem):
    if metric in ONESHOT_ONLY:
        return kind == "oneshot"
    if metric in STEM_ONLY:
        return stem
    return True


def compare(m, family, style, kind, stem=False):
    """(problems, distance): each metric outside its range, and how far outside in range widths (0 = inside)."""
    out, dist = [], 0.0
    if m.get("silent"):
        return ["silent file"], 99.0
    for metric, (lo, hi) in sorted(style["families"][family].get("ranges", {}).items()):
        if not applies(metric, kind, stem):
            continue
        v = m.get(metric)
        if v is None or (isinstance(v, float) and math.isnan(v)):
            out.append(f"{metric} could not be measured (want {lo}..{hi})")
            dist += 1.0
            continue
        if v < lo or v > hi:
            w = max(hi - lo, 1e-9)
            d = (lo - v) / w if v < lo else (v - hi) / w
            dist += min(d, 10.0)
            out.append(f"{metric}={fmt(v)} (want {lo}..{hi})")
    if stem:
        lo, hi = style["music"]["tempo_bpm"]
        t = m.get("tempo_bpm")
        if t is None or not lo <= t <= hi:
            out.append(f"tempo_bpm={fmt(t)} (want {lo}..{hi}, shared by every stem)")
            dist += 1.0
    return out, dist


def fmt(v):
    if v is None:
        return "none"
    if isinstance(v, float) and math.isinf(v):
        return "inf"
    return f"{v:.3g}" if abs(v) < 10 else f"{v:.1f}"


def summary(m, keys):
    return " ".join(f"{k}={fmt(m.get(k))}" for k in keys if k in m)


def git_head(root):
    try:
        sha = subprocess.run(["git", "-C", root, "rev-parse", "HEAD"], capture_output=True, text=True,
                             check=True).stdout.strip()
        dirty = subprocess.run(["git", "-C", root, "status", "--porcelain", "--", "Audio", "pipeline/audio"],
                               capture_output=True, text=True).stdout.strip()
        return sha, "yes" if dirty else "no"
    except (OSError, subprocess.CalledProcessError):
        return "none", "yes"


def takes(folder, ids=None):
    """{id: [paths]} of SW_<Id>_<NN>.wav under folder."""
    out = {}
    for dp, _, fns in os.walk(folder):
        for fn in sorted(fns):
            m = NAME.match(fn)
            if m and (not ids or m.group(1) in ids):
                out.setdefault(m.group(1), []).append(os.path.join(dp, fn))
    return out


def is_pointer(path):
    with open(path, "rb") as f:
        return f.read(len(audio_check.LFS_POINTER)) == audio_check.LFS_POINTER


def check_takes(by_id, style, rows, fail_lfs_pointer=False):
    """(lines, problems, results): one line per take plus the stem agreement checks."""
    kinds = {r["id"]: r["kind"] for r in rows}
    stems = set(style.get("music", {}).get("stems") or [])
    lines, probs, results, stem_m = [], [], {}, {}
    for sid in sorted(by_id):
        fam = family_of(sid, style)
        for path in by_id[sid]:
            name = os.path.basename(path)
            if fam is None:
                probs.append(f"{name}: {sid} has no single style family in style.json")
                continue
            if is_pointer(path):
                (probs if fail_lfs_pointer else lines).append(f"SKIP {name}: Git LFS pointer (run git lfs pull)")
                continue
            try:
                m = measure_file(path, stem=sid in stems)
            except ValueError as e:
                probs.append(f"{name}: {e}")
                continue
            p, d = compare(m, fam, style, kinds.get(sid, "oneshot"), sid in stems)
            results[path] = {"id": sid, "family": fam, "metrics": m, "problems": p, "distance": d}
            if sid in stems:
                stem_m[sid] = m
            keys = [k for k in sorted(style["families"][fam].get("ranges", {}))
                    if applies(k, kinds.get(sid, "oneshot"), sid in stems)]
            if p:
                probs.append(f"{name} family={fam}: " + "; ".join(p))
                lines.append(f"FAIL {name} family={fam} " + summary(m, keys))
            else:
                lines.append(f"PASS {name} family={fam} " + summary(m, keys))
    mu = style.get("music", {})
    tempos = {s: m.get("tempo_bpm") for s, m in stem_m.items() if m.get("tempo_bpm")}
    if len(tempos) > 1 and max(tempos.values()) - min(tempos.values()) > mu.get("stem_tempo_tol_bpm", 1.5):
        probs.append(f"stems disagree on tempo {({k: round(v, 1) for k, v in tempos.items()})}: layers share one tempo")
    lens = {s: m["seconds"] for s, m in stem_m.items()}
    if len(lens) > 1 and max(lens.values()) - min(lens.values()) > mu.get("stem_length_tol_s", 0.02):
        probs.append(f"stems differ in length {({k: round(v, 3) for k, v in lens.items()})}: layers share one length")
    return lines, probs, results


def build_prompt(sid, style, rows, extra=""):
    """The generation prompt for one sound id, from its family and its sound-list row. Raises ValueError."""
    fam = family_of(sid, style)
    row = next((r for r in rows if r["id"] == sid), None)
    if row is None or fam is None:
        raise ValueError(f"{sid}: not a sound-list row with one style family in style.json")
    f, brand = style["families"][fam], style["brand"]
    loop = " Seamless loop, no fade in or out." if row["kind"] == "loop" else " One shot, starts at once."
    base = (f.get("prompts") or {}).get(sid) or f["prompt"]   # a member's own sound, else the family's
    text = f"{base}. Plays when: {row['event']}.{loop} {brand['prompt_suffix']}"
    if extra.strip():
        text += f" Revision: {extra.strip()}"
    banned_problem(text, style)
    return text, f.get("seconds")


def banned_problem(text, style):
    low = text.lower()
    for t in style["brand"].get("prompt_banned") or []:
        if re.search(r"(?<![a-z])" + re.escape(t.lower()) + r"(?![a-z])", low):
            raise ValueError(f"prompt names {t!r}: prompts describe the bar, never a game, studio, composer or 'in the "
                             "style of' (provenance rule: no copyrighted IP in prompts)")


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--style", default=DEFAULT_STYLE)
    ap.add_argument("--list-file", default=audio_check.DEFAULT_LIST)
    sub = ap.add_subparsers(dest="cmd", required=True)
    p = sub.add_parser("check")
    p.add_argument("dir")
    p.add_argument("--ids")
    p.add_argument("--fail-lfs-pointer", action="store_true")
    p.add_argument("--root", default=ROOT)
    p = sub.add_parser("measure")
    p.add_argument("wav")
    p.add_argument("--stem", action="store_true")
    p.add_argument("--json", action="store_true")
    p = sub.add_parser("prompt")
    p.add_argument("id")
    p.add_argument("--extra", default="")
    a = ap.parse_args(argv)
    try:
        style, rows = load_style(a.style), audio_check.load_list(a.list_file)
    except (OSError, ValueError) as e:
        print(f"audio_style_check: cannot read style or sound list: {e}", file=sys.stderr)
        return 2
    if a.cmd == "measure":
        try:
            m = measure_file(a.wav, a.stem)
        except (OSError, ValueError) as e:
            print(f"audio_style_check: {e}", file=sys.stderr)
            return 2
        print(json.dumps(m, indent=1) if a.json else summary(m, sorted(m)))
        return 0
    if a.cmd == "prompt":
        try:
            print(build_prompt(a.id, style, rows, a.extra)[0])
        except ValueError as e:
            print(f"FAIL {e}")
            return 1
        return 0
    if not os.path.isdir(a.dir):
        print(f"note SKIP {a.dir}: folder does not exist yet")
        print("audio_style check: PASS files=0 (no folder)")
        return 0
    ids = set(a.ids.split(",")) if a.ids else None
    by_id = takes(a.dir, ids)
    lines, probs, results = check_takes(by_id, style, rows, a.fail_lfs_pointer)
    for ln in lines:
        print(ln)
    for p in probs:
        print(f"FAIL {p}")
    sha, dirty = git_head(a.root)
    print(f"audio_style check: {'FAIL' if probs else 'PASS'} files={len(results)} commit={sha[:12]} dirty={dirty}")
    return 1 if probs else 0


if __name__ == "__main__":
    sys.exit(main())
