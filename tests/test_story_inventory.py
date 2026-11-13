"""Tests for tools/build/story_inventory.py: shipped player text must be a lines.csv row, and rows must match the source."""
import os
import shutil
import sys
import tempfile
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(HERE)
sys.path.insert(0, os.path.join(REPO, "tools"))
sys.path.insert(0, os.path.join(REPO, "tools", "build"))
import story_inventory  # noqa: E402

SRC = "Source/UmbrellaElla/Private/UI/Demo.cpp"
HEADER = "id,surface,text,facts,ship,note\n"


def put(root, rel, text):
    path = os.path.join(root, rel)
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as fh:
        fh.write(text)


class SurfaceOf(unittest.TestCase):
    def test_labels_name_things_and_actions_stay_buttons(self):
        f = lambda t: story_inventory.surface_of({"text": t, "screen": "settings", "kind": "ui"})
        self.assertEqual(f("Movement speed"), "label")
        self.assertEqual(f("Deaths"), "label")
        self.assertEqual(f("Quit"), "button")
        self.assertEqual(f("Keep Editing"), "button")
        self.assertEqual(f("Paused"), "screen")
        self.assertEqual(story_inventory.surface_of({"text": "Next spell", "screen": "settings-controller", "kind": "ui"}), "label")
        self.assertEqual(f("A long sentence about many things here"), "screen")


class Inventory(unittest.TestCase):
    def setUp(self):
        self.root = tempfile.mkdtemp()
        self.old = story_inventory.ROOT
        story_inventory.ROOT = self.root
        put(self.root, SRC, 'a(LOCTEXT("K", "Hop"));\nb(FText::FromString(TEXT("Start Game")));\nc(FText::FromString(TEXT("%d")));\n')
        put(self.root, "Source/UmbrellaElla/Private/Tests/T.cpp", 'x(FText::FromString(TEXT("Test only")));')
        put(self.root, "Source/UmbrellaElla/Private/Feedback/Audio/SoundLabelHud.cpp", 'x(FText::FromString(TEXT("Dev label")));')
        self.rows = HEADER + 'ui-hop,button,Hop,,yes,screen=settings\nui-start,button,Start Game,,yes,screen=title\n'
        put(self.root, story_inventory.LINES, self.rows)

    def tearDown(self):
        story_inventory.ROOT = self.old
        shutil.rmtree(self.root)

    def test_clean_tree_passes_and_skips_tests_dev_and_formats(self):
        self.assertEqual(story_inventory.problems(), [])
        self.assertEqual(story_inventory.main(["x", "check"]), 0)

    def test_new_shipped_text_without_a_row_fails(self):
        put(self.root, SRC, open(os.path.join(self.root, SRC)).read() + 'd(LOCTEXT("N", "Quit"));\n')
        bad = story_inventory.problems()
        self.assertEqual(len(bad), 1)
        self.assertIn("[missing]", bad[0])
        self.assertIn("Quit", bad[0])
        self.assertEqual(story_inventory.main(["x", "check"]), 1)

    def test_row_text_that_differs_from_source_fails(self):
        put(self.root, story_inventory.LINES, self.rows.replace("Hop,,yes", "Hop!,,yes"))
        kinds = sorted(b.split("]")[0] for b in story_inventory.problems())
        self.assertEqual(kinds, ["FAIL [differs", "FAIL [missing"])

    def test_write_adds_only_the_missing_row(self):
        put(self.root, SRC, open(os.path.join(self.root, SRC)).read() + 'd(LOCTEXT("N", "Quit"));\n')
        story_inventory.write()
        self.assertEqual(story_inventory.problems(), [])
        self.assertEqual(len(story_inventory.read_rows()), 3)

    def test_gate_runs_it_as_blocking(self):
        import quality_gate
        self.assertIn("story_inventory", quality_gate.BLOCKING)


if __name__ == "__main__":
    unittest.main()
