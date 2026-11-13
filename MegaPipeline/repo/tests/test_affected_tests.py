"""Tests for tools/affected_tests.py and the rule that card sessions never run the full unit suite (Josh, 12 Nov: a
docs-only card spent over an hour in `unittest discover` while the game repo's CI took 30 s). Each mapping test plants
a small repo and checks the selection; the guard tests break the rule on purpose and expect the refusal."""
import ast
import glob
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, os.path.join(ROOT, "tools"))
sys.path.insert(0, HERE)
import affected_tests as at  # noqa: E402
import check_card  # noqa: E402
import test__card_session_guard as guard  # noqa: E402

DOCS_CARD = ["docs/decisions.md", "docs/jam-brief.md", ".github/CODEOWNERS"]   # card UE-0.0's change


class Planted:
    """A throwaway repo: tools/foo.py, tools/bar.py (imports foo), tests that read them, and timings."""

    def __init__(self, timings=None):
        self.dir = tempfile.mkdtemp()
        self.add("tools/foo.py", "X = 1\n")
        self.add("tools/bar.py", "import foo\n")
        self.add("tests/test_foo.py", "import foo\nclass A:\n    pass\n")
        self.add("tests/test_bar.py", "import bar\nclass B:\n    pass\n")
        self.add("tests/hermetic.py", "")
        self.add("tests/test_uses_helper.py", "import hermetic\n")
        self.add("tests/test_doc_consistency.py", "class Docs:\n    pass\n")
        self.add("tests/test_names_doc.py", "P = 'docs/x.md'\nclass N:\n    pass\n")
        self.add("tests/test_slow.py", "class Fast:\n    def test_a(self):\n        p = 'docs/x.md'\n"
                                       "class Slow:\n    def test_b(self):\n        p = 'docs/x.md'\n"
                                       "class Other:\n    def test_c(self):\n        pass\n"
                                       "class Helper:\n    p = 'docs/x.md'\n")
        self.add("tests/timings.json", json.dumps(timings or {"modules": {}, "classes": {}}))

    def add(self, path, text):
        full = os.path.join(self.dir, path)
        os.makedirs(os.path.dirname(full), exist_ok=True)
        with open(full, "w", encoding="utf-8") as fh:
            fh.write(text)

    def pick(self, paths, budget=at.BUDGET):
        picked, left, unmapped = at.select(at.Index(self.dir), paths, budget)
        return [t for t, _, _ in picked], [t for t, _, _ in left], unmapped

    def close(self):
        shutil.rmtree(self.dir, ignore_errors=True)


class Mapping(unittest.TestCase):
    def setUp(self):
        self.r = Planted()

    def tearDown(self):
        self.r.close()

    def test_a_tool_maps_to_its_tests_and_the_tests_of_its_importers(self):
        picked, _, _ = self.r.pick(["tools/foo.py"])
        self.assertEqual(picked[0], "test_foo")
        self.assertIn("test_bar", picked)          # bar imports foo
        self.assertNotIn("test_doc_consistency", picked)
        self.assertNotIn("test_names_doc", picked)

    def test_a_changed_test_runs_itself(self):
        self.assertEqual(self.r.pick(["tests/test_bar.py"])[0], ["test_bar"])

    def test_a_test_helper_maps_to_the_tests_that_import_it(self):
        self.assertEqual(self.r.pick(["tests/hermetic.py"])[0], ["test_uses_helper"])

    def test_a_doc_maps_to_the_docs_tests_and_the_tests_that_name_it(self):
        picked, _, _ = self.r.pick(["docs/x.md"])
        self.assertEqual(picked[0], "test_doc_consistency")
        self.assertIn("test_names_doc", picked)
        self.assertIn("test_slow", picked)
        self.assertNotIn("test_foo", picked)

    def test_game_files_map_to_no_python_test(self):
        picked, _, unmapped = self.r.pick(["Source/UmbrellaElla/Private/Motor.cpp", "Content/UmbrellaElla/L.umap"])
        self.assertEqual(picked, [])
        self.assertEqual(len(unmapped), 2)

    def test_base_ref_diff_feeds_the_selection(self):
        """--base REF: the files changed since REF (committed and not) are the input."""
        d = self.r.dir
        git = lambda *a: subprocess.run(["git", "-c", "core.hooksPath=/dev/null", *a], cwd=d, check=True,
                                        capture_output=True)
        git("init", "-q", "-b", "main")
        git("-c", "user.email=t@t", "-c", "user.name=t", "add", "-A")
        git("-c", "user.email=t@t", "-c", "user.name=t", "commit", "-q", "-m", "base")
        git("tag", "start")
        self.r.add("tools/foo.py", "X = 2\n")
        self.assertEqual(at.changed_files(d, "start"), ["tools/foo.py"])
        out = subprocess.run([sys.executable, os.path.join(ROOT, "tools", "affected_tests.py"), "--root", d,
                              "--base", "start"], capture_output=True, text=True)
        self.assertEqual(out.returncode, 0, out.stderr)
        self.assertIn("tests.test_foo", out.stdout.splitlines()[-1])
        self.assertTrue(out.stdout.splitlines()[-1].startswith("python3 -m unittest "))


