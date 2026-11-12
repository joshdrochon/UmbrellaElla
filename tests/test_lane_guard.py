"""Parallel lanes: check_card.py --blocked-by and tools/lane_guard.py (revert-first, daily blocked report)."""
import json
import os
import shutil
import subprocess
import sys
import tempfile
import unittest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "tools"))
import check_card  # noqa: E402
import lane_guard  # noqa: E402

DAY0_HEAD = """| # | Card | Owner role / human | Reviewer | Lane | After | Done when |
|---|---|---|---|---|---|---|
"""


def issue(num, cid, title, used_by="none", extra=""):
    body = (f"### Used by (follow-up card IDs)\n\n{used_by}\n\n### Done when (each line checkable)\n\nx\n{extra}")
    return {"number": num, "title": f"[{cid}] {title}" if cid else title, "body": body}


class BlockedByTests(unittest.TestCase):
    def setUp(self):
        self.root = tempfile.mkdtemp()
        os.makedirs(os.path.join(self.root, "pipeline", "templates"))
        shutil.copy(os.path.join(ROOT, "pipeline", "templates", "task-card.md"),
                    os.path.join(self.root, "pipeline", "templates", "task-card.md"))
        rows = [("0.0", "People", "–"), ("0.3", "Skeleton", "0.0"), ("0.4a", "MCP", "0.3"),
                ("0.4d", "Art dump", "0.4a, 0.10b"), ("0.5", "Tests", "0.3"), ("0.7", "Palette", "–"),
                ("0.10b", "Anchors", "0.7"), ("0.10", "Style frame", "0.10b, 0.4d"), ("0.13", "Physics envelope", "0.5")]
        self.write("".join(f"| {i} | {n} | Gameplay Dev | Dev Lead | `x/{i}/**` | {a} | done |\n" for i, n, a in rows))

    def tearDown(self):
        shutil.rmtree(self.root, ignore_errors=True)

    def write(self, rows):
        with open(os.path.join(self.root, "pipeline", "day0-cards.md"), "w", encoding="utf-8") as fh:
            fh.write("# Day-0\n\n" + DAY0_HEAD + rows)

    def keys(self, card, issues=()):
        return [k for k, _ in check_card.blocked_by(card, self.root, issues)]

    def test_art_card_never_blocks_physics(self):
        waiting = self.keys("0.10b")
        self.assertEqual(set(waiting), {"0.4d", "0.10"})
        self.assertNotIn("0.13", waiting)
        self.assertNotIn("0.5", waiting)

    def test_transitive(self):
        self.assertEqual(set(self.keys("0.4a")), {"0.4d", "0.10"})
        self.assertEqual(set(self.keys("0.0")), {"0.3", "0.4a", "0.4d", "0.5", "0.10", "0.13"})

    def test_leaf_blocks_nothing(self):
        self.assertEqual(self.keys("0.13"), [])

    def test_ue_prefix_is_accepted(self):
        self.assertEqual(self.keys("UE-0.4a"), self.keys("0.4a"))

    def test_unknown_card_raises(self):
        with self.assertRaises(KeyError):
            self.keys("0.99")

    def test_filed_cards_after_line_and_used_by(self):
        issues = [issue(21, "UE-21", "Umbrella physics", used_by="UE-22, #30"),
                  issue(22, "UE-22", "Glide tuning"),
                  issue(30, None, "Owl art sheet"),
                  issue(31, "UE-31", "Owl import", extra="After: #30, 0.10"),
                  issue(40, "UE-40", "Menu art")]
        self.assertEqual(set(self.keys("UE-21", issues)), {"22", "#30", "31"})
        self.assertEqual(set(self.keys("#30", issues)), {"31"})
        self.assertEqual(self.keys("UE-40", issues), [])
        self.assertIn("31", self.keys("0.10b", issues))  # a Day-0 card holds a filed card through its After line

    def test_issue_form_after_field(self):
        # dry run B M3: the issue form had no After field, so filed dependencies were invisible
        form = "\n\n### After (cards that must merge first: #<n> or UE-<n>, comma separated; \"none\")\n\n#30, UE-21\n"
        issues = [issue(21, "UE-21", "Physics"), issue(30, None, "Owl art"),
                  issue(32, "UE-32", "Owl import", extra=form), issue(33, "UE-33", "Menu",
                  extra=form.replace("#30, UE-21", "_No response_"))]
        self.assertEqual(self.keys("#30", issues), ["32"])
        self.assertEqual(self.keys("UE-21", issues), ["32"])
        self.assertEqual(self.keys("UE-33", issues), [])
        with open(os.path.join(ROOT, ".github", "ISSUE_TEMPLATE", "task.yml"), encoding="utf-8") as fh:
            self.assertIn("id: after", fh.read())

    def test_cycle_does_not_hang(self):
        self.write("| 0.1 | A | Producer | Human only | GitHub only | 0.2 | d |\n"
                   "| 0.2 | B | Producer | Human only | GitHub only | 0.1 | d |\n")
        self.assertEqual(self.keys("0.1"), ["0.2"])

    def test_cli_prints_only_the_cards(self):
        r = subprocess.run([sys.executable, os.path.join(ROOT, "tools", "check_card.py"), "--blocked-by", "0.10b",
                            "--root", self.root], capture_output=True, text=True)
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertEqual(r.stdout.splitlines(), ["0.4d  Art dump", "0.10  Style frame"])

    def test_cli_unknown_card_exits_2(self):
        r = subprocess.run([sys.executable, os.path.join(ROOT, "tools", "check_card.py"), "--blocked-by", "0.99",
                            "--root", self.root], capture_output=True, text=True)
        self.assertEqual(r.returncode, 2)
        self.assertEqual(r.stdout, "")

    def test_cli_reads_issues_from_stdin(self):
        r = subprocess.run([sys.executable, os.path.join(ROOT, "tools", "check_card.py"), "--blocked-by", "UE-21",
                            "--issues", "-", "--root", self.root], capture_output=True, text=True,
                           input=json.dumps([issue(21, "UE-21", "Physics", used_by="UE-22"), issue(22, "UE-22", "Glide")]))
        self.assertEqual(r.stdout.splitlines(), ["#22 [UE-22] Glide"])

    def test_real_day0_table(self):
        waiting = [k for k, _ in check_card.blocked_by("0.4d")]
        self.assertIn("0.10", waiting)
        self.assertNotIn("0.13", waiting)  # the movement envelope test does not wait on art


