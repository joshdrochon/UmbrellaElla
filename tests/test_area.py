"""Tests for tools/area.py and the direct build (tools/direct_build.py, run by tools/kickoff.py when docs/build/MODE
is `direct`). Each test builds a bare origin with HANDOFF.md, two area briefs and one area branch holding the lead's
work, then clones it the way a teammate does. Broken on purpose: an out-of-lane commit, a shared-file change on the
branch, a push race, a failing gate, a gh call."""
import os
import shutil
import subprocess
import sys
import tempfile
import textwrap
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
PY = sys.executable
TOOLS = ("area.py", "area.sh", "area.ps1", "direct_build.py", "ue_slot.py")
HANDOFF = textwrap.dedent("""\
    # Handoff
    | Area | Branch | Who has it | Status | Next step |
    |---|---|---|---|---|
    | keeper | area/keeper | free | in progress | swoop |
    | menus | area/menus | free | not started | title |
    | arena | area/arena | Josh | in progress | blockout |
    """)


def brief(name, lane):
    return f"# {name}\n\n## Lane\n" + "".join(f"- `{p}`\n" for p in lane) + "\n## Done when\n- gates pass\n"


class Repo:
    def __init__(self, extra=None):
        self.base = os.path.realpath(tempfile.mkdtemp(prefix="area-"))
        self.origin = os.path.join(self.base, "origin.git")
        seed = os.path.join(self.base, "seed")
        self.env = dict(os.environ, GIT_TERMINAL_PROMPT="0", GIT_CONFIG_GLOBAL=os.path.join(self.base, "gitconfig"),
                        GIT_CONFIG_NOSYSTEM="1")
        for k in ("JAM_ROLE", "JAM_CARD", "CLAUDECODE", "CODEX_SANDBOX", "CODEX_THREAD_ID", "AREA_AGENT_CMD",
                  "KICKOFF_AGENT_CMD"):
            self.env.pop(k, None)
        with open(self.env["GIT_CONFIG_GLOBAL"], "w") as fh:
            fh.write("[user]\n\tname = t\n\temail = t@example.invalid\n[init]\n\tdefaultBranch = main\n")
        os.makedirs(os.path.join(seed, "tools"))
        self.git(seed, "init", "-q")
        for f in TOOLS:
            shutil.copy(os.path.join(ROOT, "tools", f), os.path.join(seed, "tools", f))
        self.write(seed, "HANDOFF.md", HANDOFF)
        self.write(seed, "docs/build/MODE", "direct\n")
        self.write(seed, "docs/build/gates.txt", "{py} -c \"import os,sys; sys.exit(1 if os.path.exists('FAILGATE') else 0)\"\n")
        self.write(seed, "docs/build/areas/keeper.md", brief("keeper", ["Source/G/*/Owl/*", "Content/G/Keeper/"]))
        self.write(seed, "docs/build/areas/menus.md", brief("menus", ["Source/G/Private/Flow/", "Content/G/Maps/L_Title.umap"]))
        self.write(seed, "docs/build/areas/arena.md", brief("arena", ["Source/G/Private/Arena/"]))
        for name, lane in (extra or {}).items():
            self.write(seed, f"docs/build/areas/{name}.md", brief(name, lane))
        self.write(seed, "Config/DefaultEngine.ini", "[x]\n")
        self.commit(seed, "main")
        self.git(seed, "switch", "-q", "-c", "area/keeper")
        self.write(seed, "Source/G/Public/Owl/Keeper.h", "// lead wip\n")
        self.commit(seed, "keeper: lead wip")
        self.git(seed, "switch", "-q", "main")
        self.git(self.base, "clone", "-q", "--bare", seed, self.origin)
        shutil.rmtree(seed)

    def git(self, cwd, *a, check=True):
        r = subprocess.run(["git", *a], cwd=cwd, capture_output=True, text=True, env=self.env)
        if check and r.returncode:
            raise AssertionError(f"git {a}: {r.stderr}")
        return r

    def write(self, root, path, text):
        p = os.path.join(root, path)
        os.makedirs(os.path.dirname(p), exist_ok=True)
        with open(p, "w", newline="\n") as fh:
            fh.write(text)

    def commit(self, root, msg, check=True):
        self.git(root, "add", "-A")
        return self.git(root, "commit", "-q", "-m", msg, check=check)

    def clone(self, name):
        c = os.path.join(self.base, name)
        self.git(self.base, "clone", "-q", self.origin, c)
        return c

    def area(self, cwd, *a, **env):
        return subprocess.run([PY, "tools/area.py", *a], cwd=cwd, capture_output=True, text=True,
                              env=dict(self.env, **env))

    def subjects(self, ref="main"):
        return self.git(self.origin, "log", "--format=%s", ref).stdout


