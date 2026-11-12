"""tools/screen_check.py: no debug or placeholder visuals in the default build, and the 16:9 lock, on a screenshot.

Synthetic PNGs are built in a temp folder (PNGs go through Git LFS, so none is committed): an etched-style frame and a
pillarboxed ultrawide frame must pass; the frames broken on purpose (a flat teal wind box with swirl glyphs, the grey
hitbox box under the owl, a debug outline, an ultrawide frame with no bars) must fail for their reason."""
import io
import math
import os
import random
import sys
import tempfile
import unittest
from contextlib import redirect_stdout

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, os.path.join(ROOT, "tools"))
import screen_check  # noqa: E402
from png import write_png  # noqa: E402

W, H = 320, 180
PAPER = (176, 152, 118)
INK = (22, 18, 16)


def paper(w=W, h=H, seed=7):
    """Mottled paper: every pixel varies, so no flat region forms."""
    rnd = random.Random(seed)
    return [[tuple(max(0, min(255, c + rnd.randint(-9, 9))) for c in PAPER) + (255,) for _ in range(w)]
            for _ in range(h)]


def put(rows, x, y, col):
    if 0 <= y < len(rows) and 0 <= x < len(rows[0]):
        rows[y][x] = tuple(col[:3]) + (255,)


def etched_zone(rows, x0, y0, w, h, seed=3):
    """The look the art bible asks for: paper tint, etched upward wavy lines, a broken engraved border."""
    rnd = random.Random(seed)
    for y in range(y0, y0 + h):
        for x in range(x0, x0 + w):
            r, g, b, a = rows[y][x]
            rows[y][x] = (max(0, r - 10), max(0, g - 6), max(0, b - 2), a)   # subtle tint, texture kept
    for k in range(6):
        cx = x0 + 8 + k * (w - 16) // 5
        for y in range(y0 + 4, y0 + h - 4):
            if rnd.random() < 0.85:
                put(rows, cx + int(3 * math.sin(y / 6.0 + k)), y, (60 + rnd.randint(0, 20), 48, 36))
    for x in range(x0, x0 + w):
        if (x // 3) % 2 == 0:
            put(rows, x, y0, (70, 56, 40))
            put(rows, x, y0 + h - 1, (70, 56, 40))


def owl(rows, cx, cy, r):
    for y in range(cy - r, cy + r):
        for x in range(cx - r, cx + r):
            if (x - cx) ** 2 + (y - cy) ** 2 < r * r:
                put(rows, x, y, INK)


class ScreenCheck(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.mkdtemp()

    def shot(self, name, rows):
        p = os.path.join(self.tmp, name + ".png")
        write_png(p, len(rows[0]), len(rows), rows)
        return p

    def run_cli(self, *args):
        out = io.StringIO()
        with redirect_stdout(out):
            rc = screen_check.main(list(args))
        return rc, out.getvalue()

    def kinds(self, path):
        return {p["kind"] for p in screen_check.check(path)["problems"]}

    def test_etched_frame_passes(self):
        rows = paper()
        etched_zone(rows, 120, 40, 70, 110)
        owl(rows, 260, 80, 40)   # a big near-black silhouette is not a rectangle: never flagged
        rc, out = self.run_cli(self.shot("etched", rows))
        self.assertEqual(rc, 0, out)
        self.assertIn("screen_check: PASS", out)
        self.assertIn("view=320x180 aspect=1.778 bars=none flat=0 grey=0 outline=0", out)

    def test_flat_teal_wind_box_fails(self):
        """Broken on purpose: the teammate's first build drew WIND-01 as a solid teal box with swirl glyphs."""
        rows = paper()
        for y in range(40, 150):
            for x in range(120, 190):
                put(rows, x, y, (42, 157, 143))
        for k in range(4):   # placeholder swirl glyphs on top
            for a in range(0, 360, 20):
                put(rows, 140 + 10 * (k % 2) + int(5 * math.cos(math.radians(a))),
                    60 + 25 * k + int(5 * math.sin(math.radians(a))), (230, 240, 240))
        p = self.shot("teal", rows)
        self.assertEqual(self.kinds(p), {"flat"})
        rc, out = self.run_cli(p)
        self.assertEqual(rc, 1)
        self.assertIn("flat: x=120 y=40 w=70 h=110 colour=#2a9d8f", out)
        self.assertIn("FIX: flat: replace the flat fill with etched art", out)

    def test_grey_hitbox_box_under_owl_fails(self):
        rows = paper()
        owl(rows, 240, 70, 40)
        for y in range(118, 132):
            for x in range(220, 262):
                put(rows, x, y, (128, 128, 128))
        p = self.shot("grey", rows)
        self.assertEqual(self.kinds(p), {"grey"})
        self.assertIn("FIX: grey: a debug draw or a placeholder", self.run_cli(p)[1])

    def test_debug_outline_fails(self):
        rows = paper()
        for x in range(100, 200):
            put(rows, x, 50, (0, 255, 0))
            put(rows, x, 120, (0, 255, 0))
        for y in range(50, 121):
            put(rows, 100, y, (0, 255, 0))
            put(rows, 199, y, (0, 255, 0))
        self.assertEqual(self.kinds(self.shot("outline", rows)), {"outline"})

    def test_ultrawide_without_bars_fails_aspect(self):
        """Broken on purpose: the ~1.85:1 window with gameplay stretched to it (no 16:9 lock)."""
        p = self.shot("wide", paper(370, 200))
        self.assertEqual(self.kinds(p), {"aspect"})
        rc, out = self.run_cli(p)
        self.assertEqual(rc, 1)
        self.assertIn("aspect=1.850 bars=none", out)
        self.assertIn("FIX: aspect: lock the gameplay view to 16:9", out)

    def test_pillarboxed_ultrawide_passes(self):
        inner = paper(192, 108)
        rows = [[(0, 0, 0, 255)] * 32 + r + [(0, 0, 0, 255)] * 32 for r in inner]   # 256x108, 21:9 window
        rc, out = self.run_cli(self.shot("pillar", rows))
        self.assertEqual(rc, 0, out)
        self.assertIn("view=192x108 aspect=1.778 bars=pillarbox", out)

    def test_letterboxed_16x10_passes_and_ui_in_the_bars_fails(self):
        inner = paper(160, 90)
        bar = [[(0, 0, 0, 255)] * 160 for _ in range(5)]
        rows = bar + inner + [list(r) for r in bar]   # 160x100 (16:10)
        rc, out = self.run_cli(self.shot("letter", rows))
        self.assertEqual(rc, 0, out)
        self.assertIn("view=160x90 aspect=1.778 bars=letterbox", out)
        rows[1][5] = (230, 200, 90, 255)   # a HUD widget drawn into the top bar: the bars no longer read as bars
        rows[98][150] = (230, 200, 90, 255)
        self.assertIn("aspect", self.kinds(self.shot("letter_ui", rows)))

    def test_dark_band_on_one_edge_is_scene_not_a_bar(self):
        rows = paper()
        for y in range(170, 180):
            for x in range(W):
                put(rows, x, y, (4, 4, 4))   # the black rock band along the bottom only
        res = screen_check.check(self.shot("rock", rows))
        self.assertEqual(res["bars"], "none")
        self.assertNotIn("aspect", {p["kind"] for p in res["problems"]})

    def test_ignore_box_and_bad_input(self):
        rows = paper()
        for y in range(10, 40):
            for x in range(10, 80):
                put(rows, x, y, (90, 70, 50))   # a flat HUD panel the look allows
        p = self.shot("hud", rows)
        self.assertEqual(self.kinds(p), {"flat"})
        rc, out = self.run_cli(p, "--ignore", "10,10,70,30")
        self.assertEqual(rc, 0, out)
        self.assertIn("ignoring x=10 y=10 w=70 h=30", out)
        bad = os.path.join(self.tmp, "x.png")
        with open(bad, "w") as fh:
            fh.write("not a png")
        self.assertEqual(self.run_cli(bad)[0], 2)

    def test_strict_catches_placeholder_glyph_dots_and_boxes(self):
        """Tutorial: grey dots and boxes standing in for key and button glyphs fail under --strict."""
        rows = paper()
        for i, cx in enumerate((60, 100, 140)):
            for y in range(81, 91):
                for x in range(cx - 5, cx + 5):
                    if i == 0 or (x - cx) ** 2 + (y - 86) ** 2 <= 25:
                        put(rows, x, y, (150, 150, 150))   # one box, two round dots
        p = self.shot("tutorial", rows)
        self.assertEqual(self.run_cli(p)[0], 0)              # too small for the default thresholds
        rc, out = self.run_cli(p, "--strict")
        self.assertEqual(rc, 1, out)
        self.assertIn("grey=3", out)
        rows = paper()
        etched_zone(rows, 50, 70, 24, 24, seed=5)                # an etched glyph passes strict
        self.assertEqual(self.run_cli(self.shot("glyph", rows), "--strict")[0], 0)

    def test_style_json_holds_the_thresholds(self):
        t = screen_check.thresholds()
        for k in screen_check.DEFAULTS:
            self.assertIn(k, t)
        self.assertEqual(screen_check.ratio(t["aspect"]), 16 / 9)


if __name__ == "__main__":
    unittest.main()
