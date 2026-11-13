"""tools/kickoff.py run with nobody watching: a failed session is retried in the same run (AGENTS.md section 6: the
same failure twice -> blocked) and then raises a NEEDS HUMAN ask with the reason; it never ends the run as idle.
A journal or run-record error is reported once and the run goes on: logging never blocks or stops the run.
kickoff merges an approved card PR itself, only when CI is green, the reviewer approved after the last push and
check_pr passes; anything else blocks the merge and, after the retry, asks a human with the reason.
Each case is a test that failed on the code before the fix."""
import os
import shutil
import subprocess
import sys
import threading
import time
import unittest
import unittest.mock

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.join(HERE, "fixtures", "kickoff"))
sys.path.insert(0, os.path.join(ROOT, "tools"))
import journal  # noqa: E402
import kickoff  # noqa: E402
import kickoff_sandbox as ks  # noqa: E402
import test_honest_jam as thj  # noqa: E402  the filled People table

CARD = "UE-0.25"   # a pre-jam card with a plain file lane: one builder session, one review


def starts(sb, card, review=False):
    return [s for s in sb.sessions() if s["event"] == "start" and s["card"] == card and s.get("review") == review]


@unittest.skipIf(shutil.which("git") is None, "needs git")
class FailedBuilderIsRetriedNotIdle(unittest.TestCase):
    def setUp(self):
        self.sb = ks.KickoffSandbox(thj.PEOPLE)
        self.addCleanup(self.sb.close)

    def run_one(self, **env):
        return self.sb.kickoff("--agent", "codex", STUB_DAY0_ONLY="0.25", **env)

    def card(self):
        return next(i for i in self.sb.gh()["issues"] if i["title"].startswith(f"[{CARD}]"))

    def test_a_crashed_builder_is_rerun_in_the_same_run(self):
        rc, out = self.run_one(STUB_FAIL_ONCE=CARD)
        self.assertEqual(rc, 3, out)   # pre-jam mode ends 3 when nothing failed
        self.assertEqual(len(starts(self.sb, CARD)), 2, "the crashed session ran again in this run\n" + out)
        self.assertIn(f"RETRY {CARD}", out)
        self.assertTrue(any(p["headRefName"].startswith("ue-0.25-") for p in self.sb.gh()["prs"]),
                        "the rerun opened the PR in the same run\n" + out)

    def test_a_builder_that_always_crashes_asks_a_human_with_the_reason(self):
        rc, out = self.run_one(STUB_FAIL_ALWAYS=CARD)
        self.assertEqual(len(starts(self.sb, CARD)), kickoff.MAX_FAILS, out)
        it = self.card()
        self.assertIn("needs-human", it["labels"], out)
        self.assertIn("blocked", it["labels"], out)
        ask = [c["body"] for c in it["comments"] if "NEEDS HUMAN:" in c["body"]]
        self.assertEqual(len(ask), 1, it["comments"])
        self.assertIn("exited with code 1", ask[0], "the ask names the failure")
        self.assertIn("crashed on purpose", ask[0], "the ask quotes the session's last line")
        self.assertIn("1 new needs-human ask(s)", out.strip().splitlines()[-1])

    def test_a_session_that_crashes_after_committing_is_not_pushed_as_done(self):
        rc, out = self.run_one(STUB_EXIT_AFTER_COMMIT_ONCE=CARD)
        self.assertEqual(rc, 3, out)
        self.assertEqual(len(starts(self.sb, CARD)), 2, "a non-zero exit is a failed session, run again\n" + out)
        self.assertIn("exited with code 3", out)
        prs = [p for p in self.sb.gh()["prs"] if p["headRefName"].startswith("ue-0.25-")]
        self.assertEqual(len(prs), 1, out)

    def test_session_reason(self):
        import tempfile
        box = tempfile.mkdtemp()
        self.addCleanup(shutil.rmtree, box, True)
        with open(os.path.join(box, "session.log"), "w", encoding="utf-8") as fh:
            fh.write("working\nError: rate limited\n\n")
        self.assertIn("timed out", kickoff.Kickoff.session_reason(124, box))
        self.assertIn("could not start", kickoff.Kickoff.session_reason(127, box))
        self.assertEqual(kickoff.Kickoff.session_reason(2, box), "the session exited with code 2: Error: rate limited")


class BrokenJournal(unittest.TestCase):
    def kick(self):
        k = kickoff.Kickoff.__new__(kickoff.Kickoff)
        k.dry, k.run_id, k.jdb = False, 7, "/nonexistent"
        return k

    def setUp(self):
        real = journal.connect
        self.addCleanup(setattr, journal, "connect", real)

        def broken(path=None):
            raise journal.sqlite3.OperationalError("disk I/O error")
        journal.connect = broken
        self.said = []
        real_say = kickoff.say
        self.addCleanup(setattr, kickoff, "say", real_say)
        kickoff.say = lambda m: (real_say(m), self.said.append(m))

    def in_thread(self, fn):
        t = threading.Thread(target=fn, daemon=True)
        t.start()
        t.join(10)
        self.assertFalse(t.is_alive(), "logging hung the run")

    def test_run_record_error_never_hangs(self):
        k = self.kick()
        self.in_thread(lambda: k.runlog(journal.add_run_outcome, 7, "end", outcome="idle"))
        self.assertEqual(len(self.said), 1, self.said)
        self.assertIn("disk I/O error", self.said[0])

    def test_journal_error_never_stops_the_run_and_is_reported_once(self):
        k = self.kick()
        res = []
        self.in_thread(lambda: res.extend([k.j("UE-1", "step", note="a"), k.j("UE-1", "step", note="b"),
                                           k.runlog(journal.add_run_outcome, 7, "session")]))
        self.assertEqual(res, [None, None, None])
        self.assertEqual(len(self.said), 1, "reported once, not per write: " + repr(self.said))
        self.assertEqual(k.journal_lost, 3)

    def test_fail_count_survives_a_broken_journal(self):
        k = self.kick()
        k.fail_count = {("UE-1", "builder"): 1}
        self.assertEqual(k.fails("UE-1"), 1)