class FakeRun:
    def __init__(self, replies=None, fail=None):
        self.calls, self.replies, self.fail = [], replies or {}, fail

    def __call__(self, cmd):
        self.calls.append(cmd)
        if self.fail and cmd[:len(self.fail)] == self.fail:
            return 1, ""
        for prefix, out in self.replies.items():
            if tuple(cmd[:len(prefix)]) == prefix:
                return 0, out
        return 0, ""


SHA = "abcdef1234567890abcdef1234567890abcdef12"


class RevertTests(unittest.TestCase):
    def setUp(self):
        self.root = tempfile.mkdtemp()
        os.makedirs(os.path.join(self.root, "docs"))
        self.brief("| Integration owner (merges to main) | Sam | yes | BLOCKER |")

    def tearDown(self):
        shutil.rmtree(self.root, ignore_errors=True)

    def brief(self, row):
        with open(os.path.join(self.root, "docs", "jam-brief.md"), "w", encoding="utf-8") as fh:
            fh.write("## People\n| Role | Person | Confirmed | Seat |\n|---|---|---|---|\n" + row + "\n")

    def run_revert(self, subject="UE-12: umbrella physics (#34)", **kw):
        fake = FakeRun({("git", "log"): subject + "\n", ("git", "rev-list"): f"{SHA} 1111111\n",
                        ("gh", "pr", "create"): "https://github.com/o/r/pull/99\n"}, **kw)
        code = lane_guard.revert(SHA, "7", fake, self.root)
        return code, fake.calls

    def test_red_main_opens_revert_pr_and_names_owner(self):
        code, calls = self.run_revert()
        self.assertEqual(code, 0)
        self.assertIn(["git", "revert", "--no-edit", SHA], calls)
        self.assertIn(["git", "push", "origin", "HEAD:refs/heads/revert-abcdef1"], calls)
        create = next(c for c in calls if c[:3] == ["gh", "pr", "create"])
        self.assertIn("revert-abcdef1", create)
        post = next(c for c in calls if c[:3] == ["gh", "issue", "comment"])
        self.assertEqual(post[3], "7")
        body = post[-1]
        self.assertIn("Sam", body)
        self.assertIn("https://github.com/o/r/pull/99", body)
        self.assertIn("30 min", body)
        self.assertIn("Other cards keep working", body)

    def test_merge_commit_reverts_with_mainline(self):
        fake = FakeRun({("git", "log"): "Merge x\n", ("git", "rev-list"): f"{SHA} 111 222\n"})
        lane_guard.revert(SHA, None, fake, self.root)
        self.assertIn(["git", "revert", "--no-edit", "-m", "1", SHA], fake.calls)

    def test_open_revert_pr_is_not_duplicated(self):
        fake = FakeRun({("git", "log"): "UE-12: x\n", ("gh", "pr", "list"): '[{"number": 99}]'})
        self.assertEqual(lane_guard.revert(SHA, "7", fake, self.root), 0)
        self.assertFalse(any(c[:2] == ["git", "revert"] for c in fake.calls))

    def test_red_revert_commit_is_never_reverted(self):
        code, calls = self.run_revert(subject='Revert "UE-12: x"')
        self.assertFalse(any(c[:2] == ["git", "revert"] for c in calls))
        self.assertIn("fix main by hand", next(c for c in calls if c[:3] == ["gh", "issue", "comment"])[-1])

    def test_failed_revert_reports_and_fails(self):
        code, calls = self.run_revert(fail=["git", "revert"])
        self.assertEqual(code, 1)
        self.assertIn("revert it by hand", next(c for c in calls if c[:3] == ["gh", "issue", "comment"])[-1])
        self.assertFalse(any(c[:3] == ["gh", "pr", "create"] for c in calls))

    def test_tbd_owner_points_at_the_seat(self):
        self.brief("| Integration owner (merges to main) | TBD | no | BLOCKER |")
        self.assertIn("TBD", lane_guard.integration_owner(self.root))

    def test_bad_sha_is_usage_error(self):
        self.assertEqual(lane_guard.main(["revert", "--sha", "main; rm -rf /"]), 2)


