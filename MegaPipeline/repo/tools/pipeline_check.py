#!/usr/bin/env python3
"""Repository guardrails for the jam pipeline. Stdlib only; runs locally and in CI.

Checks (each one exists because of a finding in docs/audit.md):
  leak        text from another project or another engine (Unity) in pipeline/docs/code
  forbidden   Unreal build output or IDE junk committed (Binaries/, Intermediate/, ...)
  lfs         binary assets (.uasset, .umap, .png, .wav, ...) not routed through Git LFS
  size        large non-LFS files
  budget      always-loaded agent context over its word budget
  roles       role cards missing a required section (owns / inputs / outputs / done / never)
  hygiene     in Source/ and Config/ (skipped while absent; pipeline/checklists/file-hygiene.md):
              a TODO without a card or decision id (`TODO(UE-12)`, `TODO(D-new-port-4)` are fine),
              `#pragma warning(disable` or PRAGMA_DISABLE_*_WARNINGS without a decision row on that line
              (AGENTS.md section 7), and any `ROLE:` line (pipeline text in shipped code)
  placeholder `_PH` asset names (D-new-port-8) in Source/, Config/ and Content/ paths. Reported as a note
              during the jam; a problem with --release (the submission build, G4)
  private     names of private projects, tools and personal paths (describe a practice on its own merits)
  consistency cross-doc references (so docs cannot drift apart): a decision ID (D<n>, D-new-..., GDD B DEC-nn) with no row in docs/decisions.md,
              a Day-0 card ID not in pipeline/day0-cards.md, a repo path that does not exist (and is not a planned
              output in a Day-0 lane; case must match exactly, as on the Linux CI runner), a decision owner that is not a People row, person or role in
              docs/jam-brief.md / AGENTS.md, a cycle in the Day-0 "After" column, and a Day-0 row a person owns or a
              person's step outside a true checkpoint (check_card.day0_owner_problems, pipeline/human-checkpoints.md)
  repomap     docs/repo-map.md (tools/repo_map.py): a pipeline folder the installer ships is missing from it, or its
              "Pipeline folders" section names a path that does not exist. Team folders never fail it; skipped while
              the map is absent
  package     MegaPipeline/ is stale, hand-edited, or a repo doc lands in no package file (pipeline repos only, not an
              installed game repo; tools/export_package.py --check;
              skipped while MegaPipeline/ is absent)
Also prints the total size of LFS-tracked files (from the pointers; nothing is downloaded).

Usage: python3 tools/pipeline_check.py [--root PATH] [--release]
Exit 0 = clean, 1 = violations found.
"""
import argparse
import hashlib
import os
import re
import subprocess
import sys

LEAK_TERMS = [
    # The inherited pipeline's other project. These must never steer a jam agent.
    r"liquid\s*neon", r"puro\s*b[uú]ho", r"bartender", r"restaurant", r"hospitality",
    r"\bvenue\b", r"cocktail",
    # Unity concepts that have no meaning in this Unreal project.
    r"monobehaviou?r", r"scriptableobject", r"\basmdef\b",
    r"unityengine", r"\bplaymode\b", r"\beditmode\b", r"unity test framework",
    r"\.unity\b", r"\bprefab", r"\bchatgpt project instructions\b",
]
# Private references: names of other projects and private tools, plus personal paths. These apply everywhere,
# including docs/audit.md, eval cases and fixtures. Names are stored only as short SHA-256 hashes of the
# lower-case name with spaces and punctuation removed, so this file never spells them out. A name may be
# allowed after one specific word (e.g. Epic's own tool name), via PRIVATE_ALLOW_PREV.
PRIVATE_HASHES = {
    "fe8461233d1af720", "032b7782dc7b0e2c", "0d7b01056c6dfd00", "ff527fa9fad1fb3a", "5bcb80d0681d6b5e",
    "c96b07843732d2be", "40405d142c617ce4", "92a95fc2e5b06544", "6d7de70ba07f9b69", "8616136a81acd2a0",
    # names of the inherited pipeline's author (first name, handle, surname forms)
    "5d7f15f2fce8ddb2", "0963d346c518c2d9", "0335aa820af252db", "36b95dd06dd2e5df", "1770dd5b1a104300",
}
PRIVATE_ALLOW_PREV = {"fe8461233d1af720": "unreal"}
PRIVATE_PATHS = [r"~/desktop", r"/users/(?!shared/)[a-z]", r"c:\\users\\"]
PRIVATE_MAX_WORDS = 3


