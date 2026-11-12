"""Tests for tools/sprite_check.py. Sprite frames are drawn in a temp folder (PNGs are LFS-only
in this repo, so none are committed). One good silhouette sheet passes; each broken sheet has one
thing wrong on purpose and must fail on that check."""
import glob
import io
import json
import os
import re
import sys
import tempfile
import unittest
from contextlib import redirect_stderr, redirect_stdout

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, os.path.join(ROOT, "tools"))
import sprite_check  # noqa: E402
from png import write_png  # noqa: E402

# final-9 A C1: the rule fixtures are for style.json before D13 sets the mips rule (card 0.10a); the repo-state checks
# (MipsDecidedTests.test_repo) read the real file as REAL_STYLE
REAL_STYLE = json.load(open(os.path.join(ROOT, "pipeline", "art", "style.json")))
sys.path.insert(0, HERE)
import hermetic  # noqa: E402
sprite_check.DEFAULT_STYLE, STYLE = hermetic.pre_d13_style()
INK = (22, 17, 15)
GOLD = (233, 176, 74)
CLEAR = (0, 0, 0, 0)


def blob(n=64, rx=20, ry=26, color=INK, soft=1, matte=CLEAR, cx=None, cy=None):
    """An ellipse silhouette with a `soft`-pixel anti-aliased edge on a transparent frame."""
    cx = n / 2 if cx is None else cx
    cy = n / 2 if cy is None else cy
    rows = []
    for y in range(n):
        row = []
        for x in range(n):
            d = (((x + 0.5 - cx) / rx) ** 2 + ((y + 0.5 - cy) / ry) ** 2) ** 0.5
            edge = (d - 1) * min(rx, ry)  # distance outside the ellipse in pixels (approx.)
            if edge <= 0:
                row.append(color + (255,))
            elif edge < soft:
                row.append(color + (int(255 * (1 - edge / soft)),))
            else:
                row.append(matte)
        rows.append(row)
    return rows


def sheet(frames):
    """Lay frames out left to right."""
    h = len(frames[0])
    return [sum((f[y] for f in frames), []) for y in range(h)]


class SpriteCheckTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.mkdtemp()

    def png(self, name, rows):
        p = os.path.join(self.tmp, name + ".png")
        write_png(p, len(rows[0]), len(rows), rows)
        return p

    def run_check(self, rows, name="s", **kw):
        return sprite_check.check([self.png(name, rows)], STYLE, **kw)

    def assertFailsOn(self, report, word):
        self.assertFalse(report["pass"], report)
        self.assertTrue(any(word in f for f in report["failures"]), report["failures"])

    # good
    def test_good_sheet_passes(self):
        frames = [blob(rx=18 + i, ry=26) for i in range(4)]
        r = self.run_check(sheet(frames), grid=(64, 64), frames=4, size=(64, 64), pow2=False)
        self.assertTrue(r["pass"], r["failures"])
        self.assertEqual(len(r["frames"]), 4)

    def test_good_loose_frames_pass(self):
        paths = [self.png(f"f{i}", blob(rx=20, ry=24 + i)) for i in range(3)]
        self.assertTrue(sprite_check.check(paths, STYLE, size=(64, 64))["pass"])

    def test_pow2_sheet_passes_when_required(self):
        r = self.run_check(sheet([blob(), blob()]), grid=(64, 64), pow2=True)  # 128x64
        self.assertTrue(r["pass"], r["failures"])

    # size
    def test_frames_of_different_size_fail(self):
        paths = [self.png("a", blob(64)), self.png("b", blob(60, rx=18, ry=24))]
        self.assertFailsOn(sprite_check.check(paths, STYLE), "differ in size")

    def test_wrong_declared_size_fails(self):
        self.assertFailsOn(self.run_check(blob(), size=(32, 32)), "declared 32x32")

    def test_sheet_not_divisible_by_grid_fails(self):
        rows = [r + [CLEAR] * 2 for r in sheet([blob(), blob()])]  # 130x64
        self.assertFailsOn(self.run_check(rows, grid=(64, 64)), "whole number")

    def test_non_pow2_fails_when_required(self):
        self.assertFailsOn(self.run_check(blob(60, rx=18, ry=24), pow2=True), "pow2")

    def test_wrong_frame_count_fails(self):
        self.assertFailsOn(self.run_check(sheet([blob(), blob()]), grid=(64, 64), frames=3), "expected 3")

    def test_empty_frame_inside_sheet_fails(self):
        empty = [[CLEAR] * 64 for _ in range(64)]
        self.assertFailsOn(self.run_check(sheet([blob(), empty, blob()]), grid=(64, 64)), "empty")

    def test_trailing_empty_cell_is_padding(self):
        empty = [[CLEAR] * 64 for _ in range(64)]
        r = self.run_check(sheet([blob(), blob(), empty, empty]), grid=(64, 64), frames=2)
        self.assertTrue(r["pass"], r["failures"])

    # background
    def test_opaque_background_fails(self):
        paper = (140, 125, 112, 255)
        self.assertFailsOn(self.run_check(blob(matte=paper)), "background")

    def test_shape_touching_frame_edge_fails(self):
        self.assertFailsOn(self.run_check(blob(rx=20, ry=34)), "border_visible")

    # edges
    def test_wide_soft_fringe_fails(self):
        self.assertFailsOn(self.run_check(blob(rx=16, ry=20, soft=8)), "fringe")

    def test_light_matte_halo_fails(self):
        self.assertFailsOn(self.run_check(blob(matte=(255, 255, 255, 0))), "halo")

    # silhouette
    def test_wispy_shape_fails_fill(self):
        rows = [[CLEAR] * 64 for _ in range(64)]
        for i in range(4, 60):
            rows[i][i] = INK + (255,)
            rows[i][63 - i] = INK + (255,)
        self.assertFailsOn(self.run_check(rows), "fill")

    def test_box_fails_fill(self):
        rows = [[INK + (255,) if 2 <= x < 62 and 2 <= y < 62 else CLEAR for x in range(64)] for y in range(64)]
        self.assertFailsOn(self.run_check(rows), "fill")

    def test_light_silhouette_fails_dark_share(self):
        self.assertFailsOn(self.run_check(blob(color=GOLD)), "dark_share")

    def test_glow_passes_as_fx_but_not_as_silhouette(self):
        glow = blob(rx=14, ry=14, color=GOLD, soft=10)
        self.assertTrue(self.run_check(glow, kind="fx")["pass"])
        self.assertFalse(self.run_check(glow, kind="silhouette")["pass"])

    def test_every_kind_threshold_is_read_from_style(self):
        for kind, k in STYLE["sprite"]["kinds"].items():
            for key in ("border_visible_max", "fill_min", "fill_max", "fringe_max", "halo_max", "dark_share_min"):
                self.assertIn(key, k, f"{kind}.{key}")

    # CLI
    def test_cli_exit_codes(self):
        good, bad = self.png("good", blob()), self.png("bad", blob(color=GOLD))
        with redirect_stdout(io.StringIO()), redirect_stderr(io.StringIO()):
            self.assertEqual(sprite_check.main([good]), 0)
            self.assertEqual(sprite_check.main([bad]), 1)
            self.assertEqual(sprite_check.main([os.path.join(self.tmp, "missing.png")]), 2)

    def test_scan_uses_sidecars_and_skips_lfs_pointers(self):
        art = os.path.join(self.tmp, "Art")
        os.makedirs(art)
        write_png(os.path.join(art, "ella.png"), 128, 64, sheet([blob(), blob()]))
        with open(os.path.join(art, "ella.sprite.json"), "w") as f:
            json.dump({"kind": "silhouette", "grid": [64, 64], "frames": 2}, f)
        with open(os.path.join(art, "pointer.png"), "w") as f:
            f.write("version https://git-lfs.github.com/spec/v1\noid sha256:abc\nsize 10\n")
        with open(os.path.join(art, "pointer.sprite.json"), "w") as f:
            json.dump({"kind": "silhouette"}, f)
        os.makedirs(os.path.join(art, "Raw"))
        write_png(os.path.join(art, "Raw", "notes.png"), 8, 8, [[CLEAR] * 8] * 8)  # exempt folder: not a sprite
        reports, skipped = sprite_check.scan(art, STYLE)
        self.assertEqual(len(reports), 1)
        self.assertTrue(reports[0]["pass"], reports[0]["failures"])
        self.assertEqual(sorted(os.path.basename(p) for p, _ in skipped), ["notes.png", "pointer.png"])
        write_png(os.path.join(art, "ella.png"), 128, 64, sheet([blob(color=GOLD), blob()]))
        with redirect_stdout(io.StringIO()):
            self.assertEqual(sprite_check.main(["--scan", art]), 1)
            self.assertEqual(sprite_check.main(["--scan", os.path.join(self.tmp, "nothing")]), 0)

    def test_lfs_pointer_with_sidecar_fails_with_flag(self):
        art = os.path.join(self.tmp, "Art")
        os.makedirs(art)
        with open(os.path.join(art, "pointer.png"), "w") as f:
            f.write("version https://git-lfs.github.com/spec/v1\noid sha256:abc\nsize 10\n")
        with open(os.path.join(art, "pointer.sprite.json"), "w") as f:
            json.dump({"kind": "silhouette"}, f)
        reports, skipped = sprite_check.scan(art, STYLE)
        self.assertEqual((reports, len(skipped)), ([], 1))
        reports, skipped = sprite_check.scan(art, STYLE, fail_lfs_pointer=True)
        self.assertFailsOn(reports[0], "lfs")
        self.assertEqual(skipped, [])
        with redirect_stdout(io.StringIO()):
            self.assertEqual(sprite_check.main(["--scan", art]), 0)
            self.assertEqual(sprite_check.main(["--scan", art, "--fail-lfs-pointer"]), 1)
        write_png(os.path.join(art, "pointer.png"), 64, 64, blob())  # after git lfs pull: real pixels
        with redirect_stdout(io.StringIO()):
            self.assertEqual(sprite_check.main(["--scan", art, "--fail-lfs-pointer"]), 0)

    # sidecars
    def test_png_without_sidecar_fails_scan(self):
        art = os.path.join(self.tmp, "Art", "Source", "Ella", "Export")
        os.makedirs(art)
        write_png(os.path.join(art, "Ella_Idle.png"), 64, 64, blob())
        reports, _ = sprite_check.scan(os.path.join(self.tmp, "Art"), STYLE)
        self.assertFailsOn(reports[0], "sidecar")
        with redirect_stdout(io.StringIO()):
            self.assertEqual(sprite_check.main(["--scan", os.path.join(self.tmp, "Art")]), 1)

    def test_lfs_pointer_without_sidecar_still_fails(self):
        art = os.path.join(self.tmp, "Art")
        os.makedirs(art)
        with open(os.path.join(art, "ella.png"), "w") as f:
            f.write("version https://git-lfs.github.com/spec/v1\noid sha256:abc\nsize 10\n")
        reports, _ = sprite_check.scan(art, STYLE)
        self.assertFailsOn(reports[0], "sidecar")

    def test_reference_folder_is_exempt(self):
        art = os.path.join(self.tmp, "Art", "Reference")
        os.makedirs(art)
        write_png(os.path.join(art, "moodboard.png"), 8, 8, [[CLEAR] * 8] * 8)
        reports, skipped = sprite_check.scan(os.path.join(self.tmp, "Art"), STYLE)
        self.assertEqual((reports, len(skipped)), ([], 1))

    def test_missing_folder_fails_with_require_dir(self):
        gone = os.path.join(self.tmp, "nothing")
        with redirect_stdout(io.StringIO()):
            self.assertEqual(sprite_check.main(["--scan", gone]), 0)
            self.assertEqual(sprite_check.main(["--scan", gone, "--require-dir"]), 1)

    # margin and spacing
    def test_spaced_sheet_fails_when_sidecar_leaves_spacing_out(self):
        gap = [[CLEAR] * 4 for _ in range(64)]
        rows = sheet([blob(), gap, blob(), gap, blob()])  # 3 cells of 64 with 4 px spacing = 200 px
        self.assertFailsOn(self.run_check(rows, grid=(64, 64), frames=3), "spacing 0")
        r = self.run_check(rows, grid=(64, 64), frames=3, spacing=4)
        self.assertTrue(r["pass"], r["failures"])

    def test_margin_is_applied(self):
        pad = [[CLEAR] * 2 for _ in range(64)]
        mid = sheet([pad, blob(), blob(), pad])  # 132 wide
        rows = [[CLEAR] * 132] * 2 + mid + [[CLEAR] * 132] * 2  # 132x68, 2 px margin all round
        self.assertFailsOn(self.run_check(rows, grid=(64, 64)), "whole number")
        r = self.run_check(rows, grid=(64, 64), frames=2, margin=2)
        self.assertTrue(r["pass"], r["failures"])

    # pivot drift
    def test_pivot_drift_over_limit_fails_on_a_loop(self):
        rows = sheet([blob(cx=32), blob(cx=35), blob(cx=33)])  # 3 px drift in x
        self.assertFailsOn(self.run_check(rows, grid=(64, 64), loop=True), "pivot")
        self.assertTrue(self.run_check(rows, grid=(64, 64), loop=False)["pass"])  # no anim, no loop: not checked

    def test_pivot_drift_is_checked_on_one_shot_anims(self):
        rows = sheet([blob(cy=32), blob(cy=32), blob(cy=28)])  # Open: feet jump 4 px on the last frame
        self.assertFailsOn(self.run_check(rows, grid=(64, 64), anim="Open", fps=24), "pivot")
        good = sheet([blob(cy=32), blob(cy=32), blob(cy=31)])
        self.assertTrue(self.run_check(good, grid=(64, 64), anim="Open", fps=24)["pass"])

    def test_sidecar_drift_override_needs_a_reason(self):
        rows = sheet([blob(cy=32), blob(cy=32), blob(cy=28)])
        self.assertFailsOn(self.run_check(rows, grid=(64, 64), anim="Open", drift_max=5), "no pivot_drift_reason")
        r = self.run_check(rows, grid=(64, 64), anim="Open", drift_max=5, drift_reason="hop on open, D-new-port-13")
        self.assertTrue(r["pass"], r["failures"])

    def test_one_shot_drift_from_scan_sidecar(self):
        d = tempfile.mkdtemp()
        p = os.path.join(d, "SPR_Ella_Open.png")
        rows = sheet([blob(cy=32), blob(cy=32), blob(cy=28)])
        write_png(p, len(rows[0]), len(rows), rows)
        with open(os.path.join(d, "SPR_Ella_Open.sprite.json"), "w") as fh:
            json.dump({"kind": "silhouette", "grid": [64, 64], "frames": 3, "anim": "Open", "fps": 24}, fh)
        reports, _ = sprite_check.scan(d, STYLE)
        self.assertFailsOn(reports[0], "pivot")

    def test_pivot_drift_within_limit_passes(self):
        rows = sheet([blob(cx=32), blob(cx=33), blob(cx=32)])  # 1 px
        r = self.run_check(rows, grid=(64, 64), loop=True)
        self.assertTrue(r["pass"], r["failures"])
        self.assertEqual(r["pivot_drift_px"], [1, 0])

    def test_vertical_pivot_drift_fails(self):
        rows = sheet([blob(cy=32), blob(cy=29)])  # feet move 3 px up
        self.assertFailsOn(self.run_check(rows, grid=(64, 64), loop=True), "pivot")

    def test_big_jump_from_the_audit_fails(self):
        rows = sheet([blob(n=128, cx=40, cy=60), blob(n=128, cx=85, cy=80)])  # 45 px x, 20 px y
        self.assertFailsOn(self.run_check(rows, grid=(128, 128), loop=True), "pivot")

    # feet point, not the opaque box (critic: an umbrella opening to one side moved the box centre)
    @staticmethod
    def umbrella_open(canopy_rx, feet_cx=32):
        """Body with feet at feet_cx, plus a canopy above it that grows to the right only."""
        body = blob(rx=6, ry=16, cx=feet_cx, cy=44)
        canopy = blob(rx=canopy_rx, ry=6, cx=feet_cx + canopy_rx - 4, cy=12)
        return [[b if b[3] >= c[3] else c for b, c in zip(rb, rc)] for rb, rc in zip(body, canopy)]

    def pivot_fails(self, report):
        return [f for f in report["failures"] if f.startswith("pivot")]

    def test_one_sided_umbrella_open_keeps_the_feet(self):
        rows = sheet([self.umbrella_open(6), self.umbrella_open(14), self.umbrella_open(24)])
        r = self.run_check(rows, grid=(64, 64), anim="Open", fps=24)
        self.assertEqual(self.pivot_fails(r), [], r["failures"])
        self.assertEqual(r["pivot_drift_px"], [0, 0])
        # the old measure (whole opaque box) would have failed this legit sheet
        r = self.run_check(rows, grid=(64, 64), anim="Open", fps=24, feet_rows=64)
        self.assertTrue(self.pivot_fails(r), r["failures"])

    def test_feet_moving_under_an_open_umbrella_fails(self):
        rows = sheet([self.umbrella_open(6, feet_cx=30), self.umbrella_open(14, feet_cx=34)])
        self.assertTrue(self.pivot_fails(self.run_check(rows, grid=(64, 64), anim="Open", fps=24)))

    def test_feet_rows_from_scan_sidecar(self):
        d = tempfile.mkdtemp()
        p = os.path.join(d, "SPR_Ella_Open.png")
        rows = sheet([self.umbrella_open(6), self.umbrella_open(24)])
        write_png(p, len(rows[0]), len(rows), rows)
        side = os.path.join(d, "SPR_Ella_Open.sprite.json")
        for feet_rows, drifts in ((None, False), (64, True)):
            meta = {"kind": "silhouette", "grid": [64, 64], "frames": 2, "anim": "Open", "fps": 24}
            if feet_rows:
                meta["feet_rows"] = feet_rows
            with open(side, "w") as fh:
                json.dump(meta, fh)
            reports, _ = sprite_check.scan(d, STYLE)
            self.assertEqual(bool(self.pivot_fails(reports[0])), drifts, reports[0]["failures"])

    def test_feet_point_matches_box_centre_for_a_plain_blob(self):
        clear = STYLE["sprite"]["alpha_clear_max"]
        m = sprite_check.measure_frame(blob(cx=30), STYLE["sprite"])
        self.assertEqual(sprite_check.feet_point(blob(cx=30), clear, 999), (m["bbox"][0] + m["bbox"][2] / 2, m["bbox"][1] + m["bbox"][3]))
        self.assertIsNone(sprite_check.feet_point([[CLEAR] * 4] * 4, clear, 8))

    # anim table
    def test_anim_frame_count_outside_table_fails(self):
        rows = sheet([blob(), blob()])
        self.assertFailsOn(self.run_check(rows, grid=(64, 64), anim="IdleFloat"), "allows 4-6")
        rows = sheet([blob()] * 4)
        self.assertTrue(self.run_check(rows, grid=(64, 64), anim="IdleFloat", fps=8)["pass"])

    def test_anim_fps_and_name_checked(self):
        rows = sheet([blob()] * 4)
        self.assertFailsOn(self.run_check(rows, grid=(64, 64), anim="IdleFloat", fps=12), "fps")
        self.assertFailsOn(self.run_check(rows, grid=(64, 64), anim="Dance"), "not in style.json")
        self.assertTrue(self.run_check(rows, grid=(64, 64), anim="Impact", fps=22)["pass"])

    # tile seam
    def test_tile_with_matching_edges_passes(self):
        rows = [[PAPER_A if (x + y) % 2 else PAPER_B for x in range(64)] for y in range(64)]
        r = self.run_check(rows, kind="tile")
        self.assertTrue(r["pass"], r["failures"])

    def test_tile_with_a_gradient_seam_fails(self):
        rows = [[(110 + x, 100 + x // 2, 90, 255) for x in range(64)] for y in range(64)]
        self.assertFailsOn(self.run_check(rows, kind="tile"), "seam")

    def test_tile_xy_checks_top_and_bottom(self):
        rows = [[(110 + y, 100 + y // 2, 90, 255) for x in range(64)] for y in range(64)]
        self.assertTrue(self.run_check(rows, kind="tile")["pass"])
        self.assertFailsOn(self.run_check(rows, kind="tile", tile_axes="xy"), "seam")


PAPER_A, PAPER_B = (140, 125, 112, 255), (150, 133, 118, 255)


class SourcesTests(unittest.TestCase):
    """--sources: every imported asset keeps an editable layered source (ported rule, docs/coverage-map.md)."""
    def tree(self, d, layered_in):
        for name in ("Ella", "Owl"):
            os.makedirs(os.path.join(d, "Content", name))
            open(os.path.join(d, "Content", name, f"T_{name}_Idle.uasset"), "wb").close()
            os.makedirs(os.path.join(d, "Source", name, "Raw"))
        for rel in layered_in:
            open(os.path.join(d, "Source", rel), "wb").close()
        return os.path.join(d, "Content"), os.path.join(d, "Source")

    def test_every_asset_folder_with_a_layered_file_passes(self):
        with tempfile.TemporaryDirectory() as d:
            c, s = self.tree(d, ["Ella/Ella_Idle.psd", "Owl/Owl.kra"])
            self.assertEqual(sprite_check.check_sources(c, s), [])
            self.assertEqual(sprite_check.main(["--sources", c, s]), 0)

    def test_missing_or_raw_only_source_fails(self):
        with tempfile.TemporaryDirectory() as d:
            c, s = self.tree(d, ["Ella/Ella_Idle.psd", "Owl/Raw/owl_gen.psd"])
            fails = sprite_check.check_sources(c, s)
            self.assertEqual(len(fails), 1, fails)
            self.assertIn("Owl", fails[0])
            self.assertEqual(sprite_check.main(["--sources", c, s]), 1)


    def test_a_blender_scene_counts_as_the_source(self):
        """Blender is the art generator: the .blend the frames were rendered from (kept in Raw/) is the source."""
        with tempfile.TemporaryDirectory() as d:
            c, s = self.tree(d, ["Ella/Ella_Idle.psd"])
            os.makedirs(os.path.join(s, "Owl", "Raw", "Flap"))
            open(os.path.join(s, "Owl", "Raw", "Flap", "Owl_Flap.blend"), "wb").close()
            self.assertEqual(sprite_check.check_sources(c, s), [])
            os.remove(os.path.join(s, "Owl", "Raw", "Flap", "Owl_Flap.blend"))   # broken on purpose: no scene
            self.assertEqual(len(sprite_check.check_sources(c, s)), 1)


class NameTests(unittest.TestCase):
    def names(self, *files):
        d = tempfile.mkdtemp()
        for f in files:
            os.makedirs(os.path.dirname(os.path.join(d, f)) or d, exist_ok=True)
            open(os.path.join(d, f), "w").close()
        return sprite_check.check_names(d, STYLE)

    def test_good_names_pass(self):
        self.assertEqual(self.names("Ella/T_Ella_Idle.uasset", "Ella/SPR_Ella_IdleFloat_00.uasset",
                                    "Ella/SPR_Ella_IdleFloat_11.uasset", "Ella/FB_Ella_IdleFloat.uasset",
                                    "Spikes/SPR_Spikes_Strip_PH.uasset", "Ella/notes.txt"), [])

    def test_bad_prefix_and_unpadded_index_fail(self):
        f = self.names("Ella/Ella_Idle.uasset", "Ella/SPR_Ella_Idle_1.uasset", "Ella/SPR_Ella_Idle_001.uasset")
        self.assertEqual(len(f), 3, f)

    def test_unpadded_frame_points_to_the_rename_fallback(self):
        f = self.names("Ella/SPR_Ella_Idle_1.uasset", "Ella/SPR_Ella_Idle_3_PH.uasset")
        self.assertEqual(len(f), 2, f)
        self.assertTrue(all("not 2 digits" in x and "section 3" in x for x in f), f)
        f = self.names("Ella/Ella_Idle.uasset")
        self.assertTrue(f and "not 2 digits" not in f[0], f)

    def test_version_words_are_banned(self):
        for bad in ("T_Ella_Idle_v2", "SPR_Ella_Idle_final", "FB_Ella_Idle_New", "T_Ella_Idle_V12_00"):
            with self.subTest(name=bad):
                f = self.names(f"Ella/{bad}.uasset")
                self.assertTrue(f and "_v2/_final/_new" in f[0], f)
        self.assertEqual(self.names("Ella/T_Ella_Newspaper.uasset"), [])  # "New" inside a word is fine

    def test_cli(self):
        d = tempfile.mkdtemp()
        open(os.path.join(d, "T_Ella_Idle_final.uasset"), "w").close()
        with redirect_stdout(io.StringIO()):
            self.assertEqual(sprite_check.main(["--names", d]), 1)
            self.assertEqual(sprite_check.main(["--names", os.path.join(d, "none")]), 0)


GOOD_TEXTURE = {"class": "Texture2D", "name": "T_Ella_Idle", "filter": "TF_Bilinear", "srgb": True,
                "compression": "TC_EditorIcon", "never_stream": True, "lod_group": "TEXTUREGROUP_World",
                "mip_gen": "TMGS_NoMipmaps", "width": 512, "height": 128}
GOOD_SPRITE = {"class": "PaperSprite", "name": "SPR_Ella_IdleFloat_00",
               "material": "/Paper2D/MaskedUnlitSpriteMaterial.MaskedUnlitSpriteMaterial",
               "collision": "None", "atlas_group": None, "pivot_mode": "Bottom_Center", "pivot": [],
               "render_geometry": "TightBoundingBox", "width": 128, "height": 128,
               "sockets": [{"name": "Muzzle", "location": [70, 40]}]}
def kf(*idx, anim="IdleFloat", asset="Ella"):
    return [{"sprite": f"SPR_{asset}_{anim}_{i:02d}", "frame_run": 1} for i in idx]


GOOD_FLIPBOOK = {"class": "PaperFlipbook", "name": "FB_Ella_IdleFloat", "fps": 8, "keyframes": kf(0, 1, 2, 3)}
TRANSLUCENT = "/Paper2D/TranslucentUnlitSpriteMaterial.TranslucentUnlitSpriteMaterial"
ANCHORS = os.path.join(HERE, "fixtures", "art_dump", "anchors.json")
# rule -> a change that breaks only that rule
BREAKS = {
    "filter": (GOOD_TEXTURE, {"filter": "TF_Nearest"}),
    "srgb": (GOOD_TEXTURE, {"srgb": False}),
    "compression": (GOOD_TEXTURE, {"compression": "TC_Default"}),
    "stream": (GOOD_TEXTURE, {"never_stream": False}),
    "texture_group": (GOOD_TEXTURE, {"lod_group": "TEXTUREGROUP_Pixels2D"}),
    "material": (GOOD_SPRITE, {"material": "/Paper2D/DefaultLitSpriteMaterial"}),
    "collision": (GOOD_SPRITE, {"collision": "Use3DPhysics"}),
    "atlas": (GOOD_SPRITE, {"atlas_group": "/Game/UmbrellaElla/Art/AG_Ella"}),
    "pivot": (GOOD_SPRITE, {"pivot_mode": "Top_Left"}),
    "geometry": (GOOD_SPRITE, {"render_geometry": "SourceBoundingBox", "width": 512}),
    "socket": (GOOD_SPRITE, {"sockets": []}),
    "fps": (GOOD_FLIPBOOK, {"fps": 15}),
    "frames": (GOOD_FLIPBOOK, {"keyframes": kf(*range(9))}),
    "dump": ({"class": "Blueprint", "name": "BP_Ella"}, {}),
}


class ImportReportTests(unittest.TestCase):
    def test_clean_dump_has_no_errors(self):
        frame1 = dict(GOOD_SPRITE, name="SPR_Ella_IdleFloat_01")
        self.assertEqual(sprite_check.check_import_report([GOOD_TEXTURE, GOOD_SPRITE, frame1, GOOD_FLIPBOOK], STYLE), [])

    def test_each_broken_rule_prints_one_error(self):
        for rule, (base, change) in BREAKS.items():
            with self.subTest(rule=rule):
                f = sprite_check.check_import_report([dict(base, **change)], STYLE)
                self.assertEqual(len(f), 1, f)
                self.assertTrue(f[0].startswith(rule + ":"), f)

    def test_fixture_breaking_every_rule_prints_one_error_per_rule(self):
        # each broken sprite is its own anim, so the shared-pivot rule does not fire twice
        dump = [dict(base, **change, **({"name": f"SPR_Ella_Case{i}_00"} if base is GOOD_SPRITE else {}))
                for i, (base, change) in enumerate(BREAKS.values())]
        rules = sorted(f.split(":")[0] for f in sprite_check.check_import_report(dump, STYLE))
        self.assertEqual(rules, sorted(BREAKS), rules)

    def test_frames_of_one_anim_share_a_pivot(self):
        a = dict(GOOD_SPRITE, name="SPR_Enemy_IdleFloat_00", sockets=[])
        b = dict(a, name="SPR_Enemy_IdleFloat_01", pivot_mode="Custom", pivot=[64, 120])
        f = sprite_check.check_import_report([a, b], STYLE)
        self.assertTrue(len(f) == 1 and "share one pivot" in f[0], f)

    def test_empty_dump_fails(self):
        self.assertTrue(sprite_check.check_import_report([], STYLE)[0].startswith("dump:"))

    def test_anchor_dump_passes_and_one_nearest_texture_fails(self):
        dump = json.load(open(ANCHORS))
        self.assertEqual(sprite_check.check_import_report(dump, STYLE), [])
        for a in dump:
            if a["class"] == "Texture2D":
                a["filter"] = "TF_Nearest"
                break
        f = sprite_check.check_import_report(dump, STYLE)
        self.assertEqual([x.split(":")[0] for x in f], ["filter"], f)

    # pivot across anims (critic: idle Bottom_Center vs Open Center_Center passed)
    def test_required_pivot_per_asset(self):
        f = sprite_check.check_import_report([dict(GOOD_SPRITE, name="SPR_Ella_Open_00", pivot_mode="Center_Center")], STYLE)
        self.assertTrue(len(f) == 1 and "Bottom_Center" in f[0], f)
        f = sprite_check.check_import_report([dict(GOOD_SPRITE, name="SPR_Shot_Fly_00", sockets=[], pivot_mode="Bottom_Center")], STYLE)
        self.assertTrue(len(f) == 1 and "Center_Center" in f[0], f)

    def test_pivot_shared_across_anims_of_one_asset(self):
        a = dict(GOOD_SPRITE, name="SPR_Enemy_Idle_00", sockets=[], pivot_mode="Custom", pivot=[64, 120])
        b = dict(a, name="SPR_Enemy_Hit_00", pivot=[64, 100])
        f = sprite_check.check_import_report([a, b], STYLE)
        self.assertTrue(len(f) == 1 and "across anims" in f[0], f)
        self.assertEqual(sprite_check.check_import_report([a, dict(a, name="SPR_Enemy_Hit_00")], STYLE), [])

    # material by kind
    def test_silhouette_on_translucent_fails_fx_passes(self):
        f = sprite_check.check_import_report([dict(GOOD_SPRITE, material=TRANSLUCENT)], STYLE)
        self.assertTrue(len(f) == 1 and f[0].startswith("material:"), f)
        fx = dict(GOOD_SPRITE, name="SPR_FXShot_Glow_00", sockets=[], pivot_mode="Center_Center", material=TRANSLUCENT)
        self.assertEqual(sprite_check.check_import_report([fx], STYLE), [])
        self.assertEqual(sprite_check.check_import_report([dict(fx, name="SPR_Spark_Glow_00", kind="fx")], STYLE), [])
        self.assertEqual(len(sprite_check.check_import_report([dict(fx, kind="silhouette")], STYLE)), 1)

    # flipbook keyframes
    def test_keyframes_out_of_order_fail(self):
        f = sprite_check.check_import_report([dict(GOOD_FLIPBOOK, keyframes=kf(0, 2, 1, 3))], STYLE)
        self.assertTrue(len(f) == 1 and "out of order" in f[0], f)

    def test_order_any_allows_ping_pong(self):
        style = json.loads(json.dumps(STYLE))
        style["anims"]["IdleFloat"]["order"] = "any"
        self.assertEqual(sprite_check.check_import_report([dict(GOOD_FLIPBOOK, keyframes=kf(0, 1, 2, 3, 2, 1))], style), [])

    def test_duplicate_adjacent_keyframe_fails_hold_passes(self):
        f = sprite_check.check_import_report([dict(GOOD_FLIPBOOK, keyframes=kf(0, 1, 1, 2, 3))], STYLE)
        self.assertTrue(len(f) == 1 and "frame_run" in f[0], f)
        held = kf(0, 1, 2, 3)
        held[1]["frame_run"] = 2
        self.assertEqual(sprite_check.check_import_report([dict(GOOD_FLIPBOOK, keyframes=held)], STYLE), [])

    def test_keyframe_from_another_anim_fails(self):
        f = sprite_check.check_import_report([dict(GOOD_FLIPBOOK, keyframes=kf(0, 1, 2) + kf(3, anim="Open"))], STYLE)
        self.assertTrue(len(f) == 1 and "not a SPR_Ella_IdleFloat_NN" in f[0], f)

    def test_keyframes_as_a_count_fail(self):
        f = sprite_check.check_import_report([dict(GOOD_FLIPBOOK, keyframes=4)], STYLE)
        self.assertTrue(len(f) == 1 and "must be a list" in f[0], f)

    def test_frame_budget_counts_unique_sprites(self):
        style = json.loads(json.dumps(STYLE))
        style["unreal_import"]["flipbook"]["frames_total_max"] = 7
        two = [GOOD_FLIPBOOK, dict(GOOD_FLIPBOOK, name="FB_Flyer_IdleFloat", keyframes=kf(0, 1, 2, 3, asset="Flyer"))]
        f = sprite_check.check_import_report(two, style)
        self.assertTrue(len(f) == 1 and "jam cap is 7" in f[0], f)
        self.assertEqual(sprite_check.check_import_report([GOOD_FLIPBOOK, GOOD_FLIPBOOK], style), [])

    # pixels per unit
    def test_mixed_pixels_per_unit_fails(self):
        a = dict(GOOD_SPRITE, pixels_per_unit=1.0)
        b = dict(GOOD_SPRITE, name="SPR_Ella_IdleFloat_01", pixels_per_unit=0.5)
        f = sprite_check.check_import_report([a, b], STYLE)
        self.assertTrue(len(f) == 1 and f[0].startswith("ppu:"), f)
        self.assertEqual(sprite_check.check_import_report([a, dict(a, name="SPR_Ella_IdleFloat_01")], STYLE), [])

    def test_pixels_per_unit_must_match_project_value(self):
        style = json.loads(json.dumps(STYLE))
        style["unreal_import"]["pixels_per_unit"] = 1.0
        self.assertEqual(sprite_check.check_import_report([dict(GOOD_SPRITE, pixels_per_unit=1.0)], style), [])
        f = sprite_check.check_import_report([dict(GOOD_SPRITE, pixels_per_unit=2.0)], style)
        self.assertTrue(len(f) == 1 and f[0].startswith("ppu:"), f)

    def test_mips_rule_follows_d13(self):
        style = json.loads(json.dumps(STYLE))
        style["unreal_import"]["texture"]["mips"] = "mips"
        f = sprite_check.check_import_report([dict(GOOD_TEXTURE, width=500)], style)
        self.assertEqual([x.split(":")[0] for x in f], ["mips", "mips"], f)
        style["unreal_import"]["texture"]["mips"] = "none"
        self.assertEqual(sprite_check.check_import_report([GOOD_TEXTURE], style), [])

    def test_cli(self):
        d = tempfile.mkdtemp()
        p = os.path.join(d, "dump.json")
        with open(p, "w") as fh:
            json.dump([dict(GOOD_TEXTURE, filter="TF_Nearest")], fh)
        with redirect_stdout(io.StringIO()):
            self.assertEqual(sprite_check.main(["--import-report", p]), 1)
        with open(p, "w") as fh:
            json.dump([GOOD_TEXTURE], fh)
        with redirect_stdout(io.StringIO()):
            self.assertEqual(sprite_check.main(["--import-report", p]), 0)


GOOD_EDITOR_INI = """[/Script/Paper2DEditor.PaperImporterSettings]
DefaultSpriteTextureGroup=TEXTUREGROUP_World
bOverrideTextureCompression=True
DefaultSpriteTextureCompression=TC_EditorIcon
UnlitDefaultMaskedMaterialName=/Paper2D/MaskedUnlitSpriteMaterial.MaskedUnlitSpriteMaterial
UnlitDefaultTranslucentMaterialName=/Paper2D/TranslucentUnlitSpriteMaterial.TranslucentUnlitSpriteMaterial
bPickBestMaterialWhenCreatingSprites=False
DefaultPixelsPerUnrealUnit=1.0
"""
GOOD_ENGINE_INI = """[/Script/Paper2D.PaperRuntimeSettings]
bEnableSpriteAtlasGroups=False
bResizeSpriteDataToMatchTextures=True
"""


class ConfigTests(unittest.TestCase):
    def cfg(self, editor=GOOD_EDITOR_INI, engine=GOOD_ENGINE_INI):
        d = tempfile.mkdtemp()
        for name, text in (("DefaultEditor.ini", editor), ("DefaultEngine.ini", engine)):
            if text is not None:
                with open(os.path.join(d, name), "w") as fh:
                    fh.write(text)
        return sprite_check.check_config(d, STYLE)

    def test_good_config_passes(self):
        self.assertEqual(self.cfg(), [])

    def test_each_broken_key_fails(self):
        cases = {
            "pixels group": GOOD_EDITOR_INI.replace("TEXTUREGROUP_World", "TEXTUREGROUP_Pixels2D"),
            "no override": GOOD_EDITOR_INI.replace("bOverrideTextureCompression=True", "bOverrideTextureCompression=False"),
            "wrong masked": GOOD_EDITOR_INI.replace("/Paper2D/MaskedUnlit", "/Paper2D/DefaultLit"),
            "scan unset": GOOD_EDITOR_INI.replace("bPickBestMaterialWhenCreatingSprites=False\n", ""),
            "ppu unset": GOOD_EDITOR_INI.replace("DefaultPixelsPerUnrealUnit=1.0\n", ""),
        }
        for name, text in cases.items():
            with self.subTest(case=name):
                self.assertEqual(len(self.cfg(editor=text)), 1)
        self.assertEqual(len(self.cfg(engine=GOOD_ENGINE_INI.replace("Groups=False", "Groups=True"))), 1)
        self.assertEqual(len(self.cfg(engine=GOOD_ENGINE_INI.replace("Textures=True", "Textures=False"))), 1)
        self.assertEqual(self.cfg(engine=None), ["config: DefaultEngine.ini missing"])

    def test_ppu_must_equal_style_value_once_set(self):
        style = json.loads(json.dumps(STYLE))
        style["unreal_import"]["pixels_per_unit"] = 1
        d = tempfile.mkdtemp()
        for name, text in (("DefaultEditor.ini", GOOD_EDITOR_INI), ("DefaultEngine.ini", GOOD_ENGINE_INI)):
            with open(os.path.join(d, name), "w") as fh:
                fh.write(text)
        self.assertEqual(sprite_check.check_config(d, style), [])
        style["unreal_import"]["pixels_per_unit"] = 2
        f = sprite_check.check_config(d, style)
        self.assertTrue(len(f) == 1 and "DefaultPixelsPerUnrealUnit" in f[0], f)

    def test_cli_skips_until_config_exists(self):
        with redirect_stdout(io.StringIO()):
            self.assertEqual(sprite_check.main(["--config", os.path.join(tempfile.mkdtemp(), "Config")]), 0)


class UprojectTests(unittest.TestCase):
    def write(self, plugins):
        p = os.path.join(tempfile.mkdtemp(), "UmbrellaElla.uproject")
        with open(p, "w") as fh:
            json.dump({"FileVersion": 3, "EngineAssociation": "5.8", "Plugins": plugins}, fh)
        return p

    def test_paper2d_enabled_passes(self):
        self.assertEqual(sprite_check.check_uproject(self.write([{"Name": "Paper2D", "Enabled": True}]), STYLE), [])

    def test_missing_disabled_or_paperzd_fails(self):
        for plugins in ([], [{"Name": "Paper2D", "Enabled": False}],
                        [{"Name": "Paper2D", "Enabled": True}, {"Name": "PaperZD", "Enabled": True}]):
            with self.subTest(plugins=plugins):
                self.assertEqual(len(sprite_check.check_uproject(self.write(plugins), STYLE)), 1)

    def test_cli(self):
        with redirect_stdout(io.StringIO()):
            self.assertEqual(sprite_check.main(["--uproject", self.write([])]), 1)
            self.assertEqual(sprite_check.main(["--uproject", self.write([{"Name": "Paper2D", "Enabled": True}])]), 0)
            missing = os.path.join(tempfile.mkdtemp(), "UmbrellaElla.uproject")
            self.assertEqual(sprite_check.main(["--uproject", missing]), 0)
            self.assertEqual(sprite_check.main(["--uproject", missing, "--require-dir"]), 1)


class WidthRatioTests(unittest.TestCase):
    def write(self, name, frames, sidecar=True):
        d = tempfile.mkdtemp()
        p = os.path.join(d, name + ".png")
        rows = sheet(frames)
        write_png(p, len(rows[0]), len(rows), rows)
        if sidecar:
            with open(os.path.join(d, name + ".sprite.json"), "w") as fh:
                json.dump({"kind": "silhouette", "grid": [64, 64], "frames": len(frames)}, fh)
        return p

    def test_wide_open_vs_narrow_closed_passes(self):
        o = self.write("SPR_Ella_IdleFloat", [blob(rx=28, ry=20), blob(rx=29, ry=20)])  # 56-58 px wide
        c = self.write("SPR_Ella_Closed", [blob(rx=12, ry=26), blob(rx=13, ry=26)])  # 24-26 px wide
        f, ratio = sprite_check.check_width_ratio(o, c, STYLE)
        self.assertEqual(f, [])
        self.assertGreaterEqual(ratio, 1.8)

    def test_too_similar_widths_fail(self):
        o = self.write("SPR_Ella_IdleFloat", [blob(rx=24, ry=20)])  # 48 px
        c = self.write("SPR_Ella_Closed", [blob(rx=16, ry=26)])  # 32 px: 1.5x
        f, ratio = sprite_check.check_width_ratio(o, c, STYLE)
        self.assertTrue(len(f) == 1 and f[0].startswith("width:"), f)
        self.assertLess(ratio, 1.8)

    def test_one_wide_closed_frame_fails(self):
        # the widest closed frame counts: one frame where the umbrella flares open breaks the read
        o = self.write("SPR_Ella_IdleFloat", [blob(rx=28, ry=20)])
        c = self.write("SPR_Ella_Closed", [blob(rx=12, ry=26), blob(rx=20, ry=26)])
        self.assertEqual(len(sprite_check.check_width_ratio(o, c, STYLE)[0]), 1)

    def test_cli(self):
        o = self.write("SPR_Ella_IdleFloat", [blob(rx=28, ry=20)], sidecar=False)
        c = self.write("SPR_Ella_Closed", [blob(rx=12, ry=26)], sidecar=False)
        with redirect_stdout(io.StringIO()):
            self.assertEqual(sprite_check.main(["--width-ratio", o, c]), 0)
            self.assertEqual(sprite_check.main(["--width-ratio", c, o]), 1)


# Card 0.4a removes 7 [VERIFY] tags from the Unreal rules: pipeline/unreal-rules.md plus pipeline/unreal/*.md
# (17 "VERIFY" strings across those files before 0.4a, counting the one in the core's intro line; the 17th is the feature-flag asset and subsystem, GDD B).
UNREAL_RULES_VERIFY_BEFORE_04A = 18   # +1: workbench switch (D-new-workbench-debug)


def unreal_rules_verify_count(root):
    """'VERIFY' count across the core Unreal rules and its on-demand files."""
    paths = [os.path.join(root, "pipeline", "unreal-rules.md")] + sorted(
        glob.glob(os.path.join(root, "pipeline", "unreal", "*.md")))
    return sum(open(p).read().count("VERIFY") for p in paths)


def import_names_unverified_after_04a(unreal_rules_verify, status, import_rules_verify):
    """Problems once card 0.4a is done (unreal-rules.md VERIFY count dropped by 7 or more)."""
    if unreal_rules_verify > UNREAL_RULES_VERIFY_BEFORE_04A - 7:
        return []
    out = []
    if status != "verified":
        out.append(f"style.json unreal_import.status is {status!r}, card 0.4a is done: paste the 5.8.4 names and set 'verified'")
    if import_rules_verify:
        out.append(f"pipeline/art/import-rules.md still has {import_rules_verify} VERIFY tags after card 0.4a")
    return out


class ImportNamesVerifiedTests(unittest.TestCase):
    def test_repo(self):
        count = lambda rel: open(os.path.join(ROOT, rel)).read().count("VERIFY")
        self.assertEqual(import_names_unverified_after_04a(unreal_rules_verify_count(ROOT),
                                                           REAL_STYLE["unreal_import"]["status"],
                                                           count("pipeline/art/import-rules.md")), [])

    def test_count_spans_core_and_on_demand_files(self):
        # A new tag raises the baseline here; a split that loses a file would drop the count unnoticed.
        self.assertLessEqual(unreal_rules_verify_count(ROOT), UNREAL_RULES_VERIFY_BEFORE_04A)
        self.assertGreater(len(glob.glob(os.path.join(ROOT, "pipeline", "unreal", "*.md"))), 0)

    def test_rule(self):
        self.assertEqual(import_names_unverified_after_04a(UNREAL_RULES_VERIFY_BEFORE_04A, "proposed", 5), [])  # before 0.4a
        self.assertEqual(len(import_names_unverified_after_04a(UNREAL_RULES_VERIFY_BEFORE_04A - 7, "proposed", 5)), 2)  # 0.4a done, nothing pasted
        self.assertEqual(len(import_names_unverified_after_04a(5, "verified", 1)), 1)
        self.assertEqual(import_names_unverified_after_04a(5, "verified", 0), [])


def gate_style(**tex):
    st = json.loads(json.dumps(STYLE))
    st["unreal_import"]["status"] = "verified"
    # the fixture's group stands in for the D-new-art-texgroup value
    st["unreal_import"]["texture"].update({"mips": "none", "lod_group": "TEXTUREGROUP_World"}, **tex)
    return st


def envelope(assets):
    return {"tool": sprite_check.DUMP_TOOL, "root": sprite_check.DUMP_ROOT, "assets": assets}


class GridAndGateTests(unittest.TestCase):
    """import-rules.md section 2: frames sit on the sidecar grid; a gate needs the script's dump."""

    def anchors(self):
        return json.load(open(ANCHORS))

    def first(self, dump, name):
        return next(a for a in dump if a["name"] == name)

    def test_anchor_frames_sit_on_their_grid(self):
        self.assertEqual([f for f in sprite_check.check_import_report(self.anchors(), STYLE) if f.startswith("grid")], [])

    def test_frame_cut_off_grid_fails_once(self):
        for change in ({"source_uv": [130, 0]}, {"source_size": [120, 128]}, {"source_uv": None}):
            with self.subTest(change=change):
                dump = self.anchors()
                self.first(dump, "SPR_Ella_IdleFloat_02").update(change)
                f = sprite_check.check_import_report(dump, STYLE)
                self.assertEqual([x.split(":")[0] for x in f], ["grid"], f)

    def test_texture_without_sheet_grid_fails(self):
        dump = self.anchors()
        del self.first(dump, "T_Ella_Open")["sheet"]
        f = sprite_check.check_import_report(dump, STYLE)
        self.assertEqual(len(f), 3, f)  # one per Open frame
        self.assertTrue(all(x.startswith("grid: T_Ella_Open") for x in f), f)

    def test_frame_index_past_the_sheet_fails(self):
        dump = self.anchors()
        self.first(dump, "SPR_Ella_Open_02")["name"] = "SPR_Ella_Open_04"  # 512 px sheet has cells 00-03
        f = [x for x in sprite_check.check_import_report(dump, STYLE) if x.startswith("grid")]
        self.assertTrue(len(f) == 1 and "no cell 04" in f[0], f)

    def test_margin_and_spacing_move_the_cells(self):
        self.assertEqual(sprite_check.frame_rect(5, 2 * 4 + 3 * 64 + 2 * 2, 2 * 4 + 2 * 64 + 2, (64, 64), 4, 2), (136, 70))  # col 2, row 1
        self.assertIsNone(sprite_check.frame_rect(6, 204, 138, (64, 64), 4, 2))

    def test_gate_passes_only_on_the_script_dump_with_names_verified_and_d13_set(self):
        self.assertEqual(sprite_check.check_import_report(envelope(self.anchors()), gate_style(), gate=True), [])
        f = sprite_check.check_import_report(self.anchors(), gate_style(), gate=True)  # hand dump: bare list
        self.assertEqual([x.split(":")[0] for x in f], ["gate"], f)
        f = sprite_check.check_import_report(dict(envelope(self.anchors()), root="/Game/UmbrellaElla/Art/Ella"),
                                             gate_style(), gate=True)
        self.assertEqual([x.split(":")[0] for x in f], ["gate"], f)
        st = gate_style()
        st["unreal_import"]["status"] = "proposed"
        self.assertEqual(len(sprite_check.check_import_report(envelope(self.anchors()), st, gate=True)), 1)
        st = gate_style(mips=None)
        f = sprite_check.check_import_report(envelope(self.anchors()), st, gate=True)
        self.assertEqual([x.split(":")[0] for x in f], ["mips"], f)

    def test_gate_needs_each_frame_texture_in_the_dump(self):
        dump = [a for a in self.anchors() if a["name"] != "T_Flyer_Flap"]
        self.assertEqual([f for f in sprite_check.check_import_report(dump, STYLE) if f.startswith("grid")], [])
        f = sprite_check.check_import_report(envelope(dump), gate_style(), gate=True)
        self.assertEqual(len(f), 4, f)
        self.assertTrue(all(x.startswith("grid") for x in f), f)

    def test_gate_with_one_nearest_texture_gives_one_error(self):
        dump = self.anchors()
        self.first(dump, "T_Ella_IdleFloat")["filter"] = "TF_Nearest"
        f = sprite_check.check_import_report(envelope(dump), gate_style(), gate=True)
        self.assertEqual([x.split(":")[0] for x in f], ["filter"], f)

    def test_cli_gate(self):
        tmp = tempfile.mkdtemp()
        dump = os.path.join(tmp, "dump.json")
        with open(dump, "w") as fh:
            json.dump(envelope(self.anchors()), fh)
        sp = os.path.join(tmp, "style.json")
        with open(sp, "w") as fh:
            json.dump(gate_style(), fh)
        with redirect_stdout(io.StringIO()):
            self.assertEqual(sprite_check.main(["--import-report", dump, "--gate", "--style", sp]), 0)
            self.assertEqual(sprite_check.main(["--import-report", ANCHORS, "--gate", "--style", sp]), 1)
            self.assertEqual(sprite_check.main(["--import-report", ANCHORS]), 0)


def socket_sprite(name, loc):
    return dict(GOOD_SPRITE, name=name, sockets=[{"name": "Muzzle", "location": loc}])


class SocketTests(unittest.TestCase):
    """A socket keeps its place on every frame of one anim (asset-brief: same on every frame)."""

    def test_steady_socket_passes(self):
        dump = [socket_sprite("SPR_Ella_IdleFloat_00", [70, 40]), socket_sprite("SPR_Ella_IdleFloat_01", [71, 41])]
        self.assertEqual(sprite_check.check_import_report(dump, STYLE), [])

    def test_socket_jumping_between_frames_fails_once(self):
        dump = [socket_sprite("SPR_Ella_IdleFloat_00", [70, 40]), socket_sprite("SPR_Ella_IdleFloat_01", [70, 40]),
                socket_sprite("SPR_Ella_IdleFloat_02", [74, 40])]
        f = sprite_check.check_import_report(dump, STYLE)
        self.assertTrue(len(f) == 1 and f[0].startswith("socket:") and "moves 4 px" in f[0], f)

    def test_socket_may_differ_between_anims(self):
        dump = [socket_sprite("SPR_Ella_IdleFloat_00", [70, 40]), socket_sprite("SPR_Ella_Open_00", [64, 6])]
        self.assertEqual(sprite_check.check_import_report(dump, STYLE), [])

    def test_name_only_socket_fails(self):
        f = sprite_check.check_import_report([dict(GOOD_SPRITE, sockets=["Muzzle"])], STYLE)
        self.assertTrue(len(f) == 1 and "location" in f[0], f)

    def test_anchor_fixture_socket_jump_fails(self):
        with open(ANCHORS) as fh:
            dump = json.load(fh)
        next(a for a in dump if a["name"] == "SPR_Ella_Open_01")["sockets"][0]["location"] = [64, 12]
        f = sprite_check.check_import_report(dump, STYLE)
        self.assertEqual([x.split(":")[0] for x in f], ["socket"], f)


class TextureGroupTests(unittest.TestCase):
    """Once D-new-art-texgroup sets unreal_import.texture.lod_group, World and other groups fail."""

    def style(self, group):
        st = json.loads(json.dumps(STYLE))
        st["unreal_import"]["texture"]["lod_group"] = group
        return st

    def test_null_group_only_bans_pixels2d(self):
        self.assertEqual(sprite_check.check_import_report([GOOD_TEXTURE], self.style(None)), [])

    def test_set_group_must_match(self):
        st = self.style("TEXTUREGROUP_UI")
        self.assertEqual(sprite_check.check_import_report([dict(GOOD_TEXTURE, lod_group="TEXTUREGROUP_UI")], st), [])
        f = sprite_check.check_import_report([GOOD_TEXTURE], st)  # World
        self.assertTrue(len(f) == 1 and f[0].startswith("texture_group:"), f)

    def test_gate_fails_while_group_is_open(self):
        with open(ANCHORS) as fh:
            dump = json.load(fh)
        f = sprite_check.check_import_report(envelope(dump), gate_style(lod_group=None), gate=True)
        self.assertEqual([x.split(":")[0] for x in f], ["texture_group"], f)

    def test_config_group_must_match_once_set(self):
        d = tempfile.mkdtemp()
        with open(os.path.join(d, "DefaultEditor.ini"), "w") as fh:
            fh.write(GOOD_EDITOR_INI)
        with open(os.path.join(d, "DefaultEngine.ini"), "w") as fh:
            fh.write(GOOD_ENGINE_INI)
        self.assertEqual(sprite_check.check_config(d, self.style(None)), [])
        current = [ln for ln in GOOD_EDITOR_INI.splitlines() if ln.startswith("DefaultSpriteTextureGroup=")][0]
        group = current.split("=", 1)[1]
        self.assertEqual(sprite_check.check_config(d, self.style(group)), [])
        f = sprite_check.check_config(d, self.style("TEXTUREGROUP_Other"))
        self.assertTrue(len(f) == 1 and "DefaultSpriteTextureGroup" in f[0], f)


def import_rules_04d_problems(text):
    """The card 0.4d done-when in import-rules.md covers the items the critic asked for."""
    m = re.search(r"### Card 0\.4d done-when.*?(?=\n### |\Z)", text, re.S)
    if not m:
        return ["import-rules.md has no 'Card 0.4d done-when' section"]
    block = m.group(0)
    need = {"grep count": "grep -c VERIFY pipeline/art/import-rules.md", "status": "unreal_import.status",
            "naming token": "Naming Template", "padding fallback": "rename", "socket": "location",
            "texture group": "lod_group"}
    return [f"0.4d done-when lacks {k} ({v!r})" for k, v in need.items() if v not in block]


class Card04dDoneWhenTests(unittest.TestCase):
    def test_repo(self):
        self.assertEqual(import_rules_04d_problems(open(os.path.join(ROOT, "pipeline", "art", "import-rules.md")).read()), [])

    def test_rule(self):
        self.assertEqual(len(import_rules_04d_problems("no section")), 1)
        good = ("### Card 0.4d done-when\n- grep -c VERIFY pipeline/art/import-rules.md prints 0, unreal_import.status "
                "verified, Naming Template, rename, location, lod_group\n")
        self.assertEqual(import_rules_04d_problems(good), [])
        self.assertEqual(len(import_rules_04d_problems(good.replace("rename", "x"))), 1)


STYLE_FRAME_MAP = os.path.join(ROOT, "Content", "UmbrellaElla", "Maps", "L_StyleFrame.umap")


def mips_open_after_style_frame(style_frame_exists, mips):
    """Card 0.10 imports the first art: from then on the mips rule must be on (D13 or its default)."""
    if style_frame_exists and mips is None:
        return ["style.json unreal_import.texture.mips is null but card 0.10 has started (L_StyleFrame exists); "
                "set it from D13, or its default"]
    return []


class MipsDecidedTests(unittest.TestCase):
    def test_repo(self):
        self.assertEqual(mips_open_after_style_frame(os.path.exists(STYLE_FRAME_MAP),
                                                     REAL_STYLE["unreal_import"]["texture"]["mips"]), [])

    def test_rule(self):
        self.assertEqual(mips_open_after_style_frame(False, None), [])
        self.assertEqual(len(mips_open_after_style_frame(True, None)), 1)
        self.assertEqual(mips_open_after_style_frame(True, "none"), [])


if __name__ == "__main__":
    unittest.main()
