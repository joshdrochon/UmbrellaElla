"""sndtele lane recipes: one per sound id, in the format of pipeline/audio/build/regen.py (layers -> ffmpeg mix).
Layer kinds: an ElevenLabs layer (prompt, secs), or `py`: a function that renders the layer from sndtele_synth.py
sources (struck metal and wood, moving air, creaks). Extra recipe keys read by sndtele_audio.py: loop_s (a seamless
loop of that length) and loop_tail (how much longer the mix is rendered before it is folded). Edit between critic rounds.
Levels: the sound-list telegraph family sits near -18 LUFS and the motion family near -21 LUFS, so every take is
inside its style family's range and within 3 dB RMS of its sound-list family (audio_check --scan)."""
import math
import random

from sndtele_synth import (BAR, BAR2, BELL, KNOCK, PLATE, SR, accel, add, air, bed, buf, burst, creak, nrm, ramp,
                           rotate, strike, swell, teeth)

TOP = "lowpass=f=9500,lowpass=f=9500,lowpass=f=11000"      # generator layers carry a thin 15-16 kHz line
DARK = "lowpass=f=6000,lowpass=f=8000"
HALL = {"rt60": 1.0, "wet_db": -8, "damp_hz": 5000, "predelay_ms": 12}      # owl tells: medium stone hall
BIGHALL = {"rt60": 0.9, "wet_db": -9, "damp_hz": 3000, "predelay_ms": 20}   # enemies: large stone hall
ROOM = {"rt60": 0.6, "wet_db": -12, "damp_hz": 5000, "predelay_ms": 8}      # clockwork: medium room
NEAR = {"rt60": 0.35, "wet_db": -14, "damp_hz": 5000, "predelay_ms": 5}     # the umbrella and Ella are close


def build_env(dur, floor=0.2, power=2):
    """ffmpeg volume filter for a generated bed under a build: audible from the first sample, rising to dur, then out."""
    return (f"volume='min(1,{floor}+{1 - floor}*pow(t/{dur},{power}))':eval=frame,"
            f"afade=t=out:st={dur}:d=0.08")


def loop_bed(loop_s, tail):
    """ffmpeg fades for a generated bed in a folded loop (equal power, like sndtele_synth.bed)."""
    return f"afade=t=in:d={tail}:curve=qsin,afade=t=out:st={loop_s}:d={tail}:curve=qsin"


# ---------------------------------------------------------------- owl tells
# One shape: a 0.66 s build that ends on its loudest moment, then the hall rings out. Each differs in what builds and
# what ends it: air heaves into a wing snap (gust), a metal scrape and knuckles into a catch (talon), a slowing
# escapement into a two-part latch (cast), a dry clack then a ratchet that is cut off mid-wind (rear midpoint),
# a quickening tick-tock into a clipped ting (double beat).
def gust_py():
    s = buf(1.0)
    for i, (t0, d, lv) in enumerate(((0.0, 0.2, 0.45), (0.2, 0.2, 0.7), (0.4, 0.27, 1.0))):
        up = ramp(d, 0.15, 1.0, 1.5, 0.04)
        flut = lambda t, up=up: up(t) * (0.72 + 0.28 * math.sin(2 * math.pi * 27 * t))     # feathers
        add(s, nrm(air(d, lambda t, i=i, d=d: 500 + 140 * i + (1900 + 500 * i) * t / d, 1.6, flut, seed=10 + i)), t0, lv)
        add(s, nrm(air(d, lambda t, i=i, d=d: 1100 + 300 * i + (3200 + 700 * i) * t / d, 1.8, flut, seed=20 + i)), t0, lv * 0.6)
    add(s, strike(1100, 45, BAR2, nz=1.8, nz_decay=120), 0.67, 1.3)                      # the wing locks back
    add(s, nrm(air(0.09, 600, 0.9, burst(0.09, 0.003, 45), seed=31)), 0.67, 1.2)
    return s


def talon_py():
    s = buf(1.0)
    add(s, nrm(creak(0.64, 1400, 2600, ((1, 0.6), (1.48, 0.35), (2.2, 0.2)), rough=120,
                     amp=ramp(0.64, 0.15, 1.0, 1.6, 0.03), seed=3)), 0.0, 0.5)             # iron drawn across iron
    for i, t in enumerate(accel(5, 0.5, 1 / 2.5)):                                        # knuckles slow and fall as it pulls away
        add(s, strike(2600 - 220 * i, 160, BAR2, nz=1.2, seed=i), 0.06 + t, 0.5 - 0.05 * i)
    add(s, nrm(air(0.2, lambda t: 1800 - 1200 * t / 0.2, 1.4, burst(0.2, 0.012, 70), seed=41)), 0.64, 0.6)   # hollow breath: the claw is empty
    return s


def cast_py():
    s = buf(1.0)
    for i, t in enumerate(accel(8, 0.54, 1 / 3.0)):                                       # the escapement slows
        add(s, strike(2400 - 100 * i, 130, BAR2, nz=1.2, seed=i), t, 0.3 + 0.07 * i)
    add(s, strike(420, 30, BAR, nz=2.0, nz_decay=90), 0.66, 1.2)                          # bolt-throw clunk
    add(s, strike(140, 30, KNOCK, nz=0), 0.66, 0.6)
    add(s, strike(3300, 14, BELL, nz=0.4), 0.74, 0.5)                                     # locked: a small bell ping
    return s


