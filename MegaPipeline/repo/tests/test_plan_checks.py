"""Tests for the Producer's plan checks in tools/check_card.py: the card budget, Used by and content-cap
rules, and the board modes --clock, --people, --hours, --lanes and --status. Each check gets a good
input that passes and the same input broken on purpose that fails."""
import datetime as dt
import io
import json
import os
import re
import shutil
import sys
import tempfile
import unittest
from contextlib import redirect_stderr, redirect_stdout

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, os.path.join(ROOT, "tools"))
import check_card  # noqa: E402

FIX = os.path.join(HERE, "fixtures", "cards")


def setUpModule():   # the good cards build UMB-01 / HAZ-01; read them against a signed-off manifest (test_check_card.py)
    check_card.MANIFEST_PATH = os.path.join(HERE, "fixtures", "manifest", "signed_off.json")


def tearDownModule():
    check_card.MANIFEST_PATH = None


TITLE = "[UE-031] Spikes damage Ella"


def install_clock(d, text=None):
    """Put the clock template and its live copy in a temp root (Day-0 card 0.16)."""
    with open(os.path.join(ROOT, "pipeline", "templates", "clock-workflow.yml"), encoding="utf-8") as f:
        tmpl = f.read()
    for rel, body in (("pipeline/templates/clock-workflow.yml", tmpl), (".github/workflows/clock.yml", text or tmpl)):
        os.makedirs(os.path.join(d, os.path.dirname(rel)), exist_ok=True)
        with open(os.path.join(d, rel), "w", encoding="utf-8") as f:
            f.write(body)


def good_form():
    with open(os.path.join(FIX, "good_form.md"), encoding="utf-8") as f:
        return f.read()


def kinds(body):
    return {k for k, _ in check_card.problems(body, ROOT, TITLE)}


GOOD_BRIEF = """# Brief

## Clock (card 0.0 sets it)
Submission deadline: 2026-11-16T17:00-05:00
Hard stop: 01:00-08:00
Card 0.9 cutoff: 2026-11-12T18:00-05:00

| Gate | Due |
|---|---|
| G1 | 2026-11-13T20:00-05:00 |
| G2 | 2026-11-14T20:00-05:00 |
| G3 | 2026-11-15T20:00-05:00 |
| G4 | 2026-11-16T12:00-05:00 |

## People
| Role | Person | Confirmed? | Day-1 blocker |
|---|---|---|---|
| Scope decision-maker | Rick | yes | BLOCKER |
| Producer / time keeper, human | Ana | yes | BLOCKER |

## Team hours (card 0.0)
| Person | Hours D1/D2/D3/D4 | Away windows | Built UE C++ before (y/n) | Confirmed? |
|---|---|---|---|---|
| Rick | 8/8/8/6 | none | y | yes |
| Ana | 4/4/4/4 | D2 12:00-14:00 | n | yes |

## Hard limits
- none
"""


def issue(num, lane, human="Rick", budget="60 min agent + 30 min human, MVP", locks="none"):
    body = good_form().replace("Lane: Source/UmbrellaElla/{Public,Private}/Hazard/**", "Lane: " + lane)
    body = body.replace("Locks: none", "Locks: " + locks)
    body = body.replace("Rick\n", human + "\n", 1).replace("60 min agent + 15 min human, MVP", budget)
    return {"number": num, "title": f"[UE-{num}] card", "body": body}


class CardBudget(unittest.TestCase):
    def test_good_budget_passes(self):
        self.assertEqual(kinds(good_form()), set())

    def test_whenever_fails(self):
        # an unparsed budget also leaves the P0 card without its exact 'MVP' tier (HAZ-19 is APPROVED_P0)
        self.assertEqual(kinds(good_form().replace("60 min agent + 15 min human, MVP", "whenever, MVP")), {"budget", "mvp"})

    def test_agent_only_fails(self):
        self.assertEqual(kinds(good_form().replace("60 min agent + 15 min human, MVP", "60 min, MVP")), {"budget"})

    def test_agent_over_120_must_split(self):
        self.assertEqual(kinds(good_form().replace("60 min agent", "121 min agent")), {"budget"})
        self.assertEqual(kinds(good_form().replace("60 min agent", "120 min agent")), set())

    def test_human_over_60_must_split(self):
        # 120 min agent + 400 min human used to pass and got about 9.7 h of doing before a cut.
        got = check_card.problems(good_form().replace("60 min agent + 15 min human", "120 min agent + 400 min human"),
                                  ROOT, TITLE)
        self.assertEqual([k for k, _ in got], ["budget"])
        self.assertIn("human budget 400 min", got[0][1])
        self.assertEqual(kinds(good_form().replace("15 min human", "61 min human")), {"budget"})
        self.assertEqual(kinds(good_form().replace("15 min human", "60 min human")), set())


class CardUsedBy(unittest.TestCase):
    def test_used_by_without_card_number_fails(self):
        self.assertEqual(kinds(good_form().replace("BP_Spikes (Integrator card UE-040)", "BP_Spikes (Integrator)")),
                         {"usedby"})

    def test_used_by_none_or_issue_number_passes(self):
        self.assertEqual(kinds(good_form().replace("BP_Spikes (Integrator card UE-040)", "none")), set())
        self.assertEqual(kinds(good_form().replace("BP_Spikes (Integrator card UE-040)", "BP_Spikes (#40)")), set())


class CardContentCaps(unittest.TestCase):
    """The cap rule, on a brief that sets a cap. GDD SH1.0's brief sets none (ANIM-02: frame counts follow each
    receiving contract), so these tests give check_card a 60-frame cap for their duration."""

    def setUp(self):
        self.real = check_card.content_caps
        check_card.content_caps = lambda root: {"frames": 60}
        self.addCleanup(setattr, check_card, "content_caps", self.real)
        self.caps = check_card.content_caps(ROOT)

    def test_brief_has_caps(self):
        self.assertEqual(self.real(ROOT), {}, "GDD SH1.0 sets no content cap")

    def line(self, text):
        return good_form().replace("- [ ] Ella takes no second hit", "- [ ] " + text + "\n- [ ] Ella takes no second hit")

    def test_at_cap_passes(self):
        self.assertEqual(kinds(self.line(f"Owl set has {self.caps['frames']} flipbook frames (count in the sidecar JSON)")), set())

    def test_over_cap_fails(self):
        n = self.caps["frames"] + 1
        self.assertEqual(kinds(self.line(f"Ella set has {n} flipbook frames (count in the sidecar JSON)")), {"cap"})

    def test_over_cap_with_decision_row_passes(self):
        n = self.caps["frames"] + 2
        self.assertEqual(kinds(self.line(f"Owl set has {n} flipbook frames (count in the sidecar JSON), per D-new-caps")), set())


class Clock(unittest.TestCase):
    def test_good_clock_passes(self):
        self.assertEqual(check_card.clock_problems(GOOD_BRIEF), [])

    def test_real_brief_has_every_clock_line(self):
        # The lines must exist now; TBD is allowed until card 0.0 sets them.
        with open(os.path.join(ROOT, "docs", "jam-brief.md"), encoding="utf-8") as f:
            text = f.read()
        self.assertEqual(check_card.clock_problems(text, allow_tbd=True), [])
        # final-9 A C1: state-independent. Card 0.0 fills the Clock during the jam; the honest suite checks the filled one

    def test_each_break_is_caught(self):
        for old, new, want in [
            ("Submission deadline: 2026-11-16T17:00-05:00\n", "", "missing"),
            ("Submission deadline: 2026-11-16T17:00-05:00", "Submission deadline: TBD", "TBD"),
            ("2026-11-16T17:00-05:00", "2026-11-16T17:00", "UTC offset"),
            ("Hard stop: 01:00-08:00", "Hard stop: late", "HH:MM"),
            ("| G2 | 2026-11-14T20:00-05:00 |", "| G2 | 2026-11-13T19:00-05:00 |", "G1 is not before G2"),
            ("| G4 | 2026-11-16T12:00-05:00 |", "| G4 | 2026-11-16T15:00-05:00 |", "less than 3 h"),
            ("Card 0.9 cutoff: 2026-11-12T18:00-05:00", "Card 0.9 cutoff: 2026-11-14T18:00-05:00", "0.9 cutoff"),
            ("| G3 | 2026-11-15T20:00-05:00 |", "| G3 | 2026-11-15T21:01-05:00 |", "less than 20 h"),
            ("## Clock (card 0.0 sets it)", "## Timing", "no '## Clock'"),
        ]:
            with self.subTest(want=want):
                broken = GOOD_BRIEF.replace(old, new)
                self.assertNotEqual(broken, GOOD_BRIEF)
                got = check_card.clock_problems(broken)
                self.assertTrue(any(want in p for p in got), got)

    def test_cut_fires_only_past_two_hours(self):
        due = dt.datetime.fromisoformat("2026-11-14T20:00-05:00")  # G2
        g1_ok = {"G1": dt.datetime.fromisoformat("2026-11-13T21:00-05:00")}
        lines = check_card.cut_report(GOOD_BRIEF, g1_ok, due + dt.timedelta(hours=1, minutes=59))
        self.assertFalse(any("CUT FIRES" in ln for ln in lines), lines)
        lines = check_card.cut_report(GOOD_BRIEF, g1_ok, due + dt.timedelta(hours=2, minutes=1))
        self.assertTrue(any(ln.startswith("CUT FIRES: G2 open") for ln in lines), lines)
        late = {"G1": dt.datetime.fromisoformat("2026-11-13T22:30-05:00")}
        lines = check_card.cut_report(GOOD_BRIEF, late, due - dt.timedelta(hours=5))
        self.assertTrue(any(ln.startswith("CUT FIRES: G1 closed") for ln in lines), lines)

    def test_g3_exactly_20_h_before_deadline_passes(self):
        text = GOOD_BRIEF.replace("| G3 | 2026-11-15T20:00-05:00 |", "| G3 | 2026-11-15T21:00-05:00 |")
        self.assertEqual(check_card.clock_problems(text), [])

    def test_final_upload_margin(self):
        ok = dt.datetime.fromisoformat("2026-11-16T14:00-05:00")  # 3.0 h before 17:00
        late = dt.datetime.fromisoformat("2026-11-16T14:01-05:00")
        self.assertEqual(check_card.upload_problems(GOOD_BRIEF, ok), [])
        got = check_card.upload_problems(GOOD_BRIEF, late)
        self.assertTrue(any("less than 3 h" in p for p in got), got)
        self.assertTrue(check_card.upload_problems(GOOD_BRIEF.replace("2026-11-16T17:00-05:00", "TBD"), ok))
        with tempfile.TemporaryDirectory() as d:
            p = os.path.join(d, "brief.md")
            with open(p, "w", encoding="utf-8") as f:
                f.write(GOOD_BRIEF)
            install_clock(d)
            for when, code in [("2026-11-16T13:05-05:00", 0), ("2026-11-16T16:00-05:00", 1), ("soon", 2)]:
                with redirect_stdout(io.StringIO()), redirect_stderr(io.StringIO()):
                    rc = check_card.main(["--clock", "--brief", p, "--root", d, "--now", "2026-11-13T09:00-05:00",
                                          "--uploaded", when])
                self.assertEqual(rc, code, when)

    def test_cli(self):
        with tempfile.TemporaryDirectory() as d:
            p = os.path.join(d, "brief.md")
            install_clock(d)
            for text, code in [(GOOD_BRIEF, 0), (GOOD_BRIEF.replace("Hard stop: 01:00-08:00", "Hard stop: TBD"), 1)]:
                with open(p, "w", encoding="utf-8") as f:
                    f.write(text)
                with redirect_stdout(io.StringIO()):
                    rc = check_card.main(["--clock", "--brief", p, "--root", d, "--now", "2026-11-13T09:00-05:00"])
                self.assertEqual(rc, code)


