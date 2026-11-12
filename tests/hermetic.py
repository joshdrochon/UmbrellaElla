"""Fixtures copied from the repo with its jam state taken out (final-9 dry run A C1).

The unit-test CI step runs on every jam PR, so a test may not depend on how far the jam has filled the repo. A test
that needs a real file as a fixture copies it through here: the test map with every row back at `planned`, so the
rows the jam marks `merged` never demand tests a stub does not emit, and the no-player map list with only its
`default` rows (final-10 A H6). Not a test module (unittest discovers test*.py).
"""
import os
import re
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TEST_MAP = os.path.join(ROOT, "pipeline", "qa", "test-map.md")


def planned(text):
    """The test map with every table row's Card cell emptied and Status set to planned."""
    out = []
    for ln in text.split("\n"):
        cells = ln.split("|")
        if ln.startswith("|") and len(cells) >= 4 and cells[-2].strip() in ("planned", "merged"):
            cells[-3], cells[-2] = " ", " planned "
            ln = "|".join(cells)
        out.append(ln)
    return "\n".join(out)


def planned_test_map():
    with open(TEST_MAP, encoding="utf-8") as fh:
        return planned(fh.read())


def write_planned_test_map(path):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as fh:
        fh.write(planned_test_map())
    return path


NO_PLAYER = os.path.join(ROOT, "pipeline", "qa", "no-player-maps.txt")


def pre_jam_no_player_maps(text):
    """pipeline/qa/no-player-maps.txt as it is before the jam (final-10 A H6): the comment lines and the `default`
    rows only. A map card (0.10a: L_StyleFrame) adds its row, so the live file depends on the jam's progress."""
    keep = [ln for ln in text.split("\n")
            if not ln.strip() or ln.lstrip().startswith("#") or (ln.count("|") >= 2 and ln.split("|")[1].strip() == "default")]
    return "\n".join(keep).rstrip("\n") + "\n"


def write_pre_jam_no_player_maps(path):
    with open(NO_PLAYER, encoding="utf-8") as fh:
        text = pre_jam_no_player_maps(fh.read())
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as fh:
        fh.write(text)
    return path


_PRE_JAM = None


def pre_jam_root():
    """A root with the repo's docs as they are before the jam: the manifest, decisions, the test map at planned, the
    no-player map list, and no Source/ (no smoke hook). Tools that read repo state (check_pr's smoke hook and input
    waiver, the SMOKE_EFFECTIVE check) give the same answer here at any jam stage. Built once per run."""
    global _PRE_JAM
    if _PRE_JAM is None:
        import atexit
        import shutil
        import tempfile
        root = tempfile.mkdtemp()
        atexit.register(shutil.rmtree, root, True)
        for rel in ("docs/feature-manifest.json", "docs/decisions.md", "pipeline/qa/presets.json"):
            os.makedirs(os.path.dirname(os.path.join(root, rel)), exist_ok=True)
            shutil.copy(os.path.join(ROOT, rel), os.path.join(root, rel))
        write_planned_test_map(os.path.join(root, "pipeline", "qa", "test-map.md"))
        write_pre_jam_no_player_maps(os.path.join(root, "pipeline", "qa", "no-player-maps.txt"))
        _PRE_JAM = root
    return _PRE_JAM


def pre_d13_style():
    """pipeline/art/style.json with the texture mips rule back at null (before D13 / card 0.10a sets it), written to a
    temp file: (path, dict). The import-report fixtures are written for that state."""
    import atexit
    import json
    import tempfile
    with open(os.path.join(ROOT, "pipeline", "art", "style.json"), encoding="utf-8") as fh:
        style = json.load(fh)
    style["unreal_import"]["texture"]["mips"] = None
    fd, path = tempfile.mkstemp(suffix="-style.json")
    with os.fdopen(fd, "w", encoding="utf-8") as fh:
        json.dump(style, fh)
    atexit.register(os.remove, path)
    return path, style


LFS_POINTER = b"version https://git-lfs.github.com/spec/v1\n"


