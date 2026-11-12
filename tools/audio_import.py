#!/usr/bin/env python3
"""Supplied audio: a teammate's prepared sound files go into the game through the same bar as generated ones.
Stdlib only (ffmpeg only to read a file that is not WAV). Rule: pipeline/audio/style-target.md section 7.

  1. The supplier drops files into Audio/Import/ (any name; WAV, or MP3/OGG/FLAC/AIFF with ffmpeg installed).
  2. `match` maps each file to a sound-list row by name (WandBolt.wav, SW_WandBolt_00.wav, wand_bolt_2.wav). Files it
     cannot place are listed with every row's event and style character, and a best guess; the agent decides and
     writes `<file>,<Id>` lines to Audio/Import/map.csv (`#` lines are comments).
  3. `apply` processes each mapped file into Audio/Source/<Id>/SW_<Id>_<NN>.wav: the row's channels, 44.1/48 kHz,
     16-bit; one-shots trimmed to start at once and end in silence, loops cross-faded at the wrap; reverb added when
     the tail is shorter than the family's decay_s range; loudness set to the middle of the family's LUFS range
     (never above -1 dBFS peak); extra takes made by small pitch and level changes when the row needs more takes
     than were supplied. Each output gets a provenance row: origin `supplied`, the supplier as author, the source
     file, the steps. A file made before the jam start is declared, not blocked: a row in
     pipeline/submission/credits.md "Sourced assets" and in docs/pre-jam-declaration.md (Official Rules 7(h)).
  4. The takes then go through the same loop as every sound: tools/audio_style_check.py and tools/audio_loop.py
     (critic vs the style target). The agent fixes a failing take by re-running apply with other options
     (--reverb, --lufs) or edits; it generates (tools/assetgen.py) only for a row with no supplied file
     (`todo` lists them; assetgen refuses a row that has a supplied take).

Usage:
  audio_import.py match [--in Audio/Import]
  audio_import.py apply --author NAME --made YYYY-MM-DD --licence TEXT [--in Audio/Import] [--ids A,B]
                        [--reverb auto|off|<seconds>] [--lufs auto|<value>]
  audio_import.py todo                                  rows with no take and no supplied file (to generate)
Exit 0 = ok, 1 = a file failed or is unmatched, 2 = usage or input error.
"""
import argparse
import csv
import datetime as dt
import math
import os
import random
import re
import shutil
import struct
import subprocess
import sys
import tempfile
import wave

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, HERE)
import audio_check  # noqa: E402
import audio_style_check as asc  # noqa: E402

AUDIO_EXT = (".wav", ".mp3", ".ogg", ".flac", ".aif", ".aiff")
PROV_COLS = ["asset_path", "author", "origin", "tool", "model_version", "prompt", "seed", "input_images", "date",
             "licence", "attribution"]
SUPPLIED = "supplied"
TOOL = "Supplied file (tools/audio_import.py)"
CREDITS = "pipeline/submission/credits.md"
DECLARATION = "docs/pre-jam-declaration.md"
JAM_START = dt.datetime.fromisoformat("2026-11-11T21:00-08:00")   # same as tools/submission_check.py JAM_START


def norm(s):
    s = re.sub(r"\.[A-Za-z0-9]+$", "", os.path.basename(s))
    s = re.sub(r"(?i)^sw_", "", s)
    s = re.sub(r"(?i)([_ -]?(v\d+|take\d*|final|new|\d+))+$", "", s)
    return re.sub(r"[^a-z0-9]", "", s.lower())


def words(s):
    return {w for w in re.findall(r"[a-z]+", re.sub(r"([a-z])([A-Z])", r"\1 \2", s).lower()) if len(w) > 2}


def ctx(root):
    style = asc.load_style(os.path.join(root, "pipeline", "audio", "style.json"))
    rows = audio_check.load_list(os.path.join(root, "pipeline", "audio", "sound-list.csv"))
    return style, [r for r in rows if r["tier"] != "cut"]


def inbox(folder):
    if not os.path.isdir(folder):
        return []
    return sorted(f for f in os.listdir(folder) if f.lower().endswith(AUDIO_EXT))