class People(unittest.TestCase):
    def test_good_people_pass(self):
        self.assertEqual(check_card.people_problems(GOOD_BRIEF), [])

    def test_card_00_agent_defaults_pass_without_a_person(self):
        """Card 0.0 fills People and Team hours from the GitHub collaborators and the jam window, Confirmed =
        `default (agent)`; no teammate has to confirm a row. Broken on purpose: any other word still fails."""
        text = GOOD_BRIEF.replace("| yes |", "| default (agent) |")
        self.assertNotEqual(text, GOOD_BRIEF)
        self.assertEqual(check_card.people_problems(text), [])
        got = check_card.people_problems(GOOD_BRIEF.replace("| yes |", "| maybe |", 1))
        self.assertTrue(any("not yes or default (agent)" in p for p in got), got)

    def test_real_brief_has_producer_seat_and_team_table(self):
        with open(os.path.join(ROOT, "docs", "jam-brief.md"), encoding="utf-8") as f:
            text = f.read()
        got = check_card.people_problems(text)
        self.assertFalse(any("no 'Producer" in p or "table is missing" in p for p in got), got)
        # final-9 A C1: no "not filled yet" assert; card 0.0 fills it during the jam (tests/test_honest_jam.py)

    def test_each_break_is_caught(self):
        for old, new, want in [
            ("| Rick | yes | BLOCKER |", "| Rick | no | BLOCKER |", "Confirmed is 'no'"),
            ("| Rick | yes | BLOCKER |", "| Rick (proposed) | yes | BLOCKER |", "no confirmed person"),
            ("| Ana | yes | BLOCKER |", "| TBD | yes | BLOCKER |", "no confirmed person"),
            ("| Producer / time keeper, human | Ana | yes | BLOCKER |\n", "", "no 'Producer"),
            ("| 8/8/8/6 |", "| 8 |", "not D1/D2/D3/D4"),
            ("| none | y | yes |", "| TBD | y | yes |", "away windows"),
            ("| none | y | yes |", "| none | maybe | yes |", "not y or n"),
            ("| D2 12:00-14:00 | n | yes |", "| D2 12:00-14:00 | n | no |", "Confirmed is 'no'"),
            ("| Ana | 4/4/4/4 |", "| Bo | 4/4/4/4 |", "bo has Team hours but no seat"),
            ("| D2 12:00-14:00 | n |", "| afternoons | n |", "not 'D<n> HH:MM-HH:MM'"),
            ("| D2 12:00-14:00 | n |", "| D2 12:00-14:00, D5 09:00-10:00 | n |", "'D5 09:00-10:00'"),
        ]:
            with self.subTest(want=want):
                self.assertIn(old, GOOD_BRIEF)
                got = check_card.people_problems(GOOD_BRIEF.replace(old, new))
                self.assertTrue(any(want in p for p in got), got)


class Seats(unittest.TestCase):
    ROWS = "| Producer / time keeper, human | Ana | yes | BLOCKER |\n"

    def brief(self, extra_people="", extra_team=""):
        t = GOOD_BRIEF.replace(self.ROWS, self.ROWS + extra_people)
        return t.replace("| Ana | 4/4/4/4 | D2 12:00-14:00 | n | yes |\n",
                         "| Ana | 4/4/4/4 | D2 12:00-14:00 | n | yes |\n" + extra_team)

    def test_three_blocker_seats_pass_four_fail(self):
        two = "".join(f"| Seat {i} | Ana | yes | BLOCKER |\n" for i in range(2))
        self.assertEqual(check_card.people_problems(self.brief(two)), [])
        three = two + "| Seat 9 | Ana (per doc) | yes | BLOCKER |\n"
        got = check_card.people_problems(self.brief(three))
        self.assertTrue(any("ana holds 4 BLOCKER seats" in p for p in got), got)

    def test_non_blocker_seats_do_not_count(self):
        many = "".join(f"| Seat {i} | Ana | yes | |\n" for i in range(5))
        self.assertEqual(check_card.people_problems(self.brief(many)), [])

    def test_team_over_four_warns_but_passes(self):
        team = "".join(f"| P{i} | 8/8/8/6 | none | y | yes |\n" for i in range(3))
        seats = "".join(f"| Seat {i} | P{i} | yes | |\n" for i in range(3))
        text = self.brief(seats, team)
        self.assertEqual(check_card.people_problems(text), [])
        self.assertTrue(check_card.people_warnings(text))
        size = lambda t: [w for w in check_card.people_warnings(t) if "Team hours has" in w]  # noqa: E731
        self.assertEqual(size(GOOD_BRIEF), [])
        team4 = "".join(f"| P{i} | 8/8/8/6 | none | y | yes |\n" for i in range(2))
        self.assertEqual(check_card.people_warnings(self.brief(seats, team4)), [])

    def test_fewer_than_two_cpp_teammates_warns_but_passes(self):
        # GOOD_BRIEF: Rick y, Ana n -> 1 of 2.
        self.assertEqual(check_card.people_problems(GOOD_BRIEF), [])
        got = check_card.people_warnings(GOOD_BRIEF)
        self.assertTrue(any("only 1 teammate(s) built UE C++" in w and "D3" in w for w in got), got)
        two = GOOD_BRIEF.replace("| D2 12:00-14:00 | n | yes |", "| D2 12:00-14:00 | y | yes |")
        self.assertEqual(check_card.people_warnings(two), [])
        unfilled = GOOD_BRIEF.replace("| D2 12:00-14:00 | n | yes |", "| D2 12:00-14:00 | TBD | yes |")
        self.assertEqual(check_card.people_warnings(unfilled), [])  # --people fails that row instead


class Queue(unittest.TestCase):
    def test_three_in_review_pass_four_fail(self):
        three = [issue(n, f"Source/{n}/**", "Ana") for n in range(1, 4)] + [issue(9, "Source/9/**", "Rick")]
        info, got = check_card.queue_report(three)
        self.assertEqual(got, [])
        self.assertEqual(info, ["Review queue: ana 3, rick 1"])
        info, got = check_card.queue_report(three + [issue(4, "Source/4/**", "Ana")])
        self.assertEqual(len(got), 1)
        self.assertTrue(got[0].startswith("QUEUE ana has 4 cards in review"), got)

    def test_cli(self):
        for n, code in [(3, 0), (4, 1)]:
            sys.stdin = io.StringIO(json.dumps([issue(i, f"Source/{i}/**", "Ana") for i in range(n)]))
            try:
                with redirect_stdout(io.StringIO()):
                    self.assertEqual(check_card.main(["--queue"]), code)
            finally:
                sys.stdin = sys.__stdin__

    def test_two_stdin_modes_are_refused(self):
        with redirect_stderr(io.StringIO()):
            self.assertEqual(check_card.main(["--queue", "--lanes"]), 2)


def labeled(when, name="doing", event="labeled"):
    return {"event": event, "created_at": when, "label": {"name": name}}


class Overrun(unittest.TestCase):
    # Budget 60 + 15 = 75 min; OVERRUN fires past 135 min in doing.
    NOW = dt.datetime.fromisoformat("2026-11-13T12:00:00+00:00")

    def card(self, timeline, budget="60 min agent + 15 min human, MVP"):
        c = issue(5, "Source/A/**", "Ana", budget)
        c["timeline"] = timeline
        return c

    def test_within_and_over_budget_pass(self):
        info, got = check_card.overrun_report([self.card([labeled("2026-11-13T10:45:00Z")])], self.NOW)
        self.assertEqual(got, [])
        self.assertEqual(info, ["#5 doing 75 of 75 min"])
        info, got = check_card.overrun_report([self.card([labeled("2026-11-13T09:45:00Z")])], self.NOW)
        self.assertEqual(got, [])
        self.assertTrue(info[0].startswith("OVER BUDGET #5 +60 min"), info)

    def test_past_60_over_fires(self):
        info, got = check_card.overrun_report([self.card([labeled("2026-11-13T09:44:00Z")])], self.NOW)
        self.assertEqual(len(got), 1)
        self.assertTrue(got[0].startswith("OVERRUN #5 +61 min"), got)

    def test_card_at_the_caps_fires_at_240_min(self):
        # 120 agent + 60 human + 60 = 240 min (D-new-overrun-timer). D-new-feature-box asks whether a
        # feature should fire sooner (e.g. 181 min); change this test only when that row is decided.
        cap = "120 min agent + 60 min human, MVP"
        for mins, fires in [(181, False), (240, False), (241, True)]:
            start = (self.NOW - dt.timedelta(minutes=mins)).isoformat()
            with self.subTest(mins=mins):
                _, got = check_card.overrun_report([self.card([labeled(start)], cap)], self.NOW)
                self.assertEqual(bool(got), fires, got)

    def test_time_off_doing_does_not_count(self):
        # 3 h since first doing, but 2 h of it blocked: 60 min in doing.
        tl = [labeled("2026-11-13T09:00:00Z"), labeled("2026-11-13T09:30:00Z", event="unlabeled"),
              labeled("2026-11-13T09:30:00Z", "blocked"), labeled("2026-11-13T11:30:00Z")]
        info, got = check_card.overrun_report([self.card(tl)], self.NOW)
        self.assertEqual(got, [])
        self.assertEqual(info, ["#5 doing 60 of 75 min"])

    def test_bug_without_budget_is_timed_against_zero(self):
        bug = {"number": 8, "title": "Ella clips through ledge", "body": "Steps: jump",
               "timeline": [labeled("2026-11-13T10:59:00Z")]}
        info, got = check_card.overrun_report([bug], self.NOW)
        self.assertTrue(got and got[0].startswith("OVERRUN #8 +61 min") and "no Budget" in got[0], got)

    def test_no_doing_event_is_a_problem(self):
        info, got = check_card.overrun_report([self.card([labeled("2026-11-13T09:00:00Z", "review")])], self.NOW)
        self.assertTrue(any("can't time it" in p for p in got), got)

    def test_fetch_is_used_when_no_timeline(self):
        c = issue(5, "Source/A/**", "Ana")
        seen = []
        info, got = check_card.overrun_report([c], self.NOW, fetch=lambda n: seen.append(n) or [labeled("2026-11-13T11:00:00Z")])
        self.assertEqual(seen, [5])
        self.assertEqual(got, [])

    def test_cli(self):
        for start, code in [("2026-11-13T10:00:00Z", 0), ("2026-11-13T08:00:00Z", 1)]:
            sys.stdin = io.StringIO(json.dumps([self.card([labeled(start)])]))
            try:
                with redirect_stdout(io.StringIO()) as out:
                    self.assertEqual(check_card.main(["--overrun", "--now", "2026-11-13T12:00:00+00:00"]), code)
            finally:
                sys.stdin = sys.__stdin__
            if code:
                self.assertIn("OVERRUN #5", out.getvalue())


