"""Flat filled box detector (tools/build/flat_box.py) and its use in visual_qa (lead order Nov 13 21:49, item 5).

The fixtures are real captures (pipeline/qa/visual/calibration/flatbox-*.png, 800x450 from the Keeper-attacks journey
and the Director's Cut route). The Opus judge missed the salmon warning band and the grey gust cube on such frames; the
old visual_qa had only the judge, so with a judge answer that lists nothing these screens passed (tests below fail on
the old code: no "detector" key, no box item, keeper PASS)."""
import json
import os
import shutil
import sys
import tempfile
import unittest

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, os.path.join(ROOT, "tools", "build"))
import flat_box  # noqa: E402
import visual_qa  # noqa: E402

CAL = os.path.join(ROOT, "pipeline", "qa", "visual", "calibration")
BAND = os.path.join(CAL, "flatbox-keeper-band.png")
BLACK = os.path.join(CAL, "flatbox-keeper-blackbox.png")
CUBE = os.path.join(CAL, "flatbox-keeper-gustcube.png")
QUIET = os.path.join(CAL, "flatbox-keeper-quiet.png")
ROUTE = os.path.join(CAL, "flatbox-dcroute-clean.png")
STUDY = os.path.join(ROOT, visual_qa.STUDY)


def blind_judge(prompt, image):
    """A judge that sees nothing broken (what the Opus judge answered on the band and cube frames)."""
    return json.dumps({"scores": {k: 6 for k, _ in visual_qa.RUBRIC}, "broken": [], "verdict": "PASS"})


def rgb(box):
    return [int(box["rgb"][i:i + 2], 16) for i in (1, 3, 5)]


class FindBoxes(unittest.TestCase):
    def test_salmon_warning_band_is_a_box(self):
        boxes = flat_box.find_boxes(BAND)
        self.assertEqual(len(boxes), 1, boxes)
        r, g, b = rgb(boxes[0])
        self.assertTrue(r > 200 and g < 160 and b < 160, boxes[0])  # salmon
        self.assertGreater(boxes[0]["w"], 4 * boxes[0]["h"])        # a wide band

    def test_grey_gust_cube_is_a_box(self):
        boxes = flat_box.find_boxes(CUBE)
        self.assertEqual(len(boxes), 1, boxes)
        r, g, b = rgb(boxes[0])
        self.assertTrue(min(r, g, b) > 180 and max(r, g, b) - min(r, g, b) < 25, boxes[0])  # pale grey
        self.assertGreater(boxes[0]["h"], boxes[0]["w"])            # upright

    def test_black_stand_in_box_on_the_dark_sky_is_a_box(self):
        boxes = flat_box.find_boxes(BLACK)
        self.assertEqual([b["rgb"] for b in boxes], ["#000000"])

    def test_clean_frames_have_no_box(self):
        for path in (QUIET, ROUTE, STUDY, visual_qa.rel(visual_qa.KNOWN_GOOD)):
            self.assertEqual(flat_box.find_boxes(os.path.join(ROOT, path) if not os.path.isabs(path) else path), [],
                             path)

    def test_known_bad_frame_has_its_bars_and_cube(self):
        boxes = flat_box.find_boxes(os.path.join(ROOT, visual_qa.KNOWN_BAD))
        self.assertGreaterEqual(len(boxes), 2, boxes)

    def test_describe_is_a_box_defect(self):
        item = flat_box.describe(flat_box.find_boxes(CUBE)[0])
        self.assertEqual(visual_qa.defect_kind(item), "box")
        self.assertTrue(item.endswith("[detector]"))

    def test_cli_exit_codes(self):
        self.assertEqual(flat_box.main([QUIET]), 0)
        self.assertEqual(flat_box.main([QUIET, BAND]), 1)


