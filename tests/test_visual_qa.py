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
        with mock.patch.object(visual_qa, "judge_shots", return_value=ok), \
                mock.patch.object(visual_qa, "measure_noise", return_value={}):
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
        self.assertEqual(why, ["new broken: cream bar at the bottom [bar]"])

    def test_norm_item_matches_case_and_punctuation(self):
        self.assertEqual(visual_qa.norm_item("  Lilac  placeholder-cube, on the ROUTE. "),
                         visual_qa.norm_item("lilac placeholder cube on the route"))

    def test_gate_judge_passes_main_level_frame_and_fails_regression(self):
        sha = "m" * 40
        visual_qa.store_baseline(sha, "x", self.base()["screens"])
        caller = lambda p, i: answer(6, ["lilac placeholder cube on the route"], verdict="FAIL")
        with mock.patch.object(visual_qa, "judge_call", side_effect=lambda p, i, c, r, n=0: (caller(p, i), False)):
            out = io.StringIO()
            with redirect_stdout(out):
                code = visual_qa.cmd_judge(self.shots, gate=True, sha=sha)
            self.assertEqual(code, visual_qa.EXIT_PASS, out.getvalue())
            self.assertTrue(out.getvalue().strip().splitlines()[-1].startswith("VISUAL_QA GATE PASS"))
        with mock.patch.object(visual_qa, "judge_call", side_effect=lambda p, i, c, r, n=0: (answer(5), False)):
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


FIXTURES = os.path.join(ROOT, "tests", "fixtures", "visual_qa")
NOISE = os.path.join(ROOT, "pipeline", "qa", "visual", "noise")


def fixture(name, folder=FIXTURES):
    with open(os.path.join(folder, name), encoding="utf-8") as fh:
        return json.load(fh)


class GateAbsence(unittest.TestCase):
    """Lead (artella f8d779e8, Ella idle restore): the gate failed on 'no wind' / 'no islands' items, absences of rubric
    criteria main ebda6e47 already scores near 0 (play wind_ribbons 0, floating_islands 2) or names as bars (dc_route).
    Real wordings: ../logs/gate-artella-evidence.txt and the ebda6e47 baseline."""

    def setUp(self):
        self.base = fixture("baseline-ebda6e47.json")
        self.art = fixture("gate-artella-f8d779e8.json")

    def test_artella_is_not_a_regression(self):
        for screen, r in self.art["screens"].items():
            ok, why = visual_qa.decide_gate(r, self.base["screens"][screen])
            self.assertTrue(ok, "%s: %s" % (screen, why))

    def test_absence_items_have_absence_kinds(self):
        self.assertEqual(visual_qa.defect_kind("no wind ribbons visible anywhere"), "no_wind")
        self.assertEqual(visual_qa.defect_kind("no floating islands: the ground is rounded dark blobs and gear "
                                               "silhouettes, with no platform the player can read as ground"), "no_islands")
        self.assertEqual(visual_qa.defect_kind("no floating island ground anywhere; platforms are solid colour bars"),
                         "no_islands")

    def test_absence_fails_when_main_scores_the_criterion_well(self):
        base = dict(self.base["screens"]["play"], scores=dict(self.base["screens"]["play"]["scores"], wind_ribbons=6))
        r = dict(self.art["screens"]["play"], broken=["no wind ribbons visible anywhere"])
        ok, why = visual_qa.decide_gate(r, base)
        self.assertFalse(ok)
        self.assertIn("[no_wind]", why[0])

    def test_no_islands_needs_main_low_score_or_bars(self):
        base = dict(self.base["screens"]["dc_route"],
                    scores=dict(self.base["screens"]["dc_route"]["scores"], floating_islands=7), broken=[], samples=[])
        r = dict(self.art["screens"]["dc_route"], broken=["no floating island ground anywhere; platforms are solid colour bars"])
        self.assertFalse(visual_qa.decide_gate(r, base)[0])

    def test_a_genuinely_new_defect_still_fails(self):
        r = dict(self.art["screens"]["keeper"])
        r["broken"] = r["broken"] + ["Keeper sprite on an unkeyed grey rectangle"]
        ok, why = visual_qa.decide_gate(r, self.base["screens"]["keeper"])
        self.assertFalse(ok)
        self.assertIn("unkeyed grey rectangle [unkeyed]", why[0])