def rear_py():
    s = buf(1.0)
    add(s, nrm(air(0.66, lambda t: 700 + 500 * t / 0.66, 1.2, ramp(0.66, 0.3, 1.0, 1.2, 0.02), seed=51)), 0.0, 0.6)   # air held tight
    add(s, strike(2900, 14, BELL, nz=0.3), 0.2, 0.35)                                     # a hanging partial that never resolves
    for i in range(9):                                                                    # slow even ticks, then nothing
        add(s, strike(1700 + 40 * (i % 3), 110, BAR2, nz=1.0, seed=i), 0.05 + 0.07 * i * 1.6, 0.35 + 0.05 * i)
    return s


def clockbeat_py():
    s = buf(1.0)
    for i, t in enumerate(accel(8, 0.56, 1.8)):                                           # tick-tock, quickening
        if i % 2 == 0:
            add(s, strike(2300, 110, BAR2, nz=1.0, seed=i), t, 0.4 + 0.06 * i)
        else:
            add(s, strike(1300, 80, BAR2, nz=0.9, seed=i), t, 0.5 + 0.06 * i)
            add(s, strike(380, 70, KNOCK, nz=0), t, 0.4)
    add(s, strike(3300, 55, ((1, 0.7, 1), (2.4, 0.3, 1.5)), nz=1.0, nz_decay=250), 0.67, 1.3)   # a clipped ting
    return s


RECIPES = {
 # OWL-15: wing gather and load. Three slowing heaves of air drawn in, each bigger, then the wing locks back.
 "GustWindup": {
  "seconds": 1.35, "lufs": -16, "post_gain_db": 3, "fade_out": 0.3, "takes": 1, "reverb": HALL, "post": TOP,
  "layers": {
   "wing": {"kind": "py", "fn": gust_py, "prompt": "synthesised wing gather: three slowing heaves of air drawn in, each higher and bigger with a feather flutter (two gliding air bands, 0.5-2.9 kHz and 1.1-5 kHz), then a hard canvas-and-brass wing lock (struck 1.1 kHz bar partials, a burst of air)"},
   "heave": {"prompt": "one huge wing drawing back, heavy air sucked inward, slow rising whoosh that swells, dry, isolated, no other sounds",
             "secs": 1.5, "trim": 0.75, "norm_lufs": -20, "gain_db": -12, "filter": "highpass=f=500,lowpass=f=5000,lowpass=f=5000," + build_env(0.64, 0.2, 1.5)},
  }},
 # OWL-18: the EMPTY claw draws back and spreads. Iron scrapes upward, five knuckles click open faster and faster,
 # and the claw catches open with one hard high click.
 "TalonWarning": {
  "seconds": 1.35, "lufs": -16, "post_gain_db": 3, "fade_out": 0.3, "takes": 1, "reverb": HALL, "post": TOP,
  "layers": {
   "claw": {"kind": "py", "fn": talon_py, "prompt": "synthesised empty claw drawing back: a rising iron scrape (three rough partials gliding 1.4 to 2.6 kHz), five knuckle clicks quickening and rising (1.9 to 2.5 kHz), then one hard high catch click (2.7 kHz bar partials over a damped plate, contact noise)"},
   "scrape": {"prompt": "iron talons scraping slowly against metal, a rising metallic shing that sharpens, dry, isolated, no other sounds",
              "secs": 1.2, "trim": 0.75, "norm_lufs": -20, "gain_db": -12, "filter": "highpass=f=1500,lowpass=f=8000,lowpass=f=8000," + build_env(0.62, 0.25, 1.5)},
  }},
 # OWL-21: a mechanism cast locks its destination. The escapement slows as it settles on the target, then a
 # two-part latch: a heavy bolt-throw clunk and a small bell ping.
 "CastWarning": {
  "seconds": 1.35, "lufs": -16, "post_gain_db": 5, "fade_out": 0.3, "takes": 1, "reverb": HALL, "post": TOP,
  "layers": {
   "latch": {"kind": "py", "fn": cast_py, "prompt": "synthesised lock-on: eight escapement ticks slowing and falling in pitch (2.4 to 1.7 kHz) while rising in level, then a heavy bolt-throw clunk (420 Hz bar partials over a 140 Hz knock, contact noise) and a small bell ping (3.3 kHz bell partials) 80 ms later"},
   "chain": {"prompt": "iron chain links pulled taut, short rattle of a tightening chain, dry, isolated, no other sounds",
             "secs": 1.0, "trim": 0.75, "norm_lufs": -20, "gain_db": -8, "filter": "highpass=f=900,lowpass=f=8000," + build_env(0.62, 0.2, 2)},
  }},
 # OWL-27: the midpoint clack of the rear cast: the safe pause, it must not sound finished. One dry clack, then the
 # ratchet winds again, faster and higher, and is cut off mid-wind. No release, no resolved ring.
 "RearMidpointClack": {
  "seconds": 1.35, "lufs": -16, "post_gain_db": 3, "fade_out": 0.3, "takes": 1, "reverb": HALL, "post": TOP,
  "layers": {
   "clack": {"kind": "py", "fn": rear_py, "prompt": "synthesised midpoint clack: one dry damped clack (900 Hz plate partials, contact noise), then eleven ratchet teeth winding faster, higher (1.5 to 2.5 kHz) and louder, cut off on the last tooth with no release strike"},
   "tension": {"prompt": "a wound clock spring creaking tighter and tighter, rising strained metal tension that does not release, dry, isolated",
               "secs": 1.0, "trim": 0.75, "norm_lufs": -20, "gain_db": -11, "filter": "highpass=f=900,lowpass=f=7000," + build_env(0.64, 0.2, 2)},
  }},
 # OWL-28: the first volley of the double beat (hand XII to III). A quickening tick-tock, two pitches, landing on
 # a short clipped ting: the first of two.
 "ClockBeat": {
  "seconds": 1.35, "lufs": -16, "post_gain_db": 5, "fade_out": 0.3, "takes": 1, "reverb": HALL, "post": TOP,
  "layers": {
   "beat": {"kind": "py", "fn": clockbeat_py, "prompt": "synthesised clock beat: a quickening tick-tock, eight alternating strikes (a 2.3 kHz tick, a 1.3 kHz tock on a 380 Hz knock) rising in level, landing on a short clipped ting (3.3 kHz, fast decay)"},
   "gear": {"prompt": "heavy brass clock gear train advancing a quarter turn, whirring clock hand mechanism, dry, isolated",
            "secs": 1.0, "trim": 0.75, "norm_lufs": -20, "gain_db": -8, "filter": "highpass=f=1000,lowpass=f=6000," + build_env(0.62, 0.2, 2)},
  }},
}


