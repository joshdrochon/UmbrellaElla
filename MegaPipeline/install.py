#!/usr/bin/env python3
"""Install or update the Umbrella Ella pipeline from MegaPipeline/repo/ into the repo root. Stdlib only.

  bash MegaPipeline/install.sh                     install, dry run (lists what would be copied)
  bash MegaPipeline/install.sh --apply             install: copies every file that does not exist yet
  bash MegaPipeline/install.sh --update            update, dry run (lists every change, writes nothing)
  bash MegaPipeline/install.sh --update --apply    update: replaces the pipeline's own files with this version
  (Windows: powershell -File MegaPipeline\\install.ps1 with the same options)

What the pipeline owns comes from MegaPipeline/manifest.json: every file under repo/ with its SHA-256, and
"history": every SHA-256 each path ever had in repo/ (so files older versions shipped and this one dropped are known).
Update rules:
  - a pipeline file that still holds a version the pipeline shipped is replaced; the old copy goes to
    Saved/pipeline-backup/<time>/ first. A pipeline file the team changed (a hash the pipeline never shipped) is
    kept, and the new version is saved under new/ in the backup folder to merge by hand
  - a pipeline file the new version adds is copied
  - a retired file is removed (backed up first), but only when it still has a hash the pipeline shipped;
    one the team changed is kept and named
  - never touched: game content (Source/, Content/, Config/, Plugins/, Art/, Audio/, *.uproject), the GDD
    (docs/gdd/, GDD/), and the team's own files: anything not in the manifest, and the team-filled files in
    TEAM_FILES (the brief, decisions, test map, provenance, logs, README, .gitignore ...) once the team has filled
    them in. A team file still exactly as the pipeline shipped it is updated like any pipeline file; a filled-in one
    is kept and the new version is saved in the backup folder under new/ to merge by hand
  - the installed version is written to .pipeline-installed.json at the root (commit it)
One plain line per change, then `updated from <old> to <new>` (dry run: `would update from ...`).

Maintainer: `python3 MegaPipeline/install.py --make-manifest` after repo/ changes (reads repo/ and its git history).
Exit 0 = ok, 1 = the manifest does not match repo/ (stale), 2 = usage or not a git repo.
"""
import argparse
import datetime as dt
import fnmatch
import hashlib
import json
import os
import shutil
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
SRC = os.path.join(HERE, "repo")
MANIFEST = os.path.join(HERE, "manifest.json")
INSTALLED = ".pipeline-installed.json"
BACKUP = os.path.join("Saved", "pipeline-backup")
GAME = ("Source/*", "Content/*", "Config/*", "Plugins/*", "Art/*", "Audio/*", "*.uproject", "docs/gdd/*", "GDD/*",
        "Saved/*", "MegaPipeline/*")
TEAM_FILES = ("docs/jam-brief.md", "docs/decisions.md", "docs/feature-manifest.json", "docs/balance.md",
              "pipeline/qa/test-map.md", "pipeline/qa/baked.json", "pipeline/art/provenance.csv", "pipeline/feel/*.csv",
              "prompts/log/*", "README.md", ".gitignore", ".gitattributes", ".github/CODEOWNERS",
              ".github/workflows/clock.yml", ".pipeline-practice")


def say(msg):
    print(msg, flush=True)


def digest(data):
    """Hash with line endings normalised, so a Windows (CRLF) checkout of an untouched file still matches."""
    if b"\0" not in data[:8192]:
        data = data.replace(b"\r\n", b"\n")
    return hashlib.sha256(data).hexdigest()


def sha(path):
    with open(path, "rb") as fh:
        return digest(fh.read())


def match(rel, pats):
    return any(fnmatch.fnmatchcase(rel, p) for p in pats)


def files_under(d):
    out = []
    for base, dirs, fs in os.walk(d):
        dirs[:] = [x for x in dirs if x != "__pycache__"]
        for f in fs:
            if f.endswith(".pyc"):
                continue
            out.append(os.path.relpath(os.path.join(base, f), d).replace(os.sep, "/"))
    return sorted(out)