class VisualQaUsesDetector(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.mkdtemp()
        self.shots = os.path.join(self.tmp, "shots")
        os.makedirs(self.shots)
        shutil.copyfile(STUDY, os.path.join(self.shots, "vq_play.png"))
        shutil.copyfile(ROUTE, os.path.join(self.shots, "vq_dc_route.png"))
        shutil.copyfile(QUIET, os.path.join(self.shots, "vq_keeper.png"))
        self.rec = os.path.join(self.tmp, "rec")

    def tearDown(self):
        shutil.rmtree(self.tmp, ignore_errors=True)

    def test_quiet_keeper_with_a_blind_judge_passes(self):
        code, line, results = visual_qa.judge_shots(self.shots, blind_judge, self.rec)
        self.assertEqual(code, visual_qa.EXIT_PASS, line)
        self.assertEqual(results["keeper"]["detector"], [])

    def test_band_on_the_judged_keeper_shot_fails_though_the_judge_saw_nothing(self):
        shutil.copyfile(BAND, os.path.join(self.shots, "vq_keeper.png"))
        code, line, results = visual_qa.judge_shots(self.shots, blind_judge, self.rec)
        self.assertEqual(code, visual_qa.EXIT_FAIL, line)
        self.assertIn("failed=keeper", line)
        self.assertEqual(len(results["keeper"]["detector"]), 1)
        self.assertIn(results["keeper"]["detector"][0], results["keeper"]["broken"])

    def test_attacks_in_the_detector_only_shots_are_found_once(self):
        # vq_keeper itself is between attacks; the cube shows in two later shots and the band in one.
        shutil.copyfile(CUBE, os.path.join(self.shots, "vq_keeper_a2.png"))
        shutil.copyfile(CUBE, os.path.join(self.shots, "vq_keeper_a3.png"))
        shutil.copyfile(BAND, os.path.join(self.shots, "vq_keeper_a6.png"))
        code, line, results = visual_qa.judge_shots(self.shots, blind_judge, self.rec)
        self.assertEqual(code, visual_qa.EXIT_FAIL, line)
        self.assertEqual(len(results["keeper"]["detector"]), 2, results["keeper"]["detector"])

    def test_journey_takes_the_detector_only_shots(self):
        with open(os.path.join(ROOT, visual_qa.JOURNEY), encoding="utf-8") as fh:
            shots = [ln.split()[1] + ".png" for ln in fh if ln.startswith("shot ")]
        for name in visual_qa.DETECTOR_SHOTS["keeper"]:
            self.assertIn(name, shots)
        self.assertLess(shots.index("vq_keeper.png"), shots.index(visual_qa.DETECTOR_SHOTS["keeper"][0]))


class GateWithDetector(unittest.TestCase):
    """A detector item is new against main only when main's baseline was run with the detector: a baseline from before
    the detector never listed main's own boxes, and every lane would fail on the band main already shows."""
    ITEM = "flat filled box 20x42 px at (473,28) colour #cfd6dc over the play space (untextured stand-in) [detector]"

    def result(self, broken):
        return {"total": 40, "broken": broken, "scores": {}, "verdict": "PASS"}

    def test_old_baseline_does_not_count_detector_items_as_new(self):
        ok, reasons = visual_qa.decide_gate(self.result([self.ITEM]), {"total": 40, "broken": []})
        self.assertTrue(ok, reasons)

    def test_detector_baseline_without_the_box_fails_on_it(self):
        ok, reasons = visual_qa.decide_gate(self.result([self.ITEM]), {"total": 40, "broken": [], "detector": []})
        self.assertFalse(ok)
        self.assertIn("[box]", reasons[0])

    def test_detector_baseline_with_the_box_passes(self):
        base = {"total": 40, "broken": [self.ITEM], "detector": [self.ITEM]}
        ok, reasons = visual_qa.decide_gate(self.result([self.ITEM]), base)
        self.assertTrue(ok, reasons)

    def test_judge_items_still_count_against_an_old_baseline(self):
        ok, _ = visual_qa.decide_gate(self.result(["grey cube near the owl"]), {"total": 40, "broken": []})
        self.assertFalse(ok)


if __name__ == "__main__":
    unittest.main()
