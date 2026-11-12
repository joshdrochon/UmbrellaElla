"""Tests for tools/pipeline_check.py. Each test plants one known problem in a throwaway
git repo and asserts the checker catches it (we break things on purpose to test the test).
The final test runs the checker on this repository itself, which must be clean."""
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
import pipeline_check  # noqa: E402

GOOD_ROLE = "# Role\n## Owns\nx\n## Inputs\nx\n## Outputs\nx\n## Done when\nx\n## Never\nx\n"


class Repo:
    def __init__(self):
        self.dir = tempfile.mkdtemp()
        subprocess.run(["git", "init", "-q"], cwd=self.dir, check=True)
        shutil.copy(os.path.join(ROOT, ".gitattributes"), self.dir)

    def add(self, path, content=b"x"):
        full = os.path.join(self.dir, path)
        os.makedirs(os.path.dirname(full) or self.dir, exist_ok=True)
        with open(full, "wb") as f:
            f.write(content if isinstance(content, bytes) else content.encode())
        subprocess.run(["git", "add", "-f", path], cwd=self.dir, check=True)

    def kinds(self):
        subprocess.run(["git", "add", "-f", ".gitattributes"], cwd=self.dir, check=True)
        return [k for k, _, _ in pipeline_check.check(self.dir)]

    def close(self):
        shutil.rmtree(self.dir, ignore_errors=True)


