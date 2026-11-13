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
 "WindBed": {   # the always-there bed: the gale's low body only, a moan band around 380 Hz, slow 8 s swells
  "seconds": 16.0, "rms_db": -28.0,
  "post": "tremolo=f=0.125:d=0.45",
  "reverb": {"rt60": 1.8, "wet_db": -11, "damp_hz": 2500, "predelay_ms": 25},
  "layers": {
   "moan": {"from": ["GustLoop", "wall", 0], "xfade": 4.0, "filter": "highpass=f=90,lowpass=f=1100,equalizer=f=380:t=q:w=3:g=9", "level_db": -28, "pan": -0.25},
   "low": {"from": ["GustLoop", "rumble", 0], "xfade": 4.0, "rot": 5.0, "filter": "lowpass=f=300", "level_db": -31, "pan": 0.2},
   "hum": {"from": ["WindZoneLoop", "body", 0], "xfade": 4.0, "rot": 9.0, "filter": "lowpass=f=600", "level_db": -33, "pan": 0.3},
  }},
 "ClockTickLoop": {   # tick on the beat, lighter tock on the half beat, 8 beats at 75 BPM
  "seconds": 8 * BEAT, "rms_db": -29.0,
  "reverb": {"rt60": 0.7, "wet_db": -15, "damp_hz": 5000, "predelay_ms": 10},
  "layers": {
   "tick": {"prompt": "large antique clock ticking slowly and steadily, heavy brass escapement, loud clear tick tock, dry, close, no chimes, no other sounds",
            "secs": 4, "cuts": [0.585, 0.863], "rate": 0.6, "trim": 0.4, "decay": 5, "filter": "highpass=f=120,lowpass=f=7000", "peak_db": -9,
            "hits": [[i * BEAT / 2, 0 if i % 2 == 0 else -4, i % 2] for i in range(16)]},
   "body": {"kind": "synth", "prompt": "synthesised low case knock under each tick: damped partials at 96, 163 and 244 Hz (the wooden and brass body of a big clock)",
            "secs": 0.5, "expr": "0.8*exp(-22*t)*sin(2*PI*96*t)+0.45*exp(-30*t)*sin(2*PI*163*t)+0.2*exp(-45*t)*sin(2*PI*244*t)",
            "trim": 0.45, "start_db": -60, "peak_db": -14,
            "hits": [[i * BEAT / 2, 0 if i % 2 == 0 else -5] for i in range(16)]},
  }},
 "AirMillLoop": {   # a heavy gear train: a low thunk on every beat, cog clacks between, a blade passing on the off-beat
  "seconds": 8 * BEAT, "rms_db": -27.5,
  "reverb": {"rt60": 0.9, "wet_db": -15, "damp_hz": 4000, "predelay_ms": 12},
  "layers": {
   "thunk": {"kind": "synth", "prompt": "synthesised heavy gear thunk: damped partials at 72, 131 and 236 Hz (a big iron cog seating)",
             "secs": 0.6, "expr": "0.9*exp(-16*t)*sin(2*PI*72*t)+0.5*exp(-24*t)*sin(2*PI*131*t)+0.2*exp(-40*t)*sin(2*PI*236*t)",
             "trim": 0.55, "start_db": -60, "peak_db": -14, "hits": [[i * BEAT, 0 if i % 2 == 0 else -3] for i in range(8)]},
   "clack": {"from": ["ClockTickLoop", "tick", 0], "cuts": [0.585, 0.863], "rate": 0.45, "trim": 0.3, "decay": 9,
             "filter": "highpass=f=200,lowpass=f=6000", "peak_db": -9, "pan": -0.2,
             "hits": [[i * BEAT / 4, (0, -8, -4, -8)[i % 4], i % 2] for i in range(32)]},
   "blade": {"prompt": "one single heavy wooden windmill sail swooshing past, low whoosh of a big blade cutting the air, dry, isolated",
             "secs": 1.5, "samples": 1, "trim": 0.7, "start_db": -40, "filter": "highpass=f=100,lowpass=f=1400", "peak_db": -20, "pan": 0.25,
             "hits": [[i * BEAT + BEAT / 2, 0] for i in range(8)]},
  }},
 "RefugeLoop": {   # the quiet room: soft louvre wind, the works turning in the wall, a far bell twice a loop
  "seconds": 24.0, "rms_db": -28.5,
  "reverb": {"rt60": 4.0, "wet_db": -9, "damp_hz": 3000, "predelay_ms": 40},
  "layers": {
   "wind": {"from": ["WindZoneLoop", "body", 0], "xfade": 4.0, "filter": "highpass=f=70,lowpass=f=900", "level_db": -30, "pan": -0.3},
   "air": {"from": ["GustLoop", "wall", 0], "xfade": 4.0, "rot": 7.0, "filter": "highpass=f=300,lowpass=f=1800", "level_db": -37, "pan": 0.35},
   "works": {"from": ["ClockTickLoop", "tick", 0], "cuts": [0.585, 0.863], "rate": 0.7, "trim": 0.34, "decay": 8, "filter": "highpass=f=400,lowpass=f=3500", "peak_db": -27, "pan": 0.3,
             "hits": [[i * 1.6 + 0.4, 0 if i % 2 == 0 else -3, i % 2] for i in range(15)]},
   "bell": {"prompt": "one distant church bell toll, mellow bronze bell heard from far away, clean tonal ring with a long decay, isolated, no other sounds",
            "secs": 5, "samples": 1, "trim": 4.8, "start_db": -35, "filter": "highpass=f=120,lowpass=f=2600", "peak_db": -11, "pan": -0.2,
            "hits": [[5.0, 0], [16.2, -5]]},
  }},
 "MillAmbience": {   # rooftops and the mill: roof wind, the gear train far off through stone, one far bell
  "seconds": 25.6, "rms_db": -27.5,
  "reverb": {"rt60": 3.5, "wet_db": -8, "damp_hz": 2800, "predelay_ms": 40},
  "layers": {
   "wind": {"from": ["GustLoop", "wall", 0], "xfade": 4.0, "filter": "highpass=f=80,lowpass=f=1200", "level_db": -30, "pan": -0.3},
   "low": {"from": ["GustLoop", "rumble", 0], "xfade": 4.0, "rot": 6.0, "filter": "lowpass=f=250", "level_db": -34, "pan": 0.2},
   "thunk": {"from": ["AirMillLoop", "thunk", 0], "trim": 0.55, "start_db": -60, "filter": "lowpass=f=400", "peak_db": -22, "pan": 0.3,
             "hits": [[i * 2 * BEAT, 0 if i % 2 == 0 else -3] for i in range(16)]},
   "cogs": {"from": ["ClockTickLoop", "tick", 0], "cuts": [0.585, 0.863], "rate": 0.45, "trim": 0.3, "decay": 9,
            "filter": "highpass=f=250,lowpass=f=2800", "peak_db": -28, "pan": 0.3,
            "hits": [[i * BEAT / 2, (0, -7, -3, -7)[i % 4], i % 2] for i in range(64)]},
   "bell": {"from": ["RefugeLoop", "bell", 0], "trim": 4.8, "start_db": -35, "filter": "highpass=f=120,lowpass=f=2400", "peak_db": -13, "pan": -0.25,
            "hits": [[9.6, 0]]},
  }},
 "BossApproach": {   # the quiet before the Keeper: a low held wind, a deep slow toll, one heavy slow tick
  "seconds": 25.6, "rms_db": -28.5,
  "reverb": {"rt60": 5.0, "wet_db": -7, "damp_hz": 2200, "predelay_ms": 50},
  "layers": {
   "low": {"from": ["GustLoop", "rumble", 0], "xfade": 4.0, "filter": "lowpass=f=220", "level_db": -29, "pan": -0.2},
   "wind": {"from": ["WindZoneLoop", "body", 0], "xfade": 4.0, "rot": 8.0, "filter": "highpass=f=60,lowpass=f=700", "level_db": -33, "pan": 0.3},
   "toll": {"from": ["RefugeLoop", "bell", 0], "rate": 0.5, "trim": 9.0, "start_db": -35, "filter": "highpass=f=50,lowpass=f=1500", "peak_db": -10, "pan": 0.0,
            "hits": [[3.2, 0], [16.0, -3]]},
   "tick": {"from": ["ClockTickLoop", "tick", 0], "cuts": [0.585], "rate": 0.4, "trim": 0.5, "decay": 5,
            "filter": "highpass=f=120,lowpass=f=2500", "peak_db": -24, "pan": 0.25,
            "hits": [[i * 4 * BEAT + 1.6, 0] for i in range(8)]},
   "knock": {"from": ["ClockTickLoop", "body", 0], "trim": 0.45, "start_db": -60, "peak_db": -24, "pan": 0.25,
             "hits": [[i * 4 * BEAT + 1.6, 0] for i in range(8)]},
  }},
 "RealmClocks": {   # the Other Realm: several far clocks, each at its own rate and size, small chimes, thin wind
  "seconds": 24.0, "rms_db": -28.5,
  "reverb": {"rt60": 4.5, "wet_db": -7, "damp_hz": 3200, "predelay_ms": 45},
  "layers": {
   "wind": {"from": ["WindZoneLoop", "body", 0], "xfade": 4.0, "filter": "highpass=f=70,lowpass=f=800", "level_db": -35, "pan": 0.0},
   "clockA": {"from": ["ClockTickLoop", "tick", 0], "cuts": [0.585, 0.863], "rate": 0.6, "trim": 0.35, "decay": 7,
              "filter": "highpass=f=200,lowpass=f=3500", "peak_db": -19, "pan": -0.6,
              "hits": [[i * 1.0, 0 if i % 2 == 0 else -3, i % 2] for i in range(24)]},
   "clockB": {"from": ["ClockTickLoop", "tick", 0], "cuts": [1.13, 1.396], "rate": 0.4, "trim": 0.5, "decay": 5,
              "filter": "highpass=f=120,lowpass=f=2200", "peak_db": -20, "pan": 0.6,
              "hits": [[i * 1.5 + 0.35, 0 if i % 2 == 0 else -3, i % 2] for i in range(16)]},
   "clockC": {"from": ["ClockTickLoop", "tick", 0], "cuts": [1.67, 1.932], "rate": 0.85, "trim": 0.25, "decay": 9,
              "filter": "highpass=f=400,lowpass=f=4000", "peak_db": -24, "pan": 0.15,
              "hits": [[i * 0.6 + 0.2, 0 if i % 2 == 0 else -4, i % 2] for i in range(40)]},
   "chime": {"from": ["RefugeLoop", "bell", 0], "rate": 2.0, "trim": 2.2, "start_db": -35, "filter": "highpass=f=300,lowpass=f=4500", "peak_db": -15, "pan": -0.3,
             "hits": [[4.0, 0], [5.0, -3], [15.0, -2], [16.0, -5], [17.0, -8]]},
  }},
}