@unittest.skipIf(shutil.which("git") is None, "needs git")
class UnwritableJournalEndToEnd(unittest.TestCase):
    def test_kickoff_runs_on_without_its_journal(self):
        sb = ks.KickoffSandbox(thj.PEOPLE)
        self.addCleanup(sb.close)
        bad = os.path.join(sb.base, "journal-is-a-dir")
        os.makedirs(bad)   # sqlite cannot open a directory: every journal write fails
        rc, out = sb.kickoff("--agent", "codex", STUB_DAY0_ONLY="0.25", JOURNAL_DB=bad)
        self.assertEqual(rc, 3, out)
        self.assertNotIn("stopped by an unexpected error", out)
        self.assertEqual(out.count("kickoff: journal not written"), 1, out)
        self.assertTrue(starts(sb, CARD), "the card still ran\n" + out)
        self.assertIn("KICKOFF idle", out)


@unittest.skipIf(shutil.which("git") is None, "needs git")
class AutoMerge(unittest.TestCase):
    def setUp(self):
        self.sb = ks.KickoffSandbox(thj.PEOPLE)
        self.addCleanup(self.sb.close)

    def run_one(self, **env):
        rc, out = self.sb.kickoff("--agent", "codex", STUB_DAY0_ONLY="0.25", **env)
        s = self.sb.gh()
        pr = next(p for p in s["prs"] if p["headRefName"].startswith("ue-0.25-"))
        card = next(i for i in s["issues"] if i["title"].startswith(f"[{CARD}]"))
        self.sb.git("fetch", "-q", "origin")
        return rc, out, pr, card, self.sb.git("log", "--format=%s", "origin/main")

    def asks(self, card):
        return [c["body"] for c in card["comments"] if "NEEDS HUMAN:" in c["body"]]

    def test_green_ci_and_approval_merge_with_no_human(self):
        rc, out, pr, card, log = self.run_one()
        self.assertEqual(pr["state"], "MERGED", out)
        self.assertEqual(card["state"], "CLOSED", out)
        self.assertEqual(self.asks(card), [], "no merge ask")
        self.assertRegex(log.splitlines()[0], rf"^{CARD}: .*\(#{pr['number']}\)$", "one squash commit for the card")
        self.assertIn(f"MERGED {CARD} PR #{pr['number']}", out)

    def test_a_red_check_blocks_the_merge_and_asks_with_the_check(self):
        rc, out, pr, card, log = self.run_one(FAKE_GH_CHECKS="fail")
        self.assertEqual(pr["state"], "OPEN", out)
        self.assertNotIn(f"(#{pr['number']})", log, "nothing reached main")
        self.assertEqual(out.count(f"START merge {CARD}"), kickoff.MAX_FAILS, out)
        ask = self.asks(card)
        self.assertEqual(len(ask), 1, out)
        self.assertIn(f"merge PR #{pr['number']}", ask[0])
        self.assertIn("Pipeline checks / linux (fail)", ask[0])

    def test_no_ci_at_all_blocks_the_merge(self):
        rc, out, pr, card, log = self.run_one(FAKE_GH_CHECKS="none")
        self.assertEqual(pr["state"], "OPEN", out)
        self.assertIn("no CI check reported", self.asks(card)[0])

    def test_ci_still_running_waits_then_asks_after_the_cap(self):
        rc, out, pr, card, log = self.run_one(FAKE_GH_CHECKS="pending", KICKOFF_CI_POLL="1", KICKOFF_CI_WAIT="2")
        self.assertEqual(pr["state"], "OPEN", out)
        self.assertIn("WAITING on CI", out)
        self.assertIn("CI still pending after", self.asks(card)[0])

    def test_gh_refusing_the_merge_asks_with_the_gh_error(self):
        rc, out, pr, card, log = self.run_one(FAKE_GH_MERGE_FAIL="GraphQL: Base branch policy prohibits the merge")
        self.assertEqual(pr["state"], "OPEN", out)
        self.assertIn("Base branch policy prohibits the merge", self.asks(card)[0])

    def test_no_approval_after_the_last_push_blocks_the_merge(self):
        merged, failed = [], []

        class GH:
            def __init__(self, comments):
                self.comments = comments

            def pr_view(self, n, fields):
                return {"state": "OPEN", "headRefName": "ue-1-x", "headRefOid": "a" * 40, "body": "", "title": "t",
                        "comments": self.comments}

            def pr_merge(self, n, sha):
                merged.append(n)

        k = kickoff.Kickoff.__new__(kickoff.Kickoff)
        k.session_failed = lambda c, cid, what, why, box=None, pr=None: failed.append(why)
        k.worktree = lambda b: self.fail("no gate past the verdict may run")
        card = type("C", (), {"key": "1", "number": 3, "title": "t", "body": "", "human": None})()
        for comments in ([], [{"body": "ROLE: Dev Lead | s\nVERDICT: changes\n- x"}],
                         [{"body": "ROLE: Dev Lead | s\nVERDICT: approve"}, {"body": "ROLE: GD | s\nPUSHED: fixes, abc"}]):
            k.gh = GH(comments)
            k.merger(card, {"number": 9})
        self.assertEqual(merged, [], "never merged without an approve after the last push")
        self.assertEqual(len(failed), 3)
        self.assertTrue(all("VERDICT: approve" in w for w in failed), failed)


