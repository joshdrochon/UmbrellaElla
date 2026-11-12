import json
import re
import os
import sys
import tempfile
import unittest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "tools"))
import check_automation_report as car  # noqa: E402
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import hermetic  # noqa: E402


def rep(states):
    return {"succeeded": states.count("Success"), "failed": states.count("Fail"),
            "tests": [{"fullTestPath": f"UmbrellaElla.Area.T{i}", "state": s} for i, s in enumerate(states)]}


class AutomationReportTests(unittest.TestCase):
    def test_all_pass(self):
        self.assertTrue(car.evaluate(rep(["Success"] * 3))["pass"])

    def test_failure_caught(self):
        self.assertFalse(car.evaluate(rep(["Success", "Fail"]))["pass"])

    def test_zero_tests_caught(self):
        self.assertFalse(car.evaluate(rep([]))["pass"])

    def test_dropped_count_caught(self):
        self.assertFalse(car.evaluate(rep(["Success"] * 3), baseline=5)["pass"])

    def test_missing_required_test_caught(self):
        r = car.evaluate(rep(["Success"]), required=["UmbrellaElla.Umbrella.OpenRises"])
        self.assertFalse(r["pass"])

    def test_not_run_caught(self):
        self.assertFalse(car.evaluate(rep(["Success", "NotRun"]))["pass"])

    def test_required_name_must_match_whole_segment(self):
        r = {"tests": [{"fullTestPath": "UmbrellaElla.Umbrella.NotOpenRises", "state": "Success"}]}
        self.assertFalse(car.evaluate(r, required=["OpenRises"])["pass"])
        self.assertTrue(car.evaluate(r, required=["NotOpenRises"])["pass"])

    def test_required_test_found(self):
        r = car.evaluate(rep(["Success"]), required=["UmbrellaElla.Area.T0"])
        self.assertTrue(r["pass"])

    def test_missing_file_exit_2_and_bom_ok(self):
        d = tempfile.mkdtemp()
        self.assertEqual(car.main([os.path.join(d, "none.json")]), 2)
        p = os.path.join(d, "index.json")
        with open(p, "w", encoding="utf-8-sig") as fh:
            json.dump(timed(("UmbrellaElla.Area.T0", 0.1)), fh)
        self.assertEqual(car.main([p]), 0)


class ResultLineCommit(unittest.TestCase):
    # Final-7 B H7: the result line names the commit, so check_pr can match it to the PR head
    def test_result_line_names_the_commit(self):
        import io
        from contextlib import redirect_stdout
        d = tempfile.mkdtemp()
        p = os.path.join(d, "index.json")
        with open(p, "w", encoding="utf-8") as fh:
            json.dump(timed(("UmbrellaElla.Area.T0", 0.1)), fh)
        buf = io.StringIO()
        with redirect_stdout(buf):
            self.assertEqual(car.main([p, "--commit", "abc1234"]), 0)
        self.assertIn("PASS  tests=1 failed=0  commit=abc1234\n", buf.getvalue())
        buf = io.StringIO()
        with redirect_stdout(buf):
            car.main([p])
        self.assertRegex(buf.getvalue(), r"PASS  tests=1 failed=0  commit=(?:[0-9a-f]{40}|unknown)\n")


def named(*pairs):
    return {"tests": [{"fullTestPath": n, "state": st} for n, st in pairs]}


MAP = """| MVP | Required tests | Card | Status |
|---|---|---|---|
| 1 | `UmbrellaElla.Move.WalksLeftRight` | #11 | merged |
| 2 | `UmbrellaElla.Umbrella.OpenRises`, `UmbrellaElla.Umbrella.ClosedFalls` | #12 | planned |
| 3 | `UmbrellaElla.Umbrella.OpenDuringFallReverses` | | planned |
"""


