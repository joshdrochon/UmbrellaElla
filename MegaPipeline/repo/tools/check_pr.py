#!/usr/bin/env python3
"""Fail a PR whose body leaves a required template section empty.

Reads the PR body from $GITHUB_EVENT_PATH (GitHub Actions) or from a file argument.
Required sections come from .github/PULL_REQUEST_TEMPLATE.md.

Also checks:
  header    Evidence starts with the AGENTS.md section 5 line
            `commit=<sha> engine=5.8.4 config=<..> host=<win|mac> run=<..>`; with a known PR head
            (event or --head), the commit must match it, or the evidence is stale
  package   if the PR changes maps (*.umap), Config/**, *.Build.cs, *.Target.cs or *.uproject, or its
            Done-when (copied from the card) asks for package + SMOKE_OK, Evidence has the package
            script's `package exit: 0` line and the game's `SMOKE_OK map=<map> ...` line. "not run" for
            package or smoke fails (a human on the packaging machine adds the evidence before merge).
            Every SMOKE_OK line needs commit= (matching the header commit) and workbench=0. Changed paths come from
            --changed FILE (one per line, CI passes `git diff --name-only`) plus any such path named
            under "What changed"
  nonunity  if a changed path (--changed or "What changed") is under Source/, the header says engine=5.8.4 and a
            run other than none, and Evidence has the line `build exit: 0  mode=nonunity` that NONUNITY=1
            tools/ue/build.sh / build.ps1 -NonUnity prints, at the start of a line (D-new-nonunity-pr)
  exact     success lines are the tools' own lines at the start of a line (`package exit: 0`, `build exit: 0`,
            `PASS  tests=<n> failed=0`, the game's `[..]LogX: SMOKE_OK map=...` log line); a look-alike after
            other text ("expected:", "Not run:") fails. Any failing line of those kinds fails the PR, whatever
            else is pasted: `package exit: <n>0`, `build exit: <n>0`, `FAIL  tests=`, `SMOKE_FAIL` (final-6 B H6)
  commit    the build, test and package lines name the commit they ran on, and it is the header commit; the
            package line says dirty=no (final-7 B H7, M8): `build exit: 0  mode=nonunity  commit=<sha>`,
            `PASS  tests=<n> failed=0  commit=<sha>`, `package exit: 0  commit=<sha>  dirty=no`. The SMOKE_OK line
            may keep the `<file>.log:<n>:` prefix of a grep -n / Select-String hit; smoke.sh / smoke.ps1 print the
            game's line as is (final-7 A H2)
  run       the smoke script's own verdict, not only the game's SMOKE_OK line (final-8 A H1): with a SMOKE_OK line,
            Evidence also has smoke-log's `smoke: exit=0 SMOKE_OK=yes ...` summary with every count 0 and
            crash-check's `crash folders: 0 new`. Any tool failure line at the start of a line (`FAIL: ...`,
            `FAIL  tests=`, `crash folders: <n> new` with n > 0, a summary with exit or a count above 0) fails
  planted   a card whose Done-when asks for a failure on purpose (MustFail, a planted telegraph, a flipped flag,
            SMOKE_FORCE_CRASH) pastes it under a line `PLANTED FAIL: <what>`; that block runs to the next blank
            line. Its lines are neither failures nor passes. The block is allowed only when the linked card's
            Done-when (or, without --card, the PR's copy) has FAIL in capitals (final-8 A H3)
  card      with --card (CI passes the linked issue), the card's own Done-when also decides package evidence; a
            PR that needs package evidence has run=packaged in its header (final-6 A H4)
  proof     Evidence (below the header) has at least one re-runnable line: a command (`backticks`, tools/...,
            *.py/*.sh/*.ps1), tool output (PASS, FAIL, OK, exit N, key=value, "problem(s)", SMOKE_OK), a capture
            path (.png/.mp4/.log), or a "Not run: <what>, <why>" line. "all good, trust me" fails
  tests     if a changed path is under Source/, Evidence has the `tools/check_automation_report.py` result line
            (`PASS  tests=<n> failed=0`); a human on a CAN RUN build=n card pastes it before merge. The bootstrap
            line `... (bootstrap: placeholder tests only, card 0.3)` counts only when the Card ID is UE-0.3
  smoke     the SMOKE_OK line meets the smoke contract in tools/ue_run.py (fps, worst_ms, input=ok with a negative
            input_vz on a gameplay map, load_ms, a 16:9 gameplay view: view=WxH aspect=N within 0.01 of 1.778 and
            filling the window on one axis, and debugdraw=0: no debug draw in a default launch),
            when a .umap changed, map= names one of the changed maps, and a workbench= field reads 0: PR
            evidence comes from the submission package, never the -Workbench tester package (D-new-workbench-debug)
  bootstrap two scoped Day-1 exceptions to the package rule, each tied to repo state at the PR head so it ends
            by itself (dry run A C1: card 0.3 must merge before the smoke hook or MVP 2 exist):
              smoke  while Source/UmbrellaElla/Private/Smoke/ does not exist (card 0.6 not merged, and this PR does
                     not add it), `package exit: 0` plus a `SMOKE_BOOTSTRAP: no smoke hook before card 0.6` line
                     stands in for SMOKE_OK. Once the hook exists the line fails
              input  while the pipeline/qa/test-map.md QA-01 row (MVP 2 lift, UMB-01) is not `merged`, SMOKE_OK may
                     read input=none if Evidence shows the run used SMOKE_REQUIRE_INPUT=0 (card 0.6). After MVP 2
                     merges, input=ok is required again
            Nothing else is waived: "not run" still fails, and fps, worst_ms, load_ms and workbench still apply.
            Both waivers fail closed: a QA-01 Status other than exactly `planned` ends the input waiver, and any
            Source/ file that writes SMOKE_OK ends the smoke waiver (final-6 B M7, M8)
  art       every smoke ran art_check.py and screen_check.py on its own default-build screenshot (tools/ue_run.py
            smoke-log --shot): once the smoke hook exists, Evidence with a SMOKE_OK line also has the smoke's
            `smoke-art: art_check: PASS` and `smoke-art: screen_check: PASS ...` lines (and, on a map with a player,
            `smoke-art: art_judge: PASS scene ...`: the key-art composition judge), and any `smoke-art: <tool>: FAIL`
            fails. GitHub CI cannot run Unreal: the checks run in the smoke on the build machine (smoke.sh / smoke.ps1,
            the daily, kickoff's art gate) and this rule rejects a PR whose pasted smoke lacks them. Art bootstrap
            (repo state, ends by itself): until Content/UmbrellaElla/Art/Anchors/ exists (card 0.10b) a FAIL is
            accepted next to the smoke's `smoke-art: bootstrap: not blocking ...` line; after that the line fails.
            A PR that changes Content/**, pipeline/art/visual-align.json or UI or presenter code
            (Source/UmbrellaElla/*/UI/**, */Feedback/**) needs package + smoke evidence, so the art lines too
  artref    a PR that changes an art path (Content/*/Art/**, Content/*/UI/**, Content/*/VFX/**, Art/**,
            pipeline/art/**, *.sprite.json) or whose linked card is an art
            card (a card that pipeline/art/references.json assigns references to) has the line tools/art_ref_check.py
            prints: `art_ref_check: PASS card=<id> target=... refs=<hash12> commit=<sha> ...`, on the header commit and
            the current references.json hash (a PASS made against an older or smaller reference set fails); an art
            card's line names that card. Any `art_ref_check: FAIL` fails. The smoke's art_judge line carries refs= too
  artloop   a linked art card also has the `art_loop: PASS card=<id> piece=<p> verdict=<ours|same> ... refs=<hash12>
            commit=<sha>` line of each of its pieces (tools/art_loop.py: builder and blind critic until the critic
            cannot pick the reference over ours and every deterministic check passes; no round cap)
  artship   a PR that adds or changes shipped art (an image under Art/ outside Art/Source/) has, per file, the
            `art_loop: PASS ... commit=<header> file=<path> sha=<sha12>` line and the committed <stem>.artloop.json
            record for those exact bytes: a panel of 3 calibrated blind critics, unanimous ours or SAME against every
            reference of its element, the quality bar, the motion pair (a sheet) and the in-engine context; art_check,
            screen_check and art_ref_check PASS; current references.json. The gate re-runs those checks on the file
            itself (the record's word is not taken) and the record must name the piece its provenance names; only
            kickoff's art loop writes records (gates.json kickoff_only_paths). A Content/*/Art, VFX or UI .uasset
            change (visible UI too: menu screens, HUD art; not string tables, data tables or fonts) needs that line
            for the image it came from. A labelled placeholder or stand-in never passes; no label, sign-off or human
            approval waives it (tools/art_loop.py record_problems)
  hitbox    if the PR changes pipeline/feel/hitboxes.json, pipeline/art/visual-align.json or a sprite PNG hitboxes.json
            names (an art swap), Evidence has the `hitbox_check: PASS entities=<n> ...` line of
            `python3 tools/hitbox_check.py check`: the art was aligned to its collider and the check re-ran. A FAIL
            line from it fails the PR
  audio     if the PR changes a sound (a path under Audio/Source/<Id>/ or Content/UmbrellaElla/Audio/<Id>/, Core
            excluded), Evidence has the lines `python3 tools/audio_loop.py close --card <id>` prints, for the evidence
            header commit: `audio_loop close: PASS card=<the Task's Card ID> ...`, `audio_style check: PASS files=<n>
            commit=<sha> dirty=no`, and one `AUDIO LOOP: PASS piece=<Id> ... critic=<s> builder=<s> ...` line per
            changed sound id, with a critic session that is not the builder's. Any `audio_loop close: FAIL`,
            `audio_style check: FAIL` or `AUDIO LOOP: FAIL` line fails (pipeline/audio/style-target.md section 5).
            A sound whose every take is a tracked placeholder in this tree's provenance (the audio API could not
            make it) has the `AUDIO PLACEHOLDER: piece=<Id> ... commit=<sha>` line in place of its AUDIO LOOP line
  encounter if the PR changes pipeline/level/encounter.json, Evidence has `encounter_check: 0 problem(s)` and the PR
            carries `Encounter phases: <preset>/<phase>, ...` (or `Encounter phases: none (<why>)`). For each listed
            phase (in the PR or the linked card) the encounter critic loop must have passed: the newest
            `ENCOUNTER CRITIC:` line is PASS on the phase's current spec hash, by a critic session that is not the
            builder, each round with its playthrough= and check= scores (no round cap; stuck = 3 FAIL rounds with
            the same gap and no better score, then needs-human); plus the `playthrough_check: 0 problem(s)` and `encounter_ready: 0 problem(s)`
            lines (tools/encounter_spec.py C6-C9). A card or PR that lists phases needs them even without a data change
  bake      if the PR changes pipeline/qa/baked.json (tools/bake_preset.py), Evidence has its
            `bake_preset check: PASS preset=T-nn` line (D-new-workbench-debug)
  story     if the PR changes pipeline/story/** (the story bible, the text lines), Evidence has the
            `story_check: PASS bible=<h> sheet=<h> lines=<n> ...` line of `python3 tools/story_check.py` and the final
            `STORY_CRITIC: PASS ...` line of a separate critic session (tools/story_critic_prompt.md): same bible and
            sheet hashes as that PASS line and as the PR's files (any cycle: no cap), critic session other than
            the builder's. If it changes Content/UmbrellaElla/UI/ST_UI.csv or pipeline/submission/itch-page.md, Evidence
            has a `story_check: PASS` line (`--scan <file>`). Any `story_check: FAIL` line fails the PR. With --base, a
            bible row newly set to CONFIRMED needs `STORY CONFIRM: by=<game design owner> <row ids>` under Evidence: only
            Richard confirms canon (pipeline/roles/story.md)
  editor    if a changed path (--changed or "What changed") is a .uasset or .umap (editor MCP work included), Evidence
            has an `EDITOR CHECK: by=<the card's human> opened=<path>[,<path>...] ok` line naming every changed asset:
            the card's human opened each one in the editor and checked it (pipeline/agent-ops/editor-mcp.md)
  gate      a changed path that is a gate path (pipeline/agent-ops/gates.json gate_paths). On a card PR it came
            through kickoff's tool route, read from git (base..head), not from the PR body: every commit that changes
            a gate path has the trailer `GATE EDIT: by=kickoff <path>[,<path>]` (tools/git_gate.py apply --auto)
            naming it, and this rule re-runs the tool checks with --card, --base and --head (lane, guardrail
            enforcers, no loosening). A person's `GATE EDIT: by=<name>` line fails on a card PR (no human route an
            agent cannot forge). A PR with no card: a `GATE EDIT: by=<name> <path>[,<path>]` line under Evidence.
            No local git hook checks gate paths: this rule and kickoff's merge gate do
  task      the Task section links the card: `Part of #<n>` (D-new-port-1 default) or
            `Closes|Fixes|Resolves #<n>`. Both pass until D-new-port-1 is decided
  links     every line under "Not done / risks" (except "none" and the Next: line) has a link:
            #<n>, a D-row id, or a URL
  next      a `Next:` line with a value under "Not done / risks"
  unread    a `Could not read:` line with a value under "Not done / risks": the card Inputs and cited docs the agent
            could not open (missing on main, an LFS pointer, no access), or "none". Nothing may rest on an unread
            source (docs/coverage-map.md, ported rule)
  journal   (not for a linked card whose Owner role is Human: its Journal says `Human card, no agent session`)
            "## Journal" holds the block `python3 tools/journal.py export --card <id>` prints: its
            `journal.py export card=<id>` line names the Task's Card ID, and it has a `Next step:` line
  gdd       if a changed path (--changed or "What changed") is under docs/gdd/ or is docs/feature-manifest.json, a
            "## GDD impact" section holds the pasted `tools/gdd_impact.py <old> <new>` output: its
            `gdd_impact old=<rev> new=<rev> ...` line and its `cited by:` list (docs/gdd/README.md)
  revert    a PR whose Evidence has `Revert of: <sha>` (tools/lane_guard.py writes it) is the revert-first PR of
            AGENTS.md section 6: it passes when its diff against the base (--base) is exactly the inverse of that
            commit (the same removed and added lines per file; context may differ, so a non-tip revert passes),
            every section is filled, Not done lines link, and the Journal says `Revert bot, no agent session`.
            Build, test, package and smoke evidence are not asked; the next daily builds and smokes main
            (final-10 A H3, final-11 A H2)
Usage: python3 tools/check_pr.py [body.md] [--changed files.txt] [--head SHA] [--base SHA]
"""
import argparse
import fnmatch
import json
import os
import re
import subprocess
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SMOKE_HOOK_DIR = "Source/UmbrellaElla/Private/Smoke"
TEST_MAP = "pipeline/qa/test-map.md"
SMOKE_BOOTSTRAP = re.compile(r"^\W*SMOKE_BOOTSTRAP:\s*no smoke hook before card 0\.6\b", re.I | re.M)
INPUT_BOOTSTRAP = re.compile(r"\bSMOKE_REQUIRE_INPUT=0\b")
GAMEPAD_BOOTSTRAP = re.compile(r"\bSMOKE_REQUIRE_GAMEPAD=0\b")
PACKAGE_GLOBS = ["*.umap", "Config/*", "*.Build.cs", "*.Target.cs", "*.uproject"]
# Visual paths: game art, UI and presenter code. A PR touching one needs package + smoke evidence, and with it the
# smoke's art_check / screen_check lines (rule art)
VISUAL_GLOBS = ["Content/*", "pipeline/art/visual-align.json", "Source/UmbrellaElla/*/UI/*",
                "Source/UmbrellaElla/*/Feedback/*"]
