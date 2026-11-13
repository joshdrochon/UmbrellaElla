"""Frame registration and jitter (tools/frame_register.py, assetgen frames, sprite_check, art_loop): a deliberately
shaken strip fails, the same strip after registration passes, the reference animations pass."""
import json
import os
import random
import sys
import tempfile
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, os.path.join(ROOT, "tools"))
import art_loop  # noqa: E402
import assetgen  # noqa: E402
import frame_register as fr  # noqa: E402
import png  # noqa: E402
import sprite_check  # noqa: E402

W, H = 160, 200
INK = (30, 25, 35, 255)
REF = os.path.join(ROOT, "pipeline", "art", "reference", "Test_Assets")


def figure(arm=0):
    """A dark standing figure: skirt (wide base), body, head, and an arm that moves with `arm` (a pose change)."""
    rows = [[(0, 0, 0, 0)] * W for _ in range(H)]

    def box(x0, y0, x1, y1):
        for y in range(y0, y1 + 1):
            for x in range(x0, x1 + 1):
                rows[y][x] = INK
    box(50, 130, 110, 170)       # skirt: bottom 40 rows, 61 wide
    box(65, 70, 95, 129)         # body
    box(70, 45, 90, 69)          # head
    box(95, 80 - arm, 130, 88 - arm)   # arm
    return (W, H, rows)


def pose_strip(n=6):
    return [figure(arm=4 * (i % 3)) for i in range(n)]


def shake(frames, seed=7):
    rnd = random.Random(seed)
    out = []
    for i, (w, h, rows) in enumerate(frames):
        a = fr.anchor(rows)
        dx, dy = (rnd.choice((-1, 1)) * rnd.randint(3, 6) for _ in range(2))
        s = 1 + 0.05 * (1 if i % 2 else -1)
        out.append((w, h, fr._transform(w, h, rows, round(a[0]), a[1], round(a[0]) + dx, a[1] + dy, s, fr.CLEAR)))
    return out


class Registration(unittest.TestCase):
    def test_clean_strip_has_no_jitter(self):
        j = fr.jitter(pose_strip())
        self.assertEqual((j["offset_px"], j["scale_pct"]), (0, 0))

    def test_shaken_strip_fails_the_limits(self):
        j = fr.jitter(shake(pose_strip()))
        self.assertGreater(j["offset_px"], fr.JITTER_LIMITS["offset_px"])
        self.assertGreater(j["scale_pct"], fr.JITTER_LIMITS["scale_pct"])

    def test_registered_strip_passes(self):
        out, info = fr.register(shake(pose_strip()))
        j = fr.jitter(out)
        self.assertLessEqual(j["offset_px"], fr.JITTER_LIMITS["offset_px"])
        self.assertLessEqual(j["scale_pct"], fr.JITTER_LIMITS["scale_pct"])
        for _, _, r in out:   # every anchor on the target pixel (a half pixel of mask-edge rounding at most)
            a = fr.anchor(r)
            self.assertLessEqual(max(abs(a[0] - info["anchor"][0]), abs(a[1] - info["anchor"][1])), 1.0)

    def test_pose_change_is_not_flattened(self):
        # the arm moves up and the figure is taller in some frames; registration must not rescale a pose to match
        out, info = fr.register(pose_strip())
        self.assertTrue(all(f["scale"] == 1.0 for f in info["frames"]))
        self.assertEqual([fr.mask_box(r)[1] for _, _, r in out], [fr.mask_box(r)[1] for _, _, r in pose_strip()])

    def test_empty_strip_is_refused(self):
        with self.assertRaises(ValueError):
            fr.register([(4, 4, [[(0, 0, 0, 0)] * 4 for _ in range(4)])])


