#!/usr/bin/env python3
"""Pick the pipeline unit tests a change needs, inside a time budget. Stdlib only.

Card sessions (builder and reviewer) run this, never `unittest discover`: the full suite runs in the pipeline repos'
CI (.pipeline-ci-full). A selection aims at BUDGET seconds of test time (5 min, measured in tests/timings.json). The
budget picks tests; it never fails a run: a run over it prints one WARNING line and carries on.

How a changed path maps to test modules, nearest first:
  0  the test file itself; tests/test_<name>.py for tools/<name>.py; the docs tests (DOC_TESTS) for a doc
  1  a test that imports the changed tool or test helper, or names its path (`tools/kickoff.py`)
  2  a test that names a changed doc's path (`docs/decisions.md`), or a changed tool's file name (`kickoff.py`)
  3  a test that names only a doc's file name (`"decisions.md"`, often a sandbox copy list) or its folder
     (`pipeline/roles`), or imports a tool which imports the changed tool
Nearest first, then cheapest first, whole modules fill the budget. A module too slow to fit runs only its classes
that name the change, cheapest first, while they fit; the rest is listed as left for CI with its time.
Game files (Source/, Content/, Config/, ...) map to no Python test. A Source/ change maps to Unreal automation test
prefixes instead, printed as a `tools/ue/test.sh` line (never run here; the card's Unreal steps run it):
  Source/<Module>/{Public,Private}/<Area>/...   UmbrellaElla.<Area> (when a test has that name) plus the prefixes of
                                                every test file under Private/Tests/ that includes the changed header
  Source/<Module>/Private/Tests/<Area>/x.cpp    the prefixes of the test names in that file
  a test helper header (Tests/Shared/x.h)       the prefixes of the test files that include it
  *.Build.cs, *.Target.cs, a module's own file, or nothing found: the whole set, UmbrellaElla

Usage: python3 tools/affected_tests.py [FILE ...]          print the selection and the command (default files:
                                                            git diff origin/main...HEAD plus uncommitted changes)
       python3 tools/affected_tests.py --run [FILE ...]    run it, one unittest process per target, and print the time
       python3 tools/affected_tests.py --base REF          diff against REF instead of origin/main
       python3 tools/affected_tests.py --budget SECONDS    another budget (default 300)
       python3 tools/affected_tests.py --measure           time every module and class into tests/timings.json
                                                            (the full suite: pipeline repos only, never a card session)
       python3 tools/affected_tests.py --measure tests/test_x.py   time only that module (a new one) into the file
Exit 0 = nothing failed (time never fails), 1 = a selected test failed, 2 = usage error.
"""
import argparse
import ast
import json
import os
import re
import subprocess
import sys
import time

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TESTS = "tests"
TIMINGS = "tests/timings.json"
BUDGET = 300            # seconds of test time per card session (Josh, 12 Nov): a target, never a failure
DEFAULT_SECONDS = 15.0  # a module or class missing from tests/timings.json (a new test file)
DOC_EXT = {".md", ".txt", ".json", ".csv", ".yml", ".yaml", ".example", ""}
DOC_TESTS = ("test_doc_consistency",)   # reads the live docs and checks they agree
GAME_ROOTS = ("Art/", "Audio/", "Content/", "Source/", "Config/", "Plugins/", "Samples/", "scratch/", "Saved/",
              "Packaged/", "Binaries/", "Intermediate/", "DerivedDataCache/")
SKIP_PREFIX = ("MegaPipeline/", "dist/")   # generated: its sources carry the change
# Test classes that run the full suite themselves (a nested CI run on a sandbox clone): never in a card session
CI_ONLY = {"test_honest_jam.HonestJam": "runs the CI unit step (the full suite) on sandbox clones: CI only"}
UE_SOURCE = "Source/"
UE_ALL = "UmbrellaElla"                    # tools/ue/test.sh's default filter: every project test
UE_NAME = re.compile(r'"(UmbrellaElla\.[A-Z][A-Za-z0-9_]*)(?:\.[A-Za-z0-9_.]+)?"')   # first two parts of a test name
UE_INCLUDE = re.compile(r'^\s*#\s*include\s*"([^"]+)"', re.M)
UE_CODE = (".cpp", ".h", ".hpp", ".inl")