ART_LINE = re.compile(r"^[ \t>$-]*smoke-art: (?P<tool>art_check|screen_check|art_judge): (?P<v>PASS|FAIL)\b.*$", re.M)
# Art paths for rule artref: game art, sprites, VFX and UI art, and the art rules and references themselves
ART_PATHS = ["Content/*/Art/*", "Content/*/UI/*", "Content/*/VFX/*", "Art/*", "pipeline/art/*", "*.sprite.json"]
ART_LEDGERS = {"pipeline/art/provenance.csv"}   # the asset ledger: every asset card (audio too) appends to it
ART_REF_LINE = re.compile(r"^[ \t>$-]*art_ref_check: (?P<v>PASS|FAIL) card=(?P<card>\S+) target=\S+ score=\S+ min=\S+ "
                          r"refs=(?P<refs>[0-9a-f]{12}) commit=(?P<commit>\S+)", re.M)
ART_LOOP_LINE = re.compile(r"^[ \t>$-]*art_loop: PASS card=(?P<card>\S+) piece=(?P<piece>\S+) verdict=(?P<v>ours|same) "
                           r"rounds=\d+ refs=(?P<refs>[0-9a-f]{12}) commit=(?P<commit>\S+)", re.M)
ART_LOOP_FILE = re.compile(r"^[ \t>$-]*art_loop: PASS card=(?P<card>\S+) piece=(?P<piece>\S+) verdict=(?P<v>ours|same) "
                           r"rounds=\d+ refs=(?P<refs>[0-9a-f]{12}) commit=(?P<commit>\S+) file=(?P<file>\S+) "
                           r"sha=(?P<sha>[0-9a-f]{12})", re.M)
# Engine assets that ship art, visible UI included (menu screens, HUD art): a change to one needs a file-bound
# art_loop PASS for the image it was imported from. Only non-visual data stays out: string tables, data tables, fonts.
SHIP_CONTENT = ["Content/*/Art/*.uasset", "Content/*/VFX/*.uasset", "Content/*/UI/*.uasset"]
NOT_VISUAL = ("ST_", "DT_", "Font_", "F_")


def ships_art(p):
    name = p.rsplit("/", 1)[-1]
    return any(fnmatch.fnmatch(p, g) for g in SHIP_CONTENT) and "/Fonts/" not in p and not name.startswith(NOT_VISUAL)
SMOKE_REFS = re.compile(r"^[ \t>$-]*smoke-art: art_judge: (?:PASS|FAIL)\b.*?\brefs=(?P<refs>[0-9a-f]{12})", re.M)
ART_BOOT = re.compile(r"^[ \t>$-]*smoke-art: bootstrap: not blocking\b", re.M)
HEADER = re.compile(r"commit=(?P<commit>[0-9a-f]{7,40})\b.*?\bengine=(?P<engine>5\.8\.4|none)\b"
                    r".*?\bconfig=(?P<config>Development|Shipping|none)\b.*?\bhost=(?P<host>win|mac)\b"
                    r".*?\brun=(?P<run>PIE|Standalone|packaged|none)\b", re.I)
TASK_LINK = re.compile(r"\b(?:Closes|Fixes|Resolves|Part of)\s+#(\d+)", re.I)
# Exact tokens on the success path (dry run A H3, H4; B H6): each is the line the tool itself prints, at the start of
# the line. A look-alike anywhere else in a line never counts, and any failing line of the same kind fails the PR.
PACKAGE_LINE = re.compile(r"^[ \t>$-]*package exit: (?P<rc>-?\d+)\b", re.M)          # tools/ue/package.sh / .ps1
# Final-7 B H7, M8: the build, test and package lines carry the commit they ran on (and the package its dirty flag),
# so a line left over from an earlier push, or from a package of an uncommitted tree, never passes.
PACKAGE_OK = re.compile(r"^[ \t>$-]*package exit: 0\s+commit=(?P<commit>[0-9a-f]{7,40})\s+dirty=(?P<dirty>\w+)", re.M)
BUILD_LINE = re.compile(r"^[ \t>$-]*build exit: (?P<rc>-?\d+)\s+mode=(?P<mode>\S+)"
                        r"(?:\s+commit=(?P<commit>[0-9a-f]{7,40})\b)?", re.M)  # tools/ue/build.sh / .ps1
# The game's log line: optional [timestamp][frame] prefixes and a `LogX: [Verbosity:]` category, then SMOKE_OK.
# smoke.sh / smoke.ps1 print that line as is (ue_run.py smoke-log). A `grep -n` or `Select-String` hit on the log
# keeps its `<file>.log:<n>:` / `<n>:` prefix; that prefix is allowed too (final-7 dry run A H2).
SMOKE_GREP_PREFIX = r"(?:(?:[A-Za-z]:)?[^:\n]*\.log:\d+:|\d+:)?"   # no other colon: "Not run: x.log:3:" fails
SMOKE_LINE = re.compile(r"^[ \t]*" + SMOKE_GREP_PREFIX + r"(?:\[[^\]\n]*\])*[ \t]*(?:Log\w+:[ \t]*(?:\w+:[ \t]*)?)?SMOKE_OK[ \t]+map=(?P<map>[\w/.-]+)(?P<rest>[^\n]*)", re.M)
SMOKE_ANY = re.compile(r"^.*\bSMOKE_OK\b[ \t]+map=.*$", re.M)
# Final-9 B C1: the game's own SMOKE_EFFECTIVE line (live tuning values and flags, compiled-in commit and workbench)
EFFECTIVE = re.compile(r"^[ \t]*" + SMOKE_GREP_PREFIX + r"(?:\[[^\]\n]*\])*[ \t]*(?:Log\w+:[ \t]*(?:\w+:[ \t]*)?)?"
                       r"SMOKE_EFFECTIVE\b(?P<rest>[^\n]*)", re.M)
# Final-9 A H5: a card whose Done-when names a Windows script needs Windows output; "Not run" fails, and so does
# leaving the Windows run out (Mac-only evidence). Both forms fail until a Mac fallback rule exists (pending, Josh).
WINDOWS_DONE = re.compile(r"\b(?:package|smoke|daily)\.ps1\b", re.I)
PACKAGE_WIN = re.compile(r"^[ \t>$-]*package exit: 0\s+commit=[0-9a-f]{7,40}\s+dirty=no\b.*\bplatform=Win64\b", re.M)
SMOKE_FAIL = re.compile(r"^.*\bSMOKE_FAIL\b.*$", re.M)
SMOKE_FIELDS = re.compile(r"\b(\w+)=(\S+)")
PROOF = re.compile(r"`[^`]+`|\btools/|\.(?:py|sh|ps1|png|mp4|log|json)\b|\b(?:PASS|FAIL|OK)\b|(?i:\bexit(?:\s+code)?\s*[:=]?\s*-?\d)"
                   r"|\w=\S|problem\(s\)|\bRan \d+ tests?\b|\bSMOKE_OK\b|^\W*(?i:not run)\b\W+\S.{5,}", re.M)
