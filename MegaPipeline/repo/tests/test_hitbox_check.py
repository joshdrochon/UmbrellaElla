"""tools/hitbox_check.py: the art aligns to fixed collider data (GDD 1.3 7C). Each check has a passing case and a case
broken on purpose. `fit` moves only the art: the collider file stays byte-identical."""
import contextlib
import hashlib
import io
import json
import os
import shutil
import sys
import tempfile
import unittest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "tools"))
import check_pr  # noqa: E402
import hitbox_check as hb  # noqa: E402
import manifest_check  # noqa: E402
import png  # noqa: E402

INK, CLEAR = (20, 20, 20, 255), (0, 0, 0, 0)


def disc(cx=64, cy=64, r=40):
    return lambda x, y: (x + 0.5 - cx) ** 2 + (y + 0.5 - cy) ** 2 <= r * r


def rect(x0, y0, x1, y1):
    return lambda x, y: x0 <= x < x1 and y0 <= y < y1


def trapezoid(x, y):
    """A dangling clock: a 4 px chain over a trapezoid that widens downward."""
    if 20 <= y < 110:
        return abs(x + 0.5 - 64) <= 10 + 40 * (y - 20) / 90
    return 0 <= y < 20 and 62 <= x < 66


def draw(path, fn, w=128, h=128):
    png.write_png(path, w, h, [[INK if fn(x, y) else CLEAR for x in range(w)] for y in range(h)])


class Base(unittest.TestCase):
    def setUp(self):
        self.root = tempfile.mkdtemp(prefix="hitbox-")
        self.addCleanup(shutil.rmtree, self.root, True)
        os.makedirs(os.path.join(self.root, "Art", "Owl"))
        os.makedirs(os.path.join(self.root, "pipeline", "feel"))
        shutil.copy(os.path.join(ROOT, "pipeline", "feel", "hitboxes.json"), self.data_path)
        with open(os.path.join(self.root, hb.FEEL), "w") as fh:
            json.dump({"forgiveness": {"player_hurtbox_cm": {"w": 48, "h": 72}, "bolt_hitbox_radius_cm": 12}}, fh)

    @property
    def data_path(self):
        return os.path.join(self.root, hb.DATA)

    def data(self):
        with open(self.data_path, encoding="utf-8") as fh:
            return json.load(fh)

    def collider_bytes(self):
        with open(self.data_path, "rb") as fh:
            return fh.read()

    def add(self, **ent):
        d = self.data()
        d["entities"] = [e for e in d["entities"] if e["id"] != ent["id"]] + [ent]
        with open(self.data_path, "w", encoding="utf-8") as fh:
            json.dump(d, fh, indent=2)

    def sprite(self, name, fn, **kw):
        draw(os.path.join(self.root, "Art", "Owl", name), fn, **kw)
        return "Art/Owl/" + name

    def cli(self, *argv):
        with contextlib.redirect_stdout(io.StringIO()) as out:
            rc = hb.main(list(argv) + ["--root", self.root])
        return rc, out.getvalue()

    def bolt(self, art_r=15):
        """A bolt: fixed 12 cm collider at 1 cm/px = r 12 px, art a disc of art_r px."""
        rel = self.sprite("bolt.png", disc(r=art_r))
        self.add(id="bolt", role="hazard", sprite=rel, fixed={"from": "bolt_hitbox_radius_cm", "cm_per_px": 1.0},
                 shape={"type": "circle", "cx": 64, "cy": 64, "r": 12})
        return rel


