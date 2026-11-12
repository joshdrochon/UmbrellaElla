#!/usr/bin/env python3
"""A stub agent CLI for the kickoff tests (no model, no network, no credits). It speaks the `claude -p` and
`codex exec` argument shapes tools/kickoff.py sends and obeys AGENTS.md: it refuses to start unless AGENTS.md has
the "Kickoff sessions" contract, starts each reply `ROLE:`, stays in its card's lane, never edits a gate path, honours
D39 unless the repo is a practice repo, commits with `UE-<id>: ...` and `Role: <role>`, never pushes, and writes its
results to $JAM_OUTBOX (cards/, pr.md, review.md, needs-human.txt, comment.md).

Roles: producer (files every Day-0 row whose After cards are closed, Human from the People table), any builder role
(one file in its lane; art, audio and video cards run tools/assetgen.py), any reviewer (JAM_REVIEW=1: a verdict).
Test knobs: STUB_LOG (one JSON line per session), STUB_STATE (dir for once-only knobs), STUB_FAIL_ONCE (card ids
whose first session produces nothing), STUB_FAIL_ALWAYS (card ids whose every session crashes), STUB_EXIT_AFTER_COMMIT_ONCE
(card ids whose first session commits, then exits 3, as a timed-out or crashed session can), STUB_CHANGES_ONCE (card ids whose first review asks for changes),
STUB_SLEEP (seconds per session, to see parallel runs)."""
import json
import os
import re
import subprocess
import sys
import time

ENV = os.environ
ROLE = ENV.get("JAM_ROLE", "")
CARD = ENV.get("JAM_CARD", "")
OUT = ENV.get("JAM_OUTBOX", "")
GAME = ("Source/", "Content/", "Config/")
BINARY = (".umap", ".uasset", ".png", ".wav", ".mp4", ".zip")
PY = sys.executable


def log(**kw):
    if ENV.get("STUB_LOG"):
        with open(ENV["STUB_LOG"], "a", encoding="utf-8") as fh:
            fh.write(json.dumps(dict(kw, role=ROLE, card=CARD, t=time.time())) + "\n")


def once(flag):
    d = ENV.get("STUB_STATE")
    if not d:
        return False
    p = os.path.join(d, re.sub(r"\W", "_", flag))
    if os.path.exists(p):
        return False
    open(p, "w").close()
    return True


def parse_argv(argv):
    if argv[:1] == ["exec"]:
        a = argv[1:]
        assert "-s" in a and a[a.index("-s") + 1] == "workspace-write", argv
        assert "-C" in a and os.path.samefile(a[a.index("-C") + 1], os.getcwd()), argv
        assert "-c" in a and "shell_environment_policy.inherit=all" in a, argv
        return "codex", a[-1]
    assert "-p" in argv, argv
    return "claude", argv[argv.index("-p") + 1]


def write(name, text):
    """An outbox file, LF as git writes (Python's text mode would write CRLF on Windows: a CRLF gate.patch does not
    apply to an LF file)."""
    os.makedirs(os.path.dirname(os.path.join(OUT, name)) or OUT, exist_ok=True)
    with open(os.path.join(OUT, name), "w", encoding="utf-8", newline="\n") as fh:
        fh.write(text)


def git(*a, check=True):
    p = subprocess.run(["git", *a], capture_output=True, text=True)
    if check and p.returncode:
        raise SystemExit(f"stub: git {' '.join(a)}: {p.stderr}")
    return p


def role_name():
    with open("pipeline/agent-ops/gates.json", encoding="utf-8") as fh:
        return json.load(fh)["roles"].get(ROLE, ROLE)


def table_rows(text, heading=None):
    if heading:
        text = text.split(heading, 1)[1].split("\n## ", 1)[0]
    for ln in text.splitlines():
        if ln.startswith("| ") and not ln.startswith("|---"):
            yield [c.strip() for c in ln.strip().strip("|").split("|")]


