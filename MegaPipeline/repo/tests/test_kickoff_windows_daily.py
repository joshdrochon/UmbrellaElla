"""tools/kickoff.py on the Windows packaging machine: after each merge a QA and Build session runs tools\\ue\\daily.ps1
(D-new-merge-daily), only while gates.json native_windows_shell is allow. Broken on purpose to test the test."""
import json
import os
import shutil
import subprocess
import sys
import tempfile
import unittest
from unittest import mock

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, os.path.join(ROOT, "tools"))
import kickoff  # noqa: E402
import ue_run  # noqa: E402

GOOD = ("DAILY abc1234 | PC/Windows 10 | Development | clean-tree=PASS build=PASS package=PASS(warn 0) smoke=PASS(1 map(s)) "
        "workbench=PASS(warn 0) | Not checked: none")


def allow_gates(value):
    g = kickoff.gates()
    g["native_windows_shell"] = value
    return lambda: g


class GHStub:
    def __init__(self, prs=()):
        self._prs, self.comments, self.closed = list(prs), [], []

    def prs(self):
        return self._prs

    def comment(self, n, body):
        self.comments.append((n, body))

    def label(self, *a, **k):
        pass

    def close(self, n):
        self.closed.append(n)


class Card:
    def __init__(self, key="0.2", number=3):
        self.key, self.number, self.cid, self.title = key, number, f"UE-{key}", "Card"
        self.open, self.done, self.labels, self.after, self.lanes = True, False, set(), [], ["docs/x.md"]
        self.owner_key, self.reviewer_key = "producer", "dev-lead"

    def branch_prefix(self):
        return f"ue-{self.key}-"


def bare_kickoff(gh, cards):
    k = kickoff.Kickoff.__new__(kickoff.Kickoff)
    k.gh, k.running, k.prejam, k.daily_q, k.remote = gh, {}, None, [], []
    k.practice, k.tester_prompt = True, None
    k.daily_lock = kickoff.threading.Lock()
    k.cards = lambda: cards
    k.j = lambda *a, **kw: None
    return k


class WindowsDailySwitch(unittest.TestCase):
    def test_only_native_windows_with_allow(self):
        with mock.patch.object(kickoff, "gates", allow_gates("allow")):
            with mock.patch.dict(os.environ, {"AGENT_OPS_PLATFORM": "win32"}):
                self.assertTrue(kickoff.windows_daily())
            with mock.patch.dict(os.environ, {"AGENT_OPS_PLATFORM": "linux"}):
                self.assertFalse(kickoff.windows_daily(), "WSL / Mac: a person runs daily.ps1")
        with mock.patch.object(kickoff, "gates", allow_gates("block")):
            with mock.patch.dict(os.environ, {"AGENT_OPS_PLATFORM": "win32"}):
                self.assertFalse(kickoff.windows_daily(), "block: agents cannot run shells there")

    def test_merged_card_queues_one_daily_job(self):
        pr = {"number": 9, "headRefName": "ue-0.2-card", "state": "MERGED", "mergeCommit": {"oid": "abc"}}
        for value, want in (("allow", 1), ("block", 0)):
            with self.subTest(value=value):
                gh = GHStub([pr])
                k = bare_kickoff(gh, [Card()])
                with mock.patch.object(kickoff, "gates", allow_gates(value)), \
                        mock.patch.dict(os.environ, {"AGENT_OPS_PLATFORM": "win32"}):
                    jobs, _, _ = k.plan()
                self.assertEqual(gh.closed, [3], "the merged card is closed either way")
                daily = [j for j in jobs if j[0] == "daily"]
                self.assertEqual(len(daily), want, jobs)
                if want:
                    self.assertIs(daily[0][2], pr)


class DailyRun(unittest.TestCase):
    def setUp(self):
        self.base = tempfile.mkdtemp()
        self.addCleanup(shutil.rmtree, self.base, True)
        self.root = os.path.join(self.base, "repo")
        os.makedirs(self.root)
        for args in (["init", "-q", "-b", "main"], ["config", "user.email", "t@t"], ["config", "user.name", "t"]):
            subprocess.run(["git", *args], cwd=self.root, check=True)
        with open(os.path.join(self.root, "a.txt"), "w") as fh:
            fh.write("a\n")
        subprocess.run(["git", "add", "-A"], cwd=self.root, check=True)
        subprocess.run(["git", "commit", "-q", "-m", "merge of card 0.2"], cwd=self.root, check=True)
        self.sha = subprocess.run(["git", "rev-parse", "HEAD"], cwd=self.root, capture_output=True, text=True).stdout.strip()
        real_git = kickoff.git

        def git(*args, cwd=None, **kw):
            return real_git(*args, cwd=cwd or self.root, **kw)
        for name, value in (("git", git), ("ROOT", self.root),
                            ("WORKTREES", os.path.join(self.root, ".pipeline", "worktrees")),
                            ("OUTBOXES", os.path.join(self.root, ".pipeline", "outbox"))):
            p = mock.patch.object(kickoff, name, value)
            p.start()
            self.addCleanup(p.stop)
        self.gh = GHStub()
        self.k = bare_kickoff(self.gh, [])
        self.k.prompt = lambda *a, **kw: "prompt"
        self.calls = []

    def session(self, line, comment):
        def run(card_id, role, cwd, outbox, prompt, extra_env, **kw):
            self.calls.append((card_id, role, cwd, extra_env))
            if line:
                rec = os.path.join(cwd, ue_run.RECORD)
                os.makedirs(os.path.dirname(rec), exist_ok=True)
                with open(rec, "a") as fh:
                    fh.write(line + "\n")
            if comment:
                with open(os.path.join(outbox, "comment.md"), "w") as fh:
                    fh.write(comment)
            return 0
        return run

    def test_daily_on_the_merge_commit_posts_and_records(self):
        self.k.session = self.session(GOOD, "ROLE: QA and Build | session t\n" + GOOD)
        self.assertTrue(self.k.daily_run(Card(), {"number": 9, "mergeCommit": {"oid": self.sha}}))
        (cid, role, cwd, env), = self.calls
        self.assertEqual((cid, role, env["JAM_DAILY_COMMIT"]), ("UE-0.2", "qa-build", self.sha))
        head = subprocess.run(["git", "rev-parse", "HEAD"], cwd=cwd, capture_output=True, text=True).stdout.strip()
        self.assertEqual(head, self.sha, "the session runs on the merge commit")
        self.assertEqual(self.gh.comments, [(3, "ROLE: QA and Build | session t\n" + GOOD)])
        with open(os.path.join(self.root, ue_run.RECORD)) as fh:
            self.assertEqual(fh.read(), GOOD + "\n", "merge-check in this checkout sees the line")

    def test_failed_or_missing_daily_is_reported(self):
        self.k.session = self.session(GOOD.replace("workbench=PASS(warn 0)", "workbench=FAIL"), "")
        self.assertFalse(self.k.daily_run(Card(), {"number": 9}))
        self.assertIn("workbench=FAIL", self.gh.comments[-1][1])
        self.k.session = self.session("", "")
        self.assertFalse(self.k.daily_run(Card(), {"number": 9}))
        self.assertIn("No DAILY line", self.gh.comments[-1][1])
        self.assertEqual(len(self.calls), 2, "the second run reuses the qa-daily worktree")


if __name__ == "__main__":
    unittest.main()