class PipelineCheckTests(unittest.TestCase):
    def setUp(self):
        self.r = Repo()

    def tearDown(self):
        self.r.close()

    def test_clean_repo_passes(self):
        self.r.add("AGENTS.md", "Umbrella Ella jam rules.\n")
        self.r.add("pipeline/roles/producer.md", GOOD_ROLE)
        self.r.add("Source/Ella/Ella.Build.cs", "// module\n")
        self.assertEqual(self.r.kinds(), [])

    def test_other_game_leak_caught(self):
        self.r.add("pipeline/roles/producer.md", GOOD_ROLE + "Balance the bar economy for Liquid Neon.\n")
        self.assertIn("leak", self.r.kinds())

    def test_unity_term_caught(self):
        self.r.add("AGENTS.md", "Put gameplay in a MonoBehaviour and split code with an asmdef.\n")
        self.assertEqual(self.r.kinds().count("leak"), 1)

    def test_audit_may_name_leak_terms(self):
        self.r.add("docs/audit.md", "The inherited docs mention Liquid Neon and MonoBehaviour.\n")
        self.assertEqual(self.r.kinds(), [])

    def test_build_output_caught(self):
        self.r.add("Intermediate/Build/foo.txt", "x")
        self.r.add("Source/Ella/Ella.generated.h", "x")
        self.assertEqual(self.r.kinds().count("forbidden"), 2)

    def test_binary_without_lfs_caught(self):
        # A .uasset path that .gitattributes does not cover is impossible, so test the
        # rule directly: remove the attributes file and commit a map.
        os.remove(os.path.join(self.r.dir, ".gitattributes"))
        self.r.add("Content/Maps/L_Level01.umap", b"\x00\x01")
        subprocess.run(["git", "rm", "-q", "--cached", "--ignore-unmatch", ".gitattributes"], cwd=self.r.dir, check=True)
        kinds = [k for k, _, _ in pipeline_check.check(self.r.dir)]
        self.assertIn("lfs", kinds)

    def test_raw_binary_bypassing_lfs_caught(self):
        # .gitattributes matches *.umap, but the file is added with the LFS filter switched off,
        # which is what happens on a machine without `git lfs install`.
        full = os.path.join(self.r.dir, "Content", "Maps", "L_Raw.umap")
        os.makedirs(os.path.dirname(full), exist_ok=True)
        with open(full, "wb") as f:
            f.write(b"\x00RAWMAP" * 100)
        subprocess.run(["git", "-c", "filter.lfs.clean=cat", "-c", "filter.lfs.smudge=cat", "-c", "filter.lfs.process=",
                        "-c", "filter.lfs.required=false", "add", "-f", "Content/Maps/L_Raw.umap"], cwd=self.r.dir, check=True)
        subprocess.run(["git", "add", "-f", ".gitattributes"], cwd=self.r.dir, check=True)
        problems = pipeline_check.check(self.r.dir)
        self.assertTrue(any(k == "lfs" and "raw binary" in why for k, _, why in problems), problems)

    def test_large_text_file_caught(self):
        self.r.add("docs/huge.md", "word " * 500000)
        self.assertIn("size", self.r.kinds())

    def test_agents_md_budget_caught(self):
        self.r.add("AGENTS.md", "word " * 2000)
        self.assertIn("budget", self.r.kinds())

    def test_brief_fill_in_tables_do_not_count(self):
        """Dry run A H2: card 0.0's People / Team hours / Clock fill never trips the brief budget; prose still does."""
        prose = "# Brief\n" + "word " * 1100 + "\n"
        rows = "".join(f"| Seat {i} | Name {i} long text here | yes | BLOCKER |\n" for i in range(40))
        self.r.add("docs/jam-brief.md", prose + "## People (fill in; card 0.0)\n| Seat | Name | Confirmed | Needed |\n"
                   + rows + "## Team hours\n" + rows)
        self.assertNotIn("budget", self.r.kinds())
        self.r.add("docs/jam-brief.md", prose + "## Hard limits\n" + rows)   # broken on purpose: not a fill-in table
        self.assertIn("budget", self.r.kinds())
        self.r.add("docs/jam-brief.md", prose + "## People\n" + "more prose words " * 50 + "\n")
        self.assertIn("budget", self.r.kinds(), "prose under a fill-in heading still counts")

    def test_role_missing_section_caught(self):
        self.r.add("pipeline/roles/qa.md", GOOD_ROLE.replace("## Never\nx\n", ""))
        self.assertIn("roles", self.r.kinds())

    # Source/ and Config/ hygiene
    CLEAN_CPP = ("// TODO(UE-12): split once D-new-port-4 is decided\n// TODO(D-new-port-4) enum vs bools\n"
                 "#pragma warning(disable: 4100) // D-new-port-99 engine header noise\nint x = 0;\n")

    def test_clean_source_and_config_pass(self):
        self.r.add("Source/UmbrellaElla/Private/A.cpp", self.CLEAN_CPP)
        self.r.add("Config/DefaultGame.ini", "[/Script/UmbrellaElla.UmbrellaTuning]\nFallSpeed=300\n")
        self.assertEqual(self.r.kinds(), [])

    def test_bare_todo_caught(self):
        self.r.add("Source/UmbrellaElla/Private/A.cpp", "// TODO fix later\n")
        self.r.add("Config/DefaultEngine.ini", "; TODO: channels\n")
        self.assertEqual(self.r.kinds().count("hygiene"), 2)

    def test_todo_with_bad_id_caught(self):
        self.r.add("Source/UmbrellaElla/Private/A.cpp", "// TODO(rick) fix later\n")
        self.assertEqual(self.r.kinds(), ["hygiene"])

    def test_warning_pragma_without_decision_caught(self):
        self.r.add("Source/UmbrellaElla/Private/A.cpp", "#pragma warning(disable: 4100)\n")
        self.r.add("Source/UmbrellaElla/Private/B.cpp", "PRAGMA_DISABLE_DEPRECATION_WARNINGS\n")
        self.assertEqual(self.r.kinds().count("hygiene"), 2)

    def test_role_line_in_source_caught(self):
        self.r.add("Source/UmbrellaElla/Private/A.cpp", "// ROLE: Gameplay Dev | session 2026-11-06\n")
        self.assertEqual(self.r.kinds(), ["hygiene"])

    def test_hygiene_ignores_other_folders(self):
        self.r.add("docs/notes.md", "TODO fix later\nROLE: Producer\n")
        self.assertEqual(self.r.kinds(), [])

    def test_placeholder_is_a_note_during_jam_and_a_problem_on_release(self):
        self.r.add("Source/UmbrellaElla/Private/A.cpp", 'auto P = TEXT("/Game/Art/T_Ella_PH");\n')
        self.r.add("Content/UmbrellaElla/Art/T_Spikes_PH.uasset", b"x")
        subprocess.run(["git", "add", "-f", ".gitattributes"], cwd=self.r.dir, check=True)
        notes = []
        self.assertEqual(pipeline_check.check(self.r.dir, notes=notes), [])
        self.assertEqual([k for k, _, _ in notes], ["placeholder", "placeholder"])
        kinds = [k for k, _, _ in pipeline_check.check(self.r.dir, release=True)]
        self.assertEqual(kinds.count("placeholder"), 2)

    def test_lfs_bytes_sums_pointer_sizes(self):
        ptr = "version https://git-lfs.github.com/spec/v1\noid sha256:%s\nsize %d\n"
        for name, size in (("a", 1000), ("b", 2500)):
            full = os.path.join(self.r.dir, "Content", name + ".uasset")
            os.makedirs(os.path.dirname(full), exist_ok=True)
            with open(full, "w", newline="\n") as f:   # a real pointer has LF line ends, on Windows too
                f.write(ptr % (name * 64, size))
            # store the pointer text as-is (no LFS filter), which is what a real LFS commit stores
            subprocess.run(["git", "-c", "filter.lfs.clean=cat", "-c", "filter.lfs.process=", "-c", "filter.lfs.required=false",
                            "add", "-f", "Content/%s.uasset" % name], cwd=self.r.dir, check=True)
        subprocess.run(["git", "add", "-f", ".gitattributes"], cwd=self.r.dir, check=True)
        self.assertEqual(pipeline_check.lfs_bytes(self.r.dir), (3500, 2))

    def test_this_repository_is_clean(self):
        problems = pipeline_check.check(ROOT)
        self.assertEqual(problems, [], "\n".join(f"[{k}] {w}: {y}" for k, w, y in problems))


