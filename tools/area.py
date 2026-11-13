#!/usr/bin/env python3
"""Pick up one area of the build on your own machine, from its branch, and merge it back without conflicts. Stdlib only.

The build lead splits the game into areas. Each area has a branch `area/<name>` and a worker brief
`docs/build/areas/<name>.md` on main; HANDOFF.md on main says what is done and what is next. Anyone with a clone can
resume an area where it stopped (the lead's usage ran out, or a teammate takes an area):

  tools/area.sh                    HANDOFF.md, then every area: branch, last commit, lane
  tools/area.sh <name>             fetch; check out area/<name> (origin's if it exists, else new from main); merge main
                                   in; install the lane guard; print the lane and rules; start the agent with the brief
         --agent claude|codex|none choose the agent (default: the one installed; both installed: it asks)
  tools/area.sh <name> --done      fetch; merge main into area/<name>; refuse files outside the lane; merge the area
                                   into main; print the push command (it never pushes)
  tools/area.sh <name> --prompt    print the agent prompt only
  python3 tools/area.py --guard    the pre-commit hook: on an area/<name> branch, refuses staged files outside the lane
Windows: tools\\area.ps1 (same arguments).

The lane is the backticked paths in the brief's Lane section (a heading or a line that starts with "Lane"), one bullet
each: a path ending in / is a folder, * matches anything (also /), anything else is one file. Every area may also
write docs/build/needs/<name>.md: what it needs from a shared file. Files in no lane (Config/*.ini, the .uproject,
*.Build.cs, HANDOFF.md, docs/build/areas/) are the lead's and change on main only. Branches merge, never rebase, so
a pushed area branch is never rewritten. AREA_AGENT_CMD (tests) replaces the agent command; the prompt is appended.
Exit 0 = ok, 1 = refused (dirty tree, conflict, out-of-lane file, diverged branch), 2 = usage error.
"""
import argparse
import fnmatch
import os
import shlex
import shutil
import subprocess
import sys

BRIEFS = "docs/build/areas"
NEEDS = "docs/build/requests"   # the lead's name for it (docs/build/worker-rules.md)
HANDOFF = "HANDOFF.md"
REMOTE = "origin"
ROLE = "gameplay-dev"
MARK = "# area-lane-guard (tools/area.py)"
HOOK = f"""#!/bin/sh
{MARK}
# On an area/<name> branch, refuses a commit that stages files outside the area's lane. Other branches: no check.
root=$(git rev-parse --show-toplevel 2>/dev/null) || exit 0
[ -f "$root/tools/area.py" ] || exit 0
case $(git symbolic-ref --short -q HEAD) in area/*) ;; *) exit 0;; esac
for p in python3 python py; do
  if command -v "$p" >/dev/null 2>&1 && "$p" -c "import sys; sys.exit(0 if sys.version_info >= (3, 9) else 1)" >/dev/null 2>&1; then
    exec "$p" "$root/tools/area.py" --guard
  fi
done
echo "area guard: no Python 3.9+ found, so the lane was not checked (tools/area.py --done still checks it)" >&2
exit 0
"""


class Refused(Exception):
    pass


def git(*args, check=True, root=None):
    r = subprocess.run(["git", *args], cwd=root or ROOT, capture_output=True, text=True)
    if check and r.returncode != 0:
        raise Refused(f"git {' '.join(args)} failed:\n{(r.stderr or r.stdout).strip()}")
    return r


def toplevel():
    here = os.path.dirname(os.path.abspath(__file__))
    r = subprocess.run(["git", "rev-parse", "--show-toplevel"], cwd=here, capture_output=True, text=True)
    return r.stdout.strip() if r.returncode == 0 else os.path.dirname(here)


ROOT = toplevel()
SCRIPT = "tools\\area.ps1" if os.name == "nt" else "tools/area.sh"


def has_remote():
    return REMOTE in git("remote").stdout.split()


def ref_exists(ref):
    return git("rev-parse", "--verify", "-q", ref + "^{commit}", check=False).returncode == 0