UE = "Source/UmbrellaElla/"


class UnrealPrefixes(unittest.TestCase):
    """Source/<Module>/<Public|Private>/<Area>/ changes map to UmbrellaElla.<Area> automation test prefixes."""

    def setUp(self):
        self.r = Planted()
        self.addCleanup(self.r.close)
        t = 'IMPLEMENT_SIMPLE_AUTOMATION_TEST(F{0}, "{1}", EAutomationTestFlags::EngineFilter)\n'
        self.r.add(UE + "Private/Tests/Health/HealthRuleTests.cpp", '#include "Health/HealthModel.h"\n'
                   + t.format("A", "UmbrellaElla.Health.DamageScales"))
        self.r.add(UE + "Private/Tests/Health/HealthTestWorld.h", '#include "Core/EllaCharacter.h"\n')
        self.r.add(UE + "Private/Tests/Projectile/ProjectileWorldTests.cpp",
                   '#include "Tests/Health/HealthTestWorld.h"\n#include "UmbrellaElla.h"\n'
                   + t.format("B", "UmbrellaElla.Projectile.World.MovesAndExpires"))
        self.r.add(UE + "Private/Tests/Move/MoveRuleTests.cpp", '#include "Motor/MotorModel.h"\n'
                   + t.format("C", "UmbrellaElla.Move.Baseline") + t.format("D", "UmbrellaElla.Move.World.Hop"))
        self.ue = at.Unreal(self.r.dir)

    def pre(self, path):
        return self.ue.prefixes(path)[0]

    def test_an_area_file_maps_to_its_area_and_the_tests_that_include_it(self):
        self.assertEqual(self.pre(UE + "Public/Health/HealthModel.h"), ["UmbrellaElla.Health"])
        self.assertEqual(self.pre(UE + "Private/Health/HealthModel.cpp"), ["UmbrellaElla.Health"])
        # Motor has no UmbrellaElla.Motor test; the Move tests include its header
        self.assertEqual(self.pre(UE + "Private/Motor/MotorModel.cpp"), ["UmbrellaElla.Move"])

    def test_a_test_file_maps_to_the_names_in_it(self):
        self.assertEqual(self.pre(UE + "Private/Tests/Move/MoveRuleTests.cpp"), ["UmbrellaElla.Move"])

    def test_a_test_helper_header_maps_to_the_test_files_that_include_it(self):
        self.assertEqual(self.pre(UE + "Private/Tests/Health/HealthTestWorld.h"), ["UmbrellaElla.Projectile"])

    def test_build_files_and_unmapped_code_run_every_project_test(self):
        for p in (UE + "UmbrellaElla.Build.cs", "Source/UmbrellaElla.Target.cs", UE + "Private/UmbrellaElla.cpp",
                  UE + "Private/Core/UmbrellaGameMode.cpp"):
            self.assertEqual(self.pre(p), ["UmbrellaElla"], p)

    def test_non_source_paths_are_not_unreal(self):
        self.assertEqual(self.pre("Content/UmbrellaElla/Maps/L_Arena.umap"), [])
        self.assertEqual(self.pre("tools/foo.py"), [])

    def test_the_printed_commands_carry_one_filter(self):
        mac, win = at.ue_commands({"UmbrellaElla.Move", "UmbrellaElla.Health"})
        self.assertEqual(mac, "TEST_FILTER='UmbrellaElla.Health+UmbrellaElla.Move' tools/ue/test.sh")
        self.assertEqual(win, "tools\\ue\\test.ps1 -Filter 'UmbrellaElla.Health+UmbrellaElla.Move'")
        self.assertEqual(at.ue_filter({"UmbrellaElla", "UmbrellaElla.Move"}), "UmbrellaElla")

    def test_the_cli_prints_the_unreal_line_and_no_python_test(self):
        out = subprocess.run([sys.executable, os.path.join(ROOT, "tools", "affected_tests.py"), "--root", self.r.dir,
                              UE + "Public/Health/HealthModel.h"], capture_output=True, text=True)
        self.assertEqual(out.returncode, 0, out.stderr)
        self.assertIn("TEST_FILTER='UmbrellaElla.Health' tools/ue/test.sh", out.stdout)
        self.assertIn("no unit test to run", out.stdout)
        self.assertNotIn("no Python test reads", out.stdout)

    def test_paths_keep_their_leading_dot(self):
        self.assertEqual(at.norm(self.r.dir, "./.github/CODEOWNERS"), ".github/CODEOWNERS")
        self.assertEqual(at.norm(self.r.dir, os.path.join(self.r.dir, "docs", "x.md")), "docs/x.md")


