"""The art bar is calibrated from the team's own art (Josh, 11 Nov), never left at a guessed number.

- Every judge element's score_min is the lowest leave-one-out score of its team images minus a small margin, and its
  detail_min the lowest team image's interior detail minus the margin; the scene similarity_min the same over the
  scene references (tools/art_judge.py calibrate). The numbers in pipeline/art/references.json must be the ones a
  fresh calibration measures, in every repo: only the fixed set under pipeline/art/reference/ counts, so a repo's
  Assets/ studies (present or not) never change them.
- The first rough Blender renders (tests/fixtures/art/crude/) FAIL every element they target: broken on purpose.
- style.json paper_texture_min is 0.38, half the key art's measured 0.77; the key art and its earlier cut pass.
The critic's calibration, the panel and the in-engine context are in tests/test_art_ship.py."""
import json
import os
import sys
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, os.path.join(ROOT, "tools"))
sys.path.insert(0, HERE)
import art_check  # noqa: E402
import art_judge  # noqa: E402
import hermetic  # noqa: E402

CRUDE = os.path.join(HERE, "fixtures", "art", "crude")
TARGETS = {"ella_idle_crude.png": ["ella-up-open"], "ella_attack_crude.png": ["ella-attack", "ella-closed"],
           "owl_flap_crude.png": ["owl"], "bolt_crude.png": ["owl-bolt"], "skyline_crude.png": ["skyline"]}


def real_png(p):
    try:
        with open(p, "rb") as fh:
            return fh.read(8) == b"\x89PNG\r\n\x1a\n"
    except OSError:
        return False


SKIP = hermetic.refs_left_out() or not all(real_png(os.path.join(CRUDE, f)) for f in TARGETS)


@unittest.skipIf(SKIP, hermetic.LEFT_OUT)
class Calibrated(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.refs = art_judge.load_refs()
        cls.cal = art_judge.calibrate(cls.refs, [ROOT])
        with open(art_judge.REFS, encoding="utf-8") as fh:
            cls.raw = json.load(fh)

    def test_references_json_holds_the_measured_numbers(self):
        for eid, c in self.cal.items():
            with self.subTest(eid):
                if eid == "scene":
                    self.assertEqual(self.refs["scene"]["similarity_min"], c["similarity_min"])
                    self.assertEqual(self.refs["scene"]["calibration"]["loo"], c["loo"])
                    continue
                el = self.refs["elements"][eid]
                self.assertEqual(el["calibration"]["loo"], c["loo"], "re-run tools/art_judge.py calibrate --write")
                if c["score_min"] is not None:
                    self.assertEqual(el["score_min"], c["score_min"])
                    self.assertAlmostEqual(el["score_min"], min(c["loo"].values()) - art_judge.MARGIN, places=3)
                if c["detail_min"] is not None:
                    self.assertEqual(el["detail_min"], c["detail_min"])

    def test_the_numbers_do_not_depend_on_the_repo_s_assets_studies(self):
        """Calibration is a property of the fixed set under pipeline/art/reference/ (PipelineTesting PR #12: with the
        Assets/ studies checked out, the old leave-one-out changed and 116 subtests failed). The same numbers come out
        with every optional study present (stand-in images at their paths) and with none present."""
        import random
        import shutil
        import tempfile
        from png import write_png
        import art_check
        want = {e: c for e, c in self.cal.items()}
        present = tempfile.mkdtemp()
        absent = tempfile.mkdtemp()
        self.addCleanup(shutil.rmtree, present, True)
        self.addCleanup(shutil.rmtree, absent, True)
        optional = [r["path"] for r in self.raw["references"]
                    if r.get("required") is False and r.get("kind") == "image" and r.get("path")]
        self.assertTrue(optional)
        for i, rel in enumerate(optional):
            rnd = random.Random(i)
            full = os.path.join(present, rel)
            os.makedirs(os.path.dirname(full), exist_ok=True)
            write_png(full, 48, 48, [[(rnd.randrange(256), rnd.randrange(256), rnd.randrange(256), 255)
                                      for _ in range(48)] for _ in range(48)])
        spec = art_check.load_spec(present, art_judge.REFS)
        self.assertEqual(spec["_team_art"]["left_out"], [], "every optional study is present")
        self.assertEqual(art_judge.calibrate(spec, [present, ROOT]), want, "studies present")
        spec = art_check.load_spec(absent, art_judge.REFS)
        self.assertEqual(len(spec["_team_art"]["left_out"]), len(optional))
        self.assertEqual(art_judge.calibrate(spec, [absent, ROOT]), want, "studies absent")
        # broken on purpose: calibrating over every listed image again makes the numbers repo-dependent
        real = art_judge.calibrated_ref
        try:
            art_judge.calibrated_ref = lambda ref: ref.get("kind") == "image"
            spec = art_check.load_spec(present, art_judge.REFS)
            self.assertNotEqual(art_judge.calibrate(spec, [present, ROOT]), want)
        finally:
            art_judge.calibrated_ref = real

    def test_every_team_image_clears_its_own_element(self):
        for eid, c in self.cal.items():
            if eid == "scene":
                self.assertTrue(all(s >= self.refs["scene"]["similarity_min"] for s in c["loo"].values()))
                continue
            el = self.refs["elements"][eid]
            for rid, s in c["loo"].items():
                self.assertGreaterEqual(s, el["score_min"], f"{eid}: team image {rid}")
            for rid, d in c["detail"].items():
                self.assertGreaterEqual(d, el.get("detail_min", 0.0), f"{eid}: team image {rid} detail")

    def test_broken_on_purpose_the_rough_blender_renders_fail_every_element_they_target(self):
        for f, elements in TARGETS.items():
            for eid in elements:
                with self.subTest(render=f, element=eid):
                    el, rows, _ = art_judge.element(eid, [os.path.join(CRUDE, f)], self.refs, [ROOT])
                    self.assertLess(rows[0][1], el["score_min"], f"{f} must fail {eid}")

    def test_scene_bar_rose_from_the_guess(self):
        self.assertGreater(self.refs["scene"]["similarity_min"], 0.65)


class PaperTexture(unittest.TestCase):
    def test_paper_texture_min_is_half_the_key_art(self):
        with open(os.path.join(ROOT, "pipeline", "art", "style.json"), encoding="utf-8") as fh:
            st = json.load(fh)
        self.assertEqual(st["thresholds"]["paper_texture_min"], 0.38)
        self.assertNotIn("paper_texture_min is provisional", st["texture_note"])

    @unittest.skipIf(SKIP, hermetic.LEFT_OUT)
    def test_key_art_and_its_earlier_cut_pass_and_a_flat_frame_fails(self):
        with open(os.path.join(ROOT, "pipeline", "art", "style.json"), encoding="utf-8") as fh:
            st = json.load(fh)
        for rel in ("pipeline/art/reference/target-keyart.png", "pipeline/art/reference/Mockups/originalPicture.png"):
            m = art_check.measure(os.path.join(ROOT, rel), st)
            self.assertGreaterEqual(m["paper_texture"], 0.38, rel)
            self.assertEqual(art_check.evaluate(m, st), [], rel)
        import tempfile
        from png import write_png
        p = os.path.join(tempfile.mkdtemp(), "flat.png")
        write_png(p, 64, 36, [[(147, 120, 107, 255) if x > 8 else (20, 18, 16, 255) for x in range(64)]
                              for _ in range(36)])
        self.assertTrue(any(f.startswith("paper_texture") for f in art_check.evaluate(art_check.measure(p, st), st)))


if __name__ == "__main__":
    unittest.main()
