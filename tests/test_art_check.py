"""Tests for tools/art_check.py and tools/png.py. Synthetic screenshots are built in a
temp folder: one on-style frame that must pass, and off-style frames that must fail.
If someone loosens a threshold until bad art passes, these tests fail."""
import json
import os
import random
import sys
import tempfile
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, os.path.join(ROOT, "tools"))
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import hermetic  # noqa: E402
import art_check  # noqa: E402
from png import read_png, write_png  # noqa: E402

W, H = 160, 90
STYLE = json.load(open(os.path.join(ROOT, "pipeline", "art", "style.json")))


def hexrgb(h):
    return art_check.hex_to_rgb(h) + (255,)


# Colors come from style.json by name, so measuring the real palette updates the fixtures too.
_PAL = {c["name"]: c["hex"] for c in STYLE["palette"]}
PAPER = hexrgb(_PAL["paper-mid"])
PAPER_L = hexrgb(_PAL["paper-light"])
PAPER_S = hexrgb(_PAL["paper-stain"])
INK = hexrgb(_PAL["silhouette"])
OWL = hexrgb(_PAL["owl-umber"])
GOLD = hexrgb(_PAL["gold"])
RUST = hexrgb(_PAL["rust-red"])


def frame(paint):
    rows = [[PAPER for _ in range(W)] for _ in range(H)]
    paint(rows)
    return rows


def other(rows):
    """The same frame with one pixel changed: another file, so load_spec does not drop it as a byte copy."""
    rows[0][0] = PAPER_L if rows[0][0] != PAPER_L else PAPER
    return rows


def on_style(rows):
    rnd = random.Random(1)
    for y in range(H):
        for x in range(W):
            g = rnd.random()   # paper grain in three paper tones (the key art measures 0.77 paper texture)
            if g < 0.34:
                rows[y][x] = PAPER_L
            elif g < 0.67:
                rows[y][x] = PAPER_S
    for y in range(int(H * 0.8), H):  # black rock silhouette band
        for x in range(W):
            rows[y][x] = INK
    for y in range(10, 60):  # owl body
        for x in range(100, 150):
            rows[y][x] = OWL
    for x in range(20, 90, 6):  # a few gold shots
        rows[40][x] = GOLD
        rows[41][x] = GOLD
    for x in (60, 70, 80):  # rust projectiles
        rows[30][x] = RUST


