"""tools/art_loop.py and tools/art_ref_check.py: art work does not stop until it reaches the bar the references set.

The loop's exit is the bar (the blind critic cannot pick the reference over ours AND the deterministic checks pass),
never a round count; the critic works blind, in a folder with only X.png, Y.png and a fixed prompt. Broken on
purpose: a loop that stops on a round count, a critic prompt that carries the builder's side, a number-score verdict,
and art_ref_check evidence for a card with no references."""
import io
import json
import os
import shutil
import sys
import tempfile
import unittest
from contextlib import redirect_stdout

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, os.path.join(ROOT, "tools"))
sys.path.insert(0, HERE)
import art_judge  # noqa: E402
import hermetic  # noqa: E402
import art_loop  # noqa: E402
import art_ref_check  # noqa: E402
from png import write_png  # noqa: E402

KEYART = os.path.join(ROOT, "pipeline", "art", "reference", "target-keyart.png")


def rnd(verdict, checks, score):
    return {"verdict": verdict, "checks": checks, "score": score}


class Decide(unittest.TestCase):
    def test_passes_only_at_the_bar(self):
        self.assertEqual(art_loop.decide([rnd("same", True, 0.6)]), "pass")
        self.assertEqual(art_loop.decide([rnd("ours", True, 0.6)]), "pass")
        self.assertEqual(art_loop.decide([rnd("same", False, 0.6)]), "continue")       # critic ok, checks fail
        self.assertEqual(art_loop.decide([rnd("reference", True, 0.9)]), "continue")   # checks ok, critic prefers ref

    def test_no_round_cap_while_it_improves(self):
        """Broken on purpose if someone adds a round cap: 60 rounds that keep improving never stop the loop."""
        hist = [rnd("reference", False, 0.1 + i * 0.01) for i in range(60)]
        self.assertEqual(art_loop.decide(hist), "continue")
        self.assertEqual(art_loop.decide(hist + [rnd("same", True, 0.8)]), "pass")

    def test_stuck_after_three_rounds_without_improvement(self):
        hist = [rnd("reference", False, 0.4), rnd("reference", False, 0.5)]
        self.assertEqual(art_loop.decide(hist + [rnd("reference", False, 0.5)] * 2), "continue")
        self.assertEqual(art_loop.decide(hist + [rnd("reference", False, 0.45)] * 3), "stuck")
        # any improvement resets the count
        flat = hist + [rnd("reference", False, 0.5)] * 2 + [rnd("reference", True, 0.5)] + [rnd("reference", True, 0.5)] * 2
        self.assertEqual(art_loop.decide(flat), "continue")

    def test_a_new_gap_each_round_is_not_stuck(self):
        """D-new-no-round-cap: stuck means the same gap and no better score 3 rounds in a row. Broken on purpose: the
        critic names a different gap each round, so the loop keeps going; the same gap three times escalates."""
        base = [dict(rnd("reference", False, 0.5), gap="flat paper")]
        moving = base + [dict(rnd("reference", False, 0.5), gap=f"gap {i}") for i in range(6)]
        self.assertEqual(art_loop.decide(moving), "continue")
        same = base + [dict(rnd("reference", False, 0.5), gap="Flat paper.")] * 3
        self.assertEqual(art_loop.decide(same), "stuck")

    def test_run_piece_has_no_round_count_exit(self):
        """The driver keeps going for as long as rounds improve; it stops at the bar on round 25."""
        n = {"i": 0}
        seen = []

        def build(gap):
            n["i"] += 1
            return f"ours-{n['i']}.png"

        def checks(f):
            return n["i"] >= 25, n["i"] / 100.0, []

        def critic(pair):
            seen.append(pair)
            return "WINNER: SAME\nGAP: none" if n["i"] >= 25 else "WINNER: Y\nGAP: line weight too even"

        state, hist = art_loop.run_piece(build, critic, checks, lambda f: ("pair", {"ours": "X"}), lambda r: None)
        self.assertEqual((state, len(hist)), ("pass", 25))

    def test_run_piece_sends_the_gap_back_and_never_the_builder_side_to_the_critic(self):
        gaps, got = [], []

        def build(gap):
            gaps.append(gap)
            return "ours.png"

        def critic(*args):
            got.append(args)   # the critic gets the folder only
            return "WINNER: X\nGAP: paper texture missing"

        state, hist = art_loop.run_piece(build, critic, lambda f: (False, 0.2, []),
                                         lambda f: ("/tmp/pair", {"ours": "Y"}), lambda r: None)
        self.assertEqual(state, "stuck")
        self.assertTrue(all(a == ("/tmp/pair",) for a in got))
        self.assertIn("paper texture missing", gaps[1])


