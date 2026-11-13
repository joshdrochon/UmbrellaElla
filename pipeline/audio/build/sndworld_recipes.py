"""Loop recipes for the sndworld lane (sndworld_build.py). One per sound id; edit between critic rounds.
seconds: loop length. rms_db: the file's level (audio_check: every ambience loop within 3 dB of the family median).
Layer with "hits": one-shot samples on a time grid; any other layer is a continuous bed.
Music tempo: 75 BPM (beat 0.8 s); the three stems are 40 beats = 32.0 s; ClockTickLoop ticks on the same beat."""
BEAT = 0.8

RECIPES = {
 "WindZoneLoop": {   # two swelling updraft whooshes half a loop apart, so one always lifts as the other lets go
  "seconds": 6.4, "rms_db": -27.0,
  "reverb": {"rt60": 1.2, "wet_db": -12, "damp_hz": 4500, "predelay_ms": 20},
  "layers": {
   "lift": {"prompt": "a rising, lifting current of air, gentle and buoyant, brighter than a storm, smooth wind, no voices",
            "secs": 10, "cand": 1, "skip": 0.25, "xfade": 3.0, "filter": "highpass=f=200,lowpass=f=4000", "level_db": -28, "pan": -0.3},
   "lift2": {"prompt": "a rising, lifting current of air, gentle and buoyant, brighter than a storm, smooth wind, no voices",
            "secs": 10, "cand": 0, "skip": 0.25, "xfade": 3.0, "rot": 3.2, "filter": "highpass=f=200,lowpass=f=4000", "level_db": -29, "pan": 0.3},
   "body": {"prompt": "low soft wind hum under a stone arch, smooth, steady, quiet, no voices",
            "secs": 22, "filter": "lowpass=f=500", "level_db": -34},
  }},
 "GustLoop": {
  "seconds": 12.0, "rms_db": -25.5,
  "reverb": {"rt60": 1.0, "wet_db": -15, "damp_hz": 3500, "predelay_ms": 15},
  "layers": {
   "wall": {"prompt": "violent storm wind roaring and buffeting hard, heavy gusts slamming, continuous forceful gale, no voices, no rain, no thunder",
            "secs": 22, "filter": "highpass=f=60,lowpass=f=3800", "level_db": -27, "pan": -0.2},
   "flap": {"prompt": "heavy canvas sail flapping and snapping violently in a strong wind, cloth whipping, continuous, no voices",
            "secs": 22, "filter": "highpass=f=250,lowpass=f=3500,acompressor=threshold=-34dB:ratio=8:attack=0.5:release=60:makeup=1", "level_db": -32, "pan": 0.3},
   "rumble": {"prompt": "deep low wind rumble pressing against stone walls, heavy, continuous, no voices",
              "secs": 22, "filter": "lowpass=f=260", "level_db": -30},
  }},
}
