"""Tests for tools/build/art_inventory.py: a shipped visual with no art-loop piece must FAIL."""
import json
import os
import shutil
import sys
import tempfile
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(HERE)
sys.path.insert(0, os.path.join(REPO, "tools"))
sys.path.insert(0, os.path.join(REPO, "tools", "build"))
import art_inventory  # noqa: E402
import art_loop  # noqa: E402

FLOW = "Source/UmbrellaElla/Public/Flow/FlowRules.h"
VFX = "Source/UmbrellaElla/Public/Feedback/Vfx/VfxCatalog.h"
REFS = "pipeline/art/references.json"


def put(root, rel, text):
    path = os.path.join(root, rel)
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as fh:
        fh.write(text)


class FakeTree(unittest.TestCase):
    """A tiny repo: one screen, one VFX sheet, references.json with their pieces. Static GDD rows are cleared."""

    def setUp(self):
        self.root = tempfile.mkdtemp()
        self.old = (art_inventory.ROOT, art_inventory.STATIC[:])
        art_inventory.ROOT = self.root
        del art_inventory.STATIC[:]
        put(self.root, FLOW, "enum class EFlowScreen : uint8\n{\n\tTitle,\n\tPlaying\n};\n")
        put(self.root, VFX, '{ TEXT("Key"), TEXT("VFX_GoldTravel"), 1 },\n')
        self.refs = {"elements": {"ui-title": {"owner": "artui"}, "ui-hud-clock": {"owner": "artui"},
                                  "wand-shot": {}}}
        self.save()

    def tearDown(self):
        art_inventory.ROOT = self.old[0]
        art_inventory.STATIC[:] = self.old[1]
        shutil.rmtree(self.root, ignore_errors=True)

    def save(self):
        put(self.root, REFS, json.dumps(self.refs))

    def fails(self):
        return [p for p in art_inventory.build({})[1]]


class Rules(FakeTree):
    def test_covered_tree_passes(self):
        rows, problems = art_inventory.build({})
        self.assertEqual(problems, [])
        self.assertEqual({r[0] for r in rows}, {"screen:Title", "screen:Playing", "vfx-sheet:VFX_GoldTravel"})
        self.assertEqual({r[3] for r in rows}, {"artui", "artshots"})

    def test_new_screen_without_piece_fails(self):
        put(self.root, FLOW, "enum class EFlowScreen : uint8\n{\n\tTitle,\n\tPlaying,\n\tTrophyRoom\n};\n")
        self.assertTrue(any("screen:TrophyRoom" in p and "no art-loop piece" in p for p in self.fails()))

    def test_new_vfx_sheet_without_piece_fails(self):
        put(self.root, VFX, '{ TEXT("Key"), TEXT("VFX_GoldTravel"), 1 },\n{ TEXT("B"), TEXT("VFX_Rainbow"), 1 },\n')
        self.assertTrue(any("vfx-sheet:VFX_Rainbow" in p for p in self.fails()))

    def test_piece_missing_from_references_fails(self):
        del self.refs["elements"]["ui-title"]
        self.save()
        self.assertTrue(any("screen:Title" in p and "not an element" in p for p in self.fails()))

    def test_piece_without_owner_fails(self):
        self.refs["elements"]["ui-title"] = {}
        self.save()
        self.assertTrue(any("ui-title" in p and "owner" in p for p in self.fails()))

    def test_unknown_art_file_fails(self):
        put(self.root, "Art/Enemy/Roadwarden_Idle.png", "x")
        self.assertTrue(any("file:Art/Enemy/Roadwarden_Idle.png" in p for p in self.fails()))

    def test_known_sheet_file_is_covered_not_new(self):
        put(self.root, "Art/Source/VFX/Raw/VFX_GoldTravel_PH.png", "x")
        put(self.root, "Content/UmbrellaElla/Art/VFX/T_VFX_GoldTravel_PH.uasset", "x")
        rows, problems = art_inventory.build({})
        self.assertEqual(problems, [])
        self.assertEqual(len([r for r in rows if r[0] == "vfx-sheet:VFX_GoldTravel"]), 1)

    def test_widget_without_piece_fails(self):
        put(self.root, "Source/UmbrellaElla/Public/UI/NewWidget.h",
            "class UMBRELLAELLA_API UTrophyWidget : public UUserWidget\n{\n};\n")
        self.assertTrue(any("widget:UTrophyWidget" in p for p in self.fails()))

    def test_static_rule_id_must_exist_in_manifest(self):
        art_inventory.STATIC.append(("x:y", "ZZZ-99", "ui-title"))
        put(self.root, "docs/feature-manifest.json", json.dumps({"features": [{"feature_id": "ART-01"}]}))
        self.assertTrue(any("ZZZ-99" in p for p in self.fails()))

    def test_stale_csv_fails_and_written_csv_passes(self):
        put(self.root, art_inventory.CSV, "visual,source,piece,owner,passed\n")
        self.assertEqual(art_inventory.main(["check"]), 1)
        self.assertEqual(art_inventory.main(["write"]), 0)
        self.assertEqual(art_inventory.main(["check"]), 0)