def base_ref():
    """origin/main when there is an origin (fetched first by the caller), else the local main."""
    if has_remote() and ref_exists(f"{REMOTE}/main"):
        return f"{REMOTE}/main"
    if ref_exists("main"):
        return "main"
    raise Refused("no main branch here. Clone the game repo first (git clone <url>), then run this in its folder.")


def fetch():
    if has_remote():
        r = git("fetch", "--prune", REMOTE, check=False)
        if r.returncode != 0:
            print(f"area: could not fetch {REMOTE} (offline?); using what this clone already has.\n{r.stderr.strip()}")


def show(ref, path):
    r = git("show", f"{ref}:{path}", check=False)
    return r.stdout if r.returncode == 0 else None


def areas(ref):
    out = git("ls-tree", "--name-only", f"{ref}:{BRIEFS}", check=False).stdout.split()
    return sorted(n[:-3] for n in out if n.endswith(".md") and not n.endswith("-status.md"))


ROOTS = ("Source/", "Content/", "Config/", "Plugins/", "docs/", "pipeline/", "tools/", "tests/", "evals/", "Art/",
         "Audio/", "prompts/")


def braces(p):
    """`a/{B,C}/d` -> [`a/B/d`, `a/C/d`] (nested braces too)."""
    i = p.find("{")
    if i < 0:
        return [p]
    j = p.index("}", i)
    return [x for alt in p[i + 1:j].split(",") for x in braces(p[:i] + alt + p[j + 1:])]


def resolve(rel, first):
    """A bullet's later items may be written relative to its first path (`Source/G/{Public,Private}/Owl/**`,
    `Encounter/**`, `Private/Tests/Enemy/**`). Returns every reading: absolute, under Source/<Module>/ (and
    {Public,Private}/ there), under Content/<Game>/, and under each folder of the first path. Never narrower."""
    out = [rel]
    seg = first.split("/")
    if rel.startswith(ROOTS) or not first:
        return out
    if len(seg) > 2 and seg[0] in ("Source", "Content"):
        out.append(f"{seg[0]}/{seg[1]}/{rel}")
        if seg[0] == "Source":
            out.append(f"Source/{seg[1]}/{{Public,Private}}/{rel}")
    for k in range(1, len(seg)):
        if "*" in seg[k - 1]:
            break
        out.append("/".join(seg[:k]) + "/" + rel)
    return out


def lane_of(text):
    """The lane in a brief: backticked paths on the bullets under the first heading that names a lane (`## Lane`,
    `## File lane (only these)`), or after a line that starts with Lane, up to the next heading. A bullet may run
    over several lines; an item after the word "except" is excluded (prefix "!"). -> patterns ('*' and '**' match
    across folders, a path ending in / is a folder)."""
    bullets, inside = [], False
    for line in text.splitlines():
        s = line.strip()
        bare = s.lstrip("#*_ ").lower()
        if s.startswith("#"):
            if bullets:
                break
            inside = "lane" in bare
            continue
        if not inside and (bare.startswith("lane") or bare.startswith("file lane")):
            inside = True
            continue
        if not inside:
            continue
        if s.startswith(("- ", "* ")):
            bullets.append(s[2:])
        elif s and bullets and line[:1] in (" ", "\t"):
            bullets[-1] += " " + s
    pats = []
    for b in bullets:
        parts = b.split("`")
        first, exclude = "", False
        for k in range(1, len(parts), 2):
            item = parts[k].strip().replace("\\", "/")
            sep = parts[k - 1].lower()
            # "except `A`, `B`" / "(except `A`, `B`)": every item up to a ")" or ";" is excluded.
            if "except" in sep:
                exclude = True
            elif exclude and (")" in sep or ";" in sep or sep.strip(" ,").replace("and", "").replace("or", "").strip()):
                exclude = False
            if not item or " " in item:
                continue
            if not first and item.startswith(ROOTS):
                first = item
            for r in resolve(item, first):
                for x in braces(r):
                    pats.append(("!" if exclude else "") + x)
    lane = Lane(dict.fromkeys(pats))
    lane.bullets = bullets
    return lane