# ---------------------------------------------------------------- enemy and hazard tells
# The enemy family starts sharp (attack under 25 ms) and is dark and metallic. Each warning opens on a brace strike,
# builds, and ends on a catch a little louder than the opening, so the end is the loudest moment and the hall tail
# dies inside the file.
def warden_py():
    s = buf(1.2)
    add(s, strike(520, 26, BAR, nz=1.4, nz_decay=120, rise=0.0008), 0.0, 0.95)            # the brace
    add(s, strike(130, 28, KNOCK, nz=0, rise=0.0008), 0.0, 0.6)
    for i, t in enumerate(accel(7, 0.66, 2.5)):                                           # the crank tightens
        add(s, strike(700 + 65 * i, 70, BAR2, nz=1.0, seed=i), 0.18 + t, 0.3 + 0.07 * i)
    add(s, strike(620, 22, BAR, nz=1.8, nz_decay=100), 0.95, 1.1)                         # the catch: aimed
    add(s, strike(150, 26, KNOCK, nz=0), 0.95, 0.75)
    return s


def flood_py():
    s = buf(1.2)
    add(s, strike(300, 30, BAR, nz=2.6, nz_decay=160, rise=0.0008), 0.0, 1.2)            # two stilts land
    add(s, strike(110, 28, KNOCK, nz=0, rise=0.0008), 0.0, 0.75)
    add(s, strike(380, 30, BAR, nz=1.2, nz_decay=120), 0.14, 0.75)
    add(s, strike(140, 28, KNOCK, nz=0), 0.14, 0.45)
    add(s, nrm(creak(0.7, 240, 430, ((1, 0.6), (1.5, 0.35), (2.4, 0.25), (3.3, 0.15)), rough=35,
                     amp=ramp(0.7, 0.1, 1.0, 1.4, 0.03), seed=5)), 0.24, 0.5)              # the frame groans upward
    for i, t in enumerate(accel(4, 0.5, 2.0)):
        add(s, strike(900 + 80 * i, 90, BAR2, nz=1.0, seed=i), 0.4 + t, 0.25 + 0.07 * i)
    add(s, strike(260, 24, PLATE, nz=1.8, nz_decay=80), 0.95, 1.15)                       # braced: a wooden thock
    add(s, strike(820, 40, BAR2, nz=0.5), 0.95, 0.5)
    add(s, strike(105, 26, KNOCK, nz=0), 0.95, 0.65)
    return s


def courier_warn_py():
    s = buf(1.2)
    add(s, strike(700, 40, BAR2, nz=1.5, rise=0.0008), 0.0, 1.0)                          # hover catch
    add(s, strike(170, 35, KNOCK, nz=0, rise=0.0008), 0.0, 0.5)
    t, i = 0.1, 0
    while t < 0.93:                                                                       # the propeller spins up
        u = (t - 0.1) / 0.83
        add(s, nrm(air(0.03, 300 + 500 * u, 1.0, burst(0.03, 0.004, 90), seed=40 + i)), t, 0.25 + 0.45 * u)
        add(s, strike(round(380 + 420 * u), 170, KNOCK, nz=0.3, seed=i % 3), t, 0.2 + 0.4 * u)
        t += 1 / (10 + 34 * u)
        i += 1
    add(s, strike(900, 35, BAR, nz=2.0, nz_decay=110), 0.96, 1.2)                         # ratchet catch: aimed
    add(s, strike(180, 30, KNOCK, nz=0), 0.96, 0.65)
    return s


def shutter_py():
    body = ((1, 0.6, 1), (2.76, 0.4, 1.4), (0.15, 0.5, 0.8))
    s = buf(1.0)
    add(s, strike(1600, 60, body, nz=1.4, rise=0.0006), 0.0, 1.0)                         # the crank bites
    for i, t in enumerate(accel(10, 0.66, 3.0)):                                          # and speeds up
        add(s, strike(1500 + 85 * i, 120, BAR2, nz=1.2, seed=i), 0.1 + t, 0.35 + 0.05 * i)
    add(s, nrm(creak(0.74, 480, 900, rough=45, amp=ramp(0.74, 0.1, 1.0, 1.6, 0.03), seed=7)), 0.08, 0.35)   # spring strain
    add(s, strike(2000, 50, ((1, 0.6, 1), (2.76, 0.4, 1.4), (0.15, 0.6, 0.8)), nz=1.8), 0.86, 1.15)   # full tension
    return s