def _h(text):
    return hashlib.sha256(text.encode()).hexdigest()[:16]


def private_hit(line, hashes=None, allow_prev=None, paths_re=None):
    """Return the offending text if the line names a private term or a personal path, else None."""
    hashes = PRIVATE_HASHES if hashes is None else hashes
    allow_prev = PRIVATE_ALLOW_PREV if allow_prev is None else allow_prev
    paths_re = paths_re or re.compile("|".join(PRIVATE_PATHS), re.IGNORECASE)
    m = paths_re.search(line)
    if m:
        return m.group(0)
    words_ = re.findall(r"[a-z0-9]+", line.lower())
    for i in range(len(words_)):
        for n in range(1, PRIVATE_MAX_WORDS + 1):
            if i + n > len(words_):
                break
            h = _h("".join(words_[i:i + n]))
            if h in hashes:
                prev = words_[i - 1] if i > 0 else ""
                if allow_prev.get(h) == prev:
                    continue
                return " ".join(words_[i:i + n])
    return None


PRIVATE_ALLOW = {"tools/pipeline_check.py"}
PRIVATE_EXT = {".diff", ".patch", ".csv", ".html"}
# Files that are allowed to name the terms because they discuss or detect them.
LEAK_ALLOW = {
    "docs/audit.md",
    "tools/pipeline_check.py",
    "tests/test_pipeline_check.py",
    "evals/README.md",
    "MegaPipeline/Reference/Pipeline Audit.md",  # generated copy of docs/audit.md
}
LEAK_ALLOW_PREFIXES = ("evals/reviewer/cases/", "tests/fixtures/")
# Terms that are the game's own names in its C++ code (EUmbrellaPlayMode, a PlayMode member): checked everywhere else.
LEAK_CODE_OK = {r"\bplaymode\b"}
LEAK_CODE_DIRS = ("Source/",)
TEXT_EXT = {".md", ".txt", ".h", ".hpp", ".cpp", ".cs", ".ini", ".json", ".yml", ".yaml", ".py", ".sh", ".ps1", ".bat", ".uproject", ".uplugin"}

FORBIDDEN_DIRS = ("Binaries/", "Intermediate/", "Saved/", "DerivedDataCache/", ".vs/", ".idea/", "Build/Windows/", "Build/Mac/")
FORBIDDEN_SUFFIX = (".generated.h", ".gen.cpp", ".sln", ".xcworkspace", ".pdb", ".obj", ".dll", ".dylib", ".exe")

LFS_EXT = {".uasset", ".umap", ".png", ".jpg", ".jpeg", ".psd", ".ase", ".aseprite", ".kra", ".tga", ".exr",
           ".wav", ".mp3", ".ogg", ".flac", ".fbx", ".blend", ".mp4", ".mov", ".ttf", ".otf", ".zip", ".pdf"}
MAX_NON_LFS_BYTES = 2 * 1024 * 1024

