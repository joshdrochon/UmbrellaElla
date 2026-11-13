"""Stdlib sound sources for the sndtele lane's `py` layers (tools/build/assets/sndtele_recipes.py).
Physical-ish models, no samples: struck metal and wood (decaying partials plus contact noise), moving air (noise
through a gliding resonator), and creaks (gliding partials with stick-slip roughness). Every source is seeded, so a
recipe renders the same bytes each time. sndtele_audio.py writes each layer to the regen cache as a WAV; the audio
area's regen.py then mixes it like any other layer."""
import math
import random
import struct
import wave

SR = 48000
BAR = ((1, 0.6, 1), (2.76, 0.4, 1.4), (5.4, 0.25, 1.8))       # a struck metal bar: (ratio, weight, decay factor)
BAR2 = BAR[:2]
KNOCK = ((1, 1, 1), (2.1, 0.4, 1.5))                          # wood, or a heavy body
BELL = ((1, 0.6, 1), (2.0, 0.3, 1.3), (2.4, 0.2, 1.6), (3.0, 0.15, 2), (4.2, 0.1, 3))
PLATE = ((1, 1, 1), (2.3, 0.5, 1.3), (3.9, 0.3, 1.6))         # a dull, damped plate: a clack, not a ring


def buf(dur):
    return [0.0] * int(round(dur * SR))


def add(dst, src, t=0.0, g=1.0):
    """Mix src into dst at t seconds (dst grows if it must)."""
    i0 = int(round(t * SR))
    if i0 + len(src) > len(dst):
        dst.extend([0.0] * (i0 + len(src) - len(dst)))
    for i, v in enumerate(src):
        dst[i0 + i] += v * g
    return dst


_STRIKES = {}


def strike(f, decay=40, parts=BAR, nz=1.0, nz_decay=300, rise=0.002, seed=1):
    """One struck object: partials of f with their own exponential decay, a few ms of broadband contact noise and a
    short rise (sharp, never a 0 ms digital click)."""
    key = (f, decay, parts, nz, nz_decay, rise, seed)
    if key in _STRIKES:
        return _STRIKES[key]
    r = random.Random(seed)
    n = int(min(1.6, 7.0 / decay + 0.03) * SR)
    out = [0.0] * n
    w2 = [(2 * math.pi * f * ra, w, decay * m) for ra, w, m in parts]
    for i in range(n):
        t = i / SR
        v = 0.0
        for om, w, d in w2:
            v += w * math.exp(-d * t) * math.sin(om * t)
        if nz:
            v += nz * math.exp(-nz_decay * t) * (r.random() * 2 - 1)
        out[i] = v * (1 - math.exp(-t / rise))
    _STRIKES[key] = out
    return out


def air(dur, fc, q=2.0, amp=None, seed=1):
    """Moving air: white noise through a resonator whose centre fc (Hz, or a function of t) can glide; amp(t) shapes it."""
    r = random.Random(seed)
    n = int(dur * SR)
    out = [0.0] * n
    low = band = 0.0
    fixed = None if callable(fc) else 2 * math.sin(math.pi * min(fc, 7500) / SR)
    for i in range(n):
        t = i / SR
        k = fixed if fixed is not None else 2 * math.sin(math.pi * min(fc(t), 7500) / SR)
        low += k * band
        high = (r.random() * 2 - 1) - low - band / q
        band += k * high
        out[i] = band * (amp(t) if amp else 1.0)
    return out


def creak(dur, f0, f1, parts=((1, 0.6), (1.7, 0.3), (2.6, 0.2)), rough=40.0, amp=None, seed=1):
    """A strained joint or spring: partials gliding f0 -> f1 with stick-slip roughness (a random amplitude near
    `rough` Hz) and a slight pitch wander."""
    r = random.Random(seed)
    n = int(dur * SR)
    out = [0.0] * n
    ph = [0.0] * len(parts)
    a = math.exp(-2 * math.pi * rough / SR)
    am = 0.8
    jit = 0.0
    for i in range(n):
        t = i / SR
        f = f0 + (f1 - f0) * t / dur
        am = a * am + (1 - a) * abs(r.gauss(0, 1)) * 4.0
        jit = 0.9995 * jit + 0.0005 * r.gauss(0, 1) * 60
        v = 0.0
        for j, (ra, w) in enumerate(parts):
            ph[j] += 2 * math.pi * f * ra * (1 + 0.003 * jit) / SR
            v += w * math.sin(ph[j])
        out[i] = v * min(1.5, am) * (amp(t) if amp else 1.0)
    return out


