"""A reference always passes its own element after `art_judge.py calibrate` (check defect, 12 Nov).

wind-zone has no team image, only the quality bar (bar-other-realm). calibrate measured nothing for it, so
references.json kept a stale detail_min of 0.421 while that reference's own interior detail is 0.099: the reference
failed its own element and no wind piece could ever pass. calibrate now measures an element with no team image on its
own references (lowest minus the same 0.02 margin), and `--write` records it.

- Synthetic: a stale detail_min above the only reference fails the reference (the defect, kept as a broken-on-purpose
  case); after calibrate + write the reference passes and a known-bad render (tools/make_art_calibration.py crushed,
  and a flat fill) still fails.
- Real repo: every image calibrate measured clears its own element's stored numbers, the two wind references pass
  through the CLI, and their known-bad renders fail.
"""
import io
import json
import os
import random
import shutil
import sys
import tempfile
import unittest
from contextlib import redirect_stdout

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, os.path.join(ROOT, "tools"))
sys.path.insert(0, HERE)
import hermetic  # noqa: E402
import art_judge  # noqa: E402
import make_art_calibration  # noqa: E402
from png import read_png, write_png  # noqa: E402


def judge_cli(*args):
    out = io.StringIO()
    with redirect_stdout(out):
        rc = art_judge.main(list(args))
    return rc, out.getvalue()


