"""tools/art_judge.py: the automatic art judge against the team's reference images (pipeline/art/references.json).

The key art itself must PASS the scene judge; the teammate's first-build look (flat teal wind box, small owl, grey boxes,
no skyline, ~1.85:1) and the key art with its owl painted out must FAIL. Element judging picks the candidate that
matches its references and refuses one that does not. Coverage fails when any reference image has no judge or no card."""
import copy
import io
import json
import math
import os
import random
import sys
import tempfile
import unittest
from contextlib import redirect_stdout

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, os.path.join(ROOT, "tools"))
sys.path.insert(0, HERE)
import hermetic  # noqa: E402
import art_judge  # noqa: E402
from png import read_png, write_png  # noqa: E402

KEYART = os.path.join(ROOT, "pipeline", "art", "reference", "target-keyart.png")


def have_keyart():
    with open(KEYART, "rb") as fh:
        return fh.read(8) == b"\x89PNG\r\n\x1a\n"


def run(*args):
    out = io.StringIO()
    with redirect_stdout(out):
        rc = art_judge.main(list(args))
    return rc, out.getvalue()


class SceneJudge(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.tmp = tempfile.mkdtemp()

    @unittest.skipUnless(have_keyart(), "key art is an LFS pointer here")
    def test_key_art_passes(self):
        rc, out = run("scene", KEYART)
        self.assertEqual(rc, 0, out)
        self.assertIn("art_judge: scene PASS score=1.0", out)

    def test_teammate_first_build_look_fails(self):
        """Broken on purpose: the first teammate build (older pipeline): flat teal wind box, small owl, grey hitbox
        boxes, a flat floor instead of the skyline, a ~1.85:1 frame."""
        w, h = 370, 200
        rnd = random.Random(2)
        rows = [[(147 + rnd.randint(-8, 8), 120 + rnd.randint(-8, 8), 107 + rnd.randint(-8, 8), 255) for _ in range(w)]
                for _ in range(h)]
        for y in range(185, h):
            for x in range(w):
                rows[y][x] = (110, 110, 110, 255)                     # flat floor
        for y in range(40, 170):
            for x in range(150, 220):
                rows[y][x] = (42, 157, 143, 255)                      # flat teal wind box
        cx, cy, r = 320, 60, 20                                       # small owl
        for y in range(h):
            for x in range(w):
                if (x - cx) ** 2 + (y - cy) ** 2 < r * r:
                    rows[y][x] = (40, 30, 25, 255)
        for y in range(82, 92):
            for x in range(305, 335):
                rows[y][x] = (128, 128, 128, 255)                     # grey hitbox box under the owl
        p = os.path.join(self.tmp, "teammate.png")
        write_png(p, w, h, rows)
        rc, out = run("scene", p)
        self.assertEqual(rc, 1, out)
        for want in ("skyline:", "owl h=", "FIX: owl:"):
            self.assertIn(want, out)

    @unittest.skipUnless(have_keyart(), "key art is an LFS pointer here")
    def test_key_art_with_the_owl_painted_out_fails(self):
        w, h, rows = read_png(KEYART)
        rnd = random.Random(3)
        for y in range(0, int(h * 0.86)):
            for x in range(int(w * 0.34), w):
                rows[y][x] = (147 + rnd.randint(-9, 9), 120 + rnd.randint(-9, 9), 107 + rnd.randint(-9, 9), 255)
        p = os.path.join(self.tmp, "no_owl.png")
        write_png(p, w, h, rows)
        rc, out = run("scene", p)
        self.assertEqual(rc, 1, out)
        self.assertIn("owl", out)
        self.assertIn("clock", out)


def cross(size, col, bg=None):
    """An etched rust cross: the colour varies stroke by stroke (art is never a flat fill)."""
    rows = [[bg or (0, 0, 0, 0)] * size for _ in range(size)]
    c, t = size // 2, max(2, size // 8)
    rn = random.Random(size)
    for y in range(size):
        for x in range(size):
            if abs(x - c) < t or abs(y - c) < t:
                if math.hypot(x - c, y - c) < size * 0.45:
                    k = rn.randint(-30, 30)
                    rows[y][x] = (max(0, min(255, col[0] + k)), max(0, min(255, col[1] + k // 2)),
                                  max(0, min(255, col[2] + k // 3)), 255)
    return rows


class ElementJudge(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.mkdtemp()
        os.makedirs(os.path.join(self.tmp, "refs"))
        write_png(os.path.join(self.tmp, "refs", "bolt.png"), 64, 64, cross(64, (150, 50, 35, 255)))
        refs = {"references": [{"id": "bolt", "path": "refs/bolt.png", "kind": "image", "role": ["effects"],
                                "cards": ["MVP 7"], "judge": True, "required": True}],
                "elements": {"owl-bolt": {"refs": ["bolt"], "score_min": 0.5}},
                "scene": copy.deepcopy(art_judge.load_refs()["scene"])}
        refs["scene"]["refs"] = ["bolt"]
        self.refs = os.path.join(self.tmp, "references.json")
        with open(self.refs, "w") as fh:
            json.dump(refs, fh)
        self.good = os.path.join(self.tmp, "cand_cross.png")
        write_png(self.good, 48, 48, cross(48, (140, 45, 30, 255)))
        self.bad = os.path.join(self.tmp, "cand_square.png")
        write_png(self.bad, 48, 48, [[(42, 157, 143, 255)] * 48 for _ in range(48)])   # flat teal placeholder

    def test_pick_takes_the_matching_candidate(self):
        rc, out = run("--refs", self.refs, "--refs-root", self.tmp, "element", "owl-bolt", self.bad, self.good, "--pick")
        self.assertEqual(rc, 0, out)
        self.assertIn("art_judge: PICK cand_cross.png", out)
        self.assertIn("FAIL", out.split("cand_square.png")[0].splitlines()[-1])

    def test_no_passing_candidate_means_regenerate(self):
        rc, out = run("--refs", self.refs, "--refs-root", self.tmp, "element", "owl-bolt", self.bad, "--pick")
        self.assertEqual(rc, 1, out)
        self.assertIn("art_judge: NONE passed for owl-bolt: regenerate with tools/assetgen.py", out)

    def test_missing_references_fail_closed(self):
        rc, out = run("--refs", self.refs, "--refs-root", os.path.join(self.tmp, "nowhere"), "element", "owl-bolt",
                      self.good)
        self.assertEqual(rc, 1, out)
        self.assertIn("none of its references were found", out)


class Coverage(unittest.TestCase):
    @unittest.skipIf(hermetic.refs_left_out(), hermetic.LEFT_OUT)
    def test_every_reference_image_has_a_judge_and_a_card(self):
        refs = art_judge.load_refs()
        self.assertEqual(art_judge.coverage(refs), [])
        images = [r for r in refs["references"] if r["kind"] == "image" and "team art" not in r["role"]]
        self.assertEqual(len(images), 41)   # 21 refs, Ricky's 13 posts, 2 quality bars, title DM, 4 key-art crops
        team = [r for r in refs["references"] if "team art" in r["role"]]   # the studies this checkout has, plus any
        self.assertTrue(all(os.path.isfile(os.path.join(ROOT, r["path"])) for r in team))   # image team_art joined
        self.assertEqual({r["id"] for r in images if r.get("tier") == "top"}, {"bar-casters", "bar-other-realm"})
        rc, out = run("coverage")
        self.assertEqual(rc, 0, out)

    def test_one_schema_for_every_entry(self):
        refs = art_judge.load_refs()
        self.assertEqual(art_judge.schema_problems(refs), [])
        # broken on purpose: a string role, a role outside the vocabulary, no judge flag, a duplicate id, a bad kind,
        # judge true on a judge_exempt entry
        for change, want in [(lambda r: r.__setitem__("role", "owl"), "role must be a non-empty list"),
                             (lambda r: r.__setitem__("role", ["teapot"]), "not in roles"),
                             (lambda r: r.pop("judge"), "no judge true/false"),
                             (lambda r: r.pop("required"), "no required true/false"),
                             (lambda r: r.__setitem__("kind", "video"), "not one of image, data, described"),
                             (lambda r: r.__setitem__("judge_exempt", "x"), "judge_exempt but judge is true")]:
            broken = copy.deepcopy(refs)
            change(broken["references"][0])
            with self.subTest(want=want):
                self.assertTrue(any(want in p for p in art_judge.coverage(broken)), art_judge.coverage(broken))
        broken = copy.deepcopy(refs)
        broken["references"].append(copy.deepcopy(broken["references"][0]))
        self.assertTrue(any("listed twice" in p for p in art_judge.schema_problems(broken)))

    def test_a_quality_bar_image_outside_quality_bar_fails(self):
        refs = copy.deepcopy(art_judge.load_refs())
        refs["quality_bar"]["refs"] = ["bar-casters"]
        self.assertTrue(any("bar-other-realm" in p for p in art_judge.coverage(refs)))

    @unittest.skipIf(hermetic.refs_left_out(), hermetic.LEFT_OUT)
    def test_every_discord_post_is_a_reference(self):
        with open(os.path.join(ROOT, "pipeline", "art", "reference", "discord", "index.json")) as fh:
            idx = json.load(fh)
        paths = {r["path"] for r in art_judge.load_refs()["references"]}
        for x in idx["images"]:
            want = "pipeline/art/reference/discord/" + x["file"]
            with self.subTest(file=x["file"]):
                if x.get("duplicate_of"):
                    self.assertNotIn(want, paths)
                else:
                    self.assertIn(want, paths)
                    self.assertTrue(os.path.isfile(os.path.join(ROOT, want)))

    def test_an_unassigned_reference_fails(self):
        refs = art_judge.load_refs()
        broken = copy.deepcopy(refs)
        broken["references"].append({"id": "orphan", "path": "Test_Assets/New.png", "kind": "image", "role": ["owl"],
                                     "cards": [], "judge": True, "required": True})
        probs = art_judge.coverage(broken)
        self.assertIn("reference orphan (Test_Assets/New.png) is used by no judge element (or judge_exempt with a "
                      "reason)", probs)
        self.assertIn("reference orphan (Test_Assets/New.png) is assigned to no card", probs)
        broken = copy.deepcopy(refs)
        broken["references"][0]["cards"] = ["0.99"]
        self.assertTrue(any("not a Day-0 card" in p for p in art_judge.coverage(broken)))


if __name__ == "__main__":
    unittest.main()
