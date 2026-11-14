import io
import json
import os
import shutil
import sys
import tempfile
import unittest
from contextlib import redirect_stdout
from unittest import mock

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, os.path.join(ROOT, "tools", "build"))
import visual_qa  # noqa: E402


def answer(scores=8, broken=(), verdict="PASS"):
    return json.dumps({"scores": {k: scores for k, _ in visual_qa.RUBRIC}, "broken": list(broken), "verdict": verdict})


def never_called(prompt, image):
    raise AssertionError("a live judge call was made")


class Parse(unittest.TestCase):
    def test_parses_a_full_answer_with_chatter_around_it(self):
        r = visual_qa.parse_answer("Here you go:\n" + answer(7) + "\nDone.")
        self.assertEqual(r["total"], 7 * len(visual_qa.RUBRIC))
        self.assertEqual(r["verdict"], "PASS")
        self.assertEqual(r["broken"], [])

    def test_rejects_missing_or_out_of_range_scores(self):
        bad = json.loads(answer())
        del bad["scores"]["wind_ribbons"]
        with self.assertRaises(ValueError):
            visual_qa.parse_answer(json.dumps(bad))
        bad = json.loads(answer())
        bad["scores"]["dark_backdrop"] = 11
        with self.assertRaises(ValueError):
            visual_qa.parse_answer(json.dumps(bad))
        with self.assertRaises(ValueError):
            visual_qa.parse_answer("no json here")
        with self.assertRaises(ValueError):
            visual_qa.parse_answer(answer(verdict="MAYBE"))


class Decide(unittest.TestCase):
    def test_broken_item_fails(self):
        ok, why = visual_qa.decide(visual_qa.parse_answer(answer(9, ["lilac placeholder cube"])))
        self.assertFalse(ok)
        self.assertIn("lilac", why[0])

    def test_worse_than_main_fails(self):
        r = visual_qa.parse_answer(answer(6))   # total 42
        self.assertEqual(visual_qa.BASELINE_SLACK, 0)   # the brief: any screen worse than main fails
        self.assertTrue(visual_qa.decide(r, 42)[0])
        self.assertFalse(visual_qa.decide(r, 43)[0])
        self.assertTrue(visual_qa.decide(r, None)[0])

    def test_judge_fail_verdict_fails(self):
        self.assertFalse(visual_qa.decide(visual_qa.parse_answer(answer(8, verdict="FAIL")))[0])


