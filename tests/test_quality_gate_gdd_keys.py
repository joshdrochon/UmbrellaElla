"""quality_gate compares gdd_check fails by GDD key, so a gap that only changes form (broken binding -> not_in_game,
new owner text) is not a new fail, while a new key is (Nov 13)."""
import os, sys, unittest
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "tools", "build"))
import quality_gate  # noqa: E402


class GddKeys(unittest.TestCase):
    def test_same_gap_new_form_is_not_new_but_a_new_key_is(self):
        main = quality_gate.gdd_keys(["FAIL broken CAM-05.h.3: Source/x.h:HighFraction not found in the source",
                                      "FAIL NOT_IN_GAME P0 CAM-05.value GDD=0.3 owner=arena (FFieldTuning) missing=x"])
        lane = quality_gate.gdd_keys(["FAIL NOT_IN_GAME P0 CAM-05.h.3 GDD=0.7 owner=level (ChunkLayoutConst) missing=y",
                                      "FAIL NOT_IN_GAME P0 CAM-05.value GDD=0.3 owner=level (ChunkLayoutConst) missing=x",
                                      "FAIL NOT_IN_GAME P0 HAZ-03.guard_feet GDD=1450 owner=enemies2 missing=z"])
        self.assertEqual(lane - main, {"FAIL HAZ-03.guard_feet"})


if __name__ == "__main__":
    unittest.main()
