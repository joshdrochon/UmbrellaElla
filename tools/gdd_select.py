#!/usr/bin/env python3
"""Pick the GDD revision a run tests, check the pipeline can import it, and say what to fix when it cannot. Stdlib only.

  python3 tools/gdd_select.py 1.4                     a revision: docs/gdd/GDD-1.4.md, else the one .md file under
                                                      scratch/gdd/ whose `| Revision | 1.4 |` row says 1.4
  python3 tools/gdd_select.py scratch/gdd/v1.4/GameDesignDocument-v1.4.md     or any .md path inside the repo
  python3 tools/gdd_select.py 1.4 --check             validate only (the same as no option: nothing is written)
  python3 tools/gdd_select.py 1.4 --set-current       validate as the official snapshot, then write docs/gdd/CURRENT
  tools/kickoff.sh --gdd 1.4 [--set-current]          (Windows: tools\\kickoff.ps1 --gdd 1.4) the same check, then the
                                                      run uses that GDD and its run record stores it

What "importable" means: what the pipeline's own readers need (tools/gdd_impact.py, tools/manifest_check.py).
  GDD file   a `| Revision | <rev> |` row (gdd_impact.REVISION) and a `---` line under the header table
             (gdd_impact.body; docs/gdd/README.md step 1); feature status rows (a table row that starts with a feature
             ID like CORE-01 and ends with a status word); at least one APPROVED_P0 (the P0 list the BASE preset
             loads); section 5A parameter tables (manifest_check.PARAM_TABLE_HEADS; printed blank, as in GDD SH1.0
             section 9, they import and every approved start traces to a GDD sentence instead,
             manifest_check.PROSE_ROWS); test preset IDs with T-01 BASE;
             QA test IDs; a revision you asked for matches its Revision row; a copy that reuses a pinned snapshot's
             revision is byte-identical to it
  repo       everything tools/manifest_check.py holds the manifest to, against this GDD instead of docs/gdd/CURRENT:
             gdd_revision, a record for every cited feature and QA ID, statuses as the GDD states them, P0 on,
             approved_parameters equal to the 5A numbers, presets equal to the T- IDs, decisions.md rows
  snapshot   a docs/gdd/GDD-*.md file has a sha256 pin in gdd_snapshots that matches (manifest_check pins every one);
             with --set-current also: the file is docs/gdd/GDD-<rev>.md, the manifest's gdd_snapshot names it, and
             no other pinned snapshot has the same Revision
Each problem is one line: the file to change and what to add or fix there.

This tool never edits a GDD file, a status or approved_parameters (the GDD and its design owner own those). It writes one file,
docs/gdd/CURRENT, and only with --set-current. Without it the choice is run-scoped: kickoff sets JAM_GDD for its own
process and its agent sessions, so the run record (tools/journal.py runs) stores that GDD revision while the team
repo's official CURRENT stays as it is. The repo checks (manifest_check, pipeline_check) keep reading CURRENT.

Exit 0 = importable, 1 = problems (listed), 2 = no such file or revision.
"""
import argparse
import json
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, HERE)
import gdd_impact  # noqa: E402
import journal  # noqa: E402
import manifest_check as mc  # noqa: E402

GDD_DIR = "docs/gdd"
SCRATCH = "scratch/gdd"
MAN = mc.MANIFEST
README = "docs/gdd/README.md"
ENV = journal.GDD_ENV
ROW_ID = re.compile(r"^[A-Z][A-Z0-9]*(?:-[A-Z0-9]+)+$")


def me():
    return "py tools\\gdd_select.py" if os.name == "nt" else "python3 tools/gdd_select.py"


def kick():
    return "tools\\kickoff.ps1" if os.name == "nt" else "tools/kickoff.sh"


def quote(arg):
    """How to type arg again: quoted on Windows (PowerShell reads 1.10 as the number 1.1) or when it has a space."""
    return f'"{arg}"' if os.name == "nt" or " " in arg else arg