# Word budgets. Rick's review measured the inherited pipeline at ~78k words; agents should load
# a few thousand words per task, not the whole library.
BUDGETS = {
    "AGENTS.md": 1800,
    "docs/jam-brief.md": 1200,
    "docs/repo-map.md": 700,   # read second, by every agent (AGENTS.md section 1)
}
# Fill-in tables card 0.0 completes (People, Team hours, Clock) are team data, not prose agents read: their table
# rows do not count against the brief's budget, so the required fill never turns CI red (dry run A H2).
BUDGET_DATA_TABLES = {"docs/jam-brief.md": ("## Clock", "## People", "## Team hours")}
ROLE_DIR = "pipeline/roles/"
ROLE_BUDGET = 1100
ROLE_SECTIONS = ["## Owns", "## Inputs", "## Outputs", "## Done when", "## Never"]

HYGIENE_DIRS = ("Source/", "Config/")
HYGIENE_EXT = {".h", ".hpp", ".inl", ".cpp", ".cs", ".ini"}
DECISION_ID = r"\bD(?:-new-[\w-]+|\d+)\b"
BARE_TODO = re.compile(r"\bTODO\b(?!\s*\((?:UE-\d+(?:\.\d+)?|D(?:-new-[\w-]+|\d+))\))")
WARN_PRAGMA = re.compile(r"#\s*pragma\s+warning\s*\(\s*disable|\bPRAGMA_DISABLE_\w*WARNINGS\b")
ROLE_LINE = re.compile(r"\bROLE:")
PLACEHOLDER = re.compile(r"_PH\b")
PLACEHOLDER_DIRS = ("Source/", "Config/", "Content/")


# An installed repo (MegaPipeline/install.sh copied the pipeline to the root) keeps the shipped package: a copy of the
# source repo, its tests and the installer. They are checked where they are made, so here they are skipped. Same list
# as tools/export_package.py (INSTALLED, SHIPPED_DIRS, SHIPPED_FILES).
INSTALLED = ".pipeline-installed.json"
SHIPPED_DIRS = ("MegaPipeline/repo/", "MegaPipeline/tests/")
SHIPPED_FILES = {"MegaPipeline/install.py", "MegaPipeline/install.sh", "MegaPipeline/install.ps1",
                 "MegaPipeline/manifest.json", "MegaPipeline/INSTALL.md"}


# CI profile (pipeline/agent-ops/README.md): this root marker turns on the long pipeline suites in pipeline-checks.yml.
# Only the pipeline repos keep it; a shipped copy would run them in every game repo, so it fails here.
CI_FULL = ".pipeline-ci-full"


def installed(root):
    return os.path.isfile(os.path.join(root, INSTALLED)) or os.path.isdir(os.path.join(root, "MegaPipeline", "repo"))


def shipped(rel):
    return rel.startswith(SHIPPED_DIRS) or rel in SHIPPED_FILES


def git_files(root):
    out = subprocess.run(["git", "ls-files", "-z"], cwd=root, capture_output=True, check=True).stdout
    return [p for p in out.decode().split("\0") if p]


def untracked_files(root):
    """New files not yet added (and not ignored). Scanned for text checks only, so a doc is checked before `git add`."""
    out = subprocess.run(["git", "ls-files", "-o", "--exclude-standard", "-z"], cwd=root, capture_output=True, check=True).stdout
    return [p for p in out.decode().split("\0") if p]


def lfs_tracked(root, paths):
    if not paths:
        return set()
    proc = subprocess.run(["git", "check-attr", "filter", "--stdin", "-z"], cwd=root,
                          input="\0".join(paths).encode(), capture_output=True, check=True)
    parts = proc.stdout.decode().split("\0")
    tracked = set()
    for i in range(0, len(parts) - 2, 3):
        if parts[i + 2] == "lfs":
            tracked.add(parts[i])
    return tracked


def read_text(path):
    with open(path, encoding="utf-8", errors="replace") as fh:
        return fh.read()


