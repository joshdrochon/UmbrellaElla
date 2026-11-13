#!/usr/bin/env python3
"""provenance.py <Id>: append one 'generated in jam' row per Audio/Source/<Id>/*.wav (layers from recipes.py)."""
import csv, sys, datetime
from pathlib import Path
ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(Path(__file__).parent))
from recipes import RECIPES
sid = sys.argv[1]; rec = RECIPES[sid]
prompt = "Layered mix (pipeline/audio/build/regen.py, ffmpeg): " + " + ".join(
    f"{n}: {s['prompt']}" for n, s in rec["layers"].items()) + ". Original sound for an etched gothic storybook game. No vocals with words."
now = datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M+00:00")
with open(ROOT / "pipeline/art/provenance.csv", "a", newline="") as fh:
    w = csv.writer(fh, lineterminator="\n")
    for f in sorted((ROOT / "Audio/Source" / sid).glob("*.wav")):
        w.writerow([f.relative_to(ROOT).as_posix(), "team (tools/assetgen.py)", "generated in jam",
                    "ElevenLabs Sound Effects API", "", prompt, "", "", now,
                    "ElevenLabs Terms: commercial use on a paid plan; free plan needs attribution [VERIFY]",
                    "see pipeline/submission/credits.md"])