def git(*args, cwd=HERE):
    p = subprocess.run(["git", *args], cwd=cwd, capture_output=True)
    return p.stdout if p.returncode == 0 else None


def version_of(tree):
    try:
        with open(os.path.join(tree, "pipeline", "VERSION"), encoding="utf-8") as fh:
            return fh.read().strip() or None
    except OSError:
        return None


# ---------------------------------------------------------------- manifest (maintainer)
def make_manifest():
    files = {rel: sha(os.path.join(SRC, rel)) for rel in files_under(SRC)}
    top = (git("rev-parse", "--show-toplevel") or b"").decode().strip()
    prefix = os.path.relpath(os.path.realpath(SRC), os.path.realpath(top)).replace(os.sep, "/") + "/" if top else None
    history = {}
    if prefix:
        commits = (git("log", "--format=%H", "--", prefix, cwd=top) or b"").decode().split()
        for c in commits:
            names = (git("ls-tree", "-r", "--name-only", c, "--", prefix, cwd=top) or b"").decode().splitlines()
            for n in names:
                rel = n[len(prefix):]
                blob = git("show", f"{c}:{n}", cwd=top)
                if blob is not None:
                    history.setdefault(rel, set()).add(digest(blob))
    for rel, h in files.items():
        history.setdefault(rel, set()).add(h)
    commit = (git("log", "-1", "--format=%h", "--", prefix, cwd=top) or b"").decode().strip() if prefix else ""
    version = f"{version_of(SRC) or '0'}+{commit or 'local'}"
    data = {"_about": "Pipeline-owned files of this MegaPipeline version (MegaPipeline/install.py). Regenerate with "
                      "`python3 MegaPipeline/install.py --make-manifest` whenever repo/ changes.",
            "version": version, "files": files,
            "history": {k: sorted(v) for k, v in sorted(history.items())}}
    with open(MANIFEST, "w", encoding="utf-8") as fh:
        json.dump(data, fh, indent=1, sort_keys=True)
        fh.write("\n")
    say(f"manifest: {len(files)} file(s), {len(set(history) - set(files))} retired, version {version}")
    return 0


def load_manifest():
    try:
        with open(MANIFEST, encoding="utf-8") as fh:
            m = json.load(fh)
    except (OSError, ValueError):
        return None, "MegaPipeline/manifest.json is missing or broken. Run `python3 MegaPipeline/install.py --make-manifest`."
    now = {rel: sha(os.path.join(SRC, rel)) for rel in files_under(SRC)}
    if now != m.get("files"):
        return None, ("MegaPipeline/manifest.json does not match MegaPipeline/repo/ (stale). Run `python3 "
                      "MegaPipeline/install.py --make-manifest`, then this command again.")
    return m, None


# ---------------------------------------------------------------- install / update
def write_installed(root, m):
    with open(os.path.join(root, INSTALLED), "w", encoding="utf-8") as fh:
        json.dump({"version": m["version"], "installed_utc": dt.datetime.now(dt.timezone.utc).isoformat(
            timespec="seconds"), "files": m["files"]}, fh, indent=1, sort_keys=True)
        fh.write("\n")


def old_version(root):
    try:
        with open(os.path.join(root, INSTALLED), encoding="utf-8") as fh:
            return json.load(fh).get("version") or "unknown"
    except (OSError, ValueError):
        v = version_of(root)
        return v or "unknown (installed before versions)"


def install(root, m, apply):
    copied, conflicts = 0, 0
    for rel in sorted(m["files"]):
        dest = os.path.join(root, rel)
        if os.path.exists(dest):
            say(f"CONFLICT  {rel}  (exists at root; merge by hand)")
            conflicts += 1
            continue
        if apply:
            os.makedirs(os.path.dirname(dest), exist_ok=True)
            shutil.copy2(os.path.join(SRC, rel), dest)
        copied += 1
    if apply:
        write_installed(root, m)
        say(f"copied {copied} file(s); {conflicts} conflict(s) left for a human")
    else:
        say(f"dry run: would copy {copied} file(s); {conflicts} conflict(s). Re-run with --apply.")
    return 0


