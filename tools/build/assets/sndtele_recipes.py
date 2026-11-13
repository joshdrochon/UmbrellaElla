"""sndtele lane recipes: one per sound id, in the format of pipeline/audio/build/regen.py (layers -> ffmpeg mix).
Extra key read by sndtele_audio.py: loop_s (a seamless loop of that length). Edit between critic rounds.
Levels: the sound-list telegraph family sits near -18 LUFS and the motion family near -22 LUFS, so every take is
inside its style family's range and within 3 dB RMS of its sound-list family (audio_check --scan)."""



def clk(f, d=0.0, a=1.0, k=40, parts=((1, 0.6, 1), (2.76, 0.4, 1.4), (5.4, 0.25, 1.8)), rise=600, nz=0.0, nk=350, slot=0):
    """ffmpeg aevalsrc term: one struck-metal click at d seconds. Bar partials (ratio, weight, decay factor) with
    their own exponential decay and a few-ms rise, so the strike is sharp but never a 0 ms digital click. nz adds the
    strike's broadband contact noise (a few ms), which is what makes a click read as a hit and not a tone."""
    T = f"(t-{d})"
    body = "+".join(f"{w}*exp(-{round(k * m, 2)}*{T})*sin(2*PI*{round(f * r, 1)}*{T})" for r, w, m in parts)
    if nz:
        body += f"+{nz}*exp(-{nk}*{T})*(random({slot})*2-1)"
    return f"{a}*gt(t\\,{d})*(1-exp(-{T}*{rise}))*({body})"


P2 = ((1, 0.6, 1), (2.76, 0.4, 1.4))


def clicks(*terms):
    return "+".join(terms)


def ratchet(times, f, a0, a1, k=110, nz=0.8, slot=0, parts=P2):
    """A row of ratchet ticks at the given times, level rising from a0 to a1."""
    n = max(1, len(times) - 1)
    return clicks(*[clk(f, round(t, 4), round(a0 + (a1 - a0) * i / n, 3), k, parts, nz=nz, slot=slot) for i, t in enumerate(times)])


def accel(n, dur, ratio=3.0):
    """n tick times over dur seconds, the gaps shrinking by `ratio` from first to last (a ratchet speeding up)."""
    gaps = [ratio ** (-i / max(1, n - 2)) for i in range(n - 1)]
    k = dur / sum(gaps); out = [0.0]
    for g in gaps:
        out.append(out[-1] + g * k)
    return out


def train(rate, f, k, a=1.0, parts=P2, ph=0.0, nz=0.0, slot=0, rise=900):
    """ffmpeg aevalsrc term: the same struck click repeated `rate` times a second (a gear train, steps, blades).
    ph shifts the row in seconds. Pick a rate with a whole number of periods in the loop."""
    T = f"mod(t+{ph}\\,{round(1 / rate, 6)})"
    body = "+".join(f"{w}*exp(-{round(k * m, 2)}*{T})*sin(2*PI*{round(f * r, 1)}*{T})" for r, w, m in parts)
    if nz:
        body += f"+{nz}*exp(-{4 * k}*{T})*(random({slot})*2-1)"
    return f"{a}*(1-exp(-{T}*{rise}))*({body})"


LOW = ((1, 1, 1), (2.1, 0.4, 1.5))          # a knock: wood or a heavy body


def air(f0, f1, dur, slot, jit=0.7, shape="lin"):
    """ffmpeg aevalsrc term: a band of moving air whose centre glides f0 -> f1 Hz over dur seconds (a sine carrier
    with a random-walk phase, i.e. narrow-band noise). shape "u": f0 at both ends, f1 in the middle (a swing)."""
    if shape == "u":   # f(t) = f1 + (f0-f1)*(1-2t/dur)^2
        ph = f"({f1}*t-({f0}-{f1})*{dur}/6*(pow(1-2*t/{dur}\\,3)-1))"
    else:
        ph = f"({f0}*t+({f1}-{f0})*t*t/(2*{dur}))"
    return f"sin(2*PI*{ph}+st({slot + 5}\\,ld({slot + 5})+(random({slot})-0.5)*{jit}))"