class HardStop(unittest.TestCase):
    # GOOD_BRIEF: Hard stop 01:00-08:00, Clock zone -05:00.
    SINCE = dt.datetime.fromisoformat("2026-11-13T00:00-05:00")

    def test_commit_inside_window_fails(self):
        lines = ["a" * 40 + "\t2026-11-14T07:30:00+00:00\tAna\tGitHub",   # 02:30 local
                 "b" * 40 + "\t2026-11-14T13:30:00+00:00\tRick\tRick"]    # 08:30 local
        got = check_card.hardstop_problems(lines, GOOD_BRIEF, self.SINCE)
        self.assertEqual(len(got), 1, got)
        self.assertIn("by Ana (committed by GitHub)", got[0])

    def test_edges_and_old_commits(self):
        lines = ["c" * 40 + "\t2026-11-14T00:59:00-05:00\tAna\tAna",
                 "d" * 40 + "\t2026-11-14T08:00:00-05:00\tAna\tAna",
                 "e" * 40 + "\t2026-11-12T03:00:00-05:00\tAna\tAna"]  # before --since
        self.assertEqual(check_card.hardstop_problems(lines, GOOD_BRIEF, self.SINCE), [])

    def test_window_across_midnight(self):
        text = GOOD_BRIEF.replace("Hard stop: 01:00-08:00", "Hard stop: 23:00-07:00")
        got = check_card.hardstop_problems(["f" * 40 + "\t2026-11-13T23:30:00-05:00\tBo\tBo"], text, self.SINCE)
        self.assertTrue(got)
        self.assertEqual(check_card.hardstop_problems(["f" * 40 + "\t2026-11-13T22:30:00-05:00\tBo\tBo"],
                                                      text, self.SINCE), [])

    def test_unset_clock_is_a_problem(self):
        got = check_card.hardstop_problems([], GOOD_BRIEF.replace("Hard stop: 01:00-08:00", "Hard stop: TBD"), self.SINCE)
        self.assertTrue(got)

    def test_cli(self):
        with tempfile.TemporaryDirectory() as d:
            brief, log = os.path.join(d, "brief.md"), os.path.join(d, "log.txt")
            with open(brief, "w", encoding="utf-8") as f:
                f.write(GOOD_BRIEF)
            for line, code in [("a" * 40 + "\t2026-11-14T10:00:00-05:00\tAna\tAna", 0),
                               ("a" * 40 + "\t2026-11-14T03:00:00-05:00\tAna\tAna", 1)]:
                with open(log, "w", encoding="utf-8") as f:
                    f.write(line + "\n")
                with redirect_stdout(io.StringIO()):
                    rc = check_card.main(["--hardstop", "--brief", brief, "--gitlog", log,
                                          "--now", "2026-11-14T12:00-05:00"])
                self.assertEqual(rc, code)


class Hours(unittest.TestCase):
    # Ana has 4 h on day 2; RESERVE 0.7 books at most 168 min (D-new-reserve).
    # Day 2 has Ana's 2 h away window; day 3 has none.
    def test_within_hours_passes(self):
        cards = [issue(1, "Source/A/**", "Ana", "60 min agent + 84 min human, MVP"),
                 issue(2, "Source/B/**", "Ana", "60 min agent + 84 min human, MVP")]
        self.assertEqual(check_card.hours_problems(cards, GOOD_BRIEF, 3), [])

    def test_over_hours_fails(self):
        cards = [issue(1, "Source/A/**", "Ana", "60 min agent + 84 min human, MVP"),
                 issue(2, "Source/B/**", "Ana", "60 min agent + 85 min human, MVP")]
        got = check_card.hours_problems(cards, GOOD_BRIEF, 3)
        self.assertTrue(any(p.startswith("ana: 169 min") and "168 min" in p for p in got), got)

    def test_away_window_is_subtracted(self):
        # Ana is away D2 12:00-14:00: 4 h - 2 h = 2 h, so day 2 books at most 84 min.
        ok = [issue(1, "Source/A/**", "Ana", "60 min agent + 84 min human, MVP")]
        self.assertEqual(check_card.hours_problems(ok, GOOD_BRIEF, 2), [])
        over = [issue(1, "Source/A/**", "Ana", "60 min agent + 85 min human, MVP")]
        got = check_card.hours_problems(over, GOOD_BRIEF, 2)
        self.assertTrue(any("ana: 85 min" in p and "2 h away" in p and "84 min" in p for p in got), got)
        self.assertEqual(check_card.hours_problems(over, GOOD_BRIEF, 1), [])  # away only on D2

    def test_away_window_past_midnight_and_parse(self):
        self.assertEqual(check_card.away_hours("D1 23:00-01:00, D3 09:00-10:30"), {1: 2.0, 3: 1.5})
        self.assertEqual(check_card.away_hours("none"), {})

    def test_full_day_booked_fails_reserve(self):
        # 240 min fits 4 h exactly, but leaves no reserve.
        cards = [issue(1, "Source/A/**", "Ana", "60 min agent + 240 min human, MVP")]
        self.assertTrue(check_card.hours_problems(cards, GOOD_BRIEF, 2))

    def test_asset_card_needs_open_integrator_card(self):
        def asset(num, used_by):
            c = issue(num, "Art/Source/Ella/**", "Rick", "60 min agent + 20 min human, MVP")
            c["body"] = c["body"].replace("Gameplay Dev\n", "Asset Specialist\n", 1).replace(
                "BP_Spikes (Integrator card UE-040)", used_by)
            return c
        integ = issue(40, "Content/UmbrellaElla/Blueprints/Ella/**", "Rick", "30 min agent + 20 min human, MVP")
        self.assertEqual(check_card.hours_problems([asset(7, "Integrator card #40"), integ], GOOD_BRIEF, 1), [])
        self.assertEqual(check_card.hours_problems([asset(7, "Integrator card UE-40"), integ], GOOD_BRIEF, 1), [])
        got = check_card.hours_problems([asset(7, "Integrator card #41"), integ], GOOD_BRIEF, 1)
        self.assertTrue(any(p.startswith("#7: asset card") for p in got), got)
        got = check_card.hours_problems([asset(7, "Integrator card #40")], GOOD_BRIEF, 1)
        self.assertTrue(any(p.startswith("#7: asset card") for p in got), got)

    def test_unknown_person_and_bad_budget_fail(self):
        got = check_card.hours_problems([issue(1, "Source/A/**", "Zed")], GOOD_BRIEF, 1)
        self.assertTrue(any("no Team hours row" in p for p in got), got)
        got = check_card.hours_problems([issue(1, "Source/A/**", "Ana", "whenever")], GOOD_BRIEF, 1)
        self.assertTrue(any("can't count it" in p for p in got), got)


class Lanes(unittest.TestCase):
    def test_disjoint_lanes_pass(self):
        cards = [issue(1, "Source/UmbrellaElla/{Public,Private}/Hazard/**"),
                 issue(2, "Source/UmbrellaElla/{Public,Private}/Movement/**"),
                 issue(3, "Content/UmbrellaElla/Maps/L_S1.umap", locks="Content/UmbrellaElla/Maps/L_S1.umap"),
                 issue(4, "Content/UmbrellaElla/Maps/L_S2.umap", locks="Content/UmbrellaElla/Maps/L_S2.umap"),
                 issue(5, "GitHub only")]
        self.assertEqual(check_card.lanes_problems(cards), [])

    def test_overlapping_glob_fails(self):
        cards = [issue(1, "Source/UmbrellaElla/{Public,Private}/Hazard/**"),
                 issue(2, "Source/UmbrellaElla/Private/**")]
        got = check_card.lanes_problems(cards)
        self.assertTrue(any("#1 and #2 share a lane" in p for p in got), got)

    def test_card_05_lane_leaves_the_mvp_test_folders_free(self):
        # Final-7 A M3: 0.5 and the MVP cards are filed at the same moment; 0.5 owned all of Private/Tests/**
        with open(os.path.join(ROOT, "pipeline", "day0-cards.md"), encoding="utf-8") as f:
            row = next(ln for ln in f if ln.startswith("| 0.5 |"))
        lane = [c.strip() for c in row.strip().strip("|").split("|")][4]
        mvp = issue(32, "Source/UmbrellaElla/{Public,Private}/Umbrella/**, Source/UmbrellaElla/Private/Tests/Umbrella/**")
        self.assertEqual(check_card.lanes_problems([issue(21, lane), mvp]), [])
        old = issue(21, "Source/UmbrellaElla/Private/Tests/**")   # the old lane, broken on purpose
        self.assertTrue(any("#21 and #32 share a lane" in p for p in check_card.lanes_problems([old, mvp])))

    # Dry run 2, H2: two MVP cards that each set their own test-map row may run in parallel
    def test_test_map_row_edits_do_not_collide(self):
        cards = [issue(12, "Source/UmbrellaElla/{Public,Private}/Umbrella/**, pipeline/qa/test-map.md"),
                 issue(13, "Source/UmbrellaElla/{Public,Private}/Movement/**, pipeline/qa/test-map.md")]
        self.assertEqual(check_card.lanes_problems(cards), [])

    # Dry run B: decision rows in the same PR as the lane, and theme card 0.19 next to card 0.0
    def test_decisions_and_jam_brief_lines_do_not_collide(self):
        cards = [issue(12, "Source/UmbrellaElla/Private/Umbrella/**, docs/decisions.md"),
                 issue(13, "Source/UmbrellaElla/Private/Movement/**, docs/decisions.md, docs/jam-brief.md"),
                 issue(14, "docs/jam-brief.md Theme lines, docs/gdd/GDD-B1.0.md")]
        self.assertEqual(check_card.lanes_problems(cards), [])
        cards.append(issue(15, "docs/gdd/GDD-B1.0.md"))
        self.assertTrue(any("#14 and #15" in p for p in check_card.lanes_problems(cards)))

    def test_other_shared_doc_still_collides(self):
        cards = [issue(12, "Source/UmbrellaElla/Private/Umbrella/**, docs/balance.md"),
                 issue(13, "Source/UmbrellaElla/Private/Movement/**, docs/balance.md")]
        self.assertTrue(any("docs/balance.md" in p for p in check_card.lanes_problems(cards)))

    def test_exact_file_inside_glob_fails(self):
        cards = [issue(1, "Source/UmbrellaElla/Private/Hazard/**"),
                 issue(2, "Source/UmbrellaElla/Private/Hazard/Spikes.cpp")]
        self.assertTrue(check_card.lanes_problems(cards))

    def test_same_umap_and_lock_fail(self):
        m = "Content/UmbrellaElla/Maps/L_S1.umap"
        got = check_card.lanes_problems([issue(1, m, locks=m), issue(2, m, locks=m)])
        self.assertTrue(any("share a .umap" in p for p in got), got)
        self.assertTrue(any("both lock" in p for p in got), got)

    def test_cli_reads_gh_json(self):
        m = "Content/UmbrellaElla/Maps/L_S1.umap"
        for cards, code in [([issue(1, "Source/A/**"), issue(2, "Source/B/**")], 0), ([issue(1, m), issue(2, m)], 1)]:
            sys.stdin = io.StringIO(json.dumps(cards))
            try:
                with redirect_stdout(io.StringIO()):
                    self.assertEqual(check_card.main(["--lanes"]), code)
            finally:
                sys.stdin = sys.__stdin__