def index_blob_heads(root, paths, limit=64):
    """Return {path: first bytes of the staged blob}. A real LFS file is stored as a small
    text pointer; a raw binary here means it bypassed LFS even if .gitattributes matches."""
    if not paths:
        return {}
    ls = subprocess.run(["git", "ls-files", "-s", "-z", "--"] + paths, cwd=root, capture_output=True, check=True).stdout.decode()
    shas = {}
    for entry in ls.split("\0"):
        if not entry:
            continue
        meta, path = entry.split("\t", 1)
        shas[path] = meta.split()[1]
    proc = subprocess.run(["git", "cat-file", "--batch"], cwd=root, input="".join(v + "\n" for v in shas.values()).encode(),
                          capture_output=True, check=True).stdout
    heads, pos = {}, 0
    for path, sha in shas.items():
        nl = proc.index(b"\n", pos)
        header = proc[pos:nl].split()
        size = int(header[2])
        heads[path] = proc[nl + 1:nl + 1 + min(size, limit)]
        pos = nl + 1 + size + 1
    return heads


def budget_words(path, text):
    """Words that count against a budget: all of them, minus the table rows of BUDGET_DATA_TABLES sections."""
    heads, skip, keep = BUDGET_DATA_TABLES.get(path, ()), False, []
    for ln in text.splitlines():
        if ln.startswith("#"):
            skip = ln.startswith(heads) if heads else False
        if skip and ln.lstrip().startswith("|"):
            continue
        keep.append(ln)
    return words("\n".join(keep))


def words(text):
    return len(re.findall(r"\S+", text))


def hygiene(root, files, release=False):
    """Problems and notes from Source/ and Config/ text, plus _PH placeholder names."""
    problems, notes = [], []
    for f in files:
        if f.startswith(PLACEHOLDER_DIRS) and PLACEHOLDER.search(os.path.basename(os.path.splitext(f)[0])):
            (problems if release else notes).append(("placeholder", f, "_PH placeholder asset (D-new-port-8)"))
        if not f.startswith(HYGIENE_DIRS) or os.path.splitext(f)[1].lower() not in HYGIENE_EXT:
            continue
        try:
            text = read_text(os.path.join(root, f))
        except OSError:
            continue
        for n, line in enumerate(text.splitlines(), 1):
            where = f"{f}:{n}"
            if BARE_TODO.search(line):
                problems.append(("hygiene", where, "TODO without a card or decision id; write TODO(UE-<id>)"))
            if WARN_PRAGMA.search(line) and not re.search(DECISION_ID, line):
                problems.append(("hygiene", where, "warning disabled without a decision row on the same line (AGENTS.md section 7)"))
            if ROLE_LINE.search(line):
                problems.append(("hygiene", where, "'ROLE:' is pipeline text; it never goes in shipped code or config"))
            if PLACEHOLDER.search(line):
                (problems if release else notes).append(("placeholder", where, "_PH placeholder asset referenced (D-new-port-8)"))
    return problems, notes


# ---- consistency gate -------------------------------------------------------------------------
DECISIONS = "docs/decisions.md"
DAY0 = "pipeline/day0-cards.md"
BRIEF = "docs/jam-brief.md"
CONSIST_EXT = {".md", ".json", ".csv", ".yml", ".yaml", ".py", ".ps1", ".sh", ".txt"}
# Not scanned: tests and fixtures plant bad IDs on purpose; eval cases and runs are synthetic.
CONSIST_SKIP = ("tests/", "evals/reviewer/cases/", "evals/reviewer/runs/")
DEC_REF = re.compile(r"(?<![\w-])D(?:EC-\d{2}|-new-[A-Za-z0-9]+(?:-[A-Za-z0-9]+)*|\d+)\b")  # DEC-nn: GDD B §13 rows
CARD_ID = r"0\.\d{1,2}[a-z]?"
CARD_REF = re.compile(r"\b[Cc]ards?\s+(" + CARD_ID + r"(?:\s*(?:,|and|or|/|then|->|→)\s*" + CARD_ID + r")*)\b")
CARD_LETTER = re.compile(r"(?<![\w.])(0\.\d{1,2}[a-e])\b")  # 0.4c, 0.6b: never a plain number
PATH_REF = re.compile(r"(?<![\w./-])((?:docs|pipeline|tools|tests|evals|prompts|\.github)/[\w./-]*[\w/])")
PATH_SKIP = re.compile(r"[*<>{}]|NAME|\.\.\.|/$")
PATH_TEMPLATE_TAIL = re.compile(r"[\w.-]*[*<{]")  # `tools/ue/test.*`, `prompts/log/D-<host>.md`
# Files only a game repo has: the build mode kickoff saves on its first run and the build lead's gate list
# (README "Build modes"). Docs may name them before they exist.
GAME_REPO_PATHS = {"docs/build/MODE", "docs/build/gates.txt"}


