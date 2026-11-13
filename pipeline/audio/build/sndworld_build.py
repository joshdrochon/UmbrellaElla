#!/usr/bin/env python3
"""Seamless loop builder for the sndworld lane (ambience loops and the three fight music stems).
Usage: sndworld_build.py <Id> [--cand N]      (key: source ~/.umbrella-ella.env in the same shell; never printed)
       sndworld_build.py prov <Id> generated | placeholder "<gap>"

Reuses regen.py (gen_layer: ElevenLabs layers cached in $REGEN_DIR, reverb_ir: convolution impulse) and provenance.py
without editing them; recipes are in sndworld_recipes.py. What regen.py's mix does not do and a loop needs:
  - every layer is made exactly L-periodic: a bed is crossfaded tail-into-head (equal power), a grid layer (ticks,
    bells, hits at listed times) is rendered over two cycles and the second is kept, so tails wrap round the loop point;
  - the convolution reverb runs over three cycles and the middle one is kept (steady state, the tail wraps too);
  - level is one static gain to the recipe's RMS (no loudnorm, no fades: both would be heard once per cycle);
  - stereo: layers are panned, the reverb uses a different impulse per side.
"""
import csv, json, os, re, subprocess, sys
from pathlib import Path
HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
RATE = 48000
sys.path.insert(0, str(HERE))
import recipes as _base
from sndworld_recipes import RECIPES as MINE
for _r in MINE.values():                         # a layer may reuse another recipe's generated layer: "from": [id, layer, candidate]
    for _l in _r["layers"].values():
        if "from" in _l:
            _l.setdefault("prompt", MINE[_l["from"][0]]["layers"][_l["from"][1]]["prompt"])
_base.RECIPES.update(MINE)                       # provenance.py and regen.py read the same table
_src = (HERE / "regen.py").read_text()
REGEN = {"__file__": str(HERE / "regen.py"), "__name__": "regen"}
exec(compile(re.sub(r"\nmain\(\)\s*$", "\n", _src), str(HERE / "regen.py"), "exec"), REGEN)


def ff(args, what=""):
    r = subprocess.run(["ffmpeg", "-y", "-hide_banner", "-nostats", *args], capture_output=True, text=True)
    if r.returncode:
        raise SystemExit(f"ffmpeg failed ({what}): {r.stderr[-900:]}")
    return r.stderr


def dur(path):
    r = subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", str(path)],
                       capture_output=True, text=True)
    return float(r.stdout.strip())


def levels(path, flt="anull"):
    """(mean dB, max dB) of a file after a filter (ffmpeg volumedetect)."""
    err = ff(["-i", str(path), "-af", flt + ",volumedetect", "-f", "null", "-"], "volumedetect")
    return (float(re.search(r"mean_volume: (-?[\d.]+|-inf)", err).group(1)),
            float(re.search(r"max_volume: (-?[\d.]+|-inf)", err).group(1)))


def source(sid, name, spec, n, d):
    """The generated file for a layer: its own (cached per id), or the one another recipe already paid for."""
    if "from" in spec:
        s2, n2, c2 = spec["from"]
        d2 = d.parent / s2; d2.mkdir(parents=True, exist_ok=True)
        return REGEN["gen_layer"](s2, n2, MINE[s2]["layers"][n2], c2 + n, d2)
    return REGEN["gen_layer"](sid, name, spec, n + spec.get("cand", 0), d)


