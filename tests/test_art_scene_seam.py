"""BG-02 tileability: art_scene_seam.py finds a picture cut by its canvas edge at a repeat join, and the cross-fade
that art_scene_world.py repeatN applies removes it (artscene, lead order Nov 13 18:28)."""
import os
import sys
import unittest

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, os.path.join(ROOT, "tools", "build", "assets"))
import art_scene_seam as seam  # noqa: E402

PROOF = os.path.join(ROOT, "pipeline", "art", "proof", "scene")
CLEAR = (0.0, 0.0, 0.0, 0.0)


def island_row(w, x_from, x_to, colour=(0.3, 0.25, 0.2)):
    return [colour + (1.0,) if x_from <= x < x_to else CLEAR for x in range(w)]


def tile(rows, n):
    return [list(r) * n for r in rows]


def picture(w, h, islands):
    """h rows; islands: (x_from, x_to) spans of an opaque island crossing every row, like a cropped skyline."""
    rows = []
    for _ in range(h):
        row = [CLEAR] * w
        for a, b in islands:
            for x in range(a, b):
                row[x] = (0.3 + 0.002 * x, 0.25, 0.2, 1.0)   # a gentle gradient, as paint has
        rows.append(row)
    return rows


class SeamCheck(unittest.TestCase):
    def check(self, rows, n):
        joins = seam.join_columns(len(rows[0]), 0.0, 1.0, n)
        limit = seam.interior_limit(rows, step=3, skip=joins)
        return [seam.column_pair_score(rows, xl, xr) for xl, xr in joins], limit

    def test_cut_island_at_the_join_fails(self):
        # island runs into the right edge (cut), the left edge is empty sky: a hard vertical seam when tiled
        piece = picture(120, 12, [(20, 40), (80, 120)])
        scores, limit = self.check(tile(piece, 2), 2)
        self.assertGreater(scores[0], limit)
        self.assertGreater(scores[0], 0.5)

    def test_cross_faded_piece_passes(self):
        piece = picture(120, 12, [(20, 40), (80, 120)])
        fixed = [seam.make_tileable(r, 14) for r in piece]
        scores, limit = self.check(tile(fixed, 2), 2)
        self.assertLessEqual(scores[0], limit)

    def test_continuous_band_passes(self):
        piece = picture(90, 10, [(0, 90)])
        fixed = [seam.make_tileable(r, 10) for r in piece]
        scores, limit = self.check(tile(fixed, 3), 3)
        for s in scores:
            self.assertLessEqual(s, limit)

    def test_empty_join_is_no_seam(self):
        piece = picture(100, 8, [(30, 60)])
        scores, _ = self.check(tile(piece, 2), 2)
        self.assertEqual(scores[0], 0.0)

    def test_crossfade_weights_run_from_end_to_start(self):
        w = seam.crossfade_weights(5)
        self.assertEqual(w[0], 0.0)
        self.assertEqual(w[-1], 1.0)
        row = [(float(x), 0.0, 0.0, 1.0) for x in range(10)]
        out = seam.make_tileable(row, 3)
        self.assertEqual(len(out), 7)
        self.assertEqual(out[0][0], 7.0)          # starts on the source column after the tile's last one (6)
        self.assertEqual(out[-1][0], 6.0)


@unittest.skipUnless(os.path.isfile(os.path.join(PROOF, "skyline", "world_r7_post.png")), "proof images not checked out")
class ShippedRepeats(unittest.TestCase):
    """The committed posts: r6 skyline (before the fix) fails; the cross-faded r7 skyline and r4 clock rims pass."""

    def test_old_skyline_fails(self):
        ok, _, _ = seam.check(os.path.join(PROOF, "skyline", "world_r6_post.png"), 0.0, 1.0, 3)
        self.assertFalse(ok)

    def test_fixed_skyline_passes(self):
        ok, scores, limit = seam.check(os.path.join(PROOF, "skyline", "world_r7_post.png"), 0.0, 1.0, 3)
        self.assertTrue(ok, (scores, limit))

    def test_fixed_clock_rims_pass(self):
        ok, scores, limit = seam.check(os.path.join(PROOF, "bg-clock", "world_r4_post.png"), 0.0, 1.0, 2)
        self.assertTrue(ok, (scores, limit))


if __name__ == "__main__":
    unittest.main()