class BlockedReportTests(unittest.TestCase):
    def test_report_lists_only_waiting_cards(self):
        blocked = [{"number": 5, "title": "[UE-0.4d] Art dump script", "body": ""}]
        text = lane_guard.blocked_report(blocked, [], ROOT)
        self.assertIn("#5 [UE-0.4d] Art dump script", text)
        self.assertIn("0.10  Style frame", text)
        self.assertNotIn("0.13", text)

    def test_no_blocked_cards(self):
        self.assertIn("none", lane_guard.blocked_report([], [], ROOT))

    def test_blocked_posts_to_tracker(self):
        blocked = json.dumps([{"number": 5, "title": "[UE-0.4d] Art dump script", "body": ""}])
        fake = FakeRun({("gh", "issue", "list", "--label", "blocked"): blocked, ("gh", "issue", "list"): "[]"})
        self.assertEqual(lane_guard.blocked("3", fake, ROOT), 0)
        post = fake.calls[-1]
        self.assertEqual(post[:4], ["gh", "issue", "comment", "3"])
        self.assertIn("0.10  Style frame", post[-1])

    def test_gh_failure_fails(self):
        self.assertEqual(lane_guard.blocked("3", FakeRun(fail=["gh", "issue", "list"]), ROOT), 1)


class WorkflowTests(unittest.TestCase):
    def read(self, name):
        with open(os.path.join(ROOT, ".github", "workflows", name), encoding="utf-8") as fh:
            return fh.read()

    def test_main_red_runs_checks_then_reverts(self):
        wf = self.read("main-red.yml")
        self.assertIn("branches: [main]", wf)
        self.assertIn("python3 tools/pipeline_check.py", wf)
        self.assertIn("python3 -m unittest discover -s tests", wf)
        self.assertIn("if: failure() && steps.checks.outcome == 'failure'", wf)
        self.assertIn('python3 tools/lane_guard.py revert --sha "$GITHUB_SHA"', wf)
        self.assertIn("pull-requests: write", wf)

    def test_blocked_report_is_daily(self):
        wf = self.read("blocked-report.yml")
        self.assertIn("schedule:", wf)
        self.assertIn("python3 tools/lane_guard.py blocked --tracker", wf)
        self.assertIn("issues: write", wf)


if __name__ == "__main__":
    unittest.main()