@unittest.skipIf(shutil.which("git") is None, "needs git")
class MaxCards(unittest.TestCase):
    """--max-cards N (KICKOFF_MAX_CARDS): no new card starts once N cards merged (or closed) or got blocked in this
    run; cards in flight finish; the run ends with the KICKOFF bounded line, exit 0; a rerun continues."""
    CARDS = "0.1,0.2,0.25"   # no After between them, lanes apart: GitHub only, docs/jam-rules.md, Samples/Workbench

    def setUp(self):
        self.sb = ks.KickoffSandbox(thj.PEOPLE)
        self.addCleanup(self.sb.close)

    def built(self):
        return {s["card"] for s in self.sb.sessions() if s["event"] == "start" and not s.get("review")
                and s["card"].startswith("UE-")}

    def closed(self):
        return {i["title"].split("]")[0][1:] for i in self.sb.gh()["issues"]
                if "task" in i["labels"] and i["state"] == "CLOSED"}

    def test_stops_at_n_and_a_rerun_continues(self):
        rc, out = self.sb.kickoff("--agent", "codex", "--practice", "--parallel", "1", "--max-cards", "1",
                                  STUB_DAY0_ONLY=self.CARDS)
        self.assertEqual(rc, 0, out)
        last = out.strip().splitlines()[-1]
        self.assertTrue(last.startswith("KICKOFF bounded: 1 card(s) done this run (merged 1, blocked 0); run again to "
                                        "continue"), out)
        self.assertEqual(self.built(), {"UE-0.1"}, "no second card started\n" + out)
        self.assertEqual(self.closed(), {"UE-0.1"})
        rc, out = self.sb.kickoff("--agent", "codex", "--parallel", "1", STUB_DAY0_ONLY=self.CARDS,
                                  KICKOFF_MAX_CARDS="1")
        self.assertEqual(rc, 0, out)
        self.assertIn("KICKOFF bounded: 1 card(s) done this run", out)
        self.assertEqual(self.built(), {"UE-0.1", "UE-0.2"}, "the rerun picked up the next card\n" + out)
        self.assertEqual(self.closed(), {"UE-0.1", "UE-0.2"})
        rc, out = self.sb.kickoff("--agent", "codex", STUB_DAY0_ONLY=self.CARDS)   # no bound: the rest runs
        self.assertEqual(rc, 0, out)
        self.assertNotIn("KICKOFF bounded", out)
        self.assertEqual(self.closed(), {"UE-0.1", "UE-0.2", "UE-0.25"}, out)

    def test_cards_in_flight_finish(self):
        rc, out = self.sb.kickoff("--agent", "codex", "--practice", "--parallel", "2", "--max-cards", "1",
                                  STUB_DAY0_ONLY=self.CARDS, STUB_SLEEP="0.3")
        self.assertEqual(rc, 0, out)
        self.assertEqual(self.built(), {"UE-0.1", "UE-0.2"}, out)
        self.assertEqual(self.closed(), {"UE-0.1", "UE-0.2"}, "the card in flight still reviewed and merged\n" + out)
        self.assertIn("KICKOFF bounded: 2 card(s) done this run (merged 2, blocked 0)", out.strip().splitlines()[-1])

    def test_a_blocked_card_counts(self):
        rc, out = self.sb.kickoff("--agent", "codex", "--practice", "--parallel", "1", "--max-cards", "1",
                                  STUB_DAY0_ONLY=self.CARDS, STUB_FAIL_ALWAYS="UE-0.1")
        self.assertEqual(rc, 0, out)
        self.assertIn("KICKOFF bounded: 1 card(s) done this run (merged 0, blocked 1)", out)
        self.assertEqual(self.built(), {"UE-0.1"}, out)


