"""tools/kickoff.py, the one command (unit level; the end-to-end walk is in test_honest_jam.py HonestKickoff).
Each check has a passing case and a case broken on purpose."""
import os
import shutil
import subprocess
import sys
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.join(HERE, "fixtures", "kickoff"))
sys.path.insert(0, os.path.join(ROOT, "tools"))
import kickoff  # noqa: E402
import kickoff_sandbox as ks  # noqa: E402
import stubbins  # noqa: E402
import test_honest_jam as thj  # noqa: E402  the filled People table

AFTER_START = "2026-11-12T15:00Z"


@unittest.skipIf(shutil.which("git") is None, "needs git")
class NoRoundCap(unittest.TestCase):
    """D-new-no-round-cap (supersedes D21): kickoff's loops (Producer card fixes, the art gate, review rounds, queued
    asset steps) have no round cap; needs-human only after 3 rounds in a row with the same gap and no better score."""

    def test_parse_split(self):
        both = ["claude", "codex"]
        self.assertEqual(kickoff.parse_split("auto", "claude", both),
                         {"build": "codex", "review": "claude", "critic": "claude", "producer": "claude"})
        self.assertEqual(kickoff.parse_split("builders=claude, critics=codex", "codex", both),
                         {"build": "claude", "critic": "codex"})
        for bad in ("build=gpt", "tester=claude", "build"):
            with self.subTest(bad=bad), self.assertRaises(kickoff.Refused):
                kickoff.parse_split(bad, "claude", both)
        self.assertEqual(kickoff.parse_split("auto", "claude", ["claude"]), {}, "one CLI installed: no split")

    def test_session_tiers_and_columns(self):
        k = kickoff.Kickoff.__new__(kickoff.Kickoff)
        k.agent, k.split = "claude", {"build": "codex"}
        self.assertEqual(k.model("gameplay-dev"), ("Building", "claude-sonnet-5-5"))
        self.assertEqual(k.model("art-director", review=True, critic=True), ("Critic", "claude-opus-5-5"))
        self.assertEqual(k.model("integrator", review=True), ("Hard calls", "claude-fable-5-1"))
        self.assertEqual(k.model("producer"), ("Hard calls", "claude-fable-5-1"))
        self.assertEqual(k.model("gameplay-dev", agent="codex"), ("Building", "gpt-6.1-sol"), "Codex takes the GPT column")
        self.assertEqual((k.agent_for("build"), k.agent_for("critic")), ("codex", "claude"))
        argv = k.agent_argv("hi", "claude-opus-5-5", "Critic", "/w", "/o", "art-director", "claude")
        self.assertIn("--effort", argv, "critic sessions run at high effort")

    def test_no_progress(self):
        self.assertFalse(kickoff.no_progress([("gap", 2)] * 2), "two rounds are not enough")
        self.assertTrue(kickoff.no_progress([("gap a", 3), ("Gap a.", 3), ("gap a", 4)]))
        self.assertFalse(kickoff.no_progress([("gap a", 3), ("gap a", 2), ("gap a", 2)]), "a better score is progress")
        self.assertFalse(kickoff.no_progress([("gap a", 3), ("gap b", 3), ("gap a", 3)]), "a new gap is a change")
        # broken on purpose if someone adds a cap back: 50 rounds that keep getting better never escalate
        self.assertFalse(any(kickoff.no_progress([("same", 100 - i) for i in range(n)]) for n in range(1, 51)))

    def test_review_rounds(self):
        pr = {"comments": [{"body": "ROLE: Dev Lead | s\nVERDICT: changes\n- null check missing\n- name"},
                           {"body": "ROLE: Gameplay Dev | s\nPUSHED: fixes"},
                           {"body": "ROLE: Dev Lead | s2\nVERDICT: changes\n- Null check missing.\n- name"},
                           {"body": "ROLE: Dev Lead | s3\nVERDICT: changes\n- null check missing\n- name"}]}
        self.assertEqual(len(kickoff.review_rounds(pr)), 3)
        self.assertTrue(kickoff.no_progress(kickoff.review_rounds(pr)))
        pr["comments"][2]["body"] = "ROLE: Dev Lead | s2\nVERDICT: approve\nfine"
        self.assertFalse(kickoff.no_progress(kickoff.review_rounds(pr)), "an approve starts the count again")

    def test_art_gate_loop_runs_until_no_progress(self):
        class Fake(kickoff.Kickoff):
            def __init__(self, fails):
                self.fails_seq, self.asks, self.sessions_run = list(fails), [], 0

            def art_problems(self, *a, **k):
                return self.fails_seq.pop(0) if self.fails_seq else []

            def j(self, *a, **k):
                pass

            def session(self, *a, **k):
                self.sessions_run += 1

            def prompt(self, *a, **k):
                return ""

            def post_outbox(self, *a, **k):
                pass

            def raise_ask(self, *a, **k):
                self.asks.append(a)

        class GHStub:
            def label(self, *a, **k):
                pass

            def comment(self, *a, **k):
                pass

        card = type("C", (), {"key": "0.10", "number": 7, "owner_key": "integrator", "body": "", "human": None})()
        improving = [[f"p{j}" for j in range(n)] for n in range(9, 0, -1)]   # 9 failures down to 1, then pass
        k = Fake(improving)
        k.gh = GHStub()
        self.assertTrue(k.art_gate_loop(card, "UE-0.10", "/wt", "base", "/box", "b", 0))
        self.assertEqual((k.sessions_run, k.asks), (9, []), "nine fix rounds, no cap, no ask")
        k = Fake([["shot: flat fill"]] * 10)
        k.gh = GHStub()
        self.assertFalse(k.art_gate_loop(card, "UE-0.10", "/wt", "base", "/box", "b", 0))
        self.assertEqual(k.sessions_run, 2, "the third identical round asks a human")
        self.assertEqual(len(k.asks), 1)


