"""Tests for tools/prompt_log.py on planted logs: a card over 2x the median must be flagged,
the rehearsal proof must fail when a block is missing, and exports must redact secrets."""
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
import prompt_log  # noqa: E402

DAY = "2026-11-12"


def rec(event, card, session="s1", **kw):
    r = {"ts": DAY + "T10:00:00+00:00", "event": event, "card": card, "session": session, "role": "Gameplay Dev"}
    r.update(kw)
    return r


class LogCase(unittest.TestCase):
    def setUp(self):
        self.dir = tempfile.mkdtemp()

    def tearDown(self):
        shutil.rmtree(self.dir, ignore_errors=True)

    def write(self, recs, day=DAY):
        with open(os.path.join(self.dir, day + ".jsonl"), "a") as fh:
            for r in recs:
                fh.write(json.dumps(r) + "\n")
            fh.write("not json\n")  # a torn line must not crash the reader

    def cli(self, *args):
        args = list(args)
        if args[0] == "status" and "--root" not in args:
            args.append("--skip-repo")  # spend tests; AgentOpsLineTests runs the repo checks
        buf = io.StringIO()
        with redirect_stdout(buf):
            rc = prompt_log.main(args + ["--log", self.dir])
        return rc, buf.getvalue()

    def stops(self, card, total, session):
        # Stop fires several times per session with a growing total; only the last one counts.
        return [rec("stop", card, session, tokens={"input": total // 2, "output": 0}),
                rec("stop", card, session, tokens={"input": total, "output": 0})]


class StatusTests(LogCase):
    def test_card_over_twice_median_is_flagged(self):
        self.write(self.stops("1", 100, "a") + self.stops("2", 120, "b") + self.stops("3", 110, "c") + self.stops("4", 500, "d"))
        rc, out = self.cli("status", "--strict")
        self.assertEqual(rc, 1, out)
        self.assertIn("#4 4.3x", out)
        self.assertIn("median_tokens=115", out)

    def test_even_cards_pass(self):
        self.write(self.stops("1", 100, "a") + self.stops("2", 120, "b") + self.stops("3", 110, "c"))
        rc, out = self.cli("status", "--strict")
        self.assertEqual(rc, 0, out)
        self.assertIn("REVIEW(>2x median): none", out)

    def test_falls_back_to_tool_calls(self):
        self.write([rec("tool", "1")] * 2 + [rec("tool", "2")] * 2 + [rec("tool", "3")] * 9)
        rc, out = self.cli("status", "--strict")
        self.assertEqual(rc, 1)
        self.assertIn("median_calls=2", out)

    def test_too_few_cards(self):
        self.write([rec("tool", "1")])
        rc, out = self.cli("status", "--strict")
        self.assertEqual(rc, 0)
        self.assertIn("n/a", out)

    def test_no_log_exits_2(self):
        self.assertEqual(self.cli("status")[0], 2)


class AskRowsTests(LogCase):
    def test_asks_listed_and_matched_by_expect(self):
        self.write([rec("ask", "0.18", tool="Bash", command="git push origin main", reason="`git push` to 'main'")])
        rc, out = self.cli("blocked", "--expect", "git push")
        self.assertEqual(rc, 0, out)
        self.assertIn("asked: 1 call(s)", out)
        rc, out = self.cli("blocked", "--expect", "deletes in bulk")  # broken on purpose: no such ask in the log
        self.assertEqual(rc, 1, out)


class CapTests(LogCase):
    """gates.json daily_token_cap: one machine over it in one UTC day fails status even when every card looks even."""

    def gates(self, cap):
        path = os.path.join(self.dir, "gates.json")
        with open(path, "w") as fh:
            json.dump({"daily_token_cap": cap}, fh)
        return path

    def host_stops(self, card, total, session, host):
        return [dict(r, host=host) for r in self.stops(card, total, session)]

    def test_machine_over_cap_fails_even_with_even_cards(self):
        # Broken on purpose: three even cards on mac1, each 400, cap 1000 -> 1200 on one machine.
        self.write(self.host_stops("1", 400, "a", "mac1") + self.host_stops("2", 400, "b", "mac1")
                   + self.host_stops("3", 400, "c", "mac1") + self.host_stops("4", 400, "d", "win1"))
        rc, out = self.cli("status", "--gates", self.gates(1000))
        self.assertEqual(rc, 1, out)
        self.assertIn("cap=OVER:mac1@2026-11-12 1,200/1,000", out)
        self.assertIn("REVIEW(>2x median): none", out)
        self.assertNotIn("win1@", out)

    def test_under_cap_passes(self):
        self.write(self.host_stops("1", 400, "a", "mac1") + self.host_stops("2", 400, "b", "win1"))
        rc, out = self.cli("status", "--gates", self.gates(1000))
        self.assertEqual(rc, 0, out)
        self.assertIn("cap=ok(max 400/1,000)", out)

    def test_cap_counts_per_day(self):
        self.write(self.host_stops("1", 600, "a", "mac1"))
        self.write([dict(r, ts="2026-11-13T10:00:00+00:00") for r in self.host_stops("2", 600, "b", "mac1")], day="2026-11-13")
        rc, out = self.cli("status", "--gates", self.gates(1000))
        self.assertEqual(rc, 0, out)

    def test_no_token_totals_says_so(self):
        self.write([rec("tool", "1", host="mac1")])
        rc, out = self.cli("status", "--gates", self.gates(1000))
        self.assertEqual(rc, 0)
        self.assertIn("cap=n/a(no token totals)", out)

    def test_shipped_gates_have_a_cap(self):
        self.assertGreater(prompt_log.load_cap(prompt_log.GATES) or 0, 0)


class AgentOpsLineTests(LogCase):
    """status prints the whole AGENT-OPS line, so the Producer pastes one command's output."""

    def setUp(self):
        super().setUp()
        import subprocess
        sys.path.insert(0, os.path.join(ROOT, "tools"))
        import secrets_check
        self.sc = secrets_check
        self.repo = tempfile.mkdtemp()
        subprocess.run(["git", "init", "-q"], cwd=self.repo, check=True)
        src = os.path.join(ROOT, "pipeline", "agent-ops")
        os.makedirs(os.path.join(self.repo, "pipeline", "agent-ops"))
        for f in ("settings.json", "gates.json", "components.csv", "agent-tools.json"):
            shutil.copy(os.path.join(src, f), os.path.join(self.repo, "pipeline", "agent-ops", f))
        with open(os.path.join(self.repo, ".gitignore"), "w") as fh:
            fh.write(".env\n.env.*\n!.env.example\n*.pem\n*.key\n")
        secrets_check.install(self.repo)

    def tearDown(self):
        shutil.rmtree(self.repo, ignore_errors=True)
        super().tearDown()

    def line(self, out):
        return [ln for ln in out.splitlines() if ln.startswith("AGENT-OPS ")][-1]

    def test_clean_repo_and_log_pass(self):
        self.write([rec("tool", "1"), rec("ask", "1", tool="Bash", reason="push")])
        rc, out = self.cli("status", "--day", DAY, "--root", self.repo)
        self.assertEqual(rc, 0, out)
        self.assertEqual(self.line(out), f"AGENT-OPS day={DAY} secrets=0 settings=ok blocked=0 asked=1 "
                                         "cap=n/a(no token totals) REVIEW=n/a stuck=none")

    def test_missing_settings_fails(self):
        os.remove(os.path.join(self.repo, ".claude", "settings.json"))  # broken on purpose
        self.write([rec("tool", "1")])
        rc, out = self.cli("status", "--day", DAY, "--root", self.repo)
        self.assertEqual(rc, 1, out)
        self.assertIn("settings=1 ", self.line(out))
        self.assertIn(".claude/settings.json: missing", out)

    def test_tracked_secret_file_fails(self):
        import subprocess
        with open(os.path.join(self.repo, "deploy.pem"), "w") as fh:
            fh.write("x\n")
        subprocess.run(["git", "add", "-f", "deploy.pem"], cwd=self.repo, check=True)
        self.write([rec("tool", "1")])
        rc, out = self.cli("status", "--root", self.repo)
        self.assertEqual(rc, 1, out)
        self.assertIn("secrets=1 ", self.line(out))

    def test_stuck_card_fails_and_is_named(self):
        fail = dict(build=True, build_ok=False, error_sha256="abc")
        self.write([rec("tool", "7", **fail), rec("tool", "7", **fail), rec("tool", "8", build=True, build_ok=False, error_sha256="x")])
        rc, out = self.cli("status", "--root", self.repo)
        self.assertEqual(rc, 1, out)
        self.assertIn("stuck=#7", self.line(out))
        self.assertNotIn("#8", self.line(out))

    def test_review_cards_listed(self):
        self.write(self.stops("1", 100, "a") + self.stops("2", 120, "b") + self.stops("3", 110, "c") + self.stops("4", 500, "d"))
        rc, out = self.cli("status", "--root", self.repo)
        self.assertEqual(rc, 0, out)
        self.assertIn("REVIEW=#4 ", self.line(out))


class SuggestCapTests(LogCase):
    def test_cap_is_three_times_largest_session_times_sessions(self):
        self.write(self.stops("1", 100000, "a") + self.stops("2", 250000, "b"))
        rc, out = self.cli("suggest-cap", "--sessions-per-day", "6")
        self.assertEqual(rc, 0, out)
        self.assertIn("max_session_tokens=250000", out)
        self.assertIn("daily_token_cap=4500000", out)

    def test_no_token_totals_fails(self):
        self.write([rec("tool", "1"), rec("stop", "1", tokens={"input": 0, "output": 0})])  # nothing measured
        rc, out = self.cli("suggest-cap", "--sessions-per-day", "6")
        self.assertEqual(rc, 1, out)
        self.assertIn("no session", out)

    def test_needs_sessions_per_day(self):
        self.write(self.stops("1", 100, "a"))
        with self.assertRaises(SystemExit), redirect_stdout(io.StringIO()):
            import contextlib
            with contextlib.redirect_stderr(io.StringIO()):
                self.cli("suggest-cap")


class BlockedTests(LogCase):
    def test_rehearsal_proof(self):
        self.write([rec("blocked", "0.18", tool="Edit", reason="'tools/check_pr.py' is a gate file (tools/**).", command="tools/check_pr.py"),
                    rec("blocked", "0.18", tool="Bash", reason="'curl' is a network command.", command="curl x")])
        self.assertEqual(self.cli("blocked", "--expect", "tools/", "--expect", "curl")[0], 0)

    def test_blocked_settings_change_counts(self):
        self.write([rec("config", "0.18", source="project_settings", blocked=True, file_path=".claude/settings.json"),
                    rec("config", "0.18", source="user_settings", blocked=False)])
        rc, out = self.cli("blocked", "--expect", "project_settings")
        self.assertEqual(rc, 0, out)
        self.assertEqual(self.cli("blocked", "--expect", "user_settings")[0], 1)

    def test_missing_block_fails(self):
        self.write([rec("blocked", "0.18", tool="Bash", reason="'curl' is a network command.")])
        rc, out = self.cli("blocked", "--expect", "tools/", "--expect", "curl")
        self.assertEqual(rc, 1)
        self.assertIn("MISSING: no blocked or asked call mentions 'tools/'", out)


class SummaryExportTests(LogCase):
    def test_summary_counts(self):
        self.write([rec("tool", "12"), rec("tool", "12"), rec("blocked", "12"), rec("prompt", "12", prompt="hi")])
        rc, out = self.cli("summary")
        self.assertEqual(rc, 0)
        self.assertIn("12 | 1 | Gameplay Dev | 2 | 1 | 1 | 0", out)

    def test_export_redacts(self):
        key = "ghp" + "_" + "Zz9" * 12
        self.write([rec("prompt", "12", prompt="use token " + key)])
        out_file = os.path.join(self.dir, "out", DAY + ".md")
        rc, _ = self.cli("export", "--day", DAY, "--out", out_file)
        self.assertEqual(rc, 0)
        with open(out_file) as fh:
            body = fh.read()
        self.assertNotIn(key, body)
        self.assertIn("[REDACTED:github-token]", body)
        self.assertIn("## Card 12", body)


class AttemptsTests(LogCase):
    def build(self, card, ok, err="e1"):
        return rec("tool", card, tool="Bash", build=True, build_ok=ok, error_sha256=None if ok else err)

    def test_same_failure_twice_stops(self):
        self.write([self.build("12", False), self.build("12", True), self.build("12", False), self.build("13", False)])
        rc, out = self.cli("attempts", "--card", "12")
        self.assertEqual(rc, 1, out)
        self.assertIn("attempts card=12 builds=3 failed=2 same_failure_max=2", out)
        self.assertIn("STOP", out)

    def test_different_failures_and_other_cards_pass(self):
        self.write([self.build("12", False, "e1"), self.build("12", False, "e2"), self.build("13", False, "e1"),
                    self.build("13", False, "e1"), rec("tool", "12")])
        rc, out = self.cli("attempts", "--card", "12")
        self.assertEqual(rc, 0, out)
        self.assertIn("failed=2 same_failure_max=1", out)

    def test_card_with_no_builds_passes(self):
        self.write([rec("tool", "12")])
        self.assertEqual(self.cli("attempts", "--card", "0.4a")[0], 0)


class ExportCheckTests(LogCase):
    def test_missing_export_fails_then_passes(self):
        self.write([rec("prompt", "12", host="mac1", prompt="a"), rec("tool", "12", host="win1")])
        pdir = os.path.join(self.dir, "prompts")
        os.makedirs(pdir)
        open(os.path.join(pdir, f"{DAY}-mac1.md"), "w").close()
        rc, out = self.cli("export", "--check", "--day", DAY, "--prompts", pdir)
        self.assertEqual(rc, 1, out)
        self.assertIn(f"MISSING: prompts/log/{DAY}-win1.md", out)
        open(os.path.join(pdir, f"{DAY}-win1.md"), "w").close()
        rc, out = self.cli("export", "--check", "--day", DAY, "--prompts", pdir)
        self.assertEqual(rc, 0, out)

    def test_record_without_host_fails(self):
        self.write([rec("prompt", "12", prompt="a")])
        rc, out = self.cli("export", "--check", "--day", DAY, "--prompts", self.dir)
        self.assertEqual(rc, 1)
        self.assertIn("no host", out)

    def test_check_needs_day(self):
        self.write([rec("prompt", "12", host="mac1", prompt="a")])
        with self.assertRaises(SystemExit):
            with redirect_stdout(io.StringIO()), __import__("contextlib").redirect_stderr(io.StringIO()):
                self.cli("export", "--check")


if __name__ == "__main__":
    unittest.main()
