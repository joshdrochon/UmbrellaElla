#!/usr/bin/env python3
"""Layered rebuild of one sound piece: ElevenLabs layers (assetgen) mixed with ffmpeg into Audio/Source takes.
Usage: regen.py <Id> [--take N] [--fresh]   (key: source ~/.umbrella-ella.env in the same shell; never printed)
Layers are cached in $REGEN_DIR (default /tmp/gen/<Id>); take N uses candidate N of every layer."""
import argparse, json, os, subprocess, sys
from pathlib import Path
ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(Path(__file__).parent))
from recipes import RECIPES

def run(cmd, **kw):
    return subprocess.run(cmd, capture_output=True, text=True, cwd=ROOT, **kw)

def synth_expr(spec, n):
    """A synth layer may vary per take: every {f} in expr is the take's frequency from spec['freqs']."""
    fr = spec.get("freqs")
    return spec["expr"].replace("{f}", str(fr[n % len(fr)])) if fr else spec["expr"]


def reverb_ir(rv, path):
    """Room impulse for the afir convolution: seeded noise with an exponential decay to -60 dB at rt60, a one-pole
    low-pass (air damping) and a pre-delay; unit energy, so wet_db sets the level against the dry mix. A smooth tail,
    with none of the repeating taps aecho draws on a spectrogram."""
    import math, random, struct, wave
    rate, rt60 = 48000, rv["rt60"]
    n = int(rate * rt60 * 1.3); pre = int(rate * rv.get("predelay_ms", 15) / 1000)
    rng = random.Random(rv.get("seed", 7)); a = math.exp(-2 * math.pi * rv.get("damp_hz", 5000) / rate)
    k = 6.908 / (rt60 * rate); y = 0.0; out = [0.0] * pre
    for i in range(n):
        y = (1 - a) * rng.gauss(0, 1) + a * y
        out.append(y * math.exp(-k * i) * min(1.0, i / (0.004 * rate)))
    e = math.sqrt(sum(v * v for v in out)) or 1.0
    with wave.open(str(path), "wb") as w:
        w.setnchannels(1); w.setsampwidth(4); w.setframerate(rate)
        w.writeframes(b"".join(struct.pack("<i", int(max(-1, min(1, v / e * 4)) * 2147483000)) for v in out))
    return path


def gen_layer(sid, name, spec, n, d):
    """One ElevenLabs call (same endpoints as tools/assetgen.py); the key comes from the environment, never printed."""
    import urllib.request, urllib.error
    out = d / f"{name}_{n}.wav"
    if out.exists() and out.stat().st_size > 2000 and spec.get("kind") != "synth":
        return out
    if spec.get("kind") == "synth":   # deterministic ffmpeg synthesis (aevalsrc), no API: sharp, pitched, clean sources
        r = run(["ffmpeg", "-y", "-loglevel", "error", "-f", "lavfi", "-i",
                 f"aevalsrc={synth_expr(spec, n)}:s=48000:d={spec['secs']}", "-c:a", "pcm_s16le", str(out)])
        if r.returncode:
            raise SystemExit(r.stderr[-300:])
        return out
    key = os.environ.get("ELEVENLABS_API_KEY")
    if not key:
        raise SystemExit("no ELEVENLABS_API_KEY: source ~/.umbrella-ella.env in this shell")
    music = spec.get("kind") == "music"
    url = "https://api.elevenlabs.io/v1/" + ("music" if music else "sound-generation")
    body = ({"prompt": spec["prompt"], "music_length_ms": int(spec["secs"] * 1000)} if music else
            {"text": spec["prompt"], "duration_seconds": spec["secs"]})
    if not music and "influence" in spec:
        body["prompt_influence"] = spec["influence"]
    req = urllib.request.Request(url, json.dumps(body).encode(), {"xi-api-key": key, "Content-Type": "application/json"})
    try:
        raw = urllib.request.urlopen(req, timeout=300).read()
    except urllib.error.HTTPError as e:
        raise SystemExit(f"layer {name}: HTTP {e.code} {e.read()[:200]!r}")
    tmp = d / f"{name}_{n}.mp3"
    tmp.write_bytes(raw)
    r = run(["ffmpeg", "-y", "-loglevel", "error", "-i", str(tmp), "-ar", "48000", "-c:a", "pcm_s16le", str(out)])
    tmp.unlink()
    if r.returncode:
        raise SystemExit(r.stderr[-300:])
    return out