def bellows_py():
    s = buf(1.7)
    add(s, nrm(air(0.07, 300, 0.8, burst(0.07, 0.004, 40), seed=1)), 0.0, 0.45)            # the bag jerks open
    add(s, strike(95, 30, KNOCK, nz=0.5, nz_decay=80, rise=0.003), 0.0, 0.45)
    d = 0.65                                                                                 # one long swell: pressure builds in the nozzle
    add(s, nrm(creak(d, 100, 165, ((1, 0.6), (2, 0.4), (3, 0.3), (4.1, 0.2)), rough=22,
                     amp=ramp(d, 0.05, 1.0, 2.2, 0.05), seed=2)), 0.08, 0.8)
    add(s, nrm(air(d, lambda t: 900 + 2200 * (t / d) ** 1.4, 8.0, ramp(d, 0.04, 1.0, 2.4, 0.05), seed=3)), 0.08, 0.8)
    add(s, nrm(air(d, lambda t: 400 + 800 * (t / d) ** 1.2, 3.0, ramp(d, 0.05, 1.0, 2.0, 0.05), seed=5)), 0.08, 0.6)
    add(s, nrm(air(d, lambda t: 700 + 2000 * (t / d) ** 1.3, 40.0, ramp(d, 0.1, 1.0, 1.8, 0.03), seed=11)), 0.08, 0.9)   # narrow rising whistle through the stone gap
    add(s, strike(430, 40, KNOCK, nz=0.3), 0.74, 0.9)                                          # valve knock at the peak
    add(s, nrm(air(0.55, lambda t: 2800 - 2000 * t / 0.55, 3.0, burst(0.55, 0.01, 6), seed=9)), 0.78, 0.5)   # the pressure lets go, an open-air tail
    return s


RECIPES.update({
 # COM-14 Roadwarden brace / aim: an iron brace clank, the crank tightens (seven ticks, quickening, rising), a catch.
 "WardenWarning": {
  "seconds": 2.2, "lufs": -18, "post_gain_db": 2, "fade_out": 0.6, "takes": 1, "reverb": BIGHALL, "post": DARK,
  "layers": {
   "brace": {"kind": "py", "fn": warden_py, "prompt": "synthesised brace and aim: a struck-iron brace clank (520 Hz bar partials over a 130 Hz knock), seven crank ticks quickening and rising (700 to 1090 Hz), then a heavier catch clank (620 Hz over 150 Hz)"},
   "iron": {"prompt": "a heavy iron crossbow mechanism braced and cranked slowly, dark metal creak and strain, dry, isolated, no other sounds",
            "secs": 1.5, "trim": 1.0, "norm_lufs": -20, "gain_db": -11, "filter": "highpass=f=150,lowpass=f=3000,afade=t=out:st=0.9:d=0.1"},
  }},
 # COM-15 Floodstrider settle / brace: two stilts land, the frame groans upward under four tightening ticks, and it
 # braces with a wooden thock.
 "FloodWarning": {
  "seconds": 2.2, "lufs": -18, "post_gain_db": 2, "fade_out": 0.6, "takes": 1, "reverb": BIGHALL, "post": DARK,
  "layers": {
   "settle": {"kind": "py", "fn": flood_py, "prompt": "synthesised settle and brace: two stilt clunks 0.14 s apart (300 and 380 Hz bar partials over low knocks), a frame groan gliding up (four rough partials from 240 to 430 Hz) under four tightening ticks, then a wooden brace thock (260 Hz plate over a 105 Hz knock)"},
   "creak": {"prompt": "tall wooden and iron stilts creaking as they settle under a heavy weight, low strained groan, dry, isolated, no other sounds",
             "secs": 1.5, "trim": 1.0, "norm_lufs": -20, "gain_db": -11, "filter": "highpass=f=150,lowpass=f=3000,afade=t=out:st=0.9:d=0.1"},
  }},
 # COM-16 Courier hover / aim: a hover catch, the propeller spins up (blade beats 10 to 44 a second, rising), a
 # ratchet catch.
 "CourierWarning": {
  "seconds": 1.8, "lufs": -18, "post_gain_db": 2, "fade_out": 0.7, "takes": 1, "reverb": BIGHALL, "post": DARK,
  "layers": {
   "spinup": {"kind": "py", "fn": courier_warn_py, "prompt": "synthesised hover and aim: a hover catch (700 Hz bar partials over a knock), a propeller spinning up (blade beats quickening from 10 to 44 a second, each a chop of air and a wooden tick rising 380 to 800 Hz), then a hard ratchet catch (900 Hz bar partials over a 180 Hz knock)"},
   "prop": {"prompt": "a small wooden propeller spinning up faster and faster, rising clockwork whirr, dry, isolated, no other sounds",
            "secs": 1.5, "trim": 1.45, "norm_lufs": -20, "gain_db": -11, "filter": "highpass=f=200,lowpass=f=3500,afade=t=out:st=0.9:d=0.5"},
  }},
 # HAZ-20 shutter crank / tension: the crank bites, ten teeth speed up and climb while the spring groans upward,
 # and it stops at full tension on the hardest click.
 "ShutterWarning": {
  "seconds": 1.5, "lufs": -19, "post_gain_db": 3, "fade_out": 0.3, "takes": 1, "reverb": ROOM, "post": TOP,
  "layers": {
   "crank": {"kind": "py", "fn": shutter_py, "prompt": "synthesised crank under tension: a first heavy escapement click (1.6 kHz bar partials over a 240 Hz body), ten ratchet teeth speeding up and climbing (1.5 to 2.3 kHz), a spring groan gliding up under them (rough partials from 480 to 900 Hz), and a last, hardest click at full tension (2 kHz over 300 Hz)"},
   "spring": {"prompt": "an old iron crank being wound against a stiff spring, strained metal creak, dry, isolated, no other sounds",
              "secs": 1.5, "trim": 0.9, "norm_lufs": -20, "gain_db": -16, "filter": "highpass=f=600,lowpass=f=6000,afade=t=out:st=0.8:d=0.08"},
  }},
 # HAZ-21 bellows nozzle pressure: the bag jerks open, a low resonant core and a narrow hiss climb in the nozzle,
 # and the valve shuts on the held breath.
 "BellowsWarning": {
  "seconds": 2.2, "lufs": -19, "post_gain_db": 1, "fade_out": 0.8, "takes": 1, "post": "lowpass=f=5000,lowpass=f=6000",
  "reverb": {"rt60": 1.0, "wet_db": -10, "damp_hz": 3000, "predelay_ms": 15},
  "layers": {
   "nozzle": {"kind": "py", "fn": bellows_py, "prompt": "synthesised nozzle pressure: a leather jerk (a thump of air on a 95 Hz knock), a low resonant core rising 105 to 150 Hz with harmonics, a narrow hiss tightening from 0.9 to 2.6 kHz and a wider air band from 420 Hz to 1.1 kHz, all swelling to a peak, then a valve knock (420 Hz)"},
   "leather": {"prompt": "large leather forge bellows slowly filling with air, deep breath in, creaking leather, dry, isolated, no other sounds",
               "secs": 1.5, "trim": 0.95, "norm_lufs": -20, "gain_db": -10, "filter": "highpass=f=120,lowpass=f=3000," + build_env(0.86, 0.3, 1.2)},
  }},
})