class Status(unittest.TestCase):
    NOW = dt.datetime.fromisoformat("2026-11-14T09:00-05:00")

    VALUES = {"Next gate": "at risk, spikes card is 40 min over", "Absences next 12h": "none"}

    def body(self, **over):
        fields = check_card.status_fields(ROOT)
        vals = dict(self.VALUES, **over)
        return "ROLE: Producer | session x\n" + " | ".join(f + ": " + vals.get(f, "x") for f in fields)

    def test_next_gate_needs_a_value_and_reason(self):
        for v, ok in [("on track, all MVP 1-3 in build", True), ("will miss (MVP 2 blocked)", False),
                      ("", False), ("at risk", False), ("fine, going well", False), ("x", False),
                      # final-7 A M2: ordinary wording passes; a bare number or symbol is still no reason
                      ("on track, G1 21:00 package green", True), ("at risk: 2 cards blocked", True),
                      ("on track - 0.6 and 0.8 in review", True), ("at risk (G1 package not yet green)", True),
                      ("at risk: 2", False), ("on track -", False)]:
            with self.subTest(v=v):
                c = [{"createdAt": "2026-11-14T08:00:00-05:00", "body": self.body(**{"Next gate": v})}]
                got = check_card.status_problems(c, self.NOW)
                self.assertEqual(got == [], ok, got)

    def test_will_miss_needs_a_cut_proposal_since_the_last_gate(self):
        # GOOD_BRIEF G1 was 2026-11-13T20:00-05:00; NOW is the next morning.
        status = {"createdAt": "2026-11-14T08:00:00-05:00", "body": self.body(**{"Next gate": "will miss, MVP 5 blocked"})}
        upload = {"createdAt": "2026-11-13T19:00:00-05:00",
                  "body": "Jam-page test upload: https://example.test/g | sha256=" + "ab" * 32}
        cut = {"createdAt": "2026-11-14T08:05:00-05:00", "body": "Cut proposed: 2 Music (keep sound effects)"}
        self.assertEqual(check_card.status_problems([status, upload, cut], self.NOW, ROOT, GOOD_BRIEF), [])
        for name, comments in [("no proposal", [status, upload]),
                               ("before the last gate", [status, upload, dict(cut, createdAt="2026-11-13T19:30:00-05:00")]),
                               ("placeholder", [status, upload, dict(cut, body="Cut proposed: <item>")]),
                               ("empty", [status, upload, dict(cut, body="Cut proposed:")])]:
            with self.subTest(case=name):
                got = check_card.status_problems(comments, self.NOW, ROOT, GOOD_BRIEF)
                self.assertTrue(any("will miss" in p for p in got), got)
        at_risk = dict(status, body=self.body())
        self.assertEqual(check_card.status_problems([at_risk, upload], self.NOW, ROOT, GOOD_BRIEF), [])

    def test_absences_must_be_none_or_a_name(self):
        for v, ok in [("none", True), ("Ana D2 12:00-14:00", True), ("", False), ("TBD", False), ("-", False)]:
            with self.subTest(v=v):
                c = [{"createdAt": "2026-11-14T08:00:00-05:00", "body": self.body(**{"Absences next 12h": v})}]
                got = check_card.status_problems(c, self.NOW)
                self.assertEqual(got == [], ok, got)

    def test_retro_questions_needed_one_hour_before_a_gate(self):
        # GOOD_BRIEF G2 is 2026-11-14T20:00-05:00; G1 was 2026-11-13T20:00-05:00.
        now = dt.datetime.fromisoformat("2026-11-14T19:30-05:00")
        status = {"createdAt": "2026-11-14T19:00:00-05:00", "body": self.body()}
        upload = {"createdAt": "2026-11-13T19:00:00-05:00",
                  "body": "Jam-page test upload: https://example.test/g | sha256=" + "ab" * 32}
        retro = {"createdAt": "2026-11-14T18:55:00-05:00",
                 "body": "What slowed us since the last gate? What do we change for the next one?"}
        self.assertEqual(check_card.status_problems([status, upload, retro], now, ROOT, GOOD_BRIEF), [])
        got = check_card.status_problems([status, upload], now, ROOT, GOOD_BRIEF)
        self.assertEqual(len(got), 2, got)
        self.assertTrue(all("G2 is due within 1 h" in p for p in got), got)
        old = dict(retro, createdAt="2026-11-13T18:55:00-05:00")  # asked before G1, not for G2
        self.assertEqual(len(check_card.status_problems([status, upload, old], now, ROOT, GOOD_BRIEF)), 2)
        two_h_before = dt.datetime.fromisoformat("2026-11-14T18:00-05:00")
        self.assertEqual(check_card.status_problems([status, upload], two_h_before, ROOT, GOOD_BRIEF), [])

    def test_format_has_absences_and_hard_stop(self):
        fields = check_card.status_fields(ROOT)
        self.assertIn("Absences next 12h", fields)
        self.assertIn("Past hard stop", fields)
        self.assertIn("Accepted since last status", fields)

    def test_fresh_full_status_passes(self):
        c = [{"createdAt": "2026-11-14T08:00:00-05:00", "body": self.body()}]
        self.assertEqual(check_card.status_problems(c, self.NOW), [])

    def test_old_status_fails(self):
        c = [{"createdAt": "2026-11-13T20:00:00-05:00", "body": self.body()},
             {"createdAt": "2026-11-14T08:00:00-05:00", "body": "a normal comment"}]
        got = check_card.status_problems(c, self.NOW)
        self.assertTrue(any("13.0 h old" in p for p in got), got)

    def test_missing_field_fails(self):
        c = [{"createdAt": "2026-11-14T08:00:00-05:00", "body": self.body().replace("Absences next 12h", "Away")}]
        got = check_card.status_problems(c, self.NOW)
        self.assertEqual(got, ["last status line has no 'Absences next 12h' field"])

    def test_no_status_fails(self):
        self.assertTrue(check_card.status_problems([], self.NOW))

    def test_test_upload_needed_after_g1(self):
        # GOOD_BRIEF G1 is 2026-11-13T20:00-05:00; NOW is the morning after.
        status = {"createdAt": "2026-11-14T08:00:00-05:00", "body": self.body()}
        upload = {"createdAt": "2026-11-13T19:00:00-05:00",
                  "body": "Jam-page test upload: https://example.test/g/ue | sha256=" + "ab" * 32 + " | relaunched: yes"}
        self.assertEqual(check_card.status_problems([status, upload], self.NOW, ROOT, GOOD_BRIEF), [])
        got = check_card.status_problems([status], self.NOW, ROOT, GOOD_BRIEF)
        self.assertTrue(any("test upload" in p for p in got), got)
        no_hash = dict(upload, body="Jam-page test upload: https://example.test/g/ue | sha256=TBD")
        self.assertTrue(check_card.status_problems([status, no_hash], self.NOW, ROOT, GOOD_BRIEF))
        before_g1 = dt.datetime.fromisoformat("2026-11-13T19:59-05:00")
        early = dict(status, createdAt="2026-11-13T18:00:00-05:00")
        retro = {"createdAt": "2026-11-13T19:00:00-05:00",
                 "body": "What slowed us since the last gate? What do we change for the next one?"}
        self.assertEqual(check_card.status_problems([early, retro], before_g1, ROOT, GOOD_BRIEF), [])



def tracker_body(rows=None):
    rows = rows if rows is not None else [f"| {n} | #{n + 10} | todo | - | - |" for n in range(1, 16)]  # MVP 1-15 (docs/jam-brief.md, GDD SH1.0 P0)
    return "Jam tracker\n\n| MVP | Card | Status | Build sha | Playtest |\n|---|---|---|---|---|\n" + "\n".join(rows)


class Tracker(unittest.TestCase):
    def test_eight_todo_rows_pass(self):
        self.assertEqual(check_card.tracker_problems(tracker_body()), [])

    def test_template_example_rows_pass(self):
        rows = [f"| {n} | #{n + 10} | todo | - | - |" for n in range(3, 16)]
        rows = ["| 1 | #12 | in build | 1a2b3c4 | - |", "| 2 | #13 | passed | 1a2b3c4 | P1 pass 2026-11-13 |"] + rows
        self.assertEqual(check_card.tracker_problems(tracker_body(rows)), [])

    def test_each_break_is_caught(self):
        base = [f"| {n} | #{n + 10} | todo | - | - |" for n in range(1, 16)]
        cases = {
            "missing row": base[:-1],
            "duplicate row": base + [base[0]],
            "unknown status": ["| 1 | #11 | almost | - | - |"] + base[1:],
            "passed without sha": ["| 1 | #11 | passed | - | P1 pass 2026-11-13 |"] + base[1:],
            "in build without sha": ["| 1 | #11 | in build | soon | - |"] + base[1:],
            "passed without playtest": ["| 1 | #11 | passed | 1a2b3c4 | - |"] + base[1:],
            "no card": ["| 1 | later | todo | - | - |"] + base[1:],
            "item 13": base + ["| 13 | #30 | todo | - | - |"],
        }
        for name, rows in cases.items():
            with self.subTest(case=name):
                self.assertTrue(check_card.tracker_problems(tracker_body(rows)), name)
        self.assertTrue(check_card.tracker_problems("no table here"))

    def test_p0_mvp_row_cut_needs_an_explicit_override(self):
        """Dry run A H3: a P0 MVP item marked cut passed."""
        base = [f"| {n} | #{n + 10} | todo | - | - |" for n in range(1, 16)]
        rows = [r if not r.startswith("| 7 |") else "| 7 | - | cut | - | - |" for r in base]
        got = check_card.tracker_problems(tracker_body(rows))
        self.assertTrue(any("MVP 7: 'cut'" in p for p in got), got)
        root = tempfile.mkdtemp()
        os.makedirs(os.path.join(root, "docs"))
        shutil.copy(os.path.join(ROOT, "docs", "jam-brief.md"), os.path.join(root, "docs"))
        with open(os.path.join(root, "docs", "decisions.md"), "w", encoding="utf-8") as f:
            f.write("| ID | Decision | Owner | Status |\n|---|---|---|---|\n" "| D-cut | Cut the tutorial. Overrides: FLOW-03 | Rick | DECIDED 2026-11-15 (Rick) |\n")
        got = check_card.tracker_problems(tracker_body(rows), root)
        self.assertTrue(any("MOVE-16" in p for p in got), got)  # half an override is not enough
        with open(os.path.join(root, "docs", "decisions.md"), "w", encoding="utf-8") as f:
            f.write("| ID | Decision | Owner | Status |\n|---|---|---|---|\n" "| D-cut | Cut the tutorial. Overrides: FLOW-03, MOVE-16 | Rick | DECIDED 2026-11-15 (Rick) |\n")
        self.assertEqual(check_card.tracker_problems(tracker_body(rows), root), [])
        shutil.rmtree(root)

    def test_status_cli_runs_tracker_and_needs_body(self):
        brief = os.path.join(tempfile.mkdtemp(), "brief.md")
        with open(brief, "w", encoding="utf-8") as f:
            f.write(GOOD_BRIEF)
        status = {"createdAt": "2026-11-14T08:00:00-05:00", "body": Status().body()}
        upload = {"createdAt": "2026-11-13T19:00:00-05:00",
                  "body": "Jam-page test upload: https://example.test/g | sha256=" + "ab" * 32}
        args = ["--status", "--brief", brief, "--now", "2026-11-14T09:00-05:00"]
        real_hook = check_card.submission_status
        check_card.submission_status = lambda *a, **k: []
        self.addCleanup(setattr, check_card, "submission_status", real_hook)
        for data, code in [({"body": tracker_body(), "comments": [status, upload]}, 0),
                           ({"comments": [status, upload]}, 1),
                           ({"body": tracker_body([]), "comments": [status, upload]}, 1)]:
            sys.stdin = io.StringIO(json.dumps(data))
            try:
                with redirect_stdout(io.StringIO()):
                    self.assertEqual(check_card.main(args), code, data.keys())
            finally:
                sys.stdin = sys.__stdin__
        sys.stdin = io.StringIO(json.dumps({"body": tracker_body([])}))
        try:
            with redirect_stdout(io.StringIO()):
                self.assertEqual(check_card.main(["--tracker"]), 1)
        finally:
            sys.stdin = sys.__stdin__