def rel(root, path):
    return os.path.relpath(path, root).replace(os.sep, "/")


def inside(root, path):
    r, p = os.path.realpath(root), os.path.realpath(path)
    return p == r or p.startswith(r.rstrip(os.sep) + os.sep)


def read_text(path):
    with open(path, encoding="utf-8") as fh:
        return fh.read()


def file_revision(path):
    try:
        return gdd_impact.revision(read_text(path))
    except (OSError, UnicodeDecodeError):
        return "?"


def norm_rev(arg):
    """'v1.4' / 'GDD-1.4' / 'GDD-1.4.md' / '1.4' -> '1.4'."""
    r = arg.strip()
    r = re.sub(r"(?i)\.md$", "", r)
    r = re.sub(r"(?i)^gdd-", "", r)
    return re.sub(r"^[vV](?=\d)", "", r)


def looks_like_path(arg):
    return arg.lower().endswith(".md") or "/" in arg or "\\" in arg


def resolve(arg, root=ROOT, cwd=None):
    """(repo-relative path, None) or (None, one plain line saying what is wrong)."""
    cwd = cwd or os.getcwd()
    bare = "/" not in arg and "\\" not in arg
    hit = next((f for f in (os.path.normpath(os.path.join(b, arg)) for b in (cwd, root)) if os.path.isfile(f)), None)
    if looks_like_path(arg) and (hit or not bare):
        full = hit
        if not full:
            return None, f"gdd_select: there is no file {arg}. Check the name, or give a revision like 1.4."
        if not full.lower().endswith(".md"):
            return None, f"gdd_select: {arg} is not a .md file. Give the GDD's Markdown file (not the PDF)."
        if not inside(root, full):
            return None, (f"gdd_select: {arg} is outside the repo. Copy it into the repo (for example "
                          f"{SCRATCH}/v<revision>/), then run {me()} with that path.")
        return rel(os.path.realpath(root), os.path.realpath(full)), None
    rev = norm_rev(arg)
    official = os.path.join(root, GDD_DIR, f"GDD-{rev}.md")
    if os.path.isfile(official):
        return f"{GDD_DIR}/GDD-{rev}.md", None
    found = []
    for base, dirs, files in os.walk(os.path.join(root, SCRATCH)):
        dirs.sort()
        for name in sorted(files):
            full = os.path.join(base, name)
            if name.lower().endswith(".md") and file_revision(full) == rev:
                found.append(rel(root, full))
    if len(found) == 1:
        return found[0], None
    if found:
        return None, (f"gdd_select: revision {rev} matches {len(found)} files ({', '.join(found)}). Give the path "
                      "of the one you want.")
    if arg.lower().endswith(".md"):
        return None, (f"gdd_select: there is no file {arg} here, at the repo root or in {GDD_DIR}/. Check the name, "
                      "or give a revision like 1.4.")
    known = sorted({file_revision(os.path.join(root, GDD_DIR, n)) for n in os.listdir(os.path.join(root, GDD_DIR))
                    if mc.SNAPSHOT_GLOB.match(n)}) if os.path.isdir(os.path.join(root, GDD_DIR)) else []
    return None, (f"gdd_select: no GDD revision {rev}: there is no {GDD_DIR}/GDD-{rev}.md and no .md file under "
                  f"{SCRATCH}/ with a '| Revision | {rev} |' row. Known revisions: {', '.join(known) or 'none'}. "
                  "Give the file path instead.")


