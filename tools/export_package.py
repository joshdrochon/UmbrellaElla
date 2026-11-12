#!/usr/bin/env python3
"""Build MegaPipeline/, the human-browsable package of the jam pipeline. Stdlib only.

The repo files stay the single source of truth. This script copies them into one folder people can read
and share: the agent instructions, one file per role card, one file per discipline, and the reference docs.
Every generated file starts with a stamp naming its sources and the commit the export ran on.
Agents never load MegaPipeline/; they keep loading AGENTS.md and pipeline/roles/ from the repo.

Every doc in the repo (.md .txt .json .csv .yml .yaml .example, outside tests/, eval cases and the game roots in
GAME_ROOTS) and every script (tools/, pipeline/) must land in exactly one package file. An unmapped file is an orphan: add it
to PIPELINES below.

Usage: python3 tools/export_package.py            write MegaPipeline/ (removes files it no longer makes)
       python3 tools/export_package.py --check    exit 1 if MegaPipeline/ is stale, hand-edited or a doc is unmapped
       python3 tools/export_package.py --zip      write dist/MegaPipeline-<shortsha>.zip from a fresh build
Same sources and commit give byte-identical output. --check ignores the commit in the stamp, so a package
built one commit earlier from the same sources still passes.
Exit 0 = ok, 1 = problems, 2 = usage error.
"""
import argparse
import ast
import fnmatch
import os
import re
import subprocess
import sys
import zipfile

PKG = "MegaPipeline"
SELF = "tools/export_package.py"
DOC_EXT = {".md", ".txt", ".json", ".csv", ".yml", ".yaml", ".example"}
EXTRA_DOCS = {"docs/gdd/CURRENT"}
SCRIPT_EXT = {".py", ".sh", ".ps1"}
SCRIPT_DIRS = ("tools/", "pipeline/")
SKIP = ("tests/", "evals/reviewer/cases/", "evals/reviewer/runs/", PKG + "/", "dist/")
# An installed repo (MegaPipeline/install.sh copied the pipeline to the root) keeps the shipped package beside the
# generated files: the repo copy, its tests and the installer, plus the root install record. The exporter never makes
# them, so --check does not report them and a rebuild does not delete them. tools/pipeline_check.py has the same list.
INSTALLED = ".pipeline-installed.json"
SHIPPED_DIRS = ("repo/", "tests/")
SHIPPED_FILES = {"install.py", "install.sh", "install.ps1", "manifest.json", "INSTALL.md"}
# Final-8 dry run A H6: the game the jam cards build is not pipeline doc. Its data files (sprite sidecars, the UI
# string table and text styles, workbench sample notes, scratch notes from the never-merged card 0.9 / 0.18 branches,
# Config ini) live under these roots and never land in the package, so a card that makes one is not an orphan.
GAME_ROOTS = ("Art/", "Audio/", "Content/", "Source/", "Config/", "Plugins/", "Samples/", "scratch/", "Saved/",
              "Packaged/", "Binaries/", "Intermediate/", "DerivedDataCache/")
ROLE_DIR = "pipeline/roles/"
AGENT_DIR = ".claude/agents/"
GDD_DIR = "docs/gdd/"
STAMP_RE = re.compile(r"^(> Generated from .* at `)([0-9a-f]{4,40}|unknown)(` — edit the sources, not this file\.)", re.M)
LANG = {".json": "json", ".csv": "csv", ".yml": "yaml", ".yaml": "yaml", ".py": "text", ".sh": "text",
        ".ps1": "text", ".txt": "text", ".example": "text", "": "text"}
ACRONYMS = {"qa": "QA", "ui": "UI", "ux": "UX"}

