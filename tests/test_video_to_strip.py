"""tools/build/video_to_strip.py: a synthetic chroma-green clip of a bobbing figure becomes keyed, registered frames,
N-frame strips, sidecar and GIF; registration removes the jitter; the loop check is a number; no figure fails."""
import json
import os
import shutil
import subprocess
import sys
import tempfile
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, os.path.join(ROOT, "tools"))
sys.path.insert(0, os.path.join(ROOT, "tools", "build"))
import png  # noqa: E402
import video_to_strip as v  # noqa: E402

W, H, SECS, FPS = 96, 64, 2, 12


def clip(d, jitter=True, figure=True):
    """24 frames: a brown figure (feet at one y) swaying on green; the whole thing shifts by up to 3 px when jitter."""
    for i in range(SECS * FPS):
        rows = [[(0, 255, 0, 255)] * W for _ in range(H)]
        if figure:
            sway = round(4 * __import__("math").sin(2 * 3.14159 * i / (SECS * FPS)))
            jx, jy = ((i * 7) % 4 - 2, (i * 5) % 3 - 1) if jitter else (0, 0)
            for y in range(14, 58):
                for x in range(40, 56):
                    xx = x + jx + (sway if y < 30 else 0)
                    if 0 <= xx < W and 0 <= y + jy < H:
                        rows[y + jy][xx] = (110, 70, 40, 255)
        png.write_png(os.path.join(d, "f_%03d.png" % i), W, H, rows)
    out = os.path.join(d, "clip.mp4")
    subprocess.run(["ffmpeg", "-hide_banner", "-loglevel", "error", "-y", "-framerate", str(FPS), "-i",
                    os.path.join(d, "f_%03d.png"), "-c:v", "libx264", "-qp", "0", "-pix_fmt", "yuv444p", out], check=True)
    return out


class Strip(unittest.TestCase):
    def setUp(self):
        self.d = tempfile.mkdtemp()
        self.addCleanup(shutil.rmtree, self.d, True)

    def test_strips_sidecar_gif_and_jitter_removed(self):
        mp4 = clip(self.d)
        out = os.path.join(self.d, "out")
        r = v.convert(mp4, out, "T", [8, 12], FPS, H)
        self.assertEqual(r["source_frames"], SECS * FPS)
        self.assertGreater(r["jitter_before"]["max_anchor_from_first_px"], 1.0)
        self.assertLessEqual(r["jitter_after"]["max_anchor_from_first_px"], 1.0)
        for n in (8, 12):
            side = json.load(open(os.path.join(out, f"T_N{n}.frames.json")))
            self.assertEqual(side["frames"], n)
            self.assertEqual(side["pivot"], "bottom-centre")
            w, h, _ = png.read_png(os.path.join(out, f"T_N{n}_strip.png"))
            self.assertEqual((w, h), (side["frame"][0] * n, side["frame"][1]))
            self.assertTrue(os.path.getsize(os.path.join(out, f"T_N{n}_preview.gif")) > 0)
            self.assertTrue(r["sets"][str(n)]["loop"]["loops"], r["sets"][str(n)]["loop"])

    def test_keyed_frames_reused_for_other_counts(self):
        mp4 = clip(self.d)
        first = os.path.join(self.d, "first")
        v.convert(mp4, first, "T", [8], FPS, H)
        out = os.path.join(self.d, "again")
        r = v.convert(mp4, out, "T", [24], FPS, H, keyed=os.path.join(first, "keyed"))
        side = json.load(open(os.path.join(out, "T_N24.frames.json")))
        self.assertEqual(side["frames"], 24)
        self.assertFalse(os.path.exists(os.path.join(out, "keyed")))
        self.assertEqual(r["source_frames"], SECS * FPS)

    def test_grid_sheet_cuts_back_to_the_frames(self):
        mp4 = clip(self.d)
        out = os.path.join(self.d, "grid")
        v.convert(mp4, out, "T", [10], FPS, H, cols=4)
        side = json.load(open(os.path.join(out, "T_N10_grid.sprite.json")))
        gw, gh, rows = png.read_png(os.path.join(out, "T_N10_grid.png"))
        fw, fh = side["grid"]
        self.assertEqual((gw, gh), (fw * 4, fh * 3))          # 10 frames, 4 per row -> 3 rows
        f3 = png.read_png(os.path.join(out, "T_N10_03.png"))
        f5 = png.read_png(os.path.join(out, "T_N10_05.png"))
        self.assertEqual(rows[0][3 * fw:4 * fw], f3[2][0])    # cell 3 = row 0, col 3
        self.assertEqual(rows[fh][fw:2 * fw], f5[2][0])       # cell 5 = row 1, col 1
        self.assertEqual(rows[fh * 2][3 * fw:], [(0, 0, 0, 0)] * fw)   # unused cell stays empty

    def test_pick_and_loop_numbers(self):
        self.assertEqual(v.pick(8, 24), [0, 3, 6, 9, 12, 15, 18, 21])
        a = (2, 1, [[(10, 10, 10, 255), (0, 0, 0, 0)]])
        b = (2, 1, [[(20, 10, 10, 255), (0, 0, 0, 0)]])
        self.assertAlmostEqual(v.distance(a, b), 2.5)
        self.assertEqual(v.distance(a, a), 0.0)

    def test_no_figure_fails(self):
        mp4 = clip(self.d, figure=False)
        self.assertEqual(v.main([ "--video", mp4, "--out", os.path.join(self.d, "o"), "--height", str(H)]), 1)


if __name__ == "__main__":
    unittest.main()