class Lane(list):
    """The lane's patterns; .bullets = the brief's own lane lines, for people and the agent prompt."""
    bullets = ()


def match(path, pat):
    pat = pat.replace("**", "*")
    if pat.endswith("/"):
        return path.startswith(pat)
    if "*" in pat:
        return fnmatch.fnmatchcase(path, pat)
    return path == pat


def in_lane(path, lane, area):
    if path == f"{NEEDS}/{area}.md":
        return True
    if any(match(path, p[1:]) for p in lane if p.startswith("!")):
        return False
    return any(match(path, p) for p in lane if not p.startswith("!"))


def lanes_overlap(a, b):
    """True when some file could be in both lanes, so two parallel jobs never get the same files. Each pattern is
    probed with one sample path (its * filled in); a pattern with a * before its last folder is compared by its fixed
    start only (wider: such lanes wait for each other)."""
    def fixed(p):
        return p.replace("**", "*").split("*")[0]

    def probe(p):
        p = p.replace("**", "*").replace("*", "x")
        return p + "x" if p.endswith("/") else p

    def mid_star(p):
        return "*" in p.rsplit("/", 1)[0]

    def excluded(path, lane):
        return any(match(path, e[1:]) for e in lane if e.startswith("!"))

    for x in (p for p in a if not p.startswith("!")):
        for y in (p for p in b if not p.startswith("!")):
            for path in (probe(x), probe(y)):
                if match(path, x) and match(path, y) and not excluded(path, a) and not excluded(path, b):
                    return True
            fx, fy = fixed(x), fixed(y)
            if (mid_star(x) or mid_star(y)) and (fx.startswith(fy) or fy.startswith(fx)):
                return True
    return False


def shown(lane):
    """The lane as people read it: the brief's own bullets (else the patterns)."""
    return list(getattr(lane, "bullets", ()) or lane)


def brief_and_lane(area, ref):
    text = show(ref, f"{BRIEFS}/{area}.md")
    if text is None:
        names = ", ".join(areas(ref)) or f"none yet ({BRIEFS}/ is empty on {ref})"
        raise Refused(f"no area '{area}' on {ref}. Areas: {names}")
    lane = lane_of(text)
    if not lane:
        raise Refused(f"{BRIEFS}/{area}.md has no lane. The lead adds a section like:\n## Lane\n- `Source/UmbrellaElla/"
                      f"Public/Owl/`\n- `Content/UmbrellaElla/Owl/`\nThen run {SCRIPT} {area} again.")
    return text, lane


def require_clean():
    gd = git("rev-parse", "--git-dir").stdout.strip()
    gd = gd if os.path.isabs(gd) else os.path.join(ROOT, gd)
    for f in ("MERGE_HEAD", "rebase-merge", "rebase-apply", "CHERRY_PICK_HEAD"):
        if os.path.exists(os.path.join(gd, f)):
            raise Refused("a merge or rebase is in progress here. Finish it or undo it (git merge --abort), then retry.")
    dirty = git("status", "--porcelain", "--untracked-files=no").stdout.strip()
    if dirty:
        raise Refused("you have uncommitted changes:\n" + dirty + "\nCommit them (git add -A; git commit -m wip) or "
                      "put them aside (git stash), then run this again.")


def merge_in(ref, what):
    r = git("merge", "--no-edit", ref, check=False)
    if r.returncode != 0:
        files = git("diff", "--name-only", "--diff-filter=U", check=False).stdout.split()
        git("merge", "--abort", check=False)
        raise Refused(f"merging {what} conflicts in: {', '.join(files) or r.stdout.strip()}. Nothing was changed "
                      "(merge aborted). Two people changed the same file; ask the lead who owns it.")


def out_of_lane(paths, lane, area):
    return [p for p in paths if p and not in_lane(p, lane, area)]


