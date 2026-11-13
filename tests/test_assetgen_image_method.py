"""The image method in tools/assetgen.py (docs/build/art-image-model.md): explicit aspect ratio and image size on every
gemini call, Pro thinking tokens counted in the shared spend counter, the free model list, the HSV chroma key with mask
grow and despill, and cutting one painted strip into frames on a fixed pivot. Fake client only, never the network."""
import json
import os
import sys
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.join(ROOT, "tools"))
import png  # noqa: E402
import test_assetgen_image as img  # noqa: E402

PRO = "gemini-3-pro-image-preview"
FLASH31 = "gemini-3.1-flash-image-preview"
GREEN = (0, 255, 0, 255)


class ShapeAndThinking(img.ImageWork):
    def test_aspect_ratio_always_sent_and_no_image_size_for_2_5_flash(self):
        rc, o = self.paint("Art/Source/Ella/a.png", "--size", "1536x1024")
        self.assertEqual(rc, 0, o)
        self.assertEqual(self.http()[0]["image_config"], {"aspectRatio": "3:2"})
        rc, o = self.paint("Art/Source/Ella/b.png", "--aspect", "16:9")
        self.assertEqual(rc, 0, o)
        self.assertEqual(self.http()[1]["image_config"], {"aspectRatio": "16:9"})
        rc, o = self.paint("Art/Source/Ella/c.png", "--image-size", "2K")
        self.assertEqual(rc, 2, o)
        self.assertIn("takes no imageSize", o)
        self.assertEqual(len(self.http()), 2, "refused before any call")

    def test_pro_needs_an_explicit_image_size_and_sends_it(self):
        rc, o = self.paint("Art/Source/Ella/p.png", "--model", PRO, "--aspect", "1:1")
        self.assertEqual(rc, 2, o)
        self.assertIn("needs an explicit --image-size", o)
        self.assertEqual(self.http(), [])
        rc, o = self.paint("Art/Source/Ella/p.png", "--model", PRO, "--aspect", "16:9", "--image-size", "2K")
        self.assertEqual(rc, 0, o)
        self.assertEqual(self.http()[0]["image_config"], {"aspectRatio": "16:9", "imageSize": "2K"})
        req = json.load(open(os.path.join(self.repo, "Art/Source/Ella/p.request.json")))
        self.assertEqual((req["aspect_ratio"], req["image_size"]), ("16:9", "2K"))

    def test_strip_ratios_only_on_the_model_that_has_them(self):
        rc, o = self.paint("Art/Source/Ella/s.png", "--model", PRO, "--aspect", "4:1", "--image-size", "1K")
        self.assertEqual(rc, 2, o)
        self.assertIn("no aspect ratio 4:1", o)
        rc, o = self.paint("Art/Source/Ella/s.png", "--model", FLASH31, "--aspect", "4:1", "--image-size", "1K")
        self.assertEqual(rc, 0, o)
        self.assertEqual(self.http()[0]["image_config"], {"aspectRatio": "4:1", "imageSize": "1K"})

    def test_pro_thinking_tokens_reserved_then_settled_from_the_reply(self):
        """Reserve = image + 25% thinking margin; settle = image + prompt tokens + thoughts at the text-output rate."""
        usage = {"promptTokenCount": 1000, "candidatesTokenCount": 1120, "thoughtsTokenCount": 2000}
        rc, o = self.paint("Art/Source/Ella/t.png", "--model", PRO, "--aspect", "1:1", "--image-size", "2K",
                           STUB_USAGE=json.dumps(usage))
        self.assertEqual(rc, 0, o)
        want = 0.134 + 1000 * 0.000002 + 2000 * 0.000012
        c = self.counter()
        self.assertAlmostEqual(c["spent_usd"], want)
        self.assertAlmostEqual(c["calls"][0]["cost_usd"], want)
        self.assertAlmostEqual(c["calls"][0]["reserved_usd"], 0.134 * 1.25)
        self.assertIn("thinking_tokens=2000", o)

    def test_thinking_above_the_reserve_is_still_counted_and_the_next_call_sees_it(self):
        usage = {"promptTokenCount": 500, "thoughtsTokenCount": 10000}
        cap = dict(IMAGE_SPEND_CAP_USD="0.40", STUB_USAGE=json.dumps(usage))
        rc, o = self.paint("Art/Source/Ella/t1.png", "--model", PRO, "--aspect", "1:1", "--image-size", "1K", **cap)
        self.assertEqual(rc, 0, o)
        spent = 0.134 + 500 * 0.000002 + 10000 * 0.000012   # 0.255, above the 0.1675 reserve
        self.assertAlmostEqual(self.counter()["spent_usd"], spent)
        rc, o = self.paint("Art/Source/Ella/t2.png", "--model", PRO, "--aspect", "1:1", "--image-size", "1K", **cap)
        self.assertEqual(rc, 2, o)
        self.assertIn("CAP REACHED", o)

    def test_4k_pro_is_priced_at_its_own_rate(self):
        rc, o = self.paint("Art/Source/Ella/k.png", "--model", PRO, "--aspect", "1:1", "--image-size", "4K",
                           STUB_USAGE="{}")
        self.assertEqual(rc, 0, o)
        self.assertAlmostEqual(self.counter()["spent_usd"], 0.24)