class BootstrapTests(unittest.TestCase):
    """Findings 1 and 2: card 0.3 can pass before gameplay tests exist, without weakening the default."""

    PLACEHOLDER = named(("UmbrellaElla.Bootstrap.Placeholder", "Success"))

    def test_default_still_fails_zero_tests(self):
        self.assertIn("no tests ran", car.evaluate(rep([]))["problems"])

    def test_bootstrap_still_fails_zero_tests(self):
        self.assertFalse(car.evaluate(rep([]), bootstrap=True)["pass"])

    def test_placeholder_only_fails_by_default(self):
        r = car.evaluate(self.PLACEHOLDER)
        self.assertFalse(r["pass"])
        self.assertTrue(any("--bootstrap" in p for p in r["problems"]), r)

    def test_engine_tests_only_fail_by_default(self):
        self.assertFalse(car.evaluate(named(("System.Core.Misc.Smoke", "Success")))["pass"])

    def test_placeholder_passes_with_bootstrap(self):
        self.assertTrue(car.evaluate(self.PLACEHOLDER, bootstrap=True)["pass"])

    def test_engine_smoke_test_passes_with_bootstrap(self):
        self.assertTrue(car.evaluate(named(("System.Core.Misc.Smoke", "Success")), bootstrap=True)["pass"])

    def test_bootstrap_failed_placeholder_fails(self):
        self.assertFalse(car.evaluate(named(("UmbrellaElla.Bootstrap.Placeholder", "Fail")), bootstrap=True)["pass"])

    def test_bootstrap_refused_once_gameplay_tests_exist(self):
        r = car.evaluate(named(("UmbrellaElla.Bootstrap.Placeholder", "Success"),
                               ("UmbrellaElla.Meta.SampleRule", "Success")), bootstrap=True)
        self.assertFalse(r["pass"])

    def test_bootstrap_refuses_baseline_and_require(self):
        self.assertFalse(car.evaluate(self.PLACEHOLDER, baseline=1, bootstrap=True)["pass"])
        self.assertFalse(car.evaluate(self.PLACEHOLDER, required=["X"], bootstrap=True)["pass"])

    def test_cli_bootstrap(self):
        d = tempfile.mkdtemp()
        p = os.path.join(d, "index.json")
        with open(p, "w") as fh:
            json.dump(self.PLACEHOLDER, fh)
        import io
        from contextlib import redirect_stdout
        with redirect_stdout(io.StringIO()) as out:
            self.assertEqual(car.main([p]), 1)
            self.assertEqual(car.main([p, "--bootstrap"]), 0)
        self.assertIn("bootstrap", out.getvalue())


class TestMapTests(unittest.TestCase):
    """Finding 2: the daily build requires only the tests of merged test-map rows."""

    def test_only_merged_rows_required(self):
        names, problems = car.test_map_requirements(MAP)
        self.assertEqual((names, problems), (["UmbrellaElla.Move.WalksLeftRight"], []))

    def test_merged_row_missing_from_report_fails(self):
        names, _ = car.test_map_requirements(MAP)
        r = car.evaluate(named(("UmbrellaElla.Meta.SampleRule", "Success")), required=names)
        self.assertIn("required test not found: UmbrellaElla.Move.WalksLeftRight", r["problems"])

    def test_planned_rows_do_not_turn_the_build_red(self):
        names, _ = car.test_map_requirements(MAP)
        r = car.evaluate(named(("UmbrellaElla.Move.WalksLeftRight", "Success")), required=names)
        self.assertTrue(r["pass"], r)

    def test_merged_without_card_fails(self):
        _, problems = car.test_map_requirements(MAP.replace("| #11 | merged", "|  | merged"))
        self.assertTrue(any("no '#<issue>'" in p for p in problems), problems)

    def test_unknown_status_fails(self):
        _, problems = car.test_map_requirements(MAP.replace("| #12 | planned", "| #12 | done"))
        self.assertTrue(any("not planned or merged" in p for p in problems), problems)

    def test_missing_status_column_fails(self):
        _, problems = car.test_map_requirements("| MVP | Required tests | Card |\n|---|---|---|\n| 1 | `UmbrellaElla.A.B` | #1 |\n")
        self.assertTrue(problems)

    def test_real_test_map_parses_and_has_every_status(self):
        with open(os.path.join(ROOT, "pipeline", "qa", "test-map.md"), encoding="utf-8") as fh:
            text = fh.read()
        names, problems = car.test_map_requirements(text)
        self.assertEqual(problems, [])
        rows = [ln for ln in text.splitlines() if re.match(r"\|\s*QA-\d{2}\s*\|", ln)]
        # GDD 1.3 section 11: QA-01..QA-28; one QA ID may span rows, one per building card (final-8 A H4, M7)
        self.assertEqual(len({re.match(r"\|\s*(QA-\d{2})", ln).group(1) for ln in rows}), 28)
        for qa in ("QA-01", "QA-03", "QA-06", "QA-09"):   # findings 3 and 7: every code-provable test row has tests
            self.assertTrue(any(re.match(r"\|\s*%s\s*\|.*UmbrellaElla\." % qa, ln) for ln in rows), qa)

    def test_cli_test_map(self):
        d = tempfile.mkdtemp()
        rp, mp = os.path.join(d, "index.json"), os.path.join(d, "map.md")
        with open(rp, "w") as fh:
            json.dump(timed(("UmbrellaElla.Meta.SampleRule", 0.1)), fh)
        with open(mp, "w") as fh:
            fh.write(MAP)
        import io
        from contextlib import redirect_stdout
        with redirect_stdout(io.StringIO()):
            self.assertEqual(car.main([rp, "--test-map", mp]), 1)
            with open(mp, "w") as fh:
                fh.write(MAP.replace("| #11 | merged", "| #11 | planned"))
            self.assertEqual(car.main([rp, "--test-map", mp]), 0)
            self.assertEqual(car.main([rp, "--test-map", mp, "--bootstrap"]), 1)