# ---------- Producer ----------
FORM = """### MVP item (number from docs/jam-brief.md), Day 0, or Stretch: <name>

Day 0

### GDD ref (section + short quote; "none" for tooling cards)

none

### GDD revision (the one in docs/gdd/CURRENT, e.g. 1.3)

1.3

### Features (IDs from docs/feature-manifest.json; add "Hook only" for an interface + default flag with no behavior, OPEN/PROPOSED only; "none" for tooling cards)

none

### Player outcome (the player sees X, does Y, can tell why; "none" for tooling cards)

none

### Owner role

{owner}

### Reviewer role (must differ from owner)

{reviewer}

### Human who runs and merges this

{human}

### Inputs and outputs (exact paths)

Inputs: the files the Done-when names. Outputs: {lane}

### Context (what the code or asset next to Outputs does today, with file:line)

new files only

### File lane, do-not-touch paths, binary files to lock

Lane: {lane}
Do not touch: {dnt}
Locks: {locks}

### Out of scope (behaviors not to build; the reviewer rejects them)

anything outside the lane

### After (cards that must merge first: #<n> or UE-<n>, comma separated; "none")

{after}

### Used by (BPs, maps, widgets or components that read what this card changes; follow-up card IDs)

none (kickoff stub)

### Needs (build | tests | editor MCP | Windows packaging machine)

{needs}

### Done when (each line checkable)

{done}

### Budget and cut tier

{budget}, MVP

### Unknowns (Decision needed / Why it matters / Proposed test / Choice; "none" if none)

none
"""
SEATS = {"td human": "technical director, human", "integration owner": "integration owner",
         "game design owner": "game design owner", "human producer": "producer / time keeper",
         "each teammate": "producer / time keeper", "packaging and submission owner": "packaging and submission owner",
         "playtest lead": "playtest lead", "audio owner": "audio owner",
         "packaging machine owner": "windows packaging machine"}
BIG = {"0.3", "0.4d", "0.25", "0.26"}


def people():
    with open("docs/jam-brief.md", encoding="utf-8") as fh:
        text = fh.read()
    out = {}
    for cells in table_rows(text, "## People"):
        if len(cells) >= 2 and cells[0] != "Role":
            out[cells[0].lower()] = re.split(r"[ ,(]", cells[1])[0]
    return out


def person(seat, ppl):
    seat = re.sub(r"\s*\(sign-off:[^)]*\)", "", seat).strip()   # "TD human (sign-off: guardrails)" -> the seat
    key = SEATS.get(seat.lower())
    if key:
        return next(v for k, v in ppl.items() if k.startswith(key))
    return seat or next(v for k, v in ppl.items() if k.startswith("producer"))


def producer():
    with open(os.path.join(OUT, "issues.json"), encoding="utf-8") as fh:
        issues = json.load(fh)
    have = {}
    for i in issues:
        m = re.match(r"\[UE-([^\]]+)\]", i["title"])
        if m:
            have[m.group(1)] = i
    done = {k for k, i in have.items() if i["state"] == "CLOSED" and not set(i["labels"]) & {"cut", "superseded"}}
    with open("pipeline/day0-cards.md", encoding="utf-8") as fh:
        rows = [c for c in table_rows(fh.read()) if len(c) == 7 and re.fullmatch(r"0\.\d+[a-z]?", c[0])]
    only = set(filter(None, ENV.get("STUB_DAY0_ONLY", "").split(",")))
    ppl = people()
    n = 0
    for num, title, owner_human, reviewer, lane, after, done_when in rows:
        if only and num not in only:
            continue
        deps = re.findall(r"0\.\d+[a-z]?", after)
        if only:
            deps = [d for d in deps if d in only]
        if num in have or not all(d in done for d in deps):
            continue
        owner, _, human = (p.strip() for p in owner_human.partition("/"))
        is_map = ".umap" in lane
        body = FORM.format(
            owner=owner, reviewer=reviewer, human=person(human, ppl), lane=lane,
            after=", ".join("UE-" + d for d in deps) or "none",
            dnt="other maps under Content/UmbrellaElla/Maps/" if is_map else "Content/UmbrellaElla/Maps/**",
            locks=(re.search(r"Content/\S+?\.umap", lane).group(0) if is_map else "none"),
            needs="build, tests" + (", Windows packaging machine" if "package.ps1" in done_when else ""),
            budget="120 min agent + 60 min human" if num in BIG else "60 min agent + 15 min human",
            done="\n".join("- [ ] " + d.strip() for d in done_when.split("<br>")))
        write(f"cards/UE-{num}.json", json.dumps({"title": f"[UE-{num}] {title}", "body": body}))
        n += 1
    print(f"ROLE: Producer | session stub\nfiled {n} card(s)")


