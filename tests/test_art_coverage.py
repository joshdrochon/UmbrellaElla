"""GDD SH1.0 animation coverage (pipeline/art/blender/characters.json `coverage`; Ricky's import audit point 6).

Every required family the GDD names has a row; a `recipe` row renders through plan.py today; a `_PH` row names a
placeholder that ends in _PH and the Day-0 card that replaces it. Placeholders never ship (pipeline_check --release)."""
import json
import os
import re
import sys
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, os.path.join(ROOT, "pipeline", "art", "blender"))
import plan  # noqa: E402

with open(os.path.join(ROOT, "pipeline", "art", "blender", "characters.json"), encoding="utf-8") as fh:
    REC = json.load(fh)
with open(os.path.join(ROOT, "docs", "feature-manifest.json"), encoding="utf-8") as fh:
    IDS = {f["feature_id"] for f in json.load(fh)["features"]}
with open(os.path.join(ROOT, "pipeline", "day0-cards.md"), encoding="utf-8") as fh:
    CARDS = set(re.findall(r"^\| (0\.\d+[a-z]?) \|", fh.read(), re.M))


class Coverage(unittest.TestCase):
    def test_every_required_family_has_rows(self):
        got = {e["gdd"] for e in REC["coverage"]}
        self.assertLessEqual({"ANIM-03", "ANIM-04", "ANIM-05", "ANIM-06", "ANIM-08", "ART-08", "BG-03", "BG-04",
                              "VFX-03", "VFX-04", "VFX-05"}, got)
        self.assertEqual(got - IDS, set(), "every row cites a GDD SH1.0 Rule ID")
        enemies = [e for e in REC["coverage"] if e["family"] == "enemy"]
        self.assertEqual(len(enemies), 10, "five enemy types, male and female (COM-12)")

    def test_recipe_rows_render_and_placeholders_are_tracked(self):
        for e in REC["coverage"]:
            with self.subTest(e["action"]):
                self.assertIn(e["status"], ("recipe", "_PH"))
                self.assertIn(e["tool"], ("blender", "unreal"))
                if e["status"] == "recipe":
                    ch, anim = e["recipe"].split(".")
                    job = plan.job(ch, anim, "Art/Source/Test", root=ROOT)
                    self.assertTrue(job["frames"])
                else:
                    self.assertRegex(e["placeholder"], r"^(FB|T|SPR|NS)_[A-Z][A-Za-z0-9]*_[A-Z][A-Za-z0-9]*_PH$")
                    self.assertIn(e["replaced_by"], CARDS, "the replacing card is a Day-0 row")

    def test_the_stand_ins_follow_gdd_sh10(self):
        with open(os.path.join(ROOT, "pipeline", "art", "blender", "stand_ins.py"), encoding="utf-8") as fh:
            src = fh.read()
        self.assertNotIn("# gear crown", src, "the Keeper is crownless (OWL-08)")
        self.assertNotIn('star.name = "wand_star"', src, "Ella has no wand (ART-06)")
        self.assertIn("no wand", REC["characters"]["ella"]["what"])


if __name__ == "__main__":
    unittest.main()