# One entry per Pipelines/ file: name, owner, purpose, inputs, outputs, gates, then (section, [patterns]).
# Patterns are repo paths or fnmatch globs. Scripts listed in a section get their usage text, the CI steps
# that run them and the tests that cover them.
PIPELINES = [
    {
        "name": "Production",
        "owner": "Producer role; the scope decision-maker and integration owner in `docs/jam-brief.md` are the humans.",
        "purpose": "Turn the brief into ready task cards, keep lanes parallel, run the daily cadence, call cuts and record gates.",
        "inputs": "The jam brief and rules, the Day-0 card list, open rows in `docs/decisions.md`.",
        "outputs": "Task cards (GitHub issues), lane plan, status line, gate records, cut calls, new decision rows.",
        "gates": "A card is not `todo` until `check_card.py` passes. G1-G4 are closed with a gate record. Main red: revert first.",
        "sections": [
            ("Brief, rules and the Day-0 plan", ["docs/jam-brief.md", "docs/jam-rules.md", "pipeline/day0-cards.md"]),
            ("Humans in the loop", ["pipeline/human-checkpoints.md", "pipeline/how-to-run-the-jam.md",
                                    "pipeline/what-the-pipeline-controls.md"]),
            ("Checklists", ["pipeline/checklists/card-ready.md"]),
            ("Templates", ["pipeline/templates/task-card.md", "pipeline/templates/spike-card.md",
                           "pipeline/templates/gate-record.md", "pipeline/templates/tracker-table.md",
                           "pipeline/templates/clock-workflow.yml", ".github/ISSUE_TEMPLATE/task.yml"]),
            ("Automation", [".github/workflows/blocked-report.yml", ".github/workflows/main-red.yml",
                            "?.github/workflows/clock.yml"]),   # card 0.16 copies pipeline/templates/clock-workflow.yml
            ("Commands and checks", ["tools/check_card.py", "tools/lane_guard.py", "tools/status_board.py"]),
        ],
    },
    {
        "name": "Design",
        "owner": "Game Designer role; the game design owner (human) accepts numbers and design calls.",
        "purpose": "Keep the game spec, balance targets and tuning changes in line with the current GDD snapshot.",
        "inputs": "The GDD snapshot and feature manifest (see Reference/), playtest rows of class `design`.",
        "outputs": "`docs/game-spec.md` defaults, `docs/balance.md` targets, tuning cards, questions for the GDD authors.",
        "gates": "Design review before a rule card is ready; `manifest_check.py` in CI; `gdd_impact.py` on a GDD revision.",
        "sections": [
            ("How a GDD revision lands", ["docs/gdd/README.md", "docs/gdd/questions-*.md"]),
            ("Spec and balance", ["docs/game-spec.md", "docs/balance.md"]),
            ("Checklists", ["pipeline/checklists/design-review.md", "pipeline/checklists/tuning.md"]),
            ("Commands and checks", ["tools/manifest_check.py", "tools/gdd_impact.py", "tools/gdd_select.py",
                                     "tools/bake_preset.py", "tools/tuning.py", "tools/progression_model.py"]),
        ],
    },
    {
        "name": "Development",
        "owner": "Dev Lead (review) and Gameplay Dev (code).",
        "purpose": "Write and review gameplay C++ on Unreal 5.8.4 to one standard, with tests and a review gate.",
        "inputs": "A ready task card, the Unreal rules, the engine headers.",
        "outputs": "Code PRs with evidence, review verdicts, reviewer eval results.",
        "gates": "Dev Lead review on every code PR; `check_pr.py` on the PR body; the reviewer eval when the review prompt or model changes.",
        "sections": [
            ("Unreal rules", ["pipeline/unreal-rules.md", "pipeline/unreal/cpp-rules.md",
                              "pipeline/unreal/gameplay-code.md", "docs/unreal-sources.md"]),
            ("Checklists", ["pipeline/checklists/file-hygiene.md"]),
            ("Pull request template", [".github/PULL_REQUEST_TEMPLATE.md"]),
            ("Reviewer eval", ["evals/reviewer/results.md", "tools/run_reviewer_eval.py", "tools/score_review.py"]),
            ("Commands and checks", ["tools/check_pr.py"]),
        ],
    },
    {
        "name": "Technical Development",
        "owner": "Technical Director (agent role plus the TD human).",
        "purpose": "Own modules, build scripts, config, plugins and the repo guardrails that every other lane relies on.",
        "inputs": "Day-0 skeleton cards, `pipeline/unreal-rules.md`, engine logs.",
        "outputs": "Build and validate scripts, module boundaries, CI checks, this package's exporter.",
        "gates": "`pipeline_check.py` and the unit tests in CI; `module_check.py` once `Source/` exists; local compile logs in the PR.",
        "sections": [
            ("Commands and packaging", ["pipeline/unreal/commands-and-packaging.md"]),
            ("CI and repo settings", [".github/workflows/pipeline-checks.yml", ".github/CODEOWNERS.example"]),
            ("Commands and checks", ["tools/pipeline_check.py", "tools/module_check.py", "tools/ue_run.py",
                                     "tools/ue/common.*", "tools/ue/build.*", "tools/ue/validate.*", SELF]),
            ("Editor scripts (cards 0.8a and later)", ["?pipeline/unreal/editor_scripts/*"]),
        ],
    },
    {
        "name": "QA",
        "owner": "QA and Build role; the playtest lead (human) runs cold playtests.",
        "purpose": "Daily packaged build, smoke run, automation tests, the GDD test catalog and cold playtests.",
        "inputs": "`main` at the day's cut, the GDD test catalog, playtest presets.",
        "outputs": "Daily build records, automation results, bug cards, playtest rows and test notes.",
        "gates": "A red build is reported within the hour; a QA test row has a passing automation test before its feature is done.",
        "sections": [
            ("Test catalog and playtests", ["pipeline/qa/test-map.md", "pipeline/qa/playtests.md", "pipeline/qa/presets.json", "pipeline/qa/no-player-maps.txt",
                                            "?pipeline/qa/baked.json"]),
            ("Templates", ["pipeline/templates/test-note.md"]),
            ("Daily build", ["tools/ue/daily-checklist.md", "tools/ue/smoke-allow.txt"]),
            ("Commands and checks", ["tools/check_automation_report.py", "tools/ue/test.*", "tools/ue/daily.*",
                                     "tools/ue/package.*", "tools/ue/smoke.*"]),
        ],
    },
    {
        "name": "Art",
        "owner": "Art Director (direction, review) and Asset Specialist (sprites, flipbooks, provenance).",
        "purpose": "One look that matches the key art, measured in-engine, with every asset traced to a licence.",
        "inputs": "Every reference picture in `pipeline/art/references.json` (the curated set under `pipeline/art/reference/`, the key art first, plus the team art under `Assets/` and `Mockups/` it joins each run), the art bible, asset briefs on cards.",
        "outputs": "Sprites, flipbooks and backgrounds rendered in Blender (pipeline/art/blender/), art review verdicts, provenance rows, art-loop pass records, the art-judge calibration set.",
        "gates": "The automated art gate on every visible change (`art_check.py --gate`: references, numbers, calibrated blind judge; no human art sign-off). Automatic on every smoke: `art_check.py`, `screen_check.py` and `art_judge.py scene` on the smoke screenshot; `art_ref_check.py` against each card's references; the art loop (builder and blind critic until the references' bar: ours or SAME against a reference, the quality bar and, for a sheet, in motion); `check_pr.py` rules art, artref, artloop and artship in CI; `submission_check.py art` on the package; `sprite_check.py` in CI.",
        "sections": [
            ("Art direction", ["pipeline/art/art-bible.md", "pipeline/art/style.json", "pipeline/art/references.json",
                               "pipeline/art/reference/discord/index.json",
                               "pipeline/art/reference/Test_Assets/SpriteLayout.json",
                               "pipeline/art/reference/Test_Assets/Asset Notes.md"]),
            ("Blender art generator", ["pipeline/art/blender/characters.json", "pipeline/art/blender/plan.py",
                                       "pipeline/art/blender/stand_ins.py", "pipeline/art/blender/render_sprite.py"]),
            ("Import and provenance", ["pipeline/art/import-rules.md", "pipeline/art/provenance.csv",
                                       "?pipeline/art/fallback-cc0.csv"]),   # card 0.15
            ("Checklists and templates", ["pipeline/checklists/animation-review.md", "pipeline/templates/asset-brief.md"]),
            ("Art judge", ["evals/art-judge/README.md", "evals/art-judge/blind_pairwise.md",
                           "evals/art-judge/agreement.csv", "evals/art-judge/critic-calibration.json",
                           "tools/art_judge_prompt.md"]),
            ("Commands and checks", ["tools/art_check.py", "tools/screen_check.py", "tools/art_judge.py",
                                     "tools/art_ref_check.py", "tools/art_loop.py", "tools/sprite_check.py",
                                     "tools/make_art_calibration.py", "tools/png.py"]),
        ],
    },
    {
        "name": "Audio",
        "owner": "Audio role; the audio owner (human) approves by ear in the packaged build.",
        "purpose": "Every sound the game makes, on one gothic orchestral bar, with a mix that keeps every warning audible.",
        "inputs": "The sound list, the event coverage map, the style target, the audio rules, the GDD sound needs, supplied files.",
        "outputs": "Source WAVs, sound assets, provenance rows, critic verdicts, mix approvals.",
        "gates": "`audio_check.py --list`, `--events`, `--docs` and `--scan` and `audio_style_check.py check` in CI; the editor dump check; the builder and critic loop (`audio_loop.py close`, required on audio PRs); the human final listen.",
        "sections": [
            ("Style target and coverage", ["pipeline/audio/style-target.md", "pipeline/audio/style.json",
                                           "pipeline/audio/sound-events.json"]),
            ("Audio rules and sound list", ["pipeline/audio/audio-rules.md", "pipeline/audio/audio-rules.json",
                                            "pipeline/audio/sound-list.csv"]),
            ("Builder and critic loop", ["tools/audio_loop.py", "tools/audio_critic_prompt.md"]),
            ("Commands and checks", ["tools/audio_check.py", "tools/audio_style_check.py", "tools/audio_import.py",
                                     "tools/ue/audio_dump.py", "pipeline/audio/ue/audio_dump.py"]),
        ],
    },
    {
        "name": "Story",
        "owner": "Story role (an agent); Richard (game design owner) confirms what is canon.",
        "purpose": "One story bible and every player-facing word (in-game text, store page, video narration), checked by a machine gate and a separate blind critic.",
        "inputs": "The GDD snapshot, the team's #story channel (pasted on the card by a human), the art bible, the menu list.",
        "outputs": "`pipeline/story/story-bible.md`, `pipeline/story/lines.csv`, the tone sheet for the art, audio and menu lanes.",
        "gates": "`story_check.py` in CI and on every story PR; the blind critic's STORY_CRITIC PASS line (`check_pr.py` rule story, `check_card.py` rule story); Richard's STORY CONFIRM line for canon.",
        "sections": [
            ("Story bible and lines", ["pipeline/story/story-bible.md", "pipeline/story/lines.csv", "pipeline/story/story.json"]),
            ("Critic", ["tools/story_critic_prompt.md", "evals/story-critic/README.md", "evals/story-critic/calibration.csv"]),
            ("Commands and checks", ["tools/story_check.py"]),
        ],
    },
    {
        "name": "Level",
        "owner": "Level Designer (arena numbers, owl patterns, pacing), Encounter Designer (the boss fight as a whole: "
                 "encounter presets, critic loop) and Integrator (map, placement, thin Blueprints).",
        "purpose": "One arena and one owl encounter in three phases, described as data and checked before it is built.",
        "inputs": "The GDD encounter rules, `docs/balance.md`, playtest hit logs.",
        "outputs": "`pipeline/level/encounter.json` (top-level data and `encounter_presets`), the generated tables in "
                   "`pipeline/level/encounter.md`, the arena map.",
        "gates": "`encounter_check.py` (data, presets, wiring, playtest, run log, critic lines) in CI and before `doing`; "
                 "`check_pr.py` rule encounter; the arena acceptance checklist.",
        "sections": [
            ("Encounter data", ["pipeline/level/encounter.md", "pipeline/level/encounter.json"]),
            ("Checklists", ["pipeline/checklists/level-sections.md"]),
            ("Encounter references", ["pipeline/level/reference/*"]),
            ("Check fixtures", ["pipeline/level/fixtures/*"]),
            ("Commands and checks", ["tools/encounter_check.py", "tools/encounter_spec.py"]),
        ],
    },
    {
        "name": "UI UX",
        "owner": "UI and UX role.",
        "purpose": "Menus, prompts and the basic accessibility tier, each rule with a command and a threshold.",
        "inputs": "The GDD UI needs, the art bible, the feel signals.",
        "outputs": "UI art, the UI string text, UI review verdicts.",
        "gates": "`ui_check.py ci` in CI; `ui_check.py ci --release` at each gate.",
        "sections": [
            ("Rules", ["pipeline/ui/accessibility.md", "pipeline/ui/menus.md", "pipeline/ui/signals.json"]),
            ("Captures (card 0.22 and later)", ["?pipeline/ui/captures/*"]),
            ("Commands and checks", ["tools/ui_check.py"]),
        ],
    },
    {
        "name": "Game Feel",
        "owner": "Game Designer (numbers) with the creative director (human) for feel calls.",
        "purpose": "Hit-stop, shake, input latency and other feel numbers, kept in data and tested A/B.",
        "inputs": "The feel spec, playtest notes, latency measurements.",
        "outputs": "`pipeline/feel/feel.json`, A/B, arena and latency log rows.",
        "gates": "`feel_check.py` and `hitbox_check.py check` (art aligns to colliders) in CI; latency measured on the packaged build.",
        "sections": [
            ("Feel spec and data", ["docs/feel-spec.md", "pipeline/feel/feel.json", "pipeline/feel/hitboxes.json"]),
            ("Logs", ["pipeline/feel/*.csv"]),
            ("Commands and checks", ["tools/feel_check.py", "tools/hitbox_check.py"]),
        ],
    },
    {
        "name": "Agent Ops",
        "owner": "Agent Ops role; gate files change only by a human PR.",
        "purpose": "Agent settings, hooks, journals, prompt logs and secrets checks, so agents stay in their lanes.",
        "inputs": "The gate list, the role list, the team's agent CLIs.",
        "outputs": "Installed agent settings, hook logs, journals, prompt exports, eval runs.",
        "gates": "`secrets_check.py` in CI; the hook blocks writes outside a role's lane; the guardrail rehearsal.",
        "sections": [
            ("Agent ops", ["pipeline/agent-ops/README.md", "pipeline/agent-ops/gates.json",
                           "pipeline/agent-ops/settings.json", "pipeline/agent-ops/agent-tools.json",
                           "pipeline/agent-ops/components.csv", "pipeline/agent-ops/model-tiers.md",
                           "pipeline/agent-ops/model-prices.json", "pipeline/agent-ops/asset-tools.json"]),
            ("Editor MCP", ["pipeline/agent-ops/editor-mcp.md", "pipeline/agent-ops/mcp.template.json",
                            "tools/editor_mcp.py", "pipeline/agent-ops/mcp.tools.template.json",
                            "tools/mcp_config.py"]),
            ("One command (kickoff) for Claude Code and Codex", ["tools/kickoff.sh", "tools/kickoff.ps1",
                                                                "tools/kickoff.py", "tools/connections.py",
                                                                "tools/keys.py", "tools/practice.py",
                                                                "tools/git_gate.py", "tools/assetgen.py"]),
            ("Prompts, evals and sources", ["prompts/README.md", "evals/README.md", "docs/references.md"]),
            ("Repo map (agents read it second)", ["docs/repo-map.md", "tools/repo_map.py"]),
            ("Commands and checks", ["pipeline/agent-ops/hook.py", "pipeline/agent-ops/journal_hook.py",
                                     "tools/journal.py", "tools/install_git_hooks.py", "tools/agent.sh",
                                     "tools/agent.ps1", "tools/start_session.sh", "tools/start_session.ps1",
                                     "tools/start_session.py", "tools/spend_log.py", "tools/prompt_log.py",
                                     "tools/secrets_check.py"]),
        ],
    },
    {
        "name": "Submission",
        "owner": "Packaging and submission owner (human) with QA and Build.",
        "purpose": "Ship a clean build, page, video, credits and declaration on time.",
        "inputs": "The packaged build, footage log, provenance rows, jam rules.",
        "outputs": "The submission zip, itch page, video, devlog, credits, README and licence files.",
        "gates": "G4 submission checklist; `submission_check.py` for zip, credits, footage and gate records.",
        "sections": [
            ("Checklist and declaration", ["pipeline/checklists/submission.md", "docs/pre-jam-declaration.md"]),
            ("Submission files", ["pipeline/submission/*"]),
            ("Commands and checks", ["tools/submission_check.py"]),
        ],
    },
]