class ModelList(img.ImageWork):
    def test_lists_image_models_and_marks_unpriced_ones(self):
        rc, o = self.ag("image-models", **self.img_env())
        self.assertEqual(rc, 0, o)
        self.assertIn("gemini-3-pro-image-preview | gemini-3-pro-image-preview | generateContent | priced", o)
        self.assertIn("gemini-3.5-flash-image | gemini-3.5-flash-image | generateContent | UNPRICED", o)
        self.assertNotIn("MODEL gemini-2.5-flash |", o, "text-only models left out")
        self.assertNotIn(img.FAKE_KEY, o)
        self.assertTrue(self.http()[0]["key_sent"])
        self.assertEqual(self.counter()["spent_usd"], 0.0, "the model list is free: not counted")

    def test_no_key(self):
        rc, o = self.ag("image-models", **self.img_env(GEMINI_API_KEY=None, KEYS_NO_KEYCHAIN="1"))
        self.assertEqual(rc, 2, o)
        self.assertIn("NO KEY", o)


def figure_on_green(path, w=96, h=64, figs=((10, 20, 30, 50),), fringe=True, inside=(200, 60, 40, 255), line=1):
    """A green canvas with dark-outlined figures (x0, y0, x1, y1); a 1 px green-tinted fringe around each."""
    rows = [[GREEN] * w for _ in range(h)]
    for x0, y0, x1, y1 in figs:
        for y in range(y0, y1 + 1):
            for x in range(x0, x1 + 1):
                edge = min(x - x0, x1 - x, y - y0, y1 - y) < line
                rows[y][x] = (230, 225, 215, 255) if edge else inside
        if fringe:
            for y in range(y0 - 1, y1 + 2):
                for x in (x0 - 1, x1 + 1):
                    rows[y][x] = (120, 200, 110, 255)
    png.write_png(path, w, h, rows)


class ChromaKey(img.ImageWork):
    def test_green_keyed_fringe_grown_away_and_no_green_left(self):
        src = os.path.join(self.repo, "Art/Source/Ella/raw.png")
        os.makedirs(os.path.dirname(src), exist_ok=True)
        figure_on_green(src)
        rc, o = self.ag("clean", "--in", "Art/Source/Ella/raw.png", "--out", "Art/Source/Ella/cut.png",
                        "--chroma", "00FF00", "--grow", "1")
        self.assertEqual(rc, 0, o)
        self.assertIn("via=chroma", o)
        w, h, rows = png.read_png(os.path.join(self.repo, "Art/Source/Ella/cut.png"))
        self.assertEqual(rows[0][0][3], 0, "background keyed out")
        self.assertEqual(rows[30][9][3], 0, "the green-tinted fringe is gone (mask grown 1 px)")
        self.assertEqual(rows[30][20], (200, 60, 40, 255), "the subject's inside untouched")
        opaque = [px for row in rows for px in row if px[3]]
        self.assertTrue(opaque)
        self.assertFalse([px for px in opaque if px[1] > max(px[0], px[2])], "no green-dominant pixel left at the cut")
        self.assertIn("green_inside_px=0", o)
        self.assertIn("enclosed_key_px=0", o)
        self.assertNotIn("WARN", o)
        self.assertIn("chroma key #00FF00", self.prov()["Art/Source/Ella/cut.png"]["origin"])
        row = self.prov()["Art/Source/Ella/cut.png"]
        self.assertEqual(row["tool"], "tools/assetgen.py (pure Python)", "the cut is ours, not GIMP 3")
        self.assertNotIn("GPL", row["licence"])

    def test_green_inside_the_subject_is_reported(self):
        src = os.path.join(self.repo, "Art/Source/Ella/raw2.png")
        os.makedirs(os.path.dirname(src), exist_ok=True)
        figure_on_green(src, figs=((10, 10, 60, 55),), inside=(40, 160, 50, 255), line=4)
        rc, o = self.ag("clean", "--in", "Art/Source/Ella/raw2.png", "--out", "Art/Source/Ella/cut2.png",
                        "--chroma", "00FF00")
        self.assertEqual(rc, 0, o)
        self.assertIn("WARN", o)
        self.assertNotIn("enclosed_key_px=0", o, "the green coat was keyed out as a hole: reported")

    def test_background_not_the_key_colour_fails(self):
        src = os.path.join(self.repo, "Art/Source/Ella/paper.png")
        os.makedirs(os.path.dirname(src), exist_ok=True)
        png.write_png(src, 16, 16, [[(235, 228, 210, 255)] * 16 for _ in range(16)])
        rc, o = self.ag("clean", "--in", "Art/Source/Ella/paper.png", "--out", "Art/Source/Ella/x.png",
                        "--chroma", "00FF00")
        self.assertEqual(rc, 1, o)
        self.assertIn("not the key colour", o)
        self.assertFalse(os.path.exists(os.path.join(self.repo, "Art/Source/Ella/x.png")))


