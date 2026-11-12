> Generated from `AGENTS.md`, `CLAUDE.md` at `b201a66` — edit the sources, not this file.
> Rebuild: `python3 tools/export_package.py`. Check: `python3 tools/export_package.py --check`.

Agents load `AGENTS.md` and `CLAUDE.md` from the repo root; this copy is for reading and sharing.

# AGENTS.md — Umbrella Ella game jam

Build mode: `tools/kickoff.sh` (or `.ps1`) follows `docs/build/MODE`. `direct`: no cards, issues or PRs (section 4); use `HANDOFF.md`.

Every agent loads this first (budget: `tools/pipeline_check.py`).

## 1. Read order (nothing else unless your task card links it)
1. This file.
2. `docs/repo-map.md`: each folder and who writes it; one it omits is team files, read-only.
3. `docs/jam-brief.md`: the game, MVP, people, hard limits. Design: `docs/feature-manifest.json`, the GDD snapshot `docs/gdd/CURRENT` names, `docs/game-spec.md`. Never `docs/gdd/archive/`. New GDD revision: `docs/gdd/README.md`.
4. Your role card in `pipeline/roles/`. Start your first message with `ROLE: <name>`. Launched without `JAM_ROLE=<name>`, every write is blocked.
5. Your task card (the GitHub issue).
6. Unreal project: `pipeline/unreal-rules.md`. Anything visible: `pipeline/art/art-bible.md`.
   An open row in `docs/decisions.md` your card touches: that row; build its default.
7. `pipeline/checklists/` and `pipeline/templates/`: only when your card or role card links them.

First output after `ROLE:`, before any edit, pasted as run:
`git status -sb`, `git rev-parse origin/main`, `git lfs locks` (yours), your engine version,
and `CAN RUN: build=y/n tests=y/n package=y/n editor=y/n`. Card checks you cannot run go under "Not run" with who runs them.
A human launches it: `tools/kickoff.sh` (section 12) or `tools/start_session.sh <role> <card>` (`.ps1` on Windows). Before work: `python3 tools/journal.py resume --card <id>`,
this machine's record; GitHub stays the shared truth. Re-read the card and PR comments; re-run checks a handoff claimed.

Never load the inherited pipeline (`docs/references.md` R3).

## 2. Which source wins
0. The Official Rules (`docs/rules/official-rules.md`; team reading `docs/jam-rules.md`) beat everything.
1. `docs/jam-brief.md` and DECIDED rows in `docs/decisions.md`.
2. The current GDD snapshot (design source); `docs/feature-manifest.json` mirrors it (`manifest_check.py`). Then `docs/game-spec.md`.
3. Key art + `pipeline/art/art-bible.md` for how things look.
4. Everything else.

If two sources at the same level disagree, or a rule is missing, do not choose. Add a row to `docs/decisions.md`,
build its default, say so in the PR.

## 3. Roles
| Role | Use it for | Card |
|---|---|---|
| Producer | Cards, cadence, cuts, decisions | `pipeline/roles/producer.md` |
| Dev Lead | Code review | `pipeline/roles/dev-lead.md` |
| Gameplay Dev | Gameplay C++ | `pipeline/roles/gameplay-dev.md` |
| Technical Director | Modules, build, plugins, collision, input | `pipeline/roles/technical-director.md` |
| Integrator | Map, thin Blueprints, GameMode, UI layouts, eval cameras | `pipeline/roles/integrator.md` |
| Art Director | Art bible, art review of captures | `pipeline/roles/art-director.md` |
| Asset Specialist | Sprites and flipbooks | `pipeline/roles/asset-specialist.md` |
| Audio | Sound list, sound effects, music, mix | `pipeline/roles/audio.md` |
| QA and Build | Daily package, smoke, bugs, playtests | `pipeline/roles/qa-build.md` |
| Game Designer | Balance, tuning, movement envelope | `pipeline/roles/game-designer.md` |
| Level Designer | Arena numbers, owl patterns, pacing | `pipeline/roles/level-designer.md` |
| Encounter Designer | Boss fight, critic loop | `pipeline/roles/encounter-designer.md` |
| UI and UX | Menus, settings, accessibility | `pipeline/roles/ui-ux.md` |
| Story | Story bible, all player-facing text | `pipeline/roles/story.md` |
| Agent Ops | Agent settings, hooks, prompt log (D-new-agent-ops) | `pipeline/roles/agent-ops.md` |

