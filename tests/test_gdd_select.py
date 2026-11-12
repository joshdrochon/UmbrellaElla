"""tools/gdd_select.py and kickoff --gdd: pick a GDD revision to test, check the pipeline can import it, record it.
Each check has a passing case and a case broken on purpose."""
import hashlib
import json
import os
import shutil
import sqlite3
import subprocess
import sys
import tempfile
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.join(HERE, "fixtures", "kickoff"))
sys.path.insert(0, os.path.join(ROOT, "tools"))
import gdd_select  # noqa: E402
import journal  # noqa: E402

V14 = "tests/fixtures/gdd/v1.4/GameDesignDocument-v1.4.md"   # the team's v1.4 package (PipelineTesting scratch/gdd/v1.4)
GDD13 = os.path.join(ROOT, "docs", "gdd", "GDD-1.3.md")
GDDSH = os.path.join(ROOT, "docs", "gdd", "GDD-SH1.0.md")   # the current snapshot (docs/gdd/CURRENT)
LEGACY = os.path.join(HERE, "fixtures", "gdd13")             # the 1.3 manifest and presets as merged before SH1.0


def sha(path):
    with open(path, "rb") as fh:
        return hashlib.sha256(fh.read()).hexdigest()


def fixes(lines):
    return [ln[len("FIX "):] for ln in lines if ln.startswith("FIX ")]


class MiniRepo:
    """The files the check reads (manifest, presets, decisions, GDD snapshots, VERSION) in a temp folder."""
    FILES = ("docs/feature-manifest.json", "pipeline/qa/presets.json", "docs/decisions.md", "pipeline/VERSION",
             "docs/gdd/CURRENT", "docs/gdd/GDD-1.3.md", "docs/gdd/GDD-B1.0.md")

    def __init__(self):
        """A GDD 1.3 repo: the frozen 1.3 manifest and presets with CURRENT on GDD-1.3.md. The checks are generic, and
        1.3 is the revision with derived revisions (1.3.1) these tests build; GDD SH1.0 is checked on the real repo."""
        self.root = tempfile.mkdtemp(prefix="gddsel-")
        for f in self.FILES:
            os.makedirs(os.path.dirname(self.p(f)), exist_ok=True)
            shutil.copy2(os.path.join(ROOT, f), self.p(f))
        shutil.copy2(os.path.join(LEGACY, "docs", "feature-manifest.json"), self.p("docs/feature-manifest.json"))
        shutil.copy2(os.path.join(LEGACY, "pipeline", "qa", "presets.json"), self.p("pipeline/qa/presets.json"))
        self.write("docs/gdd/CURRENT", "GDD-1.3.md\n")

    def p(self, rel):
        return os.path.join(self.root, rel)

    def write(self, rel, text):
        os.makedirs(os.path.dirname(self.p(rel)), exist_ok=True)
        with open(self.p(rel), "w", encoding="utf-8", newline="\n") as fh:
            fh.write(text)

    def manifest(self, edit=None):
        with open(self.p("docs/feature-manifest.json"), encoding="utf-8") as fh:
            m = json.load(fh)
        if edit:
            edit(m)
            with open(self.p("docs/feature-manifest.json"), "w", encoding="utf-8") as fh:
                json.dump(m, fh, indent=2)
        return m

    def close(self):
        shutil.rmtree(self.root, ignore_errors=True)


def gdd13_text():
    with open(GDD13, encoding="utf-8") as fh:
        return fh.read()


