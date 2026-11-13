"""tools/frame_check.py: a black or one-flat-colour frame fails; a frame with gameplay shapes on a backdrop passes."""
import os
import sys
import tempfile
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(os.path.dirname(HERE), "tools"))
import frame_check  # noqa: E402
from png import write_png  # noqa: E402

W, H = 160, 90


def frame(fill, boxes=()):
    rows = [[fill + (255,) for _ in range(W)] for _ in range(H)]
    for x0, y0, x1, y1, colour in boxes:
        for y in range(y0, y1):
            for x in range(x0, x1):
                rows[y][x] = colour + (255,)
    return rows


class FrameCheckTest(unittest.TestCase):
    def run_on(self, rows):
        with tempfile.TemporaryDirectory() as d:
            p = os.path.join(d, "f.png")
            write_png(p, W, H, rows)
            return frame_check.check(p)

    def test_black_frame_fails(self):
        res = self.run_on(frame((0, 0, 0), [(5, 5, 20, 12, (250, 250, 250))]))
        self.assertFalse(res["pass_"])
        self.assertTrue(any("black" in p for p in res["problems"]))

    def test_flat_grey_frame_fails(self):
        res = self.run_on(frame((88, 85, 80)))
        self.assertFalse(res["pass_"])
        self.assertTrue(any("flat" in p for p in res["problems"]))

    def test_gameplay_on_backdrop_passes(self):
        res = self.run_on(frame((88, 85, 80), [(20, 20, 70, 70, (190, 175, 210)), (100, 40, 112, 70, (225, 215, 90))]))
        self.assertTrue(res["pass_"], res["problems"])


if __name__ == "__main__":
    unittest.main()
