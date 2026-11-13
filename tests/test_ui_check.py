"""Tests for tools/ui_check.py. Each check gets a passing input and inputs broken on purpose that
must fail. Captures and flash frames are built in a temp folder (PNGs stay out of git); text inputs
live in tests/fixtures/ui/. If someone loosens a threshold until bad UI passes, these tests fail."""
import copy
import csv
import io
import json
import os
import shutil
import sys
import tempfile
import unittest
from contextlib import redirect_stdout, redirect_stderr

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
FIX = os.path.join(HERE, "fixtures", "ui")
sys.path.insert(0, os.path.join(ROOT, "tools"))
import ui_check  # noqa: E402
from png import write_png  # noqa: E402

PAPER_LIGHT = (0xAA, 0x8F, 0x7F, 255)   # style.json paper-light
PAPER_MID = (0x93, 0x78, 0x6B, 255)     # style.json paper-mid
INK = (0x1D, 0x17, 0x13, 255)           # style.json silhouette
SEPIA = (0x5C, 0x47, 0x3E, 255)         # style.json owl-feather: sepia text that is too weak on paper
PLATE = (0xF2, 0xE6, 0xD0, 255)         # light backing plate


def read(path):
    with open(path, encoding="utf-8") as fh:
        return fh.read()


def dump(obj, path):
    with open(path, "w", encoding="utf-8") as fh:
        json.dump(obj, fh)


def run(argv):
    out, err = io.StringIO(), io.StringIO()
    with redirect_stdout(out), redirect_stderr(err):
        code = ui_check.main(argv)
    return code, out.getvalue() + err.getvalue()


def canvas(w, h, fill):
    return [[fill for _ in range(w)] for _ in range(h)]


def paint(rows, x, y, w, h, colour):
    for j in range(y, y + h):
        for i in range(x, x + w):
            rows[j][i] = colour


def text_block(rows, x, y, w, h, colour):
    """Fake glyphs: vertical strokes 2 px wide every 4 px, so the box holds text and background."""
    for i in range(x, x + w, 4):
        paint(rows, i, y, 2, h, colour)


def box(name, x, y, w, h, colour, **kw):
    b = {"name": name, "x": x, "y": y, "w": w, "h": h, "colour": "#%02x%02x%02x" % colour[:3], "kind": "text"}
    b.update(kw)
    return b


class TextFloor(unittest.TestCase):
    def test_scales_with_height(self):
        self.assertEqual(ui_check.text_floor(1080), 18)
        self.assertEqual(ui_check.text_floor(720), 12)
        self.assertEqual(ui_check.text_floor(2160), 36)

    def test_cli(self):
        code, out = run(["text-floor", "--res", "1280x720"])
        self.assertEqual((code, out.strip()), (0, "12"))
        self.assertEqual(run(["text-floor", "--res", "720p"])[0], 2)