class Passed(FakeTree):
    PAIRS = {"reference": "ours", "quality_bar": "same"}

    def shipped(self, data=b"png-bytes"):
        put(self.root, "Art/Title.png", "x")
        with open(os.path.join(self.root, "Art/Title.png"), "wb") as fh:
            fh.write(data)
        return art_loop.content_sha(os.path.join(self.root, "Art/Title.png"))

    def rec(self, sha, **kw):
        r = {"piece": "ui-title", "round": 1, "verdict": "ours", "checks": True, "pairs": self.PAIRS,
             "files": sha, "file": "Art/Title.png"}
        r.update(kw)
        return r

    def passed(self, *recs):
        return art_inventory.passed_pieces({"ui-title": list(recs)}, self.root)

    def test_loop_writes_tracked_record_that_inventory_counts(self):
        sha = self.shipped()
        rec = {"round": 1, "verdict": "ours", "checks": True, "pairs": self.PAIRS, "panel": 3, "sha": sha,
               "file": os.path.join(self.root, "Art/Title.png")}
        path = art_loop.write_critic_record(self.root, "C1", "ui-title", rec, "refs12", "abc")
        self.assertEqual(path, os.path.join(self.root, "pipeline/art/critic/ui-title.json"))
        saved = json.load(open(path))["records"][0]
        for k in ("piece", "round", "verdict", "checks", "pairs", "files", "at"):
            self.assertIn(k, saved)
        self.assertEqual(saved["file"], "Art/Title.png")
        rows, _ = art_inventory.build()
        self.assertEqual({r[0]: r[4] for r in rows}["screen:Title"], "yes")

    def test_newest_round_decides(self):
        sha = self.shipped()
        bad = self.rec(sha, verdict="reference")
        self.assertEqual(self.passed(bad, self.rec(sha, round=2)), {"ui-title"})
        self.assertEqual(self.passed(self.rec(sha), dict(bad, round=2)), set())

    def test_changed_image_does_not_pass(self):
        sha = self.shipped()
        self.shipped(b"edited after the pass")
        self.assertEqual(self.passed(self.rec(sha)), set())

    def test_failed_checks_or_missing_pair_do_not_pass(self):
        sha = self.shipped()
        self.assertEqual(self.passed(self.rec(sha, checks=False)), set())
        self.assertEqual(self.passed(self.rec(sha, pairs={"reference": "ours"})), set())

    def test_saved_logs_never_count(self):
        sha = self.shipped()
        rec = {"piece": "ui-title", "verdict": "ours", "checks": True, "pairs": self.PAIRS, "sha": sha}
        put(self.root, "Saved/Logs/pipeline/art-loop.jsonl", json.dumps(rec) + "\n")
        rows, _ = art_inventory.build()
        self.assertEqual({r[0]: r[4] for r in rows}["screen:Title"], "no")

    def test_rows_and_summary_count_passes(self):
        sha = self.shipped()
        rows, _ = art_inventory.build({"ui-title": [self.rec(sha, verdict="same")]})
        self.assertEqual({r[0]: r[4] for r in rows}["screen:Title"], "yes")
        self.assertTrue(art_inventory.summary(rows).startswith("TOTAL=3 PASSED=1 "))


class RealTree(unittest.TestCase):
    def test_repository_inventory_is_complete_and_current(self):
        rows, problems = art_inventory.build({})
        self.assertEqual(problems, [])
        self.assertGreater(len(rows), 28)
        on_disk = art_inventory.read_csv()
        self.assertEqual([r[:4] for r in on_disk[1:]], [r[:4] for r in rows])

    def test_gate_runs_the_check_as_blocking(self):
        import quality_gate
        self.assertIn("art_inventory", quality_gate.BLOCKING)


if __name__ == "__main__":
    unittest.main()