class StatusHook(unittest.TestCase):
    """--status runs the daily submission checks (submission_check.status_hook); dry runs found it unwired."""

    def test_status_cli_fails_when_the_daily_submission_check_fails(self):
        brief = os.path.join(tempfile.mkdtemp(), "brief.md")
        with open(brief, "w", encoding="utf-8") as f:
            f.write(GOOD_BRIEF)
        status = {"createdAt": "2026-11-14T08:00:00-05:00", "body": Status().body()}
        upload = {"createdAt": "2026-11-13T19:00:00-05:00",
                  "body": "Jam-page test upload: https://example.test/g | sha256=" + "ab" * 32}
        data = {"body": tracker_body(), "comments": [status, upload]}
        real_hook = check_card.submission_status
        self.addCleanup(setattr, check_card, "submission_status", real_hook)
        for hook, code in ((lambda *a, **k: ["submission (Day 1): devlog has no Day 1 line"], 1), (lambda *a, **k: [], 0)):
            check_card.submission_status = hook
            sys.stdin = io.StringIO(json.dumps(data))
            try:
                with redirect_stdout(io.StringIO()):
                    self.assertEqual(check_card.main(["--status", "--brief", brief, "--now", "2026-11-14T09:00-05:00"]), code)
            finally:
                sys.stdin = sys.__stdin__

    def test_hook_is_the_submission_status_hook(self):
        import submission_check
        now = check_card.parse_time("2026-11-14T09:00-05:00")
        self.assertEqual(check_card.submission_status(GOOD_BRIEF, now, ROOT),
                         submission_check.status_hook(GOOD_BRIEF, now, ROOT))


RISK_BRIEF = GOOD_BRIEF + """
## Top risks
| Risk | Trigger | Fallback | Owner |
|---|---|---|---|
| A | a | a | Rick |
| B | b | b | Ana |
"""

GOOD_RECORD = """Gate: G1 | due 2026-11-13T20:00-05:00 | closed 2026-11-13T20:30-05:00 | late by 0.5 h
Build: 1a2b3c4 | Team_Game.zip | Development
MVP items for this gate: MVP 1 pass | MVP 2 pass | MVP 3 pass | MVP 4 pass | MVP 5 pass | MVP 6 pass (build record #40)
Playtests for this gate: P1 pass, P2 pass, results-log rows 3-4
Jam-page test upload (G1 on): https://example.test/g | sha256=3f1c9a0e2b4d6f8a1c3e5a7b9d0f2a4c6e8b0d2f4a6c8e0b2d4f6a8c0e2b4d6f | re-downloaded and launched: yes
Open P0/P1: none
PLAYTHROUGH: PASS: PLAYTHROUGH 1a2b3c4: G1: survived, fail-retry, fail-bottom, quit-title, quit-pause passed
Repeat boots: DAILY 1a2b3c4 | win-1/Windows 11 | Development | clean-tree=PASS build=PASS test=PASS(40/0/40) validate=PASS(err 0, warn 0) package=PASS(warn 0) smoke=PASS(2 map(s), repeat 5/5) display=PASS(5 mode(s)) settings=PASS(garbage+old ini) client-test=PASS | Not checked: none
Gate checks: ui_check ci: PASS (0 problem(s)) | PASS: Team_Game.zip config=Development platform=Win64 commit=1a2b3c4 sha256=3f1c9a0e2b4d6f8a1c3e5a7b9d0f2a4c6e8b0d2f4a6c8e0b2d4f6a8c0e2b4d6f
Cut fired: no
What slowed us / change for next gate: review queue; merge twice a day
Process change: #77, owner Producer
Incidents since last gate: #51 cause=code missed-by=none follow-up=#78
Verdicts: design Ana pass #60 | art Rick pass #61 | UI ui_check ci: PASS | tech Rick pass #62
Risks: 1 fired no | 2 fired yes, owner Ana, fallback started
Proposed outcome: Pass
BUTLER version=v15.24.0 login=ok user=team by=Rick
"""


ALL_MVP = "MVP items for this gate: " + " | ".join(f"MVP {n} pass" for n in range(1, 16)) + " (build record #40)"


def for_gate(rec, gate):
    """GOOD_RECORD moved to another gate: its PLAYTHROUGH line and, from G2 on, all twelve MVP items."""
    rec = rec.replace("Gate: G1", "Gate: " + gate).replace("PLAYTHROUGH 1a2b3c4: G1:", f"PLAYTHROUGH 1a2b3c4: {gate}:")
    due = {"G1": "2026-11-13T20:00", "G2": "2026-11-14T20:00", "G3": "2026-11-15T20:00", "G4": "2026-11-16T12:00"}[gate]
    rec = rec.replace("due 2026-11-13T20:00-05:00 | closed 2026-11-13T20:30-05:00",
                      f"due {due}-05:00 | closed {due[:-2]}30-05:00")
    if gate != "G1":
        rec = re.sub(r"^MVP items for this gate:.*$", ALL_MVP, rec, flags=re.M)
        rec = rec.replace("ui_check ci: PASS", "ui_check ci --release: PASS")
    return rec


def git_t(root, *args):
    import subprocess
    return subprocess.run(["git", "-c", "user.email=t@t", "-c", "user.name=t", *args], cwd=root, check=True,
                          capture_output=True, text=True).stdout.strip()


def g4_head(root, msg="commit"):
    git_t(root, "add", "-A")
    git_t(root, "commit", "-qm", msg)
    return git_t(root, "rev-parse", "HEAD")


def bake_into(root, preset="T-01"):
    sys.path.insert(0, HERE)
    import test_bake_preset as tb
    import bake_preset as bp
    e = json.loads(json.dumps(tb.EXPORT))
    e["preset"] = preset
    path = os.path.join(root, "Saved", "config.json")
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(e, f)
    with redirect_stdout(io.StringIO()) as out:
        rc = bp.main(["--root", root, "bake", path])
    assert rc == 0, out.getvalue()


def g4_repo(case, preset="T-01", decisions=None, bake=True):
    """A git repo with the gate template, a small manifest, marked Source/ headers and (bake=True) a committed
    bake of the preset: the G4 record's Build commit (final-7 B H8)."""
    sys.path.insert(0, HERE)
    import test_bake_preset as tb
    import bake_preset as bp
    root = tempfile.mkdtemp()
    case.addCleanup(shutil.rmtree, root, True)
    for rel_path, text in ((bp.MANIFEST, bp.dump_json(tb.MANIFEST)), (bp.PRESETS, bp.dump_json(tb.PRESETS)),
                           ("Source/UmbrellaElla/Public/Move/EllaMovementTuning.h", tb.MOVE_H),
                           ("Source/UmbrellaElla/Public/Catch/CatchTuning.h", tb.CATCH_H),
                           ("Source/UmbrellaElla/Private/Harness/FlagDefaults.h", tb.FLAGS_H),
                           ("Source/UmbrellaElla/Public/Attack/AttackTuning.h", tb.COM_H),
                           (".gitignore", "Saved/\n"),
                           ("docs/decisions.md", (decisions or "| ID | Decision | Owner | Status |\n|---|---|---|---|\n")
                            + tb.DECIDED_TUNE)):   # final-9 B H1: the fixture's tuned numbers are Richard's
        tb.write(os.path.join(root, rel_path), text)
    os.makedirs(os.path.join(root, "pipeline", "templates"), exist_ok=True)
    shutil.copy(os.path.join(ROOT, "pipeline", "templates", "gate-record.md"), os.path.join(root, "pipeline", "templates"))
    git_t(root, "init", "-q", "-b", "main")
    sha = g4_head(root, "skeleton")
    if bake:
        bake_into(root, preset)
        sha = g4_head(root, "bake")
    return root, sha


def g4_record(sha):
    rec = for_gate(GOOD_RECORD, "G4").replace("Gate: G4 | due 2026-11-13T20:00-05:00", "Gate: G4 | due 2026-11-16T12:00-05:00")
    return rec.replace("1a2b3c4", sha[:7])


BAKED = "Baked preset: T-01 | approved by Rick #90 | bake_preset check: PASS preset=T-01 values=12\n"