class Cutter(unittest.TestCase):
    def strip(self, d, frames):
        """A keyed strip PNG: the frames side by side with a gap, as the image model paints them."""
        rows = [sum((f[2][y] for f in frames), []) for y in range(H)]
        p = os.path.join(d, "strip.png")
        png.write_png(p, W * len(frames), H, rows)
        return p

    def test_frames_cut_is_registered_and_writes_the_anchor(self):
        with tempfile.TemporaryDirectory() as d:
            src = self.strip(d, shake(pose_strip(4)))
            raw, st0 = assetgen.split_strip(src, 4, cells=True, register=False)
            frames, st = assetgen.split_strip(src, 4, cells=True)
            # the bounding-box cut already seats the feet; the wobble left in the raw cut is scale
            self.assertGreater(fr.jitter(raw)["scale_pct"], fr.JITTER_LIMITS["scale_pct"])
            self.assertLessEqual(st["jitter"]["offset_px"], fr.JITTER_LIMITS["offset_px"])
            self.assertLessEqual(st["jitter"]["scale_pct"], fr.JITTER_LIMITS["scale_pct"])
            self.assertEqual(len(st["anchor"]), 2)
            self.assertNotIn("anchor", st0)

    def test_sheet_sidecar_carries_the_anchor(self):
        with tempfile.TemporaryDirectory() as d:
            src = self.strip(d, shake(pose_strip(4)))
            frames, st = assetgen.split_strip(src, 4, cells=True)
            outs = []
            for i, (w, h, rows) in enumerate(frames):
                outs.append(os.path.join(d, f"s_{i:02d}.png"))
                png.write_png(outs[-1], w, h, rows)
            with open(os.path.join(d, "s.frames.json"), "w") as fh:
                json.dump(dict(st), fh)
            out = os.path.join(d, "sheet.png")
            ns = type("A", (), {"frames": outs, "out": out, "anim": "Idle", "fps": 8, "kind": "silhouette"})
            old = assetgen.write_provenance
            assetgen.write_provenance = lambda *a, **k: None
            try:
                assetgen.cmd_sheet(ns, [], d)
            finally:
                assetgen.write_provenance = old
            with open(os.path.join(d, "sheet.sprite.json")) as fh:
                side = json.load(fh)
            self.assertEqual(side["anchor"], st["anchor"])


class Checks(unittest.TestCase):
    def sheet(self, d, frames, loop=True):
        rows = [sum((f[2][y] for f in frames), []) for y in range(H)]
        p = os.path.join(d, "sheet.png")
        png.write_png(p, W * len(frames), H, rows)
        with open(os.path.join(d, "sheet.sprite.json"), "w") as fh:
            json.dump({"grid": [W, H], "size": [W, H], "frames": len(frames), "loop": loop, "anim": "Idle"}, fh)
        return p

    def test_art_loop_check_fails_shaken_passes_registered(self):
        with tempfile.TemporaryDirectory() as d:
            bad = art_loop.jitter_problems(self.sheet(d, shake(pose_strip())))
            self.assertTrue(any("anchor moves" in b for b in bad) and any("scale drifts" in b for b in bad), bad)
        with tempfile.TemporaryDirectory() as d:
            good = art_loop.jitter_problems(self.sheet(d, fr.register(shake(pose_strip()))[0]))
            self.assertEqual(good, [])

    def test_sprite_check_reports_jitter(self):
        with open(os.path.join(ROOT, "pipeline", "art", "style.json")) as fh:
            style = json.load(fh)
        with tempfile.TemporaryDirectory() as d:
            p = self.sheet(d, shake(pose_strip()))
            rep = sprite_check.check([p], style, grid=(W, H), loop=True)
            self.assertTrue(any(f.startswith("jitter:") for f in rep["failures"]), rep["failures"])
        with tempfile.TemporaryDirectory() as d:
            p = self.sheet(d, fr.register(shake(pose_strip()))[0])
            rep = sprite_check.check([p], style, grid=(W, H), loop=True)
            self.assertFalse([f for f in rep["failures"] if f.startswith("jitter:")], rep["failures"])
            self.assertIn("jitter", rep)


@unittest.skipUnless(os.path.isfile(os.path.join(REF, "CHR_Witch_Cast.png")), "reference sheets not in this checkout")
class ReferenceSheets(unittest.TestCase):
    """The limits come from these hand-made animations (see frame_register.JITTER_LIMITS): they must pass."""

    def test_reference_loops_pass(self):
        for name, grid, row in (("CHR_Witch_Cast.png", (432, 352), 0), ("CHR_Witch_Cast.png", (432, 352), 1),
                                ("CHR_Owl_Flap_Damage.png", (640, 512), 0)):
            with self.subTest(name=name, row=row):
                frames = fr.sheet_frames(os.path.join(REF, name), grid, 6, row)
                j = fr.jitter(frames, loop=True)
                self.assertLessEqual(j["offset_px"], fr.JITTER_LIMITS["offset_px"])
                self.assertLessEqual(j["scale_pct"], fr.JITTER_LIMITS["scale_pct"])

    def test_reference_with_added_shake_fails(self):
        frames = fr.sheet_frames(os.path.join(REF, "CHR_Witch_Cast.png"), (432, 352), 6, 0)
        j = fr.jitter(shake(frames))
        self.assertGreater(j["offset_px"], fr.JITTER_LIMITS["offset_px"])


if __name__ == "__main__":
    unittest.main()
