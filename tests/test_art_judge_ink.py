"""The off-band measure ignores dark ink pixels (D-new-vfx-calibration, 13 Nov).

A crisp ink-lined crimson effect must not trip the off-band gate (ink carries no hue); a flood-filled off-palette
effect (teal, ink-lined too) must still fail it.
"""
import os
import sys
import tempfile
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, os.path.join(ROOT, "tools"))
sys.path.insert(0, HERE)
import hermetic  # noqa: E402,F401
import art_judge  # noqa: E402
from png import write_png  # noqa: E402

INK = (23, 22, 20, 255)


def ring(fill, size=128, line=3):
    """A filled disc in `fill` with an ink outline `line` px wide and thin ink hatching inside."""
    c, r = size / 2, size * 0.4
    rows = []
    for y in range(size):
        row = []
        for x in range(size):
            d = ((x - c) ** 2 + (y - c) ** 2) ** 0.5
            if d > r:
                row.append((0, 0, 0, 0))
            elif d > r - line or (d < r - line and (x + y) % 9 == 0):
                row.append(INK)
            else:
                row.append(fill)
        rows.append(row)
    return rows


class InkIgnored(unittest.TestCase):
    def sig(self, fill):
        d = tempfile.mkdtemp()
        p = os.path.join(d, "fx.png")
        write_png(p, 128, 128, ring(fill))
        return art_judge.signature(p)

    def test_crisp_ink_lined_crimson_effect_passes_the_offband_gate(self):
        s = self.sig((255, 54, 88, 255))   # GDD crimson FF3658
        self.assertGreater(s["dark"], 0.1, "the ink is there")
        self.assertLessEqual(s["offband"], 0.05, s["offband"])

    def test_flood_filled_off_palette_effect_fails_it(self):
        s = self.sig((20, 170, 160, 255))   # teal
        self.assertGreater(s["offband"], 0.05, s["offband"])


if __name__ == "__main__":
    unittest.main()