class GateRecord(unittest.TestCase):
    def test_template_has_risks_and_retro_lines(self):
        keys = [k for k, _ in check_card.gate_template(ROOT)]
        self.assertIn("Risks", keys)
        self.assertIn("What slowed us / change for next gate", keys)

    def test_good_record_passes(self):
        self.assertEqual(check_card.gate_record_problems(GOOD_RECORD, ROOT, RISK_BRIEF), [])

    # Dry runs: the G1 record needs the BUTLER line, and a bad one fails
    def test_g1_record_without_butler_fails(self):
        rec = GOOD_RECORD.replace("BUTLER version=v15.24.0 login=ok user=team by=Rick\n", "")
        self.assertTrue(any("BUTLER" in p for p in check_card.gate_record_problems(rec, ROOT, RISK_BRIEF)))
        bad = GOOD_RECORD.replace("login=ok", "login=no")
        self.assertTrue(any("login" in p for p in check_card.gate_record_problems(bad, ROOT, RISK_BRIEF)))

    def test_each_break_is_caught(self):
        cases = {
            "no risks line": GOOD_RECORD.replace("Risks: 1 fired no | 2 fired yes, owner Ana, fallback started\n", ""),
            "no slowed line": GOOD_RECORD.replace("What slowed us / change for next gate: review queue; merge twice a day\n", ""),
            "empty slowed": GOOD_RECORD.replace(": review queue; merge twice a day", ":"),
            "template outcome": GOOD_RECORD.replace("Proposed outcome: Pass", "Proposed outcome: Pass | Pass with named exceptions | Miss → cut"),
            "placeholder": GOOD_RECORD.replace("Cut fired: no", "Cut fired: <item>"),
            "risk row missing": GOOD_RECORD.replace("1 fired no | ", ""),
            "fired yes, no owner": GOOD_RECORD.replace("owner Ana, ", ""),
            "no playthrough line": GOOD_RECORD.replace("PLAYTHROUGH: PASS: PLAYTHROUGH 1a2b3c4: G1: survived, fail-retry, fail-bottom, quit-title, quit-pause passed\n", ""),
            "no repeat boots line": re.sub(r"^Repeat boots:.*\n", "", GOOD_RECORD, flags=re.M),
            "repeat boots template": GOOD_RECORD.replace("smoke=PASS(2 map(s), repeat 5/5)", "smoke=PASS(... repeat 5/5)"),
            "no gate checks line": GOOD_RECORD.replace("Gate checks: ui_check ci: PASS (0 problem(s)) | PASS: Team_Game.zip config=Development platform=Win64 commit=1a2b3c4 sha256=3f1c9a0e2b4d6f8a1c3e5a7b9d0f2a4c6e8b0d2f4a6c8e0b2d4f6a8c0e2b4d6f\n", ""),
            # coverage-map ports: discipline verdicts, incident review, process change
            "no verdicts line": GOOD_RECORD.replace("Verdicts: design Ana pass #60 | art Rick pass #61 | UI ui_check ci: PASS | tech Rick pass #62\n", ""),
            "art verdict missing": GOOD_RECORD.replace("art Rick pass #61 | ", ""),
            "design verdict unsigned": GOOD_RECORD.replace("design Ana pass #60", "design Ana #60"),
            "verdict fail but Pass": GOOD_RECORD.replace("tech Rick pass #62", "tech Rick fail #62"),
            "incident without follow-up": GOOD_RECORD.replace(" follow-up=#78", ""),
            "incident without cause": GOOD_RECORD.replace("cause=code ", ""),
            "process change no owner": GOOD_RECORD.replace("Process change: #77, owner Producer", "Process change: merge more"),
            "no incidents line": GOOD_RECORD.replace("Incidents since last gate: #51 cause=code missed-by=none follow-up=#78\n", ""),
        }
        for name, rec in cases.items():
            with self.subTest(case=name):
                self.assertTrue(check_card.gate_record_problems(rec, ROOT, RISK_BRIEF), name)

    def test_none_forms_of_ported_lines_pass(self):
        rec = GOOD_RECORD.replace("Process change: #77, owner Producer", "Process change: none") \
                         .replace("Incidents since last gate: #51 cause=code missed-by=none follow-up=#78", "Incidents since last gate: none")
        self.assertEqual(check_card.gate_record_problems(rec, ROOT, RISK_BRIEF), [])

    def test_g4_record_needs_final_upload_three_hours_early(self):
        root, sha = g4_repo(self)
        g4 = g4_record(sha)
        ok = g4 + "Final upload: 2026-11-16T13:30-05:00\n" + BAKED
        self.assertEqual(check_card.gate_record_problems(ok, root, RISK_BRIEF), [])
        got = check_card.gate_record_problems(g4, root, RISK_BRIEF)
        self.assertTrue(any("Final upload" in p for p in got), got)
        late = g4 + "Final upload: 2026-11-16T14:30-05:00\n"
        got = check_card.gate_record_problems(late, root, RISK_BRIEF)
        self.assertTrue(any("less than 3 h" in p for p in got), got)
        self.assertEqual(check_card.gate_record_problems(GOOD_RECORD, ROOT, RISK_BRIEF), [])  # G1 needs none

    def test_g4_record_needs_the_baked_preset_check(self):
        # D-new-workbench-debug: the shipped defaults are the approved preset; the record names it.
        root, sha = g4_repo(self)
        g4 = g4_record(sha) + "Final upload: 2026-11-16T13:30-05:00\n"
        self.assertEqual(check_card.gate_record_problems(g4 + BAKED, root, RISK_BRIEF), [])
        cases = {"missing": "", "no check pasted": "Baked preset: T-01 | approved by Rick #90\n",
                 "other preset": BAKED.replace("PASS preset=T-01", "PASS preset=T-03"),
                 "failed check": BAKED.replace("PASS preset=T-01 values=12", "FAIL 1 problem(s)"),
                 # final-7 B H8: a FAIL pasted next to a PASS
                 "fail then pass": BAKED.replace("bake_preset check: PASS", "bake_preset check: FAIL 2 problem(s) | bake_preset check: PASS"),
                 "not BASE, no decision": BAKED.replace("T-01", "T-03")}
        for name, line in cases.items():
            with self.subTest(case=name):
                got = check_card.gate_record_problems(g4 + line, root, RISK_BRIEF)
                self.assertTrue(any("Baked preset" in p or "bake check" in p or "not T-01" in p for p in got), got)

    def test_g4_build_commit_must_hold_the_bake(self):
        """Final-7 B H8: the record's Build commit is a real commit on the branch, and its own tree passes the
        complete bake check; a package built before the bake merged, or with a drifted default, fails."""
        root, before = g4_repo(self, bake=False)   # Source/ with markers, nothing baked yet
        bake_into(root)
        after = g4_head(root)
        tail = "Final upload: 2026-11-16T13:30-05:00\n" + BAKED
        self.assertEqual(check_card.gate_record_problems(g4_record(after) + tail, root, RISK_BRIEF), [])
        got = check_card.gate_record_problems(g4_record(before) + tail, root, RISK_BRIEF)
        self.assertTrue(any(f"G4 Build commit {before[:7]} fails `bake_preset check --record`" in p for p in got), got)
        got = check_card.gate_record_problems(g4_record("1a2b3c4") + tail, root, RISK_BRIEF)
        self.assertTrue(any("is not a commit in this clone" in p for p in got), got)
        # a drifted default committed after the bake
        move = os.path.join(root, "Source", "UmbrellaElla", "Public", "Move", "EllaMovementTuning.h")
        with open(move, encoding="utf-8") as f:
            text = f.read()
        with open(move, "w", encoding="utf-8") as f:
            f.write(text.replace("= 640.0f;", "= 650.0f;"))
        drift = g4_head(root, "drift")
        got = check_card.gate_record_problems(g4_record(drift) + tail, root, RISK_BRIEF)
        self.assertTrue(any("unbaked value" in p for p in got), got)
        # a commit on another branch
        git_t(root, "checkout", "-q", "-b", "side", before)
        with open(os.path.join(root, "side.txt"), "w") as f:
            f.write("x\n")
        side = g4_head(root, "side")
        git_t(root, "checkout", "-q", "main")
        got = check_card.gate_record_problems(g4_record(side) + tail, root, RISK_BRIEF)
        self.assertTrue(any("not on the checked-out branch" in p for p in got), got)

    def test_g4_non_base_preset_passes_with_a_decided_row(self):
        mention = ("| ID | Decision | Owner | Status |\n|---|---|---|---|\n" "| D-ship | Ship T-03 | Richard | DECIDED 2026-11-15 (Rick) |\n")
        decided = ("| ID | Decision | Owner | Status |\n|---|---|---|---|\n" "| D-ship | Ship T-03. Overrides: T-03 | Richard | DECIDED 2026-11-15 (Rick) |\n")
        tune = __import__("test_bake_preset").DECIDED_TUNE
        root, sha = g4_repo(self, preset="T-03", decisions=decided)
        g4 = g4_record(sha) + "Final upload: 2026-11-16T13:30-05:00\n" + BAKED.replace("T-01", "T-03")
        self.assertEqual(check_card.gate_record_problems(g4, root, RISK_BRIEF), [])
        # broken on purpose: a DECIDED row that only names T-03 does not lift the BASE rule (dry run B H3)
        with open(os.path.join(root, "docs", "decisions.md"), "w", encoding="utf-8") as f:
            f.write(mention + tune)
        self.assertTrue(any("Overrides: T-03" in p for p in check_card.gate_record_problems(g4, root, RISK_BRIEF)))

    def test_g3_and_g4_need_no_shipping_line(self):
        # The jam takes the Development package (D25); a Shipping run is never required.
        root, sha = g4_repo(self)
        for gate in ("G3", "G4"):
            rec = for_gate(GOOD_RECORD, gate)
            r = ROOT
            if gate == "G4":
                rec = g4_record(sha) + "Final upload: 2026-11-16T13:30-05:00\n" + BAKED
                r = root
            with self.subTest(gate=gate):
                self.assertEqual(check_card.gate_record_problems(rec, r, RISK_BRIEF), [])

    def test_final7_gate_record_attacks(self):
        """Final-7 dry run B M5, M6, M7, M9: each passed before."""
        self.assertEqual(check_card.gate_record_problems(GOOD_RECORD, ROOT, RISK_BRIEF), [])
        late6 = "closed 2026-11-14T02:00-05:00"
        cases = {
            "6 h late, typed 0.5 h": (GOOD_RECORD.replace("closed 2026-11-13T20:30-05:00", late6), "is 6.00 h"),
            "no late field": (GOOD_RECORD.replace(" | late by 0.5 h", ""), "'late by' says nothing"),
            "late in hours word": (GOOD_RECORD.replace("closed 2026-11-13T20:30-05:00 | late by 0.5 h",
                                                       late6 + " | late by 6 hours"), "'late by' says nothing"),
            "due is not the Clock": (GOOD_RECORD.replace("due 2026-11-13T20:00-05:00 | closed 2026-11-13T20:30-05:00",
                                                         "due 2026-11-14T02:00-05:00 | closed 2026-11-14T02:30-05:00"),
                                     "but the Clock in docs/jam-brief.md has"),
            "6 h late, computed, no cut": (GOOD_RECORD.replace("closed 2026-11-13T20:30-05:00 | late by 0.5 h", late6 + " | late by 6 h"),
                                           "'Cut fired:' says no"),
            # final-8 A C1: an entry daily never writes is a hand-edited line; a step that did not run fails by name
            "DAILY not checked smoke": (GOOD_RECORD.replace("Not checked: none", "Not checked: smoke on Win64, package"), "Not checked"),
            "DAILY package not run": (GOOD_RECORD.replace("package=PASS(warn 0)", "package=NOT RUN"), "package=NOT RUN"),
            "P1 not run": (GOOD_RECORD.replace("P1 pass, P2 pass", "P1 not run, P2 pass"), "P1 reads 'not run'"),
            "P1 broken": (GOOD_RECORD.replace("P1 pass, P2 pass", "P1 broken, P2 pass"), "P1 reads 'broken'"),
            "P3 crashed": (GOOD_RECORD.replace("P1 pass, P2 pass", "P1 pass, P2 pass, P3 crashed"), "P3 reads 'crashed'"),
            "verdict fail, no owner": (GOOD_RECORD.replace("tech Rick pass #62", "tech Rick fail #62").replace(
                "Proposed outcome: Pass", "Proposed outcome: Pass with named exceptions: verdict tech fail"),
                "'tech verdict fail' has no 'owner"),
        }
        for name, (rec, why) in cases.items():
            with self.subTest(case=name):
                got = check_card.gate_record_problems(rec, ROOT, RISK_BRIEF)
                self.assertTrue(any(why in p for p in got), got)
        ok = GOOD_RECORD.replace("tech Rick pass #62", "tech Rick fail #62").replace(
            "Proposed outcome: Pass", "Proposed outcome: Pass with named exceptions: tech verdict fail, owner Rick by 18:00")
        self.assertEqual(check_card.gate_record_problems(ok, ROOT, RISK_BRIEF), [])

    def test_ui_release_line_is_required_from_g2(self):
        # Final-7 B H6: the plain `ui_check ci` run skips missing inputs; G2-G4 need the --release run's own line.
        # Final-7 A H1: G1 is the first playable before the player screens, so the plain run is enough there.
        self.assertEqual(check_card.gate_record_problems(GOOD_RECORD, ROOT, RISK_BRIEF), [])
        g1_release = GOOD_RECORD.replace("ui_check ci: PASS", "ui_check ci --release: PASS")
        self.assertEqual(check_card.gate_record_problems(g1_release, ROOT, RISK_BRIEF), [])
        g2 = for_gate(GOOD_RECORD, "G2")
        self.assertEqual(check_card.gate_record_problems(g2, ROOT, RISK_BRIEF), [])
        # broken on purpose: the plain line in Gate checks, then in the UI verdict slot
        plain = g2.replace("Gate checks: ui_check ci --release: PASS", "Gate checks: ui_check ci: PASS")
        got = check_card.gate_record_problems(plain, ROOT, RISK_BRIEF)
        self.assertTrue(any("Gate checks has the plain `ui_check ci` line" in p for p in got), got)
        slot = g2.replace("UI ui_check ci --release: PASS", "UI ui_check ci: PASS")
        got = check_card.gate_record_problems(slot, ROOT, RISK_BRIEF)
        self.assertTrue(any("Verdicts 'UI' has the plain" in p for p in got), got)

    def test_ui_check_release_prints_its_own_name(self):
        import ui_check
        root = tempfile.mkdtemp()
        try:
            for release, name in ((False, "ui_check ci: PASS"), (True, "ui_check ci --release: FAIL")):
                buf = io.StringIO()
                with redirect_stdout(buf):
                    ui_check.main(["--root", root, "ci"] + (["--release"] if release else []))
                self.assertIn(name, buf.getvalue())
        finally:
            shutil.rmtree(root)

    def test_playthrough_scoped_to_another_gate_fails(self):
        g1 = GOOD_RECORD.replace("intro, contest, desperation, survived, fail-retry, fail-bottom and both quits passed",
                                 "G1: fail-bottom, quit-title, quit-pause passed")
        self.assertEqual(check_card.gate_record_problems(g1, ROOT, RISK_BRIEF), [])
        g3 = g1.replace("Gate: G1", "Gate: G3")
        got = check_card.gate_record_problems(g3, ROOT, RISK_BRIEF)
        self.assertTrue(any("checked for G1, not G3" in p for p in got), got)

    def test_pass_with_failing_lines_is_caught(self):
        # Dry-run finding: a G1 record with failing MVP items, an open P0 and FAIL lines proposed Pass and exited 0.
        cases = {
            "mvp fail": GOOD_RECORD.replace("MVP 1 pass | MVP 2 pass", "MVP 1 fail | MVP 2 pass"),
            "open p0": GOOD_RECORD.replace("Open P0/P1: none", "Open P0/P1: #51 crash on retry"),
            "playthrough fail": GOOD_RECORD.replace("PLAYTHROUGH: PASS: PLAYTHROUGH 1a2b3c4: G1: survived, fail-retry, fail-bottom, quit-title, quit-pause passed", "PLAYTHROUGH: FAIL: PLAYTHROUGH 1a2b3c4: survived: fail"),
            "smoke fail": GOOD_RECORD.replace("smoke=PASS", "smoke=FAIL"),
            "gate checks fail": GOOD_RECORD.replace("ui_check ci: PASS", "ui_check ci: FAIL (3 problem(s))"),
            "not relaunched": GOOD_RECORD.replace("re-downloaded and launched: yes", "re-downloaded and launched: no"),
        }
        hard = {"mvp fail", "playthrough fail", "smoke fail", "gate checks fail"}
        for name, rec in cases.items():
            with self.subTest(case=name):
                got = check_card.gate_record_problems(rec, ROOT, RISK_BRIEF)
                self.assertTrue(any("proposes Pass" in p for p in got), got)
                ok = rec.replace("Proposed outcome: Pass", "Proposed outcome: Pass with named exceptions: #51 owner Ana by 18:00")
                got = check_card.gate_record_problems(ok, ROOT, RISK_BRIEF)
                # dry run B M8: a P0 gate FAIL stays a FAIL under named exceptions; open bugs may be named
                self.assertEqual(any("cannot be a named exception" in p for p in got), name in hard, got)
                if name not in hard:
                    self.assertEqual(got, [])

    def test_dry_run_records_that_passed_are_now_caught(self):
        """Dry run A H2 and B C2: each of these proposed Pass and got 0 problems before."""
        named = "Proposed outcome: Pass with named exceptions"
        cases = {
            "playtest fail": GOOD_RECORD.replace("P1 pass, P2 pass", "P1 fail, P2 pass"),
            "playtest insufficient": GOOD_RECORD.replace("P1 pass, P2 pass", "P1 pass, P2 insufficient"),
            "submission_check failing last line": GOOD_RECORD.replace(
                "PASS: Team_Game.zip config=Development platform=Win64", "submission_check: 2 problem(s)"),
            "lowercase fail": GOOD_RECORD.replace("ui_check ci: PASS (0 problem(s))", "ui_check ci: fail 3 problem(s)"),
            "mixed-case Fail": GOOD_RECORD.replace("quit-pause passed", "quit-pause Fail"),
            "mvp not working": GOOD_RECORD.replace("MVP 6 pass", "MVP 6 not working, retry missing"),
            "mvp free text": re.sub(r"^MVP items for this gate:.*$", "MVP items for this gate: MVP 1 pass #31",
                                    GOOD_RECORD, flags=re.M),
            "playthrough free text": GOOD_RECORD.replace(
                "PASS: PLAYTHROUGH 1a2b3c4: G1: survived, fail-retry, fail-bottom, quit-title, quit-pause passed",
                "looked fine in PIE"),
            "playthrough G1: ok": GOOD_RECORD.replace(
                "PASS: PLAYTHROUGH 1a2b3c4: G1: survived, fail-retry, fail-bottom, quit-title, quit-pause passed", "G1: ok"),
            "playthrough other build": GOOD_RECORD.replace("PLAYTHROUGH 1a2b3c4", "PLAYTHROUGH 9f9f9f9"),
            "gate checks free text": GOOD_RECORD.replace(
                "ui_check ci: PASS (0 problem(s)) | PASS: Team_Game.zip config=Development platform=Win64", "ran them, all good"),
            "repeat 4/5": GOOD_RECORD.replace("repeat 5/5", "repeat 4/5"),
            "lowercase fail beside real PASS lines": GOOD_RECORD.replace(
                "sha256=3f1c9a0e2b4d6f8a1c3e5a7b9d0f2a4c6e8b0d2f4a6c8e0b2d4f6a8c0e2b4d6f\n", "sha256=3f1c9a0e2b4d6f8a1c3e5a7b9d0f2a4c6e8b0d2f4a6c8e0b2d4f6a8c0e2b4d6f | audio_check --list: fail\n"),
            "upper-case FAIL beside real PASS lines": GOOD_RECORD.replace(
                "sha256=3f1c9a0e2b4d6f8a1c3e5a7b9d0f2a4c6e8b0d2f4a6c8e0b2d4f6a8c0e2b4d6f\n", "sha256=3f1c9a0e2b4d6f8a1c3e5a7b9d0f2a4c6e8b0d2f4a6c8e0b2d4f6a8c0e2b4d6f | audio_check --list: FAIL\n"),
            "mixed-case Fail beside real PASS lines": GOOD_RECORD.replace(
                "sha256=3f1c9a0e2b4d6f8a1c3e5a7b9d0f2a4c6e8b0d2f4a6c8e0b2d4f6a8c0e2b4d6f\n", "sha256=3f1c9a0e2b4d6f8a1c3e5a7b9d0f2a4c6e8b0d2f4a6c8e0b2d4f6a8c0e2b4d6f | audio_check --list: Fail\n"),
            "shipping build": GOOD_RECORD.replace("Team_Game.zip | Development", "Team_Game.zip | Shipping"),
        }
        for name, rec in cases.items():
            for outcome in ("Proposed outcome: Pass", named):
                with self.subTest(case=name, outcome=outcome):
                    got = check_card.gate_record_problems(rec.replace("Proposed outcome: Pass", outcome), ROOT, RISK_BRIEF)
                    self.assertTrue(any("cannot be a named exception" in p for p in got), got)

    def test_final6_gate_record_attacks(self):
        """Final-6 dry runs: B C2, A H7, A M1-M3, B H7, B M9. Each break proposed Pass and got 0 problems before."""
        failing = GOOD_RECORD.replace("MVP 6 pass", "MVP 6 fail").replace(
            "PLAYTHROUGH: PASS: PLAYTHROUGH 1a2b3c4: G1: survived, fail-retry, fail-bottom, quit-title, quit-pause passed",
            "PLAYTHROUGH: FAIL: PLAYTHROUGH 1a2b3c4: survived failed")
        for outcome in ("Passed", "Go", "✅ Pass", "pass", "PASS", "Pass.", "**Pass**", "Pass (mostly)", "Pass: ok"):
            with self.subTest(outcome=outcome):
                got = check_card.gate_record_problems(failing.replace("Proposed outcome: Pass", "Proposed outcome: " + outcome),
                                                      ROOT, RISK_BRIEF)
                self.assertTrue(any("not exactly one of" in p for p in got), got)
        miss = failing.replace("Proposed outcome: Pass", "Proposed outcome: Miss → cut MVP 6")
        self.assertEqual(check_card.gate_record_problems(miss, ROOT, RISK_BRIEF), [], "an honest Miss passes the record")
        sha2 = "a" * 64
        cases = {
            "upload not yet": GOOD_RECORD.replace("launched: yes", "launched: not yet"),
            "upload pending": GOOD_RECORD.replace("launched: yes", "launched: pending"),
            "upload n": GOOD_RECORD.replace("launched: yes", "launched: n"),
            "upload Yes!": GOOD_RECORD.replace("launched: yes", "launched: Yes!"),
            "late, no cut": GOOD_RECORD.replace("closed 2026-11-13T20:30-05:00 | late by 0.5 h", "closed 2026-11-13T23:30-05:00 | late by 3.5 h"),
            "zip of another build": GOOD_RECORD.replace("Win64 commit=1a2b3c4", "Win64 commit=9f9f9f9"),
            "zip with no commit": GOOD_RECORD.replace("Win64 commit=1a2b3c4 ", "Win64 "),
            "another zip": GOOD_RECORD.replace("PASS: Team_Game.zip", "PASS: Old_Game.zip"),
            "upload sha differs": GOOD_RECORD.replace("sha256=3f1c9a0e2b4d6f8a1c3e5a7b9d0f2a4c6e8b0d2f4a6c8e0b2d4f6a8c0e2b4d6f | re-downloaded", "sha256={sha2} | re-downloaded".format(sha2=sha2)),
            "upload sha short": GOOD_RECORD.replace("sha256=3f1c9a0e2b4d6f8a1c3e5a7b9d0f2a4c6e8b0d2f4a6c8e0b2d4f6a8c0e2b4d6f | re-downloaded", "sha256=abcd | re-downloaded"),
            "repeat of another build": GOOD_RECORD.replace("DAILY 1a2b3c4", "DAILY 9f9f9f9"),
            "repeat dirty": GOOD_RECORD.replace("DAILY 1a2b3c4", "DAILY 1a2b3c4+dirty"),
            "repeat 2/2": GOOD_RECORD.replace("repeat 5/5", "repeat 2/2"),
            "repeat typed": GOOD_RECORD.replace("DAILY 1a2b3c4 | win-1/Windows 11 | Development | clean-tree=PASS build=PASS test=PASS(40/0/40) validate=PASS(err 0, warn 0) package=PASS(warn 0) ", ""),
            "second playthrough line": GOOD_RECORD + "PLAYTHROUGH: FAIL: PLAYTHROUGH 1a2b3c4: G1: quit-pause failed\n",
            "mvp pass with a failure word": GOOD_RECORD.replace("MVP 6 pass", "MVP 6 pass (actually failed retest)"),
        }
        for name, rec in cases.items():
            with self.subTest(case=name):
                self.assertTrue(check_card.gate_record_problems(rec, ROOT, RISK_BRIEF), name)
        cut = GOOD_RECORD.replace("closed 2026-11-13T20:30-05:00 | late by 0.5 h", "closed 2026-11-13T23:30-05:00 | late by 3.5 h").replace(
            "Cut fired: no", "Cut fired: yes, MVP 12 polish")
        self.assertEqual(check_card.gate_record_problems(cut, ROOT, RISK_BRIEF), [], "late with the cut fired passes")
        named = GOOD_RECORD.replace("P1 pass, P2 pass", "P1 pass, P2 pass, P3 fail").replace(
            "Proposed outcome: Pass", "Proposed outcome: Pass with named exceptions")
        got = check_card.gate_record_problems(named, ROOT, RISK_BRIEF)
        self.assertTrue(any("has no 'owner <name> by HH:MM'" in p for p in got), got)
        ok = named.replace("P3 fail", "P3 fail owner Ana by 18:00")
        self.assertEqual(check_card.gate_record_problems(ok, ROOT, RISK_BRIEF), [])
        empty = GOOD_RECORD.replace("Proposed outcome: Pass", "Proposed outcome: Pass with named exceptions")
        self.assertTrue(any("names no exception" in p for p in check_card.gate_record_problems(empty, ROOT, RISK_BRIEF)))

    def test_open_p0_exception_needs_owner_and_hour(self):
        rec = GOOD_RECORD.replace("Open P0/P1: none", "Open P0/P1: #50 P0 crash on restart")
        ex = rec.replace("Proposed outcome: Pass", "Proposed outcome: Pass with named exceptions")
        self.assertTrue(any("#50 has no owner" in p for p in check_card.gate_record_problems(ex, ROOT, RISK_BRIEF)))
        ok = ex.replace("#50 P0 crash on restart", "#50 P0 crash on restart, owner Ana by 18:00")
        self.assertEqual(check_card.gate_record_problems(ok, ROOT, RISK_BRIEF), [])
        no_hour = ex.replace("#50 P0 crash on restart", "#50 P0 crash on restart, owner Ana")
        self.assertTrue(any("#50 has no owner" in p for p in check_card.gate_record_problems(no_hour, ROOT, RISK_BRIEF)))

    def test_g2_record_rechecks_every_mvp_item(self):
        g2 = for_gate(GOOD_RECORD, "G2")
        self.assertEqual(check_card.gate_record_problems(g2, ROOT, RISK_BRIEF), [])
        thin = g2.replace("MVP 1 pass | ", "")
        self.assertTrue(any("leave out 1" in p for p in check_card.gate_record_problems(thin, ROOT, RISK_BRIEF)))

    def test_gate_mvp_lists_match_producer_gates(self):
        with open(os.path.join(ROOT, "pipeline", "roles", "producer.md"), encoding="utf-8") as f:
            text = f.read()
        self.assertIn("MVP 1–6", text)
        self.assertIn("MVP 7–11", text)
        self.assertIn("MVP 12–15", text)
        self.assertEqual(check_card.GATE_MVP["G1"], [1, 2, 3, 4, 5, 6])          # D-new-sh10-g1: Start Game mode
        self.assertEqual(check_card.GATE_MVP["G2"], list(range(1, 12)))
        self.assertEqual(check_card.GATE_MVP["G3"], list(range(1, 16)))
        self.assertEqual(check_card.gate_mvp(text="## MVP\n1. a [G2]\n2. b\n## End\n"), {"G1": [], "G2": [1], "G3": [1], "G4": [1, 2]})

    def test_real_brief_risk_rows_are_counted(self):
        with open(os.path.join(ROOT, "docs", "jam-brief.md"), encoding="utf-8") as f:
            self.assertGreaterEqual(check_card.risk_count(f.read()), 1)

    def test_cli_reads_newest_gate_comment(self):
        brief = os.path.join(tempfile.mkdtemp(), "brief.md")
        with open(brief, "w", encoding="utf-8") as f:
            f.write(RISK_BRIEF)
        old = {"createdAt": "2026-11-13T20:30:00-05:00", "body": GOOD_RECORD}
        new_bad = {"createdAt": "2026-11-14T20:30:00-05:00", "body": GOOD_RECORD.replace("Risks:", "Riskz:")}
        clock_first = {"createdAt": "2026-11-15T20:30:00-05:00",
                       "body": "G1 due 2026-11-13T20:00-05:00, closed; on time\n" + GOOD_RECORD}   # final-9 A M2
        empty = os.path.join(os.path.dirname(brief), "records.txt")
        open(empty, "w").close()
        # final-9 B H4: the CLI always reads machine records; with none, only that problem is left for the good record
        for comments, risky in [([old], False), ([old, new_bad], True), ([clock_first], False)]:
            sys.stdin = io.StringIO(json.dumps({"comments": comments}))
            try:
                with redirect_stdout(io.StringIO()) as out:
                    self.assertEqual(check_card.main(["--gate-record", "--brief", brief, "--records", empty]), 1)
            finally:
                sys.stdin = sys.__stdin__
            got = [ln for ln in out.getvalue().splitlines() if ln.startswith("[plan]")]
            self.assertEqual(len(got), 1 + risky, got)
            self.assertIn("no machine record lines", got[-1 if not risky else 0] + got[-1])
            self.assertEqual(risky, any("Risks" in g for g in got), got)
        sys.stdin = io.StringIO(json.dumps({"comments": [{"createdAt": "x", "body": "hi"}]}))
        try:
            with redirect_stdout(io.StringIO()):
                self.assertEqual(check_card.main(["--gate-record", "--brief", brief]), 1)
        finally:
            sys.stdin = sys.__stdin__