def rainbow(rows):
    on_style(rows)
    for y in range(H):
        for x in range(W):
            if (x // 8) % 2 == 0:
                rows[y][x] = [(255, 40, 40, 255), (40, 200, 60, 255), (40, 90, 255, 255), (255, 0, 200, 255)][(x // 16) % 4]


def gold_flood(rows):
    on_style(rows)
    for y in range(0, 40):
        for x in range(W):
            rows[y][x] = GOLD


def teal_accents(rows):
    # Muted teal shots instead of gold: low enough saturation to slip past off_style,
    # but the hue is outside the gold/rust bands.
    on_style(rows)
    teal = (70, 120, 115, 255)
    for y in range(20, 32):
        for x in range(10, 60):
            rows[y][x] = teal


def flat_graybox(rows):
    # Red-team round 2, finding 14: gray 128 background, dark ledges, a white Ella. Every color gate
    # passes this frame (gray 128 sits within tolerance of paper-mid); only paper_texture catches it.
    for y in range(H):
        for x in range(W):
            rows[y][x] = (128, 128, 128, 255)
    for y in range(int(H * 0.85), H):
        for x in range(W):
            rows[y][x] = (40, 40, 40, 255)
    for y, x0, x1 in ((30, 10, 60), (55, 90, 150)):
        for yy in range(y, y + 3):
            for x in range(x0, x1):
                rows[yy][x] = (40, 40, 40, 255)
    for y in range(60, 66):
        for x in range(40, 44):
            rows[y][x] = (230, 230, 230, 255)


def near_uniform(rows):
    # on-style colors and silhouettes, but the paper is one flat value with a 1 L* wobble
    on_style(rows)
    for y in range(int(H * 0.8)):
        for x in range(W):
            if rows[y][x] in (PAPER, PAPER_L):
                rows[y][x] = PAPER if (x + y) % 2 else tuple(min(255, c + 1) for c in PAPER[:3]) + (255,)


def no_silhouettes(rows):
    pass  # flat paper, nothing dark


class ArtCheckTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.mkdtemp()

    def run_on(self, painter, name):
        p = os.path.join(self.tmp, name + ".png")
        write_png(p, W, H, frame(painter))
        m = art_check.measure(p, STYLE)
        return m, art_check.evaluate(m, STYLE)

    def test_png_roundtrip(self):
        p = os.path.join(self.tmp, "rt.png")
        rows = frame(on_style)
        write_png(p, W, H, rows)
        w, h, back = read_png(p)
        self.assertEqual((w, h), (W, H))
        self.assertEqual(back[40][20], GOLD)

    def test_on_style_frame_passes(self):
        m, fails = self.run_on(on_style, "good")
        self.assertEqual(fails, [], m)

    def test_colorful_storybook_frame_fails(self):
        m, fails = self.run_on(rainbow, "rainbow")
        self.assertTrue(any("off_style" in f or "on_palette" in f for f in fails), m)

    def test_off_band_hue_fails(self):
        m, fails = self.run_on(teal_accents, "teal")
        self.assertTrue(any("off_band" in f for f in fails), m)

    def test_accent_flood_fails(self):
        m, fails = self.run_on(gold_flood, "gold")
        self.assertTrue(any("accent_area" in f for f in fails), m)

    def test_flat_graybox_fails_only_on_texture(self):
        m, fails = self.run_on(flat_graybox, "graybox")
        self.assertEqual([f.split()[0] for f in fails], ["paper_texture"], m)

    def test_near_uniform_paper_fails(self):
        m, fails = self.run_on(near_uniform, "uniform")
        self.assertTrue(any(f.startswith("paper_texture") for f in fails), m)

    def test_textured_frames_keep_passing(self):
        for painter in (on_style,):
            m, fails = self.run_on(painter, "tex")
            # margin over the bar (was x2 of the provisional 0.1; at 0.38, x2 is the key art's own 0.77)
            self.assertGreaterEqual(m["paper_texture"], STYLE["thresholds"]["paper_texture_min"] + 0.1, m)
            self.assertEqual(fails, [])

    def test_missing_silhouettes_fails(self):
        m, fails = self.run_on(no_silhouettes, "flat")
        self.assertTrue(any("dark_share" in f for f in fails), m)

    def test_cli_exit_codes(self):
        good = os.path.join(self.tmp, "g.png")
        bad = os.path.join(self.tmp, "b.png")
        write_png(good, W, H, frame(on_style))
        write_png(bad, W, H, frame(rainbow))
        self.assertEqual(art_check.main([good]), 0)
        self.assertEqual(art_check.main([bad]), 1)
        self.assertEqual(art_check.main([os.path.join(self.tmp, "missing.png")]), 2)


REFERENCE = os.path.join(ROOT, "pipeline", "art", "reference", "target-keyart.png")


def reference_skip_reason(path):
    """Why the key-art calibration cannot run, or None. A Git LFS pointer is a file but not a PNG
    (a checkout without `git lfs pull`), so it skips like a missing file instead of erroring."""
    if not os.path.isfile(path):
        return "key art not in the repo yet (docs/references.md R7)"
    with open(path, "rb") as f:
        if f.read(24).startswith(b"version https://git-lfs"):
            return "key art is a Git LFS pointer; run git lfs pull --include='pipeline/art/reference/*.png'"
    return None


class ReferenceSkipTests(unittest.TestCase):
    def test_pointer_and_missing_skip_real_png_runs(self):
        tmp = tempfile.mkdtemp()
        ptr, real = os.path.join(tmp, "ptr.png"), os.path.join(tmp, "real.png")
        with open(ptr, "w") as f:
            f.write("version https://git-lfs.github.com/spec/v1\noid sha256:00\nsize 10\n")
        write_png(real, W, H, frame(on_style))
        self.assertIn("LFS pointer", reference_skip_reason(ptr))
        self.assertIn("not in the repo", reference_skip_reason(os.path.join(tmp, "none.png")))
        self.assertIsNone(reference_skip_reason(real))

    def test_ci_pulls_the_key_art_before_the_unit_tests(self):
        wf = open(os.path.join(ROOT, ".github", "workflows", "pipeline-checks.yml")).read()
        pull = wf.find("git lfs pull --include='pipeline/art/reference/*.png'")
        self.assertNotEqual(pull, -1)
        self.assertLess(pull, wf.find("python3 -m unittest discover"))

    def test_ci_pulls_the_lfs_test_fixtures_before_the_unit_tests(self):
        # CI checks out with lfs: false; the honest-jam fixtures (.uasset/.umap) and the rules PDF are LFS files the
        # sandboxes copy and check out again, so a pointer there fails (missing object) on the runner only
        wf = open(os.path.join(ROOT, ".github", "workflows", "pipeline-checks.yml")).read()
        pull = wf.find("git lfs pull --include='tests/fixtures/**,docs/rules/*.pdf'")
        self.assertNotEqual(pull, -1)
        self.assertLess(pull, wf.find("python3 -m unittest discover"))


_REF_SKIP = reference_skip_reason(REFERENCE)


@unittest.skipIf(_REF_SKIP, _REF_SKIP or "")
class ReferenceCalibrationTests(unittest.TestCase):
    """The numeric half of evals/art-judge/README.md: the reference passes, the broken variants fail."""

    def test_reference_and_known_bad(self):
        sys.path.insert(0, os.path.join(ROOT, "tools"))
        import make_art_calibration
        out = tempfile.mkdtemp()
        make_art_calibration.main([REFERENCE, out])
        self.assertEqual(art_check.evaluate(art_check.measure(REFERENCE, STYLE), STYLE), [])
        for bad in ("B1_colorful", "B4_grey_silh", "B5_flat_white", "B6_gold_flood", "B7_crushed"):
            m = art_check.measure(os.path.join(out, bad + ".png"), STYLE)
            self.assertTrue(art_check.evaluate(m, STYLE), f"{bad} passed: {m}")


class PaletteStatusTests(unittest.TestCase):
    """Card 0.7: a by-eye palette cannot give a verdict once the reference is in the repo."""

    def setUp(self):
        self.tmp = tempfile.mkdtemp()
        self.good = os.path.join(self.tmp, "g.png")
        write_png(self.good, W, H, frame(on_style))

    def test_provisional_palette_fails_when_reference_exists(self):
        prov = dict(STYLE, palette_status="provisional")
        self.assertEqual(len(art_check.provisional_failure(prov, self.good)), 1)
        self.assertEqual(art_check.provisional_failure(prov, os.path.join(self.tmp, "none.png")), [])
        self.assertEqual(art_check.provisional_failure(dict(STYLE, palette_status="measured"), self.good), [])

    def test_cli_exits_1_on_a_good_frame_with_provisional_palette(self):
        sp = os.path.join(self.tmp, "style.json")
        with open(sp, "w") as f:
            json.dump(dict(STYLE, palette_status="provisional"), f)
        from contextlib import redirect_stdout
        import io
        with redirect_stdout(io.StringIO()):
            self.assertEqual(art_check.main([self.good, "--style", sp, "--reference", self.good]), 1)
            self.assertEqual(art_check.main([self.good, "--reference", os.path.join(self.tmp, "none.png")]), 0)

    def test_repo_palette_is_measured_once_reference_exists(self):
        self.assertEqual(art_check.provisional_failure(STYLE, REFERENCE), [])

    def test_measure_palette_recentres_and_flags_missing(self):
        # paper drawn 6 L* off the palette hex comes back as the drawn colour; gold is absent
        shifted = tuple(min(255, c + 8) for c in PAPER[:3])
        p = os.path.join(self.tmp, "ref.png")
        write_png(p, W, H, [[shifted + (255,) for _ in range(W)] for _ in range(H)])
        got = {e["name"]: e for e in art_check.measure_palette(p, STYLE)}
        self.assertEqual(got["paper-mid"]["hex"], "#%02x%02x%02x" % shifted)
        self.assertTrue(got["paper-mid"]["found"])
        self.assertFalse(got["gold"]["found"])
        self.assertEqual(got["gold"]["hex"], _PAL["gold"])


class ArtGateTests(unittest.TestCase):
    """The automated art gate (no human art sign-off, Josh 2026-11-10): the team's references present, the numeric
    check, a calibrated judge and the capture's blind X/Y row. A passing root, then each part broken on purpose."""

    PIN = ("claude-test", "art-judge-xy/3", "rubric/2")

    def setUp(self):
        import shutil
        self.root = tempfile.mkdtemp()
        self.addCleanup(shutil.rmtree, self.root, True)
        r = self.root
        for d in ("pipeline/art/reference", "Test_Assets", "evals/art-judge", "tools", "docs/gdd/art-references", "Saved"):
            os.makedirs(os.path.join(r, d), exist_ok=True)
        self.capture = os.path.join(r, "Saved", "CAM_Eval_StyleFrame.png")
        write_png(self.capture, W, H, frame(on_style))
        write_png(os.path.join(r, "pipeline/art/reference/target-keyart.png"), W, H, frame(on_style))
        write_png(os.path.join(r, "Test_Assets/CHR_Owl_Flap_Damage.png"), W, H, other(frame(on_style)))
        self.spec = {"references": [
            {"id": "keyart", "path": "pipeline/art/reference/target-keyart.png", "kind": "image",
             "role": ["composition target", "palette"], "cards": ["0.10"], "judge": True, "required": True},
            {"id": "owl-flap", "path": "Test_Assets/CHR_Owl_Flap_Damage.png", "kind": "image", "role": ["owl"],
             "cards": ["MVP 7"], "consulted_by": ["0.28"], "required": True},
            {"id": "menu", "path": None, "kind": "described", "role": ["menu style bar"], "cards": ["0.21b"],
             "judge": False, "required": False, "description": ["paper cut-out"]}],
            "gdd_embedded": {"from": "docs/gdd/CURRENT", "role": ["composition target"], "required": False}}
        self.write("pipeline/art/references.json", json.dumps(self.spec))
        self.write("docs/gdd/CURRENT", "GDD-9.md\n")
        self.write("docs/gdd/GDD-9.md", "# GDD 9\n![concept](art-references/gameplay-01.png)\n"
                                        "<img src=\"art-references/gameplay-02.png\">\n![web](https://x.test/a.png)\n")
        write_png(os.path.join(r, "docs/gdd/art-references/gameplay-01.png"), W, H, frame(on_style))
        self.write("evals/art-judge/README.md", f"Judge pin: model `{self.PIN[0]}`, prompt `{self.PIN[1]}`, rubric "
                                                 f"`{self.PIN[2]}`.\n")
        self.write("tools/art_judge_prompt.md", f"Prompt version: `{self.PIN[1]}`. Rubric version: `{self.PIN[2]}` (below).\n")
        head = ",".join(art_check.JUDGE_COLS) + "\n"
        cal = "".join(self.row(f"anchor-vs-B{i}", "X", "all", "R3", "X", "calibration") for i in range(1, 7))
        cal += self.row("anchor-vs-anchor", "tie", "all", "all", "tie", "calibration")
        self.write("evals/art-judge/agreement.csv", head + cal)
        self.log = os.path.join(r, "Saved", "judge-log.csv")
        self.write("Saved/judge-log.csv", head + self.row("CAM_Eval_StyleFrame:target-keyart", "Y", "all", "all", "-",
                                                          "gate"))

    def write(self, rel, text):
        with open(os.path.join(self.root, rel), "w", encoding="utf-8") as fh:
            fh.write(text)

    def row(self, pair, closer, rx, ry, expected, note, stable="yes", pin=None):
        m, pv, rv = pin or self.PIN
        return ",".join(["2026-11-10", pair, "7", m, pv, rv, closer, rx, ry, stable, expected, note]) + "\n"

    def gate(self):
        return art_check.gate(self.capture, STYLE, self.root, self.log)[0]

    def test_passing_gate_and_cli_line(self):
        self.assertEqual(self.gate(), [])
        from contextlib import redirect_stdout
        import io
        out = io.StringIO()
        with redirect_stdout(out):
            rc = art_check.main([self.capture, "--gate", "--judge", self.log, "--root", self.root])
        self.assertEqual(rc, 0, out.getvalue())
        self.assertTrue(out.getvalue().startswith("ART_GATE: PASS"), out.getvalue())

    def test_missing_team_reference_fails(self):
        os.remove(os.path.join(self.root, "Test_Assets/CHR_Owl_Flap_Damage.png"))
        self.assertTrue(any("CHR_Owl_Flap_Damage.png is missing" in p for p in self.gate()), self.gate())

    def test_off_style_capture_fails_numeric(self):
        write_png(self.capture, W, H, frame(rainbow))
        self.assertTrue(any(p.startswith("numeric:") for p in self.gate()))

    def test_uncalibrated_or_flipped_judge_fails(self):
        self.write("evals/art-judge/agreement.csv", ",".join(art_check.JUDGE_COLS) + "\n")
        self.assertTrue(any("not calibrated" in p for p in self.gate()))
        head = ",".join(art_check.JUDGE_COLS) + "\n"
        cal = "".join(self.row(f"anchor-vs-B{i}", "X", "all", "R3", "X", "calibration") for i in range(1, 7))
        self.write("evals/art-judge/agreement.csv", head + cal + self.row("anchor-vs-anchor", "X", "all", "all", "tie",
                                                                          "calibration"))
        self.assertTrue(any("judge X vs expected tie" in p for p in self.gate()))
        self.write("evals/art-judge/agreement.csv", head + "".join(
            self.row(f"p{i}", "X", "all", "R3", "X", "calibration", pin=("other", "art-judge-xy/3", "rubric/2"))
            for i in range(7)))
        self.assertTrue(any("not calibrated" in p for p in self.gate()), "a calibration for another model")

    def test_judge_row_missing_unstable_or_a_false_row_fails(self):
        head = ",".join(art_check.JUDGE_COLS) + "\n"
        for body, want in ((head, "no pinned judge row"),
                           (head + self.row("CAM_Eval_StyleFrame:target-keyart", "Y", "all", "all", "-", "gate", "no"),
                            "flipped"),
                           (head + self.row("CAM_Eval_StyleFrame:target-keyart", "Y", "R5", "all", "-", "gate"),
                            "rubric rows false")):
            with self.subTest(want=want):
                self.write("Saved/judge-log.csv", body)
                self.assertTrue(any(want in p for p in self.gate()), self.gate())

    def test_gdd_embedded_images_join_the_list(self):
        refs = {r["path"]: r for r in art_check.load_references(self.root)}
        self.assertTrue(refs["docs/gdd/art-references/gameplay-01.png"]["exists"])
        self.assertEqual(refs["docs/gdd/art-references/gameplay-01.png"]["source"], "gdd")
        self.assertFalse(refs["docs/gdd/art-references/gameplay-02.png"]["exists"])
        self.assertFalse(refs["docs/gdd/art-references/gameplay-02.png"]["required"], "a GDD image is optional")
        self.assertNotIn("https://x.test/a.png", refs)
        self.write("docs/gdd/CURRENT", "GDD-none.md\n")   # another GDD picked: its images, or none
        self.assertNotIn("docs/gdd/art-references/gameplay-01.png",
                         {r["path"] for r in art_check.load_references(self.root)})

    @unittest.skipIf(hermetic.refs_left_out(), hermetic.LEFT_OUT)
    def test_repo_lists_every_reference_picture_with_role_and_cards(self):
        with open(os.path.join(ROOT, "pipeline", "art", "references.json"), encoding="utf-8") as fh:
            spec = json.load(fh)
        pics = [p for p in spec["references"] if p["kind"] == "image"]
        # Josh: the team's 21 reference pictures, Ricky's 13 #art-direction posts, the 2 quality-bar images and Ricky's
        # title-screen DM (11 Nov), the 4 key-art crops (keyart-crops/, 11 Nov) and the 3 crops of Ricky's sheets that
        # carry the GDD SH1.0 Keeper and red shot (discord-crops/, 12 Nov), all in this repo; plus 16
        # described team-art studies (in Assets/Art/), optional because each repo has only some of them. 11 Nov: 9 studies left the list as copies of a listed picture (the
        # 5 concept-ella-* = study-ella-*, 3 study-keeper-* and the eye-trace study = Ricky's posts; team_art.same_as)
        curated = [p for p in pics if "team art" not in p["role"]]
        team = [p for p in pics if "team art" in p["role"]]
        self.assertEqual(len(curated), 44)
        self.assertEqual(len(team), 16)
        self.assertEqual(len({p["path"] for p in pics}), 60)
        for p in curated:
            with self.subTest(ref=p["path"]):
                self.assertTrue(p["path"].startswith("pipeline/art/reference/"), "all in this repo")
                self.assertTrue(p["required"])
        for p in team:
            with self.subTest(ref=p["path"]):
                self.assertTrue(p["path"].startswith(("Assets/Art/", "Assets/Conceptual Art/")), p["path"])
                self.assertIs(p["required"], False, "a repo without the file leaves the entry out")
                self.assertTrue(p["what"])
        for p in pics:
            with self.subTest(ref=p["path"]):
                self.assertTrue(p["path"].lower().endswith((".png", ".jpg")))
                self.assertTrue(p["role"] and set(p["role"]) <= set(spec["roles"]), p["role"])
                self.assertTrue(p["cards"])
                self.assertIsInstance(p["judge"], bool)
                self.assertIsInstance(p["required"], bool)
        self.assertIn("pipeline/art/reference/target-keyart.png", {p["path"] for p in pics})
        # the layout sources (frame grids, pivots, fps) are kind data entries with role layout
        layout = {p["path"] for p in spec["references"] if "layout" in p["role"]}
        self.assertEqual(layout, {"pipeline/art/reference/Test_Assets/SpriteLayout.json",
                                  "pipeline/art/reference/Test_Assets/Asset Notes.md"})
        listed = art_check.load_references(ROOT)
        self.assertEqual(art_check.reference_problems(listed), [], "every required reference is in the repo")
        keyart = next(r for r in listed if r["path"].endswith("target-keyart.png"))
        self.assertIn("every art PR (art_check.py --gate)", keyart["cards"], "consulted_by is listed with cards")

    def test_described_entry_has_no_file_and_consulted_by_joins_cards(self):
        refs = {r["path"]: r for r in art_check.load_references(self.root)}
        self.assertNotIn(None, refs)
        self.assertEqual(refs["Test_Assets/CHR_Owl_Flap_Damage.png"]["cards"], ["MVP 7", "0.28"])
        self.assertTrue(refs["Test_Assets/CHR_Owl_Flap_Damage.png"]["judge"], "an image defaults to judge true")


class TeamArt(unittest.TestCase):
    """references.json team_art: every image under Assets/ and Mockups/ joins the list each run unless it is already
    listed (same path or same bytes); obsolete folders are skipped; an image that cannot be read fails loudly."""

    def setUp(self):
        import shutil
        self.root = tempfile.mkdtemp()
        self.addCleanup(shutil.rmtree, self.root, True)
        for d in ("pipeline/art/reference", "Assets/Art", "Assets/Old Tests - obsolete", "Mockups", "evals/art-judge",
                  "tools"):
            os.makedirs(os.path.join(self.root, d), exist_ok=True)
        self.png("pipeline/art/reference/target-keyart.png", frame(on_style))
        self.png("Assets/Art/Listed-Study.png", other(frame(on_style)))   # not the key art's bytes: listed twice
        self.spec = {"roles": {"composition target": "x", "team art": "y", "owl": "z"},
                     "references": [
                         {"id": "keyart", "path": "pipeline/art/reference/target-keyart.png", "kind": "image",
                          "role": ["composition target"], "cards": ["0.10"], "judge": True, "required": True},
                         {"id": "study", "path": "Assets/Art/Listed-Study.png", "kind": "image",
                          "role": ["team art", "owl"], "cards": ["MVP 7"], "judge": True, "required": False},
                         {"id": "absent", "path": "Assets/Conceptual Art/Elsewhere.png", "kind": "image",
                          "role": ["team art", "owl"], "cards": ["MVP 7"], "judge": True, "required": False}],
                     "elements": {"owl": {"refs": ["study", "absent"], "score_min": 0.5}},
                     "scene": {"refs": ["keyart"]},
                     "team_art": {"folders": ["Assets", "Mockups"], "skip_words": ["obsolete"], "role": ["team art"],
                                  "cards": [], "consulted_by": ["0.10"], "judge": True, "required": False}}
        self.write_spec()

    def png(self, rel, rows, w=W, h=H):
        os.makedirs(os.path.dirname(os.path.join(self.root, rel)), exist_ok=True)
        write_png(os.path.join(self.root, rel), w, h, rows)

    def write_spec(self):
        with open(os.path.join(self.root, "pipeline/art/references.json"), "w", encoding="utf-8") as fh:
            json.dump(self.spec, fh)

    def paths(self, spec):
        return {r["path"]: r for r in spec["references"]}

    def test_a_new_image_joins_with_the_defaults(self):
        self.png("Assets/New Folder/Owl-Idea.PNG", frame(rainbow))
        spec = art_check.load_spec(self.root)
        r = self.paths(spec)["Assets/New Folder/Owl-Idea.PNG"]
        self.assertEqual((r["kind"], r["role"], r["judge"], r["required"], r["auto"]),
                         ("image", ["team art"], True, False, "team art"))
        self.assertEqual(r["consulted_by"], ["0.10"])
        self.assertIn("look only", r["what"])
        self.assertEqual(spec["_team_art"]["joined"], ["Assets/New Folder/Owl-Idea.PNG"])
        self.assertEqual(spec["_team_art"]["described"], ["Assets/Art/Listed-Study.png"], "its own entry: not joined twice")
        flat = {r["path"]: r for r in art_check.load_references(self.root)}
        self.assertEqual(flat["Assets/New Folder/Owl-Idea.PNG"]["source"], "team art")
        self.assertIn("Assets/New Folder/Owl-Idea.PNG", art_check.reference_files(self.root), "never shipped")
        line = art_check.team_art_line(spec)
        self.assertIn("team art: 2 image(s) from Assets/, Mockups/", line)
        self.assertIn("1 joined automatically", line)
        import art_judge   # every tool reads the joined list: art_judge's loader is the same one
        self.assertIn("Assets/New Folder/Owl-Idea.PNG",
                      {r["path"] for r in art_judge.load_refs(os.path.join(self.root, "pipeline/art/references.json"))[
                          "references"]})
        # broken on purpose: without team_art nothing joins
        self.spec.pop("team_art")
        self.write_spec()
        self.assertNotIn("Assets/New Folder/Owl-Idea.PNG", self.paths(art_check.load_spec(self.root)))

    def test_jpg_and_webp_join_too(self):
        with open(os.path.join(self.root, "Mockups/sketch.jpeg"), "wb") as fh:
            fh.write(b"\xff\xd8\xff\xe0" + b"\0" * 64 + b"\xff\xd9")
        with open(os.path.join(self.root, "Assets/Art/paint.webp"), "wb") as fh:
            body = b"WEBPVP8 " + b"\0" * 40
            fh.write(b"RIFF" + len(body).to_bytes(4, "little") + body)
        self.assertLessEqual({"Mockups/sketch.jpeg", "Assets/Art/paint.webp"},
                             set(art_check.load_spec(self.root)["_team_art"]["joined"]))

    def test_a_byte_copy_of_a_listed_file_does_not_join(self):
        import shutil
        shutil.copy(os.path.join(self.root, "pipeline/art/reference/target-keyart.png"),
                    os.path.join(self.root, "Assets/Art/keyart-copy.png"))
        shutil.copy(os.path.join(self.root, "Assets/Art/Listed-Study.png"),
                    os.path.join(self.root, "Mockups/study-copy.png"))
        self.png("Mockups/new.png", frame(rainbow))
        shutil.copy(os.path.join(self.root, "Mockups/new.png"), os.path.join(self.root, "Mockups/new-again.png"))
        spec = art_check.load_spec(self.root)
        paths = self.paths(spec)
        self.assertNotIn("Assets/Art/keyart-copy.png", paths)
        self.assertNotIn("Mockups/study-copy.png", paths)
        self.assertEqual(len({"Mockups/new.png", "Mockups/new-again.png"} & set(paths)), 1,
                         "a new image joins; its copy beside it joins once")
        self.assertIn(("Assets/Art/keyart-copy.png", "pipeline/art/reference/target-keyart.png"),
                      spec["_team_art"]["copies"])
        # an LFS pointer (a checkout without git lfs pull) compares by its object id: still a copy, still present
        import hashlib
        raw = open(os.path.join(self.root, "pipeline/art/reference/target-keyart.png"), "rb").read()
        with open(os.path.join(self.root, "Assets/Art/keyart-copy.png"), "w") as fh:
            fh.write(f"version https://git-lfs.github.com/spec/v1\noid sha256:{hashlib.sha256(raw).hexdigest()}\n"
                     f"size {len(raw)}\n")
        spec = art_check.load_spec(self.root)
        self.assertNotIn("Assets/Art/keyart-copy.png", self.paths(spec))
        self.assertEqual(spec["_team_art"]["problems"], [])

    def test_an_obsolete_folder_is_skipped(self):
        self.png("Assets/Old Tests - obsolete/CHR_Owl.png", frame(rainbow))
        self.png("Assets/Old Tests - obsolete/sub/deeper.png", frame(rainbow))
        spec = art_check.load_spec(self.root)
        self.assertFalse([p for p in self.paths(spec) if "obsolete" in p])
        self.assertEqual(len(spec["_team_art"]["obsolete"]), 2)
        self.assertIn("2 in obsolete folders skipped", art_check.team_art_line(spec))
        # broken on purpose: the same image outside the obsolete folder joins
        self.png("Assets/Art/CHR_Owl.png", frame(rainbow))
        self.assertIn("Assets/Art/CHR_Owl.png", self.paths(art_check.load_spec(self.root)))

    def test_an_unreadable_image_fails_loudly(self):
        for rel, raw in (("Assets/Art/not-a-png.png", b"hello"), ("Assets/Art/empty.jpg", b""),
                         ("Assets/Art/cut.png", open(os.path.join(self.root, "Assets/Art/Listed-Study.png"),
                                                     "rb").read()[:200])):
            with open(os.path.join(self.root, rel), "wb") as fh:
                fh.write(raw)
        spec = art_check.load_spec(self.root)
        bad = dict(spec["_team_art"]["problems"])
        self.assertEqual(set(bad), {"Assets/Art/not-a-png.png", "Assets/Art/empty.jpg", "Assets/Art/cut.png"})
        self.assertIn("truncated", bad["Assets/Art/cut.png"])
        self.assertNotIn("Assets/Art/not-a-png.png", self.paths(spec), "never joined")
        self.assertTrue(art_check.team_art_line(spec).startswith("team art: FAIL 3 image(s) cannot be read"))
        probs = art_check.reference_problems(art_check.load_references(self.root))
        self.assertEqual(len([p for p in probs if p.startswith("team art ")]), 3, probs)
        import art_judge
        self.assertTrue(any("cannot be read" in p for p in art_judge.coverage(art_judge.load_refs(
            os.path.join(self.root, "pipeline/art/references.json")), self.root)))
        from contextlib import redirect_stdout
        import io
        out = io.StringIO()
        with redirect_stdout(out):
            rc = art_check.main(["--references", "--root", self.root])
        self.assertEqual(rc, 1, out.getvalue())
        self.assertIn("UNREADABLE Assets/Art/empty.jpg", out.getvalue())
        self.assertIn("team art: FAIL 3", out.getvalue())

    def test_an_optional_entry_whose_file_is_absent_is_left_out(self):
        spec = art_check.load_spec(self.root)
        self.assertNotIn("absent", {r["id"] for r in spec["references"]})
        self.assertEqual(spec["elements"]["owl"]["refs"], ["study"], "and out of every judge element")
        self.assertEqual(spec["_team_art"]["left_out"], ["Assets/Conceptual Art/Elsewhere.png"])
        self.assertEqual(art_check.reference_problems(art_check.load_references(self.root)), [])
        # broken on purpose: a required entry whose file is absent still fails
        self.spec["references"][2]["required"] = True
        self.write_spec()
        self.assertTrue(any("Elsewhere.png is missing" in p
                            for p in art_check.reference_problems(art_check.load_references(self.root))))

    def test_a_listed_byte_copy_is_left_out_and_same_as_skips_a_re_encoded_copy(self):
        """The same picture filed twice under two ids counts once: the later listed entry whose bytes equal an earlier
        one leaves the list and every judge element (11 Nov: 5 concept-ella-* were byte copies of study-ella-*).
        team_art.same_as names re-encoded copies (same pixels, other bytes) so they do not join either."""
        import shutil
        shutil.copy(os.path.join(self.root, "Assets/Art/Listed-Study.png"), os.path.join(self.root, "Mockups/twin.png"))
        self.spec["references"].append({"id": "twin", "path": "Mockups/twin.png", "kind": "image",
                                        "role": ["team art", "owl"], "cards": ["MVP 7"], "judge": True,
                                        "required": False})
        self.spec["elements"]["owl"]["refs"].append("twin")
        self.png("Assets/Art/Re-Encoded.png", other(frame(rainbow)))
        self.spec["team_art"]["same_as"] = {"Assets/Art/Re-Encoded.png": "keyart"}
        self.write_spec()
        spec = art_check.load_spec(self.root)
        self.assertNotIn("twin", {r["id"] for r in spec["references"]})
        self.assertEqual(spec["elements"]["owl"]["refs"], ["study"])
        self.assertEqual(spec["_team_art"]["listed_copies"], [("Mockups/twin.png", "Assets/Art/Listed-Study.png")])
        self.assertNotIn("Assets/Art/Re-Encoded.png", self.paths(spec))
        self.assertIn(("Assets/Art/Re-Encoded.png", "pipeline/art/reference/target-keyart.png"),
                      spec["_team_art"]["copies"])
        self.assertIn("1 listed entries left out as byte copies", art_check.team_art_line(spec))
        # broken on purpose: different bytes stay listed; a same_as naming an unknown id does not skip
        self.png("Mockups/twin.png", frame(rainbow))
        self.spec["team_art"]["same_as"] = {"Assets/Art/Re-Encoded.png": "nobody"}
        self.write_spec()
        spec = art_check.load_spec(self.root)
        self.assertIn("twin", {r["id"] for r in spec["references"]})
        self.assertIn("Assets/Art/Re-Encoded.png", self.paths(spec))

    def test_repo_team_art_entries_are_wired(self):
        """Each described study names known elements and cards, as art_judge coverage would check it when present."""
        import art_judge
        with open(os.path.join(ROOT, "pipeline", "art", "references.json"), encoding="utf-8") as fh:
            raw = json.load(fh)
        self.assertIn("team_art", raw)
        self.assertIn("obsolete", raw["team_art"]["_about"])
        team = {r["id"] for r in raw["references"] if "team art" in r["role"]}
        used = {rid for el in raw["elements"].values() for rid in el["refs"]}
        exempt = {r["id"] for r in raw["references"] if r.get("judge_exempt")}
        self.assertEqual(team - used - exempt, set(), "every study is used by a judge element or says why not")
        probs = [p for p in art_judge.coverage(raw) if "is missing on disk" not in p]
        self.assertEqual(probs, [])


class HueBandCanonTest(unittest.TestCase):
    """The off_band gate (hue_gate) against the canon: every canonical warm colour is inside it, a greenish pale
    yellow (the Gemini proof's rim light, e.g. 224,224,160, hue ~100) is not. Triage 12 Nov: the check is right."""

    def inside(self, rgb):
        import math
        lab = art_check.rgb_to_lab(rgb)
        chroma = math.hypot(lab[1], lab[2])
        hue = math.degrees(math.atan2(lab[2], lab[1])) % 360
        gate = STYLE["hue_gate"]
        return chroma <= gate["chroma_min"] or any(lo <= hue <= hi for lo, hi in gate["allowed_hue_bands_deg"])

    def test_canonical_warm_colours_pass(self):
        canon = [c["hex"] for c in STYLE["palette"]]   # bronze/umber/ink/paper and the by-eye golds
        canon += ["#e9c46a", "#ffc76a", "#ffd84a", "#f5aa28", "#94611e", "#fff5dc", "#fff3d6"]   # GDD SH1.0 golds, ivory
        for h in canon:
            self.assertTrue(self.inside(art_check.hex_to_rgb(h)), h)

    def test_greenish_pale_yellow_fails(self):
        for rgb in [(224, 224, 160), (224, 224, 128), (200, 200, 120)]:
            self.assertFalse(self.inside(rgb), rgb)

    def test_key_art_off_band_is_zero(self):
        key = os.path.join(ROOT, "pipeline", "art", "reference", "target-keyart.png")
        self.assertEqual(art_check.measure(key, STYLE)["off_band"], 0.0)


if __name__ == "__main__":
    unittest.main()