@unittest.skipIf(shutil.which("git") is None, "needs git")
class JamStartTag(unittest.TestCase):
    """Card 0.3 starts: kickoff tags jam-start on main itself (no person), once, on or after the Official Rules
    start, never in a practice repo, and never moves a tag that exists."""

    def setUp(self):
        import subprocess
        import tempfile
        self.base = tempfile.mkdtemp(prefix="jamstart-")
        self.addCleanup(shutil.rmtree, self.base, True)
        self.origin, self.repo = os.path.join(self.base, "o.git"), os.path.join(self.base, "r")
        run = lambda *a, cwd=None: subprocess.run(["git", *a], cwd=cwd, check=True, capture_output=True, text=True)
        self.run = run
        run("init", "-q", "--bare", "-b", "main", self.origin)
        run("init", "-q", "-b", "main", self.repo)
        for k, v in (("user.email", "t@t"), ("user.name", "t"), ("core.hooksPath", "/dev/null")):
            run("config", k, v, cwd=self.repo)
        run("commit", "-q", "--allow-empty", "-m", "pre-jam", cwd=self.repo)
        run("remote", "add", "origin", self.origin, cwd=self.repo)
        run("push", "-q", "origin", "main", cwd=self.repo)
        self.k = kickoff.Kickoff.__new__(kickoff.Kickoff)
        self.k.practice, self.k.dry = False, True   # dry: no journal writes from the unit
        old = os.environ.get("KICKOFF_NOW")
        self.addCleanup(lambda: os.environ.__setitem__("KICKOFF_NOW", old) if old else os.environ.pop("KICKOFF_NOW", None))

    def tag_on_origin(self):
        return self.run("ls-remote", "--tags", self.origin, "refs/tags/jam-start").stdout.split()[:1]

    def test_tags_once_after_the_start(self):
        os.environ["KICKOFF_NOW"] = "2026-11-12T06:00Z"
        sha = self.k.ensure_jam_start(self.repo)
        main = self.run("rev-parse", "main", cwd=self.repo).stdout.strip()
        self.assertEqual(sha, main)
        self.assertEqual(self.tag_on_origin(), [main])
        self.run("commit", "-q", "--allow-empty", "-m", "jam work", cwd=self.repo)
        self.run("push", "-q", "origin", "main", cwd=self.repo)
        self.assertIsNone(self.k.ensure_jam_start(self.repo), "an existing tag is never moved")
        self.assertEqual(self.tag_on_origin(), [main])

    def test_never_before_the_start_or_in_a_practice_repo(self):
        os.environ["KICKOFF_NOW"] = "2026-11-11T12:00Z"
        self.assertIsNone(self.k.ensure_jam_start(self.repo))
        os.environ["KICKOFF_NOW"] = "2026-11-12T06:00Z"
        self.k.practice = True
        self.assertIsNone(self.k.ensure_jam_start(self.repo))
        self.assertEqual(self.tag_on_origin(), [])


def filed(cid, number=7):
    import test_day0_cards as t0
    row = next(r for r in t0.day0_rows() if r[0] == cid)
    body, title = t0.file_card(list(row[:5]) + ["–"] + list(row[6:]))
    card = kickoff.Card({"number": number, "title": title, "body": body})
    card.human = "Rick"   # the Producer writes the seat's person from the People table when filing
    return card


def plan_of(cards, env, until=None):
    from unittest import mock
    k = kickoff.Kickoff.__new__(kickoff.Kickoff)
    k.running, k.prejam, k.daily_q, k.until = {}, None, [], until
    k.cards = lambda: cards
    k.gh = mock.Mock(prs=lambda: [])
    with mock.patch.dict(os.environ, env):
        jobs, waiting, _ = k.plan()
    return [(j[0], j[1].key) for j in jobs], waiting


class WindowsCardsWaitForThePackagingMachine(unittest.TestCase):
    """A card that says `Runs on: the Windows packaging machine` (the old HUMAN physical session start) is built only by
    a kickoff there; elsewhere it waits with a reason. Broken on purpose: the same card on the packaging machine runs.
    Its twin `Runs on: the Mac build machine` (the Mac lines of the G1 cards) waits on a Windows kickoff."""

    def plan(self, packaging):
        card = filed("0.6w")
        self.assertTrue(card.windows)
        jobs, waiting = plan_of([card], {"KICKOFF_PACKAGING_MACHINE": "1" if packaging else "0",
                                         "KICKOFF_MAC_MACHINE": "0", "AGENT_OPS_PLATFORM": "darwin"})
        return [j[0] for j in jobs], waiting

    def test_waits_off_the_packaging_machine_and_runs_on_it(self):
        jobs, waiting = self.plan(False)
        self.assertEqual(jobs, [])
        self.assertTrue(any("runs on the Windows packaging machine" in w for w in waiting), waiting)
        jobs, waiting = self.plan(True)
        self.assertEqual(jobs, ["build"], waiting)

    def test_mac_cards_run_on_the_mac_and_wait_on_windows(self):
        card = filed("0.6e")
        self.assertTrue(card.mac)
        self.assertFalse(card.windows)
        jobs, waiting = plan_of([card], {"KICKOFF_PACKAGING_MACHINE": "0", "KICKOFF_MAC_MACHINE": "0",
                                         "AGENT_OPS_PLATFORM": "darwin"})
        self.assertEqual(jobs, [("build", "0.6e")], waiting)
        jobs, waiting = plan_of([card], {"KICKOFF_PACKAGING_MACHINE": "1", "KICKOFF_MAC_MACHINE": "0",
                                         "AGENT_OPS_PLATFORM": "win32"})
        self.assertEqual(jobs, [])
        self.assertTrue(any("runs on the Mac build machine" in w for w in waiting), waiting)
        jobs, waiting = plan_of([card], {"KICKOFF_PACKAGING_MACHINE": "1", "KICKOFF_MAC_MACHINE": "1",
                                         "AGENT_OPS_PLATFORM": "win32"})
        self.assertEqual(jobs, [("build", "0.6e")], "the sandbox seam plays the Mac on a Windows host")