# tools/check_automation_report.py's result line, exactly; the bootstrap label is card 0.3's only (dry run A H4)
TESTS_RESULT = re.compile(r"^[ \t>$-]*PASS  tests=[1-9]\d* failed=0  commit=(?P<commit>[0-9a-f]{7,40})[ \t]*$", re.M)
TESTS_BOOTSTRAP = re.compile(r"^[ \t>$-]*PASS  tests=[1-9]\d* failed=0  commit=(?P<commit>[0-9a-f]{7,40}) "
                             r"\(bootstrap: placeholder tests only, card 0\.3\)[ \t]*$", re.M)
TESTS_FAIL = re.compile(r"^[ \t>$-]*FAIL  tests=\d+ failed=\d+.*$", re.M)
BOOTSTRAP_CARD = "0.3"
# Final-8 A H1: the smoke run's verdict lines (tools/ue_run.py smoke-log and crash-check, printed by smoke.sh/.ps1)
SMOKE_SUMMARY = re.compile(r"^[ \t>$-]*smoke: exit=(?P<rc>-?\d+) SMOKE_OK=(?P<ok>\w+)(?P<rest>[^\n]*)$", re.M)
CRASH_SUMMARY = re.compile(r"^[ \t>$-]*crash folders: (?P<n>\d+) new\b", re.M)
FAIL_VERDICT = re.compile(r"^[ \t>$-]*FAIL(?::|\s{2}|\s*$)[^\n]*$", re.M)
# Final-8 A H3: a failure the card asks for on purpose, pasted under `PLANTED FAIL: <what>` up to the next blank line
PLANTED = re.compile(r"^[ \t>-]*PLANTED FAIL:[^\n]*\n(?:[ \t]*\S[^\n]*(?:\n|$))*", re.M)
CARD_ASKS_FAIL = re.compile(r"\bFAIL(?:S|ED)?\b")
try:
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
    import ue_run  # noqa: E402  the smoke contract lives there
    MIN_FPS, MAX_FRAME_MS, MAX_LOAD_MS = ue_run.MIN_FPS, ue_run.MAX_FRAME_MS, ue_run.MAX_LOAD_MS
except Exception:  # pragma: no cover
    MIN_FPS, MAX_FRAME_MS, MAX_LOAD_MS = 55, 33, 10000


def smoke_hook_exists(root, changed):
    """Card 0.6's smoke hook is in the tree at the PR head (or this PR adds it); one rule with the daily bootstrap
    (tools/ue_run.py smoke_hook_exists)."""
    return ue_run.smoke_hook_exists(root, changed)


def gamepad_merged(root):
    """The QA-GP test-map row (card 0.6e, the gamepad smoke) says merged. Unreadable counts as merged (no waiver)."""
    try:
        with open(os.path.join(root, TEST_MAP), encoding="utf-8") as fh:
            text = fh.read()
    except OSError:
        return True
    for ln in text.splitlines():
        cells = [c.strip() for c in ln.strip().strip("|").split("|")]
        if cells and cells[0] == "QA-GP":
            return cells[-1] != "planned"
    return True


def mvp2_merged(root):
    """The QA-01 test-map row (MVP 2 lift) says merged. An unreadable map counts as merged (no waiver)."""
    try:
        with open(os.path.join(root, TEST_MAP), encoding="utf-8") as fh:
            text = fh.read()
    except OSError:
        return True
    for ln in text.splitlines():
        cells = [c.strip() for c in ln.strip().strip("|").split("|")]
        if cells and cells[0] == "QA-01":
            return cells[-1] != "planned"   # exactly `planned` keeps the waiver; any other word ends it (B M7)
    return True


def ue_run_no_player(root=ROOT):
    """Maps with no player (pipeline/qa/no-player-maps.txt, which map cards extend; final-9 A H2), never the
    GameDefaultMap the game boots."""
    try:
        got = {ue_run.short_map(x.strip()) for x in ue_run.no_player_maps(root).split(",") if x.strip()}
        dm = ue_run.maps(root)[0]
        return got - ({ue_run.short_map(dm)} if dm else set())
    except Exception:  # pragma: no cover
        return {"L_Title"}


def planted_blocks(ev):
    return [m.group(0) for m in PLANTED.finditer(ev)]


def without_planted(ev):
    return PLANTED.sub("", ev)


def run_verdict_problems(ev, has_smoke):
    """Failure verdict lines anywhere (outside PLANTED FAIL blocks), and the smoke run's own verdict when a SMOKE_OK
    line is pasted (final-8 A H1)."""
    out = []
    for m in FAIL_VERDICT.finditer(ev):
        if not TESTS_FAIL.match(m.group(0)):   # FAIL  tests= has its own message
            out.append(f"Evidence has a failing line '{m.group(0).strip()[:70]}'")
    for m in CRASH_SUMMARY.finditer(ev):
        if m.group("n") != "0":
            out.append(f"Evidence has '{m.group(0).strip()}': the smoke run left a crash folder")
    sums = list(SMOKE_SUMMARY.finditer(ev))
    for m in sums:
        counts = re.findall(r"'[^']+'=(\d+)", m.group("rest"))
        if m.group("rc") != "0" or m.group("ok") != "yes" or any(c != "0" for c in counts):
            out.append(f"the smoke summary '{m.group(0).strip()[:70]}' is a failed run (exit, SMOKE_OK or a log count)")
    if has_smoke:
        if not sums:
            out.append("Evidence has a SMOKE_OK line but not the smoke script's `smoke: exit=0 SMOKE_OK=yes ...` "
                       "summary: paste the whole smoke.sh / smoke.ps1 output (final-8 A H1)")
        if not list(CRASH_SUMMARY.finditer(ev)):
            out.append("Evidence has a SMOKE_OK line but not crash-check's `crash folders: 0 new` line: paste the whole "
                       "smoke.sh / smoke.ps1 output (final-8 A H1)")
    return out


def smoke_contract_problems(smoke, changed, input_waived=False, tester_ok=False, root=ROOT, gamepad_waived=False):
    """The pasted SMOKE_OK line against the contract; map= must name a changed .umap when one changed."""
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
    import ue_run   # the smoke contract: gamepad and aspect checks
    f = dict(SMOKE_FIELDS.findall("map=" + smoke.group("map") + smoke.group("rest")))
    out = []

    def num(k):
        try:
            return float(f.get(k, ""))
        except ValueError:
            return None
    fps, worst, load = num("fps"), num("worst_ms"), num("load_ms")
    if fps is None or fps < MIN_FPS:
        out.append(f"SMOKE_OK fps={f.get('fps', '<none>')} is under the smoke minimum {MIN_FPS}")
    if worst is None or worst > MAX_FRAME_MS:
        out.append(f"SMOKE_OK worst_ms={f.get('worst_ms', '<none>')} is over {MAX_FRAME_MS} ms")
    if input_waived and f.get("input", "").lower() == "none":
        pass  # bootstrap: MVP 2 not merged and the run used SMOKE_REQUIRE_INPUT=0 (see docstring)
    elif f.get("input", "").lower() == "none" and \
            f.get("map", "").rsplit("/", 1)[-1].split(".")[0] in ue_run_no_player(root):
        pass  # a map with no player (pipeline/qa/no-player-maps.txt): nothing to hold input on (final-9 A H2)
    elif f.get("input", "").lower() != "ok":
        out.append(f"SMOKE_OK input={f.get('input', '<none>')}; the smoke must inject input and log input=ok")
    elif (num("input_vz") is None or num("input_vz") >= 0) and \
            f.get("map", "").rsplit("/", 1)[-1].split(".")[0] not in ue_run_no_player(root):
        # Final-8 A H2: under GDD 1.3 the no-input state UP_OPEN rises, so a rise proves nothing; the hook holds
        # IA_Attack and logs the Z velocity it measured, which only a working binding makes negative
        out.append(f"SMOKE_OK input_vz={f.get('input_vz', '<none>')}: input=ok needs the Z velocity measured while the "
                   "hook held ATTACK, below 0 (GDD 1.3: with no input the umbrella rises, so only descent proves input)")
    elif not gamepad_waived and f.get("map", "").rsplit("/", 1)[-1].split(".")[0] not in ue_run_no_player(root):
        out += ue_run.gamepad_problems(f, ue_run.shield_merged(root))   # card 0.6e: a controller reaches move, attack, shield
    if load is None or load > MAX_LOAD_MS:
        out.append(f"SMOKE_OK load_ms={f.get('load_ms', '<none>')} is over {MAX_LOAD_MS} ms")
    out += ue_run.aspect_problems(f)
    if f.get("debugdraw") != "0":
        out.append(f"SMOKE_OK debugdraw={f.get('debugdraw', '<none>')}: a default launch has every debug draw off "
                   "(hitbox and collision draws, debug text; ue.Debug 0): the line needs debugdraw=0")
    if tester_ok and f.get("workbench") == "1":
        pass   # final-7 A M6: the card asks for -Workbench tester package proof too; a workbench=0 line is still required
    elif f.get("workbench") != "0":
        out.append(f"SMOKE_OK workbench={f.get('workbench', '<none>')}: the line needs workbench=0, the submission "
                   "package (package script without -Workbench), not the tester package (D-new-workbench-debug)")
    if not re.fullmatch(r"[0-9a-f]{7,40}", f.get("commit", "")):
        out.append(f"SMOKE_OK commit={f.get('commit', '<none>')}: the line needs the package's commit=<sha> "
                   "(a smoke with no commit could be from a stale package)")
    maps = {os.path.splitext(os.path.basename(p.strip()))[0] for p in (changed or []) if p.strip().endswith(".umap")}
    got = f.get("map", "").rsplit("/", 1)[-1].split(".")[0]
    if maps and got not in maps:
        out.append(f"SMOKE_OK map={got}, but the PR changes {', '.join(sorted(maps))}: smoke a changed map")
    return out
NOT_RUN = re.compile(r"^(?=.*\b(?:package|smoke|SMOKE_OK)\b)(?=.*\bnot[ _-]?run\b).*$", re.I | re.M)
LINK = re.compile(r"#\d+|https?://\S+|\bD(?:EC-\d{2}|-new-[\w-]+|\d+)\b")

REQUIRED = ["Task", "What changed", "Done-when checks", "Evidence", "Not done / risks", "Binary assets touched", "Journal"]
JOURNAL_MARK = re.compile(r"journal\.py export card=([^\s`]+)")
CARD_ID_LINE = re.compile(r"Card ID:\s*(UE-[\w.]+)", re.I)


def sections(body):
    out = {}
    cur = None
    for line in body.splitlines():
        m = re.match(r"^##\s+(.*?)\s*$", line)
        if m:
            cur = m.group(1)
            out[cur] = []
        elif cur is not None:
            out[cur].append(line)
    return {k: "\n".join(v) for k, v in out.items()}