class QualityBar(unittest.TestCase):
    def test_a_round_passes_only_when_the_quality_bar_does_not_win_either(self):
        """Josh, 11 Nov: the quality-bar images are the top tier; ours vs the reference alone is not enough."""
        n = {"i": 0}
        answers = {"ref": "WINNER: SAME\nGAP: none", "bar": "WINNER: X\nGAP: no light spill on the bolt core"}

        def critic(pair):
            return answers[pair]

        def make_pair(f):
            n["i"] += 1
            if n["i"] >= 4:
                answers["bar"] = "WINNER: SAME\nGAP: none"
            return [("ref", {"ours": "X"}), ("bar", {"ours": "Y"})]   # X wins the bar pair: the quality bar wins

        gaps = []

        def build(gap):
            gaps.append(gap)
            return "ours.png"

        state, hist = art_loop.run_piece(build, critic, lambda f: (True, 0.5 + n["i"] / 100, []), make_pair,
                                         lambda r: None)
        self.assertEqual(state, "pass")
        self.assertEqual([r["verdict"] for r in hist], ["reference", "reference", "reference", "same"])
        self.assertIn("no light spill on the bolt core", gaps[1])

    @unittest.skipIf(hermetic.refs_left_out(), hermetic.LEFT_OUT)
    def test_every_piece_has_a_quality_bar_pair(self):
        refs = art_judge.load_refs()
        tmp = tempfile.mkdtemp()
        ours = os.path.join(tmp, "o.png")
        write_png(ours, 4, 4, [[(9, 9, 9, 255)] * 4 for _ in range(4)])
        for piece in ("wind-zone", "owl-bolt", "scene"):
            key = art_loop.blind(refs, "0.10c" if piece == "wind-zone" else "0.10", piece, ours,
                                 os.path.join(tmp, piece), seed=1, quality=True)
            with open(key) as fh:
                self.assertIn("bar-" if False else "discord/20261111-", json.load(fh)["reference"])