class Contrast(unittest.TestCase):
    H = 1080

    def rows(self):
        r = canvas(200, self.H, PAPER_MID)
        paint(r, 0, 0, 200, 40, PAPER_LIGHT)   # lighter sky patch
        return r

    def test_ink_on_plate_passes(self):
        r = self.rows()
        paint(r, 8, 98, 84, 24, PLATE)
        text_block(r, 10, 100, 80, 20, INK)
        p, rep = ui_check.contrast_problems(r, [box("title", 8, 98, 84, 24, INK, px=20)])
        self.assertEqual(p, [], p)
        self.assertGreaterEqual(rep[0]["ratio"], 4.5)

    def test_key_art_ink_on_mid_paper_is_large_text_only(self):
        # Measured: silhouette #1d1713 on paper-mid #93786b is 4.34:1. Fine for large text, not for body text.
        r = self.rows()
        text_block(r, 10, 100, 80, 20, INK)
        p, _ = ui_check.contrast_problems(r, [box("body", 8, 98, 84, 24, INK, px=20)])
        self.assertTrue(any("4.34:1" in x for x in p), p)
        text_block(r, 10, 200, 80, 24, INK)
        p, _ = ui_check.contrast_problems(r, [box("heading", 8, 198, 84, 28, INK, px=24)])
        self.assertEqual(p, [], p)

    def test_sepia_on_paper_fails(self):
        r = self.rows()
        text_block(r, 10, 100, 80, 20, SEPIA)
        p, _ = ui_check.contrast_problems(r, [box("hint", 8, 98, 84, 24, SEPIA, px=20)])
        self.assertTrue(any("contrast" in x for x in p), p)

    def test_worst_patch_counts_not_the_average(self):
        # Light text: most of the box is dark ink, a light paper patch sits under part of it.
        r = self.rows()
        paint(r, 8, 300, 84, 24, INK)
        paint(r, 8, 300, 84, 4, PAPER_LIGHT)
        text_block(r, 10, 302, 80, 20, PLATE)
        p, _ = ui_check.contrast_problems(r, [box("light", 8, 300, 84, 24, PLATE, px=20)])
        self.assertTrue(any("contrast" in x for x in p), p)

    def test_text_below_floor_fails(self):
        r = self.rows()
        text_block(r, 10, 100, 80, 14, INK)
        p, _ = ui_check.contrast_problems(r, [box("small", 8, 98, 84, 18, INK, px=14)])
        self.assertTrue(any("14 px < floor 18" in x for x in p), p)

    def test_large_text_gets_3_to_1(self):
        self.assertEqual(ui_check.CONTRAST_LARGE, 3.0)
        self.assertEqual(ui_check.CONTRAST_TEXT, 4.5)

    def test_hud_text_needs_backing(self):
        r = self.rows()
        text_block(r, 10, 100, 80, 20, INK)
        p, _ = ui_check.contrast_problems(r, [box("timer", 8, 98, 84, 24, INK, px=20, hud=True)])
        self.assertTrue(any("backing" in x for x in p), p)
        # with a plate behind it
        paint(r, 8, 400, 84, 24, PLATE)
        text_block(r, 10, 402, 80, 20, INK)
        p, _ = ui_check.contrast_problems(r, [box("timer", 8, 400, 84, 24, INK, px=20, hud=True, backing="plate")])
        self.assertEqual(p, [], p)

    def test_declared_outline_must_be_drawn(self):
        r = self.rows()
        text_block(r, 10, 100, 80, 20, PLATE)
        b = box("timer", 8, 98, 84, 24, PLATE, px=20, hud=True, backing="outline", outline="#1d1713")
        p, _ = ui_check.contrast_problems(r, [b])
        self.assertTrue(any("not drawn" in x for x in p), p)
        for i in range(12, 92, 4):
            paint(r, i, 98, 1, 24, INK)    # outline beside each stroke
        p, _ = ui_check.contrast_problems(r, [b])
        self.assertEqual(p, [], p)

    def test_outline_must_ring_the_glyphs_not_just_appear(self):
        # Calibration for MIN_OUTLINE_RING. Light HUD text over a sky that is dark only on its left half,
        # no outline drawn. The old "2% of the box" bar passed this; the ring share is ~0.5 and fails.
        r = self.rows()
        paint(r, 8, 98, 42, 24, INK)
        text_block(r, 10, 100, 80, 20, PLATE)
        b = box("timer", 8, 98, 84, 24, PLATE, px=20, hud=True, backing="outline", outline="#1d1713")
        ring = ui_check.outline_ring(ui_check.region(r, b), 84, 24, PLATE[:3], INK[:3])
        self.assertTrue(0.3 < ring < 0.7, ring)
        p, _ = ui_check.contrast_problems(r, [b])
        self.assertTrue(any("rings" in x and "not drawn" in x for x in p), p)
        # Plain paper, no outline: 0.
        r2 = self.rows()
        text_block(r2, 10, 100, 80, 20, PLATE)
        self.assertEqual(ui_check.outline_ring(ui_check.region(r2, b), 84, 24, PLATE[:3], INK[:3]), 0.0)
        # A real 1 px outline round every stroke: 1.0, passes.
        r3 = self.rows()
        for i in range(10, 90, 4):
            paint(r3, i - 1, 99, 4, 22, INK)
        text_block(r3, 10, 100, 80, 20, PLATE)
        self.assertEqual(ui_check.outline_ring(ui_check.region(r3, b), 84, 24, PLATE[:3], INK[:3]), 1.0)
        self.assertEqual(ui_check.contrast_problems(r3, [b])[0], [])

    def test_outline_glyphs_on_box_edge_fail(self):
        r = self.rows()
        text_block(r, 10, 100, 80, 20, PLATE)
        b = box("tight", 10, 100, 80, 20, PLATE, px=20, hud=True, backing="outline", outline="#1d1713")
        p, _ = ui_check.contrast_problems(r, [b])
        self.assertTrue(any("pad the box" in x for x in p), p)

    def test_glyph_colour_is_measured_not_trusted(self):
        # Rendered text is #342e2a (a tint or opacity), but the author typed the style colour #1d1713.
        # The two are 39.8 apart in RGB, so the box still "finds" the colour. Declared: 5.9:1, passes.
        # Measured from the capture: 4.42:1, under 4.5 for body text, fails.
        r = self.rows()
        grey = (0x34, 0x2E, 0x2A, 255)
        text_block(r, 10, 2, 80, 20, grey)
        p, rep = ui_check.contrast_problems(r, [box("body", 8, 0, 84, 24, INK, px=20)])
        self.assertTrue(any("4.42:1" in x for x in p), (p, rep))
        self.assertGreater(rep[0]["glyph_lum_measured"], rep[0]["glyph_lum_declared"])
        # Same box with the text really drawn in the declared colour passes.
        r2 = self.rows()
        text_block(r2, 10, 2, 80, 20, INK)
        self.assertEqual(ui_check.contrast_problems(r2, [box("body", 8, 0, 84, 24, INK, px=20)])[0], [])

    def test_wrong_box_fails(self):
        r = self.rows()
        p, _ = ui_check.contrast_problems(r, [box("empty", 8, 98, 84, 24, INK, px=20)])
        self.assertTrue(any("wrong box" in x for x in p), p)
        p, _ = ui_check.contrast_problems(r, [box("off", 190, 98, 84, 24, INK, px=20)])
        self.assertTrue(any("outside" in x for x in p), p)

    def test_object_needs_3_to_1(self):
        r = self.rows()
        rust = (0x8E, 0x3B, 0x2A, 255)
        paint(r, 50, 600, 20, 6, rust)
        p, rep = ui_check.contrast_problems(r, [box("bolt", 45, 595, 30, 16, rust, kind="object")])
        self.assertTrue(any("contrast" in x for x in p), (p, rep))   # rust on paper-mid is under 3:1
        paint(r, 50, 700, 20, 6, INK)
        p, _ = ui_check.contrast_problems(r, [box("bolt", 45, 695, 30, 16, INK, kind="object")])
        self.assertEqual(p, [], p)

    def test_cli_on_png(self):
        d = tempfile.mkdtemp()
        self.addCleanup(shutil.rmtree, d)
        r = canvas(200, 108, PAPER_MID)
        paint(r, 8, 8, 84, 24, PLATE)
        text_block(r, 10, 10, 80, 20, INK)
        write_png(os.path.join(d, "c.png"), 200, 108, r)
        good = [box("t", 8, 8, 84, 24, INK, px=2)]  # floor at height 108 is 1.8 px
        dump(good, os.path.join(d, "b.json"))
        self.assertEqual(run(["contrast", os.path.join(d, "c.png"), "--boxes", os.path.join(d, "b.json")])[0], 0)
        bad = [box("t", 8, 8, 84, 24, INK, px=1)]
        dump(bad, os.path.join(d, "b.json"))
        self.assertEqual(run(["contrast", os.path.join(d, "c.png"), "--boxes", os.path.join(d, "b.json")])[0], 1)
        self.assertEqual(run(["contrast", os.path.join(d, "missing.png"), "--boxes", os.path.join(d, "b.json")])[0], 2)