def meaningful(text):
    text = re.sub(r"<!--.*?-->", "", text, flags=re.S)
    text = re.sub(r"<[^>]*>", "", text)  # template placeholders like <issue>
    text = re.sub(r"^\s*-\s*\[[ xX]\]\s*$", "", text, flags=re.M)  # empty checkbox
    text = text.replace("Closes #", "").replace("Part of #", "").replace("Card ID: UE-___", "")
    text = re.sub(r"^\s*commit=\s*engine=5\.8\.4\s*config=\s*host=\s*run=\s*$", "", text, flags=re.M)  # header template
    text = re.sub(r"^\s*Next:\s*$", "", text, flags=re.M)
    text = re.sub(r"(Owner role|Reviewer role):\s*___", "", text)
    return bool(re.search(r"\w", text))


def needs_package(s, changed, card_done=""):
    paths = list(changed or [])
    paths += re.findall(r"[\w./{}*-]+", s.get("What changed", ""))
    for p in paths:
        p = p.strip("`'\",.;:()").lstrip("./")
        if any(fnmatch.fnmatch(p, g) for g in PACKAGE_GLOBS):
            return f"it changes {p}"
        if any(fnmatch.fnmatch(p, g) for g in VISUAL_GLOBS):
            return f"it changes {p} (a visual path: the smoke's art and screen checks run on it)"
    for done, whose in ((card_done, "the linked card's"), (s.get("Done-when checks", ""), "its")):
        if re.search(r"\bpackage\b", done, re.I) and "SMOKE_OK" in done:
            return f"{whose} Done-when asks for package + SMOKE_OK"
    return None


def touches_source(s, changed):
    """Source/ or a plugin's C++ (Plugins/<X>/Source/): both compile into the game (final-7 dry run B M4)."""
    paths = list(changed or []) + re.findall(r"[\w./{}*-]+", s.get("What changed", ""))
    return any(re.match(r"(?:Source/|Plugins/[^/]+/Source/)", p.strip("`'\",.;:()").lstrip("./")) for p in paths)


BAKE_STAMP = "pipeline/qa/baked.json"
BAKE_PASS = re.compile(r"\bbake_preset check: PASS preset=T-\d{2}\b")


def bake_problems(s, changed):
    paths = list(changed or []) + re.findall(r"[\w./{}*-]+", s.get("What changed", ""))
    if not any(p.strip("`'\",.;:()").lstrip("./") == BAKE_STAMP for p in paths):
        return []
    if BAKE_PASS.search(re.sub(r"<!--.*?-->", "", s.get("Evidence", ""), flags=re.S)):
        return []
    return [f"PR changes {BAKE_STAMP}: paste the `python3 tools/bake_preset.py check` line "
            "(`bake_preset check: PASS preset=T-nn ...`) under Evidence (D-new-workbench-debug)"]


AUDIO_PATH = re.compile(r"^(?:Audio/Source|Content/UmbrellaElla/Audio)/([A-Z][A-Za-z0-9]*)/")
AUDIO_LOOP_PASS = re.compile(r"^[ \t>$-]*AUDIO LOOP: PASS piece=(?P<id>\w+) rounds=\d+ critic=(?P<critic>\S+) "
                             r"builder=(?P<builder>\S+) files=[0-9a-f]{12} commit=(?P<commit>[0-9a-f]{7,40})", re.M)
AUDIO_CLOSE_PASS = re.compile(r"^[ \t>$-]*audio_loop close: PASS card=(?P<card>\S+) pieces=\d+ "
                              r"commit=(?P<commit>[0-9a-f]{7,40})", re.M)
AUDIO_STYLE_PASS = re.compile(r"^[ \t>$-]*audio_style check: PASS files=[1-9]\d* commit=(?P<commit>[0-9a-f]{7,40}) "
                              r"dirty=no\b", re.M)
AUDIO_PLACEHOLDER = re.compile(r"^[ \t>$-]*AUDIO PLACEHOLDER: piece=(?P<id>\w+) takes=\d+ "
                               r"commit=(?P<commit>[0-9a-f]{7,40})", re.M)   # audio_loop.py close, a tracked placeholder
AUDIO_FAIL = re.compile(r"^[ \t>$-]*(?:audio_loop close: FAIL|audio_style check: FAIL|AUDIO LOOP: FAIL)[^\n]*", re.M)


def audio_ids(s, changed):
    paths = {p.strip("`'\",.;:()").lstrip("./") for p in
             list(changed or []) + re.findall(r"[\w./{}*-]+", s.get("What changed", ""))}
    return sorted({m.group(1) for m in map(AUDIO_PATH.match, paths) if m and m.group(1) != "Core"})


def placeholder_ids(ev, hc, root):
    """Sound ids with an `AUDIO PLACEHOLDER:` line for the header commit whose every take under Audio/Source/<Id>/ is
    a tracked placeholder in this tree's provenance (tools/audio_check.py placeholder_takes): the line alone never
    exempts a sound."""
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
    import audio_check
    ph = audio_check.placeholder_takes(root=root)
    out = set()
    for m in AUDIO_PLACEHOLDER.finditer(ev):
        sid = m.group("id")
        d = os.path.join(root, "Audio", "Source", sid)
        takes = sorted(f"Audio/Source/{sid}/{f}" for f in (os.listdir(d) if os.path.isdir(d) else ())
                       if f.lower().endswith(".wav"))
        if same_commit(m.group("commit"), hc) and takes and all(t in ph for t in takes):
            out.add(sid)
    return out


def audio_problems(s, changed, root=ROOT):
    """An audio PR closes its builder-critic loop on the PR head: the critic passed every changed sound and the
    measured style check passed on the same commit (pipeline/audio/style-target.md section 5). A sound whose every
    take is a tracked placeholder (the audio API could not make it) shows its `AUDIO PLACEHOLDER:` line instead."""
    ids = audio_ids(s, changed)
    if not ids:
        return []
    ev = without_planted(re.sub(r"<!--.*?-->", "", s.get("Evidence", ""), flags=re.S))
    out = [f"Evidence has `{m.group(0).strip()[:80]}`: the audio loop is not closed" for m in AUDIO_FAIL.finditer(ev)]
    h = HEADER.search(ev)
    hc = h.group("commit") if h else None
    how = (f"paste the output of `python3 tools/audio_loop.py close --card <id>` run on the PR head "
           f"(sounds changed: {', '.join(ids)})")
    card = card_id(s)
    held = placeholder_ids(ev, hc, root)
    ids = [i for i in ids if i not in held]
    closes = [m for m in AUDIO_CLOSE_PASS.finditer(ev) if same_commit(m.group("commit"), hc)]
    if not closes:
        out.append(f"audio PR without an `audio_loop close: PASS ... commit=<header commit>` line: {how}")
    elif card and not any(card_key(m.group("card")) == card for m in closes):
        out.append(f"the audio_loop close line is for card {closes[0].group('card')}, not this PR's Card ID")
    if ids and not any(same_commit(m.group("commit"), hc) for m in AUDIO_STYLE_PASS.finditer(ev)):
        out.append(f"audio PR without an `audio_style check: PASS files=<n> commit=<header commit> dirty=no` line: {how}")
    passes = {}
    for m in AUDIO_LOOP_PASS.finditer(ev):
        if same_commit(m.group("commit"), hc):
            passes.setdefault(m.group("id"), []).append(m)
    for sid in ids:
        got = passes.get(sid, [])
        if not got:
            out.append(f"{sid}: no `AUDIO LOOP: PASS piece={sid} ... commit=<header commit>` line (a critic verdict and "
                       "the measured check for this commit)")
        elif all(m.group("critic") == m.group("builder") for m in got):
            out.append(f"{sid}: the critic session is the builder's; a separate critic with fresh context judges it")
    return out


ENCOUNTER_DATA = "pipeline/level/encounter.json"
ENCOUNTER_OK = re.compile(r"^[ \t>$-]*encounter_check: 0 problem\(s\)", re.M)


def encounter_problems(s, changed, body, card=None, root=ROOT):
    """Rule encounter: data changes carry the check line; listed fight phases carry the critic loop's lines."""
    sys.path.insert(0, os.path.join(ROOT, "tools"))
    import encounter_spec
    paths = {p.strip("`'\",.;:()").lstrip("./") for p in
             list(changed or []) + re.findall(r"[\w./{}*-]+", s.get("What changed", ""))}
    text = re.sub(r"<!--.*?-->", "", body or "", flags=re.S) + "\n" + ((card or {}).get("body") or "")
    listed = encounter_spec.card_phases(text)
    touches = ENCOUNTER_DATA in paths
    if not touches and not listed:
        return []
    out = []
    ev = re.sub(r"<!--.*?-->", "", s.get("Evidence", ""), flags=re.S)
    if touches and not ENCOUNTER_OK.search(ev):
        out.append(f"PR changes {ENCOUNTER_DATA}: paste `python3 tools/encounter_check.py` ending "
                   "`encounter_check: 0 problem(s)` under Evidence")
    if touches and listed is None:
        out.append(f"PR changes {ENCOUNTER_DATA}: add `Encounter phases: <preset>/<phase>, ...` for the fight phases it "
                   "builds or tunes, or `Encounter phases: none (<why>)` (pipeline/roles/encounter-designer.md)")
    if listed:
        try:
            with open(os.path.join(root, ENCOUNTER_DATA), encoding="utf-8") as fh:
                data = json.load(fh)
        except (OSError, ValueError):
            data = {}
        out += [f"encounter {rule}: {msg}" for rule, _, msg in encounter_spec.card_problems(text, data, root)]
    return out


HITBOX_DATA = "pipeline/feel/hitboxes.json"
HITBOX_ALIGN = "pipeline/art/visual-align.json"
HITBOX_PASS = re.compile(r"^[ \t>$-]*hitbox_check: PASS entities=\d+", re.M)
HITBOX_FAIL = re.compile(r"^[ \t>$-]*hitbox_check: FAIL\b", re.M)


def hitbox_sprites(root):
    try:
        with open(os.path.join(root, HITBOX_DATA), encoding="utf-8") as fh:
            return {e.get("sprite") for e in json.load(fh).get("entities") or [] if e.get("sprite")}
    except (OSError, ValueError, AttributeError):
        return set()


def hitbox_problems(s, changed, root=ROOT):
    paths = {p.strip("`'\",.;:()").lstrip("./") for p in
             list(changed or []) + re.findall(r"[\w./{}*-]+", s.get("What changed", ""))}
    hit = sorted(paths & ({HITBOX_DATA, HITBOX_ALIGN} | hitbox_sprites(root)))
    if not hit:
        return []
    ev = re.sub(r"<!--.*?-->", "", s.get("Evidence", ""), flags=re.S)
    if HITBOX_FAIL.search(without_planted(ev)):
        return ["Evidence has a `hitbox_check: FAIL` line: the art does not align with its collider yet; the art "
                "swap waits for a PASS (`hitbox_check.py fit <id>` moves the art, never the collider)"]
    if HITBOX_PASS.search(ev):
        return []
    return [f"PR changes {', '.join(hit[:3])}: paste the `python3 tools/hitbox_check.py check` line "
            "(`hitbox_check: PASS entities=<n> ...`) under Evidence. Collider data or art changed, so the alignment "
            "check re-runs before the art is used"]