class WindowsLongPaths(unittest.TestCase):
    """Windows CI: `git worktree add .pipeline\\worktrees\\ue-0.26-...` failed with "Filename too long" (MAX_PATH 260)
    on a deep repo path. On native Windows every kickoff git call carries -c core.longpaths=true."""

    def calls(self, platform):
        seen = []
        real_run, real_env = kickoff.subprocess.run, os.environ.get("AGENT_OPS_PLATFORM")

        def fake(argv, **kw):
            seen.append(list(argv))
            return subprocess.CompletedProcess(argv, 0 if argv[-1] != "refs/heads/ue-0.26-deep" else 1, "", "")
        kickoff.subprocess.run = fake
        os.environ["AGENT_OPS_PLATFORM"] = platform
        try:
            k = kickoff.Kickoff.__new__(kickoff.Kickoff)
            k.remote = []
            path = k.worktree("ue-0.26-deep")
        finally:
            kickoff.subprocess.run = real_run
            if real_env is None:
                os.environ.pop("AGENT_OPS_PLATFORM", None)
            else:
                os.environ["AGENT_OPS_PLATFORM"] = real_env
        return path, seen

    def test_worktree_add_carries_longpaths_on_windows(self):
        if os.path.isdir(os.path.join(kickoff.WORKTREES, "ue-0.26-deep")):
            self.skipTest("a real worktree of that name exists")
        path, seen = self.calls("win32")
        add = [a for a in seen if "worktree" in a]
        self.assertTrue(add, seen)
        for argv in seen:
            self.assertEqual(argv[:3], ["git", "-c", "core.longpaths=true"], argv)
        self.assertIn("add", add[0])

    def test_no_longpaths_flag_elsewhere(self):
        if os.path.isdir(os.path.join(kickoff.WORKTREES, "ue-0.26-deep")):
            self.skipTest("a real worktree of that name exists")
        _, seen = self.calls("darwin")
        self.assertTrue(seen)
        self.assertFalse(any("core.longpaths=true" in a for a in seen), seen)

    def test_kickoff_ps1_sets_longpaths_for_the_repo(self):
        with open(os.path.join(ROOT, "tools", "kickoff.ps1"), encoding="utf-8") as fh:
            self.assertIn("config core.longpaths true", fh.read())