class Resolve(unittest.TestCase):
    def setUp(self):
        self.r = MiniRepo()
        self.addCleanup(self.r.close)
        self.r.write("scratch/gdd/v2.0/GameDesignDocument-v2.0.md", "# GDD\n\n| Publication | Value |\n| --- | --- |\n"
                                                                    "| Revision | 2.0 |\n")
        self.r.write("scratch/gdd/v2.0/CHANGELOG-v2.0.md", "# GDD v2.0 Changelog\n")   # no Revision row: never picked

    def test_revision_spellings(self):
        for arg in ("1.3", "v1.3", "GDD-1.3", "GDD-1.3.md"):
            with self.subTest(arg=arg):
                self.assertEqual(gdd_select.resolve(arg, self.r.root), ("docs/gdd/GDD-1.3.md", None))
        self.assertEqual(gdd_select.resolve("v2.0", self.r.root), ("scratch/gdd/v2.0/GameDesignDocument-v2.0.md", None))
        self.assertEqual(gdd_select.resolve("B1.0", self.r.root), ("docs/gdd/GDD-B1.0.md", None))

    def test_docs_gdd_wins_over_scratch(self):
        self.r.write("scratch/gdd/old/copy.md", gdd13_text())
        self.assertEqual(gdd_select.resolve("1.3", self.r.root)[0], "docs/gdd/GDD-1.3.md")

    def test_paths(self):
        rel = "scratch/gdd/v2.0/GameDesignDocument-v2.0.md"
        self.assertEqual(gdd_select.resolve(rel, self.r.root, cwd=self.r.root), (rel, None))
        self.assertEqual(gdd_select.resolve(rel.replace("/", os.sep), self.r.root, cwd="/"), (rel, None))
        sub = self.r.p("scratch/gdd")
        self.assertEqual(gdd_select.resolve("v2.0/GameDesignDocument-v2.0.md", self.r.root, cwd=sub), (rel, None))

    def test_broken_on_purpose(self):
        path, err = gdd_select.resolve("9.9", self.r.root)
        self.assertIsNone(path)
        self.assertIn("no GDD revision 9.9", err)
        self.assertIn("Known revisions: 1.3, B1.0", err)
        self.r.write("scratch/gdd/dup/a.md", "| Revision | 2.0 |\n")
        path, err = gdd_select.resolve("2.0", self.r.root)
        self.assertIsNone(path)
        self.assertIn("matches 2 files", err)
        self.assertIn("no file nope.md", gdd_select.resolve("nope.md", self.r.root)[1])
        outside = tempfile.NamedTemporaryFile("w", suffix=".md", delete=False)
        outside.close()
        self.addCleanup(os.remove, outside.name)
        self.assertIn("outside the repo", gdd_select.resolve(outside.name, self.r.root)[1])
        self.r.write("scratch/gdd/x.pdf.txt/readme", "")
        self.assertIn("not a .md file", gdd_select.resolve("scratch/gdd/x.pdf.txt/readme", self.r.root)[1])