File hygiene is a checklist (`pipeline/checklists/file-hygiene.md`), not an agent.
One session = one role; a second role in it is not an independent review.
A change across several lanes (a rename, a shared rule) is one card for the integration owner; `pipeline_check.py` fails on a cited decision, card, path or owner no doc backs.
Ties: look, feel, theme → Creative director (D34); scope → Scope decision-maker.

## 4. How work flows
1. All work is a task card (GitHub "Task card" form; fields: `pipeline/templates/task-card.md`). Day 0 starts with `pipeline/day0-cards.md`.
   No card, no work. A card with an empty field is not ready. `GDD revision:` and `Features:` name what it builds; an
   unauthorized feature gets only a `Hook only` card. Non-CONFIRMED features are built behind their flag (`pipeline/unreal-rules.md`).
2. One card = one branch `ue-<id>-<short-name>` = one PR = one fresh agent session (no other card's context). Never commit to `main`.
3. Stay inside the card's File lane. Lock binary files (`git lfs lock`) before you change them.
4. Prove it (section 5), open the PR with the template, ask the card's reviewer role.
5. The reviewer is another role in a fresh session. kickoff, never an agent, merges once CI, review and `check_pr.py` pass.
6. Every agent comment and review on GitHub starts `ROLE: <role> | session <date-time>`. Two reviewer roles give separate verdicts; after a fix only the failed one re-reviews, unless the diff touched the other's area.
7. Work and handoffs live only on GitHub, linked (pushed branch, PR, issue comment), never in chat.
   Agents cannot message each other. Could not post: say "prepared, not posted", paste the text.
8. At a human checkpoint (`pipeline/human-checkpoints.md`), label the issue `needs-human` and comment
   `NEEDS HUMAN: <who/role> <what> <link> <UTC time>`; then stop that step. Other in-lane work needs no approval.
   No human answer in 2 h: a director session decides by that page's grace default, never on its human-only kinds.

States: `todo → doing → review → done`, plus `blocked`, `needs-human`, as issue labels (closed = done; closed with `cut` or `superseded` = not done).

## 5. Evidence: measure, never claim
- "Done" needs pasted output from a command someone else can re-run: build log tail,
  `tools/check_automation_report.py` output, package log, `SMOKE_OK` line, `tools/art_check.py` JSON.
- Screenshots show looks, not function. PIE is not a build.
- Say what you did not run and why; never report an unfinished command.
- Every new engine API exists in the 5.8.4 headers; cite the header.
- Evidence starts with `commit=<sha> engine=5.8.4 config=Development host=<win|mac> run=<PIE|Standalone|packaged>`. Older than the PR head = stale (missing).
- Correct a wrong posted claim in a new comment linking it; never edit silently.

## 6. Stop rules
- Same failure twice: stop, set the card `blocked`, write the exact error, what you tried, who should look next.
  Name one cause: `env` (UE_ROOT, SDK) / `code` / `asset or cook` / `config` / `platform` (Win vs Mac) / `card unclear` / `requirements conflict` (→ decision row) / `card too big` (→ split).
- The card needs a file outside its Outputs, a second component, or behavior not in Done-when: stop, post a split proposal.
- Session end or handoff: `journal.py checkpoint --card <id> --note "..." --next "..."`, then post `journal.py export --card <id>` on the card. No PR in review: also push the branch and post `git log origin/<branch> -1`, checks not run, LFS locks held, next role.
- `main` red: within 30 min the integration owner reverts the breaking squash commit (`main-red.yml` opens the revert PR); the card returns to `doing`. Other cards keep working; they wait only to merge.
- A blocked card blocks only cards that list it in After, directly or not (`check_card.py --blocked-by <id>`).
- Over Budget (counted while `doing`): stop and report. 60 min over (`check_card.py --overrun`): the Producer cuts or splits a feature card; a non-P0 bug is hidden and refiled as P2 (D-new-overrun).
- Builder/critic loops: no round cap; needs-human only after 3 flat rounds: same gap, no better score (D-new-no-round-cap).
- A save, lock or merge touching a file outside your lane: stop and ask. Your own rows in `docs/decisions.md`, `pipeline/qa/test-map.md` and `pipeline/art/provenance.csv` are in every lane.

## 7. Never
- Never approve, accept or merge your own work.
- Never force-push or rewrite shared history.
- Never edit `.uasset`/`.umap` with file tools or git, or "Save All" in the editor. Never commit a gate path or use `--no-verify`: write `$JAM_OUTBOX/gate.patch` (`check_pr.py` and the merge gate catch it; no hook).
- Never commit `Binaries/`, `Intermediate/`, `Saved/`, `DerivedDataCache/`, generated files or secrets.
- Never resolve a `docs/decisions.md` row (grace and Day-0 defaults excepted). Never edit a GDD snapshot, change a manifest status, or edit other shared team docs.
- Never weaken a check or threshold without a measurement that proves it wrong, written in the commit message.
- Never add a plugin, module or engine setting outside the Technical Director's cards.
- Never use art or audio without a provenance row and a known licence.
- Never change the engine version or `EngineAssociation`, or accept an editor "convert project" prompt.
- Never change GitHub settings, branch protection, secrets or LFS config (CODEOWNERS: a gate patch).
- Never upload (`butler push`) or submit the entry: a human entrant does (Official Rules §17).
- Never add `#pragma warning(disable…)`, `PRAGMA_DISABLE_*_WARNINGS` or a Build.cs warning-level change without a decision row cited on that line.

## 8. Checks that run
| Check | Command | Where |
|---|---|---|
| Repo guardrails, budgets, cross-doc consistency | `python3 tools/pipeline_check.py` (`--release` for G4: `_PH` fails) | Local + CI |
| Changed files' tests (5 min target) | `python3 tools/affected_tests.py --run` | Card sessions (reviewer: if in doubt) |
| Full unit suite | `python3 -m unittest discover -s tests` | Pipeline repos' CI; before gate packages |
| PR body: task, evidence, risks, GDD impact | `python3 tools/check_pr.py` | CI |
| Card ready; daily plan (Producer) | `python3 tools/check_card.py <card>`; `--clock`, `--people`, `--hours --day N`, `--lanes`, `--status` | Local + CI; each day start |
| Module boundaries, C++ standard, feature flags (TD) | `python3 tools/module_check.py` (exit 2 = no `Source/` yet) | Local + CI |
| Manifest vs GDD; what a revision touches | `python3 tools/manifest_check.py`; `tools/gdd_impact.py <old> <new>` | Local + CI; PR |
| Sprite sheets; art aligns to its collider | `python3 tools/sprite_check.py --scan Art`; `tools/hitbox_check.py check` | Local + CI |
| Compile; automation tests | `tools/ue/build.sh`, `test.sh` (Windows `.ps1`; filter: `affected_tests.py`) | Local |
| Package + smoke | `tools\ue\package.ps1` then `tools\ue\smoke.ps1 -Exe <game.exe>` (Mac: `package.sh`, `smoke.sh`) | Windows packaging machine |
| Art numbers | `python3 tools/art_check.py <capture.png>` | Local |
| Owl encounter data | `python3 tools/encounter_check.py` | Local + CI |
| Audio data | `python3 tools/audio_check.py --list`, `--docs`, `--scan` | Local + CI |
| Reviewer still catches planted bugs | `python3 tools/run_reviewer_eval.py` | When the Dev Lead prompt or model changes |

CI cannot run Unreal; local Unreal logs go in the PR. Until `main` has branch protection, CI only reports.

## 9. Unknowns format
On a card or PR: Decision needed / Why it matters / Options (2-3, your lean) / Proposed test (smallest) / Choice: test now, accept, or postpone.

## 10. Commits
Message: `UE-<id>: <what changed>` and a trailer `Role: <role>`. Small commits.
Cards squash-merge: one commit per card, revertable alone (D-new-port-7).

## 11. Models and effort
Model and effort per role: `pipeline/agent-ops/model-tiers.md`. Escalate effort on evidence (a failing check), not on role.

## 12. Kickoff sessions
`tools/kickoff.sh` runs you non-interactively, `JAM_OUTBOX` set. Write, never post or push: `$JAM_OUTBOX/pr.md`,
`review.md` (`ROLE:` line, `VERDICT: approve` or `VERDICT: changes`, reasons), `cards/<UE-id>.json` (Producer),
`needs-human.txt` (`NEEDS HUMAN:` lines), `comment.md`, `gate.patch`. Commit; kickoff pushes and posts. `tools/assetgen.py` API steps
queue for kickoff. A committed `.pipeline-practice` (practice repo) lifts D39; submission, upload and G4 stay blocked.

---

# CLAUDE.md

@AGENTS.md

Claude Code specifics:
- Role subagents live in `.claude/agents/`. Each one only points at its card in `pipeline/roles/`; the card is the source of truth.
- Before a PR: `python3 tools/pipeline_check.py`, the card's Done-when commands and `python3 tools/affected_tests.py --run`
  (AGENTS.md section 8). The full unit suite runs in the pipeline repos' CI, never in a card session.
