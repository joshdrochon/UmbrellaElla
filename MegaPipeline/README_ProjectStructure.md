> Generated from `README.md` at `a11903f` — edit the sources, not this file.
> Rebuild: `python3 tools/export_package.py`. Check: `python3 tools/export_package.py --check`.

# MegaPipeline: what's where

This folder is the jam's AI-agent pipeline, packaged for people to read and share.
It is generated from the repo by `tools/export_package.py`. The repo files stay the single source of truth.

Agents do not read this folder. They keep loading `AGENTS.md` and their role card in `pipeline/roles/` from the repo paths. Change a rule there, then rebuild this folder.

## How to use it

1. Read `Project Instructions.md` first. It is the always-loaded agent instructions.
2. Find your role in `AI Roles/`. One file per role card.
3. Open your discipline in `Pipelines/`. Each file starts with purpose, owner, inputs, outputs and gates, then holds every checklist, rule, template, spec and check for that discipline.
4. Look up facts in `Reference/`: the GDD snapshot, feature manifest, decisions, coverage map, port log, the pipeline audit and older GDD drafts. These are copied as-is.

## Files and word counts

Word counts include the stamp at the top of each file. This README is not counted.

```text
MegaPipeline/
  Project Instructions.md  (1882 words)
  START_HERE.md  (2455 words)
  AI Roles/  (15981 words)
    MegaJam2026-AgentOps_v1.0.md  (1117 words)
    MegaJam2026-ArtDirector_v1.0.md  (1207 words)
    MegaJam2026-AssetSpecialist_v1.0.md  (1207 words)
    MegaJam2026-Audio_v1.0.md  (1208 words)
    MegaJam2026-DevLead_v1.0.md  (1206 words)
    MegaJam2026-EncounterDesigner_v1.0.md  (1194 words)
    MegaJam2026-GameDesigner_v1.0.md  (929 words)
    MegaJam2026-GameplayDev_v1.0.md  (1080 words)
    MegaJam2026-Integrator_v1.0.md  (650 words)
    MegaJam2026-LevelDesigner_v1.0.md  (988 words)
    MegaJam2026-Producer_v1.0.md  (1200 words)
    MegaJam2026-QABuild_v1.0.md  (1208 words)
    MegaJam2026-Story_v1.0.md  (933 words)
    MegaJam2026-TechnicalDirector_v1.0.md  (1108 words)
    MegaJam2026-UIUX_v1.0.md  (746 words)
  Pipelines/  (157033 words)
    Production Pipeline.md  (24191 words)
    Design Pipeline.md  (8502 words)
    Development Pipeline.md  (14792 words)
    Technical Development Pipeline.md  (7260 words)
    QA Pipeline.md  (7983 words)
    Art Pipeline.md  (27675 words)
    Audio Pipeline.md  (16648 words)
    Story Pipeline.md  (4565 words)
    Level Pipeline.md  (9664 words)
    UI UX Pipeline.md  (5511 words)
    Game Feel Pipeline.md  (7086 words)
    Agent Ops Pipeline.md  (16944 words)
    Submission Pipeline.md  (6212 words)
  Reference/  (130672 words)
    GDD Snapshot.md  (32487 words)
    Official Rules.md  (7887 words)
    Feature Manifest.md  (16217 words)
    Decisions.md  (10518 words)
    Coverage Map.md  (41298 words)
    Port Log.md  (1267 words)
    Pipeline Audit.md  (4936 words)
    GDD Archive.md  (16062 words)
```

## How files map to the repo

