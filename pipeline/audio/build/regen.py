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

def gen_layer(sid, name, spec, n, d):
    """One ElevenLabs call (same endpoints as tools/assetgen.py); the key comes from the environment, never printed."""
    import urllib.request, urllib.error
    out = d / f"{name}_{n}.wav"
    if out.exists() and out.stat().st_size > 2000:
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
        chain += (f"silenceremove=start_periods=1:start_threshold=-42dB,volume='exp(-t*{spec['decay']})':eval=frame,{f},volume={spec.get('gain_db', 0)}dB" if "decay" in spec else
                  f"silenceremove=start_periods=1:start_threshold=-42dB,{f},volume={spec.get('gain_db', 0)}dB")
        if delay: chain += f",adelay={delay}|{delay}"
        chains.append(chain + f"[l{i}]"); labels.append(f"[l{i}]")
    total = rec["seconds"]
    fade = rec.get("fade_out", 0.05)
    post = rec.get("post", "anull")
    g = ";".join(chains) + ";" + "".join(labels) + f"amix=inputs={len(labels)}:normalize=0:duration=longest," \
        f"apad=whole_dur={total},atrim=0:{total},{post},afade=t=out:st={max(0, total - fade)}:d={fade}," \
        f"loudnorm=I={rec['lufs']}:TP=-2:LRA=7,atrim=0:{total},aresample=48000,alimiter=limit=0.85:level=disabled[o]"
    r = run(["ffmpeg", "-y", "-loglevel", "error", *ins, "-filter_complex", g, "-map", "[o]", "-ac", "1",
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
            mix(rec, files, chk / f"SW_{a.sid}_{t:02d}.wav")
            r = run(["python3", "tools/audio_style_check.py", "check", str(chk)])
            if r.returncode == 0 or c == t + 3 * (a.tries - 1):
                dest = outdir / f"SW_{a.sid}_{t:02d}.wav"
                dest.write_bytes((chk / dest.name).read_bytes())
                print("made", dest.name, "candidate", c, "style", "PASS" if r.returncode == 0 else "FAIL")
                break
main()