class Budget(unittest.TestCase):
    def test_a_module_too_slow_to_fit_runs_only_its_classes_that_name_the_change(self):
        r = Planted({"modules": {"test_slow": 900, "test_names_doc": 1, "test_doc_consistency": 1},
                     "classes": {"test_slow.Fast": 20, "test_slow.Slow": 600, "test_slow.Other": 5}})
        self.addCleanup(r.close)
        picked, left, _ = r.pick(["docs/x.md"], budget=300)
        self.assertIn("test_slow.Fast", picked)
        self.assertNotIn("test_slow", picked)
        self.assertNotIn("test_slow.Other", picked)   # does not name the change
        self.assertNotIn("test_slow.Helper", picked)  # not a test class
        self.assertNotIn("test_slow.Slow", picked)    # names it but is over the budget alone: left for CI
        self.assertEqual(left, ["test_slow"])

    def test_the_selection_stays_inside_the_budget(self):
        r = Planted({"modules": {"test_foo": 200, "test_bar": 200}, "classes": {"test_bar.B": 200}})
        self.addCleanup(r.close)
        picked, left, _ = r.pick(["tools/foo.py"], budget=300)
        self.assertEqual(picked, ["test_foo"])
        self.assertEqual(left, ["test_bar"])

    def test_this_repo_docs_card_selection_is_inside_five_minutes(self):
        """Card UE-0.0's change (docs/decisions.md, docs/jam-brief.md, CODEOWNERS), on the measured timings."""
        index = at.Index(ROOT)
        self.assertTrue(index.mod_time, "tests/timings.json has no module times")
        picked, _, _ = at.select(index, DOCS_CARD)
        names = [t for t, _, _ in picked]
        self.assertIn("test_doc_consistency", names)
        self.assertLessEqual(sum(s for _, s, _ in picked), at.BUDGET)
        for slow in ("test_honest_jam", "test_honest_jam.HonestJam", "test_kickoff", "test_kickoff_unattended"):
            self.assertNotIn(slow, names)

    def test_a_class_that_runs_the_full_suite_itself_is_never_picked(self):
        """Every test class whose code starts a nested `unittest discover` is in CI_ONLY."""
        for mod in at.test_modules(ROOT):
            text = read(os.path.join("tests", mod + ".py"))
            helpers = [f.name for f in ast.parse(text).body if isinstance(f, ast.FunctionDef)
                       and re.search(r'"unittest",\s*"discover"', ast.get_source_segment(text, f))]
            for name, src in at.classes(text):
                if re.search(r'"unittest",\s*"discover"', src) and mod != "test_affected_tests" or \
                        any(h + "(" in src for h in helpers):
                    self.assertIn(f"{mod}.{name}", at.CI_ONLY)
        r = Planted({"modules": {"test_slow": 1}, "classes": {}})
        self.addCleanup(r.close)
        at.CI_ONLY["test_slow.Slow"] = "planted"
        self.addCleanup(at.CI_ONLY.pop, "test_slow.Slow")
        picked, left, _ = r.pick(["docs/x.md"])
        self.assertNotIn("test_slow", picked)
        self.assertNotIn("test_slow.Slow", picked)
        self.assertIn("test_slow.Fast", picked)
        self.assertIn("test_slow.Slow", left)

    def test_every_test_module_has_a_measured_time(self):
        index = at.Index(ROOT)
        missing = [m for m in index.mods if m not in index.mod_time and m != "test_affected_tests"]
        self.assertEqual(missing, [], "time each new module: python3 tools/affected_tests.py --measure tests/<it>.py")

    def test_measure_named_modules_merges_into_the_timings(self):
        r = Planted({"modules": {"test_foo": 7}, "classes": {"test_foo.A": 7}})
        self.addCleanup(r.close)
        r.add("tests/test_quick.py", "import unittest\nclass Q(unittest.TestCase):\n    def test_ok(self):\n"
                                     "        pass\n")
        env = dict(os.environ, JAM_KICKOFF="1", JAM_ROLE="qa-build")   # one module is allowed in a card session
        out = subprocess.run([sys.executable, os.path.join(ROOT, "tools", "affected_tests.py"), "--root", r.dir,
                              "--measure", "tests/test_quick.py"], capture_output=True, text=True, env=env)
        self.assertEqual(out.returncode, 0, out.stdout + out.stderr)
        with open(os.path.join(r.dir, at.TIMINGS), encoding="utf-8") as fh:
            got = json.load(fh)
        self.assertEqual(got["modules"]["test_foo"], 7)
        self.assertIn("test_quick", got["modules"])
        self.assertIn("test_quick.Q", got["classes"])
        full = subprocess.run([sys.executable, os.path.join(ROOT, "tools", "affected_tests.py"), "--root", r.dir,
                               "--measure"], capture_output=True, text=True, env=env)
        self.assertEqual(full.returncode, 2)   # the whole suite: never in a card session

    def test_a_run_over_the_budget_warns_and_never_fails(self):
        r = Planted({"modules": {"test_quick": 0}, "classes": {}})   # estimated 0 s, so a 0 s budget still picks it
        self.addCleanup(r.close)
        r.add("tests/test_quick.py", "import unittest\nclass Q(unittest.TestCase):\n    def test_ok(self):\n"
                                     "        pass\n")
        out = subprocess.run([sys.executable, os.path.join(ROOT, "tools", "affected_tests.py"), "--root", r.dir,
                              "--budget", "0", "--run", "tests/test_quick.py"], capture_output=True, text=True)
        self.assertEqual(out.returncode, 0, out.stdout + out.stderr)
        warn = [ln for ln in out.stdout.splitlines() if "WARNING" in ln]
        self.assertEqual(len(warn), 1, out.stdout)
        self.assertIn("slowest test_quick", warn[0])