STORY_DIR = "pipeline/story/"
STORY_BIBLE = "pipeline/story/story-bible.md"
STORY_TEXT_FILES = ("Content/UmbrellaElla/UI/ST_UI.csv", "pipeline/submission/itch-page.md")
STORY_CONFIRM = re.compile(r"^[ \t>*-]*STORY CONFIRM: by=(?P<by>[^\s=]+)\s+(?P<ids>.+?)\s*$", re.M)


def design_owner(root):
    """First name in the docs/jam-brief.md People row 'Game design owner' (Richard per GDD 1.3 section 14)."""
    try:
        with open(os.path.join(root, "docs", "jam-brief.md"), encoding="utf-8") as fh:
            for ln in fh:
                if ln.startswith("| Game design owner"):
                    m = re.match(r"\s*([A-Za-z][\w.-]*)", ln.strip().strip("|").split("|")[1])
                    if m and m.group(1) != "TBD":
                        return m.group(1)
    except (OSError, IndexError):
        pass
    return "Richard"


def confirmed_keys(text):
    import story_check
    b = story_check.parse_bible(text or "")
    keys = {n["name"] for n in b["names"] if story_check.CONFIRMED.match(n["status"])}
    return keys | {fid for fid, f in b["facts"].items() if story_check.CONFIRMED.match(f["status"])}


def git_show(root, rev, path):
    import subprocess
    r = subprocess.run(["git", "show", f"{rev}:{path}"], cwd=root, capture_output=True, text=True)
    return r.stdout if r.returncode == 0 else ""


def story_problems(s, changed, root=ROOT, base=None):
    sys.path.insert(0, os.path.join(ROOT, "tools"))
    import story_check
    paths = {p.strip("`'\",.;:()").lstrip("./") for p in
             list(changed or []) + re.findall(r"[\w./{}*-]+", s.get("What changed", ""))}
    story = sorted(p for p in paths if p.startswith(STORY_DIR))
    text = sorted(p for p in paths if p in STORY_TEXT_FILES)
    if not story and not text:
        return []
    ev = re.sub(r"<!--.*?-->", "", s.get("Evidence", ""), flags=re.S)
    live = without_planted(ev)
    if story_check.FAIL_LINE.search(live):
        return ["Evidence has a `story_check: FAIL` line: the text is fixed and re-checked first; the critic cannot "
                "override the machine check"]
    out = []
    if story:
        passes = list(story_check.PASS_LINE.finditer(live))
        crit = list(story_check.CRITIC.finditer(live))
        if not passes:
            out.append(f"PR changes {', '.join(story[:3])}: paste the `python3 tools/story_check.py` line "
                       "(`story_check: PASS bible=<h> sheet=<h> lines=<n> ...`) under Evidence")
        if not crit:
            out.append(f"PR changes {', '.join(story[:3])}: paste the final `STORY_CRITIC: PASS ...` line of a separate "
                       "critic session under Evidence (pipeline/roles/story.md, quality loop)")
        if passes and crit:
            p, c = passes[-1], crit[-1]
            try:
                rules = story_check.load_rules(os.path.join(root, story_check.RULES))
                cur = (story_check.sha8(story_check.read_text(os.path.join(root, story_check.BIBLE))),
                       story_check.sha8(story_check.read_text(os.path.join(root, story_check.LINES))))
            except (OSError, ValueError):
                rules, cur = {}, None
            if c.group("verdict") != "PASS":
                out.append("the last STORY_CRITIC line is FAIL: fix the quoted words and run a new critic session")
            if c.group("builder") == c.group("critic"):
                out.append("STORY_CRITIC: builder and critic are the same session; the critic is a separate session")
            if int(c.group("cycle")) < 1:   # no cycle cap (D-new-no-round-cap)
                out.append(f"STORY_CRITIC cycle {c.group('cycle')}: cycles count from 1")
            if rules and c.group("rubric") != rules.get("rubric_version"):
                out.append(f"STORY_CRITIC rubric {c.group('rubric')} is not {rules.get('rubric_version')}")
            if (c.group("bible"), c.group("sheet")) != (p.group("bible"), p.group("sheet")):
                out.append("STORY_CRITIC and story_check name different bible/sheet hashes: the critic judged "
                           "another version")
            if cur and (p.group("bible"), p.group("sheet")) != cur:
                out.append(f"story_check ran on bible={p.group('bible')} sheet={p.group('sheet')}, but this PR has "
                           f"bible={cur[0]} sheet={cur[1]}: re-run the check and the critic (stale evidence)")
    if text and not story_check.SCAN_PASS.search(live):
        out.append(f"PR changes {', '.join(text)}: paste `python3 tools/story_check.py --scan <file>` "
                   "(`story_check: PASS scan files=<n> ...`) under Evidence")
    if base and STORY_BIBLE in paths:
        new = confirmed_keys(story_check.read_text(os.path.join(root, STORY_BIBLE))
                             if os.path.isfile(os.path.join(root, STORY_BIBLE)) else "") \
            - confirmed_keys(git_show(root, base, STORY_BIBLE))
        owner = design_owner(root)
        given = set()
        for m in STORY_CONFIRM.finditer(live):
            if m.group("by").lower() == owner.lower():
                given |= {t.strip() for t in m.group("ids").split(",") if t.strip()}
        if new - given:
            out.append(f"bible rows newly CONFIRMED ({', '.join(sorted(new - given))}) need "
                       f"`STORY CONFIRM: by={owner} <row ids, comma-separated>` under Evidence: only the game design "
                       "owner confirms story canon")
    return out


EDITOR_CHECK = re.compile(r"^[ \t>*-]*EDITOR CHECK: by=(?P<by>[^\s=]+)\s+opened=(?P<paths>\S+)\s+ok\b", re.M)
ASSET_EXT = (".uasset", ".umap")


def editor_problems(s, changed):
    """A changed .uasset/.umap needs the card's human to open and check it (editor MCP guardrail; binary assets have
    no reviewable diff). Every changed asset is named in an `EDITOR CHECK: by=<name> opened=<paths> ok` line."""
    paths = list(changed or []) + re.findall(r"[\w./{}*-]+", s.get("What changed", ""))
    assets = sorted({p.strip("`'\",.;:()").lstrip("./") for p in paths
                     if p.strip("`'\",.;:()").lower().endswith(ASSET_EXT)})
    if not assets:
        return []
    ev = re.sub(r"<!--.*?-->", "", s.get("Evidence", ""), flags=re.S)
    checked = set()
    for m in EDITOR_CHECK.finditer(ev):
        if m.group("by").strip("<>").lower() not in ("name", "tbd", "agent", "claude"):
            checked.update(x.strip() for x in m.group("paths").split(","))
    missing = [a for a in assets if a not in checked]
    if not missing:
        return []
    return [f"PR changes {len(missing)} editor asset(s) no human opened ({', '.join(missing[:5])}): the card's human "
            "opens each in the editor and pastes `EDITOR CHECK: by=<name> opened=<path>[,<path>] ok` under Evidence "
            "(pipeline/agent-ops/editor-mcp.md)"]


GATE_EDIT = re.compile(r"^[ \t>*-]*GATE EDIT: by=(?P<by>[^\s=]+)\s+(?:paths=)?(?P<paths>\S+)", re.M)
NOT_A_HUMAN = ("name", "tbd", "agent", "claude", "codex", "ai", "bot")


def gate_globs(root):
    try:
        with open(os.path.join(root, "pipeline", "agent-ops", "gates.json"), encoding="utf-8") as fh:
            return json.load(fh).get("gate_paths") or []
    except (OSError, ValueError):
        return []


def norm_path(p):
    """A path as written in a PR: quotes and trailing punctuation off, a leading ./ off; a leading dot stays
    (.github/, .claude/, .gitignore are gate paths)."""
    p = p.strip("`'\",;:()").rstrip(".")
    while p.startswith("./"):
        p = p[2:]
    return p.lstrip("/")


def card_lanes(card):
    if not card:
        return []
    try:
        import check_card
        got = check_card.parse(card.get("body") or "", check_card.template_fields(ROOT))
        lane = (got[0] if isinstance(got, tuple) else got).get("File lane") or ""
        return [g for g in check_card.lane_globs(lane) if g not in check_card.ROW_SCOPED]
    except Exception:  # pragma: no cover
        return []


def file_reader(root, sha):
    """path -> text at sha (None = absent); sha None: the working tree under root."""
    def read_at(path):
        if sha:
            r = subprocess.run(["git", "show", f"{sha}:{path}"], cwd=root, capture_output=True, text=True)
            return r.stdout if r.returncode == 0 else None
        try:
            with open(os.path.join(root, path), encoding="utf-8") as fh:
                return fh.read()
        except OSError:
            return None
    return read_at


def gate_commits(root, base, head):
    """[(sha, message, [paths])] for each non-merge commit in base..head, or None when git cannot read the range."""
    r = subprocess.run(["git", "log", "--no-merges", "--no-renames", "--name-only", "--format=%x00%H%x01%B%x02",
                        f"{base}..{head}"], cwd=root, capture_output=True, text=True)
    if r.returncode != 0:
        return None
    out = []
    for rec in r.stdout.split("\x00")[1:]:
        sha, _, rest = rec.partition("\x01")
        msg, _, names = rest.partition("\x02")
        out.append((sha.strip(), msg, [n.strip() for n in names.splitlines() if n.strip()]))
    return out


def trailer_paths(msg, by):
    """The paths a commit message's `GATE EDIT: by=<by> <paths>` trailer lists (empty set = no such trailer)."""
    got = set()
    for m in GATE_EDIT.finditer(msg or ""):
        if m.group("by").strip("<>").lower() == by:
            got.update(norm_path(x) for x in m.group("paths").split(","))
    return got


def is_card_pr(s, card):
    return bool(card) or bool(card_id(s)) or bool(TASK_LINK.search(s.get("Task", "")))


