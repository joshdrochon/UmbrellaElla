"""The reference bar is enforced, not advised (Josh, 11 Nov). Shipped art (an image under Art/ outside Art/Source/)
reaches main and the package only with a passing art-loop record for its exact bytes: the blind critic picked ours or
SAME against a reference AND the quality bar (and, for a sheet, the whole sheet in motion), and art_check,
screen_check and art_ref_check passed. Each gate fails once on purpose here: tools/check_pr.py rule artship,
tools/submission_check.py art, tools/art_loop.py (the record, the motion pair, the measured checks, the placeholder
refusal, no override). Blender's command line and the render plan are in tests/test_assetgen.py and below."""
import csv
import json
import os
import shutil
import sys
import tempfile
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, os.path.join(ROOT, "tools"))
sys.path.insert(0, os.path.join(ROOT, "pipeline", "art", "blender"))
sys.path.insert(0, HERE)
import art_judge  # noqa: E402
import art_loop  # noqa: E402
import check_pr  # noqa: E402
import hermetic  # noqa: E402
import plan  # noqa: E402
import submission_check  # noqa: E402
from png import write_png  # noqa: E402

PROV = ["asset_path", "author", "origin", "tool", "model_version", "prompt", "seed", "input_images", "date", "licence",
        "attribution"]
HEADER = "commit=abc1234 engine=5.8.4 config=Development host=win run=packaged\n"


def ink(w, h, shift=0):
    return [[((20 + (x + y + shift) % 7), 18, 16, 255) if (x - w / 2) ** 2 + (y - h / 2) ** 2 < (w / 3) ** 2
             else (0, 0, 0, 0) for x in range(w)] for y in range(h)]


_TEAM_FRAME = {}


def team_quality_frame():
    """One 640x512 frame cut from the team's owl sheet: art that clears the owl bar (a stand-in for a Blender render
    that reached it; not a byte copy of any reference file). Cached: the source sheet is large."""
    if "path" not in _TEAM_FRAME:
        from png import read_png
        w, h, rows = read_png(os.path.join(ROOT, "pipeline", "art", "reference", "Test_Assets",
                                           "CHR_Owl_Flap_Damage.png"))
        p = os.path.join(tempfile.mkdtemp(), "owl_frame.png")
        write_png(p, 640, 512, [r[:640] for r in rows[:512]])
        _TEAM_FRAME["path"] = p
    return _TEAM_FRAME["path"]


OWL_ORIGIN = ("rendered in jam; Blender 5.2.1 render from pipeline/art/blender; style targets for piece owl: owl-flap "
              "(reference only, never shipped)")