def read_map(folder):
    p = os.path.join(folder, "map.csv")
    out = {}
    if os.path.isfile(p):
        with open(p, encoding="utf-8") as fh:
            for ln in fh:
                ln = ln.strip()
                if ln and not ln.startswith("#") and "," in ln:
                    f, i = (x.strip() for x in ln.split(",", 1))
                    out[f] = i
    return out


def matches(folder, rows):
    """({file: id}, [unmatched files]) from map.csv first, then by name."""
    ids = {r["id"] for r in rows}
    by_norm = {r["id"].lower(): r["id"] for r in rows}
    mp = read_map(folder)
    got, left = {}, []
    for f in inbox(folder):
        sid = mp.get(f) or by_norm.get(norm(f))
        if sid in ids:
            got[f] = sid
        else:
            left.append(f)
    return got, left


def guess(f, rows, style):
    fam_of = audio_check.style_families(style)
    w = words(os.path.splitext(f)[0].replace("_", " "))
    best = max(rows, key=lambda r: len(w & (words(r["id"]) | words(r["event"]) |
                                            words(" ".join(fam_of.get(r["id"], []))))))
    return best["id"]


def cmd_match(a, root):
    style, rows = ctx(root)
    folder = os.path.join(root, a.inp)
    got, left = matches(folder, rows)
    for f, sid in sorted(got.items()):
        print(f"MATCH {f} -> {sid}")
    if left:
        fam_of = audio_check.style_families(style)
        print(f"UNMATCHED {len(left)} file(s): match each by what it sounds like, then add `<file>,<Id>` lines to "
              f"{os.path.join(a.inp, 'map.csv')}")
        for f in left:
            print(f"  {f}  (best guess by name: {guess(f, rows, style)})")
        print("Rows (id | family | plays when | target character):")
        for r in rows:
            fam = (fam_of.get(r["id"]) or ["?"])[0]
            ch = style["families"].get(fam, {}).get("character", "")[:110]
            print(f"  {r['id']} | {fam} | {r['event']} | {ch}")
    print(f"audio_import match: {'PASS' if not left else 'FAIL'} matched={len(got)} unmatched={len(left)}")
    return 1 if left else 0


# ---------------------------------------------------------------- processing

def load_any(path):
    if path.lower().endswith(".wav"):
        try:
            info, ch = audio_check.read_wav(path)
            return info["rate"], ch
        except ValueError:
            pass
    ff = shutil.which(os.environ.get("FFMPEG") or "ffmpeg")
    if not ff:
        raise ValueError("not a 16/24-bit PCM WAV and ffmpeg is not installed to convert it")
    tmp = tempfile.mkdtemp()
    try:
        out = os.path.join(tmp, "in.wav")
        subprocess.run([ff, "-y", "-loglevel", "error", "-i", path, "-ar", "48000", "-c:a", "pcm_s16le", out],
                       check=True, capture_output=True)
        info, ch = audio_check.read_wav(out)
        return info["rate"], ch
    except subprocess.CalledProcessError as e:
        raise ValueError(f"ffmpeg could not read it ({(e.stderr or b'').decode()[-120:]})")
    finally:
        shutil.rmtree(tmp, True)


def resample(x, src, dst):
    if src == dst or not x:
        return list(x)
    n = int(len(x) * dst / src)
    r = src / dst
    out = []
    for i in range(n):
        p = i * r
        k = int(p)
        f = p - k
        a = x[k]
        b = x[k + 1] if k + 1 < len(x) else a
        out.append(a + (b - a) * f)
    return out


def to_channels(ch, n):
    if len(ch) == n:
        return ch
    if n == 1:
        return [[sum(c[i] for c in ch) / len(ch) for i in range(len(ch[0]))]]
    return [list(ch[0]) for _ in range(n)]


