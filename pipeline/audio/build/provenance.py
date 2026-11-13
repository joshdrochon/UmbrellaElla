#!/usr/bin/env python3
"""One provenance row per Audio/Source take (pipeline/art/provenance.csv). Never appends a second row for a path.
  provenance.py generated <Id>          the critic passed: one 'generated in jam' row per take (layers from recipes.py)
  provenance.py placeholder <Id> <gap>  the critic failed: the takes' rows read 'placeholder: audio critic fail (<gap>)'
  provenance.py dedupe                  keep the last row of every Audio/ path, at the first row's position
"""
import csv, sys, datetime
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


def generated(rows, sid):
    sys.path.insert(0, str(Path(__file__).parent))
    from recipes import RECIPES
    rec = RECIPES[sid]
    prompt = "Layered mix (pipeline/audio/build/regen.py, ffmpeg): " + " + ".join(
        f"{n}: {s['prompt']}" for n, s in rec["layers"].items()) + ". Original sound for an etched gothic storybook game. No vocals with words."
    now = datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M+00:00")
    new = {f.relative_to(ROOT).as_posix(): [f.relative_to(ROOT).as_posix(), "team (tools/assetgen.py)", "generated in jam",
           "ElevenLabs Sound Effects API", "", prompt, "", "", now,
           "ElevenLabs Terms: commercial use on a paid plan; free plan needs attribution [VERIFY]",
           "see pipeline/submission/credits.md"] for f in sorted((ROOT / "Audio/Source" / sid).glob("*.wav"))}
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
    rows = dedupe(load())
    if cmd == "generated":
        rows = generated(rows, sys.argv[2])
    elif cmd == "placeholder":
        rows = placeholder(rows, sys.argv[2], sys.argv[3])
    elif cmd != "dedupe":
        sys.exit(__doc__)
    save(rows)