STUB = textwrap.dedent("""\
    import os, subprocess, sys
    area = sys.argv[1]
    argv = sys.argv[2:]
    open(os.path.join(os.environ["LOGDIR"], area + ".argv"), "w").write("\\n".join(argv) + "\\n" + os.environ.get("JAM_ROLE", ""))
    import time
    open(os.path.join(os.environ["LOGDIR"], area + ".start"), "w").write(str(time.time()))
    time.sleep(float(os.environ.get("WORK_S", "0")))
    open(os.path.join(os.environ["LOGDIR"], area + ".end"), "w").write(str(time.time()))
    path = {"keeper": "Source/G/Private/Owl/Swoop.cpp", "menus": "Source/G/Private/Flow/Title.cpp"}.get(
        area, "Source/G/Private/" + area + "/W.cpp")
    os.makedirs(os.path.dirname(path), exist_ok=True)
    open(path, "w").write("// " + area + "\\n")
    if os.environ.get("STRAY"):
        open("Config/DefaultEngine.ini", "a").write("; stray\\n")
    """)


# The lane notation of the build lead's briefs (UmbrellaElla docs/build/areas/*.md, 12 Nov): braces, **, items
# relative to the bullet's first path, bullets over two lines, "except".
REAL = {
    "move": """## File lane (only these)
- `Source/UmbrellaElla/{Public,Private}/Input/**`, `Motor/**`, `Umbrella/**`, `Attack/**`
- `Source/UmbrellaElla/Private/Tests/Move/**`, `Private/Tests/Shared/**` (you create the shared world-test helper
  other areas will reuse)
- `Content/UmbrellaElla/Input/**` except `Input/Menu/**`; `tools/build/assets/input_*.py` (editor scripts)
- `pipeline/feel/**`, `docs/build/areas/move-status.md`, `docs/build/requests/move.md`

## What to build
- `Source/UmbrellaElla/Private/Flow/NotMine.cpp`
""",
    "flow": """## File lane (only these)
- `Source/UmbrellaElla/Public/Core/UmbrellaGameMode.h` and `Private/Core/UmbrellaGameMode.cpp` (you own the GameMode),
  `{Public,Private}/Flow/**`, `UI/Menus/**`, `Story/**`
- `Content/UmbrellaElla/Input/Menu/**`, `Content/UmbrellaElla/UI/Menus/**`, `docs/build/requests/flow.md`
""",
    "health": """## File lane (only these)
- `Source/UmbrellaElla/{Public,Private}/Projectile/**` (the Core seam headers there are yours to extend, not rename),
  `Health/**`, `UI/**` (except `UI/Menus/**`, `UI/Story/**`), `Defense/**`
""",
    "arena": """## File lane (only these)
- `Content/UmbrellaElla/Maps/**`, `Content/UmbrellaElla/Audio/**`, `Audio/Source/**`, `pipeline/art/**`
""",
}


class LaneParse(unittest.TestCase):
    def setUp(self):
        sys.path.insert(0, os.path.join(ROOT, "tools"))
        import area
        self.area = area
        self.lanes = {k: area.lane_of(v) for k, v in REAL.items()}

    def owners(self, path):
        return [k for k, lane in self.lanes.items() if self.area.in_lane(path, lane, k)]

    def test_real_notation_gives_one_owner(self):
        S = "Source/UmbrellaElla/"
        for path, want in ((S + "Private/Motor/M.cpp", ["move"]), (S + "Public/Attack/A.h", ["move"]),
                           (S + "Private/Tests/Shared/W.cpp", ["move"]), ("Content/UmbrellaElla/Input/IA_Fire.uasset", ["move"]),
                           ("Content/UmbrellaElla/Input/Menu/IMC_Menu.uasset", ["flow"]), ("tools/build/assets/input_a.py", ["move"]),
                           (S + "Private/Core/UmbrellaGameMode.cpp", ["flow"]), (S + "Private/Flow/F.cpp", ["flow"]),
                           (S + "Private/UI/Menus/Title.cpp", ["flow"]), (S + "Public/UI/UmbrellaHUD.h", ["health"]),
                           (S + "Private/Story/S.cpp", ["flow"]), ("Audio/Source/rain.wav", ["arena"]),
                           (S + "Public/UI/Story/Card.h", []), (S + "Private/Defense/D.cpp", ["health"]),
                           ("Content/UmbrellaElla/Maps/L_Graybox.umap", ["arena"]),
                           (S + "Public/Core/EllaCharacter.h", []), ("Config/DefaultEngine.ini", []),
                           ("UmbrellaElla.uproject", []), (S + "UmbrellaElla.Build.cs", [])):
            self.assertEqual(self.owners(path), want, path)

    def test_lane_section_ends_at_next_heading(self):
        self.assertEqual(self.owners("Source/UmbrellaElla/Private/Flow/NotMine.cpp"), ["flow"])