| Package file | Built from |
|---|---|
| `AI Roles/MegaJam2026-AgentOps_v1.0.md` | `pipeline/roles/agent-ops.md` |
| `AI Roles/MegaJam2026-ArtDirector_v1.0.md` | `pipeline/roles/art-director.md`, `.claude/agents/art-director.md` |
| `AI Roles/MegaJam2026-AssetSpecialist_v1.0.md` | `pipeline/roles/asset-specialist.md`, `.claude/agents/asset-specialist.md` |
| `AI Roles/MegaJam2026-Audio_v1.0.md` | `pipeline/roles/audio.md`, `.claude/agents/audio.md` |
| `AI Roles/MegaJam2026-DevLead_v1.0.md` | `pipeline/roles/dev-lead.md`, `.claude/agents/dev-lead.md` |
| `AI Roles/MegaJam2026-EncounterDesigner_v1.0.md` | `pipeline/roles/encounter-designer.md`, `.claude/agents/encounter-designer.md` |
| `AI Roles/MegaJam2026-GameDesigner_v1.0.md` | `pipeline/roles/game-designer.md`, `.claude/agents/game-designer.md` |
| `AI Roles/MegaJam2026-GameplayDev_v1.0.md` | `pipeline/roles/gameplay-dev.md`, `.claude/agents/gameplay-dev.md` |
| `AI Roles/MegaJam2026-Integrator_v1.0.md` | `pipeline/roles/integrator.md`, `.claude/agents/integrator.md` |
| `AI Roles/MegaJam2026-LevelDesigner_v1.0.md` | `pipeline/roles/level-designer.md`, `.claude/agents/level-designer.md` |
| `AI Roles/MegaJam2026-Producer_v1.0.md` | `pipeline/roles/producer.md`, `.claude/agents/producer.md` |
| `AI Roles/MegaJam2026-QABuild_v1.0.md` | `pipeline/roles/qa-build.md`, `.claude/agents/qa-build.md` |
| `AI Roles/MegaJam2026-Story_v1.0.md` | `pipeline/roles/story.md`, `.claude/agents/story.md` |
| `AI Roles/MegaJam2026-TechnicalDirector_v1.0.md` | `pipeline/roles/technical-director.md`, `.claude/agents/technical-director.md` |
| `AI Roles/MegaJam2026-UIUX_v1.0.md` | `pipeline/roles/ui-ux.md` |
| `Pipelines/Agent Ops Pipeline.md` | `pipeline/agent-ops/README.md`, `pipeline/agent-ops/gates.json`, `pipeline/agent-ops/settings.json`, `pipeline/agent-ops/agent-tools.json`, `pipeline/agent-ops/components.csv`, `pipeline/agent-ops/model-tiers.md`, `pipeline/agent-ops/model-prices.json`, `pipeline/agent-ops/asset-tools.json`, `pipeline/agent-ops/editor-mcp.md`, `pipeline/agent-ops/mcp.template.json`, `tools/editor_mcp.py`, `pipeline/agent-ops/mcp.tools.template.json`, `tools/mcp_config.py`, `tools/kickoff.sh`, `tools/kickoff.ps1`, `tools/kickoff.py`, `tools/connections.py`, `tools/keys.py`, `tools/practice.py`, `tools/git_gate.py`, `tools/assetgen.py`, `prompts/README.md`, `evals/README.md`, `docs/references.md`, `docs/repo-map.md`, `tools/repo_map.py`, `pipeline/agent-ops/hook.py`, `pipeline/agent-ops/journal_hook.py`, `tools/journal.py`, `tools/install_git_hooks.py`, `tools/agent.sh`, `tools/agent.ps1`, `tools/start_session.sh`, `tools/start_session.ps1`, `tools/start_session.py`, `tools/spend_log.py`, `tools/prompt_log.py`, `tools/secrets_check.py` |
| `Pipelines/Art Pipeline.md` | `pipeline/art/art-bible.md`, `pipeline/art/style.json`, `pipeline/art/references.json`, `pipeline/art/reference/discord/index.json`, `pipeline/art/reference/Test_Assets/SpriteLayout.json`, `pipeline/art/reference/Test_Assets/Asset Notes.md`, `pipeline/art/blender/characters.json`, `pipeline/art/blender/plan.py`, `pipeline/art/blender/stand_ins.py`, `pipeline/art/blender/render_sprite.py`, `pipeline/art/import-rules.md`, `pipeline/art/provenance.csv`, `pipeline/checklists/animation-review.md`, `pipeline/templates/asset-brief.md`, `evals/art-judge/README.md`, `evals/art-judge/blind_pairwise.md`, `evals/art-judge/agreement.csv`, `evals/art-judge/critic-calibration.json`, `tools/art_judge_prompt.md`, `tools/art_check.py`, `tools/screen_check.py`, `tools/art_judge.py`, `tools/art_ref_check.py`, `tools/art_loop.py`, `tools/sprite_check.py`, `tools/make_art_calibration.py`, `tools/png.py` |
| `Pipelines/Audio Pipeline.md` | `pipeline/audio/style-target.md`, `pipeline/audio/style.json`, `pipeline/audio/sound-events.json`, `pipeline/audio/audio-rules.md`, `pipeline/audio/audio-rules.json`, `pipeline/audio/sound-list.csv`, `tools/audio_loop.py`, `tools/audio_critic_prompt.md`, `tools/audio_check.py`, `tools/audio_style_check.py`, `tools/audio_import.py`, `tools/ue/audio_dump.py`, `pipeline/audio/ue/audio_dump.py` |
| `Pipelines/Design Pipeline.md` | `docs/gdd/README.md`, `docs/gdd/questions-1.3.md`, `docs/gdd/questions-B1.0.md`, `docs/game-spec.md`, `docs/balance.md`, `pipeline/checklists/design-review.md`, `pipeline/checklists/tuning.md`, `tools/manifest_check.py`, `tools/gdd_impact.py`, `tools/gdd_select.py`, `tools/bake_preset.py`, `tools/tuning.py`, `tools/progression_model.py` |
| `Pipelines/Development Pipeline.md` | `pipeline/unreal-rules.md`, `pipeline/unreal/cpp-rules.md`, `pipeline/unreal/gameplay-code.md`, `docs/unreal-sources.md`, `pipeline/checklists/file-hygiene.md`, `.github/PULL_REQUEST_TEMPLATE.md`, `evals/reviewer/results.md`, `tools/run_reviewer_eval.py`, `tools/score_review.py`, `tools/check_pr.py` |
| `Pipelines/Game Feel Pipeline.md` | `docs/feel-spec.md`, `pipeline/feel/feel.json`, `pipeline/feel/hitboxes.json`, `pipeline/feel/ab-log.csv`, `pipeline/feel/arena-log.csv`, `pipeline/feel/latency-log.csv`, `tools/feel_check.py`, `tools/hitbox_check.py` |
| `Pipelines/Level Pipeline.md` | `pipeline/level/encounter.md`, `pipeline/level/encounter.json`, `pipeline/checklists/level-sections.md`, `pipeline/level/reference/owl-fight-ricky.md`, `pipeline/level/fixtures/card_ok.md`, `pipeline/level/fixtures/logger_output.csv`, `tools/encounter_check.py`, `tools/encounter_spec.py` |
| `Pipelines/Production Pipeline.md` | `docs/jam-brief.md`, `docs/jam-rules.md`, `pipeline/day0-cards.md`, `pipeline/human-checkpoints.md`, `pipeline/how-to-run-the-jam.md`, `pipeline/what-the-pipeline-controls.md`, `pipeline/checklists/card-ready.md`, `pipeline/templates/task-card.md`, `pipeline/templates/spike-card.md`, `pipeline/templates/gate-record.md`, `pipeline/templates/tracker-table.md`, `pipeline/templates/clock-workflow.yml`, `.github/ISSUE_TEMPLATE/task.yml`, `.github/workflows/blocked-report.yml`, `.github/workflows/main-red.yml`, `tools/check_card.py`, `tools/lane_guard.py`, `tools/status_board.py` |
| `Pipelines/QA Pipeline.md` | `pipeline/qa/test-map.md`, `pipeline/qa/playtests.md`, `pipeline/qa/presets.json`, `pipeline/qa/no-player-maps.txt`, `pipeline/templates/test-note.md`, `tools/ue/daily-checklist.md`, `tools/ue/smoke-allow.txt`, `tools/check_automation_report.py`, `tools/ue/test.ps1`, `tools/ue/test.sh`, `tools/ue/daily.ps1`, `tools/ue/daily.sh`, `tools/ue/package.ps1`, `tools/ue/package.sh`, `tools/ue/smoke.ps1`, `tools/ue/smoke.sh` |
| `Pipelines/Story Pipeline.md` | `pipeline/story/story-bible.md`, `pipeline/story/lines.csv`, `pipeline/story/story.json`, `tools/story_critic_prompt.md`, `evals/story-critic/README.md`, `evals/story-critic/calibration.csv`, `tools/story_check.py` |
| `Pipelines/Submission Pipeline.md` | `pipeline/checklists/submission.md`, `docs/pre-jam-declaration.md`, `pipeline/submission/LICENSE.txt`, `pipeline/submission/README.txt`, `pipeline/submission/credits.md`, `pipeline/submission/devlog.md`, `pipeline/submission/footage.md`, `pipeline/submission/itch-page.md`, `pipeline/submission/video-plan.md`, `tools/submission_check.py` |
| `Pipelines/Technical Development Pipeline.md` | `pipeline/unreal/commands-and-packaging.md`, `.github/workflows/pipeline-checks.yml`, `.github/CODEOWNERS.example`, `tools/pipeline_check.py`, `tools/module_check.py`, `tools/ue_run.py`, `tools/ue/common.ps1`, `tools/ue/common.sh`, `tools/ue/build.ps1`, `tools/ue/build.sh`, `tools/ue/validate.ps1`, `tools/ue/validate.sh`, `tools/export_package.py` |
| `Pipelines/UI UX Pipeline.md` | `pipeline/ui/accessibility.md`, `pipeline/ui/menus.md`, `pipeline/ui/signals.json`, `tools/ui_check.py` |
| `Project Instructions.md` | `AGENTS.md`, `CLAUDE.md` |
| `README_ProjectStructure.md` | `README.md` |
| `Reference/Coverage Map.md` | `docs/coverage-map.md` |
| `Reference/Decisions.md` | `docs/decisions.md` |
| `Reference/Feature Manifest.md` | `docs/feature-manifest.json` |
| `Reference/GDD Archive.md` | `docs/gdd/GDD-1.3.md`, `docs/gdd/GDD-B1.0.md`, `docs/gdd/archive/gdd-umbrella-ella-draft1.0.md` |
| `Reference/GDD Snapshot.md` | `docs/gdd/GDD-SH1.0.md`, `docs/gdd/CURRENT` |
| `Reference/Official Rules.md` | `docs/rules/official-rules.md` |
| `Reference/Pipeline Audit.md` | `docs/audit.md` |
| `Reference/Port Log.md` | `docs/port-log.md` |
| `START_HERE.md` | `START_HERE.md` |