# every mix: nothing above the upper-mid register survives (generator layers carry a thin 15-16 kHz line)
TOP = "lowpass=f=9500,lowpass=f=9500,lowpass=f=11000"
HALL = {"rt60": 1.0, "wet_db": -8, "damp_hz": 5000, "predelay_ms": 12}     # owl tells: medium stone hall

RECIPES = {
 # The five owl tells share one shape: a 0.6 s build that ends on its loudest moment, one hard strike, then the hall
 # rings out for 0.7 s. They differ in what builds and what strikes: air into a wing snap (gust), a low swing into
 # one iron talon (talon), a quickening rising ratchet into a bright lock (cast), a ratchet running down into a heavy
 # clack that keeps ticking (rear midpoint), even clock ticks into a chime (double beat).
 # OWL-15: wing gather and load. Air drawn in: one rising rush, then the wing locks back with a hard snap. No ratchet.
 "GustWindup": {
  "seconds": 1.35, "lufs": -16, "post_gain_db": 3, "fade_out": 0.3, "takes": 1, "reverb": HALL, "post": TOP,
  "layers": {
   "intake": {"kind": "synth", "prompt": "synthesised wing-air intake: three bands of moving air gliding up together (0.5 to 2.6 kHz, 0.9 to 4.4 kHz, 1.4 to 6 kHz) over 0.66 s, swelling",
              "secs": 0.74, "expr": f"(0.2+0.8*pow(t/0.66\\,1.5))*(0.5*{air(500, 2600, 0.66, 0)}+0.4*{air(900, 4400, 0.66, 1)}+0.25*{air(1400, 6000, 0.66, 2)})",
              "filter": "afade=t=out:st=0.62:d=0.12", "gain_db": -1, "trim": 0.74, "start_db": -90},
   "heave": {"prompt": "one huge wing drawing back, heavy air sucked inward, slow rising whoosh that swells, dry, isolated, no other sounds",
             "secs": 1.5, "trim": 0.74, "norm_lufs": -20, "gain_db": -9, "filter": "highpass=f=500,lowpass=f=5000,lowpass=f=5000,volume='min(1,0.2+0.8*pow(t/0.62,1.5))':eval=frame,afade=t=out:st=0.62:d=0.12"},
   "snap": {"kind": "synth", "prompt": "synthesised wing lock: a hard canvas-and-brass snap, a burst of air over struck 1.1 kHz brass bar partials, fast decay",
            "secs": 0.3, "expr": clk(1100, 0.0, 1.0, 45, P2, nz=1.8, nk=120, slot=3),
            "filter": "highpass=f=600,lowpass=f=9000", "gain_db": 3, "delay_ms": 640, "trim": 0.3, "start_db": -90},
  }},
 # OWL-18: the EMPTY claw draws back and spreads. A low swing of air down and up again (the arm), ending on one dry
 # iron talon strike.
 "TalonWarning": {
  "seconds": 1.35, "lufs": -16, "post_gain_db": 3, "fade_out": 0.3, "takes": 1, "reverb": HALL, "post": TOP,
  "layers": {
   "swing": {"kind": "synth", "prompt": "synthesised pendulum swoop: two bands of moving air swinging down and back up (1.8 kHz to 0.6 kHz to 1.8 kHz, and 3.0 to 1.0 to 3.0 kHz) over 0.62 s",
             "secs": 0.7, "expr": f"(0.25+0.75*pow(t/0.62\\,1.5))*(0.55*{air(1800, 600, 0.62, 0, shape='u')}+0.35*{air(3000, 1000, 0.62, 1, shape='u')})",
             "filter": "afade=t=out:st=0.6:d=0.1", "gain_db": -1, "trim": 0.7, "start_db": -90},
   "scrape": {"prompt": "iron talons scraping slowly against metal, a rising metallic shing that sharpens, dry, isolated, no other sounds",
              "secs": 1.2, "trim": 0.7, "norm_lufs": -20, "gain_db": -6, "filter": "highpass=f=1500,lowpass=f=8000,lowpass=f=8000,volume='min(1,0.25+0.75*pow(t/0.6,1.5))':eval=frame,afade=t=out:st=0.6:d=0.1"},
   "talon": {"kind": "synth", "prompt": "synthesised iron talon strike: one dry struck-iron click at 2.4 kHz with a second bar partial and contact noise, very fast decay",
             "secs": 0.3, "expr": clk(2400, 0.0, 1.0, 70, P2, nz=2.4, nk=160, slot=3), "gain_db": 4, "delay_ms": 620, "trim": 0.3, "start_db": -90},
  }},
 # OWL-21: a mechanism cast locks its destination. The ratchet winds faster and higher into one bright lock click.
 "CastWarning": {
  "seconds": 1.35, "lufs": -16, "post_gain_db": 3, "fade_out": 0.3, "takes": 1, "reverb": HALL, "post": TOP,
  "layers": {
   "ratchet": {"kind": "synth", "prompt": "synthesised ratchet: 12 struck-steel teeth speeding up over 0.58 s (gaps shrinking threefold), each tooth a little higher (1.5 to 2.6 kHz) and louder, dry with contact noise",
               "secs": 0.66, "expr": clicks(*[clk(round(1500 + 100 * i), round(t, 4), round(0.3 + 0.045 * i, 3), 100, P2, nz=1.2, slot=0) for i, t in enumerate(accel(12, 0.58))]),
               "gain_db": 2, "trim": 0.66},
   "wind": {"prompt": "heavy clockwork ratchet winding up fast, accelerating metal clicks, dry, isolated",
            "secs": 1.0, "trim": 0.7, "norm_lufs": -20, "gain_db": -1, "filter": "highpass=f=1000,lowpass=f=7000,lowpass=f=7000,volume='min(1,0.2+0.8*pow(t/0.6,2))':eval=frame,afade=t=out:st=0.6:d=0.1"},
   "lock": {"kind": "synth", "prompt": "synthesised lock click: one bright struck-brass click at 3.1 kHz with bar partials and a burst of contact noise, short",
            "secs": 0.3, "expr": clk(3100, 0.0, 1.0, 50, P2, nz=2.0, nk=140, slot=3), "gain_db": 3, "delay_ms": 640, "trim": 0.3, "start_db": -90},
  }},
 # OWL-27: the midpoint clack of the rear cast: the safe pause, it must not sound finished. The ratchet runs down,
 # one heavy low clack lands (the loudest moment), and a soft escapement keeps ticking through the tail.
 "RearMidpointClack": {
  "seconds": 1.35, "lufs": -16, "post_gain_db": 3, "fade_out": 0.3, "takes": 1, "reverb": HALL, "post": TOP,
  "layers": {
   "rundown": {"kind": "synth", "prompt": "synthesised ratchet running down: 7 struck-brass teeth slowing over 0.5 s (gaps growing threefold), each a little lower (1.9 to 1.3 kHz), rising in level, dry with contact noise",
               "secs": 0.6, "expr": clicks(*[clk(round(1900 - 100 * i), round(t, 4), round(0.3 + 0.06 * i, 3), 150, P2, nz=1.2, slot=0) for i, t in enumerate(accel(7, 0.5, 1 / 3.0))]),
               "gain_db": 2, "trim": 0.6},
   "tension": {"prompt": "a wound clock spring creaking tighter and tighter, rising strained metal tension that does not release, dry, isolated",
               "secs": 1.0, "trim": 0.7, "norm_lufs": -20, "gain_db": -7, "filter": "highpass=f=900,lowpass=f=7000,volume='min(1,0.2+0.8*pow(t/0.6,2))':eval=frame,afade=t=out:st=0.6:d=0.1"},
   "clack": {"kind": "synth", "prompt": "synthesised heavy clack: struck brass at 1.0 kHz with bar partials over a 380 Hz knock and a burst of contact noise; then four soft even 2 kHz escapement ticks 0.12 s apart",
             "secs": 0.7, "expr": clicks(clk(1000, 0.0, 1.0, 30, nz=2.0, nk=120, slot=3), clk(380, 0.0, 0.6, 36, LOW),
                                         ratchet([0.14, 0.26, 0.38, 0.5], 2000, 0.13, 0.07, k=160, slot=4)), "gain_db": 3, "delay_ms": 640, "trim": 0.7},
  }},
 # OWL-28: the first volley of the double beat (hand XII to III). Four even escapement ticks, a quarter turn of the
 # hand, landing on a chiming tock that rings.
 "ClockBeat": {
  "seconds": 1.35, "lufs": -16, "post_gain_db": 3, "fade_out": 0.3, "takes": 1, "reverb": HALL, "post": "lowpass=f=11000",
  "layers": {
   "ticks": {"kind": "synth", "prompt": "synthesised escapement: four even ticks 0.16 s apart, rising in level (3 kHz bar partials with contact noise, dry)",
             "secs": 0.62, "expr": ratchet([0.0, 0.16, 0.32, 0.48], 3000, 0.4, 0.8, k=160, nz=1.8), "gain_db": 2, "trim": 0.62},
   "gear": {"prompt": "heavy brass clock gear train advancing a quarter turn, whirring clock hand mechanism, dry, isolated",
            "secs": 1.0, "trim": 0.72, "norm_lufs": -20, "gain_db": -10, "filter": "highpass=f=1500,lowpass=f=7000,volume='min(1,0.2+0.8*pow(t/0.6,2))':eval=frame,afade=t=out:st=0.6:d=0.12"},
   "chime": {"kind": "synth", "prompt": "synthesised clock chime tock: a struck bell at 1.32 kHz with bell partials (2.0, 2.4, 3.0, 4.2) and contact noise, ringing 0.4 s",
             "secs": 0.6, "expr": clk(1320, 0.0, 1.0, 8, ((1, 0.6, 1), (2.0, 0.3, 1.3), (2.4, 0.2, 1.6), (3.0, 0.15, 2), (4.2, 0.1, 3)), nz=1.8, nk=160, slot=3),
             "gain_db": 3, "delay_ms": 640, "trim": 0.6, "start_db": -90},
  }},
}