def soft_ribbons(size, seed):
    """A dark opaque frame with a few lighter bands and light grain: low interior detail (about 0.1), like the
    quality-bar scene that is wind-zone's only reference."""
    rn = random.Random(seed)
    rows = []
    for y in range(size):
        base = 60 if (y // 6) % 4 == 0 else 26
        rows.append([(base + rn.randint(0, 5), base + rn.randint(0, 5), base + 8 + rn.randint(0, 5), 255)
                     for _ in range(size)])
    return rows


def crushed_copy(src, out):
    """tools/make_art_calibration.py B7_crushed of one image: the whole frame darkened to 25 %."""
    w, h, rows = read_png(src)
    write_png(out, w, h, [[make_art_calibration.crushed(p) for p in row] for row in rows])
    return out


class NoTeamImageElement(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.mkdtemp()
        self.addCleanup(shutil.rmtree, self.tmp, True)
        rel = art_judge.CALIBRATION_SET + "bar.png"
        self.ref = os.path.join(self.tmp, rel)
        os.makedirs(os.path.dirname(self.ref))
        write_png(self.ref, 96, 96, soft_ribbons(96, 1))
        spec = {"references": [{"id": "bar", "path": rel, "kind": "image", "role": ["quality bar"], "cards": ["MVP 2"],
                                "judge": True, "required": True}],
                "quality_bar": {"refs": ["bar"]},
                "elements": {"zone": {"refs": ["bar"], "score_min": 0.582, "detail_min": 0.421}},
                "scene": {"refs": []}}
        self.refs = os.path.join(self.tmp, "references.json")
        with open(self.refs, "w", encoding="utf-8") as fh:
            json.dump(spec, fh)
        self.spec = spec

    def judge(self, path):
        return judge_cli("--refs", self.refs, "--refs-root", self.tmp, "element", "zone", path)

    def test_broken_on_purpose_a_stale_detail_min_fails_the_reference_itself(self):
        own = art_judge.signature(self.ref)["detail"]
        self.assertLess(own, 0.421)
        rc, out = self.judge(self.ref)
        self.assertEqual(rc, 1, out)
        self.assertIn("FAIL score=0.2", out)

    def test_calibrate_measures_the_references_and_the_reference_passes(self):
        own = art_judge.signature(self.ref)["detail"]
        cal = art_judge.calibrate(self.spec, [self.tmp])
        self.assertEqual(cal["zone"]["basis"], "references")
        self.assertEqual(cal["zone"]["detail"], {"bar": own})
        self.assertEqual(cal["zone"]["detail_min"], round(own - art_judge.MARGIN, 3))
        self.assertIsNone(cal["zone"]["score_min"], "one image: no leave-one-out, the stored score_min stays")
        rc, out = judge_cli("--refs", self.refs, "--refs-root", self.tmp, "calibrate", "--write")
        self.assertEqual(rc, 0, out)
        self.assertIn("team=0 references=1", out)
        with open(self.refs, encoding="utf-8") as fh:
            el = json.load(fh)["elements"]["zone"]
        self.assertEqual(el["detail_min"], round(own - art_judge.MARGIN, 3))
        self.assertEqual(el["score_min"], 0.582)
        self.assertIn("no team image", el["calibration"]["method"])
        rc, out = self.judge(self.ref)
        self.assertEqual(rc, 0, out)
        self.assertIn("PASS score=1.0", out)

    def test_known_bad_renders_still_fail_after_calibrate(self):
        judge_cli("--refs", self.refs, "--refs-root", self.tmp, "calibrate", "--write")
        crushed = crushed_copy(self.ref, os.path.join(self.tmp, "B7_crushed.png"))
        flat = os.path.join(self.tmp, "flat.png")
        write_png(flat, 96, 96, [[(40, 40, 52, 255)] * 96 for _ in range(96)])
        for bad in (crushed, flat):
            with self.subTest(os.path.basename(bad)):
                rc, out = self.judge(bad)
                self.assertEqual(rc, 1, out)
                self.assertIn("FAIL", out)

    def test_two_references_and_no_team_image_get_a_leave_one_out_score_min(self):
        rel = art_judge.CALIBRATION_SET + "bar2.png"
        write_png(os.path.join(self.tmp, rel), 96, 96, soft_ribbons(96, 2))
        self.spec["references"].append(dict(self.spec["references"][0], id="bar2", path=rel))
        self.spec["quality_bar"]["refs"].append("bar2")
        self.spec["elements"]["zone"]["refs"].append("bar2")
        c = art_judge.calibrate(self.spec, [self.tmp])["zone"]
        self.assertEqual(sorted(c["loo"]), ["bar", "bar2"])
        self.assertEqual(c["score_min"], round(min(c["loo"].values()) - art_judge.MARGIN, 3))
        self.assertEqual(c["detail_min"], round(min(c["detail"].values()) - art_judge.MARGIN, 3))

    def test_a_team_image_still_sets_the_bar_alone(self):
        """One team image next to the quality bar: the team image's detail is the floor, as before (the quality bar
        never lowers it)."""
        rel = art_judge.CALIBRATION_SET + "team.png"
        rn = random.Random(3)
        write_png(os.path.join(self.tmp, rel), 96, 96,
                  [[(rn.randrange(256),) * 3 + (255,) for _ in range(96)] for _ in range(96)])
        self.spec["references"].append({"id": "team", "path": rel, "kind": "image", "role": ["effects"],
                                        "cards": ["MVP 2"], "judge": True, "required": True})
        self.spec["elements"]["zone"]["refs"].append("team")
        c = art_judge.calibrate(self.spec, [self.tmp])["zone"]
        self.assertEqual(c["basis"], "team")
        self.assertEqual(list(c["detail"]), ["team"])
        self.assertGreater(c["detail_min"], art_judge.signature(self.ref)["detail"])


@unittest.skipIf(hermetic.refs_left_out(), hermetic.LEFT_OUT)
class RealReferences(unittest.TestCase):
    WIND = {"wind-zone": "bar-other-realm", "wind-lines": "keyart-wind-lines"}

    @classmethod
    def setUpClass(cls):
        cls.refs = art_judge.load_refs()
        cls.byid = art_judge.refs_by_id(cls.refs)
        cls.cal = art_judge.calibrate(cls.refs, [ROOT])

    def path(self, rid):
        return art_judge.find_ref(self.byid[rid]["path"], [ROOT])

    def test_every_measured_image_clears_its_own_element(self):
        """Each image calibrate measured for an element, judged as itself (its own cell), has at least the stored
        detail_min and, against itself, at least the stored score_min."""
        for eid, c in self.cal.items():
            if eid == "scene":
                continue
            el = self.refs["elements"][eid]
            self.assertTrue(c["detail"], f"{eid}: calibrate measured no image")
            for rid in c["detail"]:
                with self.subTest(element=eid, ref=rid):
                    s = art_judge.signature(self.path(rid), self.byid[rid].get("cell"))
                    self.assertGreaterEqual(s["detail"], el["detail_min"])
                    self.assertGreaterEqual(art_judge.element_score(s, s), el["score_min"])

    def test_references_json_holds_the_wind_numbers_calibrate_measures(self):
        for eid in self.WIND:
            with self.subTest(eid):
                self.assertEqual(self.refs["elements"][eid]["detail_min"], self.cal[eid]["detail_min"],
                                 "re-run tools/art_judge.py calibrate --write")
                self.assertEqual(self.refs["elements"][eid]["calibration"]["detail"], self.cal[eid]["detail"])
        self.assertEqual(self.cal["wind-zone"]["basis"], "references")
        self.assertEqual(self.cal["wind-lines"]["basis"], "team")

    def test_each_wind_reference_passes_its_own_element(self):
        for eid, rid in self.WIND.items():
            with self.subTest(eid):
                rc, out = judge_cli("element", eid, self.path(rid))
                self.assertEqual(rc, 0, out)
                self.assertIn(f"art_judge: element {eid} PASS score=1.0", out)

    def test_a_known_bad_render_of_each_wind_reference_fails(self):
        tmp = tempfile.mkdtemp()
        self.addCleanup(shutil.rmtree, tmp, True)
        for eid, rid in self.WIND.items():
            with self.subTest(eid):
                bad = crushed_copy(self.path(rid), os.path.join(tmp, eid + "_B7_crushed.png"))
                rc, out = judge_cli("element", eid, bad)
                self.assertEqual(rc, 1, out)
                self.assertIn(f"art_judge: element {eid} FAIL", out)


if __name__ == "__main__":
    unittest.main()