class KickoffUnit(unittest.TestCase):
    def setUp(self):
        self.sb = ks.KickoffSandbox(thj.PEOPLE)
        self.addCleanup(self.sb.close)

    def test_pre_jam_on_the_team_repo_runs_only_the_pre_jam_cards(self):
        """Pre-jam: the workbench sample and setup cards are filed and run by agents (Official Rules 7(h)); a card
        that makes game files (0.3) is never filed before the start."""
        rc, out = self.sb.kickoff("--agent", "codex", STUB_DAY0_ONLY="0.25,0.26,0.3")
        self.assertEqual(rc, 3, out)
        self.assertIn("PRE-JAM mode", out.splitlines()[0])
        self.assertIn(f"{kickoff.me()} --practice", out.strip().splitlines()[-1])
        cards = {s["card"] for s in self.sb.sessions() if s["event"] == "start"}
        self.assertIn("UE-0.25", cards, out)
        self.assertTrue(cards <= {"KICKOFF-PRODUCER", "UE-0.25", "UE-0.26"}, cards)
        titles = [i["title"] for i in self.sb.gh()["issues"]]
        self.assertFalse(any(t.startswith("[UE-0.3]") for t in titles), titles)
        rc, out = self.sb.kickoff("--agent", "codex", KICKOFF_NOW=AFTER_START, STUB_DAY0_ONLY="0.25,0.26,0.3")
        self.assertEqual(rc, 0, "broken on purpose: after the jam start the same run files 0.3 too\n" + out)
        titles = [i["title"] for i in self.sb.gh()["issues"]]
        self.assertTrue(any(t.startswith("[UE-0.3]") for t in titles), titles)

    def test_kickoff_applies_the_gate_patch_merges_and_sets_the_repo_settings(self):
        """A gate-only card (0.16: .github/workflows/clock.yml) is done by its agent as a gate.patch; kickoff applies
        it itself through the tool checks (GATE EDIT: by=kickoff), the reviewer approves, kickoff merges, closes the
        card and sets the card's repo settings. No person is asked for any of it."""
        self.sb.save({"issues": [{"number": 1, "title": "Jam tracker", "body": "", "labels": ["tracker"],
                                  "state": "OPEN", "comments": []}], "prs": [], "next": 2})
        rc, out = self.sb.kickoff("--agent", "codex", "--practice", STUB_DAY0_ONLY="0.16,0.2")
        self.assertEqual(rc, 0, out)
        self.assertIn("GATE PATCH UE-0.16 applied by kickoff", out)
        s = self.sb.gh()
        pr = next(p for p in s["prs"] if p["headRefName"].startswith("ue-0.16-"))
        self.assertIn("GATE EDIT: by=kickoff .github/workflows/clock.yml", pr["body"])
        self.assertEqual(pr["state"], "MERGED", out)
        card = next(i for i in s["issues"] if i["title"].startswith("[UE-0.16]"))
        self.assertEqual(card["state"], "CLOSED")
        self.assertFalse(any("NEEDS HUMAN" in c["body"] for c in card["comments"]), card["comments"])
        self.assertEqual(s.get("variables"), {"PIPELINE_CLOCK": "on", "TRACKER_ISSUE": "1"})
        self.assertIn(["workflow", "run", "clock"], s["settings"])
        self.sb.git("fetch", "-q", "origin")
        log = self.sb.git("log", "--format=%s", "origin/main")   # 0.2 and 0.16 merge in either order
        self.assertIn("UE-0.16", log)
        pr = next(p for p in s["prs"] if p["headRefName"].startswith("ue-0.2-"))
        self.assertEqual(pr["state"], "MERGED", "kickoff merged it: CI green, reviewer approved, check_pr passed\n" + out)
        self.assertIn("DONE UE-0.2", out)
        done = next(i for i in s["issues"] if i["title"].startswith("[UE-0.2]"))
        self.assertEqual(done["state"], "CLOSED")
        self.assertFalse(any("NEEDS HUMAN" in c["body"] for c in done["comments"]), "no person asked to merge or close it")

    def test_a_gate_patch_outside_the_lane_is_refused_back_to_the_builder(self):
        """Broken on purpose: the session's gate.patch also loosens gates.json (drops a gate path) and leaves the lane.
        kickoff refuses it (tool route), the builder gets the reasons, and after MAX_FAILS the card is blocked; nothing
        reaches origin."""
        rc, out = self.sb.kickoff("--agent", "codex", "--practice", STUB_DAY0_ONLY="0.16",
                                  STUB_GATE_EXTRA="pipeline/agent-ops/gates.json")
        self.assertEqual(rc, 0, out)
        self.assertIn("GATE PATCH UE-0.16 refused", out)
        self.assertIn("outside the card's File lane", out)
        s = self.sb.gh()
        self.assertFalse([p for p in s["prs"] if p["headRefName"].startswith("ue-0.16-")], "no PR for a refused patch")
        card = next(i for i in s["issues"] if i["title"].startswith("[UE-0.16]"))
        self.assertIn("blocked", card["labels"])

    def test_dry_run_launches_and_writes_nothing(self):
        rc, out = self.sb.kickoff("--agent", "claude", "--dry-run", KICKOFF_NOW=AFTER_START)
        self.assertEqual(rc, 0, out)
        self.assertIn("DRY RUN agent=claude", out)
        self.assertIn("would run: Producer session (tier=Hard calls model=claude-fable-5-1)", out)
        self.assertEqual(self.sb.sessions(), [])
        self.assertFalse(os.path.exists(os.path.join(self.sb.base, "journal.db")))
        self.assertFalse(os.path.exists(self.sb.state), "no issue, label or comment was written")

    def test_refuses_inside_an_agent_session(self):
        rc, out = self.sb.kickoff("--agent", "codex", JAM_ROLE="gameplay-dev")
        self.assertEqual(rc, 2)
        self.assertIn("agent session", out)

    def test_practice_refused_on_the_team_repo(self):
        real = ks.KickoffSandbox(thj.PEOPLE, origin_url="https://github.com/RickTheBuilder/GameJam2026.git")
        self.addCleanup(real.close)
        rc, out = real.kickoff("--agent", "codex", "--practice")
        self.assertEqual(rc, 2, out)
        self.assertIn("team repo", out)
        self.assertFalse(os.path.exists(os.path.join(real.repo, ".pipeline-practice")))

    def test_sessions_use_the_agent_interface_and_never_hold_keys(self):
        rc, out = self.sb.kickoff("--agent", "claude", "--practice", STUB_DAY0_ONLY="0.1,0.7",
                                  OPENAI_API_KEY="fake-openai-NEVERINSESSION0123456789")
        self.assertEqual(rc, 0, out)
        ss = [s for s in self.sb.sessions() if s["event"] == "start"]
        self.assertTrue(ss)
        self.assertEqual({s["agent"] for s in ss}, {"claude"})
        self.assertFalse(any(s["has_key"] for s in ss), "API keys never reach an agent session")
        self.assertIn("PR #", out)

    def test_split_runs_builders_and_critics_on_different_agents(self):
        """Josh, 2026-11-10: with Claude Code and Codex both installed, kickoff --split puts the builders on one and the
        Producer and reviewers on the other, each with its own column's model. Broken on purpose: without --split
        every session is on --agent."""
        rc, out = self.sb.kickoff("--agent", "claude", "--practice", "--split", STUB_DAY0_ONLY="0.1,0.7")
        self.assertEqual(rc, 0, out)
        self.assertIn("split run: build sessions on codex, review sessions on claude", out)
        ss = [s for s in self.sb.sessions() if s["event"] == "start"]
        by = {(s["role"] == "producer", s["review"]): set() for s in ss}
        for x in ss:
            by[(x["role"] == "producer", x["review"])].add(x["agent"])
        self.assertEqual(by.get((True, False)), {"claude"}, ss)     # the Producer
        self.assertEqual(by.get((False, False)), {"codex"}, ss)     # builders
        self.assertEqual(by.get((False, True)), {"claude"}, ss)     # reviewers
        self.assertIn("agent split build=codex,review=claude,critic=claude,producer=claude", out)
        rc, out = self.sb.kickoff("--agent", "codex", "--dry-run", "--split", "build=claude,critic=codex",
                                  KICKOFF_NOW=AFTER_START)
        self.assertEqual(rc, 0, out)
        self.assertIn("split: build sessions on claude (tier=Building model=claude-sonnet-5-5)", out)
        self.assertIn("split: critic sessions on codex (tier=Critic model=gpt-6-astra)", out)
        self.assertIn("split: review sessions on codex (tier=Hard calls model=gpt-6-astra)", out)

    def test_connection_gate_refuses_a_missing_required_tool(self):
        b = os.path.join(self.sb.base, "bin")
        stubbins.make(b, skip=("codex",))
        if os.name != "nt":   # Windows: system_path keeps the host PATH (git, python) minus the hidden programs
            os.symlink(shutil.which("git"), os.path.join(b, "git"))
            os.symlink(sys.executable, os.path.join(b, "python3"))
        path = os.pathsep.join([b, stubbins.system_path(b + "-sys", hide=("codex",))])
        rc, out = self.sb.kickoff("--agent", "codex", PATH=path, KICKOFF_NOW=AFTER_START, STUB_DAY0_ONLY="0.2",
                                  KICKOFF_SKIP_CHECK="0")
        self.assertEqual(rc, 4, out)
        self.assertIn("NOT CONNECTED Codex CLI", out)
        self.assertEqual(self.sb.sessions(), [])
        stubbins.make(b)   # broken-on-purpose pair: with codex back, the gate opens
        rc, out = self.sb.kickoff("--agent", "codex", PATH=path, KICKOFF_NOW=AFTER_START, STUB_DAY0_ONLY="0.2",
                                  KICKOFF_SKIP_CHECK="0")
        self.assertEqual(rc, 0, out)

    def test_seat_left_in_human_is_a_card_problem(self):
        with open(os.path.join(HERE, "fixtures", "honest_jam", "cards", "0.10.json"), encoding="utf-8") as fh:
            body = fh.read()
        import json
        it = json.loads(body)
        it.update(number=1, labels=[], state="OPEN", comments=[])
        self.assertEqual(kickoff.Card(it).problems(), [])
        it["body"] = it["body"].replace("Human who runs and merges this\n\nJosh", "Human who runs and merges this\n\nTD human")
        self.assertTrue(any("seat, not a person" in p for p in kickoff.Card(it).problems()))


if __name__ == "__main__":
    unittest.main()