class StripFrames(img.ImageWork):
    def keyed_strip(self, figs, w=200, h=80):
        src = os.path.join(self.repo, "Art/Source/Ella/strip.png")
        os.makedirs(os.path.dirname(src), exist_ok=True)
        rows = [[(0, 0, 0, 0)] * w for _ in range(h)]
        for x0, y0, x1, y1 in figs:
            for y in range(y0, y1 + 1):
                for x in range(x0, x1 + 1):
                    rows[y][x] = (90, 60, 120, 255)
        png.write_png(src, w, h, rows)
        return "Art/Source/Ella/strip.png"

    def test_three_figures_cut_to_equal_frames_on_one_baseline(self):
        strip = self.keyed_strip([(10, 20, 40, 70), (70, 10, 100, 60), (140, 25, 165, 75)])
        rc, o = self.ag("frames", "--in", strip, "--count", "3", "--out-dir", "Art/Source/Ella/Raw/Idle",
                        "--pad", "4", "--stem", "ella_idle")
        self.assertEqual(rc, 0, o)
        outs = [os.path.join(self.repo, f"Art/Source/Ella/Raw/Idle/ella_idle_{i:02d}.png") for i in range(3)]
        sizes = {png.read_png(f)[:2] for f in outs}
        self.assertEqual(sizes, {(31 + 8, 51 + 8)}, "every frame the same size: the largest figure plus pad")
        for f in outs:
            w, h, rows = png.read_png(f)
            bottom = max(y for y, row in enumerate(rows) if any(px[3] for px in row))
            self.assertEqual(bottom, h - 1 - 4, f"{f}: feet on the one baseline (bottom-centre pivot)")
        meta = json.load(open(os.path.join(self.repo, "Art/Source/Ella/Raw/Idle/ella_idle.frames.json")))
        self.assertEqual(meta["figure_heights"], [51, 51, 51])
        self.assertEqual(meta["height_spread_pct"], 0.0)
        self.assertIn("Art/Source/Ella/Raw/Idle/ella_idle_02.png", self.prov())
        self.assertEqual(self.prov()["Art/Source/Ella/Raw/Idle/ella_idle_02.png"]["tool"],
                         "tools/assetgen.py (pure Python)")
        rc, o = self.ag("sheet", "--frames", *outs, "--out", "Art/Sprites/Ella/ella_idle_PH.png", "--anim", "Idle",
                        "--fps", "6", ASSETGEN_NO_APP_DIRS="1")
        self.assertEqual(rc, 0, o)

    def test_crop_one_figure_from_the_sheet_on_its_own_background(self):
        mask = self.keyed_strip([(10, 20, 40, 70), (70, 10, 100, 60), (140, 25, 165, 75)])
        sheet = os.path.join(self.repo, "Art/Source/Ella/sheet.png")
        figure_on_green(sheet, w=200, h=80, figs=((10, 20, 40, 70), (70, 10, 100, 60), (140, 25, 165, 75)),
                        fringe=False)
        rc, o = self.ag("crop", "--in", "Art/Source/Ella/sheet.png", "--mask", mask, "--count", "3", "--figure", "2",
                        "--pad", "4", "--out", "Art/Source/Ella/side.png")
        self.assertEqual(rc, 0, o)
        self.assertIn("box=66,6,104,64", o)
        w, h, rows = png.read_png(os.path.join(self.repo, "Art/Source/Ella/side.png"))
        self.assertEqual((w, h), (39, 59))
        self.assertEqual(rows[0][0], GREEN, "the crop keeps the sheet's flat key background")
        row = self.prov()["Art/Source/Ella/side.png"]
        self.assertEqual(row["tool"], "tools/assetgen.py (pure Python)")
        self.assertIn("figure 2 of 3", row["origin"])
        rc, o = self.ag("crop", "--in", "Art/Source/Ella/sheet.png", "--mask", mask, "--count", "4", "--figure", "1",
                        "--out", "Art/Source/Ella/x.png")
        self.assertEqual(rc, 1, o)
        self.assertIn("wanted 4", o)

    def test_scale_drift_is_measured(self):
        strip = self.keyed_strip([(10, 20, 40, 70), (70, 40, 100, 70)])
        rc, o = self.ag("frames", "--in", strip, "--count", "2", "--out-dir", "Art/Source/Ella/Raw/X")
        self.assertEqual(rc, 0, o)
        self.assertIn("spread=39.2%", o)

    def test_wrong_figure_count_fails(self):
        strip = self.keyed_strip([(10, 20, 40, 70), (70, 10, 100, 60)])
        rc, o = self.ag("frames", "--in", strip, "--count", "3", "--out-dir", "Art/Source/Ella/Raw/Y")
        self.assertEqual(rc, 1, o)
        self.assertIn("found 2 separate figures, wanted 3", o)

    def test_a_stray_bit_is_bridged_to_its_figure(self):
        strip = self.keyed_strip([(10, 20, 40, 70), (43, 30, 45, 34), (70, 10, 100, 60)])
        rc, o = self.ag("frames", "--in", strip, "--count", "2", "--out-dir", "Art/Source/Ella/Raw/Z")
        self.assertEqual(rc, 0, o)

    def test_touching_figures_cut_by_equal_cells(self):
        # three figures, the first two joined by a bar (an umbrella tip touching the next pose): gaps find 2
        strip = self.keyed_strip([(10, 20, 40, 70), (40, 40, 75, 42), (75, 10, 120, 60), (140, 25, 190, 75)],
                                 w=210)
        rc, o = self.ag("frames", "--in", strip, "--count", "3", "--out-dir", "Art/Source/Ella/Raw/T")
        self.assertEqual(rc, 1, o)
        self.assertIn("wanted 3", o)
        rc, o = self.ag("frames", "--in", strip, "--count", "3", "--cells", "--out-dir", "Art/Source/Ella/Raw/T")
        self.assertEqual(rc, 0, o)
        meta = json.load(open(os.path.join(self.repo, "Art/Source/Ella/Raw/T/strip.frames.json")))
        self.assertEqual(meta["figure_heights"], [51, 51, 51])
        self.assertEqual(meta["figure_widths"], [60, 51, 51], "cells 0-69, 70-139, 140-209: the bar falls in cells 1 and 2")
        self.assertEqual(meta["cut"], "equal cells, inset 0 px")

    def test_boxed_strip_cut_by_cells_with_inset_drops_the_box_lines(self):
        figs = [(20, 20, 40, 60), (90, 15, 110, 60), (160, 25, 180, 60)]
        lines = []
        for k in range(3):   # a 1 px box line around each third, as the model drew in round 2
            x0, x1 = k * 70 + 2, k * 70 + 67
            lines += [(x0, 2, x1, 2), (x0, 77, x1, 77), (x0, 2, x0, 77), (x1, 2, x1, 77)]
        strip = self.keyed_strip(figs + lines, w=210)
        rc, o = self.ag("frames", "--in", strip, "--count", "3", "--cells", "--out-dir", "Art/Source/Ella/Raw/B")
        self.assertEqual(rc, 0, o)
        meta = json.load(open(os.path.join(self.repo, "Art/Source/Ella/Raw/B/strip.frames.json")))
        self.assertEqual(meta["figure_heights"], [76, 76, 76], "without inset the box is measured, not the figure")
        rc, o = self.ag("frames", "--in", strip, "--count", "3", "--cells", "--inset", "5",
                        "--out-dir", "Art/Source/Ella/Raw/B")
        self.assertEqual(rc, 0, o)
        meta = json.load(open(os.path.join(self.repo, "Art/Source/Ella/Raw/B/strip.frames.json")))
        self.assertEqual(meta["figure_heights"], [41, 46, 36])
        self.assertEqual(meta["figure_widths"], [21, 21, 21])

    def test_an_empty_cell_fails(self):
        strip = self.keyed_strip([(10, 20, 40, 70), (70, 10, 100, 60)], w=210)
        rc, o = self.ag("frames", "--in", strip, "--count", "3", "--cells", "--out-dir", "Art/Source/Ella/Raw/E")
        self.assertEqual(rc, 1, o)
        self.assertIn("cell 3 of 3 is empty", o)


if __name__ == "__main__":
    unittest.main()
