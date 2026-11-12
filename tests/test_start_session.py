"""tools/start_session.py (+ .sh / .ps1): argument handling, tier lookup, dry run. No network, no real claude run."""
import contextlib
import io
import os
import re
import subprocess
import sys
import tempfile
import unittest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "tools"))
import start_session as ss  # noqa: E402

# Josh, 2026-11-10: builders Sonnet 5.5, quick checks Haiku 5.5, critics and hard calls Opus 5.5 / Fable 5.1
TIERS = {"Hard calls": "claude-fable-5-1", "Critic": "claude-opus-5-5", "Building": "claude-sonnet-5-5",
         "Quick checks": "claude-haiku-5-5"}


def human_env(tmp):
    env = {k: v for k, v in os.environ.items() if k not in ss.AGENT_ENV}
    env.update(START_SESSION_NO_GH="1", JOURNAL_DB=os.path.join(tmp, "journal.db"))
    return env


class Base(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.env = human_env(self.tmp.name)
        self.saved = dict(os.environ)
        os.environ.clear()
        os.environ.update(self.env)
        self.addCleanup(self.restore)

    def restore(self):
        os.environ.clear()
        os.environ.update(self.saved)

    def run_main(self, *argv):
        out, err = io.StringIO(), io.StringIO()
        with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
            rc = ss.main(list(argv))
        return rc, out.getvalue(), err.getvalue()


class ArgTests(Base):
    def test_missing_args_exit_2(self):
        for argv in ((), ("gameplay-dev",), ("--dry-run", "gameplay-dev")):
            rc, _, err = self.run_main(*argv)
            self.assertEqual(rc, 2, argv)
            self.assertIn("usage", err)

    def test_unknown_role_exit_2(self):
        rc, _, err = self.run_main("wizard", "UE-12", "--dry-run")
        self.assertEqual(rc, 2)
        self.assertIn("unknown role", err)

    def test_bad_card_exit_2(self):
        for card in ("twelve", "UE-", "UE-12-foo", "12; rm -rf /", "#x"):
            rc, _, err = self.run_main("gameplay-dev", card, "--dry-run")
            self.assertEqual(rc, 2, card)
            self.assertIn("bad card", err)

    def test_card_forms_normalize(self):
        for raw, want in (("12", "UE-12"), ("ue-12", "UE-12"), ("UE-0.4a", "UE-0.4a"), ("0.4a", "UE-0.4a"),
                          ("#34", "#34")):
            self.assertEqual(ss.norm_card(raw), want)

    def test_model_flag_refused(self):
        rc, _, err = self.run_main("gameplay-dev", "UE-12", "--dry-run", "--model", "claude-haiku-5-5")
        self.assertEqual(rc, 2)
        self.assertIn("model-tiers.md", err)

    def test_refuses_inside_agent_session(self):
        for k in ss.AGENT_ENV:
            os.environ[k] = "1"
            rc, _, err = self.run_main("gameplay-dev", "UE-12", "--dry-run")
            self.assertEqual(rc, 2, k)
            self.assertIn("human starts sessions", err)
            del os.environ[k]


class TierTests(Base):
    def test_every_role_has_a_model(self):
        import json
        with open(ss.GATES, encoding="utf-8") as fh:
            roles = json.load(fh)["roles"]
        for role in roles:
            tier, model = ss.model_for(role)
            self.assertEqual(model, TIERS[tier], role)

    def test_known_tiers(self):
        self.assertEqual(ss.model_for("gameplay-dev"), ("Building", "claude-sonnet-5-5"))
        self.assertEqual(ss.tier_models(), TIERS)
        self.assertEqual(ss.model_for("story", tier="Critic"), ("Critic", "claude-opus-5-5"))
        self.assertEqual(ss.model_for("qa-build", tier="Quick checks"), ("Quick checks", "claude-haiku-5-5"))
        self.assertEqual(ss.model_for("dev-lead"), ("Hard calls", "claude-fable-5-1"))  # "Hard calls (reviewer)"
        self.assertEqual(ss.model_for("producer"), ("Hard calls", "claude-fable-5-1"))

    def test_broken_tier_file_fails(self):
        p = os.path.join(self.tmp.name, "tiers.md")
        with open(p, "w", encoding="utf-8") as fh:
            fh.write("| Tier | Use | Model | GPT |\n|---|---|---|---|\n| Building | x | Opus (no id) | - |\n\n"
                     "| Role (`gates.json` key) | Tier |\n|---|---|\n| gameplay-dev | Building |\n")
        with self.assertRaises(ss.Usage):
            ss.model_for("gameplay-dev", p)
        with self.assertRaises(ss.Usage):
            ss.model_for("audio", p)


class DryRunTests(Base):
    def test_dry_run_prints_command(self):
        rc, out, err = self.run_main("gameplay-dev", "UE-12", "--dry-run", "--effort", "high")
        self.assertEqual(rc, 0, err)
        self.assertIn("START role=gameplay-dev card=UE-12 tier=Building model=claude-sonnet-5-5", out)
        self.assertIn("JAM_ROLE=gameplay-dev", out)
        self.assertIn("JAM_MODEL=claude-sonnet-5-5", out)
        self.assertIn("--model claude-sonnet-5-5 --effort high", out)
        self.assertRegex(out, r"agent\.(sh|ps1)'? gameplay-dev UE-12 claude")

    def test_tier_option_picks_another_row(self):
        rc, out, err = self.run_main("qa-build", "UE-12", "--dry-run", "--tier", "Quick checks")
        self.assertEqual(rc, 0, err)
        self.assertIn("tier=Quick checks model=claude-haiku-5-5", out)
        self.assertNotIn("--tier", out.split("\n", 1)[1], "the option is not passed on to claude")
        rc, out, err = self.run_main("qa-build", "UE-12", "--dry-run", "--tier=Critic")
        self.assertIn("tier=Critic model=claude-opus-5-5", out)
        rc, out, err = self.run_main("qa-build", "UE-12", "--dry-run", "--tier", "Cheapest")   # broken on purpose
        self.assertEqual(rc, 2)
        self.assertIn("unknown --tier", err)

    def test_day0_card_context_loaded(self):
        rc, out, _ = self.run_main("technical-director", "0.4a", "--dry-run")
        self.assertEqual(rc, 0)
        self.assertIn("model=claude-fable-5-1", out)
        self.assertIn("| 0.4a | Editor MCP inventory", out)
        self.assertIn("ROLE: technical-director", out)

    def test_non_day0_card_without_gh_says_so(self):
        rc, out, _ = self.run_main("audio", "UE-40", "--dry-run")
        self.assertEqual(rc, 0)
        self.assertIn("card text not loaded", out)

    @unittest.skipIf(os.name == "nt", "POSIX wrapper")
    def test_shell_wrapper(self):
        r = subprocess.run(["sh", os.path.join(ROOT, "tools", "start_session.sh"), "gameplay-dev", "UE-12",
                            "--dry-run"], env=self.env, capture_output=True, text=True, cwd=ROOT)
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertIn("model=claude-sonnet-5-5", r.stdout)
        r = subprocess.run(["sh", os.path.join(ROOT, "tools", "start_session.sh"), "gameplay-dev"],
                           env=self.env, capture_output=True, text=True, cwd=ROOT)
        self.assertEqual(r.returncode, 2)

    def test_powershell_twin_calls_the_helper(self):
        with open(os.path.join(ROOT, "tools", "start_session.ps1"), encoding="utf-8") as fh:
            ps = fh.read()
        self.assertIn("start_session.py", ps)
        self.assertIn("@args", ps)
        self.assertTrue(re.search(r"exit \$LASTEXITCODE", ps))

    def test_real_run_goes_through_agent_sh(self):
        """Not a dry run: the command it would run is agent.sh with JAM_ROLE set; a stub CLI stands in for claude."""
        cmd, add, _summary, dry = ss.build(["gameplay-dev", "UE-12"], env=self.env)
        self.assertFalse(dry)
        self.assertEqual(add["JAM_ROLE"], "gameplay-dev")
        self.assertIn("claude", cmd)
        self.assertEqual(cmd[cmd.index("--model") + 1], "claude-sonnet-5-5")


if __name__ == "__main__":
    unittest.main()