# ---------- builders ----------
def lane_of(body):
    m = re.search(r"^Lane:\s*(.*)$", body, re.M)
    return m.group(1) if m else ""


def is_gate(path):
    p = subprocess.run([PY, "tools/git_gate.py", "check", path], capture_output=True, text=True)
    return bool(p.stdout.strip())


def target(lane):
    for g in re.findall(r"`([^`]+)`", lane):
        g = g.split(" ")[0]
        base = re.split(r"[*{]", g, 1)[0]
        path = (base.rstrip("/") + "/KICKOFF-" + CARD + ".md") if base != g or g.endswith("/") else g
        if g.endswith(BINARY) or not path.endswith((".md", ".ini")) or is_gate(path):
            continue
        return path
    return None


def gate_target(lane):
    """A gate path inside the lane for the stub's gate.patch: a new file under a lane folder, or the lane file."""
    for g in re.findall(r"`([^`]+)`", lane):
        g = g.split(" ")[0]
        base = re.split(r"[*{]", g, 1)[0]
        path = (base.rstrip("/") + "/KICKOFF-" + CARD + ".md") if base != g or g.endswith("/") else g
        if not g.endswith(BINARY) and is_gate(path):
            return path
    return None


def gate_patch(path, extra=None):
    """The honest way: make the change in the worktree, write `git diff` as gate.patch, put the worktree back
    (an agent session never commits a gate path; kickoff applies the patch). extra (STUB_GATE_EXTRA, broken on
    purpose): a second path outside the lane; for gates.json the stub also drops a gate path (a loosening)."""
    existed = os.path.exists(path)
    if existed and path.endswith(".json"):
        with open(path, encoding="utf-8") as fh:
            data = json.load(fh)
        data["_stub_" + CARD] = "stub gate work"
        if "gate_paths" in data:
            data["gate_paths"] = data["gate_paths"][1:]
        with open(path, "w", encoding="utf-8", newline="\n") as fh:   # keep the file's LF endings on Windows
            json.dump(data, fh, indent=1)
            fh.write("\n")
    else:
        os.makedirs(os.path.dirname(path) or ".", exist_ok=True)
        with open(path, "a", encoding="utf-8", newline="\n") as fh:
            fh.write(f"\n# {CARD} stub gate work\n" if path.endswith((".yml", ".yaml", ".py", "ignore", "CODEOWNERS"))
                     else f"\n<!-- {CARD} stub gate work -->\n")
    if not existed:
        git("add", "-N", path)
    diff = git("diff", "--", path).stdout
    if existed:
        git("checkout", "--", path)
    else:
        git("rm", "-q", "--cached", path)
        os.remove(path)
    if extra:
        write("gate.patch", "")
        gate_patch(extra)
        with open(os.path.join(OUT, "gate.patch"), encoding="utf-8") as fh:
            diff += fh.read()
    write("gate.patch", diff)


def assetgen(*args):
    p = subprocess.run([PY, "tools/assetgen.py", *args], capture_output=True, text=True)
    print(p.stdout.strip())
    return p.returncode