Every doc and script in the repo lands in exactly one package file. Not packaged: `tests/`, the reviewer eval cases in `evals/reviewer/cases/`, binary files (the key art in `pipeline/art/reference/`), and repo settings (`.editorconfig`, `.gitattributes`, `.gitignore`).

## How to regenerate

- Rebuild after any source change: `python3 tools/export_package.py`.
- Check it is current: `python3 tools/export_package.py --check`. `python3 tools/pipeline_check.py` runs the same check and fails when this folder is stale, hand-edited, or a doc is unmapped.
- Make a zip to share: `python3 tools/export_package.py --zip` writes `dist/MegaPipeline-<shortsha>.zip` (`dist/` is not committed).
- A new doc in the repo must be added to the mapping in `tools/export_package.py`, or the check reports it as an orphan.
- The stamp names the commit the export ran on. Same sources and commit give byte-identical files.

Never edit files in this folder by hand. The check fails and the next rebuild overwrites the edit.

## The repo README (`README.md`)

### GameJam2026

**New here, or told to merge a PR and run the pipeline? Read [`START_HERE.md`](START_HERE.md) first.** It has
every step for Windows and Mac, from setup to your first run.

Umbrella Ella (working title): a 2D Unreal Engine 5.8.4 action game for the jam.

- **Agents start at** [`AGENTS.md`](AGENTS.md).
- Game, MVP and people: [`docs/jam-brief.md`](docs/jam-brief.md)
- Open decisions: [`docs/decisions.md`](docs/decisions.md)
- Pipeline audit (issue #11): [`docs/audit.md`](docs/audit.md)
- Sources: [`docs/references.md`](docs/references.md)

Checks: `python3 tools/pipeline_check.py` and `python3 -m unittest discover -s tests` (no installs needed).

#### Install and run (Claude Code or Codex, same steps)
1. **Type `tools/kickoff.sh`** (Windows: `tools\kickoff.ps1`) with no options. It prints the pipeline version, runs the
   connection check (`CONNECTED`, `NOT CONNECTED <name> -> <fix>` or `SKIPPED`), then starts with the agent CLI it finds.
   With both Claude Code and Codex installed it asks which one. Every failure is one line that says what to type next.
2. Fix each `NOT CONNECTED` line: Python 3.9+, git, Git LFS, `gh auth login`, and one agent CLI logged in (Claude Code:
   `claude auth login`; Codex: `codex login`). Unreal 5.8.4 (`UE_ROOT`) on machines that build.
3. One-time human setup: Blender (blender.org; all art is rendered in it, `pipeline/art/blender/`) on machines that
   make art, and the audio keys `ELEVENLABS_API_KEY`, `STABILITY_API_KEY` in the environment or the OS keychain (`python3 tools/keys.py status` shows how; never in a file). The editor and art MCP servers stay off
   until the kickoff record turns them on (`pipeline/agent-ops/editor-mcp.md`).
4. Options: `--agent codex|claude`, `--check` (version and check only), `--practice` once in a test repo,
   `--prompt-file F` to record your own prompt for A/B runs (`python3 tools/journal.py compare <a> <b>`).

Codex users get the same guardrails as Claude Code users: kickoff installs git pre-commit and pre-push hooks
(`tools/install_git_hooks.py`, `tools/git_gate.py`) that refuse any agent commit to a gate path, and CI fails a PR
that changes one without the human's `GATE EDIT:` line (`tools/check_pr.py`). The Claude hook stays as an extra layer.
How to run the jam day to day: `pipeline/how-to-run-the-jam.md`. What the tools check and what people decide:
`pipeline/what-the-pipeline-controls.md`.