# Reference/: copied as-is. (file name, [sources]); "@gdd" = the snapshot docs/gdd/CURRENT names,
# "@gdd-archive" = every other GDD file (archive/ and older snapshots).
REFERENCE = [
    ("GDD Snapshot.md", ["@gdd"]),
    ("Official Rules.md", ["docs/rules/official-rules.md"]),
    ("Feature Manifest.md", ["docs/feature-manifest.json"]),
    ("Decisions.md", ["docs/decisions.md"]),
    ("Coverage Map.md", ["docs/coverage-map.md"]),
    ("Port Log.md", ["docs/port-log.md"]),
    ("Pipeline Audit.md", ["docs/audit.md"]),
    ("GDD Archive.md", ["@gdd-archive"]),
]


# ---- repo access ------------------------------------------------------------------------------
def git(root, *args):
    return subprocess.run(["git", *args], cwd=root, capture_output=True, text=True)


def head_commit(root):
    p = git(root, "rev-parse", "HEAD")
    return p.stdout.strip()[:7] if p.returncode == 0 and p.stdout.strip() else "unknown"


def tracked(root):
    """Tracked files plus new files not yet added (ignored files never count)."""
    p = git(root, "ls-files", "-z")
    if p.returncode != 0:
        raise SystemExit("export_package: not a git repo: " + root)
    files = {f for f in p.stdout.split("\0") if f}
    new = git(root, "ls-files", "-o", "--exclude-standard", "-z")  # a new doc is mapped before `git add`
    files |= {f for f in new.stdout.split("\0") if f}
    return sorted(f for f in files if os.path.isfile(os.path.join(root, f)))