class Layout(unittest.TestCase):
    """Text scale 2.0 (E9): capture each screen at 2.0 with its boxes; nothing cut, nothing overlapping."""
    def screen(self):
        r = canvas(400, 1080, PAPER_MID)
        text_block(r, 20, 20, 160, 40, INK)     # 40 px text: 2 x the 18 px floor would be 36
        text_block(r, 20, 100, 160, 40, INK)
        return r, [box("title", 16, 16, 168, 48, INK, px=40), box("play", 16, 96, 168, 48, INK, px=40)]

    def test_clean_screen_passes(self):
        r, b = self.screen()
        self.assertEqual(ui_check.layout_problems(r, b, scale=2), [])

    def test_text_not_at_scale_fails(self):
        r, b = self.screen()
        b[1]["px"] = 20
        self.assertTrue(any("is the capture at text scale 2" in x for x in ui_check.layout_problems(r, b, scale=2)))
        self.assertEqual(ui_check.layout_problems(r, b), [])    # without --scale the size is not judged here

    def test_cut_by_screen_edge_fails(self):
        r, b = self.screen()
        text_block(r, 300, 200, 100, 40, INK)
        b.append(box("quit", 296, 196, 104, 48, INK, px=40))
        self.assertTrue(any("quit" in x and "screen edge" in x for x in ui_check.layout_problems(r, b)))

    def test_overlap_fails(self):
        r, b = self.screen()
        b[1]["y"] = 50
        self.assertTrue(any("title overlaps play" in x for x in ui_check.layout_problems(r, b)))

    def test_clipped_text_touches_box_edge_fails(self):
        r, b = self.screen()
        b[0]["w"] = 118    # the widget clips the label: glyph strokes run into the box edge
        self.assertTrue(any("title: glyph pixels touch the box edge" in x for x in ui_check.layout_problems(r, b)))

    def test_cli(self):
        d = tempfile.mkdtemp()
        self.addCleanup(shutil.rmtree, d)
        r, b = self.screen()
        write_png(os.path.join(d, "s.png"), 400, 1080, r)
        dump(b, os.path.join(d, "b.json"))
        self.assertEqual(run(["layout", os.path.join(d, "s.png"), "--boxes", os.path.join(d, "b.json"), "--scale", "2"])[0], 0)
        b[1]["px"] = 20
        dump(b, os.path.join(d, "b.json"))
        self.assertEqual(run(["layout", os.path.join(d, "s.png"), "--boxes", os.path.join(d, "b.json"), "--scale", "2"])[0], 1)


class Grayscale(unittest.TestCase):
    def groups(self):
        return [{"group": "umbrella", "swatches": [
            {"name": "intact", "x": 0, "y": 0, "w": 10, "h": 10},
            {"name": "damaged", "x": 10, "y": 0, "w": 10, "h": 10},
            {"name": "critical", "x": 20, "y": 0, "w": 10, "h": 10}]}]

    def test_distinct_tiers_pass(self):
        r = canvas(30, 10, PAPER_MID)
        paint(r, 0, 0, 10, 10, PLATE)
        paint(r, 10, 0, 10, 10, PAPER_MID)
        paint(r, 20, 0, 10, 10, INK)
        p, _ = ui_check.grayscale_problems(r, self.groups())
        self.assertEqual(p, [], p)

    def test_same_lightness_different_hue_fails(self):
        r = canvas(30, 10, PAPER_MID)
        paint(r, 0, 0, 10, 10, PLATE)
        paint(r, 10, 0, 10, 10, (0x7A, 0x7A, 0x52, 255))  # olive
        paint(r, 20, 0, 10, 10, (0x9A, 0x60, 0x60, 255))  # red-brown, similar L*
        p, _ = ui_check.grayscale_problems(r, self.groups())
        self.assertTrue(any("damaged vs critical" in x for x in p), p)

    def test_one_swatch_fails(self):
        p, _ = ui_check.grayscale_problems(canvas(30, 10, INK), [{"group": "g", "swatches": [{"name": "a", "x": 0, "y": 0, "w": 5, "h": 5}]}])
        self.assertTrue(p)


class Flashes(unittest.TestCase):
    FPS = 10

    def frames(self, pattern):
        dark = [INK[:3]] * 100
        light = [PLATE[:3]] * 100
        red = [(230, 10, 10)] * 100
        return [{"d": dark, "l": light, "r": red}[c] for c in pattern]

    def test_steady_passes(self):
        p, n = ui_check.flash_problems(self.frames("d" * 100), self.FPS)
        self.assertEqual(p, [], p)
        self.assertEqual(n["flashes_per_s"], 0)

    def test_red_flashes_limit_is_two(self):
        # 15% of the frame turns red: a red flash, but under the 20% red-area rule. 3 per second must fail.
        part_red = [(230, 10, 10)] * 15 + [INK[:3]] * 85
        dark = [INK[:3]] * 100
        seq = lambda pat: [part_red if c == "R" else dark for c in pat]
        p, n = ui_check.flash_problems(seq("dRdRdRdddd" * 10), self.FPS)
        self.assertTrue(any("3 red flashes" in x for x in p), (p, n))
        self.assertFalse(any("general" in x or "saturated red" in x for x in p), p)
        p, n = ui_check.flash_problems(seq("dRdRdddddd" * 10), self.FPS)
        self.assertEqual(p, [], (p, n))

    def test_three_flashes_pass(self):
        p, n = ui_check.flash_problems(self.frames(("dldldld" + "ddd") * 10), self.FPS)
        self.assertEqual(p, [], (p, n))

    def test_four_flashes_fail(self):
        p, n = ui_check.flash_problems(self.frames("dldldldldd" * 10), self.FPS)
        self.assertTrue(any("general flashes" in x for x in p), (p, n))

    def test_slow_fade_is_not_a_flash(self):
        dark, light = INK[:3], PLATE[:3]
        steps = [tuple(int(dark[k] + (light[k] - dark[k]) * t / 20) for k in range(3)) for t in range(21)]
        seq = [[c] * 100 for c in steps + steps[::-1]] * 3
        p, n = ui_check.flash_problems(seq, self.FPS)
        self.assertNotIn("general", " ".join(p), (p, n))

    def test_red_fullscreen_fails(self):
        p, _ = ui_check.flash_problems(self.frames("d" * 50 + "r" + "d" * 49), self.FPS)
        self.assertTrue(any("saturated red" in x for x in p), p)

    def test_short_capture_fails(self):
        p, _ = ui_check.flash_problems(self.frames("d" * 20), self.FPS)
        self.assertTrue(any("need >= 10" in x for x in p), p)

    def test_cli_frame_folder(self):
        d = tempfile.mkdtemp()
        self.addCleanup(shutil.rmtree, d)
        for i, c in enumerate("dldldldldd" * 10):
            write_png(os.path.join(d, f"{i:04d}.png"), 8, 6, canvas(8, 6, INK if c == "d" else PLATE))
        code, out = run(["flashes", d, "--fps", str(self.FPS)])
        self.assertEqual(code, 1, out)