class InstalledRepoTests(unittest.TestCase):
    """A repo the pipeline was installed into keeps the shipped package (MegaPipeline/repo/, MegaPipeline/tests/,
    the installer) beside the root copy. That copy is checked where it is made, so it is skipped here."""

    SHIPPED = {
        "MegaPipeline/repo/docs/audit.md": "The old game was Liquid Neon.\n",
        "MegaPipeline/repo/tools/x.py": "LOG = '~/" + "Desktop/notes'\n",
        "MegaPipeline/tests/test_install.py": "# see D-new-zz\n",
        "MegaPipeline/install.py": "# MonoBehaviour\n",
        "MegaPipeline/manifest.json": "{\"note\": \"Liquid Neon\"}\n",
    }

    def setUp(self):
        self.r = Repo()
        self.r.add("docs/decisions.md", "# Decisions\n")
        for rel, text in self.SHIPPED.items():
            self.r.add(rel, text)

    def tearDown(self):
        self.r.close()

    def test_install_record_skips_shipped_copy(self):
        self.r.add(".pipeline-installed.json", "{}\n")
        self.assertEqual(self.r.kinds(), [])

    def test_repo_folder_alone_marks_installed(self):
        self.assertTrue(pipeline_check.installed(self.r.dir))
        self.assertEqual(self.r.kinds(), [])

    def test_root_files_still_checked_when_installed(self):
        self.r.add(".pipeline-installed.json", "{}\n")
        self.r.add("docs/notes.md", "Balance the bar for Liquid Neon.\n")
        self.assertEqual(self.r.kinds(), ["leak"])

    def test_skip_broken_on_purpose_fails(self):
        # Break the skip on purpose: with it off, the shipped copy is checked and fails like the installed repo did.
        self.r.add(".pipeline-installed.json", "{}\n")
        saved = pipeline_check.shipped
        pipeline_check.shipped = lambda rel: False
        try:
            kinds = self.r.kinds()
        finally:
            pipeline_check.shipped = saved
        for k in ("leak", "private", "consistency"):
            self.assertIn(k, kinds)

    def test_source_repo_unchanged(self):
        # No install record and no MegaPipeline/repo/: a stray file under MegaPipeline/ is still checked.
        shutil.rmtree(os.path.join(self.r.dir, "MegaPipeline", "repo"))
        subprocess.run(["git", "add", "-A"], cwd=self.r.dir, check=True)
        self.assertFalse(pipeline_check.installed(self.r.dir))
        kinds = self.r.kinds()
        self.assertIn("leak", kinds)
        self.assertIn("consistency", kinds)

    def test_shipped_full_ci_marker_fails(self):
        # A game repo installed from a copy that carries .pipeline-ci-full would run the ~100-min suites on every PR.
        self.r.add(".pipeline-installed.json", "{}\n")
        self.r.add("MegaPipeline/repo/.pipeline-ci-full", "full\n")
        self.assertEqual(self.r.kinds(), ["ciprofile"])

    def test_root_full_ci_marker_is_allowed_when_installed(self):
        # The pipeline test repo is installed and keeps the marker at its root.
        self.r.add(".pipeline-installed.json", "{}\n")
        self.r.add(".pipeline-ci-full", "full\n")
        self.assertEqual(self.r.kinds(), [])

    def test_lists_match_exporter(self):
        import export_package as ep
        self.assertEqual(pipeline_check.INSTALLED, ep.INSTALLED)
        self.assertEqual(pipeline_check.SHIPPED_DIRS, tuple(ep.PKG + "/" + d for d in ep.SHIPPED_DIRS))
        self.assertEqual(pipeline_check.SHIPPED_FILES, {ep.PKG + "/" + f for f in ep.SHIPPED_FILES})


