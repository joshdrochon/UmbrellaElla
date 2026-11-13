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