def art_card():
    sheet = "Art/Sprites/Ella/ella_idle.png"   # Blender renders in the session: art needs no key, nothing queues
    assert assetgen("blender", "--character", "ella", "--anim", "IdleFloat", "--sheet", sheet) == 0
    write("art-pieces.json", json.dumps({"ella-up-open": sheet}))   # the art loop's piece -> file map
    # the in-engine capture with the piece in it (the smoke's screenshot; the stand-in game's is the key art)
    os.makedirs(os.path.join("Saved", "Logs", "pipeline"), exist_ok=True)
    with open("pipeline/art/reference/target-keyart.png", "rb") as src, \
            open(os.path.join("Saved", "Logs", "pipeline", "smoke-L_Arena-shot.png"), "wb") as dst:
        dst.write(src.read())
    p = subprocess.run([PY, "tools/sprite_check.py", "--scan", "Art/Sprites"], capture_output=True, text=True)
    assert p.returncode == 0, p.stdout + p.stderr
    return "Evidence:\n```\n" + p.stdout.strip()[-600:] + "\n```\n"


def audio_card():
    raw = "Audio/Raw/gust_catch_raw.wav"
    final = "Audio/Source/GustCatch/SW_GustCatch_00.wav"
    if not os.path.exists(raw):
        assert assetgen("sfx", "--sound", "GustCatch", "--prompt", "short wind gust", "--out", raw, "--seconds", "1.0") == 3
        return "queued"
    assert assetgen("edit", "--in", raw, "--out", final, "--fade-ms", "5") == 0
    p = subprocess.run([PY, "tools/audio_check.py", "--scan", "Audio/Source"], capture_output=True, text=True)
    mine = [ln for ln in (p.stdout + p.stderr).splitlines() if final in ln]
    assert mine and not any(ln.startswith("FAIL") for ln in mine), p.stdout   # other P0 sounds come from other cards
    return "Evidence:\n```\n" + "\n".join(mine) + "\n```\n"


def video_card():
    raw, out = "Saved/Video/raw.mkv", "pipeline/submission/video/gameplay.mp4"
    assert assetgen("capture", "--exe", ENV["STUB_GAME_EXE"], "--seconds", "50", "--out", raw) == 0
    assert assetgen("cut", "--in", raw, "--out", out, "--duration", "45") == 0
    p = subprocess.run([PY, "tools/submission_check.py", "video", out], capture_output=True, text=True)
    assert p.returncode == 0, p.stdout
    return "Evidence:\n```\n" + p.stdout.strip() + "\n```\n"