class Strings(unittest.TestCase):
    def test_pass_fixture(self):
        self.assertEqual(ui_check.string_problems(ui_check.read_strings(os.path.join(FIX, "strings_pass.csv"))), [])

    def test_fail_fixture_catches_each_break(self):
        p = " | ".join(ui_check.string_problems(ui_check.read_strings(os.path.join(FIX, "strings_fail.csv"))))
        for want in ["all caps", "Title Case", "names a key", "no {key} placeholder", "judges the player",
                     "empty text", "duplicate key", "Hint.Wordy: reading level: sentence has",
                     "Instr.Jargon: reading level"]:
            self.assertIn(want, p)

    def test_bad_header(self):
        d = tempfile.mkdtemp()
        self.addCleanup(shutil.rmtree, d)
        f = os.path.join(d, "s.csv")
        dump_text = open(f, "w")
        dump_text.write("Name,Text\na,b\n")
        dump_text.close()
        self.assertEqual(run(["strings", f])[0], 2)

    def test_cli(self):
        self.assertEqual(run(["strings", os.path.join(FIX, "strings_pass.csv")])[0], 0)
        self.assertEqual(run(["strings", os.path.join(FIX, "strings_fail.csv")])[0], 1)


class Signals(unittest.TestCase):
    def real(self):
        return json.loads(read(os.path.join(ROOT, "pipeline", "ui", "signals.json")))

    def test_repo_registry_passes(self):
        self.assertEqual(ui_check.signal_problems(self.real()), [])

    def test_sound_id_must_exist_in_sound_list(self):
        d = self.real()
        ids = {e["sound_id"] for e in d["events"] if e.get("sound_id")}   # GDD SH1.0 ids (ClockBeat, CastWarning, ...)
        self.assertEqual(ui_check.signal_problems(d, sound_ids=ids), [])
        self.assertTrue(any("ClockBeat" in x for x in ui_check.signal_problems(d, sound_ids=ids - {"ClockBeat"})))
        d["events"][0]["sound_id"] = "NoSuchSound"
        self.assertTrue(any("NoSuchSound" in x for x in ui_check.signal_problems(d, sound_ids={"OwlBoltWindup"})))

    def test_requested_sound_is_pending_not_hidden(self):
        d = self.real()
        ids = {e["sound_id"] for e in d["events"] if e.get("sound_id") and e.get("sound_status") != "requested"}
        # requested rows missing from the list: no problem now, but listed as pending
        self.assertEqual(ui_check.signal_problems(d, sound_ids=ids), [])
        self.assertEqual(len(ui_check.pending_sounds(d, ids)), 3)
        # the flag hides nothing once the row exists, and a row without the flag still fails
        self.assertEqual(ui_check.pending_sounds(d, ids | {"LowHealthLoop", "UmbrellaCreak", "FailSting"}), [])
        for e in d["events"]:
            if e["event"] == "failed":
                e.pop("sound_status")
        self.assertTrue(any("failed: sound_id FailSting is not in" in x for x in ui_check.signal_problems(d, sound_ids=ids)))

    def test_cli_release_fails_on_pending(self):
        d = tempfile.mkdtemp()
        self.addCleanup(shutil.rmtree, d)
        sig = os.path.join(ROOT, ui_check.SIGNALS_JSON)
        code, out = run(["--root", d, "signals", sig])
        self.assertEqual(code, 0, out)
        self.assertIn("PENDING failed", out)
        code, out = run(["--root", d, "signals", sig, "--release"])
        self.assertEqual(code, 1, out)
        self.assertIn("FAIL release: failed: sound_id FailSting requested", out)

    def test_shield_and_wind_rows_are_required(self):
        # dry run B H5: the P0 shield catch, heal and wind had no signal row
        d = self.real()
        self.assertEqual(ui_check.signal_problems(d), [])
        for ev in ("shield-catch", "shield-heal", "wind-enter"):
            broken = dict(d, events=[e for e in d["events"] if e["event"] != ev])
            with self.subTest(ev):
                self.assertTrue(any(f"{ev}: missing" in x for x in ui_check.signal_problems(broken)))
        catch = next(e for e in d["events"] if e["event"] == "shield-catch")
        heal = next(e for e in d["events"] if e["event"] == "shield-heal")
        self.assertNotEqual(catch["sound_id"], heal["sound_id"])
        with open(os.path.join(ROOT, "pipeline", "audio", "sound-list.csv"), encoding="utf-8") as fh:
            tiers = {r["id"]: r["tier"] for r in csv.DictReader(fh)}
        self.assertEqual([tiers.get(s) for s in ("ShieldCatch", "ShieldHeal", "GustCatch")], ["P0", "P0", "P0"])

    def test_missing_event_fails(self):
        d = self.real()
        d["events"] = [e for e in d["events"] if e["event"] != "gust-incoming"]
        self.assertTrue(any("gust-incoming: missing" in x for x in ui_check.signal_problems(d)))

    def test_sound_without_visual_fails(self):
        d = self.real()
        d["events"][0]["visual"] = "TBD"
        self.assertTrue(any("visual is blank" in x for x in ui_check.signal_problems(d)))

    def test_colour_only_second_signal_fails(self):
        d = copy.deepcopy(self.real())
        for e in d["events"]:
            if e["event"] == "umbrella-critical":
                e["second_signal"] = "darker red tint"
        self.assertTrue(any("only a colour" in x for x in ui_check.signal_problems(d)))
        for e in d["events"]:
            if e["event"] == "umbrella-critical":
                e["second_signal"] = ""
        self.assertTrue(any("no second signal" in x for x in ui_check.signal_problems(d)))


    def test_owl_hits_and_progress_are_required(self):
        d = self.real()
        d["events"] = [e for e in d["events"] if e["event"] not in ("clock-hit", "wing-hit", "progress-motif")]
        p = " | ".join(ui_check.signal_problems(d))
        for want in ("clock-hit: missing", "wing-hit: missing", "progress-motif: missing"):
            self.assertIn(want, p)

    def test_progress_needs_a_non_colour_signal_even_without_colour(self):
        d = self.real()
        for e in d["events"]:
            if e["event"] == "progress-motif":
                e["colour"], e["second_signal"] = "", ""
        self.assertTrue(any("progress-motif: progress state with no second signal" in x for x in ui_check.signal_problems(d)))
        for e in d["events"]:
            if e["event"] == "progress-motif":
                e["second_signal"] = "darker glow"
        self.assertTrue(any("progress-motif" in x and "only a colour" in x for x in ui_check.signal_problems(d)))

    def test_blank_sound_id_fails_unless_silent(self):
        d = self.real()
        for e in d["events"]:
            if e["event"] == "failed":
                e["sound_id"] = ""
        self.assertTrue(any("failed: sound_id is blank" in x for x in ui_check.signal_problems(d)))
        intact = [e for e in d["events"] if e["event"] == "umbrella-intact"][0]
        self.assertEqual((intact["sound_id"], intact["sound"][:4]), ("", "none"))
        self.assertFalse(any(x.startswith("umbrella-intact") for x in ui_check.signal_problems(d)))

    def test_shared_sound_id_needs_a_reason(self):
        d = self.real()
        for e in d["events"]:
            if e["event"] == "umbrella-critical":
                e["sound_id"] = "UmbrellaCreak"
                e.pop("shared_ok", None)
        p = ui_check.signal_problems(d)
        self.assertTrue(any("umbrella-critical: sound_id UmbrellaCreak is already used by umbrella-tear" in x for x in p), p)
        self.assertFalse(any(x.startswith("umbrella-damaged") for x in p), p)   # has a shared_ok reason
        for e in d["events"]:
            if e["event"] == "umbrella-damaged":
                e.pop("shared_ok")
        self.assertTrue(any(x.startswith("umbrella-damaged: sound_id") for x in ui_check.signal_problems(d)))


