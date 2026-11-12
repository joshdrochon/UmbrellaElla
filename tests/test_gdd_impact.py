"""tools/gdd_impact.py: a planted revision shows added, removed, changed and status IDs and the lines citing them."""
import io
import json
import os
import sys
import tempfile
import unittest
from contextlib import redirect_stdout

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, os.path.join(ROOT, "tools"))
import gdd_impact as gi  # noqa: E402

SNAP = os.path.join(ROOT, "docs", "gdd", "GDD-B1.0.md")


def revised():
    with open(SNAP, encoding="utf-8") as fh:
        t = fh.read()
    t = t.replace("| Revision | B1.0 |", "| Revision | B1.1 |")
    t = t.replace("| UMB-02 | Closed umbrella can be aimed to shoot while falling. | PROPOSED |",
                  "| UMB-02 | Closed umbrella can be aimed to shoot while falling. | APPROVED_P1 |")
    t = t.replace("| HAZ-01 | Steam pipes or independent environmental obstacles. | EXPERIMENT |\n", "")
    t = t.replace("| HAZ-01 | Steam vent / OFF | Hazard field | Dedicated scenario |\n", "")
    t = t.replace("Steam vent | Environmental timed", "Steam vents | Environmental timed")
    t = t.replace("| WIND-02 | Some wind damages umbrella integrity. | PROPOSED |",
                  "| WIND-02 | Some wind damages umbrella integrity. | PROPOSED |\n| CORE-04 | Gravity slider in the workbench. | PROPOSED |")
    t = t.replace("No stuck input, unintended lift", "No stuck input, no unintended lift")
    t = t.replace("| OWL-01 | Owl launches visible, dodgeable projectile threats. |",
                  "| OWL-01 | Owl launches visible and dodgeable projectile threats. |")
    return t


class GddImpact(unittest.TestCase):
    def test_same_snapshot_has_no_impact(self):
        lines, d = gi.report(SNAP, SNAP, ROOT)
        self.assertEqual(gi.touched(d), [])
        self.assertTrue(lines[0].startswith("gdd_impact old=B1.0 new=B1.0 added=0 removed=0 changed=0 status=0 cited=0"))

    def test_revision_diff_and_citations(self):
        with tempfile.NamedTemporaryFile("w", suffix=".md", delete=False, encoding="utf-8") as fh:
            fh.write(revised())
        try:
            lines, d = gi.report(SNAP, fh.name, ROOT)
        finally:
            os.remove(fh.name)
        self.assertEqual(d["added"], ["CORE-04"])
        self.assertEqual(d["removed"], ["HAZ-01"])
        self.assertIn("UMB-02", d["changed"])
        self.assertIn("QA-02", d["changed"])
        self.assertIn(("UMB-02", "PROPOSED", "APPROVED_P1"), d["status"])
        text = "\n".join(lines)
        self.assertIn("new=B1.1", lines[0])
        self.assertIn("docs/feature-manifest.json", text)       # the manifest record of a touched ID
        self.assertIn("[test-map row QA-02]", text)              # the test-map row citing a changed QA
        self.assertIn("[manifest record CORE-04]", text)         # GDD SH1.0's CORE-04 record cites the added ID
        self.assertNotIn("docs/gdd/", text.split("cited by:", 1)[1])

    def test_stolen_hour_import(self):
        """GDD 1.3 -> SH1.0: a new game, so every 1.3 feature leaves and every SH1.0 Rule ID arrives."""
        lines, d = gi.report(os.path.join(ROOT, "docs", "gdd", "GDD-1.3.md"),
                             os.path.join(ROOT, "docs", "gdd", "GDD-SH1.0.md"), ROOT)
        self.assertIn("old=1.3 new=SH1.0", lines[0])
        self.assertIn("FLOW-02", d["added"])
        self.assertIn("QA-42", d["added"])
        self.assertIn("END-01", d["removed"])
        self.assertIn(("OWL-11", None, "APPROVED_P0"), d["status"])

    def test_manifest_diff(self):
        # the frozen 1.3 manifest: it still has a PROPOSED record to promote (GDD SH1.0 approves everything)
        with open(os.path.join(HERE, "fixtures", "gdd13", "docs", "feature-manifest.json"), encoding="utf-8") as fh:
            man = json.load(fh)
        new = json.loads(json.dumps(man))
        for f in new["features"]:
            if f["feature_id"] == "UMB-03":
                f["status"] = "APPROVED_P1"
                f["implementation_authorized"] = True
        paths = []
        for data in (man, new):
            with tempfile.NamedTemporaryFile("w", suffix=".json", delete=False, encoding="utf-8") as fh:
                json.dump(data, fh)
            paths.append(fh.name)
        try:
            out = io.StringIO()
            with redirect_stdout(out):
                self.assertEqual(gi.main(paths + ["--root", ROOT]), 0)
        finally:
            for p in paths:
                os.remove(p)
        self.assertIn("status: UMB-03 PROPOSED -> APPROVED_P1", out.getvalue())
        self.assertIn("changed: UMB-03", out.getvalue())

    def test_unreadable_input_exits_2(self):
        with redirect_stdout(io.StringIO()):
            self.assertEqual(gi.main(["/nonexistent.md", SNAP]), 2)


if __name__ == "__main__":
    unittest.main()