class GateWording(unittest.TestCase):
    """Lead 19:50: the owl merge (artkeeper 0d74b84a) failed the gate on 'new broken' items main b4c1fe79's baseline
    already lists in other words, and on a total inside the judge's own noise. Real wordings from both runs."""

    def setUp(self):
        self.base = fixture("baseline-b4c1fe79.json")              # main's stored run + 5 recorded noise samples
        self.owl = fixture("gate-owl-0d74b84a.json")               # the failing gate run, as judged

    def test_owl_merge_is_not_a_regression(self):
        for screen, r in self.owl["screens"].items():
            ok, why = visual_qa.decide_gate(r, self.base["screens"][screen])
            self.assertTrue(ok, "%s: %s" % (screen, why))

    def test_reworded_items_share_a_kind(self):
        pairs = [
            ("thin flat white vertical line running from the top of the frame down to the player",          # main play
             "thin full-height vertical white line/bar through the left-centre of the frame"),               # owl play
            ("thin straight vertical line across the full frame height",                                     # main keeper
             "stray thin vertical white line from the top of the frame to the player"),                      # owl dc_route
            ("flat dark brown bar used as a floating platform (mid-right)",                                   # main dc_route
             "flat dark-brown bar used as the floating platform (right middle)"),
            ("flat dark brown bar spanning the full width as ground",
             "flat dark-brown bar across the full width as ground (bottom)"),
            ("flat brown bar with solid block step at bottom left (placeholder ground)",                      # main keeper
             "flat dark-brown bar with a block step used as ground at lower left"),
            ("player girl nearly invisible against the backdrop (tiny, low contrast near centre-left)",       # main sample
             "player character barely visible (faint silhouette lost in the background at left-centre)"),
            ("Keeper owl drawn on a visible dark rectangle background (unkeyed)",
             "Keeper owl sprite on a visible rectangle background with hard cut edges (unkeyed)"),
        ]
        for a, b in pairs:
            self.assertEqual(visual_qa.defect_kind(a), visual_qa.defect_kind(b), (a, b))
        self.assertEqual(visual_qa.defect_kind("thin vertical white line from the top of the screen to the player"), "line")
        self.assertEqual(visual_qa.defect_kind("flat dark brown bar as the floor across the full width"), "bar")

    def test_a_genuinely_new_defect_still_fails(self):
        dc = dict(self.owl["screens"]["dc_route"])
        dc["broken"] = dc["broken"] + ["flat dark brown bar as a second floating ledge, top left"]   # a third bar
        ok, why = visual_qa.decide_gate(dc, self.base["screens"]["dc_route"])
        self.assertFalse(ok)
        self.assertIn("second floating ledge", why[0])
        self.assertIn("[bar]", why[0])
        play = dict(self.owl["screens"]["play"])
        play["broken"] = play["broken"] + ["large lilac placeholder cube on the route"]
        self.assertFalse(visual_qa.decide_gate(play, self.base["screens"]["play"])[0])
        odd = dict(self.owl["screens"]["play"])
        odd["broken"] = ["Ella floats upside-down"]       # a kind main never listed
        self.assertFalse(visual_qa.decide_gate(odd, self.base["screens"]["play"])[0])
        # An item no kind rule knows matches only its exact normalised text, as before.
        self.assertEqual(visual_qa.defect_kind("Something  Odd!"), "something odd")

    def test_omitted_known_defect_needs_main_samples(self):
        # Main's stored dc_route run left out the vertical line its own frame shows; the samples list it 5 of 5 times.
        bare = fixture("baseline-b4c1fe79-before-samples.json")["screens"]["dc_route"]
        ok, why = visual_qa.decide_gate(self.owl["screens"]["dc_route"], bare)
        self.assertFalse(ok)
        self.assertIn("[line]", " ".join(why))
        self.assertEqual(visual_qa.known_kinds(self.base["screens"]["dc_route"]).get("line"), 1)

    def test_total_margin_is_the_measured_noise(self):
        """GATE_TOTAL_SLACK: the most one judged run fell under its frame's median; _SINGLE: the widest spread."""
        sets = []
        for noise, stored in (("main-b4c1fe79.json", fixture("baseline-b4c1fe79-before-samples.json")),
                              ("owl-0d74b84a.json", self.owl)):
            n = fixture(noise, NOISE)
            for screen, o in n["screens"].items():
                sets.append(sorted([stored["screens"][screen]["total"]] + o["totals"]))
        self.assertEqual(len(sets), 6)
        def median(t):
            m = len(t) // 2
            return t[m] if len(t) % 2 else (t[m - 1] + t[m]) / 2.0
        import math
        self.assertEqual(visual_qa.GATE_TOTAL_SLACK, math.ceil(max(median(t) - t[0] for t in sets)))
        self.assertEqual(visual_qa.GATE_TOTAL_SLACK_SINGLE, max(t[-1] - t[0] for t in sets))
        # Inside the noise passes, past it fails (main dc_route median 25.5).
        self.assertEqual(visual_qa.base_total(self.base["screens"]["dc_route"]), (25.5, visual_qa.GATE_TOTAL_SLACK))
        r = {"total": 22, "broken": []}
        self.assertTrue(visual_qa.decide_gate(r, self.base["screens"]["dc_route"])[0])
        r["total"] = 21
        self.assertFalse(visual_qa.decide_gate(r, self.base["screens"]["dc_route"])[0])

    def test_noise_samples_are_separate_recorded_calls(self):
        tmp = tempfile.mkdtemp()
        try:
            calls = []
            def caller(p, i):
                calls.append(p)
                return answer(5)
            visual_qa.judge_call("prompt", b"img", caller, tmp)
            visual_qa.judge_call("prompt", b"img", caller, tmp, sample=1)
            visual_qa.judge_call("prompt", b"img", caller, tmp, sample=1)      # replayed
            self.assertEqual(len(calls), 2)
            self.assertEqual(len(os.listdir(tmp)), 2)
        finally:
            shutil.rmtree(tmp, ignore_errors=True)

    def test_new_baseline_stores_samples(self):
        tmp = tempfile.mkdtemp()
        shots = os.path.join(tmp, "shots")
        os.makedirs(shots)
        for name in visual_qa.SCREENS.values():
            shutil.copyfile(os.path.join(ROOT, visual_qa.STUDY), os.path.join(shots, name))
        try:
            with mock.patch.dict(os.environ, {"VISUAL_BASELINE_DIR": os.path.join(tmp, "base")}), \
                    mock.patch.object(visual_qa, "BASELINE_SAMPLES", 2), redirect_stdout(io.StringIO()):
                code = visual_qa.cmd_baseline_from_main("", "7" * 40, lambda p, i: answer(4, ["thin white line"], "FAIL"),
                                                        os.path.join(tmp, "rec"), shots=shots)
                self.assertEqual(code, visual_qa.EXIT_PASS)
                play = visual_qa.load_baseline("7" * 40)["screens"]["play"]
            self.assertEqual(len(play["samples"]), 2)
            self.assertEqual(play["samples"][0]["broken"], ["thin white line"])
        finally:
            shutil.rmtree(tmp, ignore_errors=True)