@unittest.skipIf(hermetic.refs_left_out(), hermetic.LEFT_OUT)
class ShipRepo(unittest.TestCase):
    """A repo with references.json, one owl frame that clears the bar under Art/Sprites/, its provenance row and an
    in-engine capture."""
    IMG = "Art/Sprites/Owl/owl_still.png"
    SHEET = "Art/Sprites/Owl/owl_flap.png"

    def setUp(self):
        self.root = tempfile.mkdtemp()
        self.addCleanup(shutil.rmtree, self.root, True)
        os.makedirs(os.path.join(self.root, "pipeline", "art"))
        shutil.copy(os.path.join(ROOT, "pipeline", "art", "references.json"),
                    os.path.join(self.root, "pipeline", "art", "references.json"))
        self.rh = art_judge.refs_hash(os.path.join(self.root, "pipeline", "art", "references.json"))
        os.makedirs(os.path.join(self.root, os.path.dirname(self.IMG)))
        shutil.copy(team_quality_frame(), os.path.join(self.root, self.IMG))
        self.prov(self.IMG, OWL_ORIGIN)
        self.capture = self.write("Saved/Logs/pipeline/smoke-L_Arena-shot.png", 16, 9)

    def write(self, rel, w, h, shift=0):
        full = os.path.join(self.root, rel)
        os.makedirs(os.path.dirname(full), exist_ok=True)
        write_png(full, w, h, ink(w, h, shift))
        return full

    def prov(self, rel, origin):
        p = os.path.join(self.root, "pipeline", "art", "provenance.csv")
        rows = []
        if os.path.isfile(p):
            with open(p, encoding="utf-8", newline="") as fh:
                rows = [r for r in csv.DictReader(fh) if r["asset_path"] != rel]
        rows.append(dict(asset_path=rel, author="asset-specialist", origin=origin, tool="Blender (headless scripts)",
                         model_version="Blender 5.2.1", prompt="owl", seed="11", input_images="", date="2026-11-12",
                         licence="GPL", attribution="none"))
        with open(p, "w", encoding="utf-8", newline="") as fh:
            w = csv.DictWriter(fh, PROV, lineterminator="\n")
            w.writeheader()
            w.writerows(rows)

    def record(self, rel, **over):
        full = os.path.join(self.root, rel)
        refs, _ = art_loop.refs_and_hash(self.root)
        judged = art_loop.element_refs(refs, "owl", self.root)
        rec = {"round": 3, "verdict": "same", "gap": "", "checks": True, "score": 0.9, "file": full,
               "pairs": {"reference": "same", "quality_bar": "ours", "context": "same"},
               "combos": [f"reference:{r}" for r in judged], "missing": [], "panel": art_loop.PANEL,
               "calibration": {"sessions": 15, "passed": 15}, "refs_judged": judged, "context": self.capture,
               "sessions": [f"critic-{i}" for i in range(15)],
               "results": {c: "pass" for c in art_loop.CHECKS}, "sheet": bool(art_loop.sheet_info(full))}
        if rec["sheet"]:
            rec["pairs"]["motion"] = "same"
        rec.update(over)
        return art_loop.write_record(self.root, "0.10b", "owl", rec, self.rh, "abc1234")
    def line(self, rel, sha=None, refs=None, commit="abc1234"):
        sha = sha or art_loop.content_sha(os.path.join(self.root, rel))
        return art_loop.pass_line("0.10b", "owl", "same", 3, refs or self.rh, commit, rel, sha,
                                  {"reference": "same", "quality_bar": "ours"}) + "\n"

    def ref_line(self):
        return (f"art_ref_check: PASS card=0.10b target=element:owl score=0.71 min=0.5 refs={self.rh} "
                "commit=abc1234 file=owl.png\n")

    def pr(self, ev, changed=None):
        sec = {"Task": "Part of #12. Card ID: UE-101  Owner role: Asset Specialist  Reviewer role: Art Director",
               "Evidence": HEADER + self.ref_line() + ev}
        return check_pr.artref_problems(sec, changed or [self.IMG], self.root)


