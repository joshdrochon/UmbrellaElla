"""Supplied audio (tools/audio_import.py): files a teammate prepared are matched to sound-list rows, fitted to the style
target and logged as supplied; pre-jam files are declared, not blocked; generation only fills rows nobody supplied.
Synthetic WAVs only; each rule has a passing case and one broken on purpose."""
import contextlib
import csv
import io
import math
import os
import shutil
import sys
import tempfile
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, os.path.join(ROOT, "tools"))
sys.path.insert(0, HERE)
import assetgen  # noqa: E402
import audio_check  # noqa: E402
import audio_import  # noqa: E402
import audio_style_check as asc  # noqa: E402
from test_audio_style import R, sine, write  # noqa: E402


def dry_click(freq=3000, dur=0.08, amp=0.4):
    return [amp * math.exp(-i / (0.01 * R)) * math.sin(2 * math.pi * freq * i / R) for i in range(int(dur * R))]


class Import(unittest.TestCase):
    def setUp(self):
        self.d = tempfile.mkdtemp()
        self.addCleanup(shutil.rmtree, self.d, True)
        shutil.copytree(os.path.join(ROOT, "pipeline", "audio"), os.path.join(self.d, "pipeline", "audio"))
        for rel in ("pipeline/submission/credits.md", "docs/pre-jam-declaration.md"):
            os.makedirs(os.path.dirname(os.path.join(self.d, rel)), exist_ok=True)
            shutil.copyfile(os.path.join(ROOT, rel), os.path.join(self.d, rel))
        os.makedirs(os.path.join(self.d, "pipeline", "art"))
        self.inbox = os.path.join(self.d, "Audio", "Import")

    def drop(self, name, chans, rate=R):
        write(os.path.join(self.inbox, name), chans, rate)

    def run_imp(self, *args):
        buf = io.StringIO()
        with contextlib.redirect_stdout(buf):
            rc = audio_import.main(["--root", self.d, *args])
        return rc, buf.getvalue()

    def apply(self, made="2026-11-13"):
        return self.run_imp("apply", "--author", "Rick", "--made", made, "--licence", "Team original (Rick), all rights")

    def prov(self):
        with open(os.path.join(self.d, "pipeline", "art", "provenance.csv"), encoding="utf-8") as fh:
            return {r["asset_path"]: r for r in csv.DictReader(fh)}

    def test_match_by_name_and_by_description(self):
        self.drop("WandBolt.wav", [dry_click()])
        self.drop("sw_hit_owl_02.wav", [dry_click(300)])
        self.drop("mystery_boom.wav", [dry_click(200)])
        rc, o = self.run_imp("match")
        self.assertEqual(rc, 1, "broken on purpose: one file has no row yet\n" + o)
        self.assertIn("MATCH WandBolt.wav -> WandBolt", o)
        self.assertIn("MATCH sw_hit_owl_02.wav -> HitOwl", o)
        self.assertIn("mystery_boom.wav  (best guess by name:", o)
        self.assertIn("UiMove | ui |", o, "the rows are listed for matching by description")
        with open(os.path.join(self.inbox, "map.csv"), "w") as fh:
            fh.write("# the agent listened: a deep thud\nmystery_boom.wav,HitWing\n")
        rc, o = self.run_imp("match")
        self.assertEqual(rc, 0, o)

    def test_apply_fits_the_file_to_its_row_and_family(self):
        self.drop("WandBolt.wav", [dry_click()] * 2, rate=96000)       # stereo, 96 kHz, dry
        rc, o = self.apply()
        self.assertEqual(rc, 0, o)
        outs = sorted(os.listdir(os.path.join(self.d, "Audio", "Source", "WandBolt")))
        self.assertEqual(outs, ["SW_WandBolt_00.wav", "SW_WandBolt_01.wav", "SW_WandBolt_02.wav"],
                         "the row needs 3 takes: two variations are made")
        style = asc.load_style(os.path.join(self.d, "pipeline", "audio", "style.json"))
        lo, hi = style["families"]["wand"]["ranges"]["lufs"]
        for f in outs:
            info, ch = audio_check.read_wav(os.path.join(self.d, "Audio", "Source", "WandBolt", f))
            self.assertEqual((info["channels"], info["rate"]), (1, 48000))
            m = audio_check.measure(ch, info["rate"], -40.0)
            self.assertLessEqual(m["peak_dbfs"], -1.0)
            self.assertLessEqual(m["lead_ms"], 10)
            self.assertLessEqual(m["tail_dbfs"], -60)
            self.assertTrue(lo <= asc.lufs(ch, info["rate"]) <= hi)
        self.assertIn("reverb rt60=", o, "a dry click gets the family's room")
        info, ch = audio_check.read_wav(os.path.join(self.d, "Audio", "Source", "WandBolt", "SW_WandBolt_00.wav"))
        self.assertGreaterEqual(asc.decay_s(ch[0], R), style["families"]["wand"]["ranges"]["decay_s"][0])
        row = self.prov()["Audio/Source/WandBolt/SW_WandBolt_00.wav"]
        self.assertEqual((row["origin"], row["author"]), ("supplied", "Rick"))
        self.assertEqual(row["input_images"], "Audio/Import/WandBolt.wav")
        self.assertEqual(audio_check.source_problems(row), [])

    def test_loop_wraps_cleanly(self):
        self.drop("WindBed.wav", [sine(173.37, 3.0, 0.3)] * 2)          # not a whole number of cycles: a click at the wrap
        _, before = audio_check.read_wav(os.path.join(self.inbox, "WindBed.wav"))
        self.assertGreater(audio_check.measure(before, R, -40)["wrap"], 0.05)
        rc, o = self.apply()
        self.assertEqual(rc, 0, o)
        info, ch = audio_check.read_wav(os.path.join(self.d, "Audio", "Source", "WindBed", "SW_WindBed_00.wav"))
        self.assertLessEqual(audio_check.measure(ch, info["rate"], -40)["wrap"], 0.05)

    def test_pre_jam_file_is_declared_not_blocked(self):
        self.drop("UiMove.wav", [dry_click()])
        rc, o = self.apply(made="2026-11-01")
        self.assertEqual(rc, 0, o)
        self.assertIn("PRE-JAM: Audio/Source/UiMove/SW_UiMove_00.wav", o)
        credits = open(os.path.join(self.d, "pipeline", "submission", "credits.md")).read()
        decl = open(os.path.join(self.d, "docs", "pre-jam-declaration.md")).read()
        self.assertIn("| `Audio/Source/UiMove/SW_UiMove_00.wav` | Rick |", credits)
        self.assertIn("`Audio/Source/UiMove/SW_UiMove_00.wav`", decl)
        sys.path.insert(0, os.path.join(ROOT, "tools"))
        import submission_check
        prov = open(os.path.join(self.d, "pipeline", "art", "provenance.csv")).read()
        self.assertEqual(submission_check.assets_problems(prov, credits, root=self.d), [])
        self.assertTrue(submission_check.assets_problems(prov, "", root=self.d),
                        "broken on purpose: without the credits row the date check fails")

    def test_in_jam_file_is_not_declared(self):
        self.drop("UiMove.wav", [dry_click()])
        rc, o = self.apply(made="2026-11-13")
        self.assertNotIn("PRE-JAM", o)
        self.assertNotIn("UiMove", open(os.path.join(self.d, "pipeline", "submission", "credits.md")).read())

    def test_generation_only_for_rows_nobody_supplied(self):
        self.drop("UiMove.wav", [dry_click()])
        self.assertIn("UiMove has a supplied file waiting", assetgen.supplied_block("UiMove", self.d))
        self.apply()
        self.assertIn("UiMove has a supplied take", assetgen.supplied_block("UiMove", self.d))
        self.assertIsNone(assetgen.supplied_block("UiBack", self.d))
        rc, o = self.run_imp("todo")
        self.assertIn("GENERATE UiBack", o)
        self.assertNotIn("GENERATE UiMove ", o)

    def test_unreadable_file_fails(self):
        os.makedirs(self.inbox, exist_ok=True)
        open(os.path.join(self.inbox, "UiBack.wav"), "wb").write(b"not audio")
        rc, o = self.run_imp("apply", "--author", "Rick", "--made", "2026-11-13", "--licence", "x")
        if shutil.which("ffmpeg"):
            self.assertEqual(rc, 1, o)
        else:
            self.assertIn("ffmpeg is not installed", o)
            self.assertEqual(rc, 1, o)


if __name__ == "__main__":
    unittest.main()
