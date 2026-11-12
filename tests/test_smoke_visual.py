"""The smoke's automatic visual checks (tools/ue_run.py smoke-log): a 16:9 gameplay view on SMOKE_OK (view=/aspect=),
debug draws off by default (debugdraw=0), and art_check / screen_check / art_judge scene on the hook's own screenshot.

Each case is run through the smoke-log CLI the smoke scripts call, with a fake log and a synthetic or reference
screenshot. The teammate's first build is the break-on-purpose set: a ~1.85:1 window with the gameplay not locked,
hitbox draws on, and a flat teal wind box."""
import io
import os
import shutil
import subprocess
import sys
import tempfile
import unittest
from contextlib import redirect_stdout

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, os.path.join(ROOT, "tools"))
import ue_run  # noqa: E402

FAKE_SHOT = os.path.join(HERE, "fixtures", "fake_shot.py")
KEYART = os.path.join(ROOT, "pipeline", "art", "reference", "target-keyart.png")
LINE = ("LogUmbrellaElla: SMOKE_OK map={map} fps=60 worst_ms=20 commit=abc1234 input={inp} input_vz=-120 gamepad=ok gp_vx=150 gp_attack_vz=-200 gp_shield_vz=-180 res={res} "
        "win=windowed view={view} aspect={aspect} debugdraw={dd} textpx=20 load_ms=800 workbench=0\n")


def have_keyart():
    with open(KEYART, "rb") as fh:
        return fh.read(8) == b"\x89PNG\r\n\x1a\n"