def gate_problems(s, changed, root=ROOT, card=None, head=None, base=None):
    """Rule gate: a changed gate path (gates.json gate_paths) is never an agent session's own commit.
    On a card PR the only route is kickoff's tool route (tools/git_gate.py apply --auto), read from the git history
    of the PR head, never from the PR body (the agent writes the body): every non-merge commit in base..head that
    changes a gate path carries the trailer `GATE EDIT: by=kickoff <path>[,<path>...]` naming each gate path it
    changes, and the rule re-runs git_gate.auto_problems on the result (every path in the linked card's File lane, no
    guardrail enforcer changed, no guardrail file loosened against --base). A trailer is commit text an agent could
    also type; that buys it nothing, because the re-check is the same policy kickoff applies. A person's
    `GATE EDIT: by=<name>` line does not pass on a card PR: no record of a human commit exists that an agent cannot
    forge (JAM_HUMAN is an env var, the journal is a local file agents write), so the rule fails closed.
    A PR with no card (a person's pipeline PR): a `GATE EDIT: by=<name> <path>[,<path>...]` line under Evidence names
    each gate path. No local git hook checks gate paths (Josh, 12 Nov): this rule, and kickoff's merge gate running
    it from the base checkout, catch an agent's gate-path change."""
    sys.path.insert(0, os.path.join(root, "tools"))
    import git_gate
    paths = {norm_path(p) for p in list(changed or []) + re.findall(r"[\w./{}*-]+", s.get("What changed", ""))}
    globs = gate_globs(root)
    hits = git_gate.gate_hits(sorted(p for p in paths if p and "*" not in p), globs)
    if not hits:
        return []
    ev = re.sub(r"<!--.*?-->", "", s.get("Evidence", ""), flags=re.S)
    how = ("kickoff applies a session's gate.patch (tools/git_gate.py apply --auto), which commits it with the "
           "trailer `GATE EDIT: by=kickoff <path>[,<path>]`")
    if is_card_pr(s, card):
        if not (card and base and head):
            return [f"PR changes {len(hits)} gate path(s) ({', '.join(hits[:5])}): the rule gate needs the linked "
                    "card, --base and --head to read kickoff's gate commits from git (AGENTS.md section 7)"]
        commits = gate_commits(root, base, head)
        if commits is None:
            return [f"gate: git cannot read {base[:12]}..{head[:12]} to find kickoff's gate commits (the checkout "
                    "needs the PR history: fetch-depth 0)"]
        out, done = [], set()
        for sha, msg, names in commits:
            touched = git_gate.gate_hits(sorted(norm_path(n) for n in names), globs)
            if not touched:
                continue
            listed = trailer_paths(msg, git_gate.AUTO_BY)
            bad = [t for t in touched if t not in listed]
            if bad:
                out.append(f"gate: commit {sha[:12]} changes gate path(s) {', '.join(bad[:5])} and is not kickoff's "
                           "gate commit (no `GATE EDIT: by=kickoff` trailer naming them): agent sessions never commit "
                           f"gates (AGENTS.md section 7); {how}")
            done.update(t for t in touched if t in listed)
        missing = [h for h in hits if h not in done]
        if missing and not out:
            out.append(f"gate: no kickoff gate commit in {base[:12]}..{head[:12]} changes {', '.join(missing[:5])}; "
                       + how)
        people = [m.group("by").strip("<>") for m in GATE_EDIT.finditer(ev)
                  if m.group("by").strip("<>").lower() != git_gate.AUTO_BY]
        if out and people:
            out.append(f"gate: a person's `GATE EDIT: by={people[0]}` line in the PR body does not pass on a card PR "
                       "(an agent can write it); only kickoff's tool route does")
        if out:
            return out
        why = git_gate.auto_problems(hits, card_lanes(card), file_reader(root, base), file_reader(root, head))
        return [f"gate: the tool route's gate commit fails its re-check: {w}" for w in why[:4]]
    named = set()
    for m in GATE_EDIT.finditer(ev):
        by = m.group("by").strip("<>")
        if by.lower() in NOT_A_HUMAN or by.lower() == git_gate.AUTO_BY:
            continue
        named.update(norm_path(x) for x in m.group("paths").split(","))
    missing = [h for h in hits if h not in named]
    if not missing:
        return []
    return [f"PR changes {len(missing)} gate path(s) nobody claimed ({', '.join(missing[:5])}): on a PR with no card, "
            "a person pastes `GATE EDIT: by=<name> <path>[,<path>]` under Evidence; on a card PR, " + how]


GDD_PATHS = ("docs/gdd/", "docs/feature-manifest.json")
GDD_IMPACT = re.compile(r"\bgdd_impact old=\S+ new=\S+ added=\d+ removed=\d+ changed=\d+ status=\d+ cited=\d+")


def touches_gdd(s, changed):
    paths = list(changed or []) + re.findall(r"[\w./{}*-]+", s.get("What changed", ""))
    for p in paths:
        p = p.strip("`'\",.;:()").lstrip("./")
        if p.startswith(GDD_PATHS):
            return p
    return None


def gdd_problems(s, changed):
    p = touches_gdd(s, changed)
    if not p:
        return []
    sec = re.sub(r"<!--.*?-->", "", s.get("GDD impact", ""), flags=re.S)
    if not GDD_IMPACT.search(sec) or "cited by:" not in sec:
        return [f"PR changes {p}: paste the full `python3 tools/gdd_impact.py <old> <new>` output (its gdd_impact line"
                " and 'cited by:' list) under '## GDD impact' (docs/gdd/README.md)"]
    return []


def card_done_when(card):
    """The linked card's Done-when text (gh issue view --json title,body), so the PR cannot drop a package line by
    editing its own copy (dry run A H4). '' when no card was given."""
    if not card:
        return ""
    try:
        import check_card
        got = check_card.parse(card.get("body") or "", check_card.template_fields(ROOT))
        got = got[0] if isinstance(got, tuple) else got   # parse returns (fields, order)
        return got.get("Done when", "") or ""
    except Exception:  # pragma: no cover - a card the parser cannot read gives the whole body
        return card.get("body") or ""


def card_id(s):
    c = CARD_ID_LINE.search(s.get("Task", ""))
    return card_key(c.group(1)) if c else None


def same_commit(a, b):
    a, b = (a or "").lower(), (b or "").lower()
    return bool(a and b) and (a.startswith(b) or b.startswith(a))


def evidence_problems(s, changed, head, root=ROOT, card=None):
    out = []
    ev = re.sub(r"<!--.*?-->", "", s.get("Evidence", ""), flags=re.S)
    ev = re.sub(r"<[^>\n]*>", "", ev)
    planted = planted_blocks(ev)
    if planted:
        done = card_done_when(card) or s.get("Done-when checks", "")
        if not CARD_ASKS_FAIL.search(done):
            out.append("Evidence has a `PLANTED FAIL:` block, but the card's Done-when asks for no failure on purpose: "
                       "a real failure is never pasted as planted")
        ev = without_planted(ev)
    m = HEADER.search(ev)
    if not m:
        out.append("Evidence needs the header line `commit=<sha> engine=5.8.4 config=<Development|Shipping|none> "
                   "host=<win|mac> run=<PIE|Standalone|packaged|none>` (AGENTS.md section 5)")
    elif head and not head.lower().startswith(m.group("commit").lower()):
        out.append(f"Evidence is for commit {m.group('commit')}, but the PR head is {head[:12]}: stale evidence counts as missing")
    # Any failing line fails, whatever else is pasted (dry run B H6).
    for b in BUILD_LINE.finditer(ev):
        if b.group("rc") != "0":
            out.append(f"Evidence has a failing build line '{b.group(0).strip()[:60]}'")
    for b in PACKAGE_LINE.finditer(ev):
        if b.group("rc") != "0":
            out.append(f"Evidence has a failing package line '{b.group(0).strip()[:60]}'")
    for b in TESTS_FAIL.finditer(ev):
        out.append(f"Evidence has a failing test report '{b.group(0).strip()[:60]}'")
    for b in SMOKE_FAIL.finditer(ev):
        out.append(f"Evidence has a failing smoke line '{b.group(0).strip()[:60]}'")
    out += run_verdict_problems(ev, bool(list(SMOKE_LINE.finditer(ev))))
    if touches_source(s, changed):
        hc = m.group("commit") if m else None
        nonunity = [b for b in BUILD_LINE.finditer(ev) if b.group("rc") == "0" and b.group("mode") == "nonunity"]
        if not nonunity:
            out.append("touches Source/ but has no `build exit: 0  mode=nonunity  commit=<sha>` line: run NONUNITY=1 "
                       "tools/ue/build.sh (or build.ps1 -NonUnity) and paste its last line as printed (D-new-nonunity-pr)")
        elif not any(same_commit(b.group("commit"), hc) for b in nonunity):
            got = ", ".join(b.group("commit") or "<none>" for b in nonunity)
            out.append(f"the nonunity build line is for commit={got}, not the evidence header commit {hc}: build the "
                       "PR head and paste the line build.sh / build.ps1 prints (final-7 B H7)")
        tests = list(TESTS_RESULT.finditer(ev))
        if card_id(s) == BOOTSTRAP_CARD:
            tests += list(TESTS_BOOTSTRAP.finditer(ev))
        if not tests:
            out.append("touches Source/ but has no `check_automation_report.py` result line (`PASS  tests=<n> failed=0  "
                       "commit=<sha>`); paste it (AGENTS.md section 5). The bootstrap line counts only on card 0.3. "
                       "With CAN RUN build=n, the human who runs the tests pastes it")
        elif not any(same_commit(t.group("commit"), hc) for t in tests):
            out.append(f"the test result line is for commit={tests[0].group('commit')}, not the evidence header commit "
                       f"{hc}: run the tests on the PR head (final-7 B H7)")
        if m and (m.group("engine").lower() == "none" or m.group("run").lower() == "none"):
            out.append("touches Source/ but the evidence header says engine=none or run=none: build and test it")
    why = needs_package(s, changed, card_done_when(card))
    if why:
        nr = NOT_RUN.search(ev)
        smokes = list(SMOKE_LINE.finditer(ev))
        if nr:
            out.append(f"PR needs package evidence because {why}, but Evidence says '{nr.group(0).strip()[:70]}': "
                       "'not run' is never a pass; run it on the packaging machine before merge")
        if m and m.group("run").lower() != "packaged":
            out.append(f"PR needs package evidence because {why}, but the evidence header says run={m.group('run')}: "
                       "the evidence is from the packaged build (run=packaged)")
        for x in SMOKE_ANY.finditer(ev):
            if not SMOKE_LINE.match(x.group(0)):
                out.append(f"'{x.group(0).strip()[:70]}' is not the game's SMOKE_OK log line as printed")
        boot = SMOKE_BOOTSTRAP.search(ev)
        hook = smoke_hook_exists(root, changed)
        if boot and hook:
            out.append("Evidence has SMOKE_BOOTSTRAP, but the smoke hook (card 0.6) exists: paste the SMOKE_OK line")
        pk = list(PACKAGE_OK.finditer(ev))
        if not pk:
            out.append(f"PR needs package evidence because {why}: paste the `package exit: 0  commit=<sha>  dirty=no` "
                       "line the package script prints and the game's `SMOKE_OK map=<map> fps=<n> commit=<sha>` line")
        for p in pk:
            if p.group("dirty") != "no":
                out.append(f"the package line says dirty={p.group('dirty')}: a package of an uncommitted tree "
                           "(--allow-dirty) is not evidence for this commit (final-7 B M8)")
            if m and not same_commit(p.group("commit"), m.group("commit")):
                out.append(f"the package line is for commit={p.group('commit')}, not the evidence header commit "
                           f"{m.group('commit')}: package the PR head")
        if not pk:
            pass
        elif not smokes:
            if not (boot and not hook):
                out.append(f"PR needs package evidence because {why}: paste the game's "
                           "`SMOKE_OK map=<map> fps=<n> commit=<sha>` line"
                           + ("" if hook else " (before card 0.6 merges: a `SMOKE_BOOTSTRAP: no smoke hook before "
                                              "card 0.6` line)"))
        else:
            waived = bool(INPUT_BOOTSTRAP.search(ev)) and not mvp2_merged(root)
            # A card whose Done-when asks for the -Workbench tester package (card 0.27) may paste that run's
            # workbench=1 line too; the submission package's workbench=0 line is still required (final-7 A M6).
            done = card_done_when(card) or s.get("Done-when checks", "")
            tester_ok = bool(re.search(r"-Workbench\b", done))
            if tester_ok and not any(re.search(r"\bworkbench=0\b", x.group("rest")) for x in smokes):
                out.append("the card asks for the -Workbench tester package, but no SMOKE_OK line has workbench=0: "
                           "paste the submission package's smoke too")
            for smoke in smokes:   # every SMOKE_OK line pasted must pass, not just the first
                out += smoke_contract_problems(smoke, changed, input_waived=waived, tester_ok=tester_ok, root=root,
                                               gamepad_waived=waived or (bool(GAMEPAD_BOOTSTRAP.search(ev))
                                                                         and not gamepad_merged(root)))
                c = re.search(r"\bcommit=([0-9a-f]{7,40})\b", smoke.group("rest"))
                if m and c and not (c.group(1).startswith(m.group("commit").lower())
                                    or m.group("commit").lower().startswith(c.group(1))):
                    out.append(f"SMOKE_OK is for commit {c.group(1)}, but the evidence header says {m.group('commit')}: "
                               "smoke the package built from this commit")
            if hook:
                out += effective_evidence_problems(ev, m, root, tester_ok)
        if WINDOWS_DONE.search(card_done_when(card) or s.get("Done-when checks", "")):
            out += windows_evidence_problems(ev, why)
    if smoke_hook_exists(root, changed) and list(SMOKE_LINE.finditer(ev)):
        out += art_evidence_problems(ev, root, changed)
    return out