def table_cells(line):
    return [c.strip() for c in line.strip().strip("|").split("|")]


def decision_rows(text):
    """{id: owner} for every table row whose first cell is a decision ID. Owner is '' if the table has no Owner column."""
    rows, owner_col = {}, None
    for line in text.splitlines():
        if not line.strip().startswith("|"):
            owner_col = None if not line.strip() else owner_col
            continue
        cells = table_cells(line)
        if cells and cells[0] == "ID":
            owner_col = cells.index("Owner") if "Owner" in cells else None
            continue
        if cells and DEC_REF.fullmatch(cells[0]):
            rows[cells[0]] = cells[owner_col] if owner_col is not None and owner_col < len(cells) else ""
    return rows


def day0_rows(text):
    """{card id: (after ids, lane cell)} from the Day-0 table."""
    out = {}
    for line in text.splitlines():
        cells = table_cells(line) if line.startswith("| ") else []
        if len(cells) >= 6 and re.fullmatch(CARD_ID, cells[0]):
            after = re.findall(CARD_ID, cells[5])
            out[cells[0]] = (after, cells[4])
    return out


def owner_names(brief, agents):
    """Accepted owner names: People seats and persons in the brief, and AGENTS.md roles."""
    names = set()
    sec = re.search(r"^## People.*?$(.*?)(?=^## |\Z)", brief, re.S | re.M)
    for line in (sec.group(1) if sec else "").splitlines():
        if not line.startswith("|"):
            continue
        cells = table_cells(line)
        if not cells or set(cells[0]) <= set("-: ") or cells[0] == "Role":
            continue
        names.add(norm_owner(cells[0]))
        names.add(norm_owner(re.split(r"\s*[/,]\s*", cells[0])[0]))
        if len(cells) > 1:
            for n in re.split(r",|/|\band\b", re.sub(r"\(.*?\)", "", cells[1])):
                if n.strip() and not n.strip().upper().startswith("TBD"):
                    names.add(norm_owner(n))
    sec = re.search(r"^## 3\. Roles.*?$(.*?)(?=^## |\Z)", agents, re.S | re.M)
    for line in (sec.group(1) if sec else "").splitlines():
        cells = table_cells(line) if line.startswith("|") else []
        if cells and cells[0] not in ("Role",) and not set(cells[0]) <= set("-: "):
            names.add(norm_owner(cells[0]))
    names.discard("")
    return names


def norm_owner(cell):
    return re.sub(r"\s+", " ", re.sub(r"\(.*?\)|\*", "", cell)).strip().lower()


def day0_cycle(rows):
    """One cycle in the After graph as a list of ids, or None."""
    state = {}

    def visit(n, stack):
        state[n] = 1
        for m in rows.get(n, ([], ""))[0]:
            if state.get(m) == 1:
                return stack[stack.index(m):] + [m] if m in stack else [n, m]
            if m in rows and not state.get(m) and (c := visit(m, stack + [m])):
                return c
        state[n] = 2
        return None

    for n in rows:
        if not state.get(n) and (c := visit(n, [n])):
            return c
    return None