class CheckPrArtship(ShipRepo):
    def test_a_judged_file_with_its_record_and_line_passes(self):
        self.assertIsNotNone(self.record(self.IMG))
        self.assertEqual(self.pr(self.line(self.IMG)), [])

    def test_broken_on_purpose_each_missing_piece_fails(self):
        self.record(self.IMG)
        cases = [("no art_loop line", "", "no `art_loop: PASS"),
                 ("a line for other bytes", self.line(self.IMG, sha="0" * 64), "never judged"),
                 ("an older reference set", self.line(self.IMG, refs="000000000000"), "loop again"),
                 ("another commit", self.line(self.IMG, commit="def5678"), "not abc1234")]
        for what, ev, want in cases:
            with self.subTest(what):
                found = self.pr(ev)
                self.assertTrue(any(want in p for p in found), found)

    def test_broken_on_purpose_the_record_must_show_the_whole_bar(self):
        for what, over, want in [
                ("no record", None, "no art-loop pass record"),
                ("the quality bar won", {"pairs": {"reference": "same", "quality_bar": "reference",
                                                   "context": "same"}}, None),
                ("no in-engine context", {"pairs": {"reference": "same", "quality_bar": "same"}}, None),
                ("a panel of one", {"panel": 1}, None),
                ("an uncalibrated critic", {"calibration": {"sessions": 15, "passed": 14}}, None),
                ("a lost pair still listed", {"missing": ["reference:x (2/3 calibrated sessions)"]}, None),
                ("art_check failed", {"results": {"art_check": "fail", "screen_check": "pass",
                                                  "art_ref_check": "pass"}}, None)]:
            with self.subTest(what):
                rp = art_loop.record_path(os.path.join(self.root, self.IMG))
                if os.path.exists(rp):
                    os.remove(rp)
                if over is not None:
                    self.assertIsNone(self.record(self.IMG, **over), "a failed round writes no record")
                found = self.pr(self.line(self.IMG))
                self.assertTrue(any("no art-loop pass record" in p for p in found), found)
        # a forged record (written by hand) that shows a lost pair or a failed check still fails
        self.record(self.IMG)
        rp = art_loop.record_path(os.path.join(self.root, self.IMG))
        data = json.load(open(rp))
        for key, val, want in [("pairs", {"reference": "same", "quality_bar": "reference", "context": "same"},
                                "quality_bar"),
                               ("pairs", {"reference": "same", "quality_bar": "same"}, "context"),
                               ("panel", 1, "not a panel of 3"),
                               ("calibration", {"sessions": 15, "passed": 13}, "not all calibrated"),
                               ("refs_judged", [], "did not judge every reference"),
                               ("checks", {"art_check": "pass", "screen_check": "fail", "art_ref_check": "pass"},
                                "screen_check"),
                               ("refs", "000000000000", "not the current")]:
            with self.subTest(forged=key):
                json.dump(dict(data, **{key: val}), open(rp, "w"))
                found = self.pr(self.line(self.IMG))
                self.assertTrue(any(want in p for p in found), found)
        json.dump(data, open(rp, "w"))
        self.assertEqual(self.pr(self.line(self.IMG)), [])

    def test_broken_on_purpose_new_bytes_after_the_pass_fail(self):
        self.record(self.IMG)
        old = self.line(self.IMG)
        self.write(self.IMG, 32, 32, shift=3)
        found = self.pr(old)
        self.assertTrue(any("changed after its art-loop pass" in p for p in found), found)
        self.assertTrue(any("never judged" in p for p in found), found)

    def test_broken_on_purpose_a_placeholder_never_passes(self):
        self.record(self.IMG)
        self.prov(self.IMG, "placeholder made in jam; no Blender")
        found = self.pr(self.line(self.IMG))
        self.assertTrue(any("placeholder" in p for p in found), found)
        self.assertIsNone(self.record(self.IMG), "the loop never writes a record for a placeholder")
        self.prov(self.IMG, "team reference art, source=reference (practice)")
        self.assertTrue(any("stand-in" in p or "practice" in p for p in self.pr(self.line(self.IMG))))

    def test_broken_on_purpose_no_sign_off_or_label_overrides_it(self):
        ev = ("Human sign-off: Josh approved this art, override the art bar\nLabels: needs-human, approved\n"
              "NEEDS HUMAN: resolved, art accepted by Rich\nart_loop: waived by producer\n")
        found = self.pr(ev)
        self.assertTrue(any("no `art_loop: PASS" in p for p in found), found)
        body = ("## Task\nPart of #12. Card ID: UE-101  Owner role: Asset Specialist  Reviewer role: Art Director\n"
                "## Evidence\n" + HEADER + self.ref_line() + ev)
        self.assertTrue(any("art_loop" in p for p in check_pr.problems(body, [self.IMG], root=self.root)))

    def test_a_sheet_also_needs_its_motion_pair(self):
        full = self.write(self.SHEET, 64, 16)
        self.prov(self.SHEET, "assembled in jam")
        with open(os.path.splitext(full)[0] + ".sprite.json", "w") as fh:
            json.dump({"kind": "silhouette", "grid": [16, 16], "frames": 4, "anim": "Flap", "fps": 10}, fh)
        self.assertIsNone(self.record(self.SHEET, pairs={"reference": "same", "quality_bar": "same",
                                                         "context": "same"}), "no motion verdict: no record")
        self.record(self.SHEET)
        json.dump(dict(json.load(open(art_loop.record_path(full))), pairs={"reference": "same",
                                                                           "quality_bar": "same", "context": "same"}),
                  open(art_loop.record_path(full), "w"))
        found = self.pr(self.line(self.SHEET), [self.SHEET])
        self.assertTrue(any("motion" in p for p in found), found)

    def test_an_engine_art_asset_needs_the_line_of_its_image(self):
        asset = "Content/UmbrellaElla/Art/Owl/T_Owl.uasset"
        found = self.pr("", [asset])
        self.assertTrue(any("ships art" in p for p in found), found)
        self.record(self.IMG)
        self.assertEqual(self.pr(self.line(self.IMG), [asset]), [])

    def test_visible_ui_art_ships_too_and_only_text_data_and_fonts_stay_out(self):
        for asset in ("Content/UmbrellaElla/UI/Menu/T_TitleBackground.uasset",
                      "Content/UmbrellaElla/UI/HUD/WBP_HUD.uasset"):
            with self.subTest(asset):   # broken on purpose: UI art without its image's pass line
                self.assertTrue(any("ships art" in p for p in self.pr("", [asset])), asset)
        for data in ("Content/UmbrellaElla/UI/Text/ST_UI_Strings.uasset", "Content/UmbrellaElla/UI/Fonts/F_Ink.uasset",
                     "Content/UmbrellaElla/UI/Data/DT_MenuItems.uasset"):
            with self.subTest(data):
                self.assertFalse(any("ships art" in p for p in self.pr("", [data])), data)

    def test_raw_renders_and_sources_are_not_shipped(self):
        for rel in ("Art/Source/Owl/Raw/Flap/Owl_Flap_00.png", "Art/Source/Owl/owl.psd", "pipeline/art/x.png"):
            self.assertFalse(art_loop.shipped(rel), rel)
        for rel in ("Art/Sprites/Owl/owl_flap.png", "Art/Backgrounds/skyline.png"):
            self.assertTrue(art_loop.shipped(rel), rel)