def current_refs_hash(root=ROOT):
    sys.path.insert(0, os.path.join(ROOT, "tools"))
    import art_judge
    try:
        return art_judge.refs_hash(os.path.join(root, "pipeline", "art", "references.json"))
    except OSError:
        return None


def art_card(root, cid):
    """The card's pieces when references.json assigns it references (an art card), else []."""
    if not cid:
        return []
    sys.path.insert(0, os.path.join(ROOT, "tools"))
    import art_loop
    try:
        refs, _ = art_loop.refs_and_hash(root)
    except (OSError, ValueError):
        return []
    return art_loop.pieces(refs, cid)


def artref_problems(s, changed, root=ROOT):
    """Rules artref and artloop (Josh, 10 Nov: referencing the art is enforced in code)."""
    paths = [p.strip("`'\",.;:()").lstrip("./") for p in list(changed or [])]
    hit = sorted({p for p in paths if any(fnmatch.fnmatch(p, g) for g in ART_PATHS) and p not in ART_LEDGERS})
    cid = card_id(s)
    pieces = art_card(root, cid)
    if not hit and not pieces:
        return []
    ev = without_planted(re.sub(r"<!--.*?-->", "", s.get("Evidence", ""), flags=re.S))
    hm = HEADER.search(ev)
    hc = hm.group("commit") if hm else None
    rh = current_refs_hash(root)
    why = f"it changes {hit[0]}" if hit else f"card {cid} is an art card"
    out = []
    lines = list(ART_REF_LINE.finditer(ev))
    for m in lines:
        if m.group("v") == "FAIL":
            out.append(f"Evidence has `art_ref_check: FAIL card={m.group('card')}`: the art is below its references; "
                       "regenerate, rescale or reposition and run it again")
    good = [m for m in lines if m.group("v") == "PASS"]
    if not good:
        out.append(f"PR needs `art_ref_check: PASS` because {why}: run `python3 tools/art_ref_check.py --card <id> "
                   "--scene <capture> | --element <id> <files>` and paste its line (references.json, enforced in code)")
    for m in good:
        if rh and m.group("refs") != rh:
            out.append(f"art_ref_check line refs={m.group('refs')} is not the current references.json ({rh}): evidence "
                       "made against an older or smaller reference set; run it again")
        if hc and not same_commit(m.group("commit"), hc):
            out.append(f"art_ref_check line is for commit={m.group('commit')}, not the evidence header commit {hc}")
    if pieces and good and not any(m.group("card") == cid for m in good):
        out.append(f"no art_ref_check PASS line names card={cid}: judge the card's own references")
    for m in SMOKE_REFS.finditer(ev):
        if rh and m.group("refs") != rh:
            out.append(f"the smoke's art_judge line has refs={m.group('refs')}, not the current references.json ({rh})")
    if pieces:
        done = {}
        for m in ART_LOOP_LINE.finditer(ev):
            if m.group("card") != cid:
                continue
            if rh and m.group("refs") != rh:
                out.append(f"art_loop line for piece {m.group('piece')} has refs={m.group('refs')}, not {rh}: loop again "
                           "against the current references")
            elif hc and not same_commit(m.group("commit"), hc):
                out.append(f"art_loop line for piece {m.group('piece')} is for commit={m.group('commit')}, not {hc}")
            else:
                done[m.group("piece")] = True
        missing = [p for p in pieces if p not in done]
        if missing:
            out.append(f"card {cid} is an art card: pieces {', '.join(missing)} have no `art_loop: PASS` line on this "
                       "commit (`python3 tools/art_loop.py evidence --card " + cid + "`); the loop runs until the blind "
                       "critic cannot pick the reference over ours and every deterministic check passes")
    return out + artship_problems(ev, paths, root, hc, rh)


def artship_problems(ev, paths, root=ROOT, hc=None, rh=None):
    """Rule artship (Josh, 11 Nov: the reference bar is enforced, not advised). Every shipped art file the PR adds
    or changes (an image under Art/ outside Art/Source/) needs (1) its pasted `art_loop: PASS ... file=<path>
    sha=<sha12>` line for the evidence header commit and the current references.json, and (2) its committed
    <stem>.artloop.json record (tools/art_loop.py): the blind critic picked ours or SAME against a reference AND the
    quality bar (and the motion pair for a sheet), and art_check, screen_check and art_ref_check passed, on these
    exact bytes. A Content/*/Art, VFX or UI asset change (not string tables, data tables or fonts) needs such a line
    for the image it was imported from. A labelled
    placeholder or stand-in never passes. Nothing waives it: no label, sign-off or human approval."""
    sys.path.insert(0, os.path.join(ROOT, "tools"))
    import art_loop
    images = [p for p in paths if art_loop.shipped(p) and os.path.isfile(os.path.join(root, p))]
    assets = [p for p in paths if ships_art(p)]
    if not images and not assets:
        return []
    out = []
    good = {}
    for m in ART_LOOP_FILE.finditer(ev):
        if rh and m.group("refs") != rh:
            out.append(f"art_loop line for {m.group('file')} has refs={m.group('refs')}, not {rh}: loop again")
        elif hc and not same_commit(m.group("commit"), hc):
            out.append(f"art_loop line for {m.group('file')} is for commit={m.group('commit')}, not {hc}")
        else:
            good[m.group("file")] = m.group("sha")
    for p in images:
        full = os.path.join(root, p)
        sha = art_loop.content_sha(full)[:12]
        if p not in good:
            out.append(f"{p} is shipped art with no `art_loop: PASS ... file={p} sha={sha}` line on this commit: "
                       "loop it (tools/art_loop.py) until the blind critic picks ours or SAME against a reference and "
                       "the quality bar and every check passes, then paste `art_loop.py evidence`")
        elif good[p] != sha:
            out.append(f"{p}: the art_loop line names sha={good[p]}, the file is {sha}: these bytes were never judged")
        out += [f"art_loop record: {x}" for x in art_loop.record_problems(root, p, rh)]
    if assets and not any(art_loop.shipped(f) and not art_loop.record_problems(root, f, rh) for f in good):
        out.append(f"{assets[0]} ships art: paste the file-bound `art_loop: PASS ... file=Art/... sha=...` line of the "
                   "image it was imported from (with its committed .artloop.json record)")
    return out


def art_evidence_problems(ev, root=ROOT, changed=()):
    """Rule art: the pasted smoke ran art_check.py, screen_check.py and (on a gameplay map) art_judge.py scene on its
    screenshot and each passed."""
    gameplay = any(m.group("map").rsplit("/", 1)[-1].split(".")[0] not in ue_run_no_player(root)
                   for m in SMOKE_LINE.finditer(ev))
    got = {}
    for m in ART_LINE.finditer(ev):
        got.setdefault(m.group("tool"), []).append(m.group("v"))
    boot_ok = ue_run.art_bootstrap(root) and not any(
        p.strip().lstrip("./").startswith("Content/UmbrellaElla/Art/Anchors/") for p in changed or [])
    boot = ART_BOOT.search(ev)
    out = []
    for tool in ("art_check", "screen_check", "art_judge"):
        if tool == "art_judge" and tool not in got and not gameplay:
            continue   # the scene judge runs on gameplay maps only (no-player maps: title, style frame)
        if tool not in got:
            out.append(f"Evidence has a SMOKE_OK line but not the smoke's `smoke-art: {tool}: PASS` line: paste the "
                       f"whole smoke.sh / smoke.ps1 output (the smoke runs tools/{tool}.py on its own screenshot; GitHub "
                       "CI cannot run Unreal, so the line comes from the build machine)")
        elif "FAIL" in got[tool] and not (boot_ok and boot):
            out.append(f"Evidence has `smoke-art: {tool}: FAIL`: fix the visual (regenerate or replace it; the "
                       "screen_check FIX: line says how) and smoke again")
    if boot and not boot_ok:
        out.append("Evidence has the `smoke-art: bootstrap` line, but Content/UmbrellaElla/Art/Anchors/ exists (card "
                   "0.10b): the art checks block now, smoke again")
    return out


def effective_evidence_problems(ev, header, root, tester_ok=False):
    """Final-9 B C1, H2, H3: with the smoke hook, the packaged game is the evidence. Its SMOKE_EFFECTIVE line is pasted
    (smoke.sh / smoke.ps1 print it), one is from the submission package (workbench=0) of the header commit, and each
    passes `bake_preset.py effective` on this tree: every live value is the baked or marked one."""
    import bake_preset
    out = []
    effs = [(x.group(0).strip(), ue_run.parse_effective("SMOKE_EFFECTIVE" + x.group("rest"))) for x in EFFECTIVE.finditer(ev)]
    if not effs:
        return ["Evidence has SMOKE_OK but not the game's `SMOKE_EFFECTIVE ...` line: paste the whole smoke.sh / "
                "smoke.ps1 output (the live tuning values and flags, tools/ue_run.py contract; final-9 B C1)"]
    if not any(e.get("workbench") == "0" for _, e in effs):
        out.append("no SMOKE_EFFECTIVE line has workbench=0: paste the submission package's smoke")
    if not any(e.get("at") == "end" for _, e in effs):
        out.append("no `SMOKE_EFFECTIVE at=end` line: the hook reads the values again when the run ends (final-10 B H3); "
                   "paste the whole smoke.sh / smoke.ps1 output")
    for raw, e in effs:
        if e.get("workbench") == "1" and not tester_ok:
            out.append(f"'{raw[:60]}' is from a workbench build; PR evidence is the submission package")
        if header and not same_commit(e.get("commit"), header.group("commit")):
            out.append(f"SMOKE_EFFECTIVE commit={e.get('commit')}: the game was compiled from another commit than the "
                       f"evidence header {header.group('commit')}")
        out += [f"SMOKE_EFFECTIVE: {p}" for p in bake_preset.effective_problems(root, e)]
    return out