def install_guard():
    hooks = git("config", "--get", "core.hooksPath", check=False).stdout.strip()
    if hooks:
        hooks = hooks if os.path.isabs(hooks) else os.path.join(ROOT, hooks)
    else:
        hooks = git("rev-parse", "--git-path", "hooks").stdout.strip()
        hooks = hooks if os.path.isabs(hooks) else os.path.join(ROOT, hooks)
    os.makedirs(hooks, exist_ok=True)
    path = os.path.join(hooks, "pre-commit")
    if os.path.exists(path):
        with open(path, encoding="utf-8", errors="replace") as fh:
            if MARK not in fh.read():
                print(f"area: {path} is another tool's hook, so the lane guard is not installed. "
                      f"{SCRIPT} <name> --done still refuses out-of-lane files.")
                return False
    with open(path, "w", encoding="utf-8", newline="\n") as fh:
        fh.write(HOOK)
    os.chmod(path, 0o755)
    return True


def rules(area, lane):
    lines = [f"Lane for {area} (commit only these; the guard refuses anything else):"]
    lines += [f"  - {p}" for p in shown(lane)] + [f"  - {NEEDS}/{area}.md   (what you need from a shared file)"]
    lines += [
        "Rules:",
        "  1. One person per area at a time. HANDOFF.md says who has it; tell the team before you take one.",
        "  2. Shared files (Config/*.ini, UmbrellaElla.uproject, *.Build.cs, HANDOFF.md, the briefs, other lanes)",
        "     change on main only. Write what you need in " + f"{NEEDS}/{area}.md.",
        "  3. .uasset/.umap files only inside your lane. Never save another lane's asset or the map unless the",
        "     map is in your lane (Unreal asks to save everything it opened: untick what is not yours).",
        "  4. Commit after every step that works. Merge, never rebase, so pushed history is never rewritten.",
        f"  5. Finished or stopping: {SCRIPT} {area} --done, then the push command it prints.",
    ]
    return "\n".join(lines)


def prompt(area, lane):
    lane_txt = "\n".join(f"   - {p}" for p in shown(lane))
    return (
        f'You are resuming area "{area}" of Umbrella Ella on branch area/{area}, on this machine only: no cards, no '
        f"PRs, no GitHub issues, no pushes.\n"
        f"1. Read {HANDOFF} (what is done and what is next), docs/build/worker-rules.md if it exists, "
        f"{BRIEFS}/{area}.md (your brief) and {BRIEFS}/{area}-status.md if it exists. Run `git log --oneline -15` to "
        f"see the last work on this branch. Continue from the next step for {area}; do not redo finished work.\n"
        f"2. Edit and commit only inside your lane (your brief's lane section):\n{lane_txt}\n   - {NEEDS}/{area}.md\n"
        f"   Commit with plain `git commit`: the pre-commit lane guard refuses files outside the lane. Shared files (Config/*.ini, UmbrellaElla.uproject, *.Build.cs, "
        f"other areas' folders, {HANDOFF}) are not yours: write what you need from them in {NEEDS}/{area}.md and "
        f"keep going.\n"
        f"3. .uasset/.umap files only inside your lane; never save another lane's asset or the map unless it is in "
        f"your lane.\n"
        f"4. Commit after every step that builds and passes its checks, with a message that says what works now.\n"
        f"5. When the brief's done criteria are met, or you must stop, say so and tell the person to run "
        f"{SCRIPT} {area} --done.")


def last_commit(ref):
    r = git("log", "-1", "--format=%h %cr %s", ref, check=False)
    return r.stdout.strip() if r.returncode == 0 else "-"


def cmd_status():
    fetch()
    ref = base_ref()
    text = show(ref, HANDOFF)
    print(text if text else f"(no {HANDOFF} on {ref} yet)")
    names = areas(ref)
    if not names:
        print(f"No areas yet: {BRIEFS}/ is empty on {ref}.")
        return 0
    print(f"Areas (briefs on {ref}):")
    for n in names:
        b = f"{REMOTE}/area/{n}" if ref_exists(f"{REMOTE}/area/{n}") else (f"area/{n}" if ref_exists(f"area/{n}") else None)
        print(f"  {n:<14} {('area/' + n) if b else 'no branch yet':<20} {last_commit(b) if b else ''}")
    print(f"Resume one: {SCRIPT} <name>")
    return 0