class AreaTool(unittest.TestCase):
    def setUp(self):
        self.r = Repo()
        self.addCleanup(shutil.rmtree, self.r.base, True)

    def test_resume_from_origin_branch_guard_and_merge_back(self):
        c = self.r.clone("ana")
        res = self.r.area(c, "keeper", "--agent", "none")
        self.assertEqual(res.returncode, 0, res.stderr)
        self.assertIn("Source/G/*/Owl/*", res.stdout)
        self.assertIn("| keeper | area/keeper | free | in progress | swoop |", res.stdout)
        self.assertTrue(os.path.exists(os.path.join(c, "Source/G/Public/Owl/Keeper.h")))   # the lead's work
        self.r.write(c, "Config/DefaultEngine.ini", "[x]\nchanged\n")
        bad = self.r.commit(c, "out of lane", check=False)
        self.assertNotEqual(bad.returncode, 0)
        self.assertIn("Config/DefaultEngine.ini", bad.stderr)
        self.r.git(c, "restore", "--staged", "--worktree", "Config/DefaultEngine.ini")
        self.r.write(c, "Source/G/Private/Owl/Swoop.cpp", "// swoop\n")
        self.r.write(c, "docs/build/requests/keeper.md", "- a collision channel\n")
        self.assertEqual(self.r.commit(c, "keeper: swoop").returncode, 0)
        done = self.r.area(c, "keeper", "--done")
        self.assertEqual(done.returncode, 0, done.stderr)
        self.assertIn("git push origin main area/keeper", done.stdout)
        self.r.git(self.r.origin, "fetch", "-q", c, "main:main")   # a push, as origin sees it: fast-forward only
        self.assertIn("keeper: lead wip", self.r.subjects())

    def test_new_branch_from_main_and_prompt(self):
        c = self.r.clone("cai")
        res = self.r.area(c, "menus", "--agent", "none")
        self.assertEqual(res.returncode, 0, res.stderr)
        self.assertEqual(self.r.git(c, "symbolic-ref", "--short", "HEAD").stdout.strip(), "area/menus")
        p = self.r.area(c, "menus", "--prompt").stdout
        for want in ("HANDOFF.md", "docs/build/areas/menus.md", "Content/G/Maps/L_Title.umap", "--done"):
            self.assertIn(want, p)

    def test_done_refuses_shared_file_on_branch(self):
        c = self.r.clone("ben")
        self.r.area(c, "menus", "--agent", "none")
        self.r.write(c, "Config/DefaultEngine.ini", "[x]\nlead slipped\n")
        self.r.commit(c, "x", check=False)
        self.r.git(c, "commit", "-q", "--no-verify", "-am", "bypassed the guard")
        res = self.r.area(c, "menus", "--done")
        self.assertEqual(res.returncode, 1)
        self.assertIn("outside its lane: Config/DefaultEngine.ini", res.stderr)

    def test_push_race_rerun_done_fast_forwards(self):
        a, b = self.r.clone("ana"), self.r.clone("ben")
        for c, n, f in ((a, "keeper", "Source/G/Private/Owl/S.cpp"), (b, "menus", "Source/G/Private/Flow/T.cpp")):
            self.assertEqual(self.r.area(c, n, "--agent", "none").returncode, 0)
            self.r.write(c, f, "//\n")
            self.r.commit(c, n)
            self.assertEqual(self.r.area(c, n, "--done").returncode, 0)
        self.r.git(self.r.origin, "fetch", "-q", b, "main:main")
        self.assertNotEqual(self.r.git(self.r.origin, "fetch", "-q", a, "main:main", check=False).returncode, 0)
        again = self.r.area(a, "keeper", "--done")
        self.assertEqual(again.returncode, 0, again.stderr)
        self.r.git(self.r.origin, "fetch", "-q", a, "main:main")
        subj = self.r.subjects()
        self.assertIn("Merge area/keeper", subj)
        self.assertIn("Merge area/menus", subj)

    def test_status_lists_handoff_and_areas(self):
        c = self.r.clone("x")
        out = self.r.area(c).stdout
        self.assertIn("# Handoff", out)
        self.assertIn("keeper", out)
        self.assertIn("no branch yet", out)


