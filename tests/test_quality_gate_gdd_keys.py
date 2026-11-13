"""quality_gate's no-new-FAIL compare for gdd_check (Nov 13): a gap moving between a broken binding and a NOT_IN_GAME P0
row, or with new owner text, is the same fail; a new key and every other FAIL form still count as new."""
import os, sys, unittest
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "tools", "build"))
import quality_gate  # noqa: E402

MAIN = ["FAIL broken CAM-05.h.3: Source/x.h:HighFraction not found in the source",
        "FAIL NOT_IN_GAME P0 CAM-05.value GDD=0.3 owner=arena (FFieldTuning) missing=x"]


class GddKeys(unittest.TestCase):
    def test_same_gap_new_form_is_not_new_but_a_new_key_is(self):
        lane = ["FAIL NOT_IN_GAME P0 CAM-05.h.3 GDD=0.7 owner=level (ChunkLayoutConst) missing=y",
                "FAIL NOT_IN_GAME P0 CAM-05.value GDD=0.3 owner=level (ChunkLayoutConst) missing=x",
                "FAIL NOT_IN_GAME P0 HAZ-03.guard_feet GDD=1450 owner=enemies2 missing=z"]
        self.assertEqual(quality_gate.gdd_keys(lane) - quality_gate.gdd_keys(MAIN), {"GAP HAZ-03.guard_feet"})

    def test_other_fail_forms_still_block(self):
        lane = MAIN + ["FAIL stale CAM-01.w: binding names a value the GDD spec no longer has",
                       "FAIL unbindable FLOW-02.x: needs a reason",
                       "FAIL not_in_game OWL-01.y: needs owner and missing",
                       "FAIL CAM-02.h: game 0.4 != GDD 0.5"]
        new = quality_gate.gdd_keys(lane) - quality_gate.gdd_keys(MAIN)
        self.assertEqual(len(new), 4, new)

    def test_a_cached_full_line_baseline_compares_the_same_way(self):
        cached = set(MAIN)   # what quality-base-<sha>.txt holds for gdd_check
        lane = ["FAIL NOT_IN_GAME P0 CAM-05.h.3 GDD=0.7 owner=level missing=y",
                "FAIL NOT_IN_GAME P0 CAM-05.value GDD=0.3 owner=level missing=x"]
        self.assertEqual(quality_gate.gdd_keys(lane) - quality_gate.gdd_keys(cached), set())


if __name__ == "__main__":
    unittest.main()