def mix(rec, files, out):
    ins, chains, labels = [], [], []
    for i, (name, spec) in enumerate(rec["layers"].items()):
        ins += ["-i", str(files[name])]
        f = spec.get("filter", "anull")
        delay = int(spec.get("delay_ms", 0))
        dur = spec.get("trim")
        chain = f"[{i}:a]aformat=sample_rates=48000:channel_layouts=mono,"
        if dur: chain += f"atrim=0:{dur},"
        chain += (f"silenceremove=start_periods=1:start_threshold={spec.get("start_db", -42)}dB,volume='exp(-t*{spec['decay']})':eval=frame,{f},volume={spec.get('gain_db', 0)}dB" if "decay" in spec else
                  f"silenceremove=start_periods=1:start_threshold={spec.get("start_db", -42)}dB,{f},volume={spec.get('gain_db', 0)}dB")
        if "norm_lufs" in spec:   # opt-in: equalise this layer's loudness so candidates mix to the same balance
            chain += f",loudnorm=I={spec['norm_lufs']}:TP=-2:LRA=11,volume={spec.get('gain_db', 0)}dB"
        if delay: chain += f",adelay={delay}|{delay}"
        chains.append(chain + f"[l{i}]"); labels.append(f"[l{i}]")
    total = rec["seconds"]
    fade = rec.get("fade_out", 0.05)
    post = rec.get("post", "anull")
    rv = rec.get("reverb")
    if rv:   # convolution reverb after the post chain: dry + wet (IR scaled by 4 in the file, so -12 dB here = unity)
        ins += ["-i", str(reverb_ir(rv, Path(out).parent.parent / "ir.wav"))]
        post += (f",asplit[dry][w];[w][{len(labels)}:a]afir=dry=1:wet=1:gtype=none:irnorm=-1,"
                 f"volume={rv.get('wet_db', -10) - 12}dB[wet];[dry][wet]amix=inputs=2:normalize=0:duration=longest")
    g = ";".join(chains) + ";" + "".join(labels) + f"amix=inputs={len(labels)}:normalize=0:duration=longest," \
        f"apad=whole_dur={total},atrim=0:{total},{post},afade=t=out:st={max(0, total - fade)}:d={fade}," \
        f"loudnorm=I={rec['lufs']}:TP=-2:LRA=7,atrim=0:{total},aresample=48000,afade=t=out:st={max(0, total - fade)}:d={fade}:curve=qsin," \
        f"volume={rec.get('post_gain_db', 0) + rec.get('take_gain_db', {}).get(rec.get('_take', 0), 0)}dB,alimiter=limit=0.85:level=disabled[o]"
    r = run(["ffmpeg", "-y", "-loglevel", "error", *ins, "-filter_complex", g, "-map", "[o]", "-ac", str(rec.get("channels", 1)),
             "-c:a", "pcm_s16le", str(out)])
    if r.returncode:
        raise SystemExit(r.stderr[-800:])

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("sid"); ap.add_argument("--take", type=int, action="append")
    ap.add_argument("--tries", type=int, default=4); ap.add_argument("--fresh", action="store_true", help="drop cached layers first")
    a = ap.parse_args()
    rec = RECIPES[a.sid]
    d = Path(os.environ.get("REGEN_DIR", "/tmp/gen")) / a.sid
    d.mkdir(parents=True, exist_ok=True)
    if a.fresh:
        for p in d.glob("*.wav"): p.unlink()
    outdir = ROOT / "Audio/Source" / a.sid
    outdir.mkdir(parents=True, exist_ok=True)
    for t in (a.take if a.take is not None else range(rec.get("takes", 3))):
        for c in range(t, t + 3 * a.tries, 3):   # candidate c of every layer; next candidate if the measured check fails
            files = {n: gen_layer(a.sid, n, s, c, d) for n, s in rec["layers"].items()}
            chk = d / "chk"; chk.mkdir(exist_ok=True)
            for old in chk.glob("*.wav"): old.unlink()
            rec['_take'] = t
            mix(rec, files, chk / f"SW_{a.sid}_{t:02d}.wav")
            r = run(["python3", "tools/audio_style_check.py", "check", str(chk)])
            if r.returncode == 0 or c == t + 3 * (a.tries - 1):
                dest = outdir / f"SW_{a.sid}_{t:02d}.wav"
                dest.write_bytes((chk / dest.name).read_bytes())
                print("made", dest.name, "candidate", c, "style", "PASS" if r.returncode == 0 else "FAIL")
                break
main()