class RecordReplay(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.mkdtemp()
        self.replay_only = os.environ.pop("VISUAL_QA_REPLAY_ONLY", None)

    def tearDown(self):
        shutil.rmtree(self.tmp, ignore_errors=True)
        if self.replay_only is not None:
            os.environ["VISUAL_QA_REPLAY_ONLY"] = self.replay_only

    def test_second_identical_call_replays_without_spending(self):
        calls = []
        def caller(prompt, image):
            calls.append(1)
            return answer(5)
        a, replayed = visual_qa.judge_call("p", b"img", caller, self.tmp)
        self.assertFalse(replayed)
        b, replayed = visual_qa.judge_call("p", b"img", never_called, self.tmp)
        self.assertTrue(replayed)
        self.assertEqual(a, b)
        self.assertEqual(len(calls), 1)
        # A different picture is a different call.
        os.environ["VISUAL_QA_REPLAY_ONLY"] = "1"
        try:
            with self.assertRaises(RuntimeError):
                visual_qa.judge_call("p", b"other", never_called, self.tmp)
        finally:
            os.environ.pop("VISUAL_QA_REPLAY_ONLY", None)

    def test_judge_shots_summary_and_missing_capture(self):
        shots = os.path.join(self.tmp, "shots")
        os.makedirs(shots)
        study = os.path.join(ROOT, visual_qa.STUDY)
        for name in visual_qa.SCREENS.values():
            shutil.copyfile(study, os.path.join(shots, name))
        code, line, results = visual_qa.judge_shots(shots, lambda p, i: answer(8), os.path.join(self.tmp, "rec"))
        self.assertEqual(code, visual_qa.EXIT_PASS, line)
        self.assertTrue(line.startswith("VISUAL_QA PASS play=56/70"), line)
        base = {"sha": "abc", "screens": {"keeper": {"total": 70}}}
        code, line, _ = visual_qa.judge_shots(shots, never_called, os.path.join(self.tmp, "rec"), base)
        self.assertEqual(code, visual_qa.EXIT_FAIL, line)
        self.assertIn("failed=keeper", line)
        os.remove(os.path.join(shots, "vq_keeper.png"))
        code, line, _ = visual_qa.judge_shots(shots, never_called, os.path.join(self.tmp, "rec"))
        self.assertEqual(code, visual_qa.EXIT_ERROR)


class GateBaseline(unittest.TestCase):
    """16:28 / 16:45 reviews: the gate exits 2 when main's baseline is missing; a failing run never becomes a baseline."""

    def setUp(self):
        self.tmp = tempfile.mkdtemp()
        self.env = mock.patch.dict(os.environ, {"VISUAL_BASELINE_DIR": os.path.join(self.tmp, "base")})
        self.env.start()

    def tearDown(self):
        self.env.stop()
        shutil.rmtree(self.tmp, ignore_errors=True)

    def test_required_baseline_missing_exits_2_without_judging(self):
        with mock.patch.object(visual_qa, "judge_shots", side_effect=AssertionError("judged")):
            code = visual_qa.cmd_judge(self.tmp, never_called, require_baseline=True, sha="f" * 40)
        self.assertEqual(code, visual_qa.EXIT_ERROR)
        with mock.patch.object(visual_qa, "capture", side_effect=AssertionError("captured")):
            code = visual_qa.main(["run", "--out", self.tmp, "--require-baseline", "--main-sha", "f" * 40])
        self.assertEqual(code, visual_qa.EXIT_ERROR)

    def test_failing_run_is_not_stored_as_baseline(self):
        fail = (visual_qa.EXIT_FAIL, "VISUAL_QA FAIL play=10/70", {})
        with mock.patch.object(visual_qa, "judge_shots", return_value=fail):
            code = visual_qa.main(["baseline", "--shots", self.tmp, "--sha", "a" * 40])
        self.assertEqual(code, visual_qa.EXIT_FAIL)
        self.assertFalse(os.path.exists(os.path.join(self.tmp, "base", "a" * 40 + ".json")))
        ok = (visual_qa.EXIT_PASS, "VISUAL_QA PASS play=60/70", {})
        with mock.patch.object(visual_qa, "judge_shots", return_value=ok):
            self.assertEqual(visual_qa.main(["baseline", "--shots", self.tmp, "--sha", "a" * 40]), visual_qa.EXIT_PASS)
        self.assertTrue(os.path.exists(os.path.join(self.tmp, "base", "a" * 40 + ".json")))


class GateMode(unittest.TestCase):
    """Lead 17:32: --gate fails only on a regression against main's baseline; baseline --from-main bootstraps it."""

    def setUp(self):
        self.tmp = tempfile.mkdtemp()
        self.env = mock.patch.dict(os.environ, {"VISUAL_BASELINE_DIR": os.path.join(self.tmp, "base")})
        self.env.start()
        self.shots = os.path.join(self.tmp, "shots")
        os.makedirs(self.shots)
        study = os.path.join(ROOT, visual_qa.STUDY)
        for name in visual_qa.SCREENS.values():
            shutil.copyfile(study, os.path.join(self.shots, name))
        self.rec = os.path.join(self.tmp, "rec")

    def tearDown(self):
        self.env.stop()
        shutil.rmtree(self.tmp, ignore_errors=True)

    def base(self, total=42, broken=("Lilac placeholder cube on the route.",)):
        return {"sha": "m" * 40, "screens": {s: {"total": total, "broken": list(broken)} for s in visual_qa.SCREENS}}

    def test_decide_gate_regression_only(self):
        r = visual_qa.parse_answer(answer(6, ["lilac placeholder cube on the route"], verdict="FAIL"))   # total 42
        base = self.base()["screens"]["play"]
        self.assertEqual(visual_qa.decide_gate(r, base), (True, []))   # main's own broken item + judge FAIL: no regression
        self.assertFalse(visual_qa.decide(r, 42)[0])                   # the plain judge still fails it
        worse = visual_qa.parse_answer(answer(5, ["Lilac placeholder cube on the route"]))
        ok, why = visual_qa.decide_gate(worse, base)
        self.assertFalse(ok)
        self.assertIn("below main's 42", why[0])
        new = visual_qa.parse_answer(answer(9, ["cream bar at the bottom"]))
        ok, why = visual_qa.decide_gate(new, base)
        self.assertFalse(ok)
        self.assertEqual(why, ["new broken: cream bar at the bottom"])

    def test_norm_item_matches_case_and_punctuation(self):
        self.assertEqual(visual_qa.norm_item("  Lilac  placeholder-cube, on the ROUTE. "),
                         visual_qa.norm_item("lilac placeholder cube on the route"))

    def test_gate_judge_passes_main_level_frame_and_fails_regression(self):
        sha = "m" * 40
        visual_qa.store_baseline(sha, "x", self.base()["screens"])
        caller = lambda p, i: answer(6, ["lilac placeholder cube on the route"], verdict="FAIL")
        with mock.patch.object(visual_qa, "judge_call", side_effect=lambda p, i, c, r: (caller(p, i), False)):
            out = io.StringIO()
            with redirect_stdout(out):
                code = visual_qa.cmd_judge(self.shots, gate=True, sha=sha)
            self.assertEqual(code, visual_qa.EXIT_PASS, out.getvalue())
            self.assertTrue(out.getvalue().strip().splitlines()[-1].startswith("VISUAL_QA GATE PASS"))
        with mock.patch.object(visual_qa, "judge_call", side_effect=lambda p, i, c, r: (answer(5), False)):
            with redirect_stdout(io.StringIO()):
                self.assertEqual(visual_qa.cmd_judge(self.shots, gate=True, sha=sha), visual_qa.EXIT_FAIL)

    def test_gate_without_baseline_exits_2_before_capturing(self):
        with mock.patch.object(visual_qa, "capture", side_effect=AssertionError("captured")), \
                mock.patch.object(visual_qa, "_git", return_value=""), redirect_stdout(io.StringIO()) as out:
            code = visual_qa.main(["run", "--gate", "--out", self.shots, "--main-sha", "f" * 40])
        self.assertEqual(code, visual_qa.EXIT_ERROR)
        self.assertIn("baseline --from-main", out.getvalue())

    def test_ancestor_baseline_counts_only_without_frame_changes(self):
        anc, head = "a" * 40, "b" * 40
        visual_qa.store_baseline(anc, "x", {})
        def git(*args, docs_only=True):
            if args[0] == "rev-list":
                return head + "\n" + anc + "\n"
            return "" if docs_only else "Source/UmbrellaElla/Private/Feedback/X.cpp\n"
        with mock.patch.object(visual_qa, "_git", side_effect=git):
            self.assertIsNone(visual_qa.load_baseline(head))            # exact only without walk
            self.assertEqual(visual_qa.load_baseline(head, 5)["sha"], anc)
        with mock.patch.object(visual_qa, "_git", side_effect=lambda *a: git(*a, docs_only=False)):
            self.assertIsNone(visual_qa.load_baseline(head, 5))

    def test_from_main_stores_a_failing_main_run_once(self):
        sha = "c" * 40
        fail = lambda p, i: answer(3, ["lilac placeholder cube"], verdict="FAIL")
        with mock.patch.object(visual_qa, "_git", return_value=sha + "\n"), \
                mock.patch.object(visual_qa, "capture", return_value=0) as cap, redirect_stdout(io.StringIO()):
            self.assertEqual(visual_qa.cmd_baseline_from_main(self.shots, sha, fail, self.rec), visual_qa.EXIT_PASS)
            stored = visual_qa.load_baseline(sha)
            self.assertEqual(stored["screens"]["play"]["broken"], ["lilac placeholder cube"])
            self.assertEqual(visual_qa.cmd_baseline_from_main(self.shots, sha, never_called, self.rec), visual_qa.EXIT_PASS)
            self.assertEqual(cap.call_count, 1)                        # once per sha

    def test_from_main_with_shots_stores_the_gate_run_without_capturing(self):
        sha = "9" * 40
        with mock.patch.object(visual_qa, "capture", side_effect=AssertionError("captured")), \
                mock.patch.object(visual_qa, "_git", side_effect=AssertionError("checked HEAD")), redirect_stdout(io.StringIO()):
            code = visual_qa.cmd_baseline_from_main("", sha, lambda p, i: answer(4, ["x"], "FAIL"), self.rec, shots=self.shots)
        self.assertEqual(code, visual_qa.EXIT_PASS)
        self.assertEqual(visual_qa.load_baseline(sha)["screens"]["keeper"]["total"], 4 * len(visual_qa.RUBRIC))

    def test_from_main_refuses_a_checkout_not_at_main(self):
        with mock.patch.object(visual_qa, "_git", return_value="d" * 40 + "\n"), \
                mock.patch.object(visual_qa, "capture", side_effect=AssertionError("captured")), \
                redirect_stdout(io.StringIO()):
            self.assertEqual(visual_qa.cmd_baseline_from_main(self.shots, "e" * 40), visual_qa.EXIT_ERROR)
        self.assertFalse(os.path.exists(visual_qa.baseline_path("e" * 40)))


class GateScript(unittest.TestCase):
    """gate.sh calls the gate mode against main's sha, never records exit 2 against the lane, and stores its own run
    as the new main's baseline only after the push."""

    def test_gate_sh_wires_visual_qa(self):
        with open(os.path.join(ROOT, "tools", "build", "gate.sh"), encoding="utf-8") as fh:
            gate = fh.read()
        self.assertIn('visual_qa.py run --gate --main-sha "$MAIN"', gate)
        self.assertIn('export VISUAL_BASELINE_DIR="$L/visual-baseline"', gate)
        step = gate[gate.index("visual_qa.py run --gate"):]
        self.assertRegex(step.split("esac")[0], r"\*\).*fail=1; NORECORD=1")
        store = gate.index("baseline --from-main --shots")
        self.assertGreater(store, gate.index("git push -q origin main"))


class Calibration(unittest.TestCase):
    """Replays the recorded Opus calls on the two calibration frames (no spend): good PASSES, Josh's 15:50 frame FAILS."""

    def setUp(self):
        self.replay_only = os.environ.get("VISUAL_QA_REPLAY_ONLY")
        os.environ["VISUAL_QA_REPLAY_ONLY"] = "1"

    def tearDown(self):
        if self.replay_only is None:
            os.environ.pop("VISUAL_QA_REPLAY_ONLY", None)

    def test_known_good_passes(self):
        r = visual_qa.judge_image(os.path.join(ROOT, visual_qa.KNOWN_GOOD), "known-good", never_called)
        self.assertTrue(r["replayed"])
        self.assertTrue(visual_qa.decide(r)[0], r)

    def test_known_bad_fails(self):
        r = visual_qa.judge_image(os.path.join(ROOT, visual_qa.KNOWN_BAD), "known-bad", never_called)
        self.assertTrue(r["replayed"])
        ok, why = visual_qa.decide(r)
        self.assertFalse(ok)
        self.assertTrue(r["broken"], "the 15:50 frame has placeholder boxes and framed gusts")
        self.assertLess(r["scores"]["no_placeholders"], 5)


if __name__ == "__main__":
    unittest.main()