# ---------------------------------------------------------------- the GDD file itself
def gdd_file_problems(path, text, want_rev=None, root=ROOT, pins=None):
    """(lines, covered): lines about the GDD file; covered = layer-2 kinds these lines already explain."""
    out, covered = [], set()
    rev = gdd_impact.revision(text)
    snap = f"make the snapshot {GDD_DIR}/GDD-<rev>.md: the header table of {GDD_DIR}/GDD-1.3.md, a '---' line, then " \
           f"the GDD text ({README} step 1; the GDD file itself is never edited)"
    if rev == "?":
        covered.add("no-revision")
        out.append(f"{path}: no '| Revision | <number> |' row, so the pipeline cannot tell which revision it is. Fix: "
                   + snap + ".")
    elif want_rev and rev != want_rev:
        out.append(f"{path}: you asked for revision {want_rev}, but its Revision row says {rev}. Give the right file.")
    if not re.search(r"^---\s*$", text, re.M):
        out.append(f"{path}: no line of just '---' under the header table, so the header is read as GDD text. Fix: "
                   + snap + ".")
    body = gdd_impact.body(text)
    stated = gdd_impact.snapshot_statuses(text)
    if not stated:
        covered.add("no-status")
        odd = sorted({c[0] for c in (mc.table_cells(ln) for ln in body.splitlines() if ln.strip().startswith("|"))
                      if c and ROW_ID.match(c[0]) and not gdd_impact.FEATURE_ID.fullmatch(c[0])})
        out.append(f"{path}: no feature status rows. The pipeline reads each feature's status from a table row that "
                   f"starts with its ID (like CORE-01) and ends with a status word ({', '.join(gdd_impact.STATUSES)}), "
                   f"as in {GDD_DIR}/GDD-1.3.md section 5. Ask the design owner for a revision that states them"
                   + (f" (rows like {', '.join(odd[:4])} use IDs the pipeline does not read: it reads <PREFIX>-<two "
                      "digits>, tools/gdd_impact.py FEATURE_RE)" if odd else "") + ".")
    elif not any(mc.stated_status(c) == "APPROVED_P0" for c in stated.values()):
        out.append(f"{path}: no feature is APPROVED_P0, so there is no P0 list for the BASE preset (T-01). Ask the design owner "
                   "which features are P0; only the GDD sets a status.")
    if not mc.section_5a_rows(text) and not mc.section_5a_tables(text):
        covered.add("no-5a")
        heads = ", ".join("'" + h[0].upper() + h[1:] + "'" for h in mc.PARAM_TABLE_HEADS)
        out.append(f"{path}: no section 5A parameter tables. The pipeline reads the approved numbers from tables whose "
                   f"first header cell is {heads}, with 'start / step' and 'min - max' cells, as in "
                   f"{GDD_DIR}/GDD-1.3.md section 5A. Ask the design owner for a revision that prints them.")
    presets = sorted({m.group(0) for m in mc.PRESET_ID.finditer(body)})
    if not presets:
        covered.add("no-presets")
        out.append(f"{path}: no test preset IDs (T-01 BASE, T-02, ...). {mc.PRESETS} must list the GDD's presets, so "
                   f"the GDD has to name them (as in {GDD_DIR}/GDD-1.3.md section 10).")
    elif mc.BASE_PRESET not in presets:
        out.append(f"{path}: no {mc.BASE_PRESET} (the BASE preset that loads every P0 feature). Ask the design owner to keep "
                   f"{mc.BASE_PRESET} BASE in the preset table.")
    if not mc.QA_ID.search(body):
        covered.add("no-qa")
        out.append(f"{path}: no QA test IDs (QA-01, QA-02, ...). Each feature record lists the GDD's QA tests, so the "
                   f"GDD has to name them (as in {GDD_DIR}/GDD-1.3.md section 11).")
    if rev != "?":
        mine = mc.snapshot_sha256(os.path.join(root, path))
        for p in sorted(pins or {}):
            full = os.path.join(root, p)
            if p != path and os.path.isfile(full) and file_revision(full) == rev and mc.snapshot_sha256(full) != mine:
                out.append(f"{path}: it says Revision {rev}, like {p}, but its text differs. A changed GDD is a new "
                           f"revision: ask the design owner to number it ({README}).")
    return out, covered