def trim_oneshot(ch, rate):
    peak = max(abs(v) for c in ch for v in c) or 1.0
    gate = peak * 10 ** (-40 / 20)
    first = next((i for i in range(len(ch[0])) if any(abs(c[i]) >= gate for c in ch)), 0)
    last = len(ch[0]) - 1 - next((i for i in range(len(ch[0])) if any(abs(c[-1 - i]) >= gate * 0.1 for c in ch)), 0)
    start = max(0, first - int(0.002 * rate))
    ch = [c[start:last + 1] for c in ch]
    fade = min(int(0.005 * rate), len(ch[0]))
    for c in ch:
        for j in range(fade):
            c[len(c) - fade + j] *= 1 - (j + 1) / fade
        c.extend([0.0] * int(0.010 * rate))
    return ch


def loop_crossfade(ch, rate):
    L = min(int(0.020 * rate), len(ch[0]) // 4)
    if L < 2:
        return ch
    out = []
    for c in ch:
        n = len(c)
        out.append(c[L:n - L] + [c[n - L + j] * (1 - j / L) + c[j] * (j / L) for j in range(L)])
    return out


def reverb(ch, rate, rt60, wet=0.3):
    """Schroeder reverb (4 combs, 2 all-passes) with the given RT60; adds rt60 seconds of tail."""
    combs = [0.0297, 0.0371, 0.0411, 0.0437]
    out = []
    for c in ch:
        x = c + [0.0] * int(rt60 * rate)
        acc = [0.0] * len(x)
        for d in combs:
            D = max(1, int(d * rate))
            g = 10 ** (-3 * d / rt60)
            buf = [0.0] * len(x)
            for i in range(len(x)):
                buf[i] = x[i] + (g * buf[i - D] if i >= D else 0.0)
            for i in range(len(x)):
                acc[i] += buf[i] / len(combs)
        for d, g in ((0.005, 0.7), (0.0017, 0.7)):
            D = max(1, int(d * rate))
            y = [0.0] * len(acc)
            for i in range(len(acc)):
                xd = acc[i - D] if i >= D else 0.0
                yd = y[i - D] if i >= D else 0.0
                y[i] = -g * acc[i] + xd + g * yd
            acc = y
        out.append([x[i] * (1 - wet) + acc[i] * wet for i in range(len(x))])
    return out


def gain(ch, db):
    g = 10 ** (db / 20)
    return [[v * g for v in c] for c in ch]


def peak_db(ch):
    return audio_check.dbfs(max((abs(v) for c in ch for v in c), default=0.0))


def write_wav(path, ch, rate):
    os.makedirs(os.path.dirname(os.path.abspath(path)), exist_ok=True)
    frames = bytearray()
    for i in range(len(ch[0])):
        for c in ch:
            frames += struct.pack("<h", int(round(max(-1.0, min(1.0, c[i])) * 32767)))
    with wave.open(path, "wb") as w:
        w.setnchannels(len(ch))
        w.setsampwidth(2)
        w.setframerate(rate)
        w.writeframes(bytes(frames))


def process(src, row, fam, style, reverb_opt="auto", lufs_opt="auto"):
    """(channels, rate, steps) for one supplied file, fitted to its row and style family."""
    rate, ch = load_any(src)
    steps = []
    if rate not in (44100, 48000):
        ch, steps = [resample(c, rate, 48000) for c in ch], steps + [f"resample {rate}->48000"]
        rate = 48000
    want = int(row["channels"])
    if len(ch) != want:
        ch, steps = to_channels(ch, want), steps + [f"channels {len(ch)}->{want}"]
    rng = style["families"][fam].get("ranges", {})
    oneshot = row["kind"] == "oneshot"
    if oneshot:
        m = asc.measure_chans(ch, rate)
        lo_hi = rng.get("decay_s")
        rt = None
        if reverb_opt not in ("off", "auto"):
            rt = float(reverb_opt)
        elif reverb_opt == "auto" and lo_hi and (m.get("decay_s") or 0) < lo_hi[0]:
            rt = (lo_hi[0] + lo_hi[1]) / 2
        if rt:
            ch, steps = reverb(ch, rate, rt), steps + [f"reverb rt60={rt:.2f}s"]
        ch, steps = trim_oneshot(ch, rate), steps + ["trim start, 5 ms end fade"]
    else:
        ch, steps = loop_crossfade(ch, rate), steps + ["loop wrap crossfade 20 ms"]
    if "lufs" in rng or lufs_opt != "auto":
        target = float(lufs_opt) if lufs_opt != "auto" else sum(rng["lufs"]) / 2
        now = asc.lufs(ch, rate)
        if math.isfinite(now):
            g = target - now
            head = -1.1 - (peak_db(ch) + g)
            if head < 0:
                g += head
                steps.append(f"loudness {now:.1f}->{now + g:.1f} LUFS (peak-limited; target {target:.1f})")
            else:
                steps.append(f"loudness {now:.1f}->{target:.1f} LUFS")
            ch = gain(ch, g)
    return ch, rate, steps


def variant(ch, rate, seed):
    rnd = random.Random(seed)
    cents = rnd.choice((-1, 1)) * rnd.uniform(25, 50)
    f = 2 ** (cents / 1200)
    out = [resample(c, rate, int(rate / f)) for c in ch]
    return gain(out, rnd.uniform(-0.8, 0.0)), f"variation pitch {cents:+.0f} cents"


def next_index(folder, sid):
    used = {int(m.group(2)) for f in (os.listdir(folder) if os.path.isdir(folder) else [])
            for m in [asc.NAME.match(f)] if m and m.group(1) == sid}
    i = 0
    while i in used:
        i += 1
    return i


def append_prov(root, row):
    p = os.path.join(root, "pipeline", "art", "provenance.csv")
    rows = []
    if os.path.isfile(p):
        with open(p, encoding="utf-8", newline="") as fh:
            rows = [r for r in csv.DictReader(fh) if r["asset_path"] != row["asset_path"]]
    rows.append(row)
    with open(p, "w", encoding="utf-8", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=PROV_COLS)
        w.writeheader()
        w.writerows(rows)


def add_table_row(path, heading, row_line, key):
    """Append a markdown table row under the first table after `heading` (once)."""
    if not os.path.isfile(path):
        return False
    text = open(path, encoding="utf-8").read()
    if key in text:
        return False
    lines = text.splitlines()
    i = next((k for k, ln in enumerate(lines) if ln.startswith("#") and heading in ln), None)
    if i is None:
        return False
    j = i + 1
    while j < len(lines) and not lines[j].startswith("|"):
        j += 1
    while j < len(lines) and lines[j].startswith("|"):
        j += 1
    lines.insert(j, row_line)
    with open(path, "w", encoding="utf-8") as fh:
        fh.write("\n".join(lines) + "\n")
    return True


def declare(root, rel, author, made, licence, src):
    add_table_row(os.path.join(root, CREDITS), "Sourced assets",
                  f"| `{rel}` | {author} | {licence} | supplied audio made before the jam ({made}; source {src}) |",
                  f"`{rel}`")
    add_table_row(os.path.join(root, DECLARATION), "Assets made or picked before the jam",
                  f"| `{rel}` | Supplied sound made by {author} before the jam ({made}), processed in the jam | Yes |",
                  f"`{rel}`")


def cmd_apply(a, root):
    style, rows = ctx(root)
    by_id = {r["id"]: r for r in rows}
    folder = os.path.join(root, a.inp)
    try:
        made = dt.datetime.fromisoformat(a.made + "T12:00-05:00") if len(a.made) == 10 else dt.datetime.fromisoformat(a.made)
    except ValueError:
        print("FAIL --made is YYYY-MM-DD (the day the supplier made the files)")
        return 2
    got, left = matches(folder, rows)
    ids = set(a.ids.split(",")) if a.ids else None
    groups = {}
    for f, sid in sorted(got.items()):
        if not ids or sid in ids:
            groups.setdefault(sid, []).append(f)
    fails, n_out = 0, 0
    pre = made.tzinfo is not None and made < JAM_START
    for sid, files in sorted(groups.items()):
        row, fam = by_id[sid], asc.family_of(sid, style)
        if fam is None:
            print(f"FAIL {sid}: no style family in style.json")
            fails += 1
            continue
        dest = os.path.join(root, "Audio", "Source", sid)
        outs = []
        for f in files:
            try:
                ch, rate, steps = process(os.path.join(folder, f), row, fam, style, a.reverb, a.lufs)
            except (ValueError, OSError) as e:
                print(f"FAIL {f}: {e}")
                fails += 1
                continue
            outs.append((ch, rate, steps, f))
        need = int(row["takes"])
        k = 0
        while outs and len(outs) < need:
            ch, rate, steps, f = outs[k % len(outs)]
            vch, why = variant(ch, rate, f"{sid}-{len(outs)}")
            outs.append((vch, rate, steps + [why], f))
            k += 1
        for ch, rate, steps, f in outs:
            i = next_index(dest, sid)
            out = os.path.join(dest, f"SW_{sid}_{i:02d}.wav")
            write_wav(out, ch, rate)
            rel = os.path.relpath(out, root).replace(os.sep, "/")
            src_rel = os.path.join(a.inp, f).replace(os.sep, "/")
            append_prov(root, {"asset_path": rel, "author": a.author, "origin": SUPPLIED, "tool": TOOL,
                               "model_version": "none", "prompt": "; ".join(steps), "seed": "",
                               "input_images": src_rel, "date": made.date().isoformat(), "licence": a.licence,
                               "attribution": a.author})
            print(f"IMPORT {rel} <- {src_rel} ({'; '.join(steps)})")
            if pre:
                declare(root, rel, a.author, made.date().isoformat(), a.licence, src_rel)
                print(f"PRE-JAM: {rel} was made {made.date()} by {a.author}, before the jam start: declared in "
                      f"{CREDITS} 'Sourced assets' and {DECLARATION} (Official Rules 7(h); sourced assets are noted "
                      "on the submission and are not scored)")
            n_out += 1
    for f in left:
        print(f"FAIL {f}: no row; run `audio_import.py match` and add it to map.csv")
    print(f"audio_import apply: {'FAIL' if fails or left else 'PASS'} takes={n_out} ids={len(groups)} "
          f"unmatched={len(left)}")
    if n_out:
        print("Next: tools/audio_style_check.py check Audio/Source --ids <ids>, then the critic loop "
              "(tools/audio_loop.py start / round / verdict / close)")
    return 1 if fails or left else 0


def supplied_ids(root):
    p = os.path.join(root, "pipeline", "art", "provenance.csv")
    out = set()
    for path, r in audio_check.provenance_rows(p).items():
        m = re.match(r"^Audio/Source/([A-Za-z0-9]+)/", path)
        if m and (r.get("origin") or "").strip().lower() == SUPPLIED:
            out.add(m.group(1))
    return out


def cmd_todo(a, root):
    style, rows = ctx(root)
    have = set(asc.takes(os.path.join(root, "Audio", "Source")))
    got, _ = matches(os.path.join(root, a.inp), rows)
    waiting = set(got.values())
    todo = [r for r in rows if r["id"] not in have and r["id"] not in waiting]
    for r in todo:
        print(f"GENERATE {r['id']} ({r['tier']}): tools/assetgen.py {'music' if r['class'] == 'Music' else 'sfx'} "
              f"--sound {r['id']} --out Audio/Source/{r['id']}/SW_{r['id']}_00.wav")
    print(f"audio_import todo: {len(todo)} row(s) with no take and no supplied file; {len(waiting)} waiting in "
          f"{a.inp}")
    return 0


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--root", default=ROOT)
    sub = ap.add_subparsers(dest="cmd", required=True)
    for name in ("match", "apply", "todo"):
        p = sub.add_parser(name)
        p.add_argument("--in", dest="inp", default=os.path.join("Audio", "Import"))
        if name == "apply":
            p.add_argument("--author", required=True)
            p.add_argument("--made", required=True)
            p.add_argument("--licence", required=True)
            p.add_argument("--ids")
            p.add_argument("--reverb", default="auto")
            p.add_argument("--lufs", default="auto")
    a = ap.parse_args(argv)
    root = os.path.abspath(a.root)
    try:
        return {"match": cmd_match, "apply": cmd_apply, "todo": cmd_todo}[a.cmd](a, root)
    except (OSError, ValueError) as e:
        print(f"audio_import: {e}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    sys.exit(main())