class PrivateReferenceTests(unittest.TestCase):
    """The private-name check matches hashed names, so these tests use made-up names and never spell
    out the real ones. One test proves the shipped hash list is wired in."""
    FAKE = {pipeline_check._h("zorblaxquint"): None, pipeline_check._h("wobbletool"): None}

    def setUp(self):
        self.r = Repo()

    def tearDown(self):
        self.r.close()

    def hit(self, line, allow=None):
        return pipeline_check.private_hit(line, hashes=set(self.FAKE), allow_prev=allow or {})

    def test_single_word_spaced_and_punctuated_forms_fail(self):
        for line in ["the Zorblaxquint bar", "zorblax quint", "Zorblax-Quint repo", "wobble tool notes"]:
            with self.subTest(line=line):
                self.assertIsNotNone(self.hit(line))

    def test_allowed_previous_word_passes(self):
        allow = {pipeline_check._h("zorblaxquint"): "unreal"}
        self.assertIsNone(self.hit("Run the Unreal Zorblaxquint tests", allow))
        self.assertIsNotNone(self.hit("the Zorblaxquint bar", allow))

    def test_clean_line_passes(self):
        self.assertIsNone(self.hit("Planted-bug evals and blind comparison"))

    def test_personal_paths_fail_and_shared_engine_path_passes(self):
        for line in ["~/Desk" + "top/x", "/Users/" + "someone/x", "C:\\" + "Users\\someone"]:
            with self.subTest(line=line):
                self.assertIsNotNone(pipeline_check.private_hit(line))
        self.assertIsNone(pipeline_check.private_hit("UE lives in /Users/Shared/Epic Games"))

    def test_shipped_list_is_wired_into_repo_check(self):
        self.assertEqual(len(pipeline_check.PRIVATE_HASHES), 15)
        self.r.add("docs/p.md", "Notes: /Users/" + "someone/x\n")
        self.assertIn("private", self.r.kinds())

    def test_new_file_not_yet_added_is_scanned(self):
        with open(os.path.join(self.r.dir, "notes.md"), "w") as f:
            f.write("see ~/Desk" + "top/notes\n")
        self.assertIn("private", self.r.kinds())

    def test_private_terms_apply_to_eval_cases_and_fixtures(self):
        self.r.add("evals/reviewer/cases/01/task.md", "~/Desk" + "top/x\n")
        self.r.add("tests/fixtures/x.csv", "a,/Users/" + "josh/x\n")
        self.assertEqual(self.r.kinds().count("private"), 2)


DEC = """| ID | Decision needed | Default | Owner | Status |
|---|---|---|---|---|
| D1 | Attack form | Auto-fire | Game design owner | open |
| D-new-x | Zip name | Jam form | Rich | open |

| ID | Rule |
|---|---|
| D2 | Settled rule |
"""
DAY0_TEXT = """| # | Card | Owner | Reviewer | Lane | After | Done when |
|---|---|---|---|---|---|---|
| 0.0 | People | Producer / Rick (sign-off: submission) | Dev Lead | `docs/jam-brief.md` | – | HUMAN submission: x |
| 0.3 | Skeleton | Technical Director | Dev Lead | `tools/new_tool.py` | 0.0 | x |
| 0.4a | Inventory | Technical Director | Dev Lead | `pipeline/unreal-rules.md` | 0.3 | x |
"""
BRIEF_TEXT = """# Brief
## People
| Role | Person | Confirmed? | Day-1 blocker |
|---|---|---|---|
| Game design owner | Rich | no | BLOCKER |
| Producer / time keeper, human | TBD | no | BLOCKER |
## Other
"""
AGENTS_TEXT = """# A
## 3. Roles
| Role | Use it for | Card |
|---|---|---|
| Producer | Cards | x |
| Technical Director | Skeleton | x |
| Dev Lead | Review | x |
## 4. Flow
"""