# ---------------------------------------------------------------- motion loops (seamless; sndtele_audio.py loopify)
NEAR = {"rt60": 0.35, "wet_db": -14, "damp_hz": 5000, "predelay_ms": 5}     # the umbrella and Ella are close
RECIPES.update({
 # MOVE-21 rise: the open canopy flutters in the steady updraft.
 "UmbrellaFlap": {
  "loop_s": 3.0, "seconds": 3.0, "lufs": -22, "post_gain_db": 3, "takes": 1, "reverb": NEAR, "post": TOP,
  "layers": {
   "flutter": {"prompt": "cloth umbrella canopy fluttering in a steady updraft, soft waxed canvas flapping gently and continuously, close, dry, no other sounds",
               "secs": 4.0, "trim": 3.5, "norm_lufs": -20, "filter": "highpass=f=250,lowpass=f=6000"},
   "air": {"prompt": "soft steady current of rising air, gentle continuous wind, no gusts, dry",
           "secs": 4.0, "trim": 3.5, "norm_lufs": -20, "gain_db": -10, "filter": "highpass=f=200,lowpass=f=2500"},
  }},
 # MOVE-21 fall: air past a small body, the coat flutters.
 "EllaFallLoop": {
  "loop_s": 3.0, "seconds": 3.0, "lufs": -22, "takes": 1, "reverb": NEAR, "post": TOP,
  "layers": {
   "rush": {"prompt": "air rushing softly past a small falling figure, steady smooth wind rush, continuous, dry, no other sounds",
            "secs": 4.0, "trim": 3.5, "norm_lufs": -20, "filter": "highpass=f=120,lowpass=f=4000"},
   "coat": {"prompt": "a small cloth coat fluttering quickly in falling air, light fabric flapping, continuous, close, dry",
            "secs": 4.0, "trim": 3.5, "norm_lufs": -20, "gain_db": -7, "filter": "highpass=f=400,lowpass=f=5000"},
  }},
 # MOVE-05 fast free fall: both held. A hard roar of air with a thin whistle on top and cloth snapping.
 "FreeFallRush": {
  "loop_s": 3.0, "seconds": 3.0, "lufs": -21, "takes": 1, "reverb": NEAR, "post": TOP,
  "layers": {
   "roar": {"prompt": "fast free fall, a strong roaring rush of air tearing past, intense and steady, continuous, dry, no other sounds",
            "secs": 4.0, "trim": 3.5, "norm_lufs": -20, "filter": "highpass=f=100,lowpass=f=5000"},
   "whistle": {"prompt": "thin airy wind whistle of fast air past an edge, steady, continuous, dry",
               "secs": 4.0, "trim": 3.5, "norm_lufs": -20, "gain_db": -11, "filter": "highpass=f=1200,lowpass=f=5000"},
   "snap": {"prompt": "cloth snapping rapidly in violent wind, fast fabric flapping, continuous, close, dry",
            "secs": 4.0, "trim": 3.5, "norm_lufs": -20, "gain_db": -8, "filter": "highpass=f=400,lowpass=f=6000"},
  }},
 # ANIM-06 hover: huge slow wingbeats, felt more than heard, a brass joint creak on each stroke.
 "OwlWingLoop": {
  "loop_s": 4.0, "seconds": 4.0, "lufs": -25, "takes": 1, "post": TOP,
  "reverb": {"rt60": 1.5, "wet_db": -10, "damp_hz": 2500, "predelay_ms": 20},
  "layers": {
   "wings": {"prompt": "slow heavy wing flaps of a very large bird, a feathery whoosh and soft whump of air on each beat, steady slow rhythm, close, dry, no other sounds",
             "secs": 5.0, "trim": 4.5, "norm_lufs": -20, "gain_db": -4, "filter": "highpass=f=100,highshelf=f=300:g=7,lowpass=f=2200"},
   "creak": {"prompt": "quiet old brass joints creaking slowly, soft low mechanical creak, steady, dry",
             "secs": 5.0, "trim": 4.5, "norm_lufs": -20, "gain_db": -2, "filter": "highpass=f=350,lowpass=f=3000"},
  }},
 # OWL-22: the chain pays out. Rattling links over a pulley, each link a sharp clink.
 "ChainTravel": {
  "loop_s": 2.0, "seconds": 2.0, "lufs": -22, "post_gain_db": 2.5, "takes": 1, "post": TOP,
  "reverb": {"rt60": 0.7, "wet_db": -13, "damp_hz": 5000, "predelay_ms": 10},
  "layers": {
   "chain": {"prompt": "heavy iron chain paying out fast over a metal pulley, rattling links, steady, continuous, dry, no other sounds",
             "secs": 3.0, "trim": 2.5, "norm_lufs": -20, "filter": "highpass=f=500,lowpass=f=8000"},
   "links": {"kind": "synth", "prompt": "synthesised chain links: struck-iron clinks 12 per second, alternating 1.9 and 2.3 kHz bar partials, very fast decay",
             "secs": 2.5, "expr": "(1-exp(-mod(t\\,1/6)*900))*exp(-120*mod(t\\,1/6))*(0.6*sin(2*PI*1900*t)+0.4*sin(2*PI*5244*t))"
                                  "+(1-exp(-mod(t+1/12\\,1/6)*900))*exp(-120*mod(t+1/12\\,1/6))*(0.5*sin(2*PI*2300*t)+0.35*sin(2*PI*6348*t))",
             "gain_db": -6, "trim": 2.5, "start_db": -90},
  }},
})

