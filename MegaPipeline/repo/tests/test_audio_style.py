"""Audio quality bar, measured (tools/audio_style_check.py, pipeline/audio/style.json). Every number is read out of a
small synthetic WAV with a known answer; each check has a passing case and a case broken on purpose."""
import copy
import json
import math
import os
import random
import shutil
import struct
import subprocess
import sys
import tempfile
import unittest
import wave

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "tools"))
import audio_check  # noqa: E402
import audio_style_check as asc  # noqa: E402

R = 48000
STYLE = asc.load_style()
ROWS = audio_check.load_list()


def sine(freq, dur, amp=0.1, rate=R):
    return [amp * math.sin(2 * math.pi * freq * i / rate) for i in range(int(dur * rate))]


def clicks(bpm, dur, rate=R, seed=1):
    n, rnd = int(dur * rate), random.Random(seed)
    x = [0.0] * n
    for st in range(0, n, int(rate * 60 / bpm)):
        for i in range(int(0.03 * rate)):
            if st + i < n:
                x[st + i] += 0.5 * math.exp(-i / (0.005 * rate)) * rnd.uniform(-1, 1)
    return x


def decaying_noise(rt60, dur, rate=R, seed=2):
    rnd = random.Random(seed)
    return [rnd.uniform(-1, 1) * 0.5 * 10 ** (-3 * i / (rt60 * rate)) for i in range(int(dur * rate))]


def write(path, chans, rate=R):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    fr = bytearray()
    for i in range(len(chans[0])):
        for c in chans:
            fr += struct.pack("<h", int(max(-1, min(1, c[i])) * 32767))
    with wave.open(path, "wb") as w:
        w.setnchannels(len(chans))
        w.setsampwidth(2)
        w.setframerate(rate)
        w.writeframes(bytes(fr))


class Metrics(unittest.TestCase):
    def test_lufs_matches_bs1770_reference(self):
        # a 997 Hz sine at -20 dBFS peak in one channel reads -23.0 LUFS, at both allowed rates
        for rate in (48000, 44100):
            with self.subTest(rate=rate):
                self.assertAlmostEqual(asc.lufs([sine(997, 2, 0.1, rate)], rate), -23.0, delta=0.1)
        self.assertAlmostEqual(asc.lufs([sine(997, 2, 0.1)] * 2, R), -20.0, delta=0.1)  # two channels sum

    def test_tempo_of_a_click_track(self):
        for bpm in (72, 80, 120):
            with self.subTest(bpm=bpm):
                self.assertAlmostEqual(asc.tempo_bpm(clicks(bpm, 10), R), bpm, delta=1.0)

    def test_reverb_tail_estimate(self):
        for rt in (0.5, 1.0, 2.5):
            with self.subTest(rt=rt):
                self.assertAlmostEqual(asc.decay_s(decaying_noise(rt, rt * 1.5), R), rt, delta=0.12 * rt + 0.03)
        self.assertLess(asc.decay_s(decaying_noise(0.05, 0.3), R), 0.15)  # a dry click

    def test_attack_sharp_vs_slow(self):
        self.assertLess(asc.attack_ms(decaying_noise(0.3, 0.5), R), 3)
        ramp = [min(1.0, i / (0.3 * R)) * math.sin(2 * math.pi * 300 * i / R) * 0.5 for i in range(int(0.5 * R))]
        self.assertAlmostEqual(asc.attack_ms(ramp, R), 240, delta=15)   # 10% to 90% of a 300 ms ramp

    def test_brightness_and_band_shares(self):
        m = asc.measure_chans([sine(500, 1)], R)
        self.assertAlmostEqual(m["centroid_hz"], 500, delta=40)
        self.assertGreater(asc.measure_chans([sine(100, 1)], R)["low_share"], 0.9)
        self.assertGreater(asc.measure_chans([sine(6000, 1)], R)["high_share"], 0.9)
        self.assertAlmostEqual(m["crest_db"], 3.0, delta=0.2)   # a sine is 3 dB peak to RMS


TEST_STYLE = {
    "brand": STYLE["brand"],
    "music": {"stems": ["MusicIntro", "MusicContest"], "tempo_bpm": [66, 84], "stem_tempo_tol_bpm": 1.5,
              "stem_length_tol_s": 0.02},
    "families": {
        "wand": {"members": ["WandBolt"], "prompt": "spark",
                 "ranges": {"centroid_hz": [1500, 8000], "low_share": [0, 0.25], "decay_s": [0.2, 2.0],
                            "lufs": [-30, -10]}},
        "music_intro": {"members": ["MusicIntro"], "prompt": "drone", "ranges": {"seconds": [5, 60]}},
        "music_contest": {"members": ["MusicContest"], "prompt": "brass", "ranges": {"seconds": [5, 60]}},
    },
}