# ---------------------------------------------------------------- motion loops (folded; sndtele_audio.py loopify)
def flutter(loop_s, rate_lo, rate_hi, fc_lo, fc_hi, dlen, seed, decay=(60, 110)):
    """Cloth in moving air: irregular short bursts, each its own pitch, length and level."""
    r = random.Random(seed)
    s = buf(loop_s)
    t = 0.02
    while t < loop_s - 0.01:
        d = r.uniform(*dlen)
        add(s, nrm(air(d, r.uniform(fc_lo, fc_hi), 1.2, burst(d, 0.003, r.uniform(*decay)), seed=r.randrange(10 ** 6))), t, r.uniform(0.4, 1.0))
        t += 1.0 / r.uniform(rate_lo, rate_hi)
    return s


def air_bed(loop_s, tail, bands, seed):
    """Steady broad air: a few resonant bands (centre Hz, q, level, sway Hz), each swaying a little."""
    n = loop_s + tail
    s = buf(n)
    for i, (fc, q, lv, wf) in enumerate(bands):
        add(s, nrm(air(n, fc, q, lambda t, wf=wf, i=i: 0.6 + 0.4 * math.sin(2 * math.pi * wf * t + i), seed=seed + i)), 0.0, lv)
    return bed(s, loop_s, tail)


def umbrella_flaps_py():
    r = random.Random(11)
    s = buf(3.0)
    t = 0.05
    while t < 2.98:                                                                       # canvas panels flapping
        d, lv, fc = r.uniform(0.07, 0.12), r.uniform(0.45, 1.0), r.uniform(380, 900)
        add(s, nrm(air(d, fc, 1.1, burst(d, 0.005, r.uniform(28, 45)), seed=r.randrange(10 ** 6))), t, lv)
        add(s, nrm(air(d * 0.6, fc * 2.6, 1.4, burst(d * 0.6, 0.003, 60), seed=r.randrange(10 ** 6))), t, lv * 0.5)
        t += r.uniform(0.12, 0.30)
    return s


def umbrella_ribs_py():
    s = buf(3.0)
    add(s, nrm(creak(0.5, 470, 560, rough=30, amp=swell(0.2, 0.5, 1.5, 6), seed=1)), 0.45, 0.8)   # ribs strain
    add(s, nrm(creak(0.6, 640, 540, rough=26, amp=swell(0.25, 0.6, 1.5, 5), seed=2)), 1.85, 0.7)
    add(s, strike(1900, 120, BAR2, nz=0.8), 1.25, 0.5)                                    # a brass rib ticks
    add(s, strike(2250, 120, BAR2, nz=0.8), 2.6, 0.4)
    return s


def umbrella_lift_py():
    win = lambda t: math.sin(math.pi * t / 3.0) ** 2                                      # air that keeps climbing
    a = air(3.0, lambda t: 450 * 3.2 ** (t / 3.0), 2.5, win, seed=5)
    b = rotate(air(3.0, lambda t: 450 * 3.2 ** (t / 3.0), 2.5, win, seed=6), 1.5)
    return [x + y for x, y in zip(a, b)]


def wing_strokes_py():
    s = buf(4.0)
    for t0, f_hi, sd in ((0.15, 720, 1), (2.15, 640, 2)):                                 # two slow strokes
        env = swell(0.28, 1.25, 2.0, 3.4)
        add(s, nrm(air(1.25, lambda t, f=f_hi: 110 + (f - 250) * math.exp(-3.5 * t), 1.3, env, seed=sd)), t0, 1.0)
        add(s, nrm(air(1.25, 95, 1.5, env, seed=sd + 20)), t0, 0.7)
        add(s, nrm(air(1.25, lambda t, f=f_hi: 340 + (2 * f - 340) * math.exp(-3.0 * t), 1.5,
                       lambda t, env=env: env(t) * (0.7 + 0.3 * math.sin(2 * math.pi * 22 * t)), seed=sd + 10)), t0, 0.45)
    return s


def wing_joints_py():
    parts = ((1, 0.6), (1.52, 0.4), (2.3, 0.25), (3.1, 0.15))
    s = buf(4.0)
    add(s, nrm(creak(0.55, 300, 390, parts, rough=28, amp=swell(0.2, 0.55, 1.5, 5), seed=3)), 0.3, 1.0)
    add(s, nrm(creak(0.6, 400, 320, parts, rough=24, amp=swell(0.22, 0.6, 1.5, 5), seed=4)), 2.3, 0.9)
    for k, t0 in enumerate((0.3, 2.3)):                                                   # the joint ratchets back
        for j, dt in enumerate((0.55, 0.68, 0.84)):
            add(s, strike(900 + 60 * k, 90, BAR2, nz=0.8, seed=j), t0 + dt, 0.35 - 0.08 * j)
    return s