class SmokeVisual(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.mkdtemp()

    def root(self, anchors):
        """A repo root with the real art config; anchors=True ends the art bootstrap (card 0.10b merged)."""
        r = os.path.join(self.tmp, "anchors" if anchors else "boot")
        if not os.path.isdir(r):
            os.makedirs(os.path.join(r, "pipeline", "art"))
            for f in ("style.json", "references.json"):
                shutil.copy(os.path.join(ROOT, "pipeline", "art", f), os.path.join(r, "pipeline", "art", f))
            if anchors:
                os.makedirs(os.path.join(r, ue_run.ART_ANCHORS))
        return r

    def shot(self, name, w, h, *flags):
        p = os.path.join(self.tmp, name + ".png")
        subprocess.run([sys.executable, FAKE_SHOT, p, str(w), str(h), *flags], check=True)
        return p

    def smoke(self, root, shot, map_="L_StyleFrame", res="1920x1080", view="1920x1080", aspect="1.778", dd="0",
              shot_line=True, *extra):
        log = os.path.join(self.tmp, "game.log")
        with open(log, "w") as fh:
            fh.write(LINE.format(map=map_, inp="none" if map_ == "L_StyleFrame" else "ok", res=res, view=view,
                                 aspect=aspect, dd=dd))
            if shot_line:
                fh.write("LogUmbrellaElla: SMOKE_SHOT at_s=5 w=1920 h=1080\n")
        out = io.StringIO()
        args = ["--root", root, "smoke-log", log, "--exit-code", "0", "--no-player-maps", "L_StyleFrame",
                "--allow", os.path.join(ROOT, "tools", "ue", "smoke-allow.txt"), *extra]
        if shot:
            args += ["--shot", shot]
        with redirect_stdout(out):
            try:
                rc = ue_run.main(args)
            except SystemExit as e:
                rc = e.code
        return rc, out.getvalue()

    # --- 16:9 lock -------------------------------------------------------------------------------------------
    def test_letterbox_and_pillarbox_views_pass(self):
        root = self.root(True)
        for res, view, shot in (("1280x800", "1280x720", self.shot("l", 1280, 800)),
                                ("2560x1080", "1920x1080", self.shot("p", 2560, 1080))):
            with self.subTest(res=res):
                rc, out = self.smoke(root, shot, res=res, view=view)
                self.assertEqual(rc, 0, out)
                self.assertIn("smoke-art: screen_check: PASS", out)
                self.assertIn("bars=" + ("letterbox" if res == "1280x800" else "pillarbox"), out)

    def test_unlocked_ultrawide_fails_twice_over(self):
        """Broken on purpose: the teammate's ~1.85:1 window with the gameplay stretched to it."""
        root = self.root(True)
        shot = self.shot("wide", 1998, 1080, "--no-lock")
        rc, out = self.smoke(root, shot, res="1998x1080", view="1998x1080", aspect="1.850")
        self.assertEqual(rc, 1, out)
        self.assertIn("gameplay view 1998x1080 is 1.850:1, not 16:9", out)
        self.assertIn("smoke-art: screen_check: FAIL", out)
        self.assertIn("FIX: aspect: lock the gameplay view to 16:9", out)

    def test_view_fields_must_be_measured_and_consistent(self):
        root = self.root(False)
        shot = self.shot("ok", 1920, 1080)
        for kw, want in [({"view": "1920x1080", "aspect": "1.850"}, "disagrees with view"),
                         ({"res": "1280x800", "view": "1280x800", "aspect": "1.600"}, "not 16:9"),
                         ({"res": "1280x720", "view": "1920x1080"}, "bigger than the window"),
                         ({"res": "2560x1440", "view": "1280x720"}, "fills neither axis")]:
            with self.subTest(**kw):
                rc, out = self.smoke(root, shot, **kw)
                self.assertEqual(rc, 1, out)
                self.assertIn(want, out)

    # --- debug draws ------------------------------------------------------------------------------------------
    def test_debug_draw_on_by_default_fails(self):
        rc, out = self.smoke(self.root(False), self.shot("ok", 1920, 1080), dd="1")
        self.assertEqual(rc, 1, out)
        self.assertIn("SMOKE_OK debugdraw=1, expected 0", out)

    # --- art checks on the screenshot --------------------------------------------------------------------------
    def test_flat_teal_wind_box_fails_the_smoke(self):
        """Broken on purpose: WIND-01 drawn as a flat solid teal rectangle."""
        rc, out = self.smoke(self.root(True), self.shot("teal", 1920, 1080, "--flat-teal"))
        self.assertEqual(rc, 1, out)
        self.assertIn("smoke-art: screen_check: FAIL", out)
        self.assertIn("flat: x=", out)
        self.assertIn("FIX: flat: replace the flat fill with etched art", out)

    def test_no_screenshot_fails_once_the_anchors_exist(self):
        rc, out = self.smoke(self.root(True), None, shot_line=False)
        self.assertEqual(rc, 1, out)
        self.assertIn("no --shot screenshot", out)
        self.assertIn("no SMOKE_SHOT line", out)

    def test_art_bootstrap_prints_but_does_not_block(self):
        rc, out = self.smoke(self.root(False), self.shot("teal", 1920, 1080, "--flat-teal"))
        self.assertEqual(rc, 0, out)
        self.assertIn("smoke-art: screen_check: FAIL", out)
        self.assertIn("smoke-art: bootstrap: not blocking until Content/UmbrellaElla/Art/Anchors/ exists", out)
        kind = ue_run.not_checked_kind("art checks (no anchor art before card 0.10b; shot results not blocking)")
        self.assertEqual(kind, "art-bootstrap")

    def test_gate_refuses_the_art_bootstrap_from_g2(self):
        import check_card
        line = ("DAILY abc1234 | h | Development | smoke=PASS | Not checked: art checks (no anchor art before "
                "card 0.10b; shot results not blocking)")
        self.assertEqual(check_card.daily_switch_due(line, "G1"), [])
        self.assertTrue(check_card.daily_switch_due(line, "G2"))

    def test_no_player_map_skips_the_scene_judge(self):
        rc, out = self.smoke(self.root(True), self.shot("ok", 1920, 1080))
        self.assertEqual(rc, 0, out)
        self.assertIn("smoke-art: art_check: PASS", out)
        self.assertNotIn("art_judge", out)

    def test_gameplay_map_runs_the_key_art_judge(self):
        """A gameplay-map screenshot is judged against the key art: the synthetic frame (small round owl) FAILS."""
        rc, out = self.smoke(self.root(True), self.shot("ok", 1920, 1080), "L_Graybox")
        self.assertEqual(rc, 1, out)
        self.assertIn("smoke-art: art_judge: FAIL scene", out)
        self.assertIn("smoke-art: FIX: owl:", out)

    @unittest.skipUnless(have_keyart(), "key art is an LFS pointer here")
    def test_a_build_that_looks_like_the_key_art_passes(self):
        shot = os.path.join(self.tmp, "keyart-shot.png")
        shutil.copy(KEYART, shot)
        rc, out = self.smoke(self.root(True), shot, "L_Graybox", "1672x941", "1672x941", "1.777", "0", True,
                             "--min-text-px", "0")
        self.assertEqual(rc, 0, out)
        for tool in ("art_check", "screen_check", "art_judge"):
            self.assertIn(f"smoke-art: {tool}: PASS", out)


if __name__ == "__main__":
    unittest.main()
