"""Ella's hurt frame in the gate's visual check (visual_qa.figure_check; lead order Nov 13 23:26, item 2).

Josh saw Ella turn into a solid black box when hit (T_Ella_Hurt_PH as a virtual texture). The journey now takes
`figureshot vq_figure` (her normal frame) and `hurtshot vq_hurt` (one assisted life lost, captured while she shows Hurt),
each with a plate (her actor hidden) and a sidecar. Fixtures are real 1280x720 captures of this journey step, cropped to
the top-left 480x270 (the sidecar boxes stay valid), in pipeline/qa/visual/calibration/hurt/:
  good   - T_Ella_Hurt_PH plain 6x4 grid with its 6x4 catalogue row (area/scalecheck bb2fb8f9): hurt 112 px, idle 93 px
  black  - this branch's VT texture: a 178x135 solid black box where Ella should be
  sliver - the plain 6x4 texture drawn through the old 24-column row: 9 px of her, 1 px wide
The old visual_qa has no figure_check: every test here fails on it."""
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

HURT = os.path.join(ROOT, "pipeline", "qa", "visual", "calibration", "hurt")
STUDY = os.path.join(ROOT, visual_qa.STUDY)


def blind_judge(prompt, image):
    return json.dumps({"scores": {k: 6 for k, _ in visual_qa.RUBRIC}, "broken": [], "verdict": "PASS"})


class HurtFrame(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.mkdtemp()

    def tearDown(self):
        shutil.rmtree(self.tmp, ignore_errors=True)

    def shots(self, case):
        d = os.path.join(self.tmp, case)
        os.makedirs(d)
        for folder in ("good", case):
            for name in os.listdir(os.path.join(HURT, folder)):
                shutil.copyfile(os.path.join(HURT, folder, name), os.path.join(d, name))
        return d

    def test_good_hurt_frame_reads_right(self):
        d = self.shots("good")
        hurt = visual_qa.figure_measure(d, visual_qa.HURT_SHOT)
        normal = visual_qa.figure_measure(d, visual_qa.FIGURE_SHOT)
        self.assertEqual(hurt["state"], "Hurt")
        self.assertTrue(100 <= hurt["height"] <= 125, hurt)   # measured 112
        self.assertTrue(85 <= normal["height"] <= 105, normal)  # measured 93
        self.assertLess(hurt["flat"], 0.3, hurt)
        self.assertEqual(visual_qa.figure_check(d), [])

    def test_black_box_where_ella_should_be_fails(self):
        items = visual_qa.figure_check(self.shots("black"))
        self.assertEqual(len(items), 1, items)
        self.assertIn("flat box", items[0])
        self.assertIn("#000000", items[0])
        self.assertEqual(visual_qa.defect_kind(items[0]), "hurt_frame")
        # The flat-box detector reads the same capture as a box too (it runs on vq_hurt as a play detector shot).
        boxes = flat_box.find_boxes(os.path.join(HURT, "black", "vq_hurt.png"))
        self.assertIn("#000000", [b["rgb"] for b in boxes])

    def test_sliver_fails_on_height(self):
        items = visual_qa.figure_check(self.shots("sliver"))
        self.assertEqual(len(items), 1, items)
        self.assertIn("9 px tall", items[0])
        self.assertIn("ratio 0.10", items[0])
        self.assertTrue(items[0].endswith("[detector]"))

    def test_capture_not_in_hurt_or_missing_fails(self):
        d = self.shots("good")
        path = os.path.join(d, visual_qa.HURT_SHOT + ".json")
        with open(path) as fh:
            meta = json.load(fh)
        meta["state"] = "Idle"
        with open(path, "w") as fh:
            json.dump(meta, fh)
        self.assertIn("showed Idle", visual_qa.figure_check(d)[0])
        os.remove(os.path.join(d, visual_qa.HURT_SHOT + "_plate.png"))
        self.assertIn("no hurt frame capture", visual_qa.figure_check(d)[0])

    def test_play_screen_fails_on_a_broken_hurt_frame_though_the_judge_saw_nothing(self):
        for case, expect in (("good", visual_qa.EXIT_PASS), ("black", visual_qa.EXIT_FAIL), ("sliver", visual_qa.EXIT_FAIL)):
            d = self.shots(case)
            for name in visual_qa.SCREENS.values():
                shutil.copyfile(STUDY, os.path.join(d, name))
            code, line, results = visual_qa.judge_shots(d, blind_judge, os.path.join(self.tmp, "rec"))
            self.assertEqual(code, expect, (case, line, results["play"]["detector"]))
            if expect == visual_qa.EXIT_FAIL:
                self.assertIn("failed=play", line)

    def test_gate_counts_a_new_hurt_frame_item(self):
        item = visual_qa.figure_check(self.shots("sliver"))[0]
        result = {"total": 40, "broken": [item], "scores": {}, "verdict": "PASS"}
        ok, reasons = visual_qa.decide_gate(result, {"total": 40, "broken": [], "detector": []})
        self.assertFalse(ok)
        self.assertIn("[hurt_frame]", reasons[0])
        ok, _ = visual_qa.decide_gate(result, {"total": 40, "broken": [item], "detector": [item]})
        self.assertTrue(ok)

    def test_journey_captures_the_hurt_frame_before_the_defeat_hits(self):
        with open(os.path.join(ROOT, visual_qa.JOURNEY), encoding="utf-8") as fh:
            cmds = [ln.split("#")[0].split() for ln in fh]
        cmds = [c[:2] for c in cmds if c]
        i_play = cmds.index(["shot", "vq_play"])
        i_fig = cmds.index(["figureshot", visual_qa.FIGURE_SHOT])
        i_hurt = cmds.index(["hurtshot", visual_qa.HURT_SHOT])
        i_hits = cmds.index(["hits", "Defeat"])
        self.assertTrue(i_play < i_fig < i_hurt < i_hits, (i_play, i_fig, i_hurt, i_hits))
        self.assertIn(visual_qa.HURT_SHOT + ".png", visual_qa.DETECTOR_SHOTS["play"])


if __name__ == "__main__":
    unittest.main()
