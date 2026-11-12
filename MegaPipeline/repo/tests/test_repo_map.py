"""Tests for docs/repo-map.md, tools/repo_map.py, the pipeline_check kind repomap, the kickoff prompt line and the
AGENTS.md read-order line. Each check is also broken on purpose to test the test."""
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
import kickoff  # noqa: E402
import pipeline_check  # noqa: E402
import repo_map  # noqa: E402

MAP = """# Repo map

## Pipeline folders (the installer ships these)
- `docs/`: docs. Producer.
- `pipeline/`: process docs.
- `pipeline/roles/`: role cards. Gate path.
- `tools/`: scripts. Gate path.

## Game folders (appear from Nov 12)
- `Source/`: game C++. Gameplay Dev.
- `UmbrellaElla.uproject`: the project file.

## Team and local folders
- `Assets/`: team art. Read-only.
- `Saved/`, `.pipeline/`: local. Never commit.
"""


class Repo:
    def __init__(self, repo_map_text=MAP):
        self.dir = tempfile.mkdtemp()
        subprocess.run(["git", "init", "-q"], cwd=self.dir, check=True)
        self.add("docs/jam-brief.md", "brief\n")
        self.add("pipeline/roles/producer.md", "# Role\n## Owns\nx\n## Inputs\nx\n## Outputs\nx\n## Done when\nx\n## Never\nx\n")
        self.add("tools/x.py", "print(1)\n")
        if repo_map_text is not None:
            self.add("docs/repo-map.md", repo_map_text)

    def add(self, rel, text="x\n"):
        full = os.path.join(self.dir, rel)
        os.makedirs(os.path.dirname(full), exist_ok=True)
        with open(full, "w", encoding="utf-8") as fh:
            fh.write(text)
        subprocess.run(["git", "add", "-f", rel], cwd=self.dir, check=True)

    def repomap(self):
        return [(w, why) for k, w, why in pipeline_check.check(self.dir) if k == "repomap"]

    def close(self):
        shutil.rmtree(self.dir, ignore_errors=True)


class RepoMapTool(unittest.TestCase):
    def setUp(self):
        self.r = Repo()
        self.addCleanup(self.r.close)

    def test_lists_only_folders_the_map_does_not_describe(self):
        for i in range(3):
            self.r.add(f"Sketchbook/page{i}.png")
        self.r.add("Sketchbook/notes.md")
        self.r.add("Assets/hero.png")          # described (team art)
        self.r.add("Source/Game/A.cpp")         # described (game folder)
        self.r.add("README.md")                 # a root file, not a folder
        found = repo_map.other_folders(self.r.dir)
        self.assertEqual(found, [("Sketchbook/", 4, [(".png", 3), (".md", 1)])])
        self.assertEqual(repo_map.describe(*found[0]), "Sketchbook/ (4 files: .png 3, .md 1)")

    def test_prompt_line(self):
        self.assertEqual(repo_map.prompt_line(self.r.dir), "", "no team folders: no line")
        self.r.add("Sketchbook/a.psd")
        self.r.add("zeta/b")
        self.assertEqual(repo_map.prompt_line(self.r.dir),
                         "Other folders in this repo (team files; read-only unless your card links them): "
                         "Sketchbook/ (1 file: .psd 1); zeta/ (1 file: (no ext) 1).")

    def test_untracked_folders_are_not_listed(self):
        os.makedirs(os.path.join(self.r.dir, "Loose"))
        with open(os.path.join(self.r.dir, "Loose", "a.txt"), "w") as fh:
            fh.write("x")
        self.assertEqual(repo_map.other_folders(self.r.dir), [])

    def test_no_map_no_line(self):
        r = Repo(repo_map_text=None)
        self.addCleanup(r.close)
        r.add("Sketchbook/a.png")
        self.assertEqual(repo_map.prompt_line(r.dir), "")
        self.assertEqual(repo_map.problems(r.dir), [])
        self.assertEqual(repo_map.main(["--root", r.dir]), 2)

    def test_entries_and_sections(self):
        ents = {p: checked for p, _, checked in repo_map.entries(MAP)}
        self.assertTrue(ents["pipeline/roles/"])
        self.assertFalse(ents["Source/"])
        self.assertFalse(ents[".pipeline/"], "a line may name two folders")


