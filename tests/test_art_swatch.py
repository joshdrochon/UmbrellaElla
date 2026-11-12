"""Tests for the engine colour round-trip check: art_check.py --swatch and
make_art_calibration.py --swatch. A swatch that came back unchanged passes; one that
went through a tone curve (as an unlocked post-process would do) fails."""
import io
import json
import os
import sys
import tempfile
import unittest
from contextlib import redirect_stdout

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, os.path.join(ROOT, "tools"))
import art_check  # noqa: E402
import make_art_calibration  # noqa: E402
from png import read_png, write_png  # noqa: E402

STYLE = json.load(open(os.path.join(ROOT, "pipeline", "art", "style.json")))


class SwatchTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.mkdtemp()
        self.src = os.path.join(self.tmp, "T_Swatch_Palette.png")
        with redirect_stdout(io.StringIO()):
            self.assertEqual(make_art_calibration.main(["--swatch", self.src]), 0)

    def capture(self, fn, pad=0):
        """Fake capture: the swatch, each pixel passed through fn, framed by `pad` px of black."""
        w, h, rows = read_png(self.src)
        out = [[(0, 0, 0, 255)] * (w + 2 * pad) for _ in range(pad)]
        out += [[(0, 0, 0, 255)] * pad + [fn(p) for p in r] + [(0, 0, 0, 255)] * pad for r in rows]
        out += [[(0, 0, 0, 255)] * (w + 2 * pad) for _ in range(pad)]
        p = os.path.join(self.tmp, "cap.png")
        write_png(p, len(out[0]), len(out), out)
        return p

    def test_swatch_has_one_cell_per_palette_entry(self):
        w, h, _ = read_png(self.src)
        sw = STYLE["swatch"]
        self.assertEqual(w, sw["cols"] * sw["cell_px"])
        self.assertEqual(h, -(-len(STYLE["palette"]) // sw["cols"]) * sw["cell_px"])

    def test_unchanged_swatch_passes(self):
        cells = art_check.measure_swatch(self.capture(lambda p: p), STYLE)
        self.assertEqual(len(cells), len(STYLE["palette"]))
        self.assertTrue(all(c["pass"] for c in cells), cells)

    def test_tone_curve_fails(self):
        lift = lambda p: tuple(min(255, int(255 * (v / 255) ** 0.8)) for v in p[:3]) + (p[3],)  # noqa: E731
        cells = art_check.measure_swatch(self.capture(lift), STYLE)
        self.assertFalse(all(c["pass"] for c in cells))
        with redirect_stdout(io.StringIO()):
            self.assertEqual(art_check.main(["--swatch", self.capture(lift)]), 1)

    def test_small_shift_under_limit_passes_and_over_limit_fails(self):
        nudge = lambda d: (lambda p: (min(255, p[0] + d), p[1], p[2], p[3]))  # noqa: E731
        self.assertTrue(all(c["pass"] for c in art_check.measure_swatch(self.capture(nudge(1)), STYLE)))
        self.assertFalse(all(c["pass"] for c in art_check.measure_swatch(self.capture(nudge(12)), STYLE)))

    def test_rect_locates_the_swatch_in_a_larger_capture(self):
        p = self.capture(lambda q: q, pad=20)
        self.assertFalse(all(c["pass"] for c in art_check.measure_swatch(p, STYLE)))  # wrong rect
        style = json.loads(json.dumps(STYLE))
        w, h, _ = read_png(self.src)
        style["swatch"]["rect"] = [20, 20, w, h]
        self.assertTrue(all(c["pass"] for c in art_check.measure_swatch(p, style)))
        with redirect_stdout(io.StringIO()):
            sp = os.path.join(self.tmp, "style.json")
            with open(sp, "w") as fh:
                json.dump(style, fh)
            self.assertEqual(art_check.main(["--swatch", "--style", sp, p]), 0)


if __name__ == "__main__":
    unittest.main()