def cmd_start(area, agent):
    _, lane = prepare(area)
    return run_agent(area, lane, agent)


def prepare(area):
    """Fetch, check out area/<area> (origin's, local or new from main), merge main in, guard the lane. -> (ref, lane)"""
    require_clean()
    fetch()
    ref = base_ref()
    _, lane = brief_and_lane(area, ref)
    br, remote_br = f"area/{area}", f"{REMOTE}/area/{area}"
    local, remote = ref_exists(br), has_remote() and ref_exists(remote_br)
    if local:
        git("switch", br)
        if remote:
            r = git("merge", "--ff-only", remote_br, check=False)
            if r.returncode != 0:
                raise Refused(f"your {br} and {remote_br} both have commits the other lacks: someone else also worked "
                              f"on {area}. Rule 1 is one person per area. Ask them, then merge by hand.")
    elif remote:
        git("switch", "-c", br, "--track", remote_br)
    else:
        git("switch", "--no-track", "-c", br, ref)
    merge_in(ref, f"main ({ref}) into {br}")
    guard = install_guard()
    print(f"On {br} at {last_commit('HEAD')} (main merged in).")
    handoff = show(ref, HANDOFF) or ""
    rows = [ln for ln in handoff.splitlines() if br in ln or f"| {area} " in ln]
    if rows:
        print(f"{HANDOFF} for {area}:\n" + "\n".join("  " + r.strip() for r in rows))
    print(rules(area, lane))
    stray = out_of_lane(git("diff", "--name-only", f"{ref}...HEAD").stdout.split(), lane, area)
    if stray:
        print(f"WARNING: this branch already changes files outside the lane (--done will refuse them): {', '.join(stray)}")
    if not guard:
        print("WARNING: the lane guard is not installed (see above).")
    return ref, lane


def run_agent(area, lane, agent):
    text = prompt(area, lane)
    stub = os.environ.get("AREA_AGENT_CMD")
    if agent == "none":
        print(f"No agent started. Start yours with this prompt ({SCRIPT} {area} --prompt prints it again).")
        return 0
    if stub:
        cmd = shlex.split(stub) + [text]
    else:
        found = [a for a in ("claude", "codex") if shutil.which(a)]
        if agent is None:
            if not found:
                print(f"Neither Claude Code nor Codex is installed, so no agent started. Prompt: {SCRIPT} {area} --prompt")
                return 0
            agent = found[0]
            if len(found) == 2 and sys.stdin.isatty():
                ans = input("Claude Code and Codex are both installed. Type claude or codex: ").strip().lower()
                agent = "codex" if ans in ("codex", "x") else "claude"
        if not shutil.which(agent):
            raise Refused(f"{agent} is not installed. Run {SCRIPT} {area} --agent none and start your agent yourself.")
        cmd = [shutil.which(agent), text]   # Windows: npm installs claude.cmd / codex.cmd; which() finds it
    print(f"Starting {os.path.basename(cmd[0])} in {ROOT} on area/{area}.", flush=True)
    # The agent hook blocks every write when the session has no role (AGENTS.md section 1): an area worker is
    # gameplay-dev, which may write Source/, Config/ and Content/; the lane guard narrows that to the lane.
    env = dict(os.environ, JAM_ROLE=os.environ.get("JAM_ROLE") or ROLE, JAM_CARD=f"area-{area}")
    return subprocess.call(cmd, cwd=ROOT, env=env)