# ---------------------------------------------------------------- the repo against this GDD
def fix_line(kind, where, why, rev, man):
    """One manifest_check problem as one plain 'file: what to fix' line."""
    if kind == "gdd" and where == "gdd_revision":
        return (f"{MAN}: set \"gdd_revision\" to \"{rev}\" at the top and in every feature record (now "
                f"\"{man.get('gdd_revision')}\"; {README} step 3).")
    if why.startswith("cited in the current GDD snapshot but has no manifest record"):
        return f"{MAN}: add a feature record for {where}. GDD {rev} names it and the manifest has none ({README} step 3)."
    if why.startswith("in the manifest but not cited"):
        return (f"{MAN}: {where} has a record, but GDD {rev} never names it. Remove the record if the GDD dropped it, "
                f"or ask the design owner ({README} step 3).")
    if why.startswith("QA test in the current GDD snapshot"):
        return f"{MAN}: add {where} to the \"tests\" list of the feature it checks (GDD {rev} names it, no record does)."
    if why.startswith("test listed in the manifest but not in"):
        owners = [f.get("feature_id") for f in man.get("features") or [] if where in (f.get("tests") or [])]
        return (f"{MAN}: GDD {rev} never names {where}. Remove it from the \"tests\" list of "
                f"{', '.join(owners) or 'its record'}.")
    m = re.match(r"status (\S+) differs from the GDD's '(.*)' \((\S+)\)", why)
    if kind == "gdd-status" and m:
        return (f"{MAN} {where}: status is {m.group(1)}, GDD {rev} says '{m.group(2)}'. Copy the GDD's word, "
                f"{m.group(3)}, exactly ({README} step 3: only the design owner's GDD changes a status).")
    if kind == "gdd-status" and "states no status" in why:
        return (f"{MAN} {where}: GDD {rev} states no status for it, so it may not be APPROVED, CONFIRMED, on or "
                "authorized. The design owner decides: they state its status in the GDD, or the record follows the GDD.")
    if kind == "approved" and "has no approved_parameters key" in why:
        return (f"tools/manifest_check.py PARAM_ROWS: map the new section 5A row '{where}' to an approved_parameters "
                "key (the pipeline owner changes this table).")
    if kind == "approved":
        return f"{MAN} approved_parameters {where}: {why}. The GDD's number wins; the design owner owns it."
    if kind == "presets":
        return f"{mc.PRESETS} {where}: {why}."
    if kind in ("overrides", "grace"):
        return f"{mc.DECISIONS} row '{where}': {why}."
    return f"{MAN} {where}: {why}."


def skip(kind, why, covered):
    return (("no-status" in covered and kind == "gdd-status" and "states no status" in why)
            or ("no-5a" in covered and kind == "approved" and "no parameter tables" in why)
            or ("no-presets" in covered and kind == "presets" and "must be the snapshot's" in why)
            or ("no-qa" in covered and why.startswith("test listed in the manifest but not in"))
            or ("no-revision" in covered and kind == "gdd" and why.startswith("manifest is for")))