@unittest.skipIf(shutil.which("git") is None, "needs git")
class TwoMachinesHandOff(unittest.TestCase):
    """The jam has two kickoff machines: the Mac build machine and the Windows packaging machine. Each builds its own
    `Runs on:` cards and every card with no `Runs on:` line; the other machine's cards wait, named on the idle line,
    and only the cards that list them in After wait with them. Same result on every OS: AGENT_OPS_PLATFORM names the
    machine each run plays (win32 on a Windows host is the host itself) and KICKOFF_MAC_MACHINE=0 turns off the
    sandbox's Mac seam. Cards: 0.0 and 0.2 (any machine), 0.3 (Mac, After 0.0), 0.3w (Windows, After 0.3)."""

    ONLY = "0.0,0.2,0.3,0.3w"
    WINDOWS = dict(AGENT_OPS_PLATFORM="win32", KICKOFF_MAC_MACHINE="0", KICKOFF_PACKAGING_MACHINE="1")
    MAC = dict(AGENT_OPS_PLATFORM="darwin", KICKOFF_MAC_MACHINE="0", KICKOFF_PACKAGING_MACHINE="0")

    def setUp(self):
        self.sb = ks.KickoffSandbox(thj.PEOPLE)
        self.addCleanup(self.sb.close)

    def run_on(self, machine, *args):
        """One kickoff on that machine, then the test plays the humans until nothing is asked."""
        outs = []
        for _ in range(6):
            rc, out = self.sb.kickoff("--agent", "codex", "--parallel", "2", *args, STUB_DAY0_ONLY=self.ONLY, **machine)
            self.assertEqual(rc, 0, out)
            self.assertNotIn("ERROR", out, out[-3000:])
            outs.append(out)
            args = ()
            answered, _ = self.sb.human_round()
            if not answered:
                break
        return "".join(outs)

    def built(self):
        return {s["card"] for s in self.sb.sessions() if s["event"] == "start" and not s.get("review")
                and s["card"].startswith("UE-")}

    def card(self, cid):
        return next((i for i in self.sb.gh()["issues"] if i["title"].startswith(f"[{cid}]")), None)

    def test_each_machine_builds_its_cards_and_the_rest_and_hands_off(self):
        out = self.run_on(self.WINDOWS, "--practice")
        self.assertEqual(self.built(), {"UE-0.0", "UE-0.2"}, out)
        self.assertEqual(self.card("UE-0.0")["state"], "CLOSED", out)
        self.assertEqual(self.card("UE-0.2")["state"], "CLOSED", out)
        mac = self.card("UE-0.3")
        self.assertEqual(mac["state"], "OPEN", "the Windows machine never builds the Mac skeleton")
        self.assertRegex(out, rf"(?m)^WAITING on the Mac build machine: #{mac['number']} UE-0\.3; run tools/kickoff.sh")
        self.assertIsNone(self.card("UE-0.3w"), "0.3w waits on 0.3 (After), so it is not filed yet")

        out = self.run_on(self.MAC)
        self.assertEqual(self.built(), {"UE-0.0", "UE-0.2", "UE-0.3"}, out)
        self.assertEqual(self.card("UE-0.3")["state"], "CLOSED", out)
        win = self.card("UE-0.3w")
        self.assertEqual(win["state"], "OPEN", "the Mac never builds the Windows skeleton")
        self.assertRegex(out, rf"(?m)^WAITING on the Windows packaging machine: #{win['number']} UE-0\.3w; ")

        out = self.run_on(self.WINDOWS)
        self.assertEqual(self.built(), {"UE-0.0", "UE-0.2", "UE-0.3", "UE-0.3w"}, out)
        self.assertEqual(self.card("UE-0.3w")["state"], "CLOSED", out)
        self.assertNotIn("WAITING on the", out, "nothing is left for the other machine")


class UntilG1BuildsOnlyItsPath(unittest.TestCase):
    """--until G1: only the G1 path is built (its Day-0 cards, the [G1] MVP cards and what they list in After); the
    Windows cards and every card off the path wait with a reason. Broken on purpose: without --until they run."""

    def cards(self):
        mvp = filed("0.5", 40)   # a card standing in for an MVP 3 card: MVP item 3, After UE-0.12 (off the Day-0 line)
        mvp.cid, mvp.key, mvp.mvp, mvp.after, mvp.lanes = "UE-40", "40", 3, ["0.12"], ["Source/X/**"]
        cards = [filed(k, n) for n, k in enumerate(("0.0", "0.3", "0.3w", "0.12", "0.20"), 1)] + [mvp]
        for c in cards:
            if c.key != "40":
                c.after = []   # every After merged, so readiness is only the path
        return cards

    def test_only_the_g1_path_builds(self):
        env = {"KICKOFF_PACKAGING_MACHINE": "1", "AGENT_OPS_PLATFORM": "darwin"}
        cards = self.cards()
        k = kickoff.Kickoff.__new__(kickoff.Kickoff)
        k.until = "G1"
        targets, missing = k.gate_targets(cards)
        self.assertIn("0.12", targets, "an MVP card's After joins the path")
        self.assertNotIn("0.20", targets)
        self.assertNotIn("0.3w", targets)
        self.assertEqual(missing, [1, 2, 4, 5, 6], "MVP items with no card yet keep G1 from being reached")
        for c in cards:
            if c.key == "0.12":
                c.after = ["40"]   # waits for the MVP card, so this plan shows the path filter, not readiness
        jobs, waiting = plan_of(cards, env, until="G1")
        built = {k for kind, k in jobs if kind == "build"}
        self.assertTrue({"0.0", "0.3"} <= built, (jobs, waiting))
        self.assertFalse(built & {"0.20", "0.3w"}, jobs)
        self.assertTrue(any("UE-0.20: not on the G1 path (--until G1)" in w for w in waiting), waiting)
        self.assertTrue(any("UE-0.3w: not on the G1 path (--until G1)" in w for w in waiting), waiting)
        jobs, _ = plan_of([c for c in cards if c.key != "0.3"], env)   # 0.3's lane (Config/**) would hold 0.20's
        self.assertIn(("build", "0.20"), jobs, "broken on purpose: without --until the off-path card runs")