class Alignment(Base):
    def test_aligned_art_passes_and_misaligned_art_fails(self):
        self.bolt(art_r=15)
        rc, out = self.cli("check")
        self.assertEqual(rc, 1, out)
        self.assertIn("art not aligned yet", out)                 # no alignment record yet
        self.assertEqual(self.cli("fit", "bolt")[0], 0)
        rc, out = self.cli("check")
        self.assertEqual(rc, 0, out)
        self.assertIn("hitbox_check: PASS entities=1", out)
        # broken on purpose: the bolt art is swapped for one drawn off-centre, the collider stays where gameplay put it
        self.sprite("bolt.png", disc(cx=100, r=15))
        rc, out = self.cli("check")
        self.assertEqual(rc, 1, out)
        self.assertIn("art changed since it was aligned", out)
        self.assertIn("FIX: python3 tools/hitbox_check.py fit bolt", out)

    def test_dangling_clock_target_needs_its_shaped_collider(self):
        rel = self.sprite("clock.png", trapezoid)
        poly = {"type": "polygon", "points": [[63, 1], [65, 1], [65, 21], [73, 21], [112, 109], [16, 109], [55, 21],
                                              [63, 21]]}
        self.add(id="owl_clock", role="target", sprite=rel, shape=poly)
        self.assertEqual(self.cli("fit", "owl_clock")[0], 0)
        self.assertEqual(self.cli("check")[0], 0)
        # broken on purpose: a box collider (the bounding box) over a trapezoid reaches empty space
        self.add(id="owl_clock", role="target", sprite=rel, shape={"type": "box", "x": 14, "y": 0, "w": 100, "h": 110})
        rc, out = self.cli("check")
        self.assertEqual(rc, 1, out)
        self.assertIn("spill", out)

    def test_player_hurtbox_must_equal_its_tuning_value(self):
        rel = self.sprite("ella.png", rect(34, 20, 94, 110))
        good = dict(id="ella", role="player", sprite=rel, fixed={"from": "player_hurtbox_cm", "cm_per_px": 1.0},
                    shape={"type": "box", "x": 40, "y": 29, "w": 48, "h": 72})
        self.add(**good)
        self.assertEqual(self.cli("fit", "ella")[0], 0)
        self.assertEqual(self.cli("check")[0], 0)
        for change, why in (({"shape": dict(good["shape"], w=60)}, "not its tuning value"),
                            ({"fixed": None}, "names its tuning value")):
            with self.subTest(why=why):
                self.add(**dict(good, **change))
                rc, out = self.cli("check")
                self.assertEqual(rc, 1, out)
                self.assertIn(why, out)
                self.assertNotIn("FIX:", out)      # collider data is never "fixed" by fit
                before = self.collider_bytes()
                self.assertEqual(self.cli("fit", "ella")[0], 1)
                self.assertEqual(self.collider_bytes(), before)

    def test_circle_capsule_and_worst_frame(self):
        rel = self.sprite("sheet.png", lambda x, y: disc(r=40)(x % 128, y) if x < 128 else disc(r=20)(x % 128, y),
                          w=256)
        d = self.data()
        ent = {"id": "orb", "role": "target", "sprite": rel, "frames": [[0, 0, 128, 128], [128, 0, 128, 128]],
               "shape": {"type": "circle", "cx": 64, "cy": 64, "r": 40}}
        _, fails = hb.frame_reports(d, ent, self.root, 1.0, (0, 0))
        self.assertTrue(any("frame [128, 0, 128, 128]" in f and "spill" in f for f in fails), fails)
        ent["frames"] = [[0, 0, 128, 128]]
        self.assertEqual(hb.frame_reports(d, ent, self.root, 1.0, (0, 0))[1], [])
        ent["shape"] = {"type": "capsule", "cx": 64, "cy": 64, "radius": 40, "half_height": 40}
        self.assertEqual(hb.frame_reports(d, ent, self.root, 1.0, (0, 0))[1], [])
        ent["shape"] = {"type": "capsule", "cx": 94, "cy": 64, "radius": 40, "half_height": 40}   # broken on purpose
        self.assertTrue(hb.frame_reports(d, ent, self.root, 1.0, (0, 0))[1])


class FitMovesOnlyTheArt(Base):
    """Josh's rule plus GDD 1.3 7C: fail -> the lane agent runs fit (visual-only) -> pass. Never a collider write."""

    def test_fail_fit_pass_collider_byte_identical(self):
        self.bolt(art_r=30)                      # the art is far too big for the fixed 12 px bolt collider
        self.assertEqual(self.cli("fit", "bolt")[0], 0)
        self.sprite("bolt.png", disc(cx=90, cy=40, r=30))   # a new, off-centre, oversized bolt drawing
        rc, out = self.cli("check")
        self.assertEqual(rc, 1, out)
        self.assertIn("FIX: python3 tools/hitbox_check.py fit bolt", out)
        self.assertNotIn("NEEDS HUMAN", out)
        before = self.collider_bytes()
        rc, out = self.cli("fit", "bolt")
        self.assertEqual(rc, 0, out)
        self.assertIn("collider unchanged", out)
        self.assertIn("hitbox_check: PASS entities=1", out.strip().splitlines()[-1])
        self.assertEqual(self.collider_bytes(), before, "fit never writes collider data")
        with open(os.path.join(self.root, hb.ALIGN), encoding="utf-8") as fh:
            va = json.load(fh)["entities"]["bolt"]
        self.assertLess(va["scale"], 1.0)        # the art was scaled down to sit on the collider
        self.assertNotEqual(va["offset_px"], [0, 0])

    def test_no_visual_fix_raises_a_human_only_change_request_for_richard(self):
        rel = self.sprite("ella.png", lambda x, y: rect(10, 10, 118, 20)(x, y) or rect(10, 108, 118, 118)(x, y))
        self.add(id="ella", role="player", sprite=rel, fixed={"from": "player_hurtbox_cm", "cm_per_px": 1.0},
                 shape={"type": "box", "x": 40, "y": 28, "w": 48, "h": 72})
        before = self.collider_bytes()
        rc, out = self.cli("fit", "ella")
        self.assertEqual(rc, 3, out)
        line = next(ln for ln in out.splitlines() if ln.startswith("NEEDS HUMAN: Richard hitbox change request"))
        self.assertIn("suggested collider for Richard (not applied)", out)
        self.assertEqual(self.collider_bytes(), before)
        self.assertFalse(os.path.exists(os.path.join(self.root, hb.ALIGN)))
        self.assertIsNotNone(manifest_check.grace_kind(line), "human-only: no grace default")

    def test_suggest_prints_and_writes_nothing(self):
        rel = self.sprite("clock.png", trapezoid)
        before = self.collider_bytes()
        rc, out = self.cli("suggest", rel, "--role", "target")
        self.assertEqual(rc, 0, out)
        self.assertIn('"type": "polygon"', out)
        self.assertIn("not applied", out)
        self.assertEqual(self.collider_bytes(), before)