def timed(*rows):
    return {"tests": [{"fullTestPath": n, "state": "Success", "duration": d} for n, d in rows]}


class RuleTimeTests(unittest.TestCase):
    """Rule tests must stay under 1 s; world tests (a `.World.` segment) are not held to it."""

    def test_fast_rule_tests_pass(self):
        r = car.evaluate(timed(("UmbrellaElla.Umbrella.OpenRises", 0.02)), max_rule_seconds=1.0)
        self.assertTrue(r["pass"], r)

    def test_slow_rule_test_fails(self):
        r = car.evaluate(timed(("UmbrellaElla.Umbrella.OpenRises", 0.02), ("UmbrellaElla.Attack.Slow", 45.0)),
                         max_rule_seconds=1.0)
        self.assertFalse(r["pass"])
        self.assertTrue(any("UmbrellaElla.Attack.Slow (45.00 s)" in p for p in r["problems"]), r)

    def test_slow_world_test_and_engine_test_are_not_rule_tests(self):
        r = car.evaluate(timed(("UmbrellaElla.Move.World.FallsAtTerminal", 12.0), ("System.Engine.Slow", 9.0),
                               ("UmbrellaElla.Move.WalksLeftRight", 0.1)), max_rule_seconds=1.0)
        self.assertTrue(r["pass"], r)

    def test_zero_turns_the_limit_off(self):
        self.assertTrue(car.evaluate(timed(("UmbrellaElla.Attack.Slow", 45.0)), max_rule_seconds=0)["pass"])

    def test_cli_default_is_one_second_and_prints_suite_time(self):
        import io
        from contextlib import redirect_stdout
        d = tempfile.mkdtemp()
        p = os.path.join(d, "index.json")
        with open(p, "w") as fh:
            json.dump(timed(("UmbrellaElla.Attack.Slow", 1.5), ("UmbrellaElla.Attack.Fast", 0.5)), fh)
        with redirect_stdout(io.StringIO()) as out:
            self.assertEqual(car.main([p]), 1)
            self.assertEqual(car.main([p, "--max-rule-seconds", "2"]), 0)
        self.assertIn("suite 2.0 s over 2 test(s); slowest UmbrellaElla.Attack.Slow", out.getvalue())

    # Critic round: a report with no durations passed the 1 s limit. A missing measurement must fail.
    def test_rule_test_without_duration_fails_while_limit_is_on(self):
        r = car.evaluate(rep(["Success"]), max_rule_seconds=1.0)
        self.assertFalse(r["pass"], r)
        self.assertTrue(any("have no duration" in p for p in r["problems"]), r)

    def test_one_untimed_rule_test_among_timed_ones_fails(self):
        report = timed(("UmbrellaElla.Move.WalksLeftRight", 0.1))
        report["tests"].append({"fullTestPath": "UmbrellaElla.Attack.NoTime", "state": "Success"})
        r = car.evaluate(report, max_rule_seconds=1.0)
        self.assertFalse(r["pass"], r)
        self.assertTrue(any("UmbrellaElla.Attack.NoTime" in p for p in r["problems"]), r)

    def test_untimed_world_engine_and_bootstrap_tests_are_not_held_to_it(self):
        report = {"tests": [{"fullTestPath": n, "state": "Success"} for n in
                            ("UmbrellaElla.Move.World.Falls", "System.Engine.X")]}
        report["tests"] += timed(("UmbrellaElla.Move.WalksLeftRight", 0.1))["tests"]
        self.assertTrue(car.evaluate(report, max_rule_seconds=1.0)["pass"])
        self.assertTrue(car.evaluate(rep(["Success"]), max_rule_seconds=0)["pass"])
        boot = {"tests": [{"fullTestPath": "UmbrellaElla.Bootstrap.Placeholder", "state": "Success"}]}
        self.assertTrue(car.evaluate(boot, bootstrap=True, max_rule_seconds=1.0)["pass"])

    def test_cli_untimed_report_exits_1(self):
        import io
        from contextlib import redirect_stdout
        d = tempfile.mkdtemp()
        p = os.path.join(d, "index.json")
        with open(p, "w") as fh:
            json.dump(rep(["Success"]), fh)
        with redirect_stdout(io.StringIO()) as out:
            self.assertEqual(car.main([p]), 1)
            self.assertEqual(car.main([p, "--max-rule-seconds", "0"]), 0)
        self.assertIn("have no duration", out.getvalue())

    def test_list_test_map_prints_merged_names(self):
        import io
        from contextlib import redirect_stdout
        d = tempfile.mkdtemp()
        mp = os.path.join(d, "map.md")
        with open(mp, "w") as fh:
            fh.write(MAP)
        with redirect_stdout(io.StringIO()) as out:
            self.assertEqual(car.main(["--list-test-map", mp]), 0)
        self.assertEqual(out.getvalue().split(), ["UmbrellaElla.Move.WalksLeftRight"])
        with open(mp, "w") as fh:
            fh.write(MAP.replace("| #11 | merged", "|  | merged"))
        with redirect_stdout(io.StringIO()):
            self.assertEqual(car.main(["--list-test-map", mp]), 1)


