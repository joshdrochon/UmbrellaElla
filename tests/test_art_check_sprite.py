"""art_check's sprite/effect mode (check defect fix, 13 Nov): colour rules read only the non-transparent pixels, an
effect against the effect palette. A gold burst with bronze shading passes; a teal/magenta burst fails."""
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
import art_check  # noqa: E402
from png import write_png  # noqa: E402

STYLE = json.load(open(os.path.join(ROOT, "pipeline", "art", "style.json")))
N = 96


def burst(ramp, size=N):
    """A radial burst on a transparent ground: colour runs through `ramp` (hex list) from the core out; the edge is soft."""
    cols = [art_check.hex_to_rgb(h) for h in ramp]
    rows = [[(0, 0, 0, 0)] * size for _ in range(size)]
    c = size / 2
    for y in range(size):
        for x in range(size):
            r = math.hypot(x - c, y - c) / (size * 0.42)
            if r >= 1:
                continue
            t = r * (len(cols) - 1)
            i = min(int(t), len(cols) - 2)
            f = t - i
            px = tuple(round(cols[i][k] + (cols[i + 1][k] - cols[i][k]) * f) for k in range(3))
            rows[y][x] = px + (255 if r < 0.85 else int(255 * (1 - r) / 0.15),)
    return rows


class SpriteModeTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.mkdtemp()

    def png(self, name, rows):
        p = os.path.join(self.tmp, name + ".png")
        write_png(p, len(rows[0]), len(rows), rows)
        return p

    def test_gold_burst_with_bronze_shading_passes_as_an_effect(self):
        p = self.png("gold", burst(["#FFF5DC", "#FFD84A", "#F5AA28", "#B4741F", "#94611E"]))
        self.assertEqual(art_check.sprite_failures(p, STYLE, effect=True), [])

    def test_the_effect_palette_is_what_passes_it(self):
        p = self.png("gold2", burst(["#FFF5DC", "#FFD84A", "#F5AA28", "#B4741F", "#94611E"]))
        plain = art_check.sprite_failures(p, STYLE, effect=False)
        eff = art_check.sprite_failures(p, STYLE, effect=True)
        self.assertGreater(len(plain), len(eff))   # the bronze ramp is off the brand palette, on the effect palette

    def test_red_shot_with_shadow_red_passes_as_an_effect(self):
        p = self.png("red", burst(["#FFF5DC", "#FF7848", "#FF3658", "#8F173C"]))
        self.assertEqual(art_check.sprite_failures(p, STYLE, effect=True), [])

    def test_teal_magenta_burst_fails_as_an_effect(self):
        p = self.png("bad", burst(["#FFFFFF", "#17E0D0", "#2040FF", "#D020C0"]))
        fails = art_check.sprite_failures(p, STYLE, effect=True)
        self.assertTrue(any(f.startswith("off_style") for f in fails) or any(f.startswith("on_palette") for f in fails))
        self.assertTrue(any(f.startswith("off_band") for f in fails))

    def test_flat_blue_sprite_fails_as_a_sprite(self):
        rows = [[(30, 80, 255, 255)] * N for _ in range(N)]
        self.assertTrue(art_check.sprite_failures(self.png("blue", rows), STYLE, effect=False))

    def test_the_transparent_ground_never_counts(self):
        rows = burst(["#FFF5DC", "#FFD84A", "#F5AA28", "#94611E"])
        big = [[(0, 0, 0, 0)] * (N * 3) for _ in range(N * 3)]
        for y in range(N):
            big[y + N][N:2 * N] = rows[y]
        a = art_check.measure_sprite(self.png("a", rows), STYLE, True)[0]
        b = art_check.measure_sprite(self.png("b", big), STYLE, True)[0]
        for k in ("on_palette", "off_style", "off_band"):
            self.assertAlmostEqual(a[k], b[k], delta=0.02)

    def test_effect_mode_does_not_loosen_the_thresholds(self):
        st = art_check.effect_style(STYLE)
        self.assertEqual(st["thresholds"], STYLE["thresholds"])
        self.assertEqual(st["delta_e_tolerance"], STYLE["delta_e_tolerance"])
        self.assertNotIn(190, range(*[int(v) for v in st["hue_gate"]["allowed_hue_bands_deg"][0]]))   # teal stays out

    def test_cli(self):
        p = self.png("cli", burst(["#FFF5DC", "#FFD84A", "#F5AA28", "#94611E"]))
        self.assertEqual(art_check.main([p, "--effect"]), 0)
        q = self.png("clibad", burst(["#FFFFFF", "#17E0D0", "#2040FF", "#D020C0"]))
        self.assertEqual(art_check.main([q, "--effect"]), 1)


if __name__ == "__main__":
    unittest.main()