class ArtSwapAndData(Base):
    def test_lfs_pointer_uses_its_oid_and_fails_in_ci(self):
        rel = self.bolt()
        self.assertEqual(self.cli("fit", "bolt")[0], 0)
        p = os.path.join(self.root, rel)
        with open(p, "rb") as fh:
            real = fh.read()
        with open(p, "w") as fh:
            fh.write(f"version https://git-lfs.github.com/spec/v1\noid sha256:{hashlib.sha256(real).hexdigest()}\n"
                     f"size {len(real)}\n")
        rc, out = self.cli("check")
        self.assertEqual(rc, 0, out)
        self.assertIn("SKIP bolt", out)
        rc, out = self.cli("check", "--fail-lfs-pointer")
        self.assertEqual(rc, 1, out)
        self.assertIn("Git LFS pointer", out)

    def test_sidecar_must_name_a_hitbox(self):
        self.bolt()
        self.assertEqual(self.cli("fit", "bolt")[0], 0)
        side = os.path.join(self.root, "Art", "Owl", "bolt.sprite.json")
        for meta, ok in (({"kind": "silhouette", "hitbox": "bolt"}, True), ({"kind": "fx"}, True),
                         ({"kind": "silhouette", "hitbox": "none", "hitbox_reason": "background owl"}, True),
                         ({"kind": "silhouette"}, False), ({"kind": "silhouette", "hitbox": "none"}, False),
                         ({"kind": "silhouette", "hitbox": "owl_wing"}, False)):
            with self.subTest(meta=meta):
                with open(side, "w") as fh:
                    json.dump(meta, fh)
                self.assertEqual(self.cli("check")[0], 0 if ok else 1)

    def test_bad_entities_fail(self):
        rel = self.sprite("clock.png", trapezoid)
        good = {"id": "c", "role": "target", "sprite": rel, "shape": {"type": "box", "x": 30, "y": 40, "w": 60, "h": 60}}
        d = self.data()
        for change, why in (({"role": "boss"}, "role"), ({"shape": {"type": "star"}}, "shape type"),
                            ({"shape": {"type": "polygon", "points": [[0, 0], [1, 1]]}}, "3 or more"),
                            ({"sprite": "Art/none.png"}, "not found"), ({"spill_max": 0.5}, "override_reason")):
            with self.subTest(why=why):
                fails = hb.check_entity(d, {}, dict(good, **change), self.root)[0]["failures"]
                self.assertTrue(any(why in f for f in fails), fails)
        self.add(**good)
        d = self.data()
        d["entities"].append(good)
        with open(self.data_path, "w") as fh:
            json.dump(d, fh)
        self.assertTrue(any("appears twice" in p for p in hb.run_check(self.root)[2]))

    def test_usage_errors_exit_2(self):
        self.assertEqual(self.cli("fit", "nobody")[0], 2)
        self.assertEqual(self.cli("suggest", "Art/none.png", "--role", "target")[0], 2)
        with open(self.data_path, "w") as fh:
            fh.write("{not json")
        self.assertEqual(self.cli("check")[0], 2)

    def test_repo_data_passes_and_ci_runs_it(self):
        with contextlib.redirect_stdout(io.StringIO()) as out:
            rc = hb.main(["check", "--root", ROOT])
        self.assertEqual(rc, 0, out.getvalue())
        with open(os.path.join(ROOT, ".github", "workflows", "pipeline-checks.yml"), encoding="utf-8") as fh:
            self.assertIn("python3 tools/hitbox_check.py check --fail-lfs-pointer", fh.read())


class PrRule(Base):
    BODY = "## What changed\n{changed}\n## Evidence\n{ev}\n"

    def problems(self, changed, ev):
        s = check_pr.sections(self.BODY.format(changed=changed, ev=ev))
        return check_pr.hitbox_problems(s, [changed], self.root)

    def test_collider_alignment_or_art_change_needs_the_pass_line(self):
        rel = self.bolt()
        ok = "hitbox_check: PASS entities=1 skipped=0"
        for changed in ("pipeline/feel/hitboxes.json", "pipeline/art/visual-align.json", rel):
            with self.subTest(changed=changed):
                self.assertEqual(self.problems(changed, ok), [])
                self.assertTrue(self.problems(changed, "build exit: 0"))     # broken on purpose: no check pasted
                self.assertTrue(self.problems(changed, "hitbox_check: FAIL 1 problem(s)\n" + ok))
        self.assertEqual(self.problems("Art/Other/tree.png", "build exit: 0"), [])


if __name__ == "__main__":
    unittest.main()
