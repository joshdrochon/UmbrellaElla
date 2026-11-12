"""MegaPipeline/install.py: fresh install, update over an older install, user files left alone, dry run by default.
Run: python3 -m unittest discover -s MegaPipeline/tests"""
import os
import shutil
import subprocess
import sys
import tempfile
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
MP = os.path.dirname(HERE)


def write(path, text):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as fh:
        fh.write(text)


def read(path):
    with open(path, encoding="utf-8") as fh:
        return fh.read()


class Install(unittest.TestCase):
    def setUp(self):
        self.root = tempfile.mkdtemp(prefix="mp-")
        self.addCleanup(shutil.rmtree, self.root, True)
        self.mp = os.path.join(self.root, "MegaPipeline")
        os.makedirs(self.mp)
        for f in ("install.py", "install.sh"):
            shutil.copy(os.path.join(MP, f), self.mp)
        self.git("init", "-q", "-b", "main")
        self.git("config", "user.email", "t@t")
        self.git("config", "user.name", "t")
        self.release({"AGENTS.md": "agents v1\n", "tools/a.py": "a v1\n", "tools/gone.py": "gone v1\n",
                      "docs/jam-brief.md": "brief v1\n", "pipeline/VERSION": "1.0.0\n",
                      "docs/gdd/GDD-1.3.md": "gdd v1\n"})

    def git(self, *args):
        subprocess.run(["git", *args], cwd=self.root, check=True, capture_output=True)

    def release(self, files):
        repo = os.path.join(self.mp, "repo")
        shutil.rmtree(repo, ignore_errors=True)
        for rel, text in files.items():
            write(os.path.join(repo, rel), text)
        self.git("add", "-A", "MegaPipeline")
        self.git("commit", "-q", "-m", "release")
        self.run_tool("--make-manifest")
        self.git("add", "-A", "MegaPipeline")
        self.git("commit", "-q", "-m", "manifest")

    def run_tool(self, *args):
        p = subprocess.run(["bash", os.path.join(self.mp, "install.sh"), *args], cwd=self.root, capture_output=True,
                           text=True)
        return p.returncode, p.stdout + p.stderr

    def v2(self):
        self.release({"AGENTS.md": "agents v2\n", "tools/a.py": "a v2\n", "tools/new.py": "new v2\n",
                      "docs/jam-brief.md": "brief v2\n", "pipeline/VERSION": "2.0.0\n",
                      "docs/gdd/GDD-1.3.md": "gdd v2\n"})

    def test_fresh_install_copies_and_records_the_version(self):
        rc, out = self.run_tool()
        self.assertEqual(rc, 0, out)
        self.assertIn("dry run: would copy 6 file(s)", out)
        self.assertFalse(os.path.exists(os.path.join(self.root, "tools", "a.py")), "dry run writes nothing")
        rc, out = self.run_tool("--apply")
        self.assertEqual(rc, 0, out)
        self.assertEqual(read(os.path.join(self.root, "tools", "a.py")), "a v1\n")
        self.assertIn('"version": "1.0.0+', read(os.path.join(self.root, ".pipeline-installed.json")))

    def test_update_over_an_older_install_without_a_record(self):
        # an older install: the files were copied by hand, no .pipeline-installed.json
        for rel in ("AGENTS.md", "tools/a.py", "tools/gone.py", "docs/jam-brief.md", "pipeline/VERSION"):
            shutil.copy(os.path.join(self.mp, "repo", rel), os.path.join(self.root, rel)) if os.path.isdir(
                os.path.dirname(os.path.join(self.root, rel))) else (os.makedirs(os.path.dirname(
                    os.path.join(self.root, rel))), shutil.copy(os.path.join(self.mp, "repo", rel), os.path.join(self.root, rel)))
        self.v2()
        rc, out = self.run_tool("--update")
        self.assertEqual(rc, 0, out)
        self.assertIn("dry run: would update from 1.0.0 to 2.0.0+", out)
        self.assertEqual(read(os.path.join(self.root, "tools", "a.py")), "a v1\n", "dry run by default")
        rc, out = self.run_tool("--update", "--apply")
        self.assertEqual(rc, 0, out)
        self.assertIn("REPLACE  tools/a.py", out)
        self.assertIn("ADD      tools/new.py", out)
        self.assertIn("REMOVE   tools/gone.py", out)
        self.assertIn("updated from 1.0.0 to 2.0.0+", out.strip().splitlines()[-1])
        self.assertEqual(read(os.path.join(self.root, "tools", "a.py")), "a v2\n")
        self.assertFalse(os.path.exists(os.path.join(self.root, "tools", "gone.py")))
        backups = os.path.join(self.root, "Saved", "pipeline-backup")
        stamp = os.listdir(backups)[0]
        self.assertEqual(read(os.path.join(backups, stamp, "tools", "a.py")), "a v1\n")
        self.assertEqual(read(os.path.join(backups, stamp, "tools", "gone.py")), "gone v1\n")
        # a second update has nothing to do
        rc, out = self.run_tool("--update")
        self.assertIn("0 replaced, 0 added, 0 removed", out)

    def test_windows_line_endings_still_count_as_untouched(self):
        # a Windows checkout turns LF into CRLF; that is not a team edit, so update replaces the file
        os.makedirs(os.path.join(self.root, "tools"), exist_ok=True)
        with open(os.path.join(self.root, "tools", "a.py"), "wb") as fh:
            fh.write(b"a v1\r\n")
        self.v2()
        rc, out = self.run_tool("--update", "--apply")
        self.assertEqual(rc, 0, out)
        self.assertIn("REPLACE  tools/a.py", out)
        self.assertNotIn("KEEP     tools/a.py", out)
        self.assertEqual(read(os.path.join(self.root, "tools", "a.py")), "a v2\n")

    def test_untouched_team_file_is_updated_filled_one_is_kept(self):
        for rel in ("docs/jam-brief.md", "AGENTS.md"):
            os.makedirs(os.path.dirname(os.path.join(self.root, rel)) or self.root, exist_ok=True)
            shutil.copy(os.path.join(self.mp, "repo", rel), os.path.join(self.root, rel))
        self.v2()
        rc, out = self.run_tool("--update", "--apply")
        self.assertIn("REPLACE  docs/jam-brief.md", out)
        self.assertEqual(read(os.path.join(self.root, "docs", "jam-brief.md")), "brief v2\n")
        write(os.path.join(self.root, "docs", "jam-brief.md"), "brief filled in by the team\n")
        self.release({"AGENTS.md": "agents v3\n", "docs/jam-brief.md": "brief v3\n", "pipeline/VERSION": "3.0.0\n"})
        rc, out = self.run_tool("--update", "--apply")
        self.assertIn("KEEP     docs/jam-brief.md  (team file", out)
        self.assertEqual(read(os.path.join(self.root, "docs", "jam-brief.md")), "brief filled in by the team\n")

    def test_update_leaves_user_files_alone(self):
        self.assertEqual(self.run_tool("--apply")[0], 0)
        write(os.path.join(self.root, "Source", "Game.cpp"), "game\n")
        write(os.path.join(self.root, "notes.md"), "ours\n")
        write(os.path.join(self.root, "docs", "jam-brief.md"), "brief with our People table\n")
        write(os.path.join(self.root, "AGENTS.md"), "agents v1, edited by the TD\n")
        write(os.path.join(self.root, "docs", "gdd", "GDD-1.3.md"), "our gdd\n")
        write(os.path.join(self.root, "tools", "gone.py"), "gone v1, edited\n")
        self.v2()
        rc, out = self.run_tool("--update", "--apply")
        self.assertEqual(rc, 0, out)
        for rel, text in (("Source/Game.cpp", "game\n"), ("notes.md", "ours\n"),
                          ("docs/jam-brief.md", "brief with our People table\n"),
                          ("AGENTS.md", "agents v1, edited by the TD\n"), ("docs/gdd/GDD-1.3.md", "our gdd\n"),
                          ("tools/gone.py", "gone v1, edited\n")):
            with self.subTest(rel=rel):
                self.assertEqual(read(os.path.join(self.root, rel)), text)
        self.assertIn("KEEP     docs/jam-brief.md  (team file", out)
        self.assertIn("KEEP     AGENTS.md  (changed by the team", out)
        self.assertIn("KEEP     tools/gone.py", out)
        self.assertNotIn("Source/Game.cpp", out)
        self.assertNotIn("notes.md", out)
        self.assertNotIn("GDD-1.3", out)
        stamp = os.listdir(os.path.join(self.root, "Saved", "pipeline-backup"))[0]
        self.assertEqual(read(os.path.join(self.root, "Saved", "pipeline-backup", stamp, "new", "AGENTS.md")),
                         "agents v2\n")
        self.assertEqual(read(os.path.join(self.root, "tools", "a.py")), "a v2\n")

    def test_stale_manifest_refuses(self):
        write(os.path.join(self.mp, "repo", "tools", "a.py"), "edited without a new manifest\n")
        rc, out = self.run_tool("--update")
        self.assertEqual(rc, 1, out)
        self.assertIn("--make-manifest", out)


if __name__ == "__main__":
    unittest.main()