@unittest.skipIf(hermetic.refs_left_out(), hermetic.LEFT_OUT)
class Blind(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.mkdtemp()
        self.refs = art_judge.load_refs()
        self.ours = os.path.join(self.tmp, "mine.png")
        write_png(self.ours, 8, 8, [[(30, 20, 15, 255)] * 8 for _ in range(8)])

    def test_critic_folder_is_blind_and_keyed_outside(self):
        orders = set()
        for seed in range(8):
            d = os.path.join(self.tmp, f"pair{seed}")
            key = art_loop.blind(self.refs, "0.10b", "owl", self.ours, d, seed=seed)
            self.assertEqual(sorted(os.listdir(d)), ["A", "B", "C", "prompt.md"])   # the pair among 2 calibration pairs
            for f in "ABC":
                self.assertEqual(sorted(os.listdir(os.path.join(d, f))), ["X.png", "Y.png"])
            self.assertFalse(key.startswith(d + os.sep))
            with open(key) as fh:
                k = json.load(fh)
            orders.add(k["ours"])
            self.assertEqual(sorted(list(k["calibration"]) + [k["folder"]]), ["A", "B", "C"])
            self.assertIn("SAME", k["calibration"].values())
            with open(os.path.join(d, "prompt.md")) as fh:
                self.assertEqual(art_loop.critic_prompt_problems(fh.read()), [])
        self.assertEqual(orders, {"X", "Y"})   # the order is random

    def test_menu_pieces_carry_the_written_menu_target_and_no_film_frame(self):
        refs = self.refs
        self.assertIn("menu-screen", art_loop.pieces(refs, "0.21b"))
        d = os.path.join(self.tmp, "menu")
        art_loop.blind(refs, "0.21b", "menu-screen", self.ours, d, seed=2)
        with open(os.path.join(d, "prompt.md")) as fh:
            prompt = fh.read()
        self.assertIn("paper cut-out silhouettes", prompt)
        self.assertIn("stop-motion-like motion", prompt)
        bar = art_judge.refs_by_id(refs)["menu-style-bar"]
        self.assertIsNone(bar["path"])   # described only: no image of the film is stored
        self.assertEqual(art_loop.critic_prompt_problems(prompt.split("\nThe style target for this piece")[0]), [])

    def test_a_critic_prompt_with_the_builder_side_is_refused(self):
        """Broken on purpose: a prompt that tells the critic the round, which image is ours, or the builder's notes."""
        base = art_loop.critic_prompt("the owl")
        for leak in ("This is round 3.", "X.png is ours.", "Y is the reference image.", "Previous attempt was worse."):
            with self.subTest(leak=leak):
                self.assertTrue(art_loop.critic_prompt_problems(base + leak))
        notes = "I darkened the wings and moved the clock up"
        self.assertTrue(art_loop.critic_prompt_problems(base + notes, builder_text=notes))
        self.assertTrue(art_loop.critic_prompt_problems(base + "Compare owl_v3.png too"))

    def test_verdict_is_binary(self):
        self.assertEqual(art_loop.read_verdict("WINNER: x\nGAP: flat paper"), ("X", "flat paper"))
        for bad in ("WINNER: X\nScore: 7/10", "X is better, 8/10", "WINNER: X\nWINNER: Y", "score: 6"):
            with self.subTest(bad=bad):
                with self.assertRaises(ValueError):
                    art_loop.read_verdict(bad)
        self.assertEqual(art_loop.outcome("SAME", {"ours": "X"}), "same")
        self.assertEqual(art_loop.outcome("Y", {"ours": "X"}), "reference")


class Evidence(unittest.TestCase):
    def test_pass_lines_need_this_commit_and_these_references(self):
        tmp = tempfile.mkdtemp()
        os.makedirs(os.path.join(tmp, "pipeline", "art"))
        shutil.copy(art_judge.REFS, os.path.join(tmp, "pipeline", "art", "references.json"))
        shutil.copy(os.path.join(ROOT, "pipeline", "day0-cards.md"), os.path.join(tmp, "pipeline"))
        refs, rh = art_loop.refs_and_hash(tmp)
        pieces = art_loop.pieces(refs, "0.10c")
        self.assertTrue({"skyline", "wand-shot", "wind-lines", "wind-zone"} <= set(pieces))   # the piece list grows
        commit = art_loop.head(tmp)
        for p in pieces:
            art_loop.log_round(tmp, "0.10c", p, {"round": 1, "verdict": "reference", "gap": "g", "checks": True,
                                                  "score": 0.4, "file": "f"}, rh, commit)
        lines, missing = art_loop.evidence(tmp, "0.10c")
        self.assertEqual(set(missing), set(pieces))
        for p in pieces:
            art_loop.log_round(tmp, "0.10c", p, {"round": 2, "verdict": "same", "gap": "", "checks": True,
                                                  "score": 0.7, "file": "f"}, rh, commit)
        lines, missing = art_loop.evidence(tmp, "0.10c")
        self.assertEqual(missing, [])
        self.assertTrue(all(f"refs={rh} commit={commit}" in ln for ln in lines))
        with open(os.path.join(tmp, "pipeline", "art", "references.json"), "a") as fh:
            fh.write("\n")   # a changed reference set voids the evidence
        self.assertEqual(set(art_loop.evidence(tmp, "0.10c")[1]), set(pieces))


class ArtRefCheck(unittest.TestCase):
    def test_key_art_passes_for_the_style_frame_card_with_the_refs_hash(self):
        rc, out = art_ref_check.run("0.10", scene_shot=KEYART, commit="abc1234")
        self.assertEqual(rc, 0, out)
        smin = art_judge.load_refs()["scene"]["similarity_min"]   # calibrated leave-one-out (0.732 on 11 Nov)
        self.assertIn(f"art_ref_check: PASS card=0.10 target=scene score=1.0 min={smin} refs={art_judge.refs_hash()} "
                      "commit=abc1234", out[-1])

    def test_card_without_references_and_wrong_element_are_refused(self):
        self.assertEqual(art_ref_check.run("0.5", scene_shot=KEYART)[0], 2)          # not an art card
        self.assertEqual(art_ref_check.run("0.10c", element_id="owl", files=[KEYART])[0], 2)   # not its refs

    def test_flat_teal_wind_zone_fails_against_its_references(self):
        tmp = tempfile.mkdtemp()
        p = os.path.join(tmp, "wind.png")
        write_png(p, 144, 112, [[(42, 157, 143, 255)] * 144 for _ in range(112)])
        rc, out = art_ref_check.run("0.10c", element_id="wind-zone", files=[p], commit="abc1234")
        self.assertEqual(rc, 1, out)
        self.assertTrue(out[-1].startswith("art_ref_check: FAIL card=0.10c target=element:wind-zone"))

    def test_cli(self):
        out = io.StringIO()
        with redirect_stdout(out):
            rc = art_ref_check.main(["--card", "0.10", "--scene", KEYART, "--commit", "abc1234"])
        self.assertEqual(rc, 0, out.getvalue())


class ReferenceAssignments(unittest.TestCase):
    @unittest.skipIf(hermetic.refs_left_out(), hermetic.LEFT_OUT)
    def test_every_art_card_has_references_and_runs_the_checks(self):
        self.assertEqual(art_judge.coverage(art_judge.load_refs()), [])

    def test_unassigned_art_card_and_missing_file_fail(self):
        """Broken on purpose: drop the 0.10c assignments, and point one reference at a file that is not there."""
        import copy
        refs = copy.deepcopy(art_judge.load_refs())
        for r in refs["references"]:
            r["cards"] = [c for c in r["cards"] if c != "0.10c"] or ["MVP 12"]
        self.assertIn("art card 0.10c (its lane makes or places art) has no reference assigned in references.json",
                      art_judge.coverage(refs))
        refs = copy.deepcopy(art_judge.load_refs())
        refs["references"][1]["path"] = "pipeline/art/reference/gone.png"
        self.assertTrue(any("missing on disk" in p for p in art_judge.coverage(refs)))


if __name__ == "__main__":
    unittest.main()


class PacketGroundFlattens(unittest.TestCase):
    """Critic packets show every image on one paper ground (Nov 12 critic defect: transparent sprites shown on black)."""

    def setUp(self):
        import tempfile
        self.d = tempfile.mkdtemp()
        sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "tools"))

    def test_opaque_png_is_returned_unchanged(self):
        import art_loop
        from png import write_png
        f = os.path.join(self.d, "opaque.png")
        write_png(f, 1, 1, [[(1, 2, 3, 255)]])
        self.assertEqual(art_loop.flatten_on_ground(f), f)

    def test_transparent_png_is_composited_onto_the_ground(self):
        import art_loop
        from png import read_png, write_png
        f = os.path.join(self.d, "clear.png")
        write_png(f, 2, 1, [[(0, 0, 0, 0), (10, 20, 30, 255)]])
        _, _, rows = read_png(art_loop.flatten_on_ground(f))
        pw, ph, paper = art_loop.packet_paper()
        self.assertEqual(rows[0][0], paper[0][0])
        self.assertEqual(rows[0][1], (10, 20, 30, 255))
        self.assertTrue(all(px[3] == 255 for px in rows[0]))

    def test_transparent_entry_shows_textured_paper_not_one_flat_colour(self):
        import art_loop
        from png import read_png, write_png
        f = os.path.join(self.d, "empty.png")
        write_png(f, 64, 64, [[(0, 0, 0, 0)] * 64 for _ in range(64)])
        _, _, rows = read_png(art_loop.flatten_on_ground(f))
        colours = {px for row in rows for px in row}
        self.assertGreater(len(colours), 1)