class Fonts(unittest.TestCase):
    def test_pass_fixture(self):
        self.assertEqual(ui_check.font_problems(ui_check.read_styles(os.path.join(FIX, "text_styles_pass.csv"))), [])
        self.assertEqual(run(["fonts", os.path.join(FIX, "text_styles_pass.csv")])[0], 0)

    def test_fail_fixture_catches_each_break(self):
        p = " | ".join(ui_check.font_problems(ui_check.read_styles(os.path.join(FIX, "text_styles_fail.csv"))))
        for want in ["Body.Settings: body text in Old English Text", "Body.Prompt: Use is 'label'",
                     "Body.Empty: Style and Font must be filled", "body styles use 3 fonts",
                     "UnifrakturCook is used for both title and body"]:
            self.assertIn(want, p)
        self.assertEqual(run(["fonts", os.path.join(FIX, "text_styles_fail.csv")])[0], 1)

    def test_no_body_style_and_bad_header(self):
        self.assertIn("no body style", " ".join(ui_check.font_problems([{"Style": "T", "Font": "F", "Use": "title"}])))
        self.assertEqual(ui_check.font_problems([]), ["no text styles listed"])
        d = tempfile.mkdtemp()
        self.addCleanup(shutil.rmtree, d)
        bad = os.path.join(d, "s.csv")
        with open(bad, "w") as fh:
            fh.write("Name,Face\nA,B\n")
        self.assertEqual(run(["fonts", bad])[0], 2)


class Shake(unittest.TestCase):
    def good(self):
        return {"global": {"shake_off_option": True},
                "events": [{"kind": "shake", "flag": "bHit", "amp_pct_h": 2.5}, {"kind": "hitstop", "flag": "x"}]}

    def test_pass(self):
        self.assertEqual(ui_check.shake_problems(self.good()), [])

    def test_too_big_fails(self):
        d = self.good()
        d["events"][0]["amp_pct_h"] = 2.6
        self.assertTrue(any("bHit: shake amp 2.6%" in x for x in ui_check.shake_problems(d)))
        d["events"][0].pop("amp_pct_h")
        self.assertTrue(any("no numeric amp_pct_h" in x for x in ui_check.shake_problems(d)))

    def test_no_off_switch_fails(self):
        d = self.good()
        d["global"]["shake_off_option"] = False
        self.assertTrue(any("shake_off_option" in x for x in ui_check.shake_problems(d)))

    def test_repo_feel_file(self):
        path = os.path.join(ROOT, ui_check.FEEL_JSON)
        if not os.path.exists(path):
            self.skipTest("feel.json not created yet")
        self.assertEqual(run(["shake"])[0], 0)


class ReadingLevel(unittest.TestCase):
    def test_short_plain_passes(self):
        self.assertEqual(ui_check.reading_problems("Hold the umbrella open to rise. Let go to fall."), [])
        self.assertEqual(ui_check.reading_problems("Accessibility"), [])   # one-word label is not a sample

    def test_long_sentence_fails(self):
        p = ui_check.reading_problems(" ".join(["go"] * 16) + ".")
        self.assertTrue(any("16 words" in x for x in p), p)
        self.assertEqual(ui_check.reading_problems(" ".join(["go"] * 15) + "."), [])

    def test_long_words_fail(self):
        p = ui_check.reading_problems("Use the invulnerability window to dodge every bolt now")
        self.assertTrue(any("syllables" in x for x in p), p)

    def test_syllables(self):
        self.assertEqual([ui_check.syllables(w) for w in ["go", "umbrella", "projectile", "accessibility"]], [1, 3, 3, 6])


class Flow(unittest.TestCase):
    def test_pass(self):
        text = read(os.path.join(FIX, "uiflow_pass.log"))
        self.assertEqual(ui_check.flow_problems(text, "abc1234def"), [])

    def test_fail_fixture(self):
        p = " | ".join(ui_check.flow_problems(read(os.path.join(FIX, "uiflow_fail.log")), "abc1234"))
        for want in ["pause-end-event: fail", "quit-pause: blank", "keyboard-only: not run", "text-scale-2: blank",
                     "play-presses: 3"]:
            self.assertIn(want, p)

    def test_remap_and_release_fields_are_required(self):
        text = read(os.path.join(FIX, "uiflow_pass.log"))
        for f in ("remap", "release-activate"):
            broken = text.replace(f" {f} pass |", " ")
            self.assertNotEqual(broken, text)
            self.assertIn(f"{f}: blank (a blank field is not a pass)", ui_check.flow_problems(broken, "abc1234"))
            failed = text.replace(f" {f} pass |", f" {f} fail (fired on press) |")
            self.assertIn(f"{f}: fail (fired on press)", ui_check.flow_problems(failed, "abc1234"))

    def test_prompts_consistent_is_required(self):
        text = read(os.path.join(FIX, "uiflow_pass.log"))
        broken = text.replace(" prompts-consistent pass |", " ")
        self.assertNotEqual(broken, text)
        self.assertIn("prompts-consistent: blank (a blank field is not a pass)", ui_check.flow_problems(broken, "abc1234"))
        moved = text.replace("prompts-consistent pass", "prompts-consistent fail (settings has Back on the left)")
        self.assertIn("prompts-consistent: fail (settings has back on the left)", ui_check.flow_problems(moved, "abc1234"))

    def test_wrong_commit_and_no_line(self):
        text = read(os.path.join(FIX, "uiflow_pass.log"))
        self.assertTrue(any("expected" in x for x in ui_check.flow_problems(text, "fff0000")))
        self.assertEqual(ui_check.flow_problems("nothing here", "abc"), ["no UIFLOW line"])