class Validate(unittest.TestCase):
    def test_current_gdd_passes_and_nothing_is_written(self):
        before = sha(os.path.join(ROOT, "docs", "gdd", "CURRENT")), sha(GDDSH)
        code, lines, env = gdd_select.choose("SH1.0", ROOT, check=True)
        self.assertEqual(code, 0, "\n".join(lines))
        self.assertEqual(fixes(lines), [])
        self.assertEqual(env, {})
        self.assertEqual((sha(os.path.join(ROOT, "docs", "gdd", "CURRENT")), sha(GDDSH)), before)
        # the history snapshot is not importable against today's manifest: it names none of the SH1.0 records
        code, lines, _ = gdd_select.choose("1.3", ROOT, check=True)
        self.assertEqual(code, 1)
        self.assertTrue(any("FLOW-02 has a record, but GDD 1.3 never names it" in g for g in fixes(lines)))

    def test_v14_package_lists_what_to_fix(self):
        """The team's v1.4 package as it is: its layout is not the one the pipeline reads, so it fails, one line each."""
        before = sha(os.path.join(ROOT, V14))
        code, lines, env = gdd_select.choose(V14, ROOT, check=True)
        self.assertEqual(code, 1, "\n".join(lines))
        self.assertEqual(env, {})
        got = fixes(lines)
        want_starts = [
            V14 + ": no line of just '---' under the header table",
            V14 + ": no feature status rows.",
            V14 + ": no section 5A parameter tables.",
            V14 + ": no test preset IDs (T-01 BASE, T-02, ...).",
            V14 + ": no QA test IDs (QA-01, QA-02, ...).",
            'docs/feature-manifest.json: set "gdd_revision" to "1.4" at the top and in every feature record',
            "docs/feature-manifest.json: CAM-03 has a record, but GDD 1.4 never names it.",
        ]
        for w in want_starts:
            self.assertTrue(any(g.startswith(w) for g in got), f"missing {w!r} in\n" + "\n".join(got))
        self.assertIn("rows like ABSORB-FINISH", got[1])
        self.assertTrue(lines[-1].startswith(f"gdd_select: GDD 1.4 cannot be imported yet: {len(got)} thing(s)"))
        self.assertEqual(sha(os.path.join(ROOT, V14)), before, "the GDD file is never edited")

    def test_broken_on_purpose_gives_one_clear_line_each(self):
        r = MiniRepo()
        self.addCleanup(r.close)
        text = gdd13_text()
        broken = (text.replace("| Revision | 1.3 |\n", "")
                  .replace("| Gravity magnitude |", "| Gravity strength |")
                  .replace("| CORE-01 | Regular horizontal steering is always enabled in the initial build; "
                           "wind/dash-only variants are optional. | APPROVED_P0 |",
                           "| CORE-01 | Regular horizontal steering is always enabled in the initial build; "
                           "wind/dash-only variants are optional. | PROPOSED |"))
        self.assertNotEqual(broken, text)
        r.write("scratch/gdd/broken/GDD.md", broken)
        code, lines, _ = gdd_select.choose("scratch/gdd/broken/GDD.md", r.root, check=True)
        self.assertEqual(code, 1)
        got = fixes(lines)
        self.assertTrue(any(g.startswith("scratch/gdd/broken/GDD.md: no '| Revision | <number> |' row") for g in got),
                        got)
        self.assertIn("tools/manifest_check.py PARAM_ROWS: map the new section 5A row 'Gravity strength' to an "
                      "approved_parameters key (the pipeline owner changes this table).", got)
        self.assertTrue(any(g.startswith("docs/feature-manifest.json CORE-01: status is APPROVED_P0, GDD ? says "
                                         "'PROPOSED'.") for g in got), got)
        self.assertFalse(any('"gdd_revision" to "?"' in g for g in got), got)   # the Revision line already says it
        for g in got:
            self.assertNotIn("\n", g)
            self.assertRegex(g, r"^[\w./ -]+[: ]", g)   # every line starts with the file to change
        # the same fixed file passes: the problems came from the edits alone
        r.write("scratch/gdd/broken/GDD.md", text)
        self.assertEqual(gdd_select.choose("scratch/gdd/broken/GDD.md", r.root, check=True)[0], 0)

    def test_changed_copy_under_the_same_revision_fails(self):
        r = MiniRepo()
        self.addCleanup(r.close)
        r.write("scratch/gdd/edit/GDD.md", gdd13_text().replace("four-day window", "five-day window"))
        code, lines, _ = gdd_select.choose("scratch/gdd/edit/GDD.md", r.root, check=True)
        self.assertEqual(code, 1)
        self.assertTrue(any("it says Revision 1.3, like docs/gdd/GDD-1.3.md, but its text differs" in g
                            for g in fixes(lines)), lines)

    def test_asked_revision_must_match_the_file(self):
        r = MiniRepo()
        self.addCleanup(r.close)
        r.write("docs/gdd/GDD-7.md", gdd13_text())   # named 7, says 1.3
        lines = gdd_select.validate("docs/gdd/GDD-7.md", r.root, want_rev="7")
        self.assertTrue(any("you asked for revision 7, but its Revision row says 1.3" in g for g in lines), lines)
        self.assertTrue(any("--pin docs/gdd/GDD-7.md" in g for g in lines), lines)   # every docs/gdd snapshot is pinned