def read(root, rel):
    with open(os.path.join(root, rel), "rb") as f:
        text = f.read().decode("utf-8")
    text = text.replace("\r\n", "\n")
    return text if text.endswith("\n") else text + "\n"


def installed(root, out_dir=None):
    """True in a repo the pipeline was installed into (the install record or MegaPipeline/repo/ is there)."""
    out_dir = out_dir or os.path.join(root, PKG)
    return os.path.isfile(os.path.join(root, INSTALLED)) or os.path.isdir(os.path.join(out_dir, "repo"))


def shipped(rel):
    """True for a path (relative to MegaPipeline/) that belongs to the shipped package, not the exporter."""
    return rel.startswith(SHIPPED_DIRS) or rel in SHIPPED_FILES


def doc_set(files):
    """Repo files that must land in the package: docs and scripts."""
    out = []
    for f in files:
        if f.startswith(SKIP) or f.startswith(GAME_ROOTS) or f == INSTALLED:
            continue
        ext = os.path.splitext(f)[1].lower()
        if ext in DOC_EXT or f in EXTRA_DOCS or (ext in SCRIPT_EXT and f.startswith(SCRIPT_DIRS)) or f == SELF:
            out.append(f)
    return sorted(set(out))


def camel(stem):
    return "".join(ACRONYMS.get(p, p.capitalize()) for p in stem.split("-"))