def cmd_done(area):
    require_clean()
    fetch()
    ref = base_ref()
    _, lane = brief_and_lane(area, ref)
    br = f"area/{area}"
    if not ref_exists(br):
        raise Refused(f"no {br} here. Start it first: {SCRIPT} {area}")
    git("switch", br)
    merge_in(ref, f"main ({ref}) into {br}")
    stray = out_of_lane(git("diff", "--name-only", f"{ref}...{br}").stdout.split(), lane, area)
    if stray:
        raise Refused(f"{br} changes files outside its lane: {', '.join(stray)}. Those go to main by the lead (or by "
                      f"you acting as lead, on main). Nothing was merged.")
    if ref != "main":
        if ref_exists("main"):
            # A push that was rejected leaves this tool's own "Merge area/<x>" commit on local main: drop it and
            # merge again on top of the new origin/main. Any other local-only commit on main is someone's work: stop.
            extra = git("log", "--format=%s", "main", f"^{ref}", f"^{br}").stdout.split("\n")
            extra = [s for s in extra if s]
            if extra and all(s == f"Merge {br}" for s in extra):
                git("branch", "-f", "main", ref)
            git("switch", "main")
            r = git("merge", "--ff-only", ref, check=False)
            if r.returncode != 0:
                git("switch", br)
                raise Refused(f"your local main has commits {ref} does not. Push or drop them first, then retry.")
        else:
            git("switch", "-c", "main", "--track", ref)
    else:
        git("switch", "main")
    r = git("merge", "--no-ff", "--no-edit", "-m", f"Merge {br}", br, check=False)
    if r.returncode != 0:
        git("merge", "--abort", check=False)
        git("switch", br)
        raise Refused(f"merging {br} into main conflicts (should not happen after the main merge):\n{r.stdout}")
    print(f"Merged {br} into main ({last_commit('main')}). Nothing was pushed.")
    if has_remote():
        print(f"Publish it: git push {REMOTE} main {br}\n"
              f"If git says 'rejected' (someone pushed first): run {SCRIPT} {area} --done again, then push again.")
    return 0


def cmd_guard():
    head = git("symbolic-ref", "--short", "-q", "HEAD", check=False).stdout.strip()
    if not head.startswith("area/"):
        return 0
    area = head[len("area/"):]
    ref = next((r for r in (f"{REMOTE}/main", "main", "HEAD") if ref_exists(r)), "HEAD")
    text = show(ref, f"{BRIEFS}/{area}.md") or show("HEAD", f"{BRIEFS}/{area}.md")
    if text is None or not lane_of(text):
        print(f"area guard: no lane for {area} in {BRIEFS}/{area}.md, so nothing is checked.", file=sys.stderr)
        return 0
    lane = lane_of(text)
    staged = set(git("diff", "--cached", "--name-only", "--no-renames").stdout.split("\n"))
    gd = git("rev-parse", "--git-dir").stdout.strip()
    if os.path.exists(os.path.join(gd if os.path.isabs(gd) else os.path.join(ROOT, gd), "MERGE_HEAD")):
        # A merge commit: only the files that differ from both parents are this person's own changes.
        staged &= set(git("diff", "--cached", "--name-only", "--no-renames", "MERGE_HEAD").stdout.split("\n"))
    stray = sorted(out_of_lane(staged, lane, area))
    if stray:
        print(f"area guard: commit refused. On area/{area} you may only commit inside its lane. Outside it:",
              file=sys.stderr)
        for p in stray:
            print(f"  {p}", file=sys.stderr)
        print(f"Unstage them (git restore --staged <file>) and write what you need in {NEEDS}/{area}.md.",
              file=sys.stderr)
        return 1
    return 0


def main(argv=None):
    ap = argparse.ArgumentParser(prog=SCRIPT, description="Resume one area of the build from its branch.")
    ap.add_argument("area", nargs="?")
    ap.add_argument("--agent", choices=("claude", "codex", "none"))
    ap.add_argument("--done", action="store_true")
    ap.add_argument("--prompt", action="store_true")
    ap.add_argument("--guard", action="store_true")
    a = ap.parse_args(argv)
    try:
        if a.guard:
            return cmd_guard()
        if not a.area:
            return cmd_status()
        if a.area.startswith("area/"):
            a.area = a.area[len("area/"):]
        if a.prompt:
            _, lane = brief_and_lane(a.area, base_ref())
            print(prompt(a.area, lane))
            return 0
        if a.done:
            return cmd_done(a.area)
        return cmd_start(a.area, a.agent)
    except Refused as e:
        print(f"area: {e}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