class StretchBeforeMvp(unittest.TestCase):
    def stretch(self, num, extra=""):
        c = issue(num, f"Source/S{num}/**")
        c["body"] = re.sub(r"(### MVP item[^\n]*\n\n)\d+\n", r"\1Stretch: owl gust\n", c["body"], count=1) + extra
        return c

    def test_fixture_mvp_field_is_replaced(self):
        self.assertIn("Stretch: owl gust", self.stretch(9)["body"])

    def test_stretch_with_open_mvp_card_fails(self):
        got = check_card.stretch_problems([issue(1, "Source/A/**"), self.stretch(9)])
        self.assertEqual(len(got), 1, got)
        self.assertIn("#9 is a Stretch card", got[0])

    def test_stretch_alone_passes(self):
        self.assertEqual(check_card.stretch_problems([self.stretch(9)]), [])
        self.assertEqual(check_card.stretch_problems([issue(1, "Source/A/**"), issue(2, "Source/B/**")]), [])

    def test_no_override_while_mvp_is_open(self):
        # The old exception, broken on purpose: an approval link no longer lets a stretch card start early (Josh, 11 Nov)
        signed = self.stretch(9, "\nStretch approved: https://github.com/o/r/issues/1#issuecomment-5")
        got = check_card.stretch_problems([issue(1, "Source/A/**"), signed])
        self.assertEqual(len(got), 1, got)
        self.assertIn("no override", got[0])
        self.assertFalse(hasattr(check_card, "STRETCH_OK"))
        root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        for rel in ("pipeline/roles/producer.md", "pipeline/human-checkpoints.md", "docs/jam-brief.md",
                    "pipeline/checklists/card-ready.md"):
            with open(os.path.join(root, rel), encoding="utf-8") as fh:
                self.assertNotIn("Stretch approved", fh.read(), rel)
        with open(os.path.join(root, "docs", "jam-brief.md"), encoding="utf-8") as fh:
            self.assertIn("stretch cards start automatically once every MVP item passes", fh.read())

    def test_lanes_cli_fails_on_stretch(self):
        sys.stdin = io.StringIO(json.dumps([issue(1, "Source/A/**"), self.stretch(9)]))
        try:
            with redirect_stdout(io.StringIO()):
                self.assertEqual(check_card.main(["--lanes"]), 1)
        finally:
            sys.stdin = sys.__stdin__