def exists_exact(root, rel):
    """os.path.exists with exact case on every part, so a wrong-case path fails on macOS and Windows
    as it does on the Linux CI runner."""
    cur = root
    for part in [p for p in rel.split("/") if p not in ("", ".")]:
        try:
            names = os.listdir(cur)
        except OSError:
            return False
        if part not in names:
            return False
        cur = os.path.join(cur, part)
    return True


def consistency(root, files):
    """Problems from cross-doc references. `files` are repo-relative paths."""
    def rd(rel):
        try:
            return read_text(os.path.join(root, rel))
        except OSError:
            return ""
    problems = []
    decisions = decision_rows(rd(DECISIONS))
    day0 = day0_rows(rd(DAY0))
    planned = set()
    # final-11 A M1: a `|` inside a cell (a grep in a code span) cuts the row short on GitHub and in every parser
    for n, line in enumerate(rd(DAY0).splitlines(), 1):
        if re.match(r"^\| 0\.\d+[a-z]? \|", line) and len(table_cells(line)) != 7:
            problems.append(("consistency", f"{DAY0}:{n}", f"Day-0 row has {len(table_cells(line))} cells, not 7: "
                             "a `|` inside a cell splits it; write the command without one"))
    for _, lane in day0.values():
        planned.update(m.group(1) for m in PATH_REF.finditer(lane))
    # direct local build: a path in an area card's "File lane" (docs/build/areas/<area>.md) is a planned output of that
    # area branch; it reaches main when the build lead merges the area
    for f in files:
        if re.fullmatch(r"docs/build/areas/[\w-]+\.md", f) and not f.endswith("-status.md"):
            lane = re.search(r"(?ms)^## File lane[^\n]*\n(.*?)(?=^## |\Z)", rd(f))
            if lane:
                planned.update(m.group(1).rstrip(".") for m in PATH_REF.finditer(lane.group(1)))
    planned |= GAME_REPO_PATHS
    owners = owner_names(rd(BRIEF), rd("AGENTS.md"))
    for did, owner in sorted(decisions.items()):
        if owner and norm_owner(owner) not in owners and norm_owner(owner) not in ("none", "–", "-"):
            problems.append(("consistency", f"{DECISIONS} {did}", f"owner '{owner}' is not a People seat, person or role in {BRIEF} / AGENTS.md"))
    for cid, (after, _) in sorted(day0.items()):
        for a in after:
            if a not in day0:
                problems.append(("consistency", f"{DAY0} {cid}", f"card {a} is not in {DAY0}"))
    cyc = day0_cycle(day0)
    if cyc:
        problems.append(("consistency", DAY0, "Day-0 'After' cycle: " + " -> ".join(cyc)))
    if os.path.isfile(os.path.join(root, "AGENTS.md")) and os.path.isfile(os.path.join(root, DAY0)):
        # agents own every card; a person acts only at a true checkpoint (pipeline/human-checkpoints.md)
        sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
        import check_card
        try:
            role_list = check_card.roles(root)
        except (OSError, IndexError):
            role_list = []
        problems += [("consistency", DAY0, p) for p in check_card.day0_owner_problems(rd(DAY0), role_list)]
    for f in files:
        if f.startswith(CONSIST_SKIP) or os.path.splitext(f)[1].lower() not in CONSIST_EXT or f in (
                "tools/pipeline_check.py",):
            continue
        text = rd(f)
        for n, line in enumerate(text.splitlines(), 1):
            where = f"{f}:{n}"
            for m in DEC_REF.finditer(line):
                if m.group(0) not in decisions:
                    problems.append(("consistency", where, f"decision {m.group(0)} has no row in {DECISIONS}"))
            ids = set()
            for m in CARD_REF.finditer(line):
                ids.update(re.findall(CARD_ID, m.group(1)))
            ids.update(CARD_LETTER.findall(line))
            for cid in sorted(ids):
                if cid not in day0:
                    problems.append(("consistency", where, f"card {cid} is not in {DAY0}"))
            # MegaPipeline/ wraps .json/.csv/.py text in .md; those sources are not path-checked, so neither is the copy.
            if f.endswith(".md") and not f.startswith("MegaPipeline/"):
                for m in PATH_REF.finditer(line):
                    path = m.group(1).rstrip(".")
                    if PATH_SKIP.search(path) or path in planned or PATH_TEMPLATE_TAIL.match(line, m.end()):
                        continue
                    if not exists_exact(root, path):
                        problems.append(("consistency", where, f"path {path} does not exist"))
    return problems


