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

    def test_packed_standin_sheets_get_their_cell_layout(self):
        # B2 follow-up: a 24-frame grid drawn as one picture showed Ella as 24 specks.
        self.assertEqual(art_slots.sheet_layout("x/Ella_idle_N24_grid.png", (2886, 2616)), (6, 4))
        self.assertEqual(art_slots.sheet_layout("x/ella-hurt_N24_strip.png", (23688, 565)), (24, 1))
        self.assertIsNone(art_slots.sheet_layout("x/artella_final1.png", (1920, 1080)))
        with self.assertRaises(SystemExit):
            art_slots.sheet_layout("x/odd_N24_grid.png", (2887, 2616))
        rows = art_slots.cpp_rows(["ella-state:Idle", "bg-layer:Sky", "vfx-sheet:VFX_Gust"])
        self.assertIn('TEXT("T_Ella_Idle"), 6, false, TEXT("UEllaAnimPresenterComponent"), 4, true }', rows)
        self.assertIn('TEXT("T_Paper"), 1, true, TEXT("UUmbrellaBackdropSubsystem"), 1, true }', rows)
        self.assertIn('TEXT("T_VFX_Gust"), 8, false, TEXT("VfxSheetVisual"), 1, true }', rows)

    def test_standin_admission_rejects_unkeyed_and_framed_pictures(self):
        # Josh's 15:50 frame: framed gust cards and opaque boxes on the play screen. Synthetic alpha grids.
        n = 40
        keyed_sprite = [[255 if 10 <= x < 30 and 10 <= y < 30 else 0 for x in range(n)] for y in range(n)]
        opaque_box = [[255] * n for _ in range(n)]
        framed = [[255 if x in (1, n - 2) or y in (1, n - 2) or (15 <= x < 25 and 15 <= y < 25) else 0
                   for x in range(n)] for y in range(n)]
        self.assertEqual(art_slots.standin_verdict_alpha(n, n, keyed_sprite), "ok")
        self.assertEqual(art_slots.standin_verdict_alpha(n, n, opaque_box), "unkeyed")
        self.assertEqual(art_slots.standin_verdict_alpha(n, n, framed), "framed")
        self.assertEqual(art_slots.standin_verdict_alpha(n, n, opaque_box, full_frame=True), "ok")
        # A sheet is judged per cell: two keyed cells side by side are not a frame.
        two = [row + row for row in keyed_sprite]
        self.assertEqual(art_slots.standin_verdict_alpha(2 * n, n, two, cols=2), "ok")

    def test_real_standins_on_the_1550_frame_are_rejected(self):
        # The wind field picture carries a drawn frame; the stream beam and courier are opaque rectangles.
        self.assertEqual(art_slots.standin_verdict("wind:current-field"), "framed")
        self.assertEqual(art_slots.standin_verdict("shot:stream-beam"), "unkeyed")
        self.assertEqual(art_slots.standin_verdict("enemy:SkyCourier:Male"), "unkeyed")
        self.assertEqual(art_slots.standin_verdict("ella-state:Idle"), "ok")
        self.assertEqual(art_slots.standin_verdict("bg-layer:Sky"), "ok")   # full-frame backdrop
        rows = art_slots.cpp_rows(["wind:current-field", "ella-state:Idle"])
        self.assertIn('TEXT("T_WindZone"), 1, false, TEXT("UWindPresenterSubsystem"), 1, false }', rows)
        self.assertTrue(rows.rstrip().endswith("4, true },"))

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