class RepoMapCheck(unittest.TestCase):
    def setUp(self):
        self.r = Repo()
        self.addCleanup(self.r.close)

    def test_complete_map_passes(self):
        self.assertEqual(self.r.repomap(), [])

    def test_missing_pipeline_folder_fails(self):
        self.r.add("pipeline/art/art-bible.md")
        self.r.add("evals/README.md")
        whys = [why for _, why in self.r.repomap()]
        self.assertEqual(len(whys), 2, whys)
        self.assertTrue(any("pipeline folder pipeline/art/ is not in the map" in w for w in whys), whys)
        self.assertTrue(any("pipeline folder evals/ is not in the map" in w for w in whys), whys)

    def test_listed_pipeline_path_that_does_not_exist_fails(self):
        self.r.add("docs/repo-map.md", MAP.replace("- `tools/`", "- `pipeline/gone/`: nothing.\n- `tools/`"))
        probs = self.r.repomap()
        self.assertEqual(len(probs), 1, probs)
        self.assertRegex(probs[0][0], r"^docs/repo-map\.md:\d+$")
        self.assertIn("pipeline/gone/ is listed under Pipeline folders but does not exist", probs[0][1])

    def test_wrong_case_fails(self):
        self.r.add("docs/repo-map.md", MAP.replace("`tools/`", "`Tools/`"))
        whys = [why for _, why in self.r.repomap()]
        self.assertTrue(any("Tools/ is listed" in w for w in whys), whys)
        self.assertTrue(any("pipeline folder tools/" in w for w in whys), whys)

    def test_game_and_team_folders_never_fail(self):
        # absent game folders are fine; present team folders are fine; game roots are not pipeline folders
        self.r.add("Sketchbook/a.png")
        self.r.add("Content/Maps/x.txt")
        self.r.add("scratch/probe.py")
        self.assertEqual(self.r.repomap(), [])

    def test_installed_repo_uses_the_install_record(self):
        self.r.add("MegaPipeline/repo/docs/jam-brief.md")
        self.r.add("Notes/agenda.md")   # the team's own folder, not in the record
        record = {"version": "1", "files": {"docs/jam-brief.md": "h", "tools/x.py": "h", "prompts/README.md": "h"}}
        self.r.add(".pipeline-installed.json", json.dumps(record))
        whys = [why for _, why in self.r.repomap()]
        self.assertEqual(len(whys), 1, whys)
        self.assertIn("pipeline folder prompts/", whys[0])

    def test_check_broken_on_purpose_fails(self):
        # Break the kind on purpose: with repo_map.problems silenced, a missing folder passes.
        self.r.add("pipeline/art/art-bible.md")
        saved = repo_map.problems
        repo_map.problems = lambda root, files=None: []
        try:
            self.assertEqual(self.r.repomap(), [])
        finally:
            repo_map.problems = saved
        self.assertNotEqual(self.r.repomap(), [])

    def test_this_repo_is_mapped(self):
        self.assertEqual(repo_map.problems(ROOT), [])
        # every tracked top-level folder of the source repo is in the map (a new pipeline top-level folder fails here)
        tops = {f.split("/")[0] for f in repo_map.tracked(ROOT) if "/" in f}
        self.assertTrue(tops <= repo_map.described_tops(repo_map.read_map(ROOT)), tops)
        self.assertTrue(set(repo_map.PIPELINE_TOPS) <= tops)

    def test_map_is_short_and_budgeted(self):
        self.assertIn("docs/repo-map.md", pipeline_check.BUDGETS)
        text = repo_map.read_map(ROOT)
        self.assertLessEqual(pipeline_check.words(text), pipeline_check.BUDGETS["docs/repo-map.md"])


class KickoffPromptLine(unittest.TestCase):
    def k(self):
        k = kickoff.Kickoff.__new__(kickoff.Kickoff)
        k.practice, k.prejam, k.tester_prompt = True, None, ""
        return k

    def test_prompt_names_team_folders(self):
        r = Repo()
        self.addCleanup(r.close)
        r.add("Sketchbook/a.png")
        saved = kickoff.ROOT
        kickoff.ROOT = r.dir
        try:
            text = self.k().prompt("story", "UE-0.25", "#1", "body", "task")
        finally:
            kickoff.ROOT = saved
        line = next(l for l in text.splitlines() if l.startswith("Other folders in this repo"))
        self.assertEqual(line, "Other folders in this repo (team files; read-only unless your card links them): "
                               "Sketchbook/ (1 file: .png 1).")
        self.assertLess(text.index(line), text.index("Card text"), "before the card text")

    def test_no_team_folders_no_line(self):
        r = Repo()
        self.addCleanup(r.close)
        saved = kickoff.ROOT
        kickoff.ROOT = r.dir
        try:
            text = self.k().prompt("story", "UE-0.25", "#1", "body", "task")
        finally:
            kickoff.ROOT = saved
        self.assertNotIn("Other folders in this repo", text)


class AgentsReadOrder(unittest.TestCase):
    def test_map_is_read_second(self):
        with open(os.path.join(ROOT, "AGENTS.md"), encoding="utf-8") as fh:
            agents = fh.read()
        sec = agents[agents.index("## 1. Read order"):agents.index("## 2.")]
        items = re.findall(r"^(\d)\. (.*)$", sec, re.M)
        self.assertEqual([n for n, _ in items], [str(i) for i in range(1, len(items) + 1)], "numbered in order")
        self.assertEqual(items[0][1], "This file.")
        self.assertTrue(items[1][1].startswith("`docs/repo-map.md`:"), items[1])
        self.assertIn("team files, read-only", items[1][1])
        role = next(i for i, (_, t) in enumerate(items) if t.startswith("Your role card"))
        self.assertGreater(role, 1, "the map comes before the role card")


if __name__ == "__main__":
    unittest.main()
