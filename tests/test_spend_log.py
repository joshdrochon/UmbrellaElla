"""tools/spend_log.py: per-session tokens and cost by role and card. Each check has a passing case and a broken one."""
import contextlib
import io
import json
import os
import shutil
import sys
import tempfile
import unittest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "tools"))
import spend_log  # noqa: E402


class Base(unittest.TestCase):
    def setUp(self):
        self.dir = tempfile.mkdtemp()
        self.addCleanup(shutil.rmtree, self.dir, True)
        self.csv = os.path.join(self.dir, "spend.csv")
        self.logdir = os.path.join(self.dir, "agent-log")
        os.makedirs(self.logdir)
        env = {"SPEND_CSV": self.csv, "SPEND_AGENT_LOG": self.logdir}
        for k in ("JAM_ROLE", "JAM_CARD", "JAM_MODEL", "SPEND_PRICES"):
            env[k] = None
        self.old = {k: os.environ.get(k) for k in env}
        for k, v in env.items():
            if v is None:
                os.environ.pop(k, None)
            else:
                os.environ[k] = v
        self.addCleanup(self.restore)

    def restore(self):
        for k, v in self.old.items():
            if v is None:
                os.environ.pop(k, None)
            else:
                os.environ[k] = v

    def run_cmd(self, *argv):
        out, err = io.StringIO(), io.StringIO()
        with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
            rc = spend_log.main(list(argv))
        return rc, out.getvalue(), err.getvalue()

    def stop(self, session, ts, **tokens):
        rec = {"ts": ts, "event": "stop", "session": session, "role": "gameplay-dev", "card": "12",
               "tokens": {"input": 0, "output": 0, "cache_read": 0, "cache_write": 0, **tokens}}
        with open(os.path.join(self.logdir, ts[:10] + ".jsonl"), "a", encoding="utf-8") as fh:
            fh.write(json.dumps(rec) + "\n")


class LogTests(Base):
    def test_log_prices_a_session(self):
        rc, out, err = self.run_cmd("log", "--role", "gameplay-dev", "--card", "UE-12", "--model", "claude-opus-5-5",
                                    "--session", "s1", "--input", "1000000", "--output", "100000")
        self.assertEqual(rc, 0, err)
        self.assertIn("SPEND role=gameplay-dev card=UE-12 model=claude-opus-5-5 tokens=1100000 usd=$6.00", out)
        rows = spend_log.read_rows(self.csv)
        self.assertEqual(rows[0]["usd"], 6.0)
        self.assertEqual(rows[0]["provisional"], "no")

    def test_provisional_price_marks_cost(self):
        rc, out, _ = self.run_cmd("log", "--role", "producer", "--card", "0.1", "--model", "claude-fable-5-1",
                                  "--cache-write", "1000000")
        self.assertEqual(rc, 0)
        self.assertIn("card=UE-0.1", out)
        self.assertIn("usd=~$", out)

    def test_env_defaults(self):
        os.environ.update(JAM_ROLE="audio", JAM_CARD="UE-30", JAM_MODEL="claude-opus-5-5")
        rc, out, err = self.run_cmd("log", "--output", "10")
        self.assertEqual(rc, 0, err)
        self.assertIn("role=audio card=UE-30", out)

    def test_bad_numbers_exit_2(self):
        for bad in ("-5", "lots", "1.5"):
            rc, _, err = self.run_cmd("log", "--role", "audio", "--card", "UE-1", "--model", "claude-opus-5-5",
                                      "--input", bad)
            self.assertEqual(rc, 2, bad)
            self.assertIn("--input", err)
        self.assertFalse(os.path.exists(self.csv))

    def test_unknown_model_exit_2(self):
        rc, _, err = self.run_cmd("log", "--role", "audio", "--card", "UE-1", "--model", "gpt-9")
        self.assertEqual(rc, 2)
        self.assertIn("unknown model", err)

    def test_unknown_model_word_is_unpriced(self):
        rc, out, _ = self.run_cmd("log", "--role", "audio", "--card", "UE-1", "--model", "unknown", "--input", "5")
        self.assertEqual(rc, 0)
        self.assertIn("usd=unpriced", out)

    def test_unknown_role_and_bad_card_exit_2(self):
        rc, _, err = self.run_cmd("log", "--role", "wizard", "--card", "UE-1", "--model", "claude-opus-5-5")
        self.assertEqual(rc, 2)
        self.assertIn("unknown role", err)
        rc, _, err = self.run_cmd("log", "--role", "audio", "--card", "nope", "--model", "claude-opus-5-5")
        self.assertEqual(rc, 2)
        self.assertIn("bad card", err)

    def test_note_is_redacted(self):
        key = "sk-ant-api03-" + "A" * 40
        rc, _, _ = self.run_cmd("log", "--role", "audio", "--card", "UE-1", "--model", "claude-opus-5-5",
                                "--note", f"used {key}")
        self.assertEqual(rc, 0)
        with open(self.csv, encoding="utf-8") as fh:
            self.assertNotIn(key, fh.read())