class Current(unittest.TestCase):
    """docs/gdd/CURRENT changes only with --set-current, and only for a pinned docs/gdd/GDD-<rev>.md."""

    def setUp(self):
        self.r = MiniRepo()
        self.addCleanup(self.r.close)
        self.cur = self.r.p("docs/gdd/CURRENT")

    def new_revision(self):
        """A 1.3.1 snapshot and a manifest reconciled to it (what an integration PR would hold)."""
        rel = "docs/gdd/GDD-1.3.1.md"
        self.r.write(rel, gdd13_text().replace("| Revision | 1.3 |", "| Revision | 1.3.1 |"))

        def to_131(m):
            m["gdd_revision"] = "1.3.1"
            for f in m["features"]:
                f["gdd_revision"] = "1.3.1"
        self.r.manifest(to_131)
        return rel

    def test_run_scoped_by_default(self):
        self.r.write("scratch/gdd/same/GDD.md", gdd13_text())
        before = sha(self.cur)
        code, lines, env = gdd_select.choose("scratch/gdd/same/GDD.md", self.r.root)
        self.assertEqual(code, 0, lines)
        self.assertEqual(sha(self.cur), before)
        self.assertEqual(env, {journal.GDD_ENV: os.path.join(os.path.realpath(self.r.root), "scratch/gdd/same/GDD.md")})
        self.assertIn("docs/gdd/CURRENT is unchanged", "\n".join(lines))
        line = gdd_select.version_line(self.r.root, env)
        self.assertRegex(line, r"^pipeline \S+ \| GDD 1\.3 \(scratch/gdd/same/GDD\.md sha256 [0-9a-f]{12}, --gdd; "
                               r"CURRENT GDD-1\.3\.md\)$")
        self.assertNotIn(journal.GDD_ENV, os.environ)   # version_line leaves the environment as it was

    def test_the_gdds_images_join_the_art_references(self):
        """Wired to pipeline/art/references.json gdd_embedded: the picked GDD's images join the art references for
        the run (tools/art_check.py reads $JAM_GDD), and gdd_select says which are present. Broken on purpose: a
        missing image is named; without gdd_embedded the line says the images are not used."""
        import art_check
        os.makedirs(self.r.p("pipeline/art"), exist_ok=True)
        shutil.copy2(os.path.join(ROOT, "pipeline", "art", "references.json"), self.r.p("pipeline/art/references.json"))
        def to_131(m):
            m["gdd_revision"] = "1.3.1"
            for f in m["features"]:
                f["gdd_revision"] = "1.3.1"
        self.r.manifest(to_131)
        self.r.write("scratch/gdd/pics/GDD.md", gdd13_text().replace("| Revision | 1.3 |", "| Revision | 1.3.1 |")
                     + "\n![a](art/a.png)\n<img src=\"art/b.png\">\n")
        self.r.write("scratch/gdd/pics/art/a.png", "png")
        code, lines, env = gdd_select.choose("scratch/gdd/pics/GDD.md", self.r.root)
        self.assertEqual(code, 0, lines)
        self.assertIn("gdd_select: art references: GDD embeds 2 image(s), 1 present, missing scratch/gdd/pics/art/b.png",
                      "\n".join(lines))
        refs = {r["path"]: r for r in art_check.load_references(self.r.root) if r["source"] == "gdd"}
        self.assertEqual(refs, {})   # CURRENT's GDD 1.3 embeds none
        old = os.environ.get(journal.GDD_ENV)
        os.environ.update(env)
        try:
            refs = {r["path"]: r for r in art_check.load_references(self.r.root) if r["source"] == "gdd"}
        finally:
            os.environ.pop(journal.GDD_ENV, None)
            if old is not None:
                os.environ[journal.GDD_ENV] = old
        self.assertEqual(set(refs), {"scratch/gdd/pics/art/a.png", "scratch/gdd/pics/art/b.png"})
        self.assertTrue(refs["scratch/gdd/pics/art/a.png"]["exists"])
        self.assertFalse(refs["scratch/gdd/pics/art/b.png"]["required"], "a GDD image is optional")
        with open(self.r.p("pipeline/art/references.json"), encoding="utf-8") as fh:
            spec = json.load(fh)
        spec.pop("gdd_embedded")
        self.r.write("pipeline/art/references.json", json.dumps(spec))
        self.assertIn("has no gdd_embedded", "\n".join(gdd_select.choose("scratch/gdd/pics/GDD.md", self.r.root)[1]))

    def test_the_gdd_picker_lists_its_encounter_presets(self):
        """Wired to the encounter preset hook (tools/encounter_spec.py presets_for, context gdd_picker): the picked
        revision's presets are named, the default marked. Broken on purpose: a preset not selectable in gdd_picker is
        left out, a revision with no preset says so, a missing encounter.json says so."""
        self.assertIn("encounter.json is missing", gdd_select.encounter_line("1.3", self.r.root))
        os.makedirs(self.r.p("pipeline/level"), exist_ok=True)
        shutil.copy2(os.path.join(LEGACY, "pipeline", "level", "encounter.json"), self.r.p("pipeline/level/encounter.json"))
        code, lines, _ = gdd_select.choose("1.3", self.r.root)
        self.assertEqual(code, 0, lines)
        line = next(ln for ln in lines if "encounter presets" in ln)
        self.assertIn("GDD-1.3 (baseline, default)", line)
        self.assertIn("OWL-FIGHT-RICKY (proposed, D-new-encounter-ricky)", line)
        with open(self.r.p("pipeline/level/encounter.json"), encoding="utf-8") as fh:
            data = json.load(fh)
        data["encounter_presets"]["presets"]["OWL-FIGHT-RICKY"]["selectable_in"] = ["workbench"]
        self.r.write("pipeline/level/encounter.json", json.dumps(data))
        self.assertNotIn("OWL-FIGHT-RICKY", gdd_select.encounter_line("1.3", self.r.root))
        self.assertIn("none for GDD 1.3.1", gdd_select.encounter_line("1.3.1", self.r.root))

    def test_set_current_needs_pin_and_gdd_snapshot(self):
        rel = self.new_revision()
        before = sha(self.cur)
        code, lines, _ = gdd_select.choose("1.3.1", self.r.root, set_current=True)
        self.assertEqual(code, 1, lines)
        got = fixes(lines)
        py = "py" if os.name == "nt" else "python3"   # the command this OS types (gdd_select.py prints the same)
        self.assertIn(f"docs/feature-manifest.json: add the line `{py} tools/manifest_check.py --pin "
                      f'{rel}` prints to "gdd_snapshots" (every docs/gdd/GDD-*.md is pinned; docs/gdd/README.md step 2).',
                      got)
        self.assertTrue(any(g.startswith('docs/feature-manifest.json: set "gdd_snapshot" to "docs/gdd/GDD-1.3.1.md"')
                            for g in got), got)
        self.assertEqual(sha(self.cur), before, "a failed check writes nothing")

        def pin(m):
            m["gdd_snapshots"][rel] = gdd_select.mc.snapshot_sha256(self.r.p(rel))
            m["gdd_snapshot"] = rel
        self.r.manifest(pin)
        code, lines, env = gdd_select.choose("1.3.1", self.r.root, set_current=True, check=True)
        self.assertEqual(code, 0, lines)
        self.assertEqual(sha(self.cur), before, "--check never writes")
        code, lines, env = gdd_select.choose("1.3.1", self.r.root, set_current=True)
        self.assertEqual(code, 0, lines)
        self.assertEqual(env, {})
        with open(self.cur, encoding="utf-8") as fh:
            self.assertEqual(fh.read(), "GDD-1.3.1.md\n")
        self.assertIn("docs/gdd/CURRENT now names GDD-1.3.1.md (was docs/gdd/GDD-1.3.md)", "\n".join(lines))

    def test_set_current_refuses_a_scratch_file(self):
        self.r.write("scratch/gdd/same/GDD.md", gdd13_text())
        code, lines, _ = gdd_select.choose("scratch/gdd/same/GDD.md", self.r.root, set_current=True)
        self.assertEqual(code, 1)
        self.assertIn("is not a docs/gdd/GDD-<rev>.md snapshot", "\n".join(lines))
        with open(self.cur, encoding="utf-8") as fh:
            self.assertEqual(fh.read().strip(), "GDD-1.3.md")