class ForgedRecords(ShipRepo):
    """Josh, 11 Nov: the gate never takes a record's word. It re-runs the deterministic checks on the shipped bytes,
    and no agent session can write or commit a record (hook, git_gate, art_loop itself)."""
    CRUDE = "Art/Sprites/Owl/owl_crude.png"

    def hand_written(self, rel, piece="owl", card="0.10b"):
        """A record an agent writes by hand: every field says pass, the sha is right."""
        full = os.path.join(self.root, rel)
        refs, _ = art_loop.refs_and_hash(self.root)
        data = {"file": rel, "sha256": art_loop.content_sha(full), "card": card, "piece": piece, "verdict": "ours",
                "pairs": {k: "ours" for k in art_loop.KINDS}, "panel": 3,
                "calibration": {"sessions": 33, "passed": 33}, "critic_sessions": ["a", "b", "c"],
                "refs_judged": art_loop.element_refs(refs, piece, self.root), "context": None,
                "checks": {c: "pass" for c in art_loop.CHECKS}, "rounds": 1, "refs": self.rh,
                "judged_commit": "abc1234", "at": "2026-11-12T00:00:00Z"}
        with open(art_loop.record_path(full), "w") as fh:
            json.dump(data, fh)

    def test_broken_on_purpose_a_hand_written_record_for_a_rough_render_fails(self):
        dst = os.path.join(self.root, self.CRUDE)
        shutil.copy(os.path.join(HERE, "fixtures", "art", "crude", "owl_flap_crude.png"), dst)
        self.prov(self.CRUDE, OWL_ORIGIN)
        self.hand_written(self.CRUDE)
        found = art_loop.record_problems(self.root, self.CRUDE, self.rh)
        self.assertTrue(any("re-run on the shipped file" in p and "art_ref_check" in p for p in found), found)
        self.assertTrue(any("re-run on the shipped file" in p for p in self.pr(self.line(self.CRUDE), [self.CRUDE])))
        self.assertTrue(any("re-run" in p for p in submission_check.art_loop_problems(self.root)))

    def test_broken_on_purpose_a_record_naming_an_easier_piece_fails(self):
        self.hand_written(self.IMG, piece="wand-shot")   # the lowest bar in references.json
        found = art_loop.record_problems(self.root, self.IMG, self.rh)
        self.assertTrue(any("provenance says 'owl'" in p for p in found), found)
        self.prov(self.IMG, "rendered in jam")            # provenance without the piece: the gate fails closed
        self.hand_written(self.IMG)
        self.assertTrue(any("names no judge piece" in p for p in art_loop.record_problems(self.root, self.IMG)))

    def test_the_genuine_record_names_its_critic_sessions(self):
        self.record(self.IMG)
        data = json.load(open(art_loop.record_path(os.path.join(self.root, self.IMG))))
        self.assertEqual(len(data["critic_sessions"]), 15)
        json.dump(dict(data, critic_sessions=[]), open(art_loop.record_path(os.path.join(self.root, self.IMG)), "w"))
        self.assertTrue(any("critic session" in p for p in art_loop.record_problems(self.root, self.IMG, self.rh)))

    def test_broken_on_purpose_an_agent_session_cannot_write_a_record(self):
        os.environ["JAM_ROLE"] = "asset-specialist"
        try:
            self.assertIsNone(self.record(self.IMG), "art_loop refuses inside an agent session")
        finally:
            del os.environ["JAM_ROLE"]
        self.assertIsNotNone(self.record(self.IMG), "kickoff's own process writes it")

    def test_broken_on_purpose_the_hook_and_git_refuse_agents(self):
        import subprocess
        hook = os.path.join(ROOT, "pipeline", "agent-ops", "hook.py")
        env = dict(os.environ, CLAUDE_PROJECT_DIR=self.root, JAM_ROLE="asset-specialist", AGENT_OPS_PLATFORM="linux")
        rec = os.path.join(self.root, "Art", "Sprites", "Owl", "owl_still.artloop.json")
        for tool, ti in (("Write", {"file_path": rec, "content": "{}"}),
                         ("Bash", {"command": "echo '{}' > Art/Sprites/Owl/owl_still.artloop.json"})):
            with self.subTest(tool=tool):
                p = subprocess.run([sys.executable, hook, "guard"], input=json.dumps(
                    {"hook_event_name": "PreToolUse", "tool_name": tool, "tool_input": ti, "cwd": self.root}),
                    capture_output=True, text=True, env=env)
                self.assertEqual(p.returncode, 2, p.stderr)
                self.assertIn("art-loop pass record", p.stderr)
        import git_gate
        gates = json.load(open(os.path.join(ROOT, "pipeline", "agent-ops", "gates.json")))
        ok, msg = git_gate.decide(["Art/Sprites/Owl/owl_still.artloop.json"], {"JAM_ROLE": "asset-specialist"}, gates)
        self.assertFalse(ok)
        self.assertIn("art-loop pass record", msg)
        self.assertTrue(git_gate.decide(["Art/Sprites/Owl/owl_still.artloop.json"], {}, gates)[0],
                        "kickoff commits it from its own process")