def repo_problems(path, text, rev, covered, root=ROOT, set_current=False):
    man = mc.load_manifest(root)
    presets_path = os.path.join(root, mc.PRESETS)
    presets = mc.read_json(presets_path) if os.path.exists(presets_path) else None
    out = [fix_line(k, w, y, rev, man) for k, w, y in mc.problems(man, text, presets, mc.read_decisions(root))
           if not skip(k, y, covered)]
    pins = man.get("gdd_snapshots") or {}
    is_snap = path.startswith(GDD_DIR + "/") and mc.SNAPSHOT_GLOB.match(path[len(GDD_DIR) + 1:])
    pin_cmd = f"{'py' if os.name == 'nt' else 'python3'} tools/manifest_check.py --pin {path}"
    if is_snap and path not in pins:
        out.append(f"{MAN}: add the line `{pin_cmd}` prints to \"gdd_snapshots\" (every {GDD_DIR}/GDD-*.md is pinned; "
                   f"{README} step 2).")
    elif is_snap and pins.get(path) != mc.snapshot_sha256(os.path.join(root, path)):
        out.append(f"{path}: its bytes differ from its pin in {MAN}. A merged snapshot is never edited: restore it "
                   "with `git checkout -- " + path + "`.")
    if set_current:
        if not is_snap:
            out.append(f"--set-current: {path} is not a {GDD_DIR}/GDD-<rev>.md snapshot. Make one first ({README} "
                       f"step 1), or leave out --set-current to test it for this run only.")
        else:
            for _, w, y in mc.current_target_problems(path, pins, root):
                if "no sha256 pin" in y:
                    continue  # said above
                out.append(f"--set-current {path}: {y}.")
            if man.get("gdd_snapshot") != path:
                out.append(f"{MAN}: set \"gdd_snapshot\" to \"{path}\" (now \"{man.get('gdd_snapshot')}\"; {README} "
                           "step 2).")
    return out


def validate(path, root=ROOT, want_rev=None, set_current=False):
    """All problem lines for repo-relative `path` (empty = importable)."""
    try:
        text = read_text(os.path.join(root, path))
    except UnicodeDecodeError:
        return [f"{path}: not UTF-8 text. Save the GDD as UTF-8 Markdown."]
    try:
        pins = mc.load_manifest(root).get("gdd_snapshots") or {}
    except (OSError, ValueError) as e:
        return [f"{MAN}: cannot be read ({e}). Fix the file, then run {me()} again."]
    lines, covered = gdd_file_problems(path, text, want_rev, root, pins)
    return lines + repo_problems(path, text, gdd_impact.revision(text), covered, root, set_current)


def current_path(root=ROOT):
    try:
        return mc.current_snapshot(root)
    except OSError:
        return None


def write_current(path, root=ROOT):
    """docs/gdd/CURRENT names path's file. Same one-line format as the file has today."""
    with open(os.path.join(root, mc.CURRENT), "w", encoding="utf-8", newline="\n") as fh:
        fh.write(path[len(GDD_DIR) + 1:] + "\n")


def art_line(path, root=ROOT):
    """The art references this GDD brings: the images it embeds join pipeline/art/references.json through
    gdd_embedded (tools/art_check.py) for a run that picks it."""
    import art_check
    try:
        with open(os.path.join(root, art_check.REFERENCES), encoding="utf-8") as fh:
            spec = json.load(fh).get("gdd_embedded")
    except (OSError, ValueError):
        spec = None
    if not spec:
        return f"gdd_select: art references: {art_check.REFERENCES} has no gdd_embedded, so this GDD's images are not used."
    imgs = art_check.gdd_embedded(root, spec, gdd=path)
    miss = [i for i in imgs if not os.path.isfile(os.path.join(root, i))]
    return (f"gdd_select: art references: GDD embeds {len(imgs)} image(s), {len(imgs) - len(miss)} present"
            + (f", missing {', '.join(miss)}" if miss else "")
            + f"; they join {art_check.REFERENCES} (gdd_embedded) for a run on it.")


ENCOUNTER = "pipeline/level/encounter.json"


def encounter_line(rev, root=ROOT):
    """The encounter presets the picked GDD may load: tools/encounter_spec.py presets_for(revision, 'gdd_picker'), the
    hook encounter.json gives the GDD picker. None is a flag, not a refusal: the run plays no owl fight preset."""
    import encounter_spec
    try:
        with open(os.path.join(root, ENCOUNTER), encoding="utf-8") as fh:
            data = json.load(fh)
    except (OSError, ValueError):
        return f"gdd_select: encounter presets: {ENCOUNTER} is missing or unreadable, so no fight preset is checked."
    got = encounter_spec.presets_for(data, rev, "gdd_picker")
    if not got:
        return (f"gdd_select: encounter presets: none for GDD {rev} in {ENCOUNTER}. The Encounter Designer adds one "
                f"with gdd_revision {rev} and selectable_in gdd_picker (pipeline/roles/encounter-designer.md).")
    default = (encounter_spec.block(data) or {}).get("default")
    names = [f"{pid} ({p.get('status')}{', default' if pid == default else ''}"
             f"{', ' + p['decision'] if p.get('decision') else ''})" for pid, p in got]
    return (f"gdd_select: encounter presets for GDD {rev}: {', '.join(names)}. Pick one in a workbench or practice "
            f"build with {(encounter_spec.block(data).get('select') or {}).get('env', 'JAM_ENCOUNTER_PRESET')}.")