def guard_env(card):
    env = {k: v for k, v in os.environ.items() if k not in ("JAM_KICKOFF", "JAM_ROLE")}
    if card:
        env.update(JAM_KICKOFF="1", JAM_ROLE="gameplay-dev")
    return env


class SessionGuard(unittest.TestCase):
    """Codex sessions have no deny list: tests/test__card_session_guard.py stops a full discover in a card session."""

    def unittest_(self, args, card):
        return subprocess.run([sys.executable, "-m", "unittest"] + args, cwd=ROOT, env=guard_env(card),
                              capture_output=True, text=True, timeout=120)

    def test_discover_in_a_card_session_stops_with_one_line(self):
        # -p keeps the run to the guard module: the guard fires on `discover` whatever the pattern matches
        p = self.unittest_(["discover", "-s", "tests", "-p", "test__card_session_guard.py"], card=True)
        self.assertEqual(p.returncode, 2, p.stderr)
        self.assertEqual(p.stderr.strip(), guard.MESSAGE)

    def test_a_targeted_module_still_runs_in_a_card_session(self):
        p = self.unittest_(["tests.test__card_session_guard"], card=True)
        self.assertEqual(p.returncode, 0, p.stderr)
        self.assertIn("OK", p.stderr)

    def test_discover_outside_a_card_session_is_unaffected(self):
        p = self.unittest_(["discover", "-s", "tests", "-p", "test__card_session_guard.py"], card=False)
        self.assertEqual(p.returncode, 0, p.stderr)

    def test_which_command_lines_are_a_full_discover(self):
        full = guard.is_full_discover
        self.assertTrue(full(["python -m unittest", "discover", "-s", "tests"]))
        self.assertTrue(full(["python -m unittest", "discover", "tests"]))
        self.assertTrue(full(["python -m unittest"]))
        self.assertTrue(full(["python -m unittest", "-v"]))
        self.assertFalse(full(["python -m unittest", "tests.test_check_card"]))
        self.assertFalse(full(["python -m unittest", "-k", "Mapping", "tests.test_affected_tests"]))
        self.assertFalse(full(["tools/affected_tests.py", "--measure"]))
        self.assertTrue(guard.in_card_session({"JAM_KICKOFF": "1", "JAM_ROLE": "qa-build"}))
        self.assertFalse(guard.in_card_session({"JAM_ROLE": "qa-build"}))    # a person's start_session

    def test_kickoff_denies_discover_to_claude_sessions(self):
        import kickoff
        for cmd in ("Bash(python3 -m unittest discover:*)", "Bash(python -m unittest discover:*)"):
            self.assertIn(cmd, kickoff.CLAUDE_DENY)