class ConfigAndWidgets(unittest.TestCase):
    def test_config(self):
        self.assertEqual(run(["config", os.path.join(FIX, "DefaultEngine_pass.ini")])[0], 0)
        self.assertEqual(run(["config", os.path.join(FIX, "DefaultEngine_fail.ini")])[0], 1)
        self.assertTrue(ui_check.config_problems("[/Script/Engine.RendererSettings]\nx=1\n"))

    def test_widgets(self):
        self.assertEqual(ui_check.widget_problems(os.path.join(FIX, "widgets_pass")), [])
        p = ui_check.widget_problems(os.path.join(FIX, "widgets_fail"))
        self.assertTrue(any("HudWidget.h" in x for x in p) and any("HudWidget.cpp" in x for x in p), p)

    def test_ci_skips_absent_inputs(self):
        d = tempfile.mkdtemp()
        self.addCleanup(shutil.rmtree, d)
        code, out = run(["--root", d, "ci"])
        self.assertEqual(code, 0, out)
        self.assertIn("skipped (not created yet): pipeline/ui/signals.json", out)

    def test_ci_on_repo(self):
        # The repo is green before the jam: requested sounds print PENDING, they do not fail plain ci.
        code, out = run(["ci"])
        self.assertEqual(code, 0, out)
        self.assertFalse([l for l in out.splitlines() if l.startswith("FAIL")], out)

    def test_ci_release_fails_on_skipped_inputs(self):
        d = tempfile.mkdtemp()
        self.addCleanup(shutil.rmtree, d)
        code, out = run(["--root", d, "ci", "--release"])
        self.assertEqual(code, 1, out)
        self.assertIn("release: Config/DefaultEngine.ini does not exist", out)

    def test_ci_release_passes_with_every_input(self):
        d = tempfile.mkdtemp()
        self.addCleanup(shutil.rmtree, d)
        def put(rel, src):
            os.makedirs(os.path.dirname(os.path.join(d, rel)), exist_ok=True)
            shutil.copy(src, os.path.join(d, rel))
        put(ui_check.SIGNALS_JSON, os.path.join(ROOT, ui_check.SIGNALS_JSON))
        put(ui_check.TEXT_STYLES_CSV, os.path.join(FIX, "text_styles_pass.csv"))
        ids = [e["sound_id"] for e in json.loads(read(os.path.join(ROOT, ui_check.SIGNALS_JSON)))["events"] if e.get("sound_id")]
        os.makedirs(os.path.join(d, "pipeline", "audio"), exist_ok=True)
        with open(os.path.join(d, ui_check.SOUND_LIST), "w") as fh:
            fh.write("id,family\n" + "".join(f"{i},x\n" for i in sorted(set(ids))))
        put(ui_check.STRINGS_CSV, os.path.join(FIX, "strings_pass.csv"))
        put(ui_check.ENGINE_INI, os.path.join(FIX, "DefaultEngine_pass.ini"))
        put(os.path.join(ui_check.SOURCE_DIR, "HudWidget.h"), os.path.join(FIX, "widgets_pass", "HudWidget.h"))
        with open(os.path.join(d, ui_check.SOURCE_DIR, "TitleMenu.cpp"), "w") as fh:   # the title Quit button (U15)
            fh.write("void UTitleMenu::OnQuit() { UKismetSystemLibrary::QuitGame(this, nullptr, Q, false); }\n")
        os.makedirs(os.path.join(d, "pipeline", "feel"), exist_ok=True)
        dump(Shake().good(), os.path.join(d, ui_check.FEEL_JSON))
        code, out = run(["--root", d, "ci", "--release"])   # the screens input is one of "every input" (12 Nov)
        self.assertEqual(code, 1, out)
        self.assertIn("release: pipeline/art/references.json does not exist", out)
        os.makedirs(os.path.join(d, "pipeline", "art"), exist_ok=True)
        dump({"references": [], "elements": {}}, os.path.join(d, ui_check.REFERENCES_JSON))
        code, out = run(["--root", d, "ci", "--release"])
        self.assertEqual(code, 0, out)
        self.assertNotIn("skipped", out)
        self.assertNotIn("PENDING", out)
        # break it on purpose: drop one requested row from the sound list, and the G-gate fails
        with open(os.path.join(d, ui_check.SOUND_LIST), "w") as fh:
            fh.write("id,family\n" + "".join(f"{i},x\n" for i in sorted(set(ids)) if i != "FailSting"))
        code, out = run(["--root", d, "ci", "--release"])
        self.assertEqual(code, 1, out)
        self.assertIn("release: failed: sound_id FailSting requested", out)

    def test_tests_list_defaults_to_p0(self):
        code, out = run(["tests"])
        self.assertEqual(code, 0)
        self.assertIn("UmbrellaElla.UI.World.HoldToggleSetting", out)
        self.assertIn("UmbrellaElla.UI.World.TextSizeSettingScalesUI", out)
        # P1/P2 settings and the end-event test are not card 0.21's (dry run 1, H7)
        for later in ("AssistSlidersScale", "VolumeSlidersSetSoundClass", "PauseDuringEndEvent"):
            self.assertNotIn(later, out)
        self.assertIn("UmbrellaElla.UI.World.CursorShownInMenusHiddenInPlay", out)
        self.assertIn("UmbrellaElla.UI.World.QuitButtonsExit", out)
        # team meeting 11 Nov: keyboard/mouse and controller remapping, the tutorial skip and its glyphs are P0
        for now in ("RemapUpdatesPrompt", "RemapGamepadUpdatesPrompt", "TutorialSkipReachesPlay",
                    "TutorialShowsControlGlyphs"):
            self.assertIn("UmbrellaElla.UI.World." + now, out)
        self.assertEqual(len(out.split()), 11)

    def test_tests_list_by_tier(self):
        self.assertEqual(len(run(["tests", "--tier", "all"])[1].split()), 15)
        code, out = run(["tests", "--tier", "P2"])
        self.assertEqual((code, out.split()), (0, ["UmbrellaElla.UI.World.AssistSlidersScale"]))
        self.assertEqual(run(["tests", "--tier", "P9"])[0], 2)