class WorldMarkTests(unittest.TestCase):
    """Critic gap: the 1 s rule-test limit failed the required flow and content tests."""

    SLOW_FLOW = (("UmbrellaElla.Flow.TitleToPlayToSurvived", 38.2), ("UmbrellaElla.Content.AllMapsLoad", 6.5),
                 ("UmbrellaElla.Move.WalksLeftRight", 0.1))

    def real_map(self):
        # final-9 A C1: the real map with its rows back at planned (tests/hermetic.py), so merged jam rows never
        # demand tests this fixture report does not hold
        p = hermetic.write_planned_test_map(os.path.join(tempfile.mkdtemp(), "test-map.md"))
        with open(p, encoding="utf-8") as fh:
            return p, fh.read()

    def test_unmarked_slow_flow_tests_fail(self):
        r = car.evaluate(timed(*self.SLOW_FLOW), max_rule_seconds=1.0)
        self.assertFalse(r["pass"])
        self.assertTrue(any("2 rule test(s) over 1 s" in p for p in r["problems"]), r)

    def test_real_test_map_marks_flow_and_content_as_world(self):
        _, text = self.real_map()
        world = car.test_map_world(text)
        self.assertIn("UmbrellaElla.Flow.TitleToPlayToSurvived", world)
        self.assertIn("UmbrellaElla.Content.AllMapsLoad", world)
        self.assertTrue(car.evaluate(timed(*self.SLOW_FLOW), max_rule_seconds=1.0, world=world)["pass"])
        r = car.evaluate(timed(*self.SLOW_FLOW, ("UmbrellaElla.Move.Slow", 1.5)), max_rule_seconds=1.0, world=world)
        self.assertFalse(r["pass"])
        self.assertTrue(any("UmbrellaElla.Move.Slow (1.50 s)" in p for p in r["problems"]), r)

    def test_world_mark_counts_only_in_table_rows(self):
        text = MAP + "\nProse: `UmbrellaElla.Move.WalksLeftRight` (world) is not a mark.\n"
        self.assertEqual(car.test_map_world(text), [])
        self.assertEqual(car.test_map_world(MAP.replace("`UmbrellaElla.Move.WalksLeftRight`",
                                                        "`UmbrellaElla.Move.WalksLeftRight` (world)")),
                         ["UmbrellaElla.Move.WalksLeftRight"])

    def test_four_segment_names_are_read_whole(self):
        names, _ = car.test_map_requirements(MAP.replace("UmbrellaElla.Move.WalksLeftRight",
                                                         "UmbrellaElla.World.Flow.TitleToPlayToWin"))
        self.assertEqual(names, ["UmbrellaElla.World.Flow.TitleToPlayToWin"])

    def test_cli_with_real_test_map_passes_slow_flow_tests(self):
        import io
        from contextlib import redirect_stdout
        mp, _ = self.real_map()
        d = tempfile.mkdtemp()
        p = os.path.join(d, "index.json")
        with open(p, "w") as fh:
            json.dump(timed(*self.SLOW_FLOW), fh)
        with redirect_stdout(io.StringIO()) as out:
            self.assertEqual(car.main([p]), 1)
            self.assertEqual(car.main([p, "--test-map", mp]), 0)
        self.assertIn("marked (world)", out.getvalue())


if __name__ == "__main__":
    unittest.main()