def read(rel):
    with open(os.path.join(ROOT, rel), encoding="utf-8") as fh:
        return fh.read()


class NoSessionRunsTheFullSuite(unittest.TestCase):
    """No role card, subagent file or kickoff prompt tells a card session to run `unittest discover`."""

    FULL = re.compile(r"unittest\s+discover")

    def test_role_cards_and_subagents_never_name_it(self):
        bad = [f for f in glob.glob(os.path.join(ROOT, "pipeline", "roles", "*.md")) +
               glob.glob(os.path.join(ROOT, ".claude", "agents", "*.md")) +
               glob.glob(os.path.join(ROOT, "prompts", "*.md")) if self.FULL.search(read(f))]
        self.assertEqual(bad, [])

    def test_kickoff_prompts_never_name_it(self):
        """Every string in kickoff.py outside CLAUDE_DENY: the prompts and task texts are built from them."""
        self.assertEqual(self.strings("tools/kickoff.py"), [])

    def test_start_session_prompt_never_names_it(self):
        self.assertEqual(self.strings("tools/start_session.py"), [])

    def strings(self, rel):
        tree = ast.parse(read(rel))
        deny = set()
        for node in ast.walk(tree):
            if isinstance(node, ast.Assign) and any(getattr(t, "id", "") == "CLAUDE_DENY" for t in node.targets):
                deny = {id(n) for n in ast.walk(node.value)}
        return [n.value for n in ast.walk(tree) if isinstance(n, ast.Constant) and isinstance(n.value, str)
                and id(n) not in deny and self.FULL.search(n.value)]

    def test_builder_and_reviewer_prompts_carry_the_rule(self):
        import inspect
        import kickoff
        for text in (kickoff.UNIT_TESTS, kickoff.BUILD_CHECKS):
            self.assertIn("tools/affected_tests.py --run", text)
        self.assertIn("tools/pipeline_check.py", kickoff.BUILD_CHECKS)
        self.assertIn("Done-when", kickoff.BUILD_CHECKS)
        self.assertIn("doubt", kickoff.REVIEW_CHECKS)
        self.assertIn("tools/pipeline_check.py", kickoff.REVIEW_CHECKS)
        self.assertIn("BUILD_CHECKS", inspect.getsource(kickoff.Kickoff.builder))
        self.assertIn("REVIEW_CHECKS", inspect.getsource(kickoff.Kickoff.reviewer))
        self.assertIn("UNIT_TESTS", inspect.getsource(kickoff.Kickoff.prompt))

    def test_session_docs_name_it_only_as_ci_work(self):
        """Docs a session reads may name the full suite only as CI's or the packaging owner's job, per cell."""
        docs = ["AGENTS.md", "CLAUDE.md", "README.md", "START_HERE.md", "pipeline/day0-cards.md",
                "pipeline/how-to-run-the-jam.md", ".github/ISSUE_TEMPLATE/task.yml", ".github/PULL_REQUEST_TEMPLATE.md"]
        docs += [os.path.relpath(f, ROOT) for f in glob.glob(os.path.join(ROOT, "pipeline", "checklists", "*.md"))
                 + glob.glob(os.path.join(ROOT, "pipeline", "templates", "*.md"))]
        bad = []
        for rel in docs:
            if not os.path.isfile(os.path.join(ROOT, rel)):
                continue
            for ln in read(rel).splitlines():
                for cell in re.split(r"<br>|(?<=[.;])\s", ln):   # a day0-cards row holds many Done-when lines
                    if self.FULL.search(cell) and "CI" not in cell and "packag" not in cell:
                        bad.append(f"{rel}: {cell.strip()[:100]}")
        self.assertEqual(bad, [])

    def test_check_card_fails_a_done_when_line_that_asks_for_the_full_suite(self):
        with open(os.path.join(HERE, "fixtures", "cards", "good_template.md"), encoding="utf-8") as fh:
            body = fh.read()
        bad = body.replace("  - [ ] tools/ue/build.sh exits 0 and the log is attached",
                           "  - [ ] `python3 -m unittest discover -s tests` exits 0", 1)
        self.assertNotEqual(bad, body)
        found = [m for k, m in check_card.problems(bad, ROOT) if k == "done"]
        self.assertTrue(any("full unit suite" in m for m in found), found)


if __name__ == "__main__":
    unittest.main()