class MouseAndQuit(unittest.TestCase):
    """Teammates' first build: no Quit (Alt+F4) and an unusable mouse cursor. Each rule fails when broken."""

    def test_mouse_fields_are_required(self):
        text = read(os.path.join(FIX, "uiflow_pass.log"))
        self.assertEqual(ui_check.flow_problems(text, "abc1234"), [])
        for f in ("mouse-menus", "mouse-play", "quit-title", "quit-pause"):
            with self.subTest(field=f):
                broken = text.replace(f" {f} pass", " ")
                self.assertNotEqual(broken, text)
                self.assertIn(f"{f}: blank (a blank field is not a pass)", ui_check.flow_problems(broken, "abc1234"))
                failed = text.replace(f"{f} pass", f"{f} fail (cursor hidden on pause)")
                self.assertIn(f"{f}: fail (cursor hidden on pause)", ui_check.flow_problems(failed, "abc1234"))

    def source(self, tmp, rel, text):
        p = os.path.join(tmp, "Source", "UmbrellaElla", rel)
        os.makedirs(os.path.dirname(p), exist_ok=True)
        with open(p, "w", encoding="utf-8") as fh:
            fh.write(text)

    def test_quit_check(self):
        rows = ui_check.read_strings(os.path.join(FIX, "strings_pass.csv"))
        self.assertEqual(ui_check.quit_problems(rows, None), [])
        no_title = [r for r in rows if r[0] != "Title.Quit"]
        self.assertTrue(any("Title.Quit" in p for p in ui_check.quit_problems(no_title, None)))
        no_pause = [r for r in rows if r[0] != "Pause.QuitToTitle"]
        self.assertTrue(any("Pause.QuitToTitle" in p for p in ui_check.quit_problems(no_pause, None)))
        tmp = tempfile.mkdtemp()
        self.addCleanup(shutil.rmtree, tmp, True)
        src = os.path.join(tmp, "Source")
        # broken on purpose: only the smoke hook and a test quit, so a player has no way out but Alt+F4
        self.source(tmp, "Private/Smoke/SmokeHook.cpp", "FPlatformMisc::RequestExit(false);\n")
        self.source(tmp, "Private/Tests/QuitTest.cpp", "UKismetSystemLibrary::QuitGame(W, nullptr, Q, false);\n")
        self.assertTrue(any("Alt+F4" in p for p in ui_check.quit_problems(None, src)))
        self.source(tmp, "Private/UI/TitleMenu.cpp", "void UTitleMenu::OnQuit() { UKismetSystemLibrary::QuitGame("
                                                     "this, nullptr, EQuitPreference::Quit, false); }\n")
        self.assertEqual(ui_check.quit_problems(None, src), [])
        code, out = run(["--root", tmp, "quit"])
        self.assertEqual(code, 0, out)
        empty = tempfile.mkdtemp()
        self.addCleanup(shutil.rmtree, empty, True)
        self.assertEqual(run(["--root", empty, "quit"])[0], 2)

    def test_ci_fails_without_quit(self):
        tmp = tempfile.mkdtemp()
        self.addCleanup(shutil.rmtree, tmp, True)
        self.source(tmp, "Private/Core/Game.cpp", "int x;\n")
        with redirect_stdout(io.StringIO()):
            self.assertTrue(any(p.startswith("quit:") for p in ui_check.run_ci(tmp)))
        self.source(tmp, "Private/UI/TitleMenu.cpp", "UKismetSystemLibrary::QuitGame(this, nullptr, Q, false);\n")
        with redirect_stdout(io.StringIO()):
            self.assertFalse(any(p.startswith("quit:") for p in ui_check.run_ci(tmp)))

    def test_gate_record_rechecks_uiflow_from_g2(self):
        import check_card
        sha = "abc1234def5678"
        line = read(os.path.join(FIX, "uiflow_pass.log")).splitlines()[-1]
        lines = {"build": f"{sha[:12]} | T.zip | Development"}
        daily = "DAILY abc1234 | x"

        def uiflow(recs, gate="G2"):
            return [p for p in check_card.machine_record_problems(lines, gate, recs, ROOT) if p.startswith("UIFLOW")]
        self.assertEqual(uiflow([daily, line]), [])
        self.assertEqual(uiflow([daily], "G1"), [])   # G1 has no player screens yet
        self.assertTrue(any("no UIFLOW line" in p for p in uiflow([daily])))
        self.assertTrue(any("mouse-menus: fail" in p for p in
                            uiflow([daily, line.replace("mouse-menus pass", "mouse-menus fail")])))
        self.assertTrue(any("no UIFLOW line" in p for p in uiflow([daily, line.replace("commit=abc1234",
                                                                                       "commit=fff9999")])))


