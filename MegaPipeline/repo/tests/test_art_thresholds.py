"""Calibration suite for tools/art_check.py: every threshold in pipeline/art/style.json is shown
to pass a good frame and fail a frame broken on purpose. Each frame is built with exact pixel
shares, so each broken frame trips ONLY the threshold it targets, just past the limit, and its
good twin sits just inside it. If a threshold is loosened past a broken frame, its test fails.

Also runs tools/make_art_calibration.py on a synthetic on-style frame, so the numeric half of
evals/art-judge/README.md is exercised before the real key art is in the repo."""
import colorsys
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
import hermetic  # noqa: E402
import art_check  # noqa: E402
import make_art_calibration  # noqa: E402
from png import write_png  # noqa: E402

STYLE = json.load(open(os.path.join(ROOT, "pipeline", "art", "style.json")))
T = STYLE["thresholds"]
PAL = {c["name"]: art_check.hex_to_rgb(c["hex"]) + (255,) for c in STYLE["palette"]}
W, H = 200, 100  # 20,000 pixels: under max_samples, so every pixel is measured

PAPER, PAPER_L, INK, GOLD = PAL["paper-mid"], PAL["paper-light"], PAL["silhouette"], PAL["gold"]
GREY = (225, 225, 225, 255)    # off-palette, unsaturated, no chroma: lowers on_palette only
YELLOW = (255, 200, 0, 255)    # saturated, off-palette, but inside the gold hue band: off_style only
TEAL = (70, 130, 125, 255)     # muted (HSV s < 0.55) but colorful and outside the hue bands: off_band only

# The good base frame: 20% silhouette, 4% gold, rest paper.
BASE = {"dark": 0.20, "accent": 0.04}

# threshold key in style.json -> (metric, good shares, broken shares)
CASES = {
    "on_palette_min": ("on_palette", {"grey": 0.15}, {"grey": 0.25}),
    "off_style_max": ("off_style", {"yellow": 0.01}, {"yellow": 0.04}),
    "off_band_max": ("off_band", {"teal": 0.005}, {"teal": 0.03}),
    "accent_area_max": ("accent_area", {"accent": 0.07}, {"accent": 0.12}),
    "dark_share_min": ("dark_share", {"dark": 0.05}, {"dark": 0.02}),
    "dark_share_max": ("dark_share", {"dark": 0.40}, {"dark": 0.55}),
    # "flat" = share of the frame that is one flat paper color instead of grain (finding 14)
    "paper_texture_min": ("paper_texture", {"flat": 0.25}, {"flat": 0.35}),   # 0.425 / 0.342 around 0.38
}
COLORS = {"dark": INK, "accent": GOLD, "grey": GREY, "yellow": YELLOW, "teal": TEAL}


def build(shares):
    """A W x H frame with exact pixel shares; paper grain fills the rest."""
    s = dict(BASE)
    s.update(shares)
    pixels = []
    for key, color in COLORS.items():
        pixels += [color] * round(s.get(key, 0) * W * H)
    flat = min(round(s.get("flat", 0) * W * H), W * H - len(pixels))
    pixels += [PAPER] * flat
    rest = W * H - len(pixels)
    pixels += [PAPER if i % 3 else PAPER_L for i in range(rest)]
    return [pixels[y * W:(y + 1) * W] for y in range(H)]


def classify(rgb):
    lab = art_check.rgb_to_lab(rgb[:3])
    pal = [(c["role"], art_check.rgb_to_lab(art_check.hex_to_rgb(c["hex"]))) for c in STYLE["palette"]]
    near = min(art_check.delta_e(lab, p) for _, p in pal) <= STYLE["delta_e_tolerance"]
    sat = colorsys.rgb_to_hsv(*(v / 255 for v in rgb[:3]))[1]
    chroma = math.hypot(lab[1], lab[2])
    hue = math.degrees(math.atan2(lab[2], lab[1])) % 360
    in_band = any(lo <= hue <= hi for lo, hi in STYLE["hue_gate"]["allowed_hue_bands_deg"])
    return near, sat, chroma, in_band


class FixtureColorsAreWhatTheyClaim(unittest.TestCase):
    """If the palette is re-measured these preconditions say which fixture color needs moving."""

    def test_grey_is_off_palette_and_dull(self):
        near, sat, chroma, _ = classify(GREY)
        self.assertFalse(near)
        self.assertLess(sat, STYLE["off_style_saturation_min"])
        self.assertLess(chroma, STYLE["hue_gate"]["chroma_min"])

    def test_yellow_is_saturated_in_band(self):
        near, sat, chroma, in_band = classify(YELLOW)
        self.assertFalse(near)
        self.assertGreaterEqual(sat, STYLE["off_style_saturation_min"])
        self.assertTrue(in_band)

    def test_teal_is_colorful_off_band_but_not_saturated(self):
        near, sat, chroma, in_band = classify(TEAL)
        self.assertFalse(near)
        self.assertLess(sat, STYLE["off_style_saturation_min"])
        self.assertGreater(chroma, STYLE["hue_gate"]["chroma_min"] + 3)
        self.assertFalse(in_band)