def bed(src, spec, L, out):
    """A continuous layer made exactly L seconds long and periodic: trim the generator's own fade in and out, filter,
    set the level, then crossfade the last X seconds into the first X (equal power)."""
    skip, X = spec.get("skip", 0.4), spec.get("xfade", 3.0)
    flt = f"aformat=sample_fmts=flt:sample_rates={RATE}:channel_layouts=mono,atrim={skip}:{dur(src) - skip},asetpts=N/SR/TB,{spec.get('filter', 'anull')}"
    tmp = out.with_suffix(".pre.wav")
    ff(["-i", str(src), "-af", flt, "-c:a", "pcm_f32le", str(tmp)], "bed filter")
    mean, mx = levels(tmp)
    print(f"  bed {out.stem}: raw mean {mean:.1f} dB crest {mx - mean:.1f} dB")
    gain = spec.get("level_db", -30) - mean
    cur = tmp
    while dur(cur) < L + X + 0.05:                # too short: loop it on itself first, then cut the long loop
        d = dur(cur); P = d - X
        nxt = cur.with_suffix(".tile.wav")
        ff(["-i", str(cur), "-filter_complex",
            f"[0]asplit[a][b];[a]atrim={X}:{d},asetpts=N/SR/TB[a1];[b]atrim=0:{X},asetpts=N/SR/TB[b1];"
            f"[a1][b1]acrossfade=d={X}:c1=qsin:c2=qsin,aloop=loop=-1:size={int(P * RATE)},atrim=0:{2 * L + 3 * X}",
            "-c:a", "pcm_f32le", str(nxt)], "bed tile")
        cur = nxt
    ff(["-i", str(cur), "-filter_complex",
        f"[0]asplit[a][b];[a]atrim={X}:{L + X},asetpts=N/SR/TB[a1];[b]atrim=0:{X},asetpts=N/SR/TB[b1];"
        f"[a1][b1]acrossfade=d={X}:c1=qsin:c2=qsin,volume={gain}dB,atrim=end_sample={int(L * RATE)},asetpts=N/SR/TB"
        + (f",asplit[r0][r1];[r0]atrim=start={spec['rot']},asetpts=N/SR/TB[r2];[r1]atrim=end={spec['rot']},asetpts=N/SR/TB[r3];"
           f"[r2][r3]concat=n=2:v=0:a=1,atrim=end_sample={int(L * RATE)}" if spec.get("rot") else ""),   # rot: start the loop rot seconds in
        "-c:a", "pcm_f32le", str(out)], "bed loop")


def pre(spec, si):
    """Filter chain for one grid sample. cuts: [seconds] = where sample si starts inside one generated file (a
    generated run of ticks, cut into single ticks); without cuts each sample is its own file, leading silence removed."""
    head = (f"atrim=start={spec['cuts'][si]},asetpts=N/SR/TB" if "cuts" in spec else
            f"silenceremove=start_periods=1:start_threshold={spec.get('start_db', -30)}dB")
    trim, rate = spec.get("trim", 1.0), spec.get("rate", 1.0)   # rate < 1: slower and lower (a heavier, bigger source)
    return (f"aformat=sample_fmts=flt:sample_rates={RATE}:channel_layouts=mono,{head},atrim=0:{trim * rate},asetpts=N/SR/TB,"
            f"asetrate={int(RATE * rate)},aresample={RATE},"
            f"afade=t=in:d=0.002,volume='exp(-t*{spec.get('decay', 0)})':eval=frame,{spec.get('filter', 'anull')},"
            f"afade=t=out:st={trim - 0.02}:d=0.02")


def grid(srcs, spec, L, out):
    """One-shot samples placed at exact times; rendered over two cycles, second kept, so tails wrap the loop point.
    hits: [seconds, gain dB, sample index]; each sample's peak is set to peak_db first."""
    ins, chains, labs = [], [], []
    nsamp = len(spec["cuts"]) if "cuts" in spec else len(srcs)
    for s in srcs:
        ins += ["-i", str(s)]
    peak = {si: levels(srcs[0 if "cuts" in spec else si], pre(spec, si))[1] for si in range(nsamp)}
    k = 0
    for cyc in (0, 1):
        for h in spec["hits"]:
            t, g, si = h[0], (h[1] if len(h) > 1 else 0), (h[2] if len(h) > 2 else 0) % nsamp
            ms = int(round((t + cyc * L) * 1000))
            chains.append(f"[{0 if 'cuts' in spec else si}:a]{pre(spec, si)},volume={spec.get('peak_db', -12) - peak[si] + g}dB,adelay={ms}:all=1[h{k}]")
            labs.append(f"[h{k}]"); k += 1
    g = ";".join(chains) + ";" + "".join(labs) + (f"amix=inputs={k}:normalize=0:duration=longest," if k > 1 else "anull,") + \
        f"apad=whole_len={int(2 * L * RATE)},atrim=start_sample={int(L * RATE)}:end_sample={int(2 * L * RATE)},asetpts=N/SR/TB"
    ff([*ins, "-filter_complex", g, "-c:a", "pcm_f32le", str(out)], "grid")