class Screens(unittest.TestCase):
    """Every UI screen is an art-loop piece (Josh, 12 Nov): a widget class or screen with no element fails."""
    MENU_H = ("class UMBRELLAELLA_API SFlowMenu : public SCompoundWidget\n{\n};\n"
              "// class SCommented : public SCompoundWidget {};\n"
              "struct FFlowMenuItem { int x; };\n")
    RULES_H = "UENUM()\nenum class EFlowScreen : uint8\n{\n\tTitle,\n\tDefeat\n};\nenum class EFlowCommand : uint8 { Go };\n"

    def setUp(self):
        self.tmp = tempfile.mkdtemp()
        self.addCleanup(shutil.rmtree, self.tmp, True)
        self.src = os.path.join(self.tmp, "Source")
        self.put("UmbrellaElla/Public/UI/Menus/FlowMenuWidgets.h", self.MENU_H)
        self.put("UmbrellaElla/Public/Flow/FlowRules.h", self.RULES_H)
        self.refs = {"references": [{"id": "title-screen"}, {"id": "bar"}],
                     "quality_bar": {"refs": ["bar"], "default": "bar"},
                     "elements": {
                         "owl": {"refs": ["title-screen"]},
                         "ui-title": {"refs": ["title-screen"], "ui": {"widgets": ["SFlowMenu"], "screens": ["EFlowScreen::Title"]}},
                         "ui-defeated": {"refs": ["title-screen"], "ui": {"widgets": ["SFlowMenu"], "screens": ["EFlowScreen::Defeat"]}}}}

    def put(self, rel, text):
        path = os.path.join(self.src, rel)
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, "w", encoding="utf-8") as fh:
            fh.write(text)

    def problems(self):
        return ui_check.screen_problems(self.src, self.refs)

    def test_covered_screens_pass(self):
        self.assertEqual(self.problems(), [])

    def test_fake_slate_screen_without_element_fails(self):
        self.put("UmbrellaElla/Public/UI/Fake/FakeScreen.h", "class UMBRELLAELLA_API SFakeScreen : public SCompoundWidget\n{\n};\n")
        probs = self.problems()
        self.assertEqual(len(probs), 1, probs)
        self.assertIn("SFakeScreen is no art-loop piece", probs[0])
        self.refs["elements"]["ui-title"]["ui"]["widgets"].append("SFakeScreen")
        self.assertEqual(self.problems(), [])

    def test_fake_umg_final_hud_and_cpp_only_widgets_fail(self):
        self.put("UmbrellaElla/Public/UI/Fake.h",
                 "UCLASS()\nclass UMBRELLAELLA_API UFakeWidget final : public UUserWidget\n{\n};\n"
                 "class AFakeHUD : public AHUD\n{\n};\n")
        self.put("UmbrellaElla/Private/Flow/Hidden.cpp", "class SHiddenBox final : public SCompoundWidget\n{\n};\n")
        text = "\n".join(self.problems())
        for name in ("UFakeWidget", "AFakeHUD", "SHiddenBox"):
            self.assertIn(f"widget class {name} is no art-loop piece", text)

    def test_subclass_of_our_own_widget_fails(self):
        self.put("UmbrellaElla/Public/UI/Sub.h", "class SDerivedMenu : public SFlowMenu\n{\n};\n")
        self.assertTrue(any("SDerivedMenu" in p for p in self.problems()))

    def test_new_screen_enum_value_fails(self):
        self.put("UmbrellaElla/Public/Flow/FlowRules.h", self.RULES_H.replace("\tDefeat\n", "\tDefeat,\n\tShop\n"))
        probs = self.problems()
        self.assertEqual(len(probs), 1, probs)
        self.assertIn("screen EFlowScreen::Shop is no art-loop piece", probs[0])

    def test_not_a_widget_and_other_folders_and_tests_are_ignored(self):
        self.put("UmbrellaElla/Public/UI/Model.h", "class FClockModel : public FBase\n{\n};\nclass UThing : public UObject\n{\n};\n")
        self.put("UmbrellaElla/Public/Owl/Keeper.h", "class SElsewhere : public SCompoundWidget\n{\n};\n")
        self.put("UmbrellaElla/Private/Tests/UI/T.cpp", "class STestOnly : public SCompoundWidget\n{\n};\n")
        self.assertEqual(self.problems(), [])

    def test_stale_element_fails(self):
        self.refs["elements"]["ui-title"]["ui"]["widgets"].append("SGone")
        self.refs["elements"]["ui-defeated"]["ui"]["screens"].append("EFlowScreen::Gone")
        text = "\n".join(self.problems())
        self.assertIn("names widget class SGone, which is not declared", text)
        self.assertIn("names screen EFlowScreen::Gone, which is not declared", text)

    def test_element_needs_a_reference_and_a_quality_bar_and_one_screen_one_piece(self):
        self.refs["elements"]["ui-title"]["refs"] = ["unknown"]
        self.assertTrue(any("ui-title has no reference" in p for p in self.problems()))
        self.refs["elements"]["ui-title"]["refs"] = ["title-screen"]
        self.refs["quality_bar"] = {"refs": [], "default": "bar"}
        self.assertTrue(any("ui-title has no quality-bar image" in p for p in self.problems()))
        self.refs["quality_bar"] = {"refs": ["bar"], "default": "bar"}
        self.refs["elements"]["ui-defeated"]["ui"]["screens"].append("EFlowScreen::Title")
        self.assertTrue(any("named by two elements" in p for p in self.problems()))

    def test_cli_and_ci(self):
        refs = os.path.join(self.tmp, "refs.json")
        dump(self.refs, refs)
        code, out = run(["screens", "--src", self.src, "--refs", refs])
        self.assertEqual(code, 0, out)
        self.put("UmbrellaElla/Public/UI/Fake/FakeScreen.h", "class SFakeScreen : public SLeafWidget\n{\n};\n")
        code, out = run(["screens", "--src", self.src, "--refs", refs])
        self.assertEqual(code, 1, out)
        self.assertIn("SFakeScreen", out)
        os.makedirs(os.path.join(self.tmp, "pipeline", "art"))
        dump(self.refs, os.path.join(self.tmp, "pipeline", "art", "references.json"))
        with redirect_stdout(io.StringIO()):
            self.assertTrue(any(p.startswith("screens:") and "SFakeScreen" in p for p in ui_check.run_ci(self.tmp)))

    def test_repo_screens_all_have_an_element(self):
        code, out = run(["screens"])
        self.assertEqual(code, 0, out)
        with open(os.path.join(ROOT, "pipeline", "art", "references.json"), encoding="utf-8") as fh:
            els = ui_check.screen_elements(json.load(fh))
        for eid in ("ui-title", "ui-pause", "ui-settings", "ui-credits", "ui-defeated", "ui-story-text",
                    "ui-journey-complete", "ui-purchase", "ui-level-up", "ui-tutorial", "ui-hud-clock", "ui-xp-ring"):
            self.assertIn(eid, els)

    def test_repo_screen_elements_can_go_to_the_blind_critic(self):
        """The element's `what` is the critic's whole brief: a word that leaks the builder's side would stop the panel."""
        import art_loop
        with open(os.path.join(ROOT, "pipeline", "art", "references.json"), encoding="utf-8") as fh:
            refs = json.load(fh)
        for eid in ui_check.screen_elements(refs):
            prompt = art_loop.critic_prompt(refs["elements"][eid]["what"])
            self.assertEqual(art_loop.critic_prompt_problems(prompt), [], eid)


if __name__ == "__main__":
    unittest.main()