class ThresholdCalibration(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.mkdtemp()

    def measure(self, name, shares):
        p = os.path.join(self.tmp, name + ".png")
        write_png(p, W, H, build(shares))
        m = art_check.measure(p, STYLE)
        return m, art_check.evaluate(m, STYLE)

    def test_base_frame_passes(self):
        m, fails = self.measure("base", {})
        self.assertEqual(fails, [], m)

    def test_every_threshold_has_a_case(self):
        self.assertEqual(sorted(CASES), sorted(T))

    def test_each_threshold_passes_good_and_fails_broken(self):
        for key, (metric, good, bad) in CASES.items():
            with self.subTest(threshold=key, limit=T[key]):
                m, fails = self.measure(key + "_good", good)
                self.assertEqual(fails, [], f"good frame for {key} failed: {m}")
                m, fails = self.measure(key + "_bad", bad)
                self.assertEqual(len(fails), 1, f"broken frame for {key} should fail only {metric}: {fails}")
                self.assertTrue(fails[0].startswith(metric), fails)

    def test_cli_json_reports_the_failure(self):
        p = os.path.join(self.tmp, "flood.png")
        write_png(p, W, H, build({"accent": 0.12}))
        import io
        from contextlib import redirect_stdout
        buf = io.StringIO()
        with redirect_stdout(buf):
            self.assertEqual(art_check.main(["--json", p]), 1)
        self.assertIn("accent_area", json.loads(buf.getvalue())["failures"][0])


def hexa(h):
    return art_check.hex_to_rgb(h) + (255,)


ACC = STYLE["accents"]
WIND, RUST, YEL = hexa("#555e60"), hexa("#4e2017"), hexa("#ffd84a")   # RUST: a key-art rust variant outside the palette
PINK = hexa("#ff3658")   # bar-casters' shot red: not our look (D-new-owl-shot-look)
SAT_TEAL = (42, 157, 143, 255)   # a flat saturated teal placeholder box


class CappedAccents(unittest.TestCase):
    """Josh, DECIDED 2026-11-10 (D-new-palette-accents): the quality-bar colours (wind ash blue, the shot yellows)
    pass art_check in their roles up to a capped share of the frame; anything else still fails. Josh, DECIDED
    2026-11-11 (D-new-owl-shot-look): the shot red is the key art's rust family; the bar's pink is no accent."""

    def setUp(self):
        self.tmp = tempfile.mkdtemp()

    def frame(self, extra):
        """The good base frame with exact shares of extra colours put in place of paper."""
        rows = build({})
        flat = [px for row in rows for px in row]
        i = 0
        for color, share in extra:
            n = round(share * W * H)
            for _ in range(n):
                while flat[i] not in (PAPER, PAPER_L):
                    i += 1
                flat[i] = color
                i += 1
        return [flat[y * W:(y + 1) * W] for y in range(H)]

    def measure(self, name, extra, style=STYLE):
        p = os.path.join(self.tmp, name + ".png")
        write_png(p, W, H, self.frame(extra))
        m = art_check.measure(p, style)
        return m, art_check.evaluate(m, style)

    def test_the_caps(self):
        self.assertEqual(ACC["total_share_max"], 0.10)
        self.assertEqual(ACC["roles"]["wind"]["share_max"], 0.06)
        self.assertEqual({c["hex"] for c in ACC["roles"]["shot-red"]["colours"]}, {"#723929", "#5b2519", "#79331f"})
        self.assertEqual({c["hex"] for c in ACC["roles"]["shot-yellow"]["colours"]},
                         {"#ffd84a", "#f5aa28", "#94611e", "#fff5dc"})
        self.assertIn("#171614", {c["hex"] for c in STYLE["palette"] if c["role"] == "silhouette"}, "INK joins the darks")

    def test_accents_in_their_role_pass(self):
        m, fails = self.measure("ok", [(WIND, 0.05), (RUST, 0.025), (YEL, 0.015)])
        self.assertEqual(fails, [], m)
        self.assertEqual((m["accent_wind"], m["accent_shot-red"], m["accent_shot-yellow"]), (0.05, 0.025, 0.015))
        self.assertEqual((m["off_style"], m["off_band"]), (0.0, 0.0))

    def test_broken_on_purpose(self):
        cases = {
            "over the wind cap": ([(WIND, 0.07)], "accent_wind"),
            "over a shot cap": ([(RUST, 0.05)], "accent_shot-red"),
            "over the total cap": ([(WIND, 0.055), (RUST, 0.035), (YEL, 0.035)], "accent_extra"),
            "pink shots past the off_style cap (D-new-owl-shot-look)": ([(PINK, 0.03)], "off_style"),
            "a teal box": ([(SAT_TEAL, 0.03)], "off_style"),
            "a flat red fill": ([(RUST, 0.6)], "accent_shot-red"),
        }
        for name, (extra, want) in cases.items():
            with self.subTest(name):
                m, fails = self.measure(name.replace(" ", "_"), extra)
                self.assertTrue(any(f.startswith(want) for f in fails), (fails, m))
        m, fails = self.measure("teal", [(SAT_TEAL, 0.03)])
        self.assertTrue(any(f.startswith("off_band") for f in fails), fails)
        self.assertEqual(m["accent_extra"], 0.0, "teal is no accent")
        m, _ = self.measure("grey", [((100, 100, 100, 255), 0.05)])
        self.assertEqual(m["accent_wind"], 0.0, "a neutral grey box is not the ash-blue wind (chroma floor)")

    def test_without_the_accents_the_shot_colours_fail(self):
        """The rule the accents changed: the same shot colours fail off_style when style.json has no accents."""
        bare = {k: v for k, v in STYLE.items() if k != "accents"}
        m, fails = self.measure("bare", [(RUST, 0.025), (YEL, 0.015)], bare)
        self.assertTrue(any(f.startswith("off_style") for f in fails), (fails, m))

    def test_quality_bar_images_pass_on_colour(self):
        """bar-casters and bar-other-realm (pipeline/art/references.json quality_bar) pass every colour rule: off_style,
        off_band and the accent caps. (Other numbers, like dark_share on the dark Other Realm scene, are not colour.)
        Since D-new-owl-shot-look (Josh, 11 Nov) the casters' pink shots are no accent: they pass only as off_style
        under its 2% cap, like any stray colour."""
        for rel in ("discord/20261111-0319_Ricky_roadwarden-sundial-casters.png",
                    "discord/20261111-0318_Ricky_other-realm.png"):
            path = os.path.join(ROOT, "pipeline", "art", "reference", rel)
            if not os.path.isfile(path):
                self.skipTest(f"{rel} is not on disk here ({hermetic.LEFT_OUT})")
            with open(path, "rb") as fh:
                if fh.read(8) != b"\x89PNG\r\n\x1a\n":
                    self.skipTest(f"{rel} is an LFS pointer here")
            with self.subTest(rel):
                m = art_check.measure(path, STYLE)
                colour = [f for f in art_check.evaluate(m, STYLE)
                          if f.split()[0] in ("off_style", "off_band", "accent_area") or f.startswith("accent_")]
                self.assertEqual(colour, [], m)
        bare = {k: v for k, v in STYLE.items() if k != "accents"}
        m = art_check.measure(os.path.join(ROOT, "pipeline", "art", "reference",
                                           "discord/20261111-0319_Ricky_roadwarden-sundial-casters.png"), bare)
        self.assertTrue(any(f.startswith("off_style") for f in art_check.evaluate(m, bare)),
                        "broken on purpose: without the accents the casters sheet fails off_style")


class CalibrationVariantsOnSyntheticFrame(unittest.TestCase):
    """tools/make_art_calibration.py variants of a passing frame must fail the numeric gate."""

    def test_variants_fail(self):
        tmp = tempfile.mkdtemp()
        src = os.path.join(tmp, "good.png")
        rows = build({})
        # put the silhouette in the bottom band and gold in a few shots, like a real frame
        write_png(src, W, H, rows)
        self.assertEqual(art_check.evaluate(art_check.measure(src, STYLE), STYLE), [])
        out = os.path.join(tmp, "cal")
        import io
        from contextlib import redirect_stdout
        with redirect_stdout(io.StringIO()):
            make_art_calibration.main([src, out])
        # B5: flat near-white paper lands within tolerance of spark-white, an accent color, so it
        # fails as an accent flood. It fails for the right image, with a misleading reason (see evals/README.md).
        expect = {"B1_colorful": None, "B4_grey_silh": "dark_share", "B5_flat_white": "accent_area",
                  "B6_gold_flood": "accent_area", "B7_crushed": "dark_share"}
        for name, metric in expect.items():
            with self.subTest(variant=name):
                fails = art_check.evaluate(art_check.measure(os.path.join(out, name + ".png"), STYLE), STYLE)
                self.assertTrue(fails, name + " passed")
                if metric:
                    self.assertTrue(any(f.startswith(metric) for f in fails), fails)


if __name__ == "__main__":
    unittest.main()