def build(sid, cand=0):
    rec = MINE[sid]
    L = rec["seconds"]; N = int(round(L * RATE)); L = N / RATE
    d = Path(os.environ.get("REGEN_DIR", "/tmp/gen")) / sid
    d.mkdir(parents=True, exist_ok=True)
    ins, chains, labs = [], [], []
    for i, (name, spec) in enumerate(rec["layers"].items()):
        lay = d / f"L_{name}.wav"
        if "hits" in spec:
            n = spec.get("samples", 1)
            grid([source(sid, name, spec, cand + j, d) for j in range(n)], spec, L, lay)
        else:
            bed(source(sid, name, spec, cand, d), spec, L, lay)
        p = spec.get("pan", 0.0)                  # -1 left .. 1 right, constant power
        import math
        a = (p + 1) * math.pi / 4
        ins += ["-i", str(lay)]
        chains.append(f"[{i}:a]volume={spec.get('gain_db', 0)}dB,pan=stereo|c0={math.cos(a):.4f}*c0|c1={math.sin(a):.4f}*c0[l{i}]")
        labs.append(f"[l{i}]")
    n = len(labs)
    g = ";".join(chains) + ";" + "".join(labs) + f"amix=inputs={n}:normalize=0:duration=first,{rec.get('post', 'anull')},atrim=end_sample={N}"
    rv = rec.get("reverb")
    if rv:
        irs = [REGEN["reverb_ir"](dict(rv, seed=rv.get("seed", 7) + k), d / f"ir{k}.wav") for k in (0, 1)]
        ins += ["-i", str(irs[0]), "-i", str(irs[1])]
        wet = rv.get("wet_db", -10) - 12
        g += (f",aloop=loop=2:size={N},asplit=3[dry][s0][s1];"
              f"[s0]pan=mono|c0=0.5*c0+0.5*c1[m0];[s1]pan=mono|c0=0.5*c0+0.5*c1[m1];"
              f"[m0][{n}:a]afir=dry=1:wet=1:gtype=none:irnorm=-1[w0];[m1][{n + 1}:a]afir=dry=1:wet=1:gtype=none:irnorm=-1[w1];"
              f"[w0][w1]join=inputs=2:channel_layout=stereo,volume={wet}dB[wet];"
              f"[dry][wet]amix=inputs=2:normalize=0:duration=first,atrim=start_sample={N}:end_sample={2 * N},asetpts=N/SR/TB")
    raw = d / "mix.wav"
    ff([*ins, "-filter_complex", g + "[o]", "-map", "[o]", "-c:a", "pcm_f32le", str(raw)], "mix")
    mean, mx = levels(raw)
    gain = rec["rms_db"] - mean
    if mx + gain > -1.3:
        raise SystemExit(f"{sid}: peak would be {mx + gain:.1f} dBFS at RMS {rec['rms_db']} (crest {mx - mean:.1f} dB); tame the peaks in the recipe")
    out = ROOT / "Audio/Source" / sid / f"SW_{sid}_00.wav"
    out.parent.mkdir(parents=True, exist_ok=True)
    ff(["-i", str(raw), "-af", f"volume={gain}dB,atrim=end_sample={N}", "-ar", str(RATE), "-c:a", "pcm_s16le", str(out)], "final")
    print(f"made {out.relative_to(ROOT)} seconds={L:.3f} rms={rec['rms_db']} peak={mx + gain:.1f}")
    r = subprocess.run([sys.executable, "tools/audio_style_check.py", "check", "Audio/Source", "--ids", sid], cwd=ROOT, capture_output=True, text=True)
    print(r.stdout.strip())


TOOLS = {"music": ("ElevenLabs Music API", "ElevenLabs Terms: commercial use on a paid plan [VERIFY]")}


def prov(sid, mode, gap=""):
    """One row per take, inserted at its sorted place among the Audio/ rows (parallel lanes rarely touch the same lines)."""
    import provenance
    rows = provenance.dedupe(provenance.load())
    if mode == "placeholder" and any(r and r[0].startswith(f"Audio/Source/{sid}/") for r in rows):
        rows = provenance.placeholder(rows, sid, gap)
    else:
        rows = provenance.generated(rows, sid)
        mine = [r for r in rows if r and r[0].startswith(f"Audio/Source/{sid}/")]
        rows = [r for r in rows if r not in mine]
        for r in mine:
            if any(l.get("kind") == "music" for l in MINE[sid]["layers"].values()):
                r[3], r[9] = TOOLS["music"]
            r[5] = r[5].replace("regen.py", "sndworld_build.py")
            if mode == "placeholder":
                r[2] = f"placeholder: audio critic fail ({gap.strip()})"
            at = next((i for i, x in enumerate(rows) if i and x and x[0].startswith("Audio/") and x[0] > r[0]), None)
            if at is None:
                at = max((i for i, x in enumerate(rows) if x and x[0].startswith("Audio/")), default=len(rows) - 1) + 1
            rows.insert(at, r)
    provenance.save(rows)
    print(f"provenance: {sid} {mode}")


if __name__ == "__main__":
    if sys.argv[1] == "prov":
        prov(sys.argv[2], sys.argv[3], sys.argv[4] if len(sys.argv) > 4 else "")
    else:
        build(sys.argv[1], int(sys.argv[sys.argv.index("--cand") + 1]) if "--cand" in sys.argv else 0)