class ConsistencyTests(unittest.TestCase):
    """The cross-doc gate. Each test breaks one reference on purpose and expects one problem."""

    def setUp(self):
        self.dir = tempfile.mkdtemp()
        self.files = {"docs/decisions.md": DEC, "pipeline/day0-cards.md": DAY0_TEXT, "docs/jam-brief.md": BRIEF_TEXT,
                      "AGENTS.md": AGENTS_TEXT, "pipeline/unreal-rules.md": "rules\n",
                      "docs/notes.md": "See D1, D2 and D-new-x. Card 0.3 and card 0.4a. Read `pipeline/unreal-rules.md`."
                                       " Card 0.3 builds `tools/new_tool.py`. Day-0 cards 0.0, 0.3 and 0.4a.\n"}

    def tearDown(self):
        shutil.rmtree(self.dir, ignore_errors=True)

    def run_gate(self):
        for rel, text in self.files.items():
            full = os.path.join(self.dir, rel)
            os.makedirs(os.path.dirname(full) or self.dir, exist_ok=True)
            with open(full, "w") as f:
                f.write(text)
        return [why for _, _, why in pipeline_check.consistency(self.dir, sorted(self.files))]

    def test_clean_docs_pass(self):
        self.assertEqual(self.run_gate(), [])

    def test_person_owned_day0_card_fails(self):
        # broken on purpose: agents own every card; a person's step needs its HUMAN <kind>: tag
        self.files["pipeline/day0-cards.md"] = DAY0_TEXT.replace("| Producer / Rick (sign-off: submission) |", "| Human |")
        got = self.run_gate()
        self.assertTrue(any("0.0: owner 'Human' is not an agent role" in g for g in got), got)
        self.files["pipeline/day0-cards.md"] = DAY0_TEXT.replace("| 0.3 | x |", "| 0.3 | the TD human writes it |")
        got = self.run_gate()
        self.assertTrue(any(g.startswith("0.4a: a person acts") for g in got), got)

    def test_missing_decision_row_fails(self):
        self.files["docs/notes.md"] += "Build the D-new-pool default.\n"
        self.assertEqual(self.run_gate(), ["decision D-new-pool has no row in docs/decisions.md"])

    def test_gdd_b_dec_ids_need_a_row(self):
        # GDD B §13 decision IDs (DEC-nn) are decision references too; a cited DEC row must exist.
        self.files["docs/notes.md"] += "Interim behavior: DEC-06 and DEC-11.\n"
        self.files["docs/decisions.md"] += "| DEC-06 | completion rule | timer fixture | none | Rick | Nov 12 | open |\n"
        self.assertEqual(self.run_gate(), ["decision DEC-11 has no row in docs/decisions.md"])

    def test_missing_card_fails(self):
        self.files["docs/notes.md"] += "Card 0.17 builds the logger. 0.4c dumps art.\n"
        self.assertEqual(sorted(self.run_gate()), ["card 0.17 is not in pipeline/day0-cards.md",
                                                   "card 0.4c is not in pipeline/day0-cards.md"])

    def test_plain_numbers_are_not_cards(self):
        self.files["docs/notes.md"] += "A 0.4 s telegraph at 0.5x speed; paper_texture 0.38.\n"
        self.assertEqual(self.run_gate(), [])

    def test_missing_path_fails(self):
        self.files["docs/notes.md"] += "Run `tools/design_check.py`. Patterns: `tools/ue/test.*`, `prompts/log/D-<host>.md`.\n"
        self.assertEqual(self.run_gate(), ["path tools/design_check.py does not exist"])

    def test_wrong_case_path_fails_on_every_os(self):
        self.files["docs/notes.md"] += "Read `pipeline/Unreal-Rules.md`.\n"
        self.assertEqual(self.run_gate(), ["path pipeline/Unreal-Rules.md does not exist"])

    def test_exact_case_path_passes(self):
        self.files["docs/notes.md"] += "Read `pipeline/unreal-rules.md` again.\n"
        self.assertEqual(self.run_gate(), [])

    def test_bad_owner_fails(self):
        self.files["docs/decisions.md"] = DEC.replace("| Rich |", "| QA and Build owner |")
        self.assertEqual(len(self.run_gate()), 1)
        self.assertIn("owner 'QA and Build owner'", self.run_gate()[0])

    def test_agents_role_is_a_valid_owner(self):
        self.files["docs/decisions.md"] = DEC.replace("| Rich |", "| Producer (human) |")
        self.assertEqual(self.run_gate(), [])

    def test_after_cycle_fails(self):
        self.files["pipeline/day0-cards.md"] = DAY0_TEXT.replace("| `docs/jam-brief.md` | – |", "| `docs/jam-brief.md` | 0.4a |")
        gate = self.run_gate()
        self.assertEqual(len(gate), 1)
        self.assertIn("cycle", gate[0])

    def test_after_naming_a_missing_card_fails(self):
        self.files["pipeline/day0-cards.md"] += "| 0.5 | Harness | Producer | Dev Lead | `x` | 0.3, 0.9 | x |\n"
        self.files["docs/notes.md"] += "Card 0.5.\n"
        self.assertEqual(self.run_gate(), ["card 0.9 is not in pipeline/day0-cards.md"])