def read(path):
    try:
        with open(path, encoding="utf-8", errors="replace") as fh:
            return fh.read()
    except OSError:
        return ""


def test_modules(root):
    d = os.path.join(root, TESTS)
    return sorted(f[:-3] for f in os.listdir(d) if f.startswith("test") and f.endswith(".py")) if os.path.isdir(d) else []


def imports(text):
    """Top-level module names a Python file imports."""
    try:
        tree = ast.parse(text)
    except SyntaxError:
        return set()
    out = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            out.update(a.name.split(".")[0] for a in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module and not node.level:
            out.add(node.module.split(".")[0])
    return out


def classes(text):
    """[(class name, its source)] of the module's top-level test classes (a class with a test_* method)."""
    try:
        tree = ast.parse(text)
    except SyntaxError:
        return []
    lines = text.splitlines()
    return [(n.name, "\n".join(lines[n.lineno - 1:n.end_lineno])) for n in tree.body if isinstance(n, ast.ClassDef)
            and any(isinstance(f, (ast.FunctionDef, ast.AsyncFunctionDef)) and f.name.startswith("test")
                    for f in n.body)]


def needles(path):
    """Strings whose presence in a test's text means the test reads `path`."""
    base = os.path.basename(path)
    out = [path]
    if path.startswith(("tools/", "tests/")):
        out.append(base)                         # kickoff.py, build.sh
    if os.path.splitext(base)[1] or "." in base or base.isupper():
        for q in ('"', "'"):
            out.append(q + base + q)             # os.path.join(ROOT, "docs", "decisions.md")
    parent = os.path.dirname(path)
    if parent.count("/") >= 1:
        out.append(parent)                       # pipeline/roles
    return out


def mentions(text, path):
    return [n for n in needles(path) if n in text]


class Index:
    def __init__(self, root):
        self.root = root
        self.mods = test_modules(root)
        self.text = {m: read(os.path.join(root, TESTS, m + ".py")) for m in self.mods}
        self.imp = {m: imports(t) for m, t in self.text.items()}
        tdir = os.path.join(root, "tools")
        self.tools = {f[:-3] for f in os.listdir(tdir) if f.endswith(".py")} if os.path.isdir(tdir) else set()
        self.tool_imp = {t: imports(read(os.path.join(tdir, t + ".py"))) for t in self.tools}
        tm = read(os.path.join(root, TIMINGS))
        try:
            tm = json.loads(tm) if tm else {}
        except ValueError:
            tm = {}
        self.mod_time, self.cls_time = tm.get("modules", {}), tm.get("classes", {})

    def seconds(self, target):
        mod = target.split(".")[0]
        if "." in target:
            return float(self.cls_time.get(target, DEFAULT_SECONDS))
        return float(self.mod_time.get(mod, DEFAULT_SECONDS))

    def hits(self, path):
        """{module: (tier, why, [needles])} for one changed path."""
        out = {}

        def add(mod, tier, why, keys):
            if mod in self.text and (mod not in out or tier < out[mod][0]):
                out[mod] = (tier, why, keys)

        stem, ext = os.path.splitext(os.path.basename(path))
        if path.startswith(GAME_ROOTS) or path.startswith(SKIP_PREFIX):
            return out
        if path.startswith(TESTS + "/") and ext == ".py":
            if stem in self.text:
                add(stem, 0, "changed test", [])
            else:   # a helper (hermetic, kickoff_sandbox): the tests that import it
                for m in self.mods:
                    if stem in self.imp[m]:
                        add(m, 1, f"imports {stem}", [stem])
            return out
        if path.startswith("tools/") and ext == ".py" and stem in self.tools:
            add("test_" + stem, 0, f"tests {path}", [stem, path])
            for m in self.mods:
                if stem in self.imp[m]:
                    add(m, 1, f"imports {stem}", [stem + ".", stem + ".py", path])
            users = {t for t, imp in self.tool_imp.items() if stem in imp and t != stem}
            for m in self.mods:
                via = sorted(users & self.imp[m])
                if via:
                    add(m, 3, f"imports {via[0]}, which imports {stem}", [stem, via[0] + "."])
        if ext in DOC_EXT and not path.startswith(("tools/", "tests/")):
            for m in DOC_TESTS:
                add(m, 0, "docs test", [path])
        code = path.startswith(("tools/", "tests/"))
        for m in self.mods:
            keys = mentions(self.text[m], path)
            if not keys:
                continue
            if path in keys:      # the whole path: a tool 1, a doc 2
                tier = 1 if code else 2
            elif keys == [os.path.dirname(path)]:
                tier = 3          # only its folder
            else:                 # its file name (a sandbox copy list, os.path.join pieces)
                tier = 2 if code else 3
            add(m, tier, f"names {keys[0].strip(chr(34) + chr(39))}", keys)
        return out

    def relevant_classes(self, mod, keys):
        found = []
        for name, src in classes(self.text[mod]):
            if not keys or any(k in src for k in keys):
                found.append(f"{mod}.{name}")
        return found


class Unreal:
    """The project's automation test files: Source/<Module>/Private/Tests/**, their test-name prefixes and includes."""

    def __init__(self, root):
        self.tests = {}   # repo path -> (prefixes, includes)
        src = os.path.join(root, UE_SOURCE)
        for d, dirs, files in os.walk(src):
            dirs[:] = sorted(x for x in dirs if x not in ("Intermediate", "Binaries"))
            rel_dir = os.path.relpath(d, root).replace(os.sep, "/")
            parts = rel_dir.split("/")
            if len(parts) < 4 or parts[2:4] != ["Private", "Tests"]:
                continue
            for f in sorted(files):
                if f.endswith(UE_CODE):
                    text = read(os.path.join(d, f))
                    self.tests[rel_dir + "/" + f] = (set(UE_NAME.findall(text)), set(UE_INCLUDE.findall(text)))
        self.known = set().union(*(p for p, _ in self.tests.values())) if self.tests else set()

    def includers(self, header):
        """Prefixes of the test files that include `header` (as written after Public/ or Private/)."""
        out = set()
        for p, inc in self.tests.values():
            if any(i == header or i.endswith("/" + header) for i in inc):
                out |= p
        return out

    def prefixes(self, path):
        """(sorted prefixes, why) for one changed path; ([], "") when it is not Unreal C++."""
        if not path.startswith(UE_SOURCE):
            return [], ""
        parts = path.split("/")
        name = parts[-1]
        if name.endswith((".Build.cs", ".Target.cs")) or len(parts) < 5 or parts[2] not in ("Public", "Private"):
            return [UE_ALL], "build file or module file: every project test"
        if parts[2:4] == ["Private", "Tests"]:
            own = self.tests.get(path, (set(), set()))[0]
            via = self.includers("/".join(parts[3:])) if name.endswith((".h", ".hpp", ".inl")) else set()
            got = own | via
            if got:
                return sorted(got), "test names in it" if own else "test files that include it"
            area = parts[4] if len(parts) > 5 else ""
            if area and f"{UE_ALL}.{area}" in self.known:
                return [f"{UE_ALL}.{area}"], f"tests of area {area}"
            return [UE_ALL], "no test file names it: every project test"
        area = parts[3] if len(parts) > 4 else ""
        if not area or not name.endswith(UE_CODE):
            return [UE_ALL], "no area folder: every project test"
        header = "/".join(parts[3:-1] + [os.path.splitext(name)[0] + ".h"])
        got = self.includers(header)
        if f"{UE_ALL}.{area}" in self.known:
            got.add(f"{UE_ALL}.{area}")
        if not got:
            return [UE_ALL], f"no test includes {header} or is named {UE_ALL}.{area}: every project test"
        return sorted(got), f"area {area} and the tests that include {header}"


def ue_filter(prefixes):
    """The RunTests filter: a + list (ue_run.py shuffle uses the same form), or the whole set."""
    return UE_ALL if UE_ALL in prefixes else "+".join(sorted(prefixes))


def ue_commands(prefixes):
    f = ue_filter(prefixes)
    return f"TEST_FILTER='{f}' tools/ue/test.sh", f"tools\\ue\\test.ps1 -Filter '{f}'"


def unreal_select(ue, paths):
    """{changed Source/ path: (prefixes, why)}."""
    out = {}
    for p in paths:
        pre, why = ue.prefixes(p)
        if pre:
            out[p] = (pre, why)
    return out


def select(index, paths, budget=BUDGET):
    """(picked [(target, seconds, why)], left [(target, seconds, why)], unmapped paths)."""
    best = {}   # module -> (tier, why, keys)
    unmapped = []
    for p in paths:
        h = index.hits(p)
        if not h:
            unmapped.append(p)
        for m, (tier, why, keys) in h.items():
            if m not in best or tier < best[m][0]:
                best[m] = (tier, why, list(keys))
            elif tier == best[m][0]:
                best[m][2].extend(k for k in keys if k not in best[m][2])
    order = sorted(best, key=lambda m: (best[m][0], index.seconds(m), m))
    picked, left, spent = [], [], 0.0
    for m in order:
        tier, why, keys = best[m]
        s = index.seconds(m)
        ci_only = [c for c in CI_ONLY if c.split(".")[0] == m]
        for c in ci_only:
            left.append((c, index.seconds(c), f"{why}; {CI_ONLY[c]}"))
        if not ci_only and spent + s <= budget:
            picked.append((m, s, why))
            spent += s
            continue
        cls = sorted((c for c in index.relevant_classes(m, keys) if c not in CI_ONLY),
                     key=lambda c: (index.seconds(c), c))
        took = []
        for c in cls:
            cs = index.seconds(c)
            if spent + cs <= budget:
                picked.append((c, cs, f"{why}; class names the change ({m} is {s:.0f} s whole)"))
                spent += cs
                took.append(c)
        rest = [c for c in cls if c not in took]
        if not took:
            left.append((m, s, f"{why}; {s:.0f} s whole, no class that names the change fits"))
        elif rest:
            left.append((m, sum(index.seconds(c) for c in rest), f"{len(rest)} more class(es) of {m}"))
    return picked, left, unmapped


def changed_files(root, base):
    out = []
    for args in (["diff", "--name-only", f"{base}...HEAD"], ["diff", "--name-only", "HEAD"],
                 ["ls-files", "--others", "--exclude-standard"]):
        p = subprocess.run(["git"] + args, cwd=root, capture_output=True, text=True)
        if p.returncode == 0:
            out += [ln.strip() for ln in p.stdout.splitlines() if ln.strip()]
        elif args[1] == "--name-only" and "..." in args[2]:
            print(f"affected_tests: git diff {base}...HEAD failed ({p.stderr.strip()[:120]}); pass the files instead",
                  file=sys.stderr)
    return sorted(set(out))


def norm(root, f):
    """A repo-relative posix path from what a person typed (absolute, ./x, x\\y)."""
    f = os.path.relpath(f, root) if os.path.isabs(f) else f
    f = f.replace(os.sep, "/").replace("\\", "/")
    while f.startswith("./"):
        f = f[2:]
    return f


def command(targets):
    return "python3 -m unittest " + " ".join(f"{TESTS}.{t}" for t in targets)


def run(root, picked, budget):
    """Run each target in its own process; print the time. Over the budget = one WARNING line, never a failure."""
    took, rc = {}, 0
    t0 = time.time()
    for target, _, _ in picked:
        s = time.time()
        p = subprocess.run([sys.executable, "-m", "unittest", f"{TESTS}.{target}"], cwd=root)
        took[target] = time.time() - s
        rc = rc or (1 if p.returncode else 0)
    total = time.time() - t0
    if picked:
        slow = max(took, key=took.get)
        if total > budget:
            print(f"affected_tests: WARNING ran {total:.0f} s, over the {budget} s target; slowest {slow} "
                  f"{took[slow]:.0f} s (carrying on)")
        else:
            print(f"affected_tests: ran {len(picked)} target(s) in {total:.0f} s (target {budget} s); "
                  f"slowest {slow} {took[slow]:.0f} s; {'FAILED' if rc else 'OK'}")
    return rc


def measure(root, only=()):
    """Time test modules and their classes into tests/timings.json: every module (the full suite, once; pipeline
    repos only, never a card session), or only the named ones, merged into the file (a new test module)."""
    import unittest
    if not only and os.environ.get("JAM_KICKOFF") == "1":
        print("affected_tests: --measure without modules runs the full suite; card sessions never do", file=sys.stderr)
        return 2
    sys.path.insert(0, os.path.join(root, TESTS))
    res = {"note": "seconds per test module and class, from tools/affected_tests.py --measure", "modules": {},
           "classes": {}}
    if only:
        try:
            with open(os.path.join(root, TIMINGS), encoding="utf-8") as fh:
                res.update(json.load(fh))
        except (OSError, ValueError):
            pass
    mods = [os.path.splitext(os.path.basename(m))[0] for m in only] or test_modules(root)
    for mod in mods:
        res["classes"] = {k: v for k, v in res["classes"].items() if k.split(".")[0] != mod}
        suite = unittest.defaultTestLoader.loadTestsFromName(mod)
        by_class = {}

        def leaves(s):
            for x in s:
                yield from (leaves(x) if isinstance(x, unittest.TestSuite) else [x])
        for t in leaves(suite):
            by_class.setdefault(type(t).__name__, []).append(t)
        m0 = time.time()
        for cls, ts in by_class.items():
            c0 = time.time()
            unittest.TestSuite(ts).run(unittest.TestResult())
            res["classes"][f"{mod}.{cls}"] = round(time.time() - c0, 2)
        res["modules"][mod] = round(time.time() - m0, 2)
        print(f"{mod} {res['modules'][mod]:.1f} s", flush=True)
    res["modules"] = dict(sorted(res["modules"].items()))
    with open(os.path.join(root, TIMINGS), "w", encoding="utf-8") as fh:
        json.dump(res, fh, indent=1, sort_keys=True)
        fh.write("\n")
    return 0


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("files", nargs="*")
    ap.add_argument("--root", default=ROOT)
    ap.add_argument("--base", default="origin/main")
    ap.add_argument("--budget", type=float, default=BUDGET)
    ap.add_argument("--run", action="store_true")
    ap.add_argument("--measure", action="store_true")
    a = ap.parse_args(argv)
    if a.measure:
        return measure(a.root, a.files)
    paths = [norm(a.root, f) for f in a.files] or changed_files(a.root, a.base)
    index = Index(a.root)
    picked, left, unmapped = select(index, paths, a.budget)
    ue = unreal_select(Unreal(a.root), paths)
    unmapped = [p for p in unmapped if p not in ue]
    est = sum(s for _, s, _ in picked)
    print(f"affected_tests: {len(paths)} changed file(s); {len(picked)} target(s), about {est:.0f} s "
          f"(target {a.budget:.0f} s); always also run python3 tools/pipeline_check.py")
    for t, s, why in picked:
        print(f"  RUN  {TESTS}.{t}  {s:.0f} s  ({why})")
    for t, s, why in left:
        print(f"  CI   {TESTS}.{t}  {s:.0f} s  ({why}; the full suite runs in the pipeline repos' CI)")
    if ue:
        for p, (pre, why) in sorted(ue.items()):
            print(f"  UE   {p}: {', '.join(pre)} ({why})")
        mac, win = ue_commands(set().union(*(set(pre) for pre, _ in ue.values())))
        print(f"unreal (the card's Unreal step; not run here): {mac}   Windows: {win}")
    if unmapped:
        print("  no Python test reads: " + ", ".join(unmapped[:8]) + (" ..." if len(unmapped) > 8 else ""))
    if not picked:
        print("affected_tests: no unit test to run")
        return 0
    if not a.run:
        print(command([t for t, _, _ in picked]))
        return 0
    return run(a.root, picked, a.budget)


if __name__ == "__main__":
    sys.exit(main())