def refs_left_out(root=None):
    """True inside the honest-jam sandbox's nested CI run (HONEST_JAM_NESTED=1) when a reference image that
    pipeline/art/references.json lists is not on disk: the sandbox copy leaves LFS pointer files out (see lfs_pointer),
    so a test that needs those files skips there. The top-level run always checks the real repo."""
    import json
    if os.environ.get("HONEST_JAM_NESTED") != "1":
        return False
    root = root or os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    try:
        with open(os.path.join(root, "pipeline", "art", "references.json"), encoding="utf-8") as fh:
            refs = json.load(fh)
    except (OSError, ValueError):
        return False
    return any(r.get("path") and r.get("required") is not False and not os.path.isfile(os.path.join(root, r["path"]))
               for r in refs.get("references", []))   # an optional (team-art) entry may be absent from any repo


def drawn_figure(w, h):
    """RGBA rows of a near-black figure under an open umbrella on transparency: a stand-in for the team's reference
    art where a checkout has only LFS pointers (the CI runner). It reads like the reference cells to the checks."""
    clear = (0, 0, 0, 0)
    rows = []
    for y in range(h):
        row = []
        for x in range(w):
            dx, fy = (x - w / 2) / w, y / h
            canopy = 0.12 <= fy <= 0.32 and abs(dx) <= 0.36 * (fy - 0.10) / 0.22
            shaft = 0.30 <= fy <= 0.45 and abs(dx) <= 0.01
            head = (dx ** 2 + (fy - 0.50) ** 2) <= 0.06 ** 2
            body = 0.54 <= fy <= 0.88 and abs(dx) <= 0.06 + 0.16 * (fy - 0.54)
            v = 12 + int(36 * fy + 40 * abs(dx))   # inked shading, not one flat fill (art_judge flat cap)
            row.append((v, v - 3, v - 5, 255) if canopy or shaft or head or body else clear)
        rows.append(row)
    return rows


def reference_stand_ins(src_root, dst_root):
    """For each pipeline/art/references.json image that is an LFS pointer in src_root, write a drawn stand-in (one
    cell of the entry's size) at the same path under dst_root, so a sandbox copy can run the reference checks on a
    pointer checkout. Returns the paths written. Real images are copied as they are by the caller."""
    import json
    sys.path.insert(0, os.path.join(src_root, "tools"))
    from png import write_png
    try:
        with open(os.path.join(src_root, "pipeline", "art", "references.json"), encoding="utf-8") as fh:
            refs = json.load(fh)
    except (OSError, ValueError):
        return []
    out = []
    for r in refs.get("references", []):
        p = r.get("path") or ""
        if r.get("kind") != "image" or not lfs_pointer(os.path.join(src_root, p)):
            continue
        w, h = r.get("cell") or (256, 256)
        w, h = min(int(w), 512), min(int(h), 512)
        dst = os.path.join(dst_root, p)
        os.makedirs(os.path.dirname(dst), exist_ok=True)
        write_png(dst, w, h, drawn_figure(w, h))
        out.append(p)
    return out


LEFT_OUT = "the honest-jam sandbox leaves LFS pointer files out; the top-level run checks the real repo"


def lfs_pointer(path):
    """True for a Git LFS pointer file left in place of a binary (CI checks out with `lfs: false`). A sandbox that
    copies the repo leaves these out: its own git has no LFS object for them, so a checkout there fails to smudge."""
    try:
        with open(path, "rb") as fh:
            return fh.read(len(LFS_POINTER)) == LFS_POINTER
    except OSError:
        return False


def rmtree(path, ignore_errors=False):
    """shutil.rmtree that also removes read-only files: on Windows git writes its object files read-only, so a plain
    rmtree of a temp repo fails with Access is denied (or, with ignore_errors, leaves the folder behind)."""
    import shutil
    import stat

    def retry(func, p, _exc):
        try:
            os.chmod(p, stat.S_IWRITE)
            func(p)
        except OSError:
            if not ignore_errors:
                raise
    if ignore_errors and not os.path.lexists(path):
        return
    if sys.version_info >= (3, 12):
        shutil.rmtree(path, onexc=retry)
    else:
        shutil.rmtree(path, onerror=retry)