if __name__ == "__main__":
    unittest.main()


class WorkflowYaml(unittest.TestCase):
    """GitHub rejects a workflow whose YAML does not parse, and then runs no check at all (the story branch's step name
    `Story text (Story role): bible, ...` did that). Python has no YAML parser in the stdlib, so this checks the trap
    that bit: a plain scalar after `name:`/`run:` that holds ': ' or ' #' must be quoted."""

    PLAIN = re.compile(r"^\s*(?:-\s+)?(name|run|if):\s+(?P<v>[^\"'|>\s].*)$")

    def problems(self, text):
        out = []
        for i, ln in enumerate(text.splitlines(), 1):
            m = self.PLAIN.match(ln)
            if m and (": " in m.group("v") or " #" in m.group("v")):
                out.append(f"line {i}: {ln.strip()[:80]}")
        return out

    def test_every_workflow_and_issue_form(self):
        for d in (".github/workflows", ".github/ISSUE_TEMPLATE"):
            for f in sorted(os.listdir(os.path.join(ROOT, d))):
                if f.endswith((".yml", ".yaml")):
                    with self.subTest(f=f), open(os.path.join(ROOT, d, f), encoding="utf-8") as fh:
                        self.assertEqual(self.problems(fh.read()), [])

    def test_broken_on_purpose(self):
        self.assertTrue(self.problems("      - name: Story text (Story role): bible\n"))
        self.assertEqual(self.problems('      - name: "Story text (Story role): bible"\n'), [])