def builder():
    with open(os.path.join(OUT, "card.json"), encoding="utf-8") as fh:
        card = json.load(fh)
    body, number = card["body"], card["number"]
    issue = f"#{number}"
    if CARD in set(ENV.get("STUB_FAIL_ONCE", "").split(",")) and once("fail-" + CARD) or \
            CARD in set(ENV.get("STUB_FAIL_ALWAYS", "").split(",")):
        print("ROLE: stub | crashed on purpose")
        raise SystemExit(1)
    lane = lane_of(body)
    asks = []
    evidence = ""
    kind = "art" if "Art/Sprites/Ella" in lane else "audio" if "Audio/Source/GustCatch" in lane else \
        "video" if "pipeline/submission/video" in lane else "plain"
    if kind != "plain":
        res = {"art": art_card, "audio": audio_card, "video": video_card}[kind]()
        if res == "queued":
            print(f"ROLE: {role_name()} | session stub\nasset requests queued")
            return
        evidence = res
    else:
        path = target(lane)
        if path is None:
            if "GitHub only" in lane or not lane.strip("` "):
                write("comment.md", f"ROLE: {role_name()} | session stub\nprepared, not posted: {CARD} needs no files")
            else:
                gate = gate_target(lane)
                if gate:   # the agent does the gate work; kickoff applies it (tools/git_gate.py apply --auto)
                    gate_patch(gate, ENV.get("STUB_GATE_EXTRA") or None)
                    write("pr.md", pr_body(issue, body, "", changed=gate))
                else:
                    write("comment.md", f"ROLE: {role_name()} | session stub\n{CARD}: every lane path is a binary "
                                        "file; the editor change is described below (prepared, not posted)")
                    asks.append(f"NEEDS HUMAN: Josh make the gate or binary edit the diff above describes for {CARD} "
                                f"{issue} {time.strftime('%Y-%m-%dT%H:%MZ', time.gmtime())}")
            if asks:
                write("needs-human.txt", "\n".join(asks) + "\n")
            print(f"ROLE: {role_name()} | session stub")
            return
        if path.startswith(GAME) and not os.path.exists(".pipeline-practice"):
            write("needs-human.txt", f"NEEDS HUMAN: Rick D39 forbids game files before the jam start ({path}) {issue} "
                                     f"{time.strftime('%Y-%m-%dT%H:%MZ', time.gmtime())}\n")
            print("ROLE: stub | refused by D39")
            return
        os.makedirs(os.path.dirname(path) or ".", exist_ok=True)
        with open(path, "a", encoding="utf-8") as fh:
            fh.write(f"\n; {CARD} stub work\n" if path.endswith(".ini") else f"\n<!-- {CARD} stub work -->\n")
    git("add", "-A")
    git("commit", "-q", "-m", f"{CARD}: stub work in the lane\n\nRole: {role_name()}")
    if asks:
        write("needs-human.txt", "\n".join(asks) + "\n")
    if kind == "art":   # art paths need the reference check (check_pr rule artref), on the commit it pushes
        r = subprocess.run([PY, "tools/art_ref_check.py", "--card", CARD.replace("UE-", ""), "--element",
                            "ella-up-open", "Art/Sprites/Ella/ella_idle.png"], capture_output=True, text=True)
        evidence += "Evidence:\n```\n" + r.stdout.strip() + "\n```\n"
    m = re.search(r"art_ref_check\.py --card (\S+) --scene (pipeline/art/reference/target-keyart\.png)", body)
    if m:   # an honest agent runs the reference check its Done-when names, on the commit it pushes
        p = subprocess.run([PY, "tools/art_ref_check.py", "--card", m.group(1), "--scene", m.group(2)],
                           capture_output=True, text=True)
        evidence += "Evidence:\n```\n" + p.stdout.strip() + "\n```\n"
    if kind == "art":   # no header: kickoff's own art-loop pass-record commit comes after it (see pr_body)
        write("pr.md", f"## Task\nPart of {issue}. Card ID: {CARD}  Owner role: {role_name()}\n\n## Evidence\n{evidence}")
    else:
        write("pr.md", pr_body(issue, body, evidence))
    if CARD in set(ENV.get("STUB_EXIT_AFTER_COMMIT_ONCE", "").split(",")) and once("exit-" + CARD):
        print("ROLE: stub | committed half the work, then crashed on purpose")
        raise SystemExit(3)
    print(f"ROLE: {role_name()} | session stub\ncommitted")


def card_section(body, heading):
    m = re.search(rf"^### {re.escape(heading)}[^\n]*\n+(.*?)(?=^### |\Z)", body, re.M | re.S)
    return m.group(1).strip() if m else ""