# ---- rendering helpers ------------------------------------------------------------------------
def stamp(sources, commit):
    return "> Generated from " + ", ".join(f"`{s}`" for s in sources) + f" at `{commit}` — edit the sources, not this file.\n" \
        "> Rebuild: `python3 tools/export_package.py`. Check: `python3 tools/export_package.py --check`.\n\n"


def fence(text, lang):
    run = max([len(m) for m in re.findall(r"^\s*(`{3,})", text, re.M)] + [2])
    tick = "`" * (run + 1)
    return f"{tick}{lang}\n{text}{tick}\n"


def demote(text, by):
    """Push Markdown headings down `by` levels (max 6), outside code fences."""
    out, in_fence = [], None
    for line in text.split("\n"):
        m = re.match(r"^\s*(`{3,}|~{3,})", line)
        if m:
            mark = m.group(1)
            if in_fence is None:
                in_fence = mark
            elif mark[0] == in_fence[0] and len(mark) >= len(in_fence):
                in_fence = None
        elif in_fence is None:
            h = re.match(r"^(#{1,6})(\s.*)$", line)
            if h:
                line = "#" * min(6, len(h.group(1)) + by) + h.group(2)
        out.append(line)
    return "\n".join(out)


def as_markdown(root, rel, demote_by=0):
    text = read(root, rel)
    ext = os.path.splitext(rel)[1].lower()
    if ext == ".md":
        return demote(text, demote_by) if demote_by else text
    return fence(text, LANG.get(ext, "text"))


def script_usage(root, rel):
    text = read(root, rel)
    if rel.endswith(".py"):
        try:
            doc = ast.get_docstring(ast.parse(text), clean=True)
        except SyntaxError:
            doc = None
        if doc:
            return doc.rstrip() + "\n"
    lines = text.split("\n")
    if lines and lines[0].startswith("#!"):
        lines = lines[1:]
    block = []
    for line in lines:
        if line.startswith("#"):
            block.append(re.sub(r"^#+ ?", "", line))
        elif line.strip() == "" and not block:
            continue
        else:
            break
    return ("\n".join(block).rstrip() or "(no usage text in the file)") + "\n"