@unittest.skipIf(shutil.which("git") is None, "needs git")
@unittest.skipIf(os.name == "nt", "G1 ends on the Mac package (kickoff --until G1 is the Mac path); the Windows cards wait for the packaging machine")
class UntilG1EndsOnTheMacPackage(unittest.TestCase):
    """End to end on the sandbox, with G1 narrowed to two cards and no MVP item due at G1: kickoff --until G1 builds
    and merges only those, then runs the G1 Mac package itself (KICKOFF_PACKAGE_CMD: a stub daily.sh) and stops on
    its DAILY line. A failing package goes to the Producer and, the same way 3 times, fails the run."""

    def setUp(self):
        import re
        self.sb = ks.KickoffSandbox(thj.PEOPLE)
        self.addCleanup(self.sb.close)
        p = os.path.join(self.sb.repo, "pipeline", "day0-cards.md")
        with open(p, encoding="utf-8") as fh:
            t = re.sub(r"^\*\*G1 cards:\*\*.*$", "**G1 cards:** 0.1, 0.25", fh.read(), flags=re.M)
        with open(p, "w", encoding="utf-8") as fh:
            fh.write(t)
        b = os.path.join(self.sb.repo, "docs", "jam-brief.md")
        with open(b, encoding="utf-8") as fh:
            t = fh.read().replace("[G1]\n", "[G2]\n")
        with open(b, "w", encoding="utf-8") as fh:
            fh.write(t)
        self.sb.git("commit", "-qam", "G1 = 0.1 and 0.25 for this test")
        self.sb.git("push", "-q", "origin", "main")
        self.pkg = f"{sys.executable} {os.path.join(HERE, 'fixtures', 'kickoff', 'stub_daily.py')}"

    def built(self):
        return {s["card"] for s in self.sb.sessions() if s["event"] == "start" and not s.get("review")
                and s["card"].startswith("UE-")}

    def test_reaches_g1_on_the_mac_package(self):
        rc, out = self.sb.kickoff("--agent", "codex", "--practice", "--parallel", "1", "--until", "G1",
                                  STUB_DAY0_ONLY="0.1,0.2,0.25", KICKOFF_PACKAGE_CMD=self.pkg,
                                  AGENT_OPS_PLATFORM="darwin")
        self.assertEqual(rc, 0, out)
        self.assertEqual(self.built(), {"UE-0.1", "UE-0.25"}, out)
        self.assertIn("G1 PACKAGE:", out)
        last = out.strip().splitlines()[-1]
        self.assertTrue(last.startswith("KICKOFF G1 reached: DAILY "), out)
        self.assertIn("package=PASS smoke=PASS", last)
        with open(os.path.join(self.sb.repo, "Saved", "Logs", "pipeline", "daily-records.txt"), encoding="utf-8") as fh:
            self.assertIn("smoke=PASS", fh.read(), "the record is in this checkout too")

    def test_broken_on_purpose_a_failing_package_never_reaches_g1(self):
        rc, out = self.sb.kickoff("--agent", "codex", "--practice", "--parallel", "1", "--until", "G1",
                                  STUB_DAY0_ONLY="0.1,0.2,0.25", KICKOFF_PACKAGE_CMD=self.pkg, STUB_DAILY_FAIL="1",
                                  AGENT_OPS_PLATFORM="darwin")
        self.assertEqual(rc, 1, out)
        self.assertNotIn("G1 reached", out)
        self.assertEqual(out.count("G1 PACKAGE FAILED"), 3, out)
        self.assertIn("the G1 Mac package failed 3 times in a row on smoke", out)

    def test_dry_run_prints_the_g1_order(self):
        rc, out = self.sb.kickoff("--agent", "codex", "--dry-run", "--until", "G1", AGENT_OPS_PLATFORM="darwin",
                                  KICKOFF_NOW="2026-11-12T12:00Z")
        self.assertEqual(rc, 0, out)
        self.assertIn("UNTIL G1 on the Mac: 2 Day-0 card(s)", out)
        self.assertIn("UNTIL G1: 0 step(s) need a person", out)


class RuleKSwitchesOnFromTheMeasurement(unittest.TestCase):
    """Card 0.3 needs no gate patch for module_check rule K: it runs by default once card 0.4a removes the [VERIFY]
    on `final` from pipeline/unreal/cpp-rules.md (the 5.8.4 compile log is the proof), never before."""

    def test_k_proven_reads_the_verify_tag(self):
        import tempfile
        import module_check
        root = tempfile.mkdtemp()
        self.addCleanup(shutil.rmtree, root, True)
        with open(os.path.join(ROOT, "pipeline", "unreal", "cpp-rules.md"), encoding="utf-8") as fh:
            text = fh.read()
        self.assertFalse(module_check.k_proven(ROOT), "today: [VERIFY], rule K off by default")
        self.assertFalse(module_check.k_proven(root), "no file is no proof")
        os.makedirs(os.path.join(root, "pipeline", "unreal"))
        proven = module_check.FINAL_VERIFY.sub("`final` on a C++ class nothing derives from (compile log: ...", text)
        with open(os.path.join(root, "pipeline", "unreal", "cpp-rules.md"), "w", encoding="utf-8") as fh:
            fh.write(proven)
        self.assertTrue(module_check.k_proven(root))