def pr_body(issue, body, evidence, changed=None):
    """The whole PR template, as an honest agent fills it: the header names the commit it pushes (check_pr reads
    the body at the head before kickoff merges), what it did not run says so, the journal export is pasted.
    Not for art cards: kickoff commits the art-loop pass record after the session, so a header naming the session's
    commit never matches the pass line's commit and the art gate fails the card (open: how check_pr treats that commit)."""
    head = git("rev-parse", "HEAD").stdout.strip()
    base = git("merge-base", "origin/main", "HEAD", check=False).stdout.strip() or "HEAD~1"
    changed = "\n".join(git("diff", "--name-only", f"{base}..HEAD").stdout.split() + ([changed] if changed else [])) \
        or "none"
    reviewer = card_section(body, "Reviewer role") or "Dev Lead"
    done = "\n".join(f"- [ ] {ln.lstrip('-* ').strip()}" for ln in card_section(body, "Done when").splitlines()
                     if ln.strip()) or "- [ ] the card's Done-when"
    journal = subprocess.run([PY, "tools/journal.py", "export", "--card", CARD], capture_output=True, text=True).stdout
    return (f"## Task\nPart of {issue}. Card ID: {CARD}  Owner role: {role_name()}  Reviewer role: {reviewer}\n\n"
            f"## What changed\n{changed}\n\n## Done-when checks\n{done}\n\n"
            f"## Evidence\ncommit={head[:12]} engine=none config=none host=mac run=none\n"
            f"{evidence or 'Not run: Unreal build, tests and package, this stub lane changes no Source/, Config/ or map'}\n\n"
            f"## Not done / risks\nnone\nCould not read: none\nNext: {reviewer} reviews {issue}\n\n"
            f"## Binary assets touched\nnone\n\n## Journal\n{journal.strip() or 'none'}\n")


def critic():
    """A blind art critic session (kickoff's art loop): the folder holds lettered X/Y pairs and prompt.md. The stub
    peeks at the sealed key beside the folder (a real critic never sees it) to answer the calibration pairs right,
    and answers the judged pair by STUB_CRITIC: pass (SAME) or fail (the other image wins)."""
    with open(os.getcwd().rstrip("/") + ".key.json", encoding="utf-8") as fh:
        key = json.load(fh)
    lines = [f"{f}: WINNER: {w} | GAP: -" for f, w in sorted(key["calibration"].items())]
    if ENV.get("STUB_CRITIC", "pass") == "pass":
        lines.append(f"{key['folder']}: WINNER: SAME | GAP: none")
    else:
        lines.append(f"{key['folder']}: WINNER: {'Y' if key['ours'] == 'X' else 'X'} | GAP: the ink lines are too even")
    write("verdict.md", "\n".join(lines) + "\n")
    print("\n".join(lines))


def reviewer():
    verdict = "changes" if CARD in set(ENV.get("STUB_CHANGES_ONCE", "").split(",")) and once("rev-" + CARD) \
        else "approve"
    write("review.md", f"ROLE: {role_name()} | session {time.strftime('%Y-%m-%dT%H:%MZ', time.gmtime())}\n"
                       f"VERDICT: {verdict}\nRead the diff against the card lane.\n")
    print(f"ROLE: {role_name()} | review {verdict}")


def main(argv):
    agent, prompt = parse_argv(argv)
    if ENV.get("JAM_REVIEW") == "1" and os.path.isfile("prompt.md") and os.path.isdir("A"):
        log(event="start", agent=agent, cwd=os.getcwd(), review=True, critic=True)
        critic()   # a blind critic folder: no repo, no AGENTS.md, only the pairs and the fixed prompt
        log(event="end")
        return 0
    with open("AGENTS.md", encoding="utf-8") as fh:
        agents = fh.read()
    sec = agents.split("Kickoff sessions", 1)[1][:1500] if "Kickoff sessions" in agents else ""
    for word in ("JAM_OUTBOX", "pr.md", "review.md", "needs-human.txt", "cards/", "VERDICT"):
        if word not in sec:
            print(f"stub: AGENTS.md has no kickoff contract for {word}; refusing")
            return 3
    assert prompt.startswith(f"ROLE: {ROLE}."), prompt[:80]
    log(event="start", agent=agent, cwd=os.getcwd(), review=ENV.get("JAM_REVIEW") == "1",
        has_key=any(ENV.get(k) for k in ("OPENAI_API_KEY", "ELEVENLABS_API_KEY", "STABILITY_API_KEY")))
    time.sleep(float(ENV.get("STUB_SLEEP", "0")))
    if CARD == "KICKOFF-PRODUCER":
        producer()
    elif ENV.get("JAM_REVIEW") == "1":
        reviewer()
    else:
        builder()
    log(event="end")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