def lfs_bytes(root, files=None):
    """Total size of LFS-tracked files, read from the committed pointers."""
    files = git_files(root) if files is None else files
    binaries = [f for f in files if os.path.splitext(f)[1].lower() in LFS_EXT]
    tracked = sorted(lfs_tracked(root, binaries))
    total = 0
    for f, head in index_blob_heads(root, tracked, limit=200).items():
        m = re.search(rb"^size (\d+)$", head, re.M)
        if head.startswith(b"version https://git-lfs") and m:
            total += int(m.group(1))
    return total, len(tracked)


def check(root, release=False, notes=None):
    files = git_files(root)
    problems = [("ciprofile", f, f"the shipped copy carries the full-CI marker {CI_FULL}; remove it so installed game "
                                 "repos get the fast CI profile")
                for f in files if f.startswith("MegaPipeline/") and f.endswith("/" + CI_FULL)]
    inst = installed(root)
    if inst:
        files = [f for f in files if not shipped(f)]
    hp, hn = hygiene(root, files, release)
    problems += hp
    if notes is not None:
        notes += hn
    leak_re = re.compile("|".join(LEAK_TERMS), re.IGNORECASE)
    leak_code_re = re.compile("|".join(t for t in LEAK_TERMS if t not in LEAK_CODE_OK), re.IGNORECASE)

    binaries = [f for f in files if os.path.splitext(f)[1].lower() in LFS_EXT]
    lfs = lfs_tracked(root, binaries)
    heads = index_blob_heads(root, [f for f in binaries if f in lfs])
    for f, head in heads.items():
        if not head.startswith(b"version https://git-lfs"):
            problems.append(("lfs", f, "matches an LFS pattern but was committed as raw binary (run `git lfs install`, then re-add)"))
            lfs.discard(f)

    for f in files:
        full = os.path.join(root, f)
        ext = os.path.splitext(f)[1].lower()
        if f.startswith(FORBIDDEN_DIRS) or any(("/" + d) in ("/" + f) for d in FORBIDDEN_DIRS) or f.endswith(FORBIDDEN_SUFFIX):
            problems.append(("forbidden", f, "build output / IDE file must not be committed"))
            continue
        if ext in LFS_EXT and f not in lfs:
            problems.append(("lfs", f, "binary asset is not tracked by Git LFS (see .gitattributes)"))
        try:
            size = os.path.getsize(full)
        except OSError:
            continue
        if f not in lfs and size > MAX_NON_LFS_BYTES:
            problems.append(("size", f, f"{size} bytes outside LFS (limit {MAX_NON_LFS_BYTES})"))
        if (ext in TEXT_EXT or ext in PRIVATE_EXT) and f not in PRIVATE_ALLOW:
            try:
                for n, line in enumerate(read_text(full).splitlines(), 1):
                    hit = private_hit(line)
                    if hit:
                        problems.append(("private", f"{f}:{n}", f"'{hit}' is a private reference; describe the practice on its own merits"))
            except OSError:
                pass
        if ext in TEXT_EXT or os.path.basename(f) in ("AGENTS.md", "CLAUDE.md"):
            if f in LEAK_ALLOW or f.startswith(LEAK_ALLOW_PREFIXES):
                pass
            else:
                try:
                    text = read_text(full)
                except OSError:
                    continue
                term_re = leak_code_re if f.startswith(LEAK_CODE_DIRS) and ext in (".h", ".hpp", ".cpp") else leak_re
                for n, line in enumerate(text.splitlines(), 1):
                    m = term_re.search(line)
                    if m:
                        problems.append(("leak", f"{f}:{n}", f"'{m.group(0)}' belongs to another project or engine"))
            if f in BUDGETS:
                wc = budget_words(f, read_text(full))
                if wc > BUDGETS[f]:
                    problems.append(("budget", f, f"{wc} words > budget {BUDGETS[f]}"))
            if f.startswith(ROLE_DIR) and f.endswith(".md"):
                text = read_text(full)
                wc = words(text)
                if wc > ROLE_BUDGET:
                    problems.append(("budget", f, f"{wc} words > role budget {ROLE_BUDGET}"))
                for s in ROLE_SECTIONS:
                    if s not in text:
                        problems.append(("roles", f, f"missing section '{s}'"))
    new = [f for f in untracked_files(root) if os.path.splitext(f)[1].lower() in TEXT_EXT | PRIVATE_EXT
           and f not in PRIVATE_ALLOW and not (inst and shipped(f))]
    for f in new:
        try:
            for n, line in enumerate(read_text(os.path.join(root, f)).splitlines(), 1):
                hit = private_hit(line)
                if hit:
                    problems.append(("private", f"{f}:{n}", f"'{hit}' is a private reference; describe the practice on its own merits"))
        except OSError:
            pass
    if os.path.exists(os.path.join(root, DECISIONS)) or os.path.exists(os.path.join(root, DAY0)):
        problems += consistency(root, files + new)
    problems += repomap(root, files)
    problems += package(root)
    problems += practice_problems(root, release)
    return problems