SPIKE = """
Decision row:  D3
Decides it:    if the C++ rule compiles and its test passes in 60 min, pick C++; if not, pick Blueprint
Time box:      60 min
"""


class SpikeCards(unittest.TestCase):
    def body(self, block=SPIKE):
        # the spike lines go in the Unknowns field: before it they would land in the P0 card's "Budget and cut
        # tier" field and change its tier (the good card builds HAZ-19, APPROVED_P0 in GDD SH1.0)
        head = '### Unknowns (Decision needed / Why it matters / Proposed test / Choice; "none" if none)\n\n'
        return good_form().replace(head + "none\n", head + (block or "none\n"), 1)

    def spike_kinds(self, body, title="[UE-40] Spike D3: C++ or Blueprint"):
        return {k for k, _ in check_card.problems(body, ROOT, title)}

    def test_good_spike_passes(self):
        self.assertEqual(self.spike_kinds(self.body()), set())

    def test_each_break_is_caught(self):
        for name, block in [
            ("no decision row", SPIKE.replace("Decision row:  D3", "Decision row:  the C++ one")),
            ("no if/then", SPIKE.replace("if the C++ rule compiles and its test passes in 60 min, pick C++; if not, pick Blueprint",
                                         "we will see")),
            ("placeholder", SPIKE.replace("if the C++ rule", "<if X, pick A>")),
            ("box too long", SPIKE.replace("Time box:      60 min", "Time box:      2 h")),
            ("no box", SPIKE.replace("Time box:      60 min\n", "")),
            ("no fields at all", ""),
        ]:
            with self.subTest(case=name):
                self.assertIn("spike", self.spike_kinds(self.body(block)))

    def test_decision_row_line_marks_a_spike_without_the_title(self):
        block = SPIKE.replace("Time box:      60 min\n", "")
        self.assertIn("spike", self.spike_kinds(self.body(block), "[UE-40] C++ or Blueprint"))

    def test_normal_card_and_spike_filing_card_are_not_spikes(self):
        self.assertEqual(self.spike_kinds(good_form(), TITLE), set())
        self.assertEqual(check_card.spike_problems("x", "Spike cards for open decisions"), [])
        self.assertEqual(self.spike_kinds(self.body(SPIKE.replace("60 min", "45 min"))), set())


class ClockWorkflow(unittest.TestCase):
    TEMPLATE = os.path.join(ROOT, "pipeline", "templates", "clock-workflow.yml")
    LIVE = os.path.join(ROOT, ".github", "workflows", "clock.yml")

    def test_template_runs_the_three_checks_every_3_h_behind_a_switch(self):
        with open(self.TEMPLATE, encoding="utf-8") as f:
            text = f.read()
        self.assertIn('cron: "0 */3 * * *"', text)
        self.assertIn("vars.PIPELINE_CLOCK == 'on'", text)
        for cmd in ("check_card.py --clock", "check_card.py --status", "check_card.py --overrun"):
            self.assertIn(cmd, text)
        self.assertIn("--json body,comments", text)
        self.assertEqual(text.count("if: always()"), 2)  # a failing first check still runs the others

    def run_clock(self, d, now):
        p = os.path.join(d, "brief.md")
        with open(p, "w", encoding="utf-8") as f:
            f.write(GOOD_BRIEF)
        out = io.StringIO()
        with redirect_stdout(out):
            rc = check_card.main(["--clock", "--brief", p, "--root", d, "--now", now])
        return rc, out.getvalue()

    def test_clock_fails_after_cutoff_until_installed(self):
        # GOOD_BRIEF card 0.9 cutoff is 2026-11-12T18:00-05:00.
        with tempfile.TemporaryDirectory() as d:
            self.assertEqual(self.run_clock(d, "2026-11-12T17:59-05:00")[0], 0)
            rc, out = self.run_clock(d, "2026-11-12T18:00-05:00")
            self.assertEqual(rc, 1)
            self.assertIn("clock.yml is not installed", out)
            install_clock(d, "name: clock\n")  # an edited copy
            rc, out = self.run_clock(d, "2026-11-13T09:00-05:00")
            self.assertEqual(rc, 1)
            self.assertIn("differs from", out)
            install_clock(d)
            self.assertEqual(self.run_clock(d, "2026-11-13T09:00-05:00")[0], 0)

    def test_clock_install_is_not_checked_while_the_clock_is_tbd(self):
        with open(os.path.join(ROOT, "docs", "jam-brief.md"), encoding="utf-8") as f:
            text = f.read()
        now = dt.datetime.fromisoformat("2030-01-01T00:00+00:00")
        if check_card.parse_time((check_card.clock(text) or {}).get("Card 0.9 cutoff") or "") is None:
            self.assertEqual(check_card.clock_install_problems(tempfile.gettempdir(), text, now), [])

    def test_day0_card_installs_the_clock(self):
        with open(os.path.join(ROOT, "pipeline", "day0-cards.md"), encoding="utf-8") as f:
            row = [r for r in f.read().splitlines() if r.startswith("| 0.16 ")]
        self.assertEqual(len(row), 1)
        for need in (".github/workflows/clock.yml", "PIPELINE_CLOCK", "TRACKER_ISSUE", "gh run list", "git_gate.py apply UE-0.16 --auto", "repo_settings"):
            self.assertIn(need, row[0])

    def test_live_workflow_matches_template_when_present(self):
        if not os.path.exists(self.LIVE):
            self.skipTest(".github/workflows/clock.yml not copied from the template yet (D-new-schedule)")
        with open(self.TEMPLATE, encoding="utf-8") as a, open(self.LIVE, encoding="utf-8") as b:
            self.assertEqual(a.read(), b.read())


if __name__ == "__main__":
    unittest.main()
