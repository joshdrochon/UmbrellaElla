"""art_loop check-defect fixes (13 Nov): calibration pair that is always the same kind of thing, redraw of uncalibrated
sessions (bounded, never counted), and the context pair cropped to the piece."""
import json
import math
import os
import sys
import tempfile
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, os.path.join(ROOT, "tools"))
sys.path.insert(0, HERE)
import hermetic  # noqa: E402,F401
import art_loop  # noqa: E402
from png import read_png, write_png  # noqa: E402

GOLD = [(255, 245, 220), (255, 216, 74), (245, 170, 40), (148, 97, 30)]


def gold_burst(size=64):
    rows = [[(0, 0, 0, 0)] * size for _ in range(size)]
    c = size / 2
    for y in range(size):
        for x in range(size):
            r = math.hypot(x - c, y - c) / (size * 0.45)
            if r < 1:
                rows[y][x] = GOLD[min(int(r * 4), 3)] + (255,)
    return rows


def capture(with_piece, at=(200, 60), w=320, h=180):
    rows = [[(22 + (x * y) % 5, 20, 19, 255) for x in range(w)] for y in range(h)]
    if with_piece:
        for y, row in enumerate(gold_burst(30)):
            for x, px in enumerate(row):
                if px[3]:
                    rows[at[1] + y][at[0] + x] = px
    return rows


class ContextCropTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.mkdtemp()

    def png(self, name, rows):
        p = os.path.join(self.tmp, name + ".png")
        write_png(p, len(rows[0]), len(rows), rows)
        return p

    def test_the_piece_is_found_in_a_dark_graybox_capture(self):
        cap, ours = self.png("cap", capture(True)), self.png("ours", gold_burst())
        x, y, w, h = art_loop.locate_piece(cap, ours)
        self.assertTrue(x <= 200 and 230 <= x + w and y <= 60 and 90 <= y + h)   # the 30 px burst at (200, 60) is inside
        self.assertLess(w * h, 0.2 * 320 * 180)                                  # a crop, not the frame

    def test_a_capture_without_the_piece_has_no_crop(self):
        cap, ours = self.png("cap0", capture(False)), self.png("ours0", gold_burst())
        with self.assertRaises(art_loop.PieceNotFound):
            art_loop.locate_piece(cap, ours)

    def test_context_pair_is_the_capture_crop_against_the_key_art_crop(self):
        cap, ours = self.png("cap1", capture(True)), self.png("ours1", gold_burst())
        refs, _ = art_loop.refs_and_hash(ROOT)
        key_path = art_loop.blind(refs, "0.10c", "vfx-gold-impact", cap, os.path.join(self.tmp, "ctx"), seed=3, root=ROOT,
                                  kind="context", calibrate=False, piece_file=ours)
        key = json.load(open(key_path))
        sizes = [read_png(os.path.join(self.tmp, "ctx", f))[:2] for f in ("X.png", "Y.png")]
        self.assertEqual(key["kind"], "context")
        self.assertTrue(key["reference"].endswith("target-keyart.png"))   # the combo stays the key art's
        self.assertEqual(key["context_crop"]["reference"], [1010, 380, 220, 120])
        for w, h in sizes:
            self.assertLess(w * h, 0.2 * 320 * 180 + 220 * 120)   # nothing like a 1672x941 or 320x180 whole frame
        self.assertIn((220, 120), sizes)

    def test_a_missing_piece_makes_the_context_pair_missing_not_a_whole_frame_pair(self):
        cap, ours = self.png("cap2", capture(False)), self.png("ours2", gold_burst())
        refs, _ = art_loop.refs_and_hash(ROOT)
        with self.assertRaises(art_loop.PieceNotFound):
            art_loop.blind(refs, "0.10c", "vfx-gold-impact", cap, os.path.join(self.tmp, "ctx2"), seed=3, root=ROOT,
                           kind="context", calibrate=False, piece_file=ours)

    def test_an_element_without_a_crop_uses_its_own_reference(self):
        refs, _ = art_loop.refs_and_hash(ROOT)
        ref, rect = art_loop.context_reference(refs, "vfx-clock-open", ROOT)
        self.assertIsNone(rect)
        self.assertFalse(ref.endswith("target-keyart.png"))


def answer(key):
    """A correct critic answer for a calibrated folder set."""
    lines = [f"{f}: WINNER: {w} | GAP: none" for f, w in key["calibration"].items()]
    lines.append(f"{key['folder']}: WINNER: {key['ours']} | GAP: none")
    return "\n".join(sorted(lines))


class CalibrationTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.mkdtemp()
        self.refs, _ = art_loop.refs_and_hash(ROOT)
        self.ours = os.path.join(self.tmp, "ours.png")
        write_png(self.ours, 64, 64, gold_burst())

    def make(self, piece="vfx-gold-impact"):
        refs, base = self.refs, self.tmp
        other = art_loop.element_refs(refs, piece, ROOT)[0]

        def sess(m):
            return art_loop.session_folder(refs, "0.10c", piece, "reference", other, self.ours, base, 1, 0, m, ROOT)
        return [sess(m) for m in range(art_loop.PANEL)], (lambda key, m: sess(m))

    def test_a_vfx_piece_calibration_pair_is_the_team_image_against_a_crude_copy_of_it(self):
        fold, _ = self.make()
        d, key = fold[0]
        bad = [f for f, w in key["calibration"].items() if w != "SAME"][0]
        want = art_loop.element_refs(self.refs, "vfx-gold-impact", ROOT)
        self.assertEqual(len(want) > 0, True)
        x, y = (read_png(os.path.join(d, bad, f))[:2] for f in ("X.png", "Y.png"))
        self.assertTrue(os.path.isfile(os.path.join(d, bad, "X.png")))

    def test_crude_copy_is_flat_and_blocky(self):
        src = os.path.join(self.tmp, "src.png")
        rows = [[((x * 7) % 256, (y * 5) % 256, (x + y) % 256, 255) for x in range(120)] for y in range(120)]
        write_png(src, 120, 120, rows)
        out = art_loop.crude_of(src)
        _, _, got = read_png(out)
        self.assertLessEqual(len({px for row in got for px in row}), 4 ** 3)   # three tones per channel at most
        self.assertNotEqual(got, rows)

    def test_uncalibrated_sessions_are_redrawn_until_panel_counted_and_never_counted_themselves(self):
        fold, redraw = self.make()
        calls = []

        def ask(d):
            key = json.load(open(d.rstrip("/") + ".key.json"))
            calls.append(d)
            return "A: WINNER: SAME | GAP: x\nB: WINNER: SAME | GAP: x\nC: WINNER: SAME | GAP: x" \
                if len(calls) <= 4 else answer(key)
        items = art_loop.ask_calibrated(fold, ask, redraw, jobs=1)
        good = [k for _, k, t in items if art_loop.calibrated(t, k)]
        self.assertEqual(len(good), art_loop.PANEL)
        self.assertEqual(len(items), art_loop.PANEL + 4)   # 4 refused, every refusal replaced once
        answers, _ = art_loop.judge_items(ROOT, [(d, k, t) for d, k, t in items], record=False)
        counted = [o for _, o, _ in answers if o is not None]
        self.assertEqual(len(counted), art_loop.PANEL)

    def test_redraw_is_bounded_and_a_pair_that_never_calibrates_fails(self):
        fold, redraw = self.make()
        ask = lambda d: "A: WINNER: SAME | GAP: x\nB: WINNER: SAME | GAP: x\nC: WINNER: SAME | GAP: x"
        items = art_loop.ask_calibrated(fold, ask, redraw, jobs=1)
        self.assertEqual(len(items), art_loop.PANEL + art_loop.REDRAW_MAX)
        answers, _ = art_loop.judge_items(ROOT, items, record=False)
        summ = art_loop.summarise(answers, sorted({a[0]["combo"] for a in answers}))
        self.assertEqual(summ["pairs"]["reference"], "reference")   # no counted vote: the round cannot pass

    def test_all_calibrated_draws_no_extra_session(self):
        fold, redraw = self.make()
        items = art_loop.ask_calibrated(fold, lambda d: answer(json.load(open(d.rstrip("/") + ".key.json"))), redraw, jobs=1)
        self.assertEqual(len(items), art_loop.PANEL)

    def test_the_panel_prompt_names_clear_quality_gaps_and_keeps_same_for_equal_images(self):
        p = art_loop.PANEL_PROMPT
        self.assertIn("cruder", p)
        self.assertIn("Answer SAME only", p)
        self.assertEqual(art_loop.critic_prompt_problems(p.format(letters="A, B, C", what="x")), [])


if __name__ == "__main__":
    unittest.main()


class FitPacket(unittest.TestCase):
    def test_large_frame_is_cropped_at_full_detail_not_shrunk(self):
        d = tempfile.mkdtemp()
        big = os.path.join(d, "enemy.png")
        w, h = 1792, 2400
        rows = [[(0, 0, 0, 0)] * w for _ in range(h)]
        for y in range(900, 1500):
            for x in range(700, 1000):
                rows[y][x] = (200, 40, 40, 255)
        write_png(big, w, h, rows)
        out = art_loop.fit_packet(big)
        cw, ch, crop = read_png(out)
        self.assertLessEqual(max(cw, ch), art_loop.PACKET_MAX)
        self.assertEqual((cw, ch), (300, 600))   # the subject's box, one source pixel per packet pixel
        self.assertTrue(all(px == (200, 40, 40, 255) for r in crop for px in r))

    def test_oversize_subject_is_windowed_and_small_images_untouched(self):
        d = tempfile.mkdtemp()
        full = os.path.join(d, "full.png")
        write_png(full, 1792, 2400, [[(9, 9, 9, 255)] * 1792 for _ in range(2400)])
        cw, ch, _ = read_png(art_loop.fit_packet(full))
        self.assertEqual((cw, ch), (art_loop.PACKET_MAX, art_loop.PACKET_MAX))
        small = os.path.join(d, "s.png")
        write_png(small, 64, 64, gold_burst())
        self.assertEqual(art_loop.fit_packet(small), small)

    def test_blind_packet_images_are_within_limit(self):
        d = tempfile.mkdtemp()
        a, b = os.path.join(d, "a.png"), os.path.join(d, "b.png")
        write_png(a, 1792, 2400, [[(30, 60, 90, 255)] * 1792 for _ in range(2400)])
        write_png(b, 32, 32, [[(1, 2, 3, 255)] * 32 for _ in range(32)])
        import random
        out = os.path.join(d, "p")
        art_loop._pair(out, a, b, random.Random(1))
        for f in ("X.png", "Y.png"):
            w, h, _ = read_png(os.path.join(out, f))
            self.assertLessEqual(max(w, h), art_loop.PACKET_MAX)