def swell(peak_t, total, up=2.0, down=3.2, floor=0.0):
    """amp(t): rises to 1 at peak_t (power curve), then falls exponentially."""
    return lambda t: floor + (1 - floor) * ((t / peak_t) ** up if t < peak_t else math.exp(-down * (t - peak_t)))


def ramp(dur, a0=0.2, a1=1.0, power=1.5, cut=0.03):
    """amp(t): rises a0 -> a1 over dur, with a short fade at the very end so the layer never clicks off."""
    return lambda t: (a0 + (a1 - a0) * (t / dur) ** power) * min(1.0, max(0.0, (dur - t) / cut))


def burst(dur, attack=0.005, decay=30.0):
    """amp(t): a flap or chop of air: fast attack, exponential decay."""
    return lambda t: min(1.0, t / attack) * math.exp(-decay * t) * min(1.0, max(0.0, (dur - t) / 0.004))


def accel(n, dur, ratio=3.0):
    """n event times over dur seconds; the gaps shrink by `ratio` from first to last (ratio < 1: they grow)."""
    gaps = [ratio ** (-i / max(1, n - 2)) for i in range(n - 1)]
    k = dur / sum(gaps)
    out = [0.0]
    for g in gaps:
        out.append(out[-1] + g * k)
    return out


def rotate(sig, t):
    """The same loop cycle started t seconds later."""
    i = int(round(t * SR)) % len(sig)
    return sig[i:] + sig[:i]


def bed(sig, loop_s, tail, periodic=False):
    """A steady layer for a folded loop: fade in over `tail` and out over [loop_s, loop_s + tail], so the fold
    (sndtele_audio.py loopify) sums it back to a constant level. Noise fades by power; a layer that repeats exactly
    every loop_s (periodic) is the same signal on both sides and fades by amplitude."""
    n, x = int(round(loop_s * SR)), int(round(tail * SR))
    out = list(sig[:n + x]) + [0.0] * max(0, n + x - len(sig))
    for i in range(x):
        p = i / x
        a, b = (p, 1 - p) if periodic else (math.sin(0.5 * math.pi * p), math.cos(0.5 * math.pi * p))
        out[i] *= a
        out[n + i] *= b
    return out


def write(path, sig, peak=0.7):
    """16-bit mono WAV at SR, peak-normalised. A layer that starts silent gets one -80 dBFS sample at 0, because
    regen.py strips leading digital silence and the layer's timing would move."""
    m = max(1e-9, max(abs(v) for v in sig))
    out = [int(max(-1.0, min(1.0, v / m * peak)) * 32767) for v in sig]
    if abs(out[0]) < 3:
        out[0] = 3
    with wave.open(str(path), "wb") as w:
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(SR)
        w.writeframes(struct.pack(f"<{len(out)}h", *out))


def nrm(sig, peak=1.0):
    """Peak-normalise a component, so the gains a recipe mixes with are relative peaks."""
    m = max(1e-9, max(abs(v) for v in sig))
    return [v / m * peak for v in sig]


def teeth(loop_s, tail, per_loop, f, decay, parts, nz=0.3, level=1.0, wobble=0.0):
    """A gear or blade row that repeats exactly every loop_s (per_loop teeth, in phase at the seam), rendered for
    loop_s + tail and faded by amplitude at both ends so the fold sums it back to one steady row."""
    n = int(round((loop_s + tail) * SR))
    s = [0.0] * n
    k = 0
    while True:
        i = k % per_loop
        t = k * loop_s / per_loop
        if t >= loop_s + tail:
            break
        t += wobble * math.sin(2 * math.pi * i / per_loop)
        add(s, strike(f, decay, parts, nz=nz, seed=i % 3), max(0.0, t), level * (0.85 + 0.15 * math.sin(2 * math.pi * 2 * i / per_loop)))
        k += 1
    return bed(s[:n], loop_s, tail, periodic=True)
