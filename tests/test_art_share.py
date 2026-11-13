"""Shared-layer judging (tools/art_share.py, art_loop.shared_layer, art_pass_verify.base_link_problems).

Broken on purpose: an off-model repaint fails the consistency check, a reuse piece whose base region was altered fails
the pixel check, a derived piece without a verified base never counts."""
import json
import os
import shutil
import sys
import tempfile
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, os.path.join(ROOT, "tools"))
sys.path.insert(0, os.path.join(ROOT, "tools", "build"))
sys.path.insert(0, HERE)
import art_loop  # noqa: E402
import art_pass_verify  # noqa: E402
import art_share  # noqa: E402
from png import write_png  # noqa: E402


def figure(path, x0=14, x1=34, y0=6, y1=42, ink=(30, 26, 24), size=(48, 48)):
    """A dark inked silhouette on transparent, with line work inside (not a flat fill)."""
    w, h = size
    rows = []
    for y in range(h):
        row = []
        for x in range(w):
            if x0 <= x < x1 and y0 <= y < y1:
                k = 36 if (x // 2 + y // 3) % 2 else 0
                row.append((ink[0] + k, ink[1] + k, ink[2] + k, 255))
            else:
                row.append((0, 0, 0, 0))
        rows.append(row)
    write_png(path, w, h, rows)


def refs_for(base="base-fig", derived="derived-fig", mode="repaint", extra=None):
    refs = {"references": [
        {"id": "r1", "kind": "image", "path": "ref1.png"},
        {"id": "r2", "kind": "image", "path": "ref2.png"},
        {"id": "r3", "kind": "image", "path": "ref3.png"}],
        "elements": {
            base: {"what": "a figure", "refs": ["r1", "r2", "r3"]},
            derived: {"what": "the figure in a new pose", "refs": ["r1"], "base": base, "base_mode": mode,
                      "new": "the raised arm and the open umbrella"}}}
    refs["elements"][derived].update(extra or {})
    return refs


class Repaint(unittest.TestCase):
    def setUp(self):
        self.d = tempfile.mkdtemp()
        self.addCleanup(shutil.rmtree, self.d, True)
        figure(self.p("ref1.png"))
        figure(self.p("ref2.png"), 13, 34, 6, 42)
        figure(self.p("ref3.png"), 14, 35, 5, 42)
        figure(self.p("base.png"))

    def p(self, name):
        return os.path.join(self.d, name)

    def assess(self, derived, refs=None):
        return art_share.assess(refs or refs_for(), "derived-fig", self.p(derived), self.p("base.png"), [self.d])

    def test_the_floor_comes_from_the_base_known_good_refs(self):
        floor = art_share.known_good_floor(refs_for(), "base-fig", [self.d])
        self.assertGreater(floor, 0.5)
        self.assertLess(floor, 1.0)

    def test_an_on_model_derivative_passes_and_names_the_new_layer(self):
        figure(self.p("good.png"), 15, 34, 6, 41)
        got = self.assess("good.png")
        self.assertTrue(got["ok"], got)
        self.assertEqual(got["brief"], "the raised arm and the open umbrella")

    def test_a_deliberately_off_model_derivative_fails_the_consistency_check(self):
        figure(self.p("off.png"), 2, 46, 20, 28, ink=(40, 200, 60))   # wide, bright green, wrong shape
        got = self.assess("off.png")
        self.assertFalse(got["ok"], got)
        self.assertIsNone(got["brief"])   # no shortcut: the full panel

    def test_no_base_image_gives_no_shortcut(self):
        figure(self.p("good.png"))
        self.assertFalse(art_share.assess(refs_for(), "derived-fig", self.p("good.png"), None, [self.d])["ok"])

    def test_a_piece_without_a_base_is_not_a_shared_layer(self):
        self.assertIsNone(art_share.assess(refs_for(), "base-fig", self.p("base.png"), None, [self.d]))

    def test_the_brief_passes_the_critic_leak_check(self):
        what = art_share.brief_what("the figure in a new pose", "the raised arm and the open umbrella")
        self.assertEqual(art_loop.critic_prompt_problems(art_loop.critic_prompt(what)), [])


class Reuse(unittest.TestCase):
    def setUp(self):
        self.d = tempfile.mkdtemp()
        self.addCleanup(shutil.rmtree, self.d, True)
        figure(os.path.join(self.d, "base.png"))
        # the derived piece: the base's pixels at (8, 8) in a bigger canvas, plus an added layer
        from png import read_png
        w, h, rows = read_png(os.path.join(self.d, "base.png"))
        self.rows = [[(0, 0, 0, 0)] * 64 for _ in range(64)]
        for y in range(h):
            for x in range(w):
                self.rows[y + 8][x + 8] = rows[y][x]
        self.base = os.path.join(self.d, "base.png")

    def derived(self, name, rows):
        p = os.path.join(self.d, name)
        write_png(p, 64, 64, rows)
        return p

    def test_the_base_pixels_inside_the_derived_piece_pass_and_the_panel_judges_the_layer(self):
        rows = [r[:] for r in self.rows]
        for x in range(2, 10):
            rows[2][x] = (200, 160, 40, 255)   # the added layer, outside the base region
        p = self.derived("ok.png", rows)
        ok, share = art_share.reuse_check(self.base, p, (8, 8))
        self.assertTrue(ok)
        self.assertEqual(share, 1.0)
        refs = refs_for(mode="reuse", extra={"base_region": [8, 8]})
        got = art_share.assess(refs, "derived-fig", p, self.base, [self.d])
        self.assertTrue(got["ok"])
        self.assertEqual(got["brief"], "the raised arm and the open umbrella")

    def test_a_reuse_piece_whose_base_region_was_altered_fails_the_pixel_check(self):
        rows = [r[:] for r in self.rows]
        for y in range(14, 26):
            for x in range(14, 34):
                rows[y][x] = (230, 40, 40, 255)   # repainted inside the base region
        p = self.derived("altered.png", rows)
        ok, share = art_share.reuse_check(self.base, p, (8, 8))
        self.assertFalse(ok)
        self.assertLess(share, art_share.REUSE_SHARE)
        refs = refs_for(mode="reuse", extra={"base_region": [8, 8]})
        got = art_share.assess(refs, "derived-fig", p, self.base, [self.d])
        self.assertFalse(got["ok"])
        self.assertIsNone(got["brief"])

    def test_the_wrong_place_or_a_canvas_too_small_is_not_a_reuse(self):
        p = self.derived("ok.png", self.rows)
        self.assertFalse(art_share.reuse_check(self.base, p, (0, 0))[0])
        self.assertFalse(art_share.reuse_check(self.base, p, (30, 30))[0])


class BaseLink(unittest.TestCase):
    """base_link_problems: a derived pass counts only with a verified base; a reuse is re-measured on shipped pixels."""
    def test_a_derived_piece_without_a_verified_base_never_counts(self):
        root = tempfile.mkdtemp()
        self.addCleanup(shutil.rmtree, root, True)
        os.makedirs(os.path.join(root, "pipeline", "art"))
        refs = refs_for()
        refs.update({"roles": {}, "scene": {"what": "s", "refs": []}})
        with open(os.path.join(root, "pipeline", "art", "references.json"), "w") as fh:
            json.dump(refs, fh)
        verified = {"derived-fig"}   # the derived piece passed, its base did not
        orig = art_pass_verify.verified_pieces
        art_pass_verify.verified_pieces = lambda r, *a, **k: verified
        self.addCleanup(setattr, art_pass_verify, "verified_pieces", orig)
        lines = art_pass_verify.base_link_problems(root)
        self.assertEqual(len(lines), 1, lines)
        self.assertIn("no verified pass", lines[0])

    def test_a_reuse_pass_whose_shipped_pixels_were_altered_fails_the_verify(self):
        root = tempfile.mkdtemp()
        self.addCleanup(shutil.rmtree, root, True)
        os.makedirs(os.path.join(root, "pipeline", "art"))
        figure(os.path.join(root, "base.png"))
        figure(os.path.join(root, "derived.png"), 14, 34, 6, 42, ink=(200, 40, 40))   # not the base's pixels
        refs = refs_for(mode="reuse")
        refs.update({"roles": {}, "scene": {"what": "s", "refs": []}})
        with open(os.path.join(root, "pipeline", "art", "references.json"), "w") as fh:
            json.dump(refs, fh)
        files = {"base-fig": {"file": "base.png"}, "derived-fig": {"file": "derived.png"}}
        patches = [(art_pass_verify, "verified_pieces", lambda r, *a, **k: set(files)),
                   (art_loop, "newest_record", lambda r, piece: files[piece])]
        for obj, name, fn in patches:
            old = getattr(obj, name)
            setattr(obj, name, fn)
            self.addCleanup(setattr, obj, name, old)
        lines = art_pass_verify.base_link_problems(root)
        self.assertEqual(len(lines), 1, lines)
        self.assertIn("claims to reuse", lines[0])


if __name__ == "__main__":
    unittest.main()