# ---------------------------------------------------------------- P1: red travel, enemies, hazards
BIGHALL = {"rt60": 1.0, "wet_db": -11, "damp_hz": 3000, "predelay_ms": 20}  # enemies and red shots: large stone hall
ROOM = {"rt60": 0.6, "wet_db": -13, "damp_hz": 5000, "predelay_ms": 8}      # clockwork: medium room
DARK = "lowpass=f=6000,lowpass=f=8000"
RECIPES.update({
 # OWL-11 red travel: a low spinning gear, 24 teeth a second, dark and metallic.
 "OwlBoltTravelLoop": {
  "loop_s": 2.0, "seconds": 2.0, "lufs": -21, "post_gain_db": -1.5, "takes": 1, "post": DARK,
  "reverb": {"rt60": 0.8, "wet_db": -14, "damp_hz": 3000, "predelay_ms": 12},
  "layers": {
   "teeth": {"kind": "synth", "prompt": "synthesised spinning gear: 24 dark struck-iron teeth a second (380 Hz and 1.05 kHz bar partials), with a slow 2 Hz wobble",
             "secs": 2.5, "expr": f"(0.8+0.2*sin(2*PI*2*t))*({train(24, 380, 150, 1.0, nz=0.3)})", "gain_db": 0, "trim": 2.5, "start_db": -90},
   "whirr": {"prompt": "low spinning clockwork gear whirr, dark metallic hum of a heavy flywheel, steady, continuous, dry, no other sounds",
             "secs": 3.0, "trim": 2.5, "norm_lufs": -20, "gain_db": -8, "filter": "highpass=f=120,lowpass=f=2500"},
  }},
 # COM-14 Roadwarden brace / aim: a heavy iron brace clank, then four slow crank ticks, rising.
 "WardenWarning": {
  "seconds": 1.3, "lufs": -18, "post_gain_db": 4, "fade_out": 0.3, "takes": 1, "reverb": BIGHALL, "post": DARK,
  "layers": {
   "brace": {"kind": "synth", "prompt": "synthesised brace clank: struck iron at 520 Hz with bar partials over a 130 Hz knock, contact noise; then four slow crank ticks at 800 Hz, 0.2 s apart, rising",
             "secs": 1.1, "expr": clicks(clk(520, 0.0, 1.0, 22, rise=1500, nz=1.2, nk=120, slot=3), clk(130, 0.0, 0.6, 25, LOW, rise=1500),
                                         ratchet([0.2, 0.4, 0.6, 0.8], 800, 0.35, 0.6, k=60, slot=4)), "gain_db": 0, "trim": 1.1},
   "iron": {"prompt": "a heavy iron crossbow mechanism braced and cranked slowly, dark metal creak and strain, dry, isolated, no other sounds",
            "secs": 1.5, "trim": 1.0, "norm_lufs": -20, "gain_db": -9, "filter": "highpass=f=150,lowpass=f=3000"},
  }},
 # COM-14 Roadwarden movement: slow armoured steps, a low thud and an iron buckle on each.
 "WardenMove": {
  "loop_s": 2.4, "seconds": 2.4, "lufs": -21, "takes": 1, "post": DARK,
  "reverb": {"rt60": 0.9, "wet_db": -13, "damp_hz": 3000, "predelay_ms": 15},
  "layers": {
   "steps": {"kind": "synth", "prompt": "synthesised armoured steps every 0.6 s: a 95 Hz boot thud with an iron buckle clank (640 Hz bar partials) 40 ms after it",
             "secs": 2.9, "expr": clicks(train(1 / 0.6, 95, 28, 0.45, LOW, nz=0.5), train(1 / 0.6, 640, 40, 0.9, P2, ph=-0.04 + 0.6, nz=0.5, slot=1)),
             "gain_db": 0, "trim": 2.9, "start_db": -90},
   "kit": {"prompt": "iron armour and equipment rattling on a slowly marching soldier, buckles and plates shifting, steady, dry, no voice",
           "secs": 3.5, "trim": 2.9, "norm_lufs": -20, "gain_db": -5, "filter": "highpass=f=300,lowpass=f=4000"},
  }},
 # COM-15 Floodstrider settle / brace: two stilts land one after the other, the frame groans down as it takes the weight.
 "FloodWarning": {
  "seconds": 1.4, "lufs": -18, "post_gain_db": 2, "fade_out": 0.3, "takes": 1, "reverb": BIGHALL, "post": DARK,
  "layers": {
   "settle": {"kind": "synth", "prompt": "synthesised stilts settling: two wooden-iron clunks 0.16 s apart (300 Hz and 380 Hz bar partials over low knocks), then a groan of three partials sliding down a fourth over 0.8 s",
              "secs": 1.2, "expr": clicks(clk(300, 0.0, 1.0, 26, rise=1500, nz=1.0, nk=120, slot=3), clk(110, 0.0, 0.6, 25, LOW, rise=1500),
                                          clk(380, 0.16, 0.9, 26, nz=1.0, nk=120, slot=3), clk(140, 0.16, 0.5, 25, LOW),
                                          "0.22*gt(t\\,0.25)*exp(-2.2*(t-0.25))*(0.5*sin(2*PI*(640*t-100*t*t))+0.3*sin(2*PI*(1010*t-158*t*t))+0.2*sin(2*PI*(1490*t-233*t*t)))*(0.7+0.3*sin(2*PI*23*t))"),
              "gain_db": 0, "trim": 1.2},
   "creak": {"prompt": "tall wooden and iron stilts creaking as they settle under a heavy weight, low strained groan, dry, isolated, no other sounds",
             "secs": 1.5, "trim": 1.1, "norm_lufs": -20, "gain_db": -9, "filter": "highpass=f=150,lowpass=f=3000"},
  }},
 # COM-15 Floodstrider movement: four stilts walking, alternating wooden knocks with a joint creak between.
 "FloodStiltMove": {
  "loop_s": 3.0, "seconds": 3.0, "lufs": -21, "takes": 1, "post": DARK,
  "reverb": {"rt60": 0.9, "wet_db": -13, "damp_hz": 3000, "predelay_ms": 15},
  "layers": {
   "stilts": {"kind": "synth", "prompt": "synthesised stilt steps every 0.75 s, alternating 330 Hz and 410 Hz wooden-iron knocks over low thuds",
              "secs": 3.5, "expr": clicks(train(1 / 1.5, 330, 30, 1.0, P2, nz=0.5), train(1 / 1.5, 120, 28, 0.6, LOW),
                                          train(1 / 1.5, 410, 30, 0.9, P2, ph=0.75, nz=0.5, slot=1), train(1 / 1.5, 150, 28, 0.5, LOW, ph=0.75)),
              "gain_db": 0, "trim": 3.5, "start_db": -90},
   "joints": {"prompt": "slow walking machine on tall wooden stilts, iron joints creaking between heavy steps, steady, dry, no other sounds",
              "secs": 4.0, "trim": 3.5, "norm_lufs": -20, "gain_db": -9, "filter": "highpass=f=250,lowpass=f=3500"},
  }},
 # COM-16 Sky Courier flight: propeller blades, 32 soft low beats a second, a wooden flutter on top.
 "CourierFlightLoop": {
  "loop_s": 2.0, "seconds": 2.0, "lufs": -21, "post_gain_db": -1.5, "takes": 1, "post": DARK,
  "reverb": {"rt60": 0.7, "wet_db": -15, "damp_hz": 3000, "predelay_ms": 12},
  "layers": {
   "blades": {"kind": "synth", "prompt": "synthesised propeller: 32 soft blade beats a second (260 Hz and 720 Hz partials), with a slow 1.5 Hz sway",
              "secs": 2.5, "expr": f"(0.8+0.2*sin(2*PI*1.5*t))*({train(32, 260, 120, 1.0, nz=0.6)})", "gain_db": 0, "trim": 2.5, "start_db": -90},
   "prop": {"prompt": "small wooden propellers spinning steadily, soft fluttering whirr of a clockwork flying machine, continuous, dry, no other sounds",
            "secs": 3.0, "trim": 2.5, "norm_lufs": -20, "gain_db": -7, "filter": "highpass=f=200,lowpass=f=3500"},
  }},
 # COM-16 Courier hover / aim: a catch clicks and the propeller spins up, blade beats quickening from 14 to 46 a second.
 "CourierWarning": {
  "seconds": 1.3, "lufs": -18, "fade_out": 0.3, "takes": 1, "reverb": BIGHALL, "post": DARK,
  "layers": {
   "spinup": {"kind": "synth", "prompt": "synthesised hover catch (struck brass at 700 Hz, contact noise), then a propeller spinning up: blade beats quickening from 14 to 46 a second over 0.9 s (300 Hz and 830 Hz partials), rising",
              "secs": 1.0, "expr": clicks(clk(700, 0.0, 0.9, 30, rise=1500, nz=1.2, nk=140, slot=3),
                                          "(0.3+0.7*t)*exp(-5*mod(14*t+17.8*t*t\\,1))*(0.5*sin(2*PI*300*t)+0.35*sin(2*PI*830*t)+0.5*sin(2*PI*150*t))"),
              "filter": "afade=t=out:st=0.94:d=0.06", "gain_db": 0, "trim": 1.0},
   "prop": {"prompt": "a small wooden propeller spinning up faster and faster, rising clockwork whirr, dry, isolated, no other sounds",
            "secs": 1.5, "trim": 1.0, "norm_lufs": -20, "gain_db": -9, "filter": "highpass=f=200,lowpass=f=3500,afade=t=out:st=0.94:d=0.06"},
  }},
 # HAZ-20 shutter crank / tension: one heavy crank clack, then the pawl rattles down six quick teeth as the spring
 # takes the load. The first strike is the loudest (the clockwork family starts sharp and dies fast).
 "ShutterWarning": {
  "seconds": 1.0, "lufs": -19, "post_gain_db": 4, "fade_out": 0.25, "takes": 1, "reverb": ROOM, "post": TOP,
  "layers": {
   "crank": {"kind": "synth", "prompt": "synthesised crank: one heavy escapement clack (1.6 kHz bar partials over a 240 Hz body, contact noise), then six quick pawl ticks 0.07 s apart, each softer and a little higher",
             "secs": 0.7, "expr": clicks(clk(1600, 0.0, 1.0, 60, ((1, 0.6, 1), (2.76, 0.4, 1.4), (0.15, 0.5, 0.8)), rise=2500, nz=1.4),
                                         *[clk(1700 + 60 * i, round(0.07 * (i + 1), 3), round(0.5 - 0.065 * i, 3), 120, P2, nz=1.2, slot=1) for i in range(6)]),
             "gain_db": 0, "trim": 0.7},
   "spring": {"prompt": "an old iron crank being wound against a stiff spring, strained metal creak, dry, isolated, no other sounds",
              "secs": 1.5, "trim": 0.6, "decay": 5, "norm_lufs": -20, "gain_db": -12, "filter": "highpass=f=600,lowpass=f=6000"},
  }},
 # HAZ-21 bellows nozzle pressure: the leather bag fills, air climbing in the nozzle, then holds its breath.
 "BellowsWarning": {
  "seconds": 1.3, "lufs": -19, "fade_out": 0.35, "takes": 1, "post": "lowpass=f=5000,lowpass=f=6000",
  "reverb": {"rt60": 1.0, "wet_db": -12, "damp_hz": 3000, "predelay_ms": 15},
  "layers": {
   "fill": {"kind": "synth", "prompt": "synthesised bellows filling: two low bands of moving air climbing over 0.85 s (220 to 900 Hz and 420 to 1700 Hz), swelling",
            "secs": 0.85, "expr": f"(0.3+0.7*pow(t/0.85\\,1.2))*(0.6*{air(220, 900, 0.85, 0, jit=0.5)}+0.4*{air(420, 1700, 0.85, 1, jit=0.5)})",
            "filter": "afade=t=out:st=0.77:d=0.08", "gain_db": -3, "trim": 0.85, "start_db": -90},
   "leather": {"prompt": "large leather forge bellows slowly filling with air, deep breath in, creaking leather, dry, isolated, no other sounds",
               "secs": 1.5, "trim": 0.85, "norm_lufs": -20, "gain_db": -6, "filter": "highpass=f=120,lowpass=f=3000,volume='min(1,0.3+0.7*pow(t/0.78,1.2))':eval=frame,afade=t=out:st=0.77:d=0.08"},
  }},
})