@unittest.skipIf(shutil.which("git") is None, "needs git")
class GitHubOutageNeverCrashesTheRun(unittest.TestCase):
    """A live unattended run died on one `gh issue list` HTTP 401 (Bad credentials) while the keyring login worked
    seconds before and after. Every gh call retries a transient failure; one that still fails skips the cycle."""
    NO_WAIT = dict(KICKOFF_GH_RETRY_DELAYS="0,0,0,0")

    def setUp(self):
        self.sb = ks.KickoffSandbox(thj.PEOPLE)
        self.addCleanup(self.sb.close)

    def journal_notes(self):
        con = journal.connect(os.path.join(self.sb.base, "journal.db"))
        try:
            return [e["note"] or "" for e in journal.events(con, kickoff.KICK)]
        finally:
            con.close()

    def test_two_401s_then_success_the_run_goes_on(self):
        rc, out = self.sb.kickoff("--agent", "codex", STUB_DAY0_ONLY="0.25", FAKE_GH_FAIL="2", **self.NO_WAIT)
        self.assertNotIn("unexpected error", out)
        self.assertEqual(rc, 3, out)   # pre-jam mode ends 3 when nothing failed
        retries = [ln for ln in out.splitlines() if ln.startswith("GH RETRY gh issue list --state")]
        self.assertEqual(len(retries), 2, out)
        self.assertIn("HTTP 401: Bad credentials", retries[0])
        self.assertEqual(len([n for n in self.journal_notes() if n.startswith("kickoff: GH RETRY")]), 2,
                         "each retry is one journal line")
        self.assertTrue(any(p["headRefName"].startswith("ue-0.25-") for p in self.sb.gh()["prs"]),
                        "the card still ran to its PR\n" + out)

    def test_always_401_ends_the_run_failed_with_the_reason_not_a_traceback(self):
        rc, out = self.sb.kickoff("--agent", "codex", STUB_DAY0_ONLY="0.25", FAKE_GH_FAIL="always", **self.NO_WAIT)
        self.assertNotIn("Traceback", out)
        self.assertNotIn("unexpected error", out)
        self.assertEqual(rc, 1, out)
        self.assertEqual(out.count("SKIP cycle: GitHub failed after the retries"), kickoff.GH_CYCLE_FAILS - 1, out)
        last = out.strip().splitlines()[-1]
        self.assertIn(f"KICKOFF FAILED: GitHub did not answer for {kickoff.GH_CYCLE_FAILS} cycles in a row", last)
        self.assertIn("HTTP 401: Bad credentials", last)
        self.assertTrue(any(n.startswith("kickoff: failed: GitHub did not answer") for n in self.journal_notes()))

    def test_a_create_github_did_before_a_502_is_not_filed_twice(self):
        env = self.sb.env(FAKE_GH_FAIL="1", FAKE_GH_FAIL_ON="issue create", FAKE_GH_FAIL_AFTER="1",
                          FAKE_GH_FAIL_TEXT="HTTP 502: Bad Gateway (https://api.github.com/graphql)", **self.NO_WAIT)
        lines = []
        with unittest.mock.patch.dict(os.environ, env), unittest.mock.patch.object(kickoff, "GH_RETRY_DELAYS", (0,) * 4):
            gh = kickoff.GH()
            gh.on_retry = lines.append
            n = gh.create_issue("[UE-9.9] a card", "body", ["task"])
        self.assertEqual([i["number"] for i in self.sb.gh()["issues"]], [n])
        self.assertEqual(len(lines), 1, lines)
        self.assertIn("GitHub did it after all", lines[0])

    def test_a_permanent_error_is_not_retried(self):
        env = self.sb.env(FAKE_GH_FAIL="always", FAKE_GH_FAIL_TEXT="HTTP 404: Not Found", **self.NO_WAIT)
        lines = []
        with unittest.mock.patch.dict(os.environ, env):
            gh = kickoff.GH()
            gh.on_retry = lines.append
            with self.assertRaises(kickoff.GHError):
                gh.issues()
        self.assertEqual(lines, [])