class SubmissionArt(ShipRepo):
    def test_package_fails_without_a_pass_and_passes_with_one(self):
        found = submission_check.art_loop_problems(self.root)
        self.assertTrue(any("no art-loop pass record" in p for p in found), found)
        self.record(self.IMG)
        self.assertEqual(submission_check.art_loop_problems(self.root), [])
        self.prov(self.IMG, "placeholder made in jam")   # broken on purpose: a placeholder in the package
        self.assertTrue(any("placeholder" in p for p in submission_check.art_loop_problems(self.root)))


@unittest.skipIf(hermetic.refs_left_out(), hermetic.LEFT_OUT)
class LoopMotionAndPanel(unittest.TestCase):
    """The critic judges single frames, the whole sheet in motion and the piece in an in-engine capture, as a panel of
    PANEL calibrated sessions per pair against every reference of the element and the quality bar; a round passes
    only when every session counted (all calibration right) and every pair is ours or SAME, and the measured checks
    pass."""

    def setUp(self):
        self.tmp = tempfile.mkdtemp()
        self.addCleanup(shutil.rmtree, self.tmp, True)
        self.refs = art_judge.load_refs()
        self.sheet = os.path.join(self.tmp, "owl_flap.png")
        frames = [ink(24, 24, i) for i in range(4)]
        write_png(self.sheet, 96, 24, [sum((f[y] for f in frames), []) for y in range(24)])
        with open(os.path.join(self.tmp, "owl_flap.sprite.json"), "w") as fh:
            json.dump({"kind": "silhouette", "grid": [24, 24], "frames": 4, "anim": "Flap", "fps": 10}, fh)

    def mine(self, d, key):
        from png import read_png
        return read_png(os.path.join(d, key["folder"], key["ours"] + ".png"))[:2]

    def test_motion_pair_shows_the_whole_sheet_with_a_leak_free_prompt(self):
        d = os.path.join(self.tmp, "m")
        key = json.load(open(art_loop.blind(self.refs, "0.10b", "owl", self.sheet, d, seed=1, kind="motion")))
        self.assertEqual(key["kind"], "motion")
        prompt = open(os.path.join(d, "prompt.md")).read()
        self.assertIn("animation sheet", prompt)
        self.assertEqual(art_loop.critic_prompt_problems(prompt), [])
        self.assertEqual(self.mine(d, key), (96, 24))
        d2 = os.path.join(self.tmp, "r")
        key = json.load(open(art_loop.blind(self.refs, "0.10b", "owl", self.sheet, d2, seed=1)))
        self.assertEqual(self.mine(d2, key), (24, 24), "one frame against the reference")
        single = os.path.join(self.tmp, "one.png")
        write_png(single, 8, 8, ink(8, 8))
        with self.assertRaises(ValueError):   # broken on purpose: a still has no motion pair
            art_loop.blind(self.refs, "0.10b", "owl", single, os.path.join(self.tmp, "x"), kind="motion")

    def panel_run(self, real_answer, cal_wrong=lambda n, key: False):
        """Drive run_piece with a stub critic: right on calibration unless cal_wrong(n, key); real_answer(n, key) gives
        X, Y or SAME for the judged folder (n = the round)."""
        n = {"i": 0}
        sessions = []
        cap = os.path.join(self.tmp, "smoke-shot.png")
        write_png(cap, 16, 9, ink(16, 9))
        for name, val in (("measure", lambda root, card, piece, f: (True, 0.9, [], {c: "pass" for c in
                                                                                     art_loop.CHECKS})),
                          ("find_capture", lambda root, ours: cap),
                          ("CAL_LOG", os.path.join(self.tmp, "cal.csv"))):
            orig = getattr(art_loop, name)
            setattr(art_loop, name, val)
            self.addCleanup(setattr, art_loop, name, orig)

        def make_pair(f):
            n["i"] += 1
            d = os.path.join(self.tmp, f"seed-{n['i']}")
            return [(d, json.load(open(art_loop.blind(self.refs, "0.10b", "owl", f, d, seed=n["i"]))))]

        def critic(d):
            key = json.load(open(d + ".key.json"))
            sessions.append(key)
            lines = [f"{f}: WINNER: {('X' if want != 'X' else 'Y') if cal_wrong(n['i'], key) else want} | GAP: -"
                     for f, want in key["calibration"].items()]
            lines.append(f"{key['folder']}: WINNER: {real_answer(n['i'], key)} | GAP: the pivot jitters")
            return "\n".join(lines)

        state, hist = art_loop.run_piece(lambda gap: self.sheet, critic, lambda f: (True, 0.5, []), make_pair,
                                         lambda r: None)
        return state, hist, sessions

    def test_panel_judges_every_reference_the_bar_motion_and_context_until_all_agree(self):
        def answer(rnd, key):
            if key["kind"] == "motion" and rnd < 3:   # the frames pop: the sheet in motion loses twice
                return "Y" if key["ours"] == "X" else "X"
            return "SAME"

        state, hist, sessions = self.panel_run(answer)
        self.assertEqual((state, len(hist)), ("pass", 3))
        refs = art_loop.element_refs(self.refs, "owl")
        last = [s for s in sessions if s["seed"] // 1000 == 3]
        judged = {s["reference"] for s in last if s["kind"] == "reference"}
        self.assertEqual(judged, set(refs), "every reference of the element, not one random one")
        kinds = {s["kind"] for s in last}
        self.assertEqual(kinds, {"reference", "quality_bar", "motion", "context"})
        per = {}
        for s in last:
            per[(s["kind"], s["reference"])] = per.get((s["kind"], s["reference"]), 0) + 1
        self.assertEqual(set(per.values()), {art_loop.PANEL}, "three fresh sessions per pair")
        self.assertEqual(hist[0]["pairs"]["motion"], "reference")
        self.assertIn("pivot jitters", hist[0]["gap"])
        self.assertEqual(hist[-1]["calibration"]["passed"], hist[-1]["calibration"]["sessions"])
        self.assertEqual(hist[-1]["panel"], art_loop.PANEL)

    def test_broken_on_purpose_one_dissenting_critic_or_one_uncalibrated_session_blocks_the_round(self):
        def one_no(rnd, key):   # one of three sessions on the quality bar prefers the bar, every round
            return ("Y" if key["ours"] == "X" else "X") if key["kind"] == "quality_bar" and key["seed"] % 10 == 0 \
                else "SAME"

        state, hist, _ = self.panel_run(one_no)
        self.assertEqual(state, "stuck")
        self.assertTrue(all(h["pairs"]["quality_bar"] == "reference" for h in hist))
        state, hist, _ = self.panel_run(lambda rnd, key: "SAME",
                                        cal_wrong=lambda rnd, key: key["kind"] == "reference" and key["seed"] % 10 == 1)
        self.assertEqual(state, "stuck", "a session that misses calibration does not count: 2 of 3 is not a panel")
        self.assertTrue(any("2/3 calibrated sessions" in m for m in hist[-1]["missing"]), hist[-1]["missing"])
        self.assertLess(hist[-1]["calibration"]["passed"], hist[-1]["calibration"]["sessions"])

    def test_broken_on_purpose_no_in_engine_capture_no_pass(self):
        orig = art_loop.find_capture
        art_loop.find_capture = lambda root, ours: None
        self.addCleanup(setattr, art_loop, "find_capture", orig)
        req = art_loop.required_pairs(self.refs, "owl", self.sheet)
        self.assertIn(("context", art_loop.context_ref(self.refs), None), req)
        folders, missing = art_loop.panel_folders(self.refs, "0.10b", "owl", self.sheet, self.tmp, 1)
        self.assertTrue(missing and "in-engine capture" in missing[0])
        self.assertFalse([k for _, k in folders if k["kind"] == "context"])

    def test_judge_refuses_a_session_that_misses_calibration_and_logs_agreement_rows(self):
        d = os.path.join(self.tmp, "j")
        key = json.load(open(art_loop.blind(self.refs, "0.10b", "owl", self.sheet, d, seed=4)))
        good = "\n".join([f"{f}: WINNER: {w} | GAP: -" for f, w in key["calibration"].items()] +
                         [f"{key['folder']}: WINNER: SAME | GAP: none"])
        orig = art_loop.CAL_LOG
        art_loop.CAL_LOG = os.path.join(self.tmp, "cal.csv")
        self.addCleanup(setattr, art_loop, "CAL_LOG", orig)
        self.assertEqual(art_loop.judge(good, key, self.tmp, "s1"), ("SAME", "none"))
        crude = [f for f, w in key["calibration"].items() if w != "SAME"][0]
        flipped = good.replace(f"{crude}: WINNER: {key['calibration'][crude]}",
                               f"{crude}: WINNER: {'Y' if key['calibration'][crude] == 'X' else 'X'}")
        with self.assertRaises(ValueError):   # the crude render beat the team art: the session does not count
            art_loop.judge(flipped, key, self.tmp, "s2")
        with self.assertRaises(ValueError):   # a folder left out
            art_loop.judge(good.split("\n", 1)[1], key, self.tmp, "s3")
        rows = list(csv.DictReader(open(os.path.join(self.tmp, "cal.csv"))))
        header = open(os.path.join(ROOT, "evals", "art-judge", "agreement.csv")).readline().strip().split(",")
        self.assertEqual(list(rows[0]), header)
        self.assertIn("WRONG: session does not count", [r["note"] for r in rows])

    def test_a_round_missing_a_kind_or_a_measured_check_never_passes(self):
        base = {"verdict": "same", "checks": True, "score": 0.9, "sheet": True}
        self.assertEqual(art_loop.decide([dict(base, pairs={"reference": "same", "quality_bar": "same"})]),
                         "continue", "a sheet without its motion verdict")
        self.assertEqual(art_loop.decide([dict(base, pairs={"reference": "same", "motion": "same"})]), "continue")
        self.assertEqual(art_loop.decide([dict(base, pairs={"reference": "same", "quality_bar": "same",
                                                            "motion": "ours"})]), "pass")
        stuck = [dict(base, verdict="reference", checks=False, score=0.2, gap="flat", pairs={})] * 4
        self.assertEqual(art_loop.decide(stuck), "stuck", "stuck asks for help; it never passes")

    def test_placeholder_is_measured_as_a_failure(self):
        root = tempfile.mkdtemp()
        self.addCleanup(shutil.rmtree, root, True)
        f = os.path.join(root, "Art", "Sprites", "o.png")
        os.makedirs(os.path.dirname(f))
        write_png(f, 8, 8, ink(8, 8))
        os.makedirs(os.path.join(root, "pipeline", "art"))
        with open(os.path.join(root, "pipeline", "art", "provenance.csv"), "w") as fh:
            fh.write(",".join(PROV) + "\nArt/Sprites/o.png,a,placeholder made in jam,Blender,none,,,,2026-11-12,GPL,none\n")
        ok, _, lines, results = art_loop.measure(root, "0.10b", "owl", f)
        self.assertFalse(ok)
        self.assertIn("placeholder", lines[0])

    def test_no_override_flag_exists(self):
        with self.assertRaises(SystemExit):
            art_loop.main(["verdict", "--pair", "p", "--critic", "c", "--card", "0.10b", "--piece", "owl",
                           "--approve"])


class BlenderPlan(unittest.TestCase):
    def test_job_takes_size_pivot_and_fps_from_the_layout_and_the_art_bible(self):
        j = plan.job("owl", "Flap", "Art/Source/Owl/Raw/Flap")
        lay = json.load(open(os.path.join(ROOT, "pipeline", "art", "reference", "Test_Assets", "SpriteLayout.json")))
        self.assertEqual(j["frame_size"], lay["CHR_Owl_Flap_Damage.png"]["frame_size"])
        self.assertEqual(j["pivot_px"], [float(v) for v in lay["CHR_Owl_Flap_Damage.png"]["pivot_px"]])
        self.assertEqual((j["faces"], j["fps"], len(j["frames"])), ("left", 10, 6))
        self.assertEqual(j["frames"][0], "Art/Source/Owl/Raw/Flap/Owl_Flap_00.png")
        self.assertEqual(len({json.dumps(j["look"])}), 1)
        loop = plan.interpolate([{"t": 0, "rot": {"a": 0}}, {"t": 0.5, "rot": {"a": 10}}], 4, True)
        self.assertEqual([p["rot"]["a"] for p in loop], [0, 5, 10, 5], "a loop wraps back to its first key")

    def test_command_line_is_headless_factory_and_job_only(self):
        argv = plan.blender_argv(["blender"], "/x/job.json")
        self.assertEqual(argv[:4], ["blender", "-b", "--factory-startup", "-P"])
        self.assertTrue(argv[4].endswith(os.path.join("pipeline", "art", "blender", "render_sprite.py")))
        self.assertEqual(argv[5:], ["--", "--job", "/x/job.json"])
        m = plan.RENDER_LINE.search("BLENDER_RENDER version=5.2.1 frames=6 blend=a.blend freestyle=on compositor=on")
        self.assertEqual((m.group("version"), m.group("freestyle")), ("5.2.1", "on"))

    def test_broken_on_purpose_rows_the_art_bible_forbids(self):
        with self.assertRaises(ValueError):
            plan.job("ella", "Attack", "Raw", frames=8)    # attack is 3-4 frames
        with self.assertRaises(ValueError):
            plan.job("ella", "Swim", "Raw")
        with self.assertRaises(ValueError):
            plan.job("dragon", "Flap", "Raw")


if __name__ == "__main__":
    unittest.main()