class GateRecapture(unittest.TestCase):
    """Lead (ellaidle 9177511f, only T_Ella_Idle_PH changed): dc_route failed on 'figure at right (Keeper or enemy) has
    a solid dark red rectangle behind it [unkeyed]', the enemy, whose place and pose differ capture to capture. Main's
    samples re-judge one capture, so on a gate FAIL the tip is captured again and only a regression in both counts."""

    def setUp(self):
        self.base = fixture("baseline-ebda6e47.json")
        self.tip = fixture("gate-ellaidle-9177511f.json")
        self.dc = self.tip["screens"]["dc_route"]
        self.again = fixture("gate-ellaidle-9177511f-recheck.json")["screens"]["dc_route"]

    def test_9177511f_one_capture_alone_fails(self):
        ok, why = visual_qa.decide_gate(self.dc, self.base["screens"]["dc_route"])
        self.assertFalse(ok)
        self.assertIn("dark red rectangle behind it [unkeyed]", why[0])

    def test_9177511f_item_absent_from_the_recapture_passes(self):
        self.assertNotIn("unkeyed", [visual_qa.defect_kind(b) for b in self.again["broken"]])
        for screen, r in self.tip["screens"].items():
            r2 = fixture("gate-ellaidle-9177511f-recheck.json")["screens"][screen]
            ok, why = visual_qa.confirm_gate(r, r2, self.base["screens"][screen])
            self.assertTrue(ok, "%s: %s" % (screen, why))

    def test_defect_in_both_captures_and_not_on_main_fails(self):
        second = dict(self.again, broken=self.again["broken"] + ["enemy sprite drawn on a dark red rectangle (unkeyed)"])
        ok, why = visual_qa.confirm_gate(self.dc, second, self.base["screens"]["dc_route"])
        self.assertFalse(ok)
        self.assertIn("both captures", why[0])
        self.assertIn("[unkeyed]", why[0])

    def test_total_regression_must_hold_in_both(self):
        b = self.base["screens"]["dc_route"]
        low = dict(self.dc, total=0, broken=[])
        self.assertTrue(visual_qa.confirm_gate(low, dict(self.dc, broken=[]), b)[0])
        self.assertFalse(visual_qa.confirm_gate(low, dict(low), b)[0])

    def test_gate_fail_recaptures_once_and_records_both(self):
        tmp = tempfile.mkdtemp()
        shots = os.path.join(tmp, "shots")
        os.makedirs(shots)
        for name in visual_qa.SCREENS.values():
            shutil.copyfile(os.path.join(ROOT, visual_qa.STUDY), os.path.join(shots, name))
        captures = []

        def fake_capture(out):
            captures.append(out)
            os.makedirs(out, exist_ok=True)
            # A different frame: the enemy moved. A real capture with no flat box (known-bad has boxes, which the
            # box detector now lists on the recapture too).
            clean = os.path.join(ROOT, visual_qa.CALIBRATION, "flatbox-dcroute-clean.png")
            for name in visual_qa.SCREENS.values():
                shutil.copyfile(clean, os.path.join(out, name))
            return 0

        def caller(prompt, image):
            first = len(captures) == 0
            return answer(5, ["enemy has a dark red rectangle behind it"] if first else [], "FAIL")
        base = {"sha": "b" * 40, "screens": {s: {"total": 35, "broken": [], "scores": {}} for s in visual_qa.SCREENS}}
        try:
            os.makedirs(os.path.join(tmp, "base"))
            with open(os.path.join(tmp, "base", "b" * 40 + ".json"), "w") as fh:
                json.dump(base, fh)
            with mock.patch.dict(os.environ, {"VISUAL_BASELINE_DIR": os.path.join(tmp, "base")}), \
                    mock.patch.object(visual_qa, "capture", side_effect=fake_capture), \
                    mock.patch.object(visual_qa, "RECORDS", os.path.join(tmp, "rec"), create=True), \
                    redirect_stdout(io.StringIO()) as out:
                code = visual_qa.cmd_judge(shots, caller, sha="b" * 40, gate=True, recapture=True)
            self.assertEqual(code, visual_qa.EXIT_PASS, out.getvalue())
            self.assertEqual(captures, [os.path.join(shots, "recheck")])
            with open(os.path.join(shots, "visual_qa.json")) as fh:
                rep = json.load(fh)
            self.assertIn("recheck=1", rep["summary"])
            self.assertEqual(rep["screens"]["play"]["recheck"]["broken"], [])
            self.assertIn("[unkeyed]", rep["screens"]["play"]["first_reasons"][0])
            self.assertTrue(os.path.exists(os.path.join(shots, "recheck", "visual_qa.json")))
        finally:
            shutil.rmtree(tmp, ignore_errors=True)