class CiProfile(unittest.TestCase):
    """CI profile (pipeline/agent-ops/README.md): .pipeline-ci-full turns on the long pipeline suites. The game checks,
    the art ship gate and check_pr run in both profiles."""

    GATE = "if: hashFiles('.pipeline-ci-full') != ''"

    @classmethod
    def setUpClass(cls):
        with open(os.path.join(ROOT, ".github", "workflows", "pipeline-checks.yml"), encoding="utf-8") as fh:
            wf = fh.read()
        parts = re.split(r"\n  ([a-z]+):\n", "\n" + wf.split("\njobs:\n", 1)[1])
        cls.jobs = dict(zip(parts[1::2], parts[2::2]))
        cls.steps = {}
        for name, block in re.findall(r"- name: (.*?)\n((?:        .*\n|\n)*?)(?=      - |\Z)", cls.jobs["checks"] + "\n"):
            cls.steps[name.strip().strip('"')] = block

    def step(self, needle):
        hits = [b for b in self.steps.values() if needle in b]
        self.assertEqual(len(hits), 1, needle)
        return hits[0]

    def test_source_repo_has_the_marker(self):
        self.assertTrue(os.path.isfile(os.path.join(ROOT, pipeline_check.CI_FULL)))

    def test_profile_job_reads_the_marker(self):
        self.assertIn("if [ -f .pipeline-ci-full ]; then full=true; else full=false; fi", self.jobs["profile"])
        self.assertIn("full: ${{ steps.marker.outputs.full }}", self.jobs["profile"])

    def test_windows_job_runs_only_in_the_full_profile(self):
        w = self.jobs["windows"]
        self.assertIn("    needs: profile\n", w)
        self.assertRegex(w, r"\n    if: .*needs\.profile\.outputs\.full == 'true'")

    def test_unit_tests_and_their_lfs_pulls_are_gated(self):
        for needle in ("python3 -m unittest discover", "git lfs pull --include='pipeline/art/reference/*.png'",
                       "git lfs pull --include='tests/fixtures/**,docs/rules/*.pdf'"):
            with self.subTest(step=needle):
                self.assertIn(self.GATE, self.step(needle))

    def test_game_checks_ship_gate_and_check_pr_always_run(self):
        always = ("tools/pipeline_check.py", "tools/manifest_check.py", "tools/module_check.py", "tools/sprite_check.py",
                  "tools/hitbox_check.py", "tools/encounter_check.py", "tools/ui_check.py ci", "tools/feel_check.py",
                  "tools/bake_preset.py", "submission_check.py wiring", "submission_check.py rules",
                  "tools/editor_mcp.py check", "tools/secrets_check.py", "audio_check.py --list", "story_check.py",
                  "audio_check.py --scan", "audio_style_check.py", "tools/check_pr.py", "tools/check_card.py",
                  "git lfs ls-files", "git lfs pull --include='pipeline/art/reference/**,Assets/**,Mockups/**,docs/gdd/**'",
                  "actions/cache@v4")
        for needle in always:
            with self.subTest(step=needle):
                self.assertNotIn("hashFiles", self.step(needle))
        self.assertNotIn("needs.profile", self.jobs["checks"].split("steps:", 1)[1])
        self.assertRegex(self.jobs["checks"], r"timeout-minutes: \$\{\{ needs\.profile\.outputs\.full == 'true' && \d+ \|\| 20 \}\}")

    def test_every_job_has_a_timeout(self):
        for name, block in self.jobs.items():
            with self.subTest(job=name):
                self.assertRegex(block, r"(?m)^    timeout-minutes: ")