class AgentLogTests(Base):
    def test_from_agent_log_takes_largest_total_per_session(self):
        self.stop("abc", "2026-11-12T10:00:00+00:00", input=100, output=10)
        self.stop("abc", "2026-11-12T10:30:00+00:00", input=500, output=50)
        self.stop("old", "2026-11-11T09:00:00+00:00", input=999)
        rc, out, err = self.run_cmd("log", "--from-agent-log", "--since", "2026-11-12T00:00:00", "--role",
                                    "gameplay-dev", "--card", "UE-12", "--model", "claude-opus-5-5")
        self.assertEqual(rc, 0, err)
        rows = spend_log.read_rows(self.csv)
        self.assertEqual([(r["session"], r["input"], r["output"]) for r in rows], [("abc", 500, 50)])
        rc, out, _ = self.run_cmd("log", "--from-agent-log", "--since", "2026-11-12T00:00:00", "--role",
                                  "gameplay-dev", "--card", "UE-12", "--model", "claude-opus-5-5")
        self.assertIn("already logged", out)
        self.assertEqual(len(spend_log.read_rows(self.csv)), 1)

    def test_no_stop_record_exits_1(self):
        rc, _, err = self.run_cmd("log", "--from-agent-log", "--role", "audio", "--card", "UE-1", "--model",
                                  "claude-opus-5-5")
        self.assertEqual(rc, 1)
        self.assertIn("nothing logged", err)


class SummaryTests(Base):
    def seed(self):
        for role, card, inp in (("audio", "UE-1", 1000000), ("audio", "UE-2", 1000000), ("producer", "UE-1", 0)):
            self.assertEqual(self.run_cmd("log", "--role", role, "--card", card, "--model", "claude-opus-5-5",
                                          "--input", str(inp))[0], 0)

    def test_summary_groups(self):
        self.seed()
        rc, out, _ = self.run_cmd("summary", "--by", "role")
        self.assertEqual(rc, 0)
        self.assertIn("role=audio sessions=2 tokens=2000000 usd=$8.00", out)
        self.assertIn("role=producer sessions=1 tokens=0 usd=$0.00", out)
        self.assertIn("TOTAL sessions=3 tokens=2000000 usd=$8.00", out)
        rc, out, _ = self.run_cmd("summary")
        for head in ("## by role", "## by card", "## by day"):
            self.assertIn(head, out)
        self.assertIn("card=UE-1 sessions=2", out)

    def test_summary_empty(self):
        rc, out, _ = self.run_cmd("summary")
        self.assertEqual(rc, 0)
        self.assertIn("no sessions logged", out)

    def test_malformed_row_exit_2(self):
        self.seed()
        with open(self.csv, "a", encoding="utf-8") as fh:
            fh.write("2026-11-12T00:00:00+00:00,2026-11-12,s,audio,UE-1,claude-opus-5-5,many,0,0,0,,no,\n")
        rc, _, err = self.run_cmd("summary")
        self.assertEqual(rc, 2)
        self.assertIn("line 5", err)

    def test_short_row_exit_2(self):
        self.seed()
        with open(self.csv, "a", encoding="utf-8") as fh:
            fh.write("only,three,fields\n")
        rc, _, err = self.run_cmd("summary")
        self.assertEqual(rc, 2)
        self.assertIn("3 fields", err)

    def test_prices_file_covers_tier_models(self):
        prices = spend_log.load_prices()
        for m in ("claude-fable-5-1", "claude-opus-5-5", "claude-sonnet-5-5", "claude-haiku-5-5"):
            self.assertIn(m, prices)
            for f in spend_log.TOKEN_FIELDS:
                self.assertGreaterEqual(float(prices[m][f]), 0)


if __name__ == "__main__":
    unittest.main()