class Target(unittest.TestCase):
    def setUp(self):
        self.d = tempfile.mkdtemp()
        self.addCleanup(shutil.rmtree, self.d, True)

    def wand(self, chans):
        p = os.path.join(self.d, "WandBolt", "SW_WandBolt_00.wav")
        write(p, chans)
        return asc.check_takes({"WandBolt": [p]}, TEST_STYLE, ROWS)

    def bright_tail(self, rt=0.8):
        return [0.5 * 10 ** (-3 * i / (rt * R)) * math.sin(2 * math.pi * 3000 * i / R) for i in range(int(rt * 1.5 * R))]

    def test_on_target_take_passes(self):
        lines, probs, res = self.wand([self.bright_tail()])
        self.assertEqual(probs, [], lines)
        self.assertTrue(lines[0].startswith("PASS SW_WandBolt_00.wav family=wand"), lines)

    def test_broken_on_purpose_too_dark_too_dry_too_soft(self):
        cases = {"centroid_hz": [sine(120, 1.0, 0.3)],                          # a low hum, not a spark
                 "decay_s": [self.bright_tail(0.05)],
                 "lufs": [[v * 0.003 for v in self.bright_tail()]]}             # far too soft
        for metric, chans in cases.items():
            with self.subTest(metric=metric):
                _, probs, res = self.wand(chans)
                self.assertTrue(any(metric in p for p in probs), probs)
                self.assertGreater(next(iter(res.values()))["distance"], 0)

    def test_stems_share_tempo_and_length(self):
        def stem(sid, bpm, dur=8.0):
            p = os.path.join(self.d, sid, f"SW_{sid}_00.wav")
            c = clicks(bpm, dur)
            write(p, [c, c])
            return p
        ok = {"MusicIntro": [stem("MusicIntro", 72)], "MusicContest": [stem("MusicContest", 72)]}
        self.assertEqual(asc.check_takes(ok, TEST_STYLE, ROWS)[1], [])
        off = {"MusicIntro": ok["MusicIntro"], "MusicContest": [stem("MusicContest", 80)]}
        self.assertTrue(any("disagree on tempo" in p for p in asc.check_takes(off, TEST_STYLE, ROWS)[1]))
        long = {"MusicIntro": ok["MusicIntro"], "MusicContest": [stem("MusicContest", 72, 8.5)]}
        self.assertTrue(any("differ in length" in p for p in asc.check_takes(long, TEST_STYLE, ROWS)[1]))
        fast = {"MusicIntro": [stem("MusicIntro", 120)]}
        self.assertTrue(any("tempo_bpm" in p for p in asc.check_takes(fast, TEST_STYLE, ROWS)[1]))

    def test_cli_prints_the_commit_bound_summary(self):
        write(os.path.join(self.d, "src", "WandBolt", "SW_WandBolt_00.wav"), [sine(120, 1.0, 0.3)])
        p = subprocess.run([sys.executable, os.path.join(ROOT, "tools", "audio_style_check.py"), "check",
                            os.path.join(self.d, "src")], capture_output=True, text=True)
        self.assertEqual(p.returncode, 1, p.stdout)
        self.assertRegex(p.stdout, r"audio_style check: FAIL files=1 commit=\S+ dirty=(yes|no)")


class StyleFile(unittest.TestCase):
    def test_every_family_is_complete(self):
        known = set(STYLE["metrics"])
        for fam, f in STYLE["families"].items():
            with self.subTest(family=fam):
                for k in ("members", "character", "instruments", "register", "reverb", "prompt", "ranges"):
                    self.assertTrue(f.get(k), k)
                self.assertLessEqual(set(f.get("prompts") or {}), set(f["members"]), "a member prompt names a member")
                for m, (lo, hi) in f["ranges"].items():
                    self.assertIn(m, known)
                    self.assertLess(lo, hi)

    def test_josh_families_are_all_there(self):
        for fam in ("music_intro", "music_contest", "music_desperation", "owl_telegraph", "owl_attack", "clockwork",
                    "bell", "wind", "umbrella", "wand", "hit", "ui"):
            self.assertIn(fam, STYLE["families"])

    def test_no_reference_audio_is_stored_or_linked(self):
        text = json.dumps(STYLE).lower()
        self.assertNotRegex(text, r"https?://|\.(?:wav|mp3|ogg|flac)\b")
        for d, _, fs in os.walk(os.path.join(ROOT, "pipeline", "audio")):
            self.assertFalse([f for f in fs if f.lower().endswith((".wav", ".mp3", ".ogg", ".flac"))], d)


class Prompts(unittest.TestCase):
    def test_prompt_comes_from_the_family_and_the_row(self):
        text, secs = asc.build_prompt("GustCatch", STYLE, ROWS, "less hiss")
        self.assertIn(STYLE["families"]["wind"]["prompts"]["GustCatch"], text, "a member's own sound")
        self.assertIn(STYLE["families"]["wind"]["prompt"], asc.build_prompt("WindBed", STYLE, ROWS)[0], "the family's")
        self.assertIn("WindEntered", text)
        self.assertIn(STYLE["brand"]["prompt_suffix"], text)
        self.assertTrue(text.endswith("Revision: less hiss"))
        self.assertIn("Seamless loop", asc.build_prompt("WindBed", STYLE, ROWS)[0])

    def test_broken_on_purpose_a_named_game_or_style_of_fails(self):
        for bad in ("make it like Bloodborne", "in the style of a famous composer", "Dark Souls boss"):
            with self.subTest(bad=bad), self.assertRaises(ValueError):
                asc.build_prompt("HitOwl", STYLE, ROWS, bad)
        asc.build_prompt("HitOwl", STYLE, ROWS, "most ghostly frost")   # 'ost' inside a word is fine
        with self.assertRaises(ValueError):
            asc.build_prompt("NotASound", STYLE, ROWS)

    def test_every_live_row_has_a_prompt(self):
        for r in ROWS:
            if r["tier"] != "cut":
                with self.subTest(id=r["id"]):
                    asc.build_prompt(r["id"], STYLE, ROWS)


if __name__ == "__main__":
    unittest.main()