class Cli(unittest.TestCase):
    def run_tool(self, *args):
        p = subprocess.run([sys.executable, os.path.join(ROOT, "tools", "gdd_select.py"), *args], cwd=ROOT,
                           capture_output=True, text=True, env={k: v for k, v in os.environ.items()
                                                                if k != journal.GDD_ENV})
        return p.returncode, p.stdout + p.stderr

    def test_exit_codes_and_version_line(self):
        rc, out = self.run_tool("SH1.0", "--check")
        self.assertEqual(rc, 0, out)
        self.assertRegex(out, r"(?m)^pipeline \d[\w.]*\+\w+(-dirty)? \| GDD SH1\.0 \(GDD-SH1\.0\.md sha256 ")
        rc, out = self.run_tool(V14, "--check")
        self.assertEqual(rc, 1, out)
        self.assertIn("FIX ", out)
        self.assertNotIn("Traceback", out)
        rc, out = self.run_tool("9.9")
        self.assertEqual(rc, 2, out)
        self.assertEqual(len(out.strip().splitlines()), 1, out)
        rc, out = self.run_tool()
        self.assertEqual(rc, 2, out)
        self.assertIn("I did not understand that", out)


class JournalRecord(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.mkdtemp()
        self.addCleanup(shutil.rmtree, self.tmp, True)
        self.old = os.environ.pop(journal.GDD_ENV, None)
        self.addCleanup(lambda: os.environ.update({journal.GDD_ENV: self.old}) if self.old else
                        os.environ.pop(journal.GDD_ENV, None))

    def record(self):
        con = journal.connect(os.path.join(self.tmp, "j.db"))
        try:
            rid = journal.start_run(con, "kickoff", "codex", "m", None, None, ROOT)
            return journal.get_run(con, rid)
        finally:
            con.close()

    def test_run_record_stores_the_chosen_gdd(self):
        self.assertTrue(self.record()["gdd_revision"].startswith("SH1.0 (GDD-SH1.0.md sha256 "))
        os.environ[journal.GDD_ENV] = os.path.join(ROOT, V14)
        run = self.record()
        self.assertEqual(run["gdd_revision"], f"1.4 ({V14} sha256 {sha(os.path.join(ROOT, V14))[:12]}, --gdd; "
                                              "CURRENT GDD-SH1.0.md)")
        self.assertTrue(run["pipeline_version"])
        os.environ[journal.GDD_ENV] = os.path.join(self.tmp, "gone.md")   # broken on purpose
        self.assertTrue(self.record()["gdd_revision"].startswith("unknown (JAM_GDD="))


@unittest.skipIf(shutil.which("git") is None, "needs git")
class KickoffGdd(unittest.TestCase):
    def setUp(self):
        import kickoff_sandbox as ks
        import test_honest_jam as thj
        self.sb = ks.KickoffSandbox(thj.PEOPLE)
        self.addCleanup(self.sb.close)
        os.makedirs(os.path.join(self.sb.repo, "scratch", "gdd", "copy"))
        shutil.copy2(GDDSH, os.path.join(self.sb.repo, "scratch", "gdd", "copy", "GDD.md"))

    def test_run_records_the_chosen_gdd_and_current_is_unchanged(self):
        cur = os.path.join(self.sb.repo, "docs", "gdd", "CURRENT")
        before = sha(cur)
        rc, out = self.sb.kickoff("--agent", "claude", "--practice", "--gdd", "scratch/gdd/copy/GDD.md",
                                  STUB_DAY0_ONLY="0.7")
        self.assertEqual(rc, 0, out)
        self.assertIn("kickoff: OK, GDD SH1.0 (scratch/gdd/copy/GDD.md) passes every import check.", out)
        self.assertRegex(out, r"kickoff: pipeline \S+ \| GDD SH1\.0 \(scratch/gdd/copy/GDD\.md sha256 [0-9a-f]{12}, "
                              r"--gdd; CURRENT GDD-SH1\.0\.md\)")
        self.assertEqual(sha(cur), before)
        con = sqlite3.connect(os.path.join(self.sb.base, "journal.db"))
        try:
            gdd, ver = con.execute("SELECT gdd_revision, pipeline_version FROM runs").fetchone()
            prompts = [r[0] for r in con.execute("SELECT prompt FROM run_prompts WHERE run_id = 1")]
        finally:
            con.close()
        self.assertTrue(gdd.startswith("SH1.0 (scratch/gdd/copy/GDD.md sha256 "), gdd)
        self.assertRegex(ver, r"^\d[\w.]*\+[0-9a-f]{7}")
        self.assertTrue(prompts and all("GDD for this run (kickoff --gdd, SH1.0)" in p and "scratch/gdd/copy/GDD.md" in p
                                        for p in prompts), prompts)

    def test_failing_gdd_never_starts_a_run(self):
        os.makedirs(os.path.join(self.sb.repo, "tests", "fixtures", "gdd", "v1.4"), exist_ok=True)
        rc, out = self.sb.kickoff("--agent", "claude", "--gdd", V14)
        self.assertEqual(rc, 2, out)
        self.assertIn("FIX ", out)
        self.assertIn("kickoff: GDD 1.4 cannot be imported yet", out)
        self.assertNotIn("RUN #", out)
        self.assertFalse(os.path.exists(os.path.join(self.sb.base, "journal.db")))
        rc, out = self.sb.kickoff("--agent", "claude", "--set-current")
        self.assertEqual(rc, 2, out)
        self.assertIn("--set-current needs --gdd", out)

    def test_check_validates_and_prints_version(self):
        rc, out = self.sb.kickoff("--agent", "claude", "--check", "--gdd", "SH1.0")
        self.assertIn("kickoff: OK, GDD SH1.0 (docs/gdd/GDD-SH1.0.md) passes every import check.", out)
        self.assertRegex(out, r"kickoff: pipeline \S+ \| GDD SH1\.0 \(GDD-SH1\.0\.md sha256 ")


if __name__ == "__main__":
    unittest.main()