class AutoParallel(unittest.TestCase):
    """No --parallel: kickoff starts every ready card whose lane overlaps no running card's (bounded by the CPU
    count), not a fixed 2. Four day-0 cards with no After and disjoint lanes build at the same time; --parallel 2
    (or KICKOFF_PARALLEL) caps them at 2. Broken on purpose (the old fixed default of 2): the peak is 2."""

    ONLY = "0.0,0.2,0.7,0.19"

    def setUp(self):
        self.sb = ks.KickoffSandbox(thj.PEOPLE)
        self.addCleanup(self.sb.close)

    def peak(self):
        spans, open_ = [], {}
        for s in self.sb.sessions():
            if s.get("review") or not s["card"].startswith("UE-"):
                continue
            if s["event"] == "start":
                open_[s["card"]] = s["t"]
            elif s["event"] == "end" and s["card"] in open_:
                spans.append((open_.pop(s["card"]), s["t"]))
        return max((sum(1 for a, b in spans if a <= t < b) for t, _ in spans), default=0)

    def test_four_ready_cards_start_together_without_a_flag(self):
        self.assertGreaterEqual(os.cpu_count() or 1, 4, "needs a machine with 4 CPUs")
        rc, out = self.sb.kickoff("--agent", "codex", "--practice", STUB_DAY0_ONLY=self.ONLY, STUB_SLEEP="4")
        self.assertEqual(rc, 0, out)
        self.assertEqual(self.peak(), 4, out[-3000:])

    def test_parallel_flag_caps(self):
        rc, out = self.sb.kickoff("--agent", "codex", "--practice", "--parallel", "2", STUB_DAY0_ONLY=self.ONLY,
                                  STUB_SLEEP="4")
        self.assertEqual(rc, 0, out)
        self.assertEqual(self.peak(), 2, out[-3000:])

    def test_session_cap(self):
        cpus = os.cpu_count() or 1
        self.assertEqual(kickoff.session_cap(0), cpus)
        self.assertEqual(kickoff.session_cap(2), min(2, cpus))
        self.assertEqual(kickoff.session_cap(10 ** 6), cpus)


class TwoMachinesAtOnce(unittest.TestCase):
    """The Mac and the Windows packaging machine run kickoff at the same time on one repo: each card job runs on one
    machine only. Both Producers can file a card twice; only the oldest issue runs. A card another machine claimed
    (KICKOFF CLAIM comment) waits; the claim read-back settles two claims made in the same second. Broken on purpose
    (no claim, no twin check): every card was built on both machines, 4 of 4, simultaneous or 'doing' first."""

    ONLY = "0.0,0.2,0.7,0.19"   # cards with no `Runs on:` line and no After: both machines may build each one
    MACHINES = {"mac": dict(AGENT_OPS_PLATFORM="darwin", KICKOFF_MAC_MACHINE="0", KICKOFF_PACKAGING_MACHINE="0"),
                "win": dict(AGENT_OPS_PLATFORM="win32", KICKOFF_MAC_MACHINE="0", KICKOFF_PACKAGING_MACHINE="1")}

    def setUp(self):
        self.sb = ks.KickoffSandbox(thj.PEOPLE)
        self.addCleanup(self.sb.close)
        with open(os.path.join(self.sb.repo, kickoff.practice.MARKER), "w", encoding="utf-8") as fh:
            fh.write(kickoff.practice.MARKER_TEXT)
        self.sb.git("add", "-A")
        self.sb.git("commit", "-q", "-m", "practice repo")
        self.sb.git("push", "-q", "origin", "main")
        self.repos = {"mac": self.sb.repo, "win": self.sb.second_machine("win")}

    def start(self, name):
        env = self.sb.machine_env(name, STUB_DAY0_ONLY=self.ONLY, STUB_SLEEP="2", **self.MACHINES[name])
        return subprocess.Popen([sys.executable, "tools/kickoff.py", "--agent", "codex", "--parallel", "2"],
                                cwd=self.repos[name], env=env, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                                text=True)

    def doing(self):
        try:
            return any("doing" in i["labels"] for i in self.sb.gh()["issues"])
        except (OSError, ValueError):   # not written yet, or mid-write
            return False

    def run_both(self, doing_first):
        outs = []
        for _ in range(5):
            procs = {"mac": self.start("mac")}
            if doing_first:   # the Windows kickoff starts once the Mac has moved a card to `doing`
                deadline = time.time() + 300
                while not self.doing() and time.time() < deadline and procs["mac"].poll() is None:
                    time.sleep(0.1)
                doing_first = False
            procs["win"] = self.start("win")
            for name, p in procs.items():
                out = p.communicate(timeout=1200)[0]
                self.assertEqual(p.returncode, 0, f"{name}:\n{out[-3000:]}")
                self.assertNotIn("ERROR", out, f"{name}:\n{out[-3000:]}")
                outs.append(out)
            answered, _ = self.sb.human_round()
            if not answered:
                break
        return "\n".join(outs)

    def check(self, out):
        built = {n: [s["card"] for s in self.sb.machine_sessions(n) if s["event"] == "start" and not s.get("review")
                     and s["card"].startswith("UE-")] for n in self.MACHINES}
        reviewed = [s["card"] for n in self.MACHINES for s in self.sb.machine_sessions(n)
                    if s["event"] == "start" and s.get("review")]
        cards = ["UE-" + k for k in self.ONLY.split(",")]
        self.assertEqual(sorted(built["mac"] + built["win"]), sorted(cards), (built, out[-4000:]))
        self.assertEqual(sorted(reviewed), sorted(cards), "one review per card, on one machine")
        s = self.sb.gh()
        self.assertEqual(sorted(p["headRefName"].split("-")[1] for p in s["prs"]), sorted(self.ONLY.split(",")))
        self.assertTrue(all(p["state"] == "MERGED" for p in s["prs"]), s["prs"])
        for it in s["issues"]:
            if "task" in it["labels"]:
                self.assertEqual(it["state"], "CLOSED", it["title"])
                self.assertEqual(kickoff.active_claims(it["comments"]), [], it["title"])
        self.assertNotIn("push of", out, "no machine pushed over the other's branch")

    def test_both_start_in_the_same_second(self):
        self.check(self.run_both(doing_first=False))

    def test_the_second_machine_starts_while_a_card_is_doing(self):
        self.check(self.run_both(doing_first=True))


if __name__ == "__main__":
    unittest.main()
