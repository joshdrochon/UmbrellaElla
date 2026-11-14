"""dcseamless (Josh, Nov 13 23:45): the Director's Cut route must read as one seamless painted world. art_scene_frameseam.py
finds straight picture/panel edges in a captured frame; it FAILs the route frames captured on main dab58cfa (start
picture's hard right edge, end picture's hard left edge, the arena's stand-in planes) and PASSes the same route stops
after the fix (edge-faded start/end pictures, arena stand-in planes hidden, no layer wrap)."""
import os
import sys
import unittest

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, os.path.join(ROOT, "tools", "build", "assets"))
import art_scene_frameseam as fs  # noqa: E402

PROOF = os.path.join(ROOT, "pipeline", "art", "proof", "dcseamless")
# Ella's drawn x in each capture (from its journey.log), so her rope is not read as a seam.
BEFORE = {"005": 640, "010": 640, "033": 776}
AFTER = {"005": 632, "010": 640, "033": 776}


def frame(w, h, value_at):
    return [[tuple(int(round(v)) for v in value_at(x, y)) + (255,) for x in range(w)] for y in range(h)]


def is_real_png(path):
    with open(path, "rb") as fh:
        return fh.read(8) == b"\x89PNG\r\n\x1a\n"


class FrameSeamSynthetic(unittest.TestCase):
    W, H = 320, 720

    def scores(self, value_at, ella_x=10):
        L = [[0.2126 * p[0] + 0.7152 * p[1] + 0.0722 * p[2] for p in row] for row in frame(self.W, self.H, value_at)]
        col, row = fs.frame_scores(self.W, self.H, L, ella_x)
        return max(col), max(row)

    def test_hard_picture_edge_fails(self):
        c, _ = self.scores(lambda x, y: (40, 38, 35) if x < 200 else (22, 20, 18))
        self.assertGreaterEqual(c, fs.SEAM_LIMIT)

    def test_same_edge_faded_passes(self):
        def faded(x, y):
            t = min(1.0, max(0.0, (x - 120) / 160.0))   # the edge-fade material's linear ramp over 160 px
            return tuple(a + (b - a) * t for a, b in zip((40, 38, 35), (22, 20, 18)))
        c, _ = self.scores(faded)
        self.assertLess(c, fs.SEAM_LIMIT)

    def test_horizontal_panel_edge_fails(self):
        _, r = self.scores(lambda x, y: (18, 18, 18) if y < 53 else (15, 15, 15))
        self.assertGreaterEqual(r, fs.SEAM_LIMIT - 0.01)

    def test_rope_is_ignored(self):
        c, _ = self.scores(lambda x, y: (200, 200, 200) if x == 250 else (20, 20, 20), ella_x=250)
        self.assertLess(c, fs.SEAM_LIMIT)


class FrameSeamCaptures(unittest.TestCase):
    def check(self, name, ella_x):
        path = os.path.join(PROOF, name)
        if not is_real_png(path):
            self.skipTest("%s is an LFS pointer here" % name)
        c, _, r, _ = fs.check(path, ella_x)
        return max(c, r)

    def test_main_route_frames_fail(self):
        for n, x in BEFORE.items():
            self.assertGreaterEqual(self.check("route-before-%s.png" % n, x), fs.SEAM_LIMIT, n)

    def test_fixed_route_frames_pass(self):
        for n, x in AFTER.items():
            self.assertLess(self.check("route-after-%s.png" % n, x), fs.SEAM_LIMIT, n)


if __name__ == "__main__":
    unittest.main()
