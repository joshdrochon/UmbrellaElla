import csv
import os
import sys
import unittest

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, os.path.join(ROOT, "tools", "build"))
sys.path.insert(0, os.path.join(ROOT, "tools", "build", "assets"))
import art_slots  # noqa: E402


class ArtSlots(unittest.TestCase):
    def test_every_inventory_visual_has_a_unique_slot(self):
        names = [art_slots.slot_path(v) for v in art_slots.visuals() if v not in art_slots.NO_SLOT]
        self.assertGreaterEqual(len(names), 100)
        self.assertNotIn("", names)
        self.assertEqual(len(names), len(set(names)))

    def test_cpp_catalogue_matches_the_inventory(self):
        self.assertEqual(art_slots.main(["check"]), 0)

    def test_csv_slot_column_matches(self):
        with open(os.path.join(ROOT, art_slots.CSV), newline="", encoding="utf-8") as fh:
            for r in csv.DictReader(fh):
                self.assertEqual(r["slot"], art_slots.slot_path(r["visual"]))
                self.assertEqual(r["drawn_by"], art_slots.consumer(r["visual"]))

    def test_slots_the_presenters_load_are_marked_drawn(self):
        by = {v: art_slots.consumer(v) for v in art_slots.visuals()}
        self.assertEqual(by["bg-layer:FarLand"], "UUmbrellaBackdropSubsystem")
        self.assertEqual(by["ella-state:Hurt"], "UEllaAnimPresenterComponent")
        self.assertEqual(by["enemy:Floodstrider:Male"], "UEnemyPresenterSubsystem")
        self.assertEqual(by["vfx-sheet:VFX_Gust"], "VfxSheetVisual")

    def test_import_script_resolves_visual_id_and_slot_path(self):
        import import_art_candidate as imp
        self.assertEqual(imp.resolve("bg-layer:FarLand"), ("/Game/UmbrellaElla/Art/Scene", "T_Skyline_PH", False))
        self.assertEqual(imp.resolve("/Game/UmbrellaElla/Art/Scene/T_Paper")[2], True)
        with self.assertRaises(SystemExit):
            imp.resolve("no:such")
        with self.assertRaises(SystemExit):
            imp.resolve("vfx-material:M_VFX_Sheet")   # a material, not a texture slot


if __name__ == "__main__":
    unittest.main()
