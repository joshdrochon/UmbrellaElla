"""One recipe per sound id: layers (prompt, filter) mixed to a take. Edit these between critic rounds."""
RECIPES = {
 "WandBolt": {
  "seconds": 0.6, "lufs": -22, "fade_out": 0.25, "takes": 3,
  "post": "aecho=0.8:0.5:35|70:0.25|0.12",
  "layers": {
   "pluck": {"prompt": "single plucked celesta note, clean bell-like tone with clear harmonic partials, dry, isolated, no noise, no other sounds", "secs": 1.0, "filter": "highpass=f=500,lowpass=f=9000", "trim": 0.6, "decay": 6},
   "spark": {"prompt": "tiny glittering music box sparkle, three soft high chime pings, clean, quiet", "secs": 1.0, "filter": "highpass=f=2500", "gain_db": -13, "delay_ms": 60, "trim": 0.5, "decay": 10},
  }},
}

RECIPES.update({
 "HitOwl": {
  "seconds": 0.8, "post_gain_db": 3, "take_gain_db": {1: -2.5}, "lufs": -14, "fade_out": 0.2, "takes": 3,
  "post": "aecho=0.8:0.6:50|110:0.3|0.15",
  "layers": {
   "thud": {"prompt": "single deep low thud impact, heavy boom of a stone and wood hit, dry, isolated, no other sounds", "secs": 1.0, "filter": "highpass=f=60,lowpass=f=260", "norm_lufs": -20, "gain_db": -3, "trim": 0.8, "decay": 6},
   "clank": {"prompt": "one heavy brass clank struck once, pitched metallic ring with a bell partial, dry, isolated", "secs": 1.0, "filter": "highpass=f=400", "norm_lufs": -20, "gain_db": 0, "trim": 0.8, "decay": 5},
  }},
 "OwlBoltLaunch": {
  "post_gain_db": 3, "seconds": 0.8, "lufs": -19, "fade_out": 0.25, "takes": 3,
  "post": "aecho=0.8:0.5:40|90:0.3|0.15",
  "layers": {
   "thunk": {"prompt": "single low clockwork spring release thunk, heavy and dark, dry, isolated", "secs": 1.0, "filter": "lowpass=f=700", "norm_lufs": -20, "gain_db": -9, "trim": 0.6, "decay": 6},
   "clank": {"prompt": "one iron gear clank, pitched metal strike, dry, isolated", "secs": 1.0, "filter": "highpass=f=500", "norm_lufs": -20, "gain_db": 0, "delay_ms": 15, "trim": 0.6, "decay": 6},
   "ratchet": {"prompt": "fast clock ratchet whirring and slowing down, metallic clicks, dry", "secs": 1.0, "filter": "highpass=f=800", "norm_lufs": -20, "gain_db": -3, "delay_ms": 70, "trim": 0.7, "decay": 3},
  }},
 "PlayerHurt": {
  "post_gain_db": 9, "seconds": 0.5, "lufs": -17, "fade_out": 0.12, "takes": 3,
  "post": "aecho=0.9:0.6:13|19|27|37|51:0.35|0.3|0.25|0.2|0.15",
  "layers": {
   "crack": {"prompt": "one sharp wooden crack, a thin wooden rib snapping, dry, isolated", "secs": 1.0, "filter": "highpass=f=700", "norm_lufs": -20, "gain_db": 8, "start_db": -24, "trim": 0.4, "decay": 12},
   "thud": {"prompt": "one deep sub thud, low heavy drop, dry, isolated, no other sounds", "secs": 1.0, "filter": "lowpass=f=200", "norm_lufs": -20, "gain_db": -11, "start_db": -24, "trim": 0.5, "decay": 7},
  }},
 "ShieldCatch": {
  "post_gain_db": 3, "seconds": 0.56, "lufs": -21, "fade_out": 0.15, "takes": 3,
  "post": "aecho=0.8:0.4:25|55:0.2|0.1",
  "layers": {
   "thump": {"prompt": "a deep soft thump of a heavy ball swallowed by taut canvas, dry, isolated", "secs": 1.0, "filter": "lowpass=f=450", "norm_lufs": -20, "gain_db": -9, "trim": 0.5, "decay": 7},
   "click": {"prompt": "one sharp wooden rib click, short dry tick, isolated", "secs": 1.0, "filter": "highpass=f=1200,lowpass=f=5000", "norm_lufs": -20, "gain_db": 0, "trim": 0.3, "decay": 18},
   "canvas": {"prompt": "waxed canvas fabric snapping taut, short, dry, isolated", "secs": 1.0, "filter": "highpass=f=500,lowpass=f=3000", "norm_lufs": -20, "gain_db": -2, "trim": 0.4, "decay": 9},
  }},
 "KeeperHoot": {
  "seconds": 3.0, "take_gain_db": {1: 1.5}, "lufs": -25, "fade_out": 0.8, "takes": 3,
  "post": "aecho=0.8:0.6:120|250:0.3|0.2",
  "layers": {
   "thump": {"prompt": "one single huge slow wingbeat, low heavy thump of a giant wing, dry, isolated", "secs": 2.0, "filter": "lowpass=f=500", "norm_lufs": -20, "gain_db": -8, "start_db": -24, "trim": 2.0, "decay": 1.5},
   "whoosh": {"prompt": "slow heavy leathery whoosh of a giant wing sweeping air, smooth, isolated", "secs": 2.5, "filter": "lowpass=f=2500,highpass=f=120", "norm_lufs": -20, "gain_db": 2, "delay_ms": 120, "trim": 2.4, "decay": 1.0},
   "creak": {"prompt": "slow creak of old brass joints, deep and low, isolated", "secs": 2.5, "filter": "lowpass=f=3000,highpass=f=150", "norm_lufs": -20, "gain_db": -3, "delay_ms": 300, "trim": 2.4, "decay": 1.0},
  }},
 "EndEvent": {
  "seconds": 4.0, "lufs": -18, "fade_out": 1.2, "takes": 3,
  "post": "aecho=0.8:0.7:150|330:0.3|0.2",
  "layers": {
   "strike": {"prompt": "single deep church tower bell strike, clean tonal ring with a long decay, dry, isolated", "secs": 4.0, "filter": "highpass=f=80", "norm_lufs": -20, "trim": 4.0},
   "hum": {"prompt": "very low deep bell hum, sustained resonant drone, smooth, isolated", "secs": 4.0, "filter": "lowpass=f=300", "norm_lufs": -20, "gain_db": -4, "trim": 4.0},
  }},
 "FailSting": {
  "seconds": 5.0, "lufs": -17, "fade_out": 1.5, "takes": 1,
  "post": "aecho=0.8:0.7:150|330:0.3|0.2",
  "layers": {
   "brass": {"prompt": "low brass section playing a slow falling descending note, sombre and heavy, isolated", "secs": 3.0, "filter": "lowpass=f=1500", "norm_lufs": -20, "trim": 3.0},
   "bell": {"prompt": "one dull muffled low bell strike, short ring, isolated", "secs": 2.5, "filter": "lowpass=f=1200", "norm_lufs": -20, "gain_db": -2, "delay_ms": 800, "trim": 2.5},
   "choir": {"prompt": "wordless low choir singing a sustained dark chord that slowly drops in pitch and fades away, isolated", "secs": 4.0, "filter": "lowpass=f=2500", "norm_lufs": -20, "gain_db": -3, "delay_ms": 1200, "trim": 3.8},
  }},
 "SurvivedSting": {
  "seconds": 6.0, "lufs": -17, "fade_out": 2.0, "takes": 1,
  "post": "aecho=0.8:0.7:150|330:0.3|0.2",
  "layers": {
   "bell": {"prompt": "one bright clear church bell toll, clean tonal ring, isolated", "secs": 4.0, "filter": "highpass=f=200", "norm_lufs": -20, "trim": 4.0},
   "choir": {"prompt": "wordless warm choir singing a bright resolved major chord, swelling and sustained, isolated", "secs": 5.0, "filter": "highpass=f=150", "norm_lufs": -20, "gain_db": -3, "delay_ms": 300, "trim": 5.0},
   "wind": {"prompt": "soft gentle wind settling to calm, quiet, isolated", "secs": 4.0, "filter": "lowpass=f=1500", "norm_lufs": -20, "gain_db": -12, "delay_ms": 1500, "trim": 4.0},
  }},
 "LevelUpClock": {
  "post_gain_db": 3, "seconds": 0.477, "lufs": -26, "fade_out": 0.3, "takes": 1,
  "post": "aecho=0.8:0.3:20|45:0.15|0.08",
  "layers": {
   "tick": {"prompt": "short clean escapement tick, dry, isolated", "secs": 0.5, "filter": "highpass=f=800,lowpass=f=4500", "norm_lufs": -20, "gain_db": -3, "start_db": -20, "trim": 0.25, "decay": 30},
   "bell": {"kind": "synth", "prompt": "synthesised small bell: 880 Hz fundamental with inharmonic partials at 1320 and 2217 Hz, exponential decay", "secs": 0.6,
            "expr": "0.6*exp(-7*t)*sin(2*PI*880*t)+0.3*exp(-9*t)*sin(2*PI*1320*t)+0.2*exp(-12*t)*sin(2*PI*2217*t)",
            "filter": "lowpass=f=4000", "gain_db": 0, "trim": 0.6},
  }},
})