def ci_steps(root, files, rel):
    out = []
    for wf in [f for f in files if f.startswith(".github/workflows/") and f.endswith((".yml", ".yaml"))]:
        name = None
        for line in read(root, wf).split("\n"):
            m = re.match(r"\s*- name:\s*(.*)", line)
            if m:
                name = m.group(1).strip()
                continue
            if rel in line and name and (wf, name) not in out:
                out.append((wf, name))
    return out


def covering_tests(root, files, rel):
    base = os.path.basename(rel)
    stem = os.path.splitext(base)[0]
    pat = re.compile(r"\b" + re.escape(base) + r"\b|import " + re.escape(stem) + r"\b|[\"']" + re.escape(stem) + r"[\"']")
    return [t for t in files if t.startswith("tests/") and t.endswith(".py") and pat.search(read(root, t))]


def render_script(root, files, rel):
    parts = [f"Usage text from the file:\n\n", fence(script_usage(root, rel), "text")]
    steps = ci_steps(root, files, rel)
    if steps:
        parts.append("\nRun in CI by:\n\n" + "".join(f"- `{wf}`: {name}\n" for wf, name in steps))
    tests = covering_tests(root, files, rel)
    if tests:
        parts.append("\nTests: " + ", ".join(f"`{t}`" for t in tests) + "\n")
    return "".join(parts)


# ---- the build --------------------------------------------------------------------------------
def gdd_current(root):
    try:
        name = read(root, GDD_DIR + "CURRENT").strip()
    except OSError:
        return None
    return GDD_DIR + name if name else None


def resolve(patterns, docs, root):
    """Expand patterns against the doc set. Returns (paths, problems)."""
    out, problems = [], []
    cur = gdd_current(root)
    for pat in patterns:
        optional = pat.startswith("?")   # a file a later card writes (pipeline/qa/baked.json at G4; dry run B H5)
        pat = pat.lstrip("?")
        if pat == "@gdd":
            hit = [p for p in ([cur] if cur in docs else [])] + [GDD_DIR + "CURRENT"]
            if cur not in docs:
                problems.append(f"docs/gdd/CURRENT names {cur!r}, which is not a tracked file")
        elif pat == "@gdd-archive":
            hit = [d for d in docs if d.startswith(GDD_DIR + "archive/")
                   or (fnmatch.fnmatchcase(d, GDD_DIR + "GDD-*.md") and d != cur)]
        elif any(c in pat for c in "*?["):
            hit = [d for d in docs if fnmatch.fnmatchcase(d, pat)]
        else:
            hit = [pat] if pat in docs else []
        if not hit and not optional:
            problems.append(f"mapping entry {pat!r} matches no tracked doc")
        out += [h for h in hit if h not in out]
    return out, problems


def pipeline_file(root, files, spec, sections, commit):
    sections = [(h, ps) for h, ps in sections if ps]   # an optional entry a later card writes, not there yet
    sources = [p for _, paths in sections for p in paths]
    title = f"{spec['name']} Pipeline"
    out = [stamp(sources, commit), f"# {title}\n\n",
           "A readable copy for people. Agents load these rules from the repo paths listed below.\n\n",
           "## About this pipeline\n\n",
           f"- **Purpose:** {spec['purpose']}\n- **Owner:** {spec['owner']}\n- **Inputs:** {spec['inputs']}\n",
           f"- **Outputs:** {spec['outputs']}\n- **Gates:** {spec['gates']}\n\n",
           "## Built from\n\n"]
    for head, paths in sections:
        out.append(f"- {head}: " + ", ".join(f"`{p}`" for p in paths) + "\n")
    for head, paths in sections:
        out.append(f"\n## {head}\n")
        for p in paths:
            out.append(f"\n### `{p}`\n\n")
            ext = os.path.splitext(p)[1].lower()
            if ext in SCRIPT_EXT:
                out.append(render_script(root, files, p))
            else:
                out.append(as_markdown(root, p, demote_by=3))
    return "".join(out)


def role_file(root, card, agent, commit):
    sources = [card] + ([agent] if agent else [])
    out = [stamp(sources, commit), read(root, card)]
    if agent:
        out.append(f"\n---\n\n## Claude Code entry point (`{agent}`)\n\n"
                   "This small file only points the agent at the card above. The card wins.\n\n")
        out.append(fence(read(root, agent), "text"))
    return "".join(out)