def practice_problems(root, release=False):
    """The practice marker (tools/practice.py) never lands on the team repo, and a practice repo never makes a
    release (G4) build."""
    sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__))))
    import practice
    out = [("practice", practice.MARKER, p) for p in practice.marker_problems(root)]
    if release and practice.is_practice(root):
        out.append(("practice", practice.MARKER, practice.blocked("the G4 release check (--release)", root)))
    return out


def repomap(root, files=None):
    """docs/repo-map.md names every pipeline folder, and every pipeline path it names exists (tools/repo_map.py)."""
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
    import repo_map
    return [("repomap", where, why) for where, why in repo_map.problems(root, files)]


def package(root):
    """MegaPipeline/ must match a fresh tools/export_package.py build (skipped while either is absent)."""
    tool = os.path.join(root, "tools", "export_package.py")
    if not (os.path.isdir(os.path.join(root, "MegaPipeline")) and os.path.exists(tool)):
        return []
    if os.path.exists(os.path.join(root, ".pipeline-installed.json")):
        # an installed game repo: MegaPipeline/ is the update bundle, refreshed only by a pipeline update. Card PRs
        # never regenerate it (the export stamps the commit into ~38 files, so parallel PRs would all conflict).
        return []
    import importlib.util
    spec = importlib.util.spec_from_file_location("export_package", tool)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return [("package", where, why) for where, why in mod.check(root)]


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--root", default=os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    ap.add_argument("--release", action="store_true", help="submission build: _PH placeholders are problems")
    a = ap.parse_args(argv)
    notes = []
    problems = check(a.root, a.release, notes)
    for kind, where, why in problems:
        print(f"[{kind}] {where}: {why}")
    for kind, where, why in notes:
        print(f"note [{kind}] {where}: {why}")
    total, count = lfs_bytes(a.root)
    print(f"lfs: {count} file(s), {total} bytes ({total / 1048576:.1f} MiB) tracked by Git LFS")
    print(f"pipeline_check: {len(problems)} problem(s)")
    return 1 if problems else 0


if __name__ == "__main__":
    sys.exit(main())