# Round after the gate critic (Nov 12): convolution reverb (regen.py reverb_ir) instead of aecho taps, which drew
# vertical stripes; WandBolt from clean additive partials (a celesta bar is near-sinusoidal partials with fast decay).
RECIPES["WandBolt"] = {
  "seconds": 0.9, "lufs": -22, "fade_out": 0.3, "takes": 3,
  "reverb": {"rt60": 0.5, "wet_db": -9, "damp_hz": 7000, "predelay_ms": 8},
  "layers": {
   "pluck": {"kind": "synth", "prompt": "synthesised celesta pluck: fundamental with partials at 2x, 3.01x and 4.2x, each with its own exponential decay",
             "secs": 0.9, "freqs": [1568, 1760, 2093], "expr": "0.6*exp(-9*t)*sin(2*PI*{f}*t)+0.25*exp(-13*t)*sin(2*PI*2*{f}*t)+0.12*exp(-18*t)*sin(2*PI*3.01*{f}*t)+0.05*exp(-26*t)*sin(2*PI*4.2*{f}*t)", "trim": 0.9},
   "spark": {"kind": "synth", "prompt": "synthesised tiny chime ping two octaves above the pluck, fast decay",
             "secs": 0.5, "freqs": [1568, 1760, 2093], "expr": "0.5*exp(-22*t)*sin(2*PI*4*{f}*t)+0.3*exp(-30*t)*sin(2*PI*6*{f}*t)", "gain_db": -15, "delay_ms": 70, "trim": 0.5},
   "glint": {"kind": "synth", "prompt": "synthesised second chime ping a fifth above the first, fast decay",
             "secs": 0.5, "freqs": [1568, 1760, 2093], "expr": "0.5*exp(-24*t)*sin(2*PI*3*{f}*t)", "gain_db": -19, "delay_ms": 150, "trim": 0.5},
  }}