class BaselineCaptures(unittest.TestCase):
    """Main captured 3 times (pipeline/qa/visual/noise/capvar-main-d812ba29.json): the enemy's red backing is named in
    2 of 3 captures (once 'unkeyed', once 'box'), dc_route totals 19/22/23. Stored as samples, they count as main's."""

    def test_capture_variance_numbers(self):
        cv = fixture("capvar-main-d812ba29.json", NOISE)["captures"]
        dc = [c["dc_route"] for c in cv.values()]
        self.assertEqual(sorted(c["total"] for c in dc), [19, 22, 23])
        self.assertEqual(sum(1 for c in dc if "unkeyed" in c["kinds"] or "box" in c["kinds"]), 2)

    def test_add_captures_joins_main_samples(self):
        tmp = tempfile.mkdtemp()
        shots = os.path.join(tmp, "cap1")
        os.makedirs(shots)
        for name in visual_qa.SCREENS.values():
            shutil.copyfile(os.path.join(ROOT, visual_qa.STUDY), os.path.join(shots, name))
        base = {"sha": "c" * 40, "screens": {s: {"total": 30, "broken": [], "scores": {}} for s in visual_qa.SCREENS}}
        try:
            os.makedirs(os.path.join(tmp, "base"))
            with open(os.path.join(tmp, "base", "c" * 40 + ".json"), "w") as fh:
                json.dump(base, fh)
            with mock.patch.dict(os.environ, {"VISUAL_BASELINE_DIR": os.path.join(tmp, "base")}), \
                    redirect_stdout(io.StringIO()):
                code = visual_qa.add_captures("c" * 40, [shots], lambda p, i: answer(3, ["enemy on a dark red "
                                              "rectangle (unkeyed)"], "FAIL"), os.path.join(tmp, "rec"))
                self.assertEqual(code, visual_qa.EXIT_PASS)
                dc = visual_qa.load_baseline("c" * 40)["screens"]["dc_route"]
            self.assertEqual(dc["samples"][0]["capture"], shots)
            self.assertEqual(visual_qa.known_kinds(dc), {"unkeyed": 1})
            self.assertTrue(visual_qa.decide_gate({"total": 30, "broken": ["red rectangle behind the enemy (unkeyed)"]},
                                                  dc)[0])
        finally:
            shutil.rmtree(tmp, ignore_errors=True)