def windows_evidence_problems(ev, why):
    """Final-9 A H5: the card names package.ps1 / smoke.ps1 / daily.ps1, so the Windows run is part of done."""
    out = []
    if not PACKAGE_WIN.search(ev):
        out.append("the card's Done-when names a Windows script, but Evidence has no `package exit: 0  commit=<sha>  "
                   "dirty=no ... platform=Win64` line from package.ps1: run it on the Windows packaging machine. "
                   "Mac-only evidence fails the same as a 'Not run' line (no Mac fallback rule yet)")
    if why and SMOKE_LINE.search(ev) and not any(ue_run.parse_effective("SMOKE_EFFECTIVE" + x.group("rest")).get("platform")
                                                 == "Windows" for x in EFFECTIVE.finditer(ev)):
        out.append("the card's Done-when names a Windows script, but no SMOKE_EFFECTIVE line has platform=Windows: "
                   "paste the smoke.ps1 output of the Win64 package")
    return out


def not_done_problems(text):
    out, has_next, has_unread = [], False, False
    text = re.sub(r"<!--.*?-->", "", text, flags=re.S)
    for line in text.splitlines():
        ln = line.strip().lstrip("-* ").strip()
        if not ln or re.fullmatch(r"<[^>]*>", ln):
            continue
        if ln.lower().startswith("next:"):
            if re.search(r"\w", re.sub(r"<[^>]*>", "", ln[5:])):
                has_next = True
            continue
        if ln.lower().startswith("could not read:"):
            if re.search(r"\w", re.sub(r"<[^>]*>", "", ln[15:])):
                has_unread = True
            continue
        if re.fullmatch(r"none\.?", ln, re.I):
            continue
        if not LINK.search(ln):
            out.append(f"'Not done' line has no link (#<issue>, D-row or URL): '{ln[:70]}'")
    if not has_next:
        out.append("'Not done / risks' needs a `Next:` line (next role and step, or 'none')")
    if not has_unread:
        out.append("'Not done / risks' needs a `Could not read:` line (inputs or docs you could not open, or 'none')")
    return out


def card_key(card):
    return re.sub(r"(?i)^ue-", "", card.strip()).lower()


HUMAN_JOURNAL = re.compile(r"^\W*Human card, no agent session\b", re.I | re.M)


def human_card(card, s):
    """A card whose Owner role is Human has no agent session, so no journal export (no Day-0 card is Human-owned now:
    check_card rejects it; this is for a card filed before that rule): the
    Journal section says `Human card, no agent session`. Read from the linked card (--card), never from the PR body
    alone, so an agent PR cannot claim it (final-7 dry run A M4)."""
    if not card or not HUMAN_JOURNAL.search(s.get("Journal", "")):
        return False
    try:
        import check_card
        got = check_card.parse(card.get("body") or "", check_card.template_fields(ROOT))
        owner = (got[0] if isinstance(got, tuple) else got).get("Owner role", "")
    except Exception:  # pragma: no cover
        return False
    return (owner or "").strip() == "Human"


def journal_problems(s):
    j = re.sub(r"<!--.*?-->", "", s.get("Journal", ""), flags=re.S)
    m = JOURNAL_MARK.search(j)
    if not m:
        return ["'## Journal' needs the block from `python3 tools/journal.py export --card <id>` (its "
                "`journal.py export card=<id>` line); AGENTS.md section 6"]
    out = []
    c = CARD_ID_LINE.search(s.get("Task", ""))
    if c and card_key(c.group(1)) != card_key(m.group(1)):
        out.append(f"'## Journal' is the export for {m.group(1)}, but the Task's Card ID is {c.group(1)}")
    if not re.search(r"^Next step:\s*\S", j, re.M):
        out.append("'## Journal' has no `Next step:` line; paste the whole journal.py export block")
    return out


REVERT_OF = re.compile(r"^[ \t]*Revert of: (?P<sha>[0-9a-f]{40})\b", re.M)
REVERT_JOURNAL = re.compile(r"^\W*Revert bot, no agent session\b", re.M)


def changed_lines(diff):
    """A -U0 diff without the lines that depend on context or position (index blob ids, @@ hunk headers)."""
    return [ln for ln in diff.split(b"\n") if not ln.startswith((b"index ", b"@@"))]


def revert_problems(root, sha, base):
    """Final-10 A H3: a lane_guard revert PR (AGENTS.md section 6) undoes one squash commit that passed every check
    when it merged. It is waived from build, test, package and smoke evidence only when its diff against the base
    is exactly the inverse of that commit (the same removed and added lines, file by file), so nothing else can ride
    along. Returns problems."""
    import subprocess

    def run(*args, stdin=None):
        return subprocess.run(["git", "-C", root, *args], capture_output=True, input=stdin)
    if not base:
        return [f"'Revert of: {sha[:12]}' needs the PR base (--base; CI passes it) to check the revert"]
    parents = run("rev-list", "--parents", "-n", "1", sha)
    if parents.returncode != 0:
        return [f"'Revert of: {sha[:12]}': that commit is not in this clone (CI fetches it with --depth=2)"]
    if run("merge-base", "--is-ancestor", sha, base).returncode != 0:
        return [f"'Revert of: {sha[:12]}' is not a commit of the base branch: a revert PR undoes a commit on main"]
    # Final-11 A H2: patch-id hashes context lines, so a later card's edit next to the reverted lines (the row-scoped
    # test map) made a non-tip revert fail. Compare only what changes: per file, the removed and added lines in order
    # (-U0, no index or hunk position lines), plus the file headers and binary patches.
    inverse = run("diff", "-U0", "--binary", "--no-color", "--no-ext-diff", sha, sha + "^1")
    pr = run("diff", "-U0", "--binary", "--no-color", "--no-ext-diff", base, "HEAD")
    if inverse.returncode or pr.returncode:
        return [f"'Revert of: {sha[:12]}': git diff failed: fetch the base and the reverted commit"]
    a, b = changed_lines(inverse.stdout), changed_lines(pr.stdout)
    if not a or a != b:
        return [f"'Revert of: {sha[:12]}': the PR's diff is not exactly the inverse of {sha[:12]}: a revert PR changes "
                "nothing else (open a normal PR with full evidence for any other change)"]
    return []


def problems(body, changed=None, head=None, root=ROOT, card=None, base=None):
    s = sections(body)
    out = []
    rv = REVERT_OF.search(s.get("Evidence", ""))
    if rv:   # final-10 A H3: the lane_guard revert PR; sections still required, evidence replaced by the patch check
        out += revert_problems(root, rv.group("sha"), base)
        for r in REQUIRED:
            if r not in s or not meaningful(s[r]):
                out.append(f"section '## {r}' is missing or empty")
        if "Not done / risks" in s:
            out += not_done_problems(s["Not done / risks"])
        if not REVERT_JOURNAL.search(s.get("Journal", "")):
            out.append("a revert PR's Journal says `Revert bot, no agent session`")
        if "Task" in s and not TASK_LINK.search(s["Task"]):
            out.append("Task section must link the card issue: 'Part of #<number>'")
        return out
    for r in REQUIRED:
        if r not in s:
            out.append(f"missing section '## {r}'")
        elif not meaningful(s[r]):
            out.append(f"section '## {r}' is empty or still the template")
    if "Evidence" in s and meaningful(s["Evidence"]):
        ev = re.sub(r"<!--.*?-->", "", s["Evidence"], flags=re.S)
        ev = "\n".join(ln for ln in ev.splitlines() if not HEADER.search(ln)).strip().lower()
        if not meaningful(ev):
            out.append("section '## Evidence' is empty or still the template")
        elif re.fullmatch(r"[\s\-*]*(n/?a|none|tbd|todo|see above|-)[\s.]*", ev):
            out.append("Evidence must show output or say what was not run and why; 'n/a' alone is not evidence")
        elif not PROOF.search(re.sub(r"<[^>]*>", "", ev)):
            out.append("Evidence has no re-runnable line: paste a command and its output (PASS/FAIL, exit code, a "
                       "key=value line) or 'Not run: <what>, <why>'. A claim like 'all good' is not evidence (AGENTS.md section 5)")
    if "Evidence" in s and meaningful(s["Evidence"]):
        out += evidence_problems(s, changed, head, root, card)
    if "Not done / risks" in s and meaningful(s["Not done / risks"]):
        out += not_done_problems(s["Not done / risks"])
    if "Journal" in s and not human_card(card, s):
        out += journal_problems(s)
    out += gdd_problems(s, changed)
    out += bake_problems(s, changed)
    out += hitbox_problems(s, changed, root)
    out += artref_problems(s, changed, root)
    out += audio_problems(s, changed, root)
    out += encounter_problems(s, changed, body, card, root)
    out += story_problems(s, changed, root, base)
    out += editor_problems(s, changed)
    out += gate_problems(s, changed, root, card, head, base)
    if "Task" in s and not TASK_LINK.search(s["Task"]):
        out.append("Task section must link the card issue: 'Part of #<number>' (D-new-port-1 default) or 'Closes #<number>'")
    return out


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("body", nargs="?")
    ap.add_argument("--changed", help="file with one changed path per line")
    ap.add_argument("--head", help="PR head commit SHA (read from the event when absent)")
    ap.add_argument("--base", help="PR base commit SHA (read from the event when absent): a `Revert of:` PR is "
                                   "checked against it (final-10 A H3)")
    ap.add_argument("--card", help="the linked card as `gh issue view N --json title,body` JSON: its Done-when "
                                   "decides package evidence too (dry run A H4)")
    a = ap.parse_args(sys.argv[1:] if argv is None else argv)
    head, base = a.head, a.base
    if a.body:
        with open(a.body, encoding="utf-8") as fh:
            body = fh.read()
    else:
        path = os.environ.get("GITHUB_EVENT_PATH")
        if not path:
            print("check_pr: no body file and no GITHUB_EVENT_PATH")
            return 2
        with open(path, encoding="utf-8") as fh:
            pr = json.load(fh).get("pull_request") or {}
        body = pr.get("body") or ""
        head = head or (pr.get("head") or {}).get("sha")
        base = base or (pr.get("base") or {}).get("sha")
    changed = []
    if a.changed:
        with open(a.changed, encoding="utf-8") as fh:
            changed = [ln.strip() for ln in fh if ln.strip()]
    card = None
    if a.card:
        with open(a.card, encoding="utf-8") as fh:
            card = json.load(fh)
    p = problems(body, changed, head, card=card, base=base)
    for x in p:
        print("- " + x)
    print(f"check_pr: {len(p)} problem(s)")
    return 1 if p else 0


if __name__ == "__main__":
    sys.exit(main())