def chain_py():
    r = random.Random(5)
    s = buf(2.0)
    for i in range(24):                                                                   # twelve links a second
        t = i / 12 + r.uniform(-0.006, 0.006) + 0.008
        lv, hi = r.uniform(0.75, 1.0), i % 2
        add(s, strike(2300 if hi else 1900, 110, BAR2, nz=0.9, seed=i % 4), t, 0.7 * lv)
        add(s, strike(260 if hi else 210, 55, KNOCK, nz=0.4, nz_decay=120, seed=i % 4), t, 0.32 * lv)
        if i % 6 == 0:                                                                    # a pulley tooth
            add(s, strike(140, 35, KNOCK, nz=0.3, nz_decay=80), t, 0.35)
    return s


def bolt_gear_py():
    s = buf(2.0)
    for i in range(44):                                                                   # 22 ringing teeth a second
        ph = i * 2.0 / 44
        t = ph + 0.012 * math.sin(2 * math.pi * ph) + 0.013                               # the spin wobbles
        add(s, strike(520, 45, BAR, nz=0.5, seed=i % 3), t, 0.6 + 0.2 * math.sin(math.pi * ph))
        add(s, strike(170, 60, KNOCK, nz=0, rise=0.003), t, 0.3)
        if i % 11 == 0:
            add(s, strike(300, 30, BAR2, nz=0.8), t, 0.9)
            add(s, strike(120, 30, KNOCK, nz=0), t, 0.7)
    return s


def warden_steps_py():
    s = buf(2.4)

    def heavy(t, f, fk, sd):
        add(s, strike(fk, 24, KNOCK, nz=0.6, nz_decay=60, seed=sd), t, 0.5)
        add(s, strike(f, 34, BAR, nz=0.8, seed=sd), t + 0.035, 0.9)

    def light(t, f, fk, sd):
        add(s, strike(fk, 30, KNOCK, nz=0.4, nz_decay=80, seed=sd), t, 0.28)
        add(s, strike(f, 60, BAR2, nz=0.6, seed=sd), t + 0.03, 0.6)

    heavy(0.02, 560, 85, 1)
    light(0.72, 840, 115, 2)
    heavy(1.22, 610, 92, 3)
    light(1.92, 760, 120, 4)
    add(s, strike(1500, 150, BAR2, nz=0.6), 0.84, 0.2)                                    # a strap
    for j, dt in enumerate((0.1, 0.16, 0.21)):                                            # a buckle jingle
        add(s, strike(2200 + 150 * j, 170, BAR2, nz=0.6, seed=j), 1.92 + dt, 0.22)
    return s


def flood_steps_py():
    s = buf(3.0)
    for k in range(4):                                                                    # an even, heavy stride: 0.75 s a step
        t0 = 0.02 + (0.0, 0.72, 1.55, 2.25)[k]
        add(s, strike((150, 128, 165, 118)[k], 30, KNOCK, nz=0.5, nz_decay=70, seed=k), t0, 0.7)     # footfall thump
        add(s, strike(230, 40, PLATE, nz=0.8, seed=k), t0 + 0.01, 0.7)
        for j, dt in enumerate(((0.09, 0.15, 0.21, 0.30), (0.1, 0.19), (0.08, 0.14, 0.2), (0.12, 0.17, 0.26, 0.33))[k]):                                  # strap and buckle rattle
            add(s, strike(1700 + 140 * ((j + k) % 3), 120, BAR2, nz=0.8, seed=j + k), t0 + dt, 0.65 - 0.08 * j)
        if k % 2:
            add(s, nrm(creak(0.35, 520, 410, rough=30, amp=swell(0.12, 0.35, 1.5, 6), seed=k)), t0 + 0.25, 0.35)
    return s


def courier_blades_py():
    loop_s, tail, rate = 2.0, 0.8, 13
    s = buf(loop_s + tail)
    for i in range(int((loop_s + tail) * rate)):                                          # 13 blade chops a second
        t, alt = i / rate, i % 2
        lv = (1.0 if alt else 0.85) * (0.85 + 0.15 * math.sin(math.pi * t))
        add(s, nrm(air(0.06, 360 if alt else 300, 1.0, burst(0.06, 0.008, 38), seed=50 + i % 26)), t, lv)
        add(s, strike(230 if alt else 205, 60, KNOCK, nz=0, rise=0.004), t, 0.5 * lv)
    return bed(s[:int((loop_s + tail) * SR)], loop_s, tail, periodic=True)


