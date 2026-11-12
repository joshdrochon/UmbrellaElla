#!/usr/bin/env python3
"""Install the git hooks every agent hits (Claude Code, Codex or any other). Stdlib only.

  post-commit  journals each commit (tools/journal.py commit-hook). Never blocks or fails a commit: with no card
               (JAM_CARD unset and a branch that is not ue-<id>-...), or no python, it does nothing.
  pre-commit   tools/git_gate.py pre-commit: rejects a commit that changes a gate path (gates.json gate_paths)
               unless a human makes it by the human route (`JAM_HUMAN=<name>`, no agent env; tools/git_gate.py).
  pre-push     tools/git_gate.py pre-push: the same rule for every commit the push sends, then `git lfs pre-push`
               (chained: the stock LFS pre-push hook is replaced by this one, so LFS objects still upload).
Both gate hooks run the committed HEAD copy of tools/git_gate.py and gates.json, so an edit in the working tree
cannot switch them off. tools/kickoff.py installs them on every run; the TD human may also run this once per clone
(card 0.17).
Git LFS writes its own post-commit hook (`git lfs post-commit`, which keeps lockable files read-only). This hook
chains it: it runs `git lfs post-commit` first, so installing over the stock LFS hook keeps the LFS protection
(final-8 dry run A H5). Any other hook this script did not write is left alone (exit 1); move it first.

Usage: python3 tools/install_git_hooks.py [--repo PATH] [--check]
  --check   exit 0 only if every hook is installed and current
Exit 0 = installed (or current), 1 = a foreign hook is in the way or a hook is missing, 2 = not a git repo.
"""
import argparse
import os
import re
import stat
import subprocess
import sys

MARK = "# journal-post-commit (tools/install_git_hooks.py)"
HOOK = f"""#!/bin/sh
{MARK}
# Journals each commit for the card (tools/journal.py). Never blocks or fails the commit.
# Git LFS first (chained; the stock LFS hook is replaced by this one): lockable files stay read-only.
if command -v git-lfs >/dev/null 2>&1; then git lfs post-commit "$@"
elif git config --get filter.lfs.process >/dev/null 2>&1 || grep -qs "filter=lfs" "$(git rev-parse --show-toplevel)/.gitattributes"; then
  echo "post-commit: this repo uses Git LFS but git-lfs is not on PATH; lockable files were not made read-only" >&2
fi
root=$(git rev-parse --show-toplevel 2>/dev/null) || exit 0
py=$(command -v python3 || command -v python) || exit 0
"$py" "$root/tools/journal.py" commit-hook >/dev/null 2>&1
exit 0
"""
GATE_MARK = "# jam-git-gate (tools/install_git_hooks.py)"
_RUN_GATE = """root=$(git rev-parse --show-toplevel 2>/dev/null) || exit 0
py=$(command -v python3 || command -v python) || {{ echo "{name}: no python3, so the gate-path check cannot run (blocked)" >&2; exit 1; }}
gate=$(mktemp "${{TMPDIR:-/tmp}}/git_gate.XXXXXX") || exit 1
git show HEAD:tools/git_gate.py > "$gate" 2>/dev/null || cp "$root/tools/git_gate.py" "$gate" 2>/dev/null || {{ rm -f "$gate"; exit 0; }}
"""
PRE_COMMIT = ("#!/bin/sh\n" + GATE_MARK + "\n# Gate paths need a human (tools/git_gate.py). Every agent hits this, not only Claude Code.\n"
              + _RUN_GATE.format(name="pre-commit") +
              '(cd "$root" && "$py" "$gate" pre-commit); rc=$?\nrm -f "$gate"\nexit $rc\n')
PRE_PUSH = ("#!/bin/sh\n" + GATE_MARK + "\n# Gate paths need a human (tools/git_gate.py), then Git LFS uploads (chained).\n"
            "refs=$(mktemp \"${TMPDIR:-/tmp}/git_refs.XXXXXX\") || exit 1\ncat > \"$refs\"\n"
            + _RUN_GATE.format(name="pre-push") +
            '(cd "$root" && "$py" "$gate" pre-push "$1" "$2" --refs "$refs"); rc=$?\nrm -f "$gate"\n'
            'if [ $rc -ne 0 ]; then rm -f "$refs"; exit $rc; fi\n'
            'if command -v git-lfs >/dev/null 2>&1; then git lfs pre-push "$@" < "$refs"; rc=$?\n'
            'elif git config --get filter.lfs.process >/dev/null 2>&1 || grep -qs "filter=lfs" "$root/.gitattributes"; then\n'
            '  echo "pre-push: this repo uses Git LFS but git-lfs is not on PATH; LFS objects were not uploaded" >&2\nfi\n'
            'rm -f "$refs"\nexit $rc\n')
HOOKS = {"post-commit": (MARK, HOOK), "pre-commit": (GATE_MARK, PRE_COMMIT), "pre-push": (GATE_MARK, PRE_PUSH)}
LFS_LINE = re.compile(r'^git lfs (?:post-commit|pre-push) "\$@"$')
LFS_GUARD = re.compile(r"^command -v git-lfs >/dev/null 2>&1 \|\| \{.*\}$")


def is_lfs_hook(text):
    """The stock hook `git lfs install` writes: a shebang, comments, the git-lfs guard and `git lfs post-commit "$@"`."""
    body = [ln.strip() for ln in text.splitlines() if ln.strip() and not ln.strip().startswith("#")]
    return bool(body) and any(LFS_LINE.match(b) for b in body) and \
        all(LFS_LINE.match(b) or LFS_GUARD.match(b) for b in body)


def hook_path(repo, name="post-commit"):
    r = subprocess.run(["git", "rev-parse", "--git-path", "hooks"], cwd=repo, capture_output=True, text=True)
    if r.returncode != 0:
        return None
    d = r.stdout.strip()
    return os.path.join(d if os.path.isabs(d) else os.path.join(repo, d), name)


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--repo", default=os.getcwd())
    ap.add_argument("--check", action="store_true")
    a = ap.parse_args(argv)
    if not hook_path(a.repo):
        print(f"install_git_hooks: {a.repo} is not a git repo", file=sys.stderr)
        return 2
    code = 0
    for name, (mark, body) in HOOKS.items():
        path = hook_path(a.repo, name)
        current = None
        if os.path.exists(path):
            with open(path, encoding="utf-8", errors="replace") as fh:
                current = fh.read()
        if current is not None and mark not in current and not is_lfs_hook(current):
            print(f"install_git_hooks: {path} exists and is not ours or the stock Git LFS hook; move it, then run this "
                  "again", file=sys.stderr)
            code = 1
            continue
        if a.check:
            ok = current == body
            print(f"install_git_hooks: {name} {'current' if ok else 'missing or old'} ({path})")
            code = code if ok else 1
            continue
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, "w", encoding="utf-8", newline="\n") as fh:
            fh.write(body)
        os.chmod(path, os.stat(path).st_mode | stat.S_IXUSR | stat.S_IXGRP | stat.S_IXOTH)
        print(f"install_git_hooks: {name} installed ({path})")
    return code


if __name__ == "__main__":
    sys.exit(main())
