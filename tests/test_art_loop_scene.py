"""Scene work is judged as a whole frame against the north star by visual_qa.py, not by art_check.py
(D-new-north-star-frame, Josh Nov 13): art_check's key-art limits fail the Other Realm study itself."""
import os
import sys
import unittest

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, os.path.join(ROOT, "tools"))
sys.path.insert(0, os.path.join(ROOT, "tools", "build"))
import art_loop  # noqa: E402
import visual_qa  # noqa: E402


class SceneIsJudgedAsAFrame(unittest.TestCase):
    def test_scene_pieces_are_recognised(self):
        for p in ("scene", "bg", "bg-layer:land", "bg:atmosphere", "world-island-a", "scene:gameplay-frame"):
            self.assertTrue(art_loop.is_scene_piece(p), p)
        for p in ("ella-idle", "keeper-talon", "ui-defeated", "background-ui", "enemy-courier"):
            self.assertFalse(art_loop.is_scene_piece(p), p)

    def test_study_passes_the_scene_path(self):
        os.environ["VISUAL_QA_REPLAY_ONLY"] = "1"   # the recorded calibration judgement; no spend
        try:
            ok, line = art_loop.frame_judge(os.path.join(ROOT, visual_qa.KNOWN_GOOD), screen="known-good")
        finally:
            os.environ.pop("VISUAL_QA_REPLAY_ONLY", None)
        self.assertTrue(ok, line)

    def test_josh_broken_frame_fails_the_scene_path(self):
        os.environ["VISUAL_QA_REPLAY_ONLY"] = "1"
        try:
            ok, line = art_loop.frame_judge(os.path.join(ROOT, visual_qa.KNOWN_BAD), screen="known-bad")
        finally:
            os.environ.pop("VISUAL_QA_REPLAY_ONLY", None)
        self.assertFalse(ok, line)


if __name__ == "__main__":
    unittest.main()
