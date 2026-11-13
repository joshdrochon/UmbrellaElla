#!/usr/bin/env python3
"""One provenance row per Audio/Source take (pipeline/art/provenance.csv). Never appends a second row for a path.
  provenance.py generated <Id>          the critic passed: one 'generated in jam' row per take (layers from recipes.py)
  provenance.py placeholder <Id> <gap>  the critic failed: the takes' rows read 'placeholder: audio critic fail (<gap>)'
  provenance.py dedupe                  keep the last row of every Audio/ path, at the first row's position
  provenance.py record <Id> [state dir] copy the critic rounds on the current takes from the audio_loop state
                                        (default Saved/AudioLoop) to pipeline/audio/critic/<Id>.json (committed)
`generated` needs a passing record on the current bytes; `placeholder` refuses while the latest record on them passes
(tools/audio_check.py --scan fails on either mismatch).
"""
import csv, sys, datetime, json, glob
from pathlib import Path
ROOT = Path(__file__).resolve().parents[3]
PROV = ROOT / "pipeline/art/provenance.csv"
APPROVED = "approved by Josh"          # a take Josh listened to: its row is never rewritten


def load():
    with open(PROV, newline="", encoding="utf-8") as fh:
        return list(csv.reader(fh))


def save(rows):
    with open(PROV, "w", newline="", encoding="utf-8") as fh:
        csv.writer(fh, lineterminator="\n").writerows(rows)


def dedupe(rows):
    last = {r[0]: r for r in rows[1:] if r and r[0].startswith("Audio/")}
    for r in rows[1:]:                 # an approved row wins over any later row for its path
        if r and r[0] in last and APPROVED in r[2]:
            last[r[0]] = r
    out, seen = [rows[0]], set()
    for r in rows[1:]:
        if r and r[0] in last:
            if r[0] in seen:
                continue
            seen.add(r[0]); r = last[r[0]]
        out.append(r)
    return out


def _check():
    sys.path.insert(0, str(ROOT / "tools"))
    import audio_check
    return audio_check


def takes(sid):
    return sorted(str(f) for f in (ROOT / "Audio/Source" / sid).glob("*.wav"))


def latest(sid):
    """The latest committed critic record on the current takes, or None."""
    return _check().critic_verdict(sid, takes(sid), str(ROOT))


def passed(sid):
    r = latest(sid)
    return bool(r and r.get("verdict") == "pass" and r.get("style_pass"))


def record(sid, state="Saved/AudioLoop"):
    ac = _check()
    h = ac.takes_hash(takes(sid))
    out = ROOT / ac.CRITIC_DIR / f"{sid}.json"
    recs = ac.critic_records(sid, str(ROOT))
    have = {(r.get("card"), r.get("round"), r.get("files")) for r in recs}
    for f in sorted(glob.glob(str(ROOT / state / "*" / "state.json"))):
        st = json.load(open(f, encoding="utf-8"))
        for r in st.get("pieces", {}).get(sid, {}).get("rounds", []):
            key = (st.get("card"), r.get("n"), r.get("files"))
            if r.get("files") == h and r.get("verdict") in ("pass", "fail") and key not in have:
                have.add(key)
                recs.append({"files": h, "verdict": r["verdict"], "style_pass": bool(r.get("style_pass")),
                             "gap": r.get("gap", ""), "card": st.get("card"), "round": r.get("n"),
                             "critic": r.get("critic", ""), "at": r.get("judged") or r.get("at", "")})
    recs.sort(key=lambda r: r.get("at", ""))
    if not any(r["files"] == h for r in recs):
        sys.exit(f"{sid}: no critic round on the current takes ({h[:12]}) under {state}")
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps({"id": sid, "records": recs}, indent=1) + "\n", encoding="utf-8")
    r = latest(sid)
    print(f"{sid}: {len(recs)} record(s); latest on {h[:12]}: {r['verdict']} (card {r['card']} round {r['round']})")


def generated(rows, sid):
    if not passed(sid):
        sys.exit(f"{sid}: no passing critic record on the current takes; run `provenance.py record {sid}` after the critic passes")
    sys.path.insert(0, str(Path(__file__).parent))
    from recipes import RECIPES
    rec = RECIPES[sid]
    prompt = "Layered mix (pipeline/audio/build/regen.py, ffmpeg): " + " + ".join(
        f"{n}: {s['prompt']}" for n, s in rec["layers"].items()) + ". Original sound for an etched gothic storybook game. No vocals with words."
    synth = all(l.get("kind") == "synth" for l in rec["layers"].values())   # no API layer: ffmpeg synthesis only
    tool, lic = (("ffmpeg", "LGPL-2.1-or-later (GPL build options); output belongs to the team") if synth else
                 ("ElevenLabs Sound Effects API", "ElevenLabs Terms: commercial use on a paid plan; free plan needs attribution [VERIFY]"))
    now = datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M+00:00")
    new = {f.relative_to(ROOT).as_posix(): [f.relative_to(ROOT).as_posix(), "team (tools/assetgen.py)", "synthesized in jam" if synth else "generated in jam",
           tool, "", prompt, "", "", now, lic,
           "none" if synth else "see pipeline/submission/credits.md"] for f in sorted((ROOT / "Audio/Source" / sid).glob("*.wav"))}
    out, seen = [], set()
    for r in rows:
        if r and r[0] in new:
            if APPROVED in r[2]:
                sys.exit(f"{r[0]}: approved by Josh, not rewritten")
            if r[0] in seen:
                continue
            seen.add(r[0]); r = new[r[0]]
        elif r and r[0].startswith(f"Audio/Source/{sid}/"):
            continue                   # a take that no longer exists
        out.append(r)
    return out + [v for k, v in new.items() if k not in seen]


def placeholder(rows, sid, gap):
    if passed(sid):
        r = latest(sid)
        sys.exit(f"{sid}: the blind critic passed these bytes (card {r['card']} round {r['round']}); not marked placeholder. "
                 "Record the failing round first (provenance.py record) if a later critic failed them")
    n = 0
    for r in rows[1:]:
        if r and r[0].startswith(f"Audio/Source/{sid}/"):
            if APPROVED in r[2]:
                sys.exit(f"{r[0]}: approved by Josh, not rewritten")
            r[2] = f"placeholder: audio critic fail ({gap.strip()})"; n += 1
    if not n:
        sys.exit(f"no provenance row for Audio/Source/{sid}/")
    return rows


if __name__ == "__main__":
    cmd = sys.argv[1]
    if cmd == "record":
        record(*sys.argv[2:4])
        sys.exit(0)
    rows = dedupe(load())
    if cmd == "generated":
        rows = generated(rows, sys.argv[2])
    elif cmd == "placeholder":
        rows = placeholder(rows, sys.argv[2], sys.argv[3])
    elif cmd != "dedupe":
        sys.exit(__doc__)
    save(rows)