def update(root, m, apply, stamp=None):
    stamp = stamp or dt.datetime.now().strftime("%Y%m%d-%H%M%S")
    bdir = os.path.join(root, BACKUP, stamp)
    old, new = old_version(root), m["version"]
    counts = {"replaced": 0, "added": 0, "removed": 0, "kept": 0}

    def backup(rel, sub=""):
        dst = os.path.join(bdir, sub, rel)
        if apply:
            os.makedirs(os.path.dirname(dst), exist_ok=True)
            shutil.copy2(os.path.join(root if not sub else SRC, rel), dst)
        return os.path.relpath(dst, root).replace(os.sep, "/")

    for rel, want in sorted(m["files"].items()):
        dest = os.path.join(root, rel)
        if match(rel, GAME):
            continue
        if not os.path.exists(dest):
            say(f"ADD      {rel}")
            counts["added"] += 1
            if apply:
                os.makedirs(os.path.dirname(dest), exist_ok=True)
                shutil.copy2(os.path.join(SRC, rel), dest)
            continue
        if sha(dest) == want:
            continue
        untouched = sha(dest) in m.get("history", {}).get(rel, ())
        if match(rel, TEAM_FILES) and not untouched:
            say(f"KEEP     {rel}  (team file; new version saved as {backup(rel, 'new')} to merge by hand)")
            counts["kept"] += 1
            continue
        if not untouched:
            say(f"KEEP     {rel}  (changed by the team, or not from the pipeline; new version saved as "
                f"{backup(rel, 'new')} to merge by hand)")
            counts["kept"] += 1
            continue
        say(f"REPLACE  {rel}  (old copy: {backup(rel)})")
        counts["replaced"] += 1
        if apply:
            shutil.copy2(os.path.join(SRC, rel), dest)
    for rel, hashes in sorted(m.get("history", {}).items()):
        if rel in m["files"]:
            continue
        dest = os.path.join(root, rel)
        if match(rel, GAME) or match(rel, TEAM_FILES) or not os.path.isfile(dest):
            continue
        if sha(dest) not in hashes:
            say(f"KEEP     {rel}  (the pipeline dropped it, but your copy was changed; delete it by hand if unused)")
            counts["kept"] += 1
            continue
        say(f"REMOVE   {rel}  (dropped by the new version; old copy: {backup(rel)})")
        counts["removed"] += 1
        if apply:
            os.remove(dest)
    summary = (f"{counts['replaced']} replaced, {counts['added']} added, {counts['removed']} removed, "
               f"{counts['kept']} kept for you to merge")
    if apply:
        write_installed(root, m)
        say(f"updated from {old} to {new}: {summary}. Backups: {os.path.relpath(bdir, root)}")
    else:
        say(f"dry run: would update from {old} to {new}: {summary}. Nothing written. Re-run with --update --apply.")
    return 0


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--apply", action="store_true")
    ap.add_argument("--update", action="store_true")
    ap.add_argument("--make-manifest", action="store_true")
    ap.add_argument("--root", help="the repo root (default: the git top level of this folder)")
    a = ap.parse_args(argv)
    if a.make_manifest:
        return make_manifest()
    root = a.root or (git("rev-parse", "--show-toplevel") or b"").decode().strip()
    if not root or not os.path.isdir(root):
        say("install: this folder is not inside a git repo. Put MegaPipeline/ in your game repo, then run "
            "`bash MegaPipeline/install.sh` from there.")
        return 2
    m, err = load_manifest()
    if err:
        say("install: " + err)
        return 1
    return update(root, m, a.apply) if a.update else install(root, m, a.apply)


if __name__ == "__main__":
    sys.exit(main())