@unittest.skipIf(os.name == "nt", "the stub worker and fake gh are sh scripts")
class DirectKickoff(unittest.TestCase):
    """tools/kickoff.py in a clone whose docs/build/MODE is direct: no gh call, areas built, merged, pushed."""

    def setUp(self):
        self.r = Repo()
        self.addCleanup(shutil.rmtree, self.r.base, True)
        self.c = self.r.clone("teammate")
        self.logdir = os.path.join(self.r.base, "log")
        os.makedirs(self.logdir)
        self.stub = os.path.join(self.r.base, "stub.py")
        with open(self.stub, "w") as fh:
            fh.write(STUB)
        bindir = os.path.join(self.r.base, "bin")
        os.makedirs(bindir)
        with open(os.path.join(bindir, "gh"), "w") as fh:   # any gh call is recorded: there must be none
            fh.write(f"#!/bin/sh\necho \"$@\" >> {self.logdir}/gh-calls\nexit 1\n")
        os.chmod(os.path.join(bindir, "gh"), 0o755)
        self.path = bindir + os.pathsep + os.environ.get("PATH", "")

    def kick(self, *args, **env):
        e = dict(self.r.env, PATH=self.path, LOGDIR=self.logdir, **env)
        cap = int(args[args.index("--parallel") + 1]) if "--parallel" in args else 0
        script = ("import sys; sys.path.insert(0, 'tools'); import direct_build; "
                  "sys.exit(direct_build.run(dry_run=%r, cap=%d))" % ("--dry-run" in args, cap))
        return subprocess.run([PY, "-c", script], cwd=self.c, capture_output=True, text=True, env=e)

    def worker(self, pre=""):
        """One command plays every worker: the stub reads its area from the branch name."""
        w = os.path.join(self.r.base, "worker.sh")
        with open(w, "w") as fh:
            fh.write(f"#!/bin/sh\n{pre}exec {PY} {self.stub} \"$(git symbolic-ref --short HEAD | sed 's|area/||')\" \"$@\"\n")
        os.chmod(w, 0o755)
        return w

    def test_direct_build_resumes_merges_pushes_updates_handoff(self):
        res = self.kick(KICKOFF_AGENT_CMD=self.worker())
        self.assertEqual(res.returncode, 0, res.stdout + res.stderr)
        self.assertIn("skip arena: held by Josh", res.stdout)
        self.assertFalse(os.path.exists(os.path.join(self.logdir, "gh-calls")), "gh was called")
        with open(os.path.join(self.logdir, "keeper.argv")) as fh:
            argv = fh.read()
        for want in ("-p", "bypassPermissions", "Bash(git push:*)", "Bash(gh:*)", "sonnet", "gameplay-dev"):
            self.assertIn(want, argv)
        subj = self.r.subjects()
        for want in ("Merge area/keeper", "Merge area/menus", "keeper: lead wip", "HANDOFF: keeper merged",
                     "keeper: worker changes (kickoff direct build)"):
            self.assertIn(want, subj)
        handoff = self.r.git(self.r.origin, "show", "main:HANDOFF.md").stdout
        self.assertRegex(handoff, r"\| keeper \| area/keeper \| free \| merged [0-9a-f]+ \|")
        self.assertIn("| arena | area/arena | Josh | in progress |", handoff)
        # Merged but not finished: the next run resumes keeper and menus again; AREA DONE marks it done.
        res = self.kick("--dry-run")
        self.assertIn("areas to build: keeper, menus", res.stdout)
        res = self.kick(KICKOFF_AGENT_CMD=self.worker("mkdir -p docs/build/areas; echo 'AREA DONE' >> "
                                                      "docs/build/areas/keeper-status.md\n"))
        self.assertEqual(res.returncode, 0, res.stdout + res.stderr)
        handoff = self.r.git(self.r.origin, "show", "main:HANDOFF.md").stdout
        self.assertRegex(handoff, r"\| keeper \| area/keeper \| free \| done \(merged [0-9a-f]+\) \|")
        self.assertIn("skip keeper", self.kick("--dry-run").stdout)

    def test_failing_gate_pushes_branch_only_and_records_it(self):
        res = self.kick(KICKOFF_AGENT_CMD=self.worker("touch FAILGATE\n"))
        self.assertEqual(res.returncode, 1, res.stdout)
        self.assertNotIn("Merge area/keeper", self.r.subjects())
        self.assertIn("keeper: worker changes", self.r.subjects("area/keeper"))   # the work is on origin
        handoff = self.r.git(self.r.origin, "show", "main:HANDOFF.md").stdout
        self.assertIn("gates failed", handoff)

    def test_branch_outside_its_lane_is_not_merged_and_handoff_says_why(self):
        pre = "echo x >> Config/DefaultEngine.ini; git commit -q --no-verify -am 'bypassed the guard'\n"
        res = self.kick(KICKOFF_AGENT_CMD=self.worker(pre))
        self.assertEqual(res.returncode, 1, res.stdout)
        self.assertNotIn("Merge area/keeper", self.r.subjects())
        handoff = self.r.git(self.r.origin, "show", "main:HANDOFF.md").stdout
        self.assertIn("| keeper | area/keeper | free | stopped: area/keeper changes files outside its lane: "
                      "Config/DefaultEngine.ini |", handoff)

    def test_stray_shared_file_is_stashed_not_committed(self):
        res = self.kick(KICKOFF_AGENT_CMD=self.worker(), STRAY="1")
        self.assertEqual(res.returncode, 0, res.stdout + res.stderr)
        self.assertIn("stashed changes outside the keeper lane", res.stdout)
        self.assertEqual(self.r.git(self.r.origin, "show", "main:Config/DefaultEngine.ini").stdout, "[x]\n")

    def overlap_peak(self, names):
        spans = []
        for n in names:
            with open(os.path.join(self.logdir, n + ".start")) as a, open(os.path.join(self.logdir, n + ".end")) as b:
                spans.append((float(a.read()), float(b.read())))
        return max(sum(1 for s0, e0 in spans if s0 <= s < e0) for s, _ in spans)

    def test_kickoff_mode_switch(self):
        sys.path.insert(0, os.path.join(ROOT, "tools"))
        import direct_build as d
        self.assertEqual(d.mode(self.c), "direct")
        mode_file = os.path.join(self.c, "docs/build/MODE")
        asked = []

        def ask(q):
            asked.append(q)
            return answers.pop(0)
        # MODE exists: never asked, the file wins; --mode overrides for one run.
        self.assertEqual(d.resolve_mode(self.c, ask=ask, tty=True, env={}, say=lambda m: None), "direct")
        self.assertEqual(d.resolve_mode(self.c, "cards", ask=ask, tty=True, env={}, say=lambda m: None), "cards")
        self.assertEqual(asked, [])
        os.remove(mode_file)
        # No MODE, no terminal (or CI): direct, no question, nothing saved.
        self.assertEqual(d.resolve_mode(self.c, ask=ask, tty=False, env={}, say=lambda m: None), "direct")
        self.assertEqual(d.resolve_mode(self.c, ask=ask, tty=True, env={"CI": "true"}, say=lambda m: None), "direct")
        self.assertEqual(asked, [])
        self.assertFalse(os.path.exists(mode_file))
        # No MODE on a terminal: one question; a wrong word asks again; the answer is saved.
        answers, said = ["maybe", "cards"], []
        self.assertEqual(d.resolve_mode(self.c, ask=ask, tty=True, env={}, say=said.append), "cards")
        self.assertEqual(len(asked), 2)
        self.assertIn("`cards`", asked[0])
        self.assertIn("[direct]", asked[0])
        with open(mode_file) as fh:
            self.assertEqual(fh.read(), "cards\n")
        self.assertIn("--mode cards|direct", said[-1])
        os.remove(mode_file)
        answers = [""]   # Enter = direct
        self.assertEqual(d.resolve_mode(self.c, ask=ask, tty=True, env={}, say=lambda m: None), "direct")
        with open(mode_file) as fh:
            self.assertEqual(fh.read(), "direct\n")
        with open(os.path.join(ROOT, "tools", "kickoff.py"), encoding="utf-8") as fh:
            src = fh.read()
        self.assertLess(src.index("direct_build.resolve_mode(ROOT, a.mode"), src.index("tester_prompt = read_prompt(a)"))

    def test_no_flag_runs_every_ready_area_at_once_and_cap_limits(self):
        extra = {f"a{i}": [f"Source/G/Private/a{i}/"] for i in range(1, 5)}
        for cap, want in ((0, 4), (2, 2)):
            r = Repo(extra)
            self.addCleanup(shutil.rmtree, r.base, True)
            self.r, self.c = r, r.clone("t")
            handoff = HANDOFF.replace("free | in progress | swoop", "free | done | -").replace(
                "free | not started", "free | done")
            r.write(self.c, "HANDOFF.md", handoff)
            r.commit(self.c, "only a1..a4 are ready")
            r.git(self.c, "push", "-q", "origin", "main")
            args = ("--parallel", str(cap)) if cap else ()
            res = self.kick(*args, KICKOFF_AGENT_CMD=self.worker(), WORK_S="3")
            self.assertEqual(res.returncode, 0, res.stdout + res.stderr)
            self.assertEqual(res.stdout.count("START area"), 4)
            self.assertEqual(self.overlap_peak(list(extra)), want, res.stdout)
            for n in extra:
                self.assertIn(f"Merge area/{n}", r.subjects())

    def test_overlapping_lanes_never_run_together(self):
        extra = {"b1": ["Source/G/Private/Shared/"], "b2": ["Source/G/Private/Shared/B2/"]}
        r = Repo(extra)
        self.addCleanup(shutil.rmtree, r.base, True)
        self.r, self.c = r, r.clone("t")
        r.write(self.c, "HANDOFF.md", HANDOFF.replace("free | in progress | swoop", "free | done | -").replace(
            "free | not started", "free | done"))
        r.commit(self.c, "only b1, b2")
        r.git(self.c, "push", "-q", "origin", "main")
        res = self.kick(KICKOFF_AGENT_CMD=self.worker(), WORK_S="2")
        self.assertEqual(self.overlap_peak(["b1", "b2"]), 1, res.stdout)

    def test_dry_run_plans_without_running(self):
        res = self.kick("--dry-run")
        self.assertEqual(res.returncode, 0, res.stdout + res.stderr)
        self.assertIn("areas to build: keeper, menus", res.stdout)
        self.assertEqual(self.r.git(self.c, "symbolic-ref", "--short", "HEAD").stdout.strip(), "main")