def build(root, commit=None, files=None):
    """Return (outputs, mapping, problems). outputs: {package relpath: text}; mapping: {package relpath: [sources]}."""
    files = tracked(root) if files is None else sorted(files)
    commit = commit or head_commit(root)
    docs = doc_set(files)
    outputs, mapping, problems = {}, {}, []

    mapping["Project Instructions.md"] = ["AGENTS.md", "CLAUDE.md"]
    outputs["Project Instructions.md"] = (
        stamp(mapping["Project Instructions.md"], commit)
        + "Agents load `AGENTS.md` and `CLAUDE.md` from the repo root; this copy is for reading and sharing.\n\n"
        + read(root, "AGENTS.md") + "\n---\n\n" + read(root, "CLAUDE.md"))

    cards = [d for d in docs if d.startswith(ROLE_DIR) and d.endswith(".md") and "/" not in d[len(ROLE_DIR):]]
    roles = []
    for card in cards:
        stem = os.path.splitext(os.path.basename(card))[0]
        agent = AGENT_DIR + stem + ".md"
        agent = agent if agent in docs else None
        name = f"AI Roles/MegaJam2026-{camel(stem)}_v1.0.md"
        mapping[name] = [card] + ([agent] if agent else [])
        outputs[name] = role_file(root, card, agent, commit)
        roles.append((name, card))
    for d in docs:
        if d.startswith(AGENT_DIR) and d.endswith(".md") and ROLE_DIR + os.path.basename(d) not in docs:
            problems.append(f"{d}: no role card {ROLE_DIR + os.path.basename(d)} to attach it to")

    for spec in PIPELINES:
        sections = []
        for head, pats in spec["sections"]:
            paths, probs = resolve(pats, docs, root)
            problems += [f"Pipelines/{spec['name']} Pipeline.md: {p}" for p in probs]
            sections.append((head, paths))
        name = f"Pipelines/{spec['name']} Pipeline.md"
        mapping[name] = [p for _, ps in sections for p in ps]
        outputs[name] = pipeline_file(root, files, spec, sections, commit)

    for fname, pats in REFERENCE:
        paths, probs = resolve(pats, docs, root)
        problems += [f"Reference/{fname}: {p}" for p in probs]
        name = "Reference/" + fname
        mapping[name] = paths
        body = []
        for p in paths:
            if p == GDD_DIR + "CURRENT":
                continue
            if len(paths) > 1 and not (pats == ["@gdd"]):
                body.append(f"\n---\n\n<!-- source: {p} -->\n\n")
            body.append(read(root, p) if p.endswith(".md") else fence(read(root, p), LANG.get(os.path.splitext(p)[1], "text")))
        outputs[name] = stamp(paths, commit) + "".join(body).lstrip("\n")

    mapping["START_HERE.md"] = ["START_HERE.md"]
    outputs["START_HERE.md"] = read(root, "START_HERE.md")  # verbatim: the beginner path, no stamp
    mapping["README_ProjectStructure.md"] = ["README.md"]
    outputs["README_ProjectStructure.md"] = readme(root, outputs, mapping, roles, commit)

    seen = {}
    for out_name, srcs in mapping.items():
        for s in srcs:
            seen.setdefault(s, []).append(out_name)
    for s, outs in sorted(seen.items()):
        if len(outs) > 1:
            problems.append(f"{s}: lands in {len(outs)} package files ({', '.join(sorted(outs))}); map it to one")
    for d in docs:
        if d not in seen:
            problems.append(f"{d}: orphan doc, in no package file; add it to PIPELINES or REFERENCE in {SELF}")
    return dict(sorted(outputs.items())), mapping, problems


def words(text):
    return len(re.findall(r"\S+", text))


def readme(root, outputs, mapping, roles, commit):
    folders = {}
    for name, text in outputs.items():
        folders.setdefault(os.path.dirname(name) or ".", []).append((os.path.basename(name), words(text)))
    lines = [stamp(mapping["README_ProjectStructure.md"], commit),
             "# MegaPipeline: what's where\n\n",
             "This folder is the jam's AI-agent pipeline, packaged for people to read and share.\n",
             "It is generated from the repo by `tools/export_package.py`. The repo files stay the single source of truth.\n\n",
             "Agents do not read this folder. They keep loading `AGENTS.md` and their role card in `pipeline/roles/` "
             "from the repo paths. Change a rule there, then rebuild this folder.\n\n",
             "## How to use it\n\n",
             "1. Read `Project Instructions.md` first. It is the always-loaded agent instructions.\n",
             "2. Find your role in `AI Roles/`. One file per role card.\n",
             "3. Open your discipline in `Pipelines/`. Each file starts with purpose, owner, inputs, outputs and gates, "
             "then holds every checklist, rule, template, spec and check for that discipline.\n",
             "4. Look up facts in `Reference/`: the GDD snapshot, feature manifest, decisions, coverage map, port log, "
             "the pipeline audit and older GDD drafts. These are copied as-is.\n\n",
             "## Files and word counts\n\n",
             "Word counts include the stamp at the top of each file. This README is not counted.\n\n```text\nMegaPipeline/\n"]
    for folder in sorted(folders):
        entries = folders[folder]
        if folder == ".":
            for fname, wc in entries:
                lines.append(f"  {fname}" + ("" if fname.startswith("README") else f"  ({wc} words)") + "\n")
            continue
        total = sum(wc for _, wc in entries)
        lines.append(f"  {folder}/  ({total} words)\n")
        for fname, wc in entries:
            lines.append(f"    {fname}  ({wc} words)\n")
    lines.append("```\n\n## How files map to the repo\n\n| Package file | Built from |\n|---|---|\n")
    for name in sorted(mapping):
        lines.append(f"| `{name}` | " + ", ".join(f"`{s}`" for s in mapping[name]) + " |\n")
    lines.append(
        "\nEvery doc and script in the repo lands in exactly one package file. Not packaged: `tests/`, the "
        "reviewer eval cases in `evals/reviewer/cases/`, binary files (the key art in `pipeline/art/reference/`), "
        "and repo settings (`.editorconfig`, `.gitattributes`, `.gitignore`).\n\n"
        "## How to regenerate\n\n"
        "- Rebuild after any source change: `python3 tools/export_package.py`.\n"
        "- Check it is current: `python3 tools/export_package.py --check`. `python3 tools/pipeline_check.py` runs "
        "the same check and fails when this folder is stale, hand-edited, or a doc is unmapped.\n"
        "- Make a zip to share: `python3 tools/export_package.py --zip` writes `dist/MegaPipeline-<shortsha>.zip` "
        "(`dist/` is not committed).\n"
        "- A new doc in the repo must be added to the mapping in `tools/export_package.py`, or the check reports it as an orphan.\n"
        "- The stamp names the commit the export ran on. Same sources and commit give byte-identical files.\n\n"
        "Never edit files in this folder by hand. The check fails and the next rebuild overwrites the edit.\n\n"
        "## The repo README (`README.md`)\n\n")
    lines.append(demote(read(root, "README.md"), 2))
    return "".join(lines)