class DirectBuildMode(unittest.TestCase):
    """12 Nov: the team builds directly (a build lead merges area/* into main after tools/build/gate.sh and pushes).
    While docs/build/MODE says `direct` (or there is no MODE file and HANDOFF.md exists) CI skips the card-only jobs and
    the main-red auto-revert, keeps the fast checks, and never runs the Unreal build on a GitHub runner."""

    FAST = ("tools/pipeline_check.py", "tools/manifest_check.py", "tools/module_check.py", "tools/encounter_check.py",
            "tools/feel_check.py", "submission_check.py wiring", "submission_check.py rules", "tools/editor_mcp.py check",
            "tools/secrets_check.py", "audio_check.py --list", "story_check.py")
    CARD_ONLY = ("tools/ui_check.py ci", "tools/bake_preset.py", "audio_check.py --scan", "audio_style_check.py",
                 "tools/check_pr.py", "tools/check_card.py", "git lfs ls-files", "actions/cache@v4",
                 "git lfs pull --include='pipeline/art/reference/**,Assets/**,Mockups/**,docs/gdd/**'")

    @classmethod
    def setUpClass(cls):
        cls.wf = {}
        for f in ("pipeline-checks.yml", "main-red.yml", "blocked-report.yml"):
            with open(os.path.join(ROOT, ".github", "workflows", f), encoding="utf-8") as fh:
                cls.wf[f] = fh.read()
        parts = re.split(r"\n  ([a-z]+):\n", "\n" + cls.wf["pipeline-checks.yml"].split("\njobs:\n", 1)[1])
        cls.jobs = dict(zip(parts[1::2], parts[2::2]))
        cls.steps = {}
        for name, block in re.findall(r"- name: (.*?)\n((?:        .*\n|\n)*?)(?=      - |\Z)", cls.jobs["checks"] + "\n"):
            cls.steps[name.strip().strip('"')] = block

    def step(self, needle):
        hits = [b for b in self.steps.values() if needle in b]
        self.assertEqual(len(hits), 1, needle)
        return hits[0]

    def mode_of(self, files):
        """Run the workflows' mode snippet in a folder holding `files` ({path: text})."""
        line = next(l.strip() for l in self.jobs["profile"].splitlines() if "docs/build/MODE" in l and "then" in l)
        for wf in ("main-red.yml", "blocked-report.yml"):
            self.assertIn(line, self.wf[wf], f"{wf} reads the mode the same way")
        d = tempfile.mkdtemp()
        try:
            for rel, text in files.items():
                os.makedirs(os.path.dirname(os.path.join(d, rel)) or d, exist_ok=True)
                with open(os.path.join(d, rel), "w") as fh:
                    fh.write(text)
            return subprocess.run(["bash", "-c", line + '\necho "$mode"'], cwd=d, capture_output=True, text=True,
                                  check=True).stdout.strip()
        finally:
            shutil.rmtree(d, ignore_errors=True)

    def test_mode_file_then_handoff_fallback(self):
        self.assertEqual(self.mode_of({}), "cards", "the pipeline source repo: no MODE, no HANDOFF.md")
        self.assertEqual(self.mode_of({"HANDOFF.md": "x\n"}), "direct")
        self.assertEqual(self.mode_of({"docs/build/MODE": "direct\n"}), "direct")
        self.assertEqual(self.mode_of({"docs/build/MODE": "cards\n", "HANDOFF.md": "x\n"}), "cards")

    def test_profile_job_exports_the_mode_for_every_event(self):
        self.assertIn("direct: ${{ steps.mode.outputs.direct }}", self.jobs["profile"])
        self.assertNotIn("    if:", self.jobs["profile"].split("steps:", 1)[0])
        self.assertIn("DIRECT: ${{ needs.profile.outputs.direct }}", self.jobs["checks"].split("steps:", 1)[0])

    def test_card_jobs_and_auto_revert_skip_in_direct_mode(self):
        self.assertRegex(self.jobs["card"], r"\n    if: .*needs\.profile\.outputs\.direct != 'true'")
        self.assertRegex(self.jobs["windows"], r"\n    if: .*needs\.profile\.outputs\.direct != 'true'")
        self.assertRegex(self.wf["main-red.yml"], r"\n  revert-first:\n    needs: mode\n    if: needs\.mode\.outputs\.direct != 'true'\n")
        self.assertRegex(self.wf["blocked-report.yml"], r"\n  blocked:\n    needs: mode\n    if: .*needs\.mode\.outputs\.direct != 'true'\n")

    def test_fast_checks_run_and_card_only_steps_skip(self):
        for needle in self.FAST:
            with self.subTest(fast=needle):
                self.assertNotIn("DIRECT", self.step(needle))
        for needle in self.CARD_ONLY:
            with self.subTest(card_only=needle):
                self.assertIn("env.DIRECT != 'true'", self.step(needle))
        self.assertIn("env.DIRECT == 'true'", self.step("submission_check.py prejam"))

    def test_no_unreal_build_on_github_runners(self):
        for f, text in self.wf.items():
            with self.subTest(wf=f):
                code = "\n".join(l for l in text.splitlines() if not l.strip().startswith("#"))
                self.assertNotRegex(code, r"tools[/\\]ue[/\\](build|test|package)|RunUAT|UnrealEditor")


class DirectBuildChecks(unittest.TestCase):
    """pipeline_check in the direct build: the game's own play-mode type is not a Unity leak in C++, and a path in an
    area card's File lane is a planned output of that area branch (each test breaks one thing on purpose)."""

    def test_playmode_in_game_code_passes_and_in_docs_fails(self):
        r = Repo()
        try:
            r.add("Source/Ella/Ella.h", "EUmbrellaPlayMode PlayMode = EUmbrellaPlayMode::StartGame;\n")
            self.assertEqual(r.kinds(), [])
            r.add("AGENTS.md", "Run the tests in PlayMode.\n")
            self.assertEqual(r.kinds().count("leak"), 1)
        finally:
            r.close()

    def test_area_file_lane_paths_are_planned(self):
        d = tempfile.mkdtemp()
        try:
            files = {"docs/build/areas/flow.md": "# flow\n## File lane (only these)\n- `docs/build/areas/flow-status.md`\n"
                                                 "## GDD sections\n2\n",
                     "HANDOFF.md": "Status: `docs/build/areas/flow-status.md`. Missing: `docs/build/areas/x-status.md`.\n"}
            for rel, text in files.items():
                os.makedirs(os.path.dirname(os.path.join(d, rel)) or d, exist_ok=True)
                with open(os.path.join(d, rel), "w") as fh:
                    fh.write(text)
            got = [why for _, _, why in pipeline_check.consistency(d, sorted(files))]
            self.assertEqual(got, ["path docs/build/areas/x-status.md does not exist"])
        finally:
            shutil.rmtree(d, ignore_errors=True)