RECIPES["PlayerHurt"].update({"seconds": 1.5, "fade_out": 0.5, "post": "anull", "post_gain_db": 3,
  "reverb": {"rt60": 1.1, "wet_db": -9, "damp_hz": 3500, "predelay_ms": 18}})
RECIPES["FailSting"].update({"seconds": 7.0, "fade_out": 2.5, "post": "anull",
  "reverb": {"rt60": 4.0, "wet_db": -8, "damp_hz": 3000, "predelay_ms": 30}})
RECIPES["FailSting"]["layers"]["clock"] = {"prompt": "old clock mechanism ticking slower and slower, then stopping with one final heavy clunk, dry, isolated", "secs": 3.0, "filter": "highpass=f=300,lowpass=f=5000", "norm_lufs": -20, "gain_db": -10, "delay_ms": 2600, "trim": 3.0}
RECIPES["SurvivedSting"].update({"seconds": 7.5, "fade_out": 2.5, "post": "anull",
  "reverb": {"rt60": 4.0, "wet_db": -8, "damp_hz": 5000, "predelay_ms": 30}})
# Stinger numbers: the peak must land in the first 60 ms, so the bell strike opens both cards and the rest sits under it.
RECIPES["FailSting"]["layers"]["bell"].update({"delay_ms": 0, "gain_db": 4, "start_db": -24})
RECIPES["FailSting"]["layers"]["brass"].update({"gain_db": -3, "delay_ms": 60})
RECIPES["FailSting"]["layers"]["choir"].update({"gain_db": -8, "delay_ms": 1000})
RECIPES["FailSting"]["layers"]["clock"].update({"gain_db": -14, "delay_ms": 3000})
RECIPES["SurvivedSting"].update({"seconds": 6.5, "fade_out": 2.5})
RECIPES["SurvivedSting"]["reverb"].update({"rt60": 3.0, "wet_db": -10})
RECIPES["SurvivedSting"]["layers"]["bell"].update({"gain_db": 4, "start_db": -24})
RECIPES["SurvivedSting"]["layers"]["choir"].update({"gain_db": -8, "delay_ms": 400})
RECIPES["FailSting"].update({"seconds": 6.0, "fade_out": 2.0})
RECIPES["FailSting"]["reverb"].update({"rt60": 3.0, "wet_db": -10})
RECIPES["FailSting"]["layers"]["bell"].update({"gain_db": 6})
RECIPES["FailSting"]["layers"]["brass"].update({"gain_db": -9})
RECIPES["FailSting"]["layers"]["choir"].update({"gain_db": -11, "trim": 3.0})
RECIPES["FailSting"]["layers"]["clock"].update({"gain_db": -16, "delay_ms": 2400, "trim": 2.6})
RECIPES["SurvivedSting"].update({"seconds": 6.0, "fade_out": 2.0})
RECIPES["SurvivedSting"]["layers"]["bell"].update({"gain_db": 6})
RECIPES["SurvivedSting"]["layers"]["choir"].update({"gain_db": -10, "trim": 3.6})
RECIPES["SurvivedSting"]["layers"]["wind"].update({"trim": 3.5})
RECIPES["FailSting"]["layers"]["bell"].update({"decay": 2.5})
RECIPES["FailSting"]["layers"]["choir"].update({"gain_db": -12, "trim": 2.8})
RECIPES["FailSting"]["layers"]["clock"].update({"delay_ms": 2200})
RECIPES["FailSting"].update({"seconds": 5.6})
RECIPES["SurvivedSting"]["layers"]["bell"].update({"decay": 2.5})
RECIPES["SurvivedSting"]["layers"]["bell"].update({"decay": 4})
RECIPES["SurvivedSting"]["layers"]["choir"].update({"gain_db": -12, "trim": 3.2, "delay_ms": 300})
RECIPES["SurvivedSting"].update({"seconds": 5.6})
# Sting tails (critic round 1): loudnorm lifted the faded tail back up, so regen.py now fades again after it; 8 s files
# so the cathedral tail (measured decay under the file length) rings out to silence.
RECIPES["FailSting"].update({"seconds": 8.0, "fade_out": 3.5})
RECIPES["FailSting"]["reverb"].update({"rt60": 3.0, "wet_db": -10})
RECIPES["SurvivedSting"].update({"seconds": 8.0, "fade_out": 3.5})
RECIPES["SurvivedSting"]["layers"]["wind"].update({"filter": "highpass=f=200,lowpass=f=1500"})
RECIPES["PlayerHurt"]["take_gain_db"] = {2: 1.5}   # audio_check: take 02 sat 3.1 dB under the hit family median (max 3.0)
RECIPES["SurvivedSting"]["layers"]["choir"].update({"trim": 2.4})
RECIPES["SurvivedSting"]["layers"]["wind"].update({"trim": 3.0, "delay_ms": 1200})
RECIPES["FailSting"]["channels"] = 2       # sound-list.csv: the stings are 2-channel Music class files
RECIPES["SurvivedSting"]["channels"] = 2
# PlayerHurt level: the 1.5 s tail dropped its RMS 3+ dB under the hit family median; a wetter hall and a 1.3 s file bring it back.
RECIPES["PlayerHurt"].update({"seconds": 1.3, "fade_out": 0.45, "take_gain_db": {}, "post_gain_db": 5})
RECIPES["PlayerHurt"]["reverb"].update({"wet_db": -5})