# ---- write, check, zip ------------------------------------------------------------------------
def normalize(text):
    return STAMP_RE.sub(r"\1<commit>\3", text)


def existing(out_dir):
    found = {}
    for d, _, names in os.walk(out_dir):
        for n in names:
            full = os.path.join(d, n)
            found[os.path.relpath(full, out_dir).replace(os.sep, "/")] = full
    return found


def write(outputs, out_dir, keep_shipped=False):
    for rel, full in existing(out_dir).items() if os.path.isdir(out_dir) else []:
        if rel not in outputs and not (keep_shipped and shipped(rel)):
            os.remove(full)
    for rel, text in outputs.items():
        full = os.path.join(out_dir, rel)
        os.makedirs(os.path.dirname(full), exist_ok=True)
        data = text.encode("utf-8")
        try:
            with open(full, "rb") as f:
                if f.read() == data:
                    continue
        except OSError:
            pass
        with open(full, "wb") as f:
            f.write(data)
    for d, subdirs, names in sorted(os.walk(out_dir), reverse=True):
        if d != out_dir and not os.listdir(d):
            os.rmdir(d)


def check(root, out_dir=None, commit=None, files=None):
    """Problems as (where, why). Empty = MegaPipeline/ matches a fresh build."""
    out_dir = out_dir or os.path.join(root, PKG)
    outputs, _, mapping_problems = build(root, commit, files)
    problems = [(SELF, p) for p in mapping_problems]
    have = existing(out_dir) if os.path.isdir(out_dir) else {}
    if installed(root, out_dir):
        have = {rel: full for rel, full in have.items() if not shipped(rel)}
    fix = "run `python3 tools/export_package.py`"
    for rel, text in outputs.items():
        where = f"{PKG}/{rel}"
        if rel not in have:
            problems.append((where, f"missing; {fix}"))
            continue
        with open(have[rel], "rb") as f:
            try:
                cur = f.read().decode("utf-8")
            except UnicodeDecodeError:
                cur = None
        if cur is None or normalize(cur) != normalize(text):
            problems.append((where, f"stale or hand-edited (differs from its sources); {fix}"))
    for rel in sorted(set(have) - set(outputs)):
        problems.append((f"{PKG}/{rel}", f"not made by the exporter; delete it or {fix}"))
    return problems


def make_zip(root, outputs, commit):
    path = os.path.join(root, "dist", f"{PKG}-{commit}.zip")
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with zipfile.ZipFile(path, "w", zipfile.ZIP_DEFLATED) as z:
        for rel in sorted(outputs):
            info = zipfile.ZipInfo(f"{PKG}/{rel}", date_time=(1980, 1, 1, 0, 0, 0))
            info.external_attr = 0o644 << 16
            info.compress_type = zipfile.ZIP_DEFLATED
            z.writestr(info, outputs[rel].encode("utf-8"))
    return path


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--root", default=os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    ap.add_argument("--out", help="output folder (default <root>/MegaPipeline)")
    mode = ap.add_mutually_exclusive_group()
    mode.add_argument("--check", action="store_true")
    mode.add_argument("--zip", action="store_true")
    a = ap.parse_args(argv)
    out_dir = a.out or os.path.join(a.root, PKG)
    if a.check:
        problems = check(a.root, out_dir)
        for where, why in problems:
            print(f"[package] {where}: {why}")
        print(f"export_package --check: {len(problems)} problem(s)")
        return 1 if problems else 0
    outputs, _, problems = build(a.root)
    for p in problems:
        print(f"[package] {p}")
    if problems:
        print(f"export_package: {len(problems)} problem(s); nothing written")
        return 1
    if a.zip:
        print("export_package: wrote " + os.path.relpath(make_zip(a.root, outputs, head_commit(a.root)), a.root))
        return 0
    write(outputs, out_dir, keep_shipped=installed(a.root, out_dir))
    print(f"export_package: wrote {len(outputs)} file(s) to {os.path.relpath(out_dir, a.root)}/")
    return 0


if __name__ == "__main__":
    sys.exit(main())