def choose(arg, root=ROOT, cwd=None, set_current=False, check=False):
    """(exit code, output lines, env for the run). The one entry point kickoff and main share."""
    path, err = resolve(arg, root, cwd)
    if err:
        return 2, [err], {}
    want = None if looks_like_path(arg) else norm_rev(arg)
    rev = file_revision(os.path.join(root, path))
    head = f"gdd_select: checking GDD {rev} ({path})"
    shown = quote(arg)
    try:
        probs = validate(path, root, want, set_current)
    except (OSError, ValueError) as e:
        return 2, [head, f"gdd_select: cannot read the repo files the check needs ({e})."], {}
    if probs:
        return 1, [head] + [f"FIX {p}" for p in probs] + [
            f"gdd_select: GDD {rev} cannot be imported yet: {len(probs)} thing(s) to fix (FIX lines above). "
            f"Nothing was changed. Fix them, then run {me()} {shown}{' --set-current' if set_current else ''} --check "
            "again."], {}
    cur = current_path(root)
    out = [head, f"gdd_select: OK, GDD {rev} ({path}) passes every import check.", art_line(path, root),
           encounter_line(rev, root)]
    env = {}
    if path == cur:
        out.append(f"gdd_select: {mc.CURRENT} already names it.")
    elif set_current and not check:
        write_current(path, root)
        out.append(f"gdd_select: {mc.CURRENT} now names {path[len(GDD_DIR) + 1:]} (was {cur}). Commit it in the "
                   f"PR that imports the revision ({README}).")
    else:
        env = {ENV: os.path.join(os.path.realpath(root), path)}
        out.append(f"gdd_select: {mc.CURRENT} is unchanged ({cur}). " +
                   ("Check only: nothing was written." if check else
                    f"This run uses {path} (run-scoped); repo checks still read {mc.CURRENT}. "
                    "Add --set-current to switch the team's official GDD."))
    return 0, out, env


def version_line(root=ROOT, env=None):
    old = os.environ.get(ENV)
    try:
        os.environ.pop(ENV, None)
        os.environ.update(env or {})
        return f"pipeline {journal.pipeline_version(root)['string']} | GDD {journal.gdd_revision(root)}"
    finally:
        os.environ.pop(ENV, None)
        if old is not None:
            os.environ[ENV] = old


class PlainParser(argparse.ArgumentParser):
    def error(self, message):
        print(f"gdd_select: I did not understand that ({message}). Type {me()} 1.4, or {me()} --help.")
        sys.exit(2)


def main(argv=None):
    ap = PlainParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("gdd", help="a revision like 1.4, or a .md file path inside the repo")
    ap.add_argument("--check", action="store_true", help="validate only; never writes anything")
    ap.add_argument("--set-current", action="store_true", help="also point docs/gdd/CURRENT at it")
    ap.add_argument("--root", default=ROOT)
    a = ap.parse_args(argv)
    code, lines, env = choose(a.gdd, a.root, set_current=a.set_current, check=a.check or not a.set_current)
    print("\n".join(lines))
    if code == 0:
        print(version_line(a.root, env))
        if env:
            print(f"gdd_select: to run the pipeline on it, type: {kick()} --gdd {quote(a.gdd)}")
    return code


if __name__ == "__main__":
    sys.exit(main())