RECIPES.update({
 # MOVE-21 rise: lifted under the open umbrella. Canvas panels flap, the ribs strain, the air keeps climbing.
 "UmbrellaFlap": {
  "loop_s": 3.0, "loop_tail": 0.6, "seconds": 3.0, "lufs": -21, "post_gain_db": 1, "takes": 1, "reverb": NEAR, "post": TOP,
  "layers": {
   "flaps": {"kind": "py", "fn": umbrella_flaps_py, "prompt": "synthesised canvas flaps: irregular soft whumps of air four to eight a second (380-900 Hz with a lighter band above), each its own length and level"},
   "ribs": {"kind": "py", "fn": umbrella_ribs_py, "gain_db": -9, "prompt": "synthesised rib strain: two slow wooden creaks (rough partials near 500 and 600 Hz) and two small brass rib ticks"},
   "lift": {"kind": "py", "fn": umbrella_lift_py, "gain_db": -8, "prompt": "synthesised rising air: two overlapping bands that keep climbing from 450 Hz to 1.4 kHz, one fading in as the other fades out"},
   "flutter": {"prompt": "cloth umbrella canopy fluttering in a steady updraft, soft waxed canvas flapping gently and continuously, close, dry, no other sounds",
               "secs": 4.0, "trim": 3.6, "norm_lufs": -20, "gain_db": -9, "filter": "highpass=f=250,lowpass=f=6000," + loop_bed(3.0, 0.6)},
  }},
 # MOVE-21 fall: a small body falling. Broad, bright air and a quick coat flutter close to the ear.
 "EllaFallLoop": {
  "loop_s": 3.0, "loop_tail": 0.5, "seconds": 3.0, "lufs": -21, "takes": 1, "reverb": NEAR, "post": TOP,
  "layers": {
   "air": {"kind": "py", "fn": lambda: air_bed(3.0, 0.5, ((800, 0.8, 1.0, 1 / 3), (1700, 0.9, 0.7, 2 / 3), (3200, 1.0, 0.35, 1 / 3)), 60),
           "prompt": "synthesised broad air rushing past: three swaying bands at 0.8, 1.7 and 3.2 kHz"},
   "coat": {"kind": "py", "fn": lambda: flutter(3.0, 10, 15, 700, 2400, (0.03, 0.055), 61, (45, 80)), "gain_db": 3,
            "prompt": "synthesised coat flutter: irregular quick cloth flicks 10 to 15 a second (0.7-2.4 kHz)"},
   "cloth": {"prompt": "a small cloth coat fluttering quickly in falling air, light fabric flapping, continuous, close, dry",
             "secs": 4.0, "trim": 3.5, "norm_lufs": -20, "gain_db": -8, "filter": "highpass=f=400,lowpass=f=3000,lowpass=f=3000," + loop_bed(3.0, 0.5)},
  }},
 # MOVE-05 fast free fall: both held. Hard, fast air with a thin whistle on top and cloth snapping twice as fast.
 "FreeFallRush": {
  "loop_s": 3.0, "loop_tail": 0.5, "seconds": 3.0, "lufs": -20, "takes": 1, "reverb": NEAR, "post": TOP,
  "layers": {
   "hiss": {"kind": "py", "fn": lambda: air_bed(3.0, 0.5, ((1000, 0.8, 1.0, 2 / 3), (1900, 0.9, 0.9, 1 / 3), (3300, 1.0, 0.45, 2 / 3)), 70),
            "prompt": "synthesised fast air: three strong swaying bands at 1.0, 1.9 and 3.3 kHz"},
   "whistle": {"kind": "py", "fn": lambda: bed(nrm(air(3.5, lambda t: 2900 + 150 * math.sin(2 * math.pi * 2 / 3 * t), 30.0, None, seed=71)), 3.0, 0.5),
               "gain_db": -13, "prompt": "synthesised edge whistle: a thin wavering band of air near 2.9 kHz"},
   "snap": {"kind": "py", "fn": lambda: flutter(3.0, 18, 26, 1000, 3000, (0.015, 0.03), 72, (80, 140)), "gain_db": 2,
            "prompt": "synthesised cloth snapping in fast air: irregular sharp flicks 18 to 26 a second (1-3 kHz)"},
   "cloth": {"prompt": "cloth snapping rapidly in violent wind, fast fabric flapping, continuous, close, dry",
             "secs": 4.0, "trim": 3.5, "norm_lufs": -20, "gain_db": -9, "filter": "highpass=f=500,lowpass=f=3500,lowpass=f=3500," + loop_bed(3.0, 0.5)},
  }},
 # ANIM-06 hover: two huge slow wing strokes every 4 s. Each is a feathered whoosh that falls in pitch, with a brass
 # joint creak and three ratchet ticks as the wing turns. Felt more than heard.
 "OwlWingLoop": {
  "loop_s": 4.0, "loop_tail": 0.8, "seconds": 4.0, "lufs": -24, "post_gain_db": 2, "takes": 1, "post": "lowpass=f=4000,lowpass=f=6000",
  "reverb": {"rt60": 1.5, "wet_db": -12, "damp_hz": 2500, "predelay_ms": 20},
  "layers": {
   "strokes": {"kind": "py", "fn": wing_strokes_py, "prompt": "synthesised wing strokes, one every 2 s: a low band of air that swells and falls from 700 to 160 Hz with a fluttering feather band above it"},
   "joints": {"kind": "py", "fn": wing_joints_py, "gain_db": -6, "prompt": "synthesised brass joints: on each stroke a rough creak (partials near 300-400 Hz, one rising, one falling) and three soft ratchet ticks"},
   "wings": {"prompt": "slow heavy wing flaps of a very large bird, a feathery whoosh and soft whump of air on each beat, steady slow rhythm, close, dry, no other sounds",
             "secs": 5.0, "trim": 4.8, "norm_lufs": -20, "gain_db": -12, "filter": "highpass=f=100,highshelf=f=300:g=7,lowpass=f=2200," + loop_bed(4.0, 0.8)},
  }},
 # OWL-22: the chain pays out. Twelve heavy iron links a second, each a click on a low iron body, a pulley tooth
 # every sixth link, silence between them.
 "ChainTravel": {
  "loop_s": 2.0, "loop_tail": 0.6, "seconds": 2.0, "lufs": -21, "post_gain_db": 1, "takes": 1, "post": TOP,
  "reverb": {"rt60": 0.6, "wet_db": -11, "damp_hz": 5000, "predelay_ms": 10},
  "layers": {
   "links": {"kind": "py", "fn": chain_py, "prompt": "synthesised chain paying out: twelve struck-iron links a second with small timing and level differences, alternating 1.9 and 2.3 kHz bar partials over 210 and 260 Hz bodies, and a 140 Hz pulley tooth every sixth link"},
  }},
 # OWL-11 red travel: a heavy gear spinning through the belfry: 22 ringing iron teeth a second, the spin wobbling,
 # a heavier tooth four times a turn, air moving round it.
 "OwlBoltTravelLoop": {
  "loop_s": 2.0, "loop_tail": 0.8, "seconds": 2.0, "lufs": -21, "takes": 1, "post": DARK,
  "reverb": {"rt60": 1.3, "wet_db": -8, "damp_hz": 3000, "predelay_ms": 15},
  "layers": {
   "gear": {"kind": "py", "fn": bolt_gear_py, "prompt": "synthesised spinning gear: 22 ringing struck-iron teeth a second (520 Hz bar partials) with a once-a-second speed wobble and a heavier 300 Hz tooth every eleventh"},
   "air": {"kind": "py", "fn": lambda: bed(nrm(air(2.8, lambda t: 480 + 160 * math.sin(math.pi * t), 1.5, None, seed=9)), 2.0, 0.8),
           "gain_db": -12, "prompt": "synthesised air moving round the shot: a low swaying band near 480 Hz"},
   "whirr": {"prompt": "low spinning clockwork gear whirr, dark metallic hum of a heavy flywheel, steady, continuous, dry, no other sounds",
             "secs": 3.0, "trim": 2.8, "norm_lufs": -20, "gain_db": -12, "filter": "highpass=f=120,lowpass=f=2500," + loop_bed(2.0, 0.8)},
  }},
 # COM-14 Roadwarden movement: a heavy-light armoured gait, a different clank on every step, a low gear turning under it.
 "WardenMove": {
  "loop_s": 2.4, "loop_tail": 0.8, "seconds": 2.4, "lufs": -21, "takes": 1, "post": DARK,
  "reverb": {"rt60": 0.9, "wet_db": -11, "damp_hz": 3000, "predelay_ms": 15},
  "layers": {
   "steps": {"kind": "py", "fn": warden_steps_py, "prompt": "synthesised armoured gait: heavy, light, heavy, light (0.7 s then 0.5 s apart): boot thuds at 85-120 Hz with a different iron clank on each (560, 840, 610, 760 Hz), a strap tick and a three-note buckle jingle"},
   "gear": {"kind": "py", "fn": lambda: teeth(2.4, 0.8, 36, 260, 80, KNOCK, nz=0.3), "gain_db": -13,
            "prompt": "synthesised low gear turning: 15 soft 260 Hz teeth a second"},
   "kit": {"prompt": "iron armour and equipment rattling on a slowly marching soldier, buckles and plates shifting, steady, dry, no voice",
           "secs": 3.5, "trim": 3.2, "norm_lufs": -20, "gain_db": -11, "filter": "highpass=f=300,lowpass=f=4000," + loop_bed(2.4, 0.8)},
  }},
 # COM-15 Floodstrider movement: a striding machine. Heavy and light stilt footfalls, each different, ratchet ticks
 # and joint groans between them, a low gear turning under the whole stride.
 "FloodStiltMove": {
  "loop_s": 3.0, "loop_tail": 0.8, "seconds": 3.0, "lufs": -21, "takes": 1, "post": DARK,
  "reverb": {"rt60": 0.9, "wet_db": -11, "damp_hz": 3000, "predelay_ms": 15},
  "layers": {
   "stride": {"kind": "py", "fn": flood_steps_py, "prompt": "synthesised stilt stride: four different footfalls (heavy 300 Hz, light 410 Hz with two ratchet ticks, heavy 340 Hz, light 460 Hz with three falling ticks, each a wooden plate over a low knock), and two joint groans"},
   "gear": {"kind": "py", "fn": lambda: teeth(3.0, 0.8, 42, 180, 70, KNOCK, nz=0.3), "gain_db": -20,
            "prompt": "synthesised low gear turning: 14 soft 180 Hz teeth a second"},
   "joints": {"prompt": "slow walking machine on tall wooden stilts, iron joints creaking between heavy steps, steady, dry, no other sounds",
              "secs": 4.0, "trim": 3.8, "norm_lufs": -20, "gain_db": -11, "filter": "highpass=f=250,lowpass=f=3500," + loop_bed(3.0, 0.8)},
  }},
 # COM-16 Sky Courier flight: wooden blades beating air, 13 chops a second, alternate blades a little different,
 # a fast small gear and moving wind under them, washed in the hall.
 "CourierFlightLoop": {
  "loop_s": 2.0, "loop_tail": 0.8, "seconds": 2.0, "lufs": -21, "takes": 1, "post": DARK,
  "reverb": {"rt60": 1.2, "wet_db": -8, "damp_hz": 3000, "predelay_ms": 15},
  "layers": {
   "blades": {"kind": "py", "fn": courier_blades_py, "prompt": "synthesised propeller: 13 blade chops a second, each a soft thump of air (300 or 360 Hz, alternate blades) on a wooden 205-230 Hz tone, swaying once a loop"},
   "gear": {"kind": "py", "fn": lambda: teeth(2.0, 0.8, 78, 700, 200, BAR2, nz=0.3), "gain_db": -16,
            "prompt": "synthesised small fast gear: 39 light 700 Hz teeth a second"},
   "wind": {"kind": "py", "fn": lambda: bed(nrm(air(2.8, lambda t: 800 + 300 * math.sin(math.pi * t), 1.2, None, seed=8)), 2.0, 0.8),
            "gain_db": -11, "prompt": "synthesised wind round the blades: a swaying band near 800 Hz"},
   "prop": {"prompt": "small wooden propellers spinning steadily, soft fluttering whirr of a clockwork flying machine, continuous, dry, no other sounds",
            "secs": 3.0, "trim": 2.8, "norm_lufs": -20, "gain_db": -11, "filter": "highpass=f=200,lowpass=f=3500," + loop_bed(2.0, 0.8)},
  }},
})
