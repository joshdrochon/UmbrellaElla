"""tools/status_board.py: the hourly status board renders from saved gh JSON, local git and the journal, with no
network (a fake runner stands in for gh), and its problems and unreadable-input cases fail."""
import io
import json
import os
import shutil
import sqlite3
import subprocess
import sys
import tempfile
import unittest
from contextlib import redirect_stderr, redirect_stdout

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, os.path.join(ROOT, "tools"))
import journal  # noqa: E402
import status_board  # noqa: E402

FIX = os.path.join(HERE, "fixtures", "status_board")
NOW = "2026-11-13T15:00-08:00"   # after G1 and G2 due, before G3


def fake_root(tmp):
    """A root with only what the board reads: the task-card template and a filled Clock (no jam state)."""
    os.makedirs(os.path.join(tmp, "pipeline", "templates"))
    os.makedirs(os.path.join(tmp, "docs"))
    shutil.copy(os.path.join(ROOT, "pipeline", "templates", "task-card.md"), os.path.join(tmp, "pipeline", "templates"))
    shutil.copy(os.path.join(FIX, "jam-brief.md"), os.path.join(tmp, "docs", "jam-brief.md"))
    return tmp


def load(path):
    with open(path, encoding="utf-8") as fh:
        return json.load(fh)


def dump(obj, path):
    with open(path, "w", encoding="utf-8") as fh:
        json.dump(obj, fh)


def slurp(path):
    with open(path, encoding="utf-8") as fh:
        return fh.read()


def run(argv, runner=None):
    out, err = io.StringIO(), io.StringIO()
    with redirect_stdout(out), redirect_stderr(err):
        code = status_board.main(argv, runner=runner) if runner else status_board.main(argv)
    return code, out.getvalue(), err.getvalue()


class StatusBoardTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.mkdtemp()
        self.root = fake_root(os.path.join(self.tmp, "repo"))
        self.out = os.path.join(self.tmp, "board.md")
        self.db = os.path.join(self.tmp, "journal.db")
        con = journal.connect(self.db)
        journal.add(con, "UE-12", "start", role="gameplay-dev")
        journal.add(con, "UE-15", "start", role="audio")
        journal.add(con, "UE-15", "end")
        con.close()

    def tearDown(self):
        shutil.rmtree(self.tmp, ignore_errors=True)

    def board(self, extra=(), runner=None):
        code, out, err = run(["--root", self.root, "--out", self.out, "--now", NOW, "--journal", self.db, *extra], runner)
        text = slurp(self.out) if os.path.isfile(self.out) else ""
        return code, out, err, text

    def test_good_fixture_renders_every_section(self):
        code, out, _, md = self.board(["--from-json", os.path.join(FIX, "good")])
        self.assertEqual(code, 0, out)
        self.assertIn("#13 Richard: approve the arena width outside the 5A range #13", md)
        self.assertRegex(md, r"\| UE-13 \| #13 \| blocked \| Level Designer \| Richard \| yes \|")
        self.assertRegex(md, r"\| UE-14 \| #14 \| done \|")
        self.assertRegex(md, r"\| UE-12 \| gameplay-dev \| host-\w+ \| .* \| yes \| journal \|")
        self.assertRegex(md, r"\| UE-15 \| audio \| .* \| ended \| journal \|")
        self.assertIn("| #40 | UE-12 | UE-12: umbrella lift | ready | pass |", md)
        self.assertIn("| #41 | UE-13 | UE-13: arena | draft | fail |", md)
        self.assertIn("| #42 | #15 | docs tweak | ready | pending |", md)
        self.assertIn("| G1 | 2026-11-12T12:00-08:00 | record posted: Pass |", md)
        self.assertIn("| G2 | 2026-11-13T12:00-08:00 | OVERDUE |", md)
        self.assertIn("| G3 | 2026-11-14T12:00-08:00 | due |", md)
        self.assertIn("| G4 | TBD | TBD |", md)
        self.assertIn("STATUS-BOARD cards=4 needs-human=1 prs=3 failing=1 problems=0", out)

    def test_html_output(self):
        code, _, _, page = self.board(["--from-json", os.path.join(FIX, "good"), "--html"])
        self.assertEqual(code, 0)
        self.assertTrue(page.startswith("<!doctype html>"))
        self.assertIn("<td>OVERDUE</td>", page)

    def test_gh_source_uses_the_runner_not_the_network(self):
        calls = []

        def runner(argv):
            calls.append(argv)
            name = "issues.json" if argv[1] == "issue" else "prs.json"
            with open(os.path.join(FIX, "good", name), encoding="utf-8") as fh:
                return fh.read()
        code, out, _, md = self.board(["--source", "gh", "--repo", "o/r"], runner)
        self.assertEqual(code, 0, out)
        self.assertEqual([c[:3] for c in calls], [["gh", "issue", "list"], ["gh", "pr", "list"]])
        self.assertIn("statusCheckRollup", calls[1][calls[1].index("--json") + 1])
        self.assertIn("--repo", calls[0])
        self.assertIn("record posted: Pass", md)

    def test_gh_failure_exits_2(self):
        def runner(argv):
            raise status_board.InputError("gh issue list exited 1: not logged in")
        code, _, err, _ = self.board(["--source", "gh"], runner)
        self.assertEqual(code, 2)
        self.assertIn("not logged in", err)

    def test_malformed_json_exits_2(self):
        code, _, err, md = self.board(["--from-json", os.path.join(FIX, "bad_json")])
        self.assertEqual(code, 2)
        self.assertIn("not JSON", err)
        self.assertEqual(md, "")

    def test_not_a_list_exits_2_and_missing_dir_exits_2(self):
        d = os.path.join(self.tmp, "obj")
        os.makedirs(d)
        dump({"number": 1}, os.path.join(d, "issues.json"))
        dump([], os.path.join(d, "prs.json"))
        self.assertEqual(self.board(["--from-json", d])[0], 2)
        self.assertEqual(self.board(["--from-json", os.path.join(self.tmp, "nope")])[0], 2)

    def test_source_args_and_bad_now(self):
        self.assertEqual(run(["--root", self.root, "--out", self.out])[0], 2)
        self.assertEqual(run(["--root", self.root, "--source", "local", "--from-json", FIX, "--out", self.out])[0], 2)
        self.assertEqual(run(["--root", self.root, "--source", "local", "--now", "tomorrow", "--out", self.out])[0], 2)

    def test_broken_needs_human_label_without_comment_is_a_problem(self):
        issues = load(os.path.join(FIX, "good", "issues.json"))
        for it in issues:
            if it["number"] == 13:
                it["comments"] = [{"body": "ROLE: level-designer | session x\nplease look"}]
        d = os.path.join(self.tmp, "broken")
        os.makedirs(d)
        dump(issues, os.path.join(d, "issues.json"))
        shutil.copy(os.path.join(FIX, "good", "prs.json"), d)
        code, out, _, md = self.board(["--from-json", d])
        self.assertEqual(code, 1)
        self.assertIn("#13: labelled needs-human but no comment reads", out)
        self.assertIn("## Needs human\n\n- none", md)

    def test_broken_two_state_labels_and_doing_without_session(self):
        issues = load(os.path.join(FIX, "good", "issues.json"))
        for it in issues:
            if it["number"] == 15:
                it["labels"].append({"name": "doing"})
        d = os.path.join(self.tmp, "two")
        os.makedirs(d)
        dump(issues, os.path.join(d, "issues.json"))
        shutil.copy(os.path.join(FIX, "good", "prs.json"), d)
        os.remove(self.db)
        code, out, _, _ = self.board(["--from-json", d])
        self.assertEqual(code, 1)
        self.assertIn("#15: two state labels (todo, doing)", out)
        self.assertNotIn("UE-12: doing, but no session", out)   # its ROLE: comment counts as a session

    def test_unreadable_journal_exits_2(self):
        with open(self.db, "wb") as fh:
            fh.write(b"not sqlite at all" * 100)
        self.assertEqual(self.board(["--from-json", os.path.join(FIX, "good")])[0], 2)

    def test_local_source_reads_branches_tags_and_journal(self):
        g = ["git", "-C", self.root]
        env = dict(os.environ, GIT_AUTHOR_NAME="t", GIT_AUTHOR_EMAIL="t@e", GIT_COMMITTER_NAME="t",
                   GIT_COMMITTER_EMAIL="t@e")
        for cmd in (["init", "-q", "-b", "main"], ["commit", "-q", "--allow-empty", "-m", "x"],
                    ["branch", "ue-12-umbrella-lift"], ["branch", "ue-20-owl-dive"], ["branch", "scratch"],
                    ["tag", "-a", "gate-G1", "-m", "G1"]):
            subprocess.run(g + cmd, check=True, env=env, capture_output=True)
        code, out, _, md = self.board(["--source", "local"])
        self.assertEqual(code, 1, out)       # UE-20 is doing on a branch with no journal session
        self.assertIn("| G1 | 2026-11-12T12:00-08:00 | closed (tag gate-G1) |", md)
        self.assertIn("(branch ue-12-umbrella-lift)", md)
        self.assertNotIn("scratch", md)
        self.assertIn("UE-20: doing, but no session", out)
        self.assertNotIn("UE-12: doing, but no session", out)


if __name__ == "__main__":
    unittest.main()
