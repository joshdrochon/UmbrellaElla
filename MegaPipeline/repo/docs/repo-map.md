# Repo map

Every folder an agent may touch: what it holds, who writes it. Your card's File lane still decides what you change.
Gate path (`pipeline/agent-ops/gates.json`): never commit it; write `$JAM_OUTBOX/gate.patch`, kickoff applies it through the tool checks (`tools/git_gate.py apply --auto`).
A tracked folder not listed here is team files: read-only unless your card links it (`tools/repo_map.py` lists them).
`tools/pipeline_check.py` fails when a pipeline folder is missing here.

## Pipeline folders (the installer ships these)
- `.claude/`: Claude Code settings, a copy of `pipeline/agent-ops/settings.json` (`secrets_check.py --install`). Gate path.
- `.claude/agents/`: one agent file per role card. Gate path.
- `.github/`: PR template, CODEOWNERS example. Gate path.
- `.github/ISSUE_TEMPLATE/`: the Task card form. Gate path.
- `.github/workflows/`: CI (pipeline checks, main-red revert, blocked report). Gate path.
- `docs/`: brief, decisions, game spec, balance, feel spec, feature manifest, audit. Producer: `decisions.md` rows (any role: its own rows); Game Designer: `balance.md`; the rest are shared team docs (AGENTS.md section 7).
- `docs/gdd/`: GDD snapshots, `CURRENT` names the live one. Read-only; Game Designer adds questions to `questions-*.md`.
- `docs/rules/`: the Official Rules (PDF and text). Read-only.
- `evals/`: agent evals. `README.md` is a gate path.
- `evals/art-judge/`: art-judge calibration set. Gate path; Art Director.
- `evals/reviewer/`: planted-bug cases and results for the Dev Lead reviewer eval. Gate path (`runs/` is local).
- `evals/story-critic/`: story critic calibration. Gate path.
- `pipeline/`: process docs. Producer: `day0-cards.md`; Technical Director: `unreal-rules.md`.
- `pipeline/agent-ops/`: gates, settings, hooks, model tiers. Gate path; Agent Ops.
- `pipeline/art/`: art bible, style, references (`reference/`), import rules, provenance. Art Director: `art-bible.md`; `style.json` is a gate path; `provenance.csv`: your own rows.
- `pipeline/audio/`: sound list, style target, audio rules. Audio; `style.json` and `sound-events.json` are gate paths.
- `pipeline/checklists/`: checklists. Read when your card links them; a change is one card for the integration owner.
- `pipeline/feel/`: feel numbers, colliders, A/B and latency logs. Game Designer: `feel.json`; Gameplay Dev: `hitboxes.json`.
- `pipeline/level/`: encounter data, references, check fixtures. Level Designer (top-level rows), Encounter Designer (`encounter_presets`, `reference/`); `encounter.md` tables come from `--write-md`.
- `pipeline/qa/`: test map, playtests, presets. QA and Build: `playtests.md`; `test-map.md`: your own rows.
- `pipeline/roles/`: the role cards. Gate path.
- `pipeline/story/`: story bible, player-facing lines. Story; `story.json` is a gate path.
- `pipeline/submission/`: devlog, footage log, video plan, page, credits. Producer: `devlog.md`; Asset Specialist: `footage.md`, `video-plan.md`.
- `pipeline/templates/`: card, brief and record templates. Read when your card links them; a change is one card for the integration owner.
- `pipeline/ui/`: menus, accessibility, UI signals. UI and UX.
- `pipeline/unreal/`: C++ rules, commands and packaging. Dev Lead (C++ rules); Integrator: `editor_scripts/`.
- `prompts/`: prompt log readme and daily exports (`log/`). Agent Ops.
- `tests/`: pipeline unit tests. Gate path.
- `tests/fixtures/`: test data. Gate path.
- `tools/`: every check and script. Gate path.
- `tools/ue/`: Unreal build, test, package and smoke scripts. Gate path; Technical Director.

## Game folders (appear from Nov 12)
- `Source/`: game C++. Gameplay Dev (the card's File lane); Technical Director: modules, `*.Build.cs`, core headers.
- `Content/`: Unreal assets (Git LFS; never edit with file tools, lock first). Integrator: maps, thin Blueprints; Asset Specialist: art; Audio: sounds; Level Designer: owl data; UI and UX, Story: `ST_UI.csv`.
- `Config/`: engine and game ini. Technical Director; Integrator: only `+MapsToCook` lines.
- `Samples/Workbench/`: the pre-jam workbench sample (synthetic objects only). Technical Director (cards 0.25, 0.26).
- `UmbrellaElla.uproject`: the project file. Technical Director.
- `Plugins/`: project plugins. Technical Director only (AGENTS.md section 7).
- `Art/`: source art (Git LFS). Asset Specialist.
- `Audio/`: source WAVs (Git LFS). Audio.
- `docs/asset-changes/`: asset-change sidecars. Integrator.
- `scratch/`: throwaway files on never-merged branches (cards 0.9, 0.18).

## Team and local folders
- `Assets/`: team art. Read-only; the art tools join it as look-only references.
- `MegaPipeline/`: installer bundle and readable export. Never edit (`tools/export_package.py` builds it).
- `Saved/`, `.pipeline/`: local logs, backups, journal. Never commit.