if __name__ == "__main__":
    unittest.main()


@unittest.skipIf(os.name == "nt", "pty is POSIX only")
class ModeQuestionOnATerminal(unittest.TestCase):
    """The real tools/kickoff.py in a full repo copy with no docs/build/MODE: on a terminal it asks once and saves the
    answer; piped (no terminal) it asks nothing and runs direct; with MODE saved it never asks again."""

    def setUp(self):
        sys.path.insert(0, HERE)
        import kickoff_sandbox as ks
        import test_honest_jam as thj
        self.sb = ks.KickoffSandbox(thj.PEOPLE)
        self.addCleanup(self.sb.close)
        os.remove(os.path.join(self.sb.repo, "docs", "build", "MODE"))
        self.sb.git("commit", "-q", "-am", "no MODE file")
        self.env = self.sb.env()
        for k in ("CI", "GITHUB_ACTIONS"):
            self.env.pop(k, None)

    def on_tty(self, answer):
        import pty
        import select
        pid, fd = pty.fork()
        if pid == 0:
            os.chdir(self.sb.repo)
            os.execve(PY, [PY, "tools/kickoff.py"], self.env)
        out, sent = b"", False
        while True:
            r, _, _ = select.select([fd], [], [], 60)
            if not r:
                break
            try:
                chunk = os.read(fd, 4096)
            except OSError:
                break
            if not chunk:
                break
            out += chunk
            if not sent and b"[direct]" in out:
                os.write(fd, answer.encode() + b"\n")
                sent = True
        os.waitpid(pid, 0)
        return out.decode("utf-8", "replace")

    def test_asks_on_a_terminal_saves_and_never_again(self):
        out = self.on_tty("")
        self.assertEqual(out.count("Run with the GitHub ceremonies"), 1, out)
        mode = os.path.join(self.sb.repo, "docs", "build", "MODE")
        with open(mode) as fh:
            self.assertEqual(fh.read(), "direct\n")
        self.assertIn("docs/build/MODE is direct", out)
        self.assertIn("no HANDOFF.md", out)   # direct mode ran; this repo has no build lead yet
        out = self.on_tty("cards")
        self.assertNotIn("Run with the GitHub ceremonies", out)

    def test_no_terminal_no_question(self):
        rc, out = self.sb.kickoff()
        self.assertNotIn("Run with the GitHub ceremonies", out)
        self.assertIn("docs/build/MODE is direct", out)
        self.assertFalse(os.path.exists(os.path.join(self.sb.repo, "docs", "build", "MODE")))