class UserState(unittest.TestCase):
    """A capture leaves saves and GameUserSettings.ini exactly as before (a progress save left by a game run made
    the gate's LevelUpShowsAndResumes start on the purchase screen)."""

    def test_capture_restores_saves_and_settings(self):
        root = tempfile.mkdtemp()
        self.addCleanup(shutil.rmtree, root)
        saves = os.path.join(root, "Saved", "SaveGames")
        cfg = os.path.join(root, "Saved", "Config", "Mac")
        os.makedirs(saves)
        os.makedirs(cfg)
        kept = os.path.join(saves, "Slot.sav")
        ini = os.path.join(cfg, "GameUserSettings.ini")
        with open(kept, "wb") as fh:
            fh.write(b"before")
        with open(ini, "w") as fh:
            fh.write("[Flow]\n")

        def game_run(*_a, **_k):
            with open(kept, "wb") as fh:
                fh.write(b"points earned")
            with open(os.path.join(saves, "UmbrellaEllaProgress.sav"), "wb") as fh:
                fh.write(b"new")
            with open(ini, "w") as fh:
                fh.write("[Flow]\nTutorialSeen=True\n")
            return mock.Mock(returncode=0)

        with mock.patch.object(visual_qa, "ROOT", root), \
                mock.patch.object(visual_qa.subprocess, "run", side_effect=game_run):
            self.assertEqual(visual_qa.capture(os.path.join(root, "out")), 0)
        self.assertEqual(sorted(os.listdir(saves)), ["Slot.sav"])
        with open(kept, "rb") as fh:
            self.assertEqual(fh.read(), b"before")
        with open(ini) as fh:
            self.assertEqual(fh.read(), "[Flow]\n")


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
