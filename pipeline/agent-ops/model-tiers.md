# Model tiers

One table for every role. Each role card names its tier in a `Model:` line; this page is the source. `tools/kickoff.sh`
and `tools/start_session.sh <role> <card>` (a human runs them) read this page: Claude Code gets `--model <id>` from the
Model column; Codex gets `-m <id>` from the GPT column when it holds an ID in backticks, otherwise Codex runs its
default model. By hand: `tools/agent.sh <role> <card> claude --model <id>`. Source: R12 in `docs/references.md`.

| Tier | Use it for | Model | GPT equivalent (Codex) |
|---|---|---|---|
| Hard calls | What we build and why, plans, code reviews, gate verdicts, grace-default director sessions | Fable 5.1 (`claude-fable-5-1`); Opus 5.5 (`claude-opus-5-5`) when the plan has no Fable | GPT-6 Astra (`gpt-6-astra`); reasoning effort high (`-c model_reasoning_effort="high"`) |
| Critic | Every blind critic: the art loop, art judge, audio, story and encounter critics | Opus 5.5 (`claude-opus-5-5`); Fable 5.1 (`claude-fable-5-1`) for a call the critic flags as hard | GPT-6 Astra (`gpt-6-astra`); reasoning effort high |
| Building | Builders: mechanics, gameplay C++, art and Blender scripts, integration, text, data | Sonnet 5.5 (`claude-sonnet-5-5`) | GPT-6.1 Sol (`gpt-6.1-sol`); default effort |
| Quick checks | Read-only lookups and status checks (`tools/start_session.sh <role> <card> --tier "Quick checks"`); never writing code, never a verdict | Haiku 5.5 (`claude-haiku-5-5`) | GPT-6 Luna (`gpt-6-luna`); low effort |

Josh, 2026-11-10: builders Sonnet 5.5, quick checks Haiku 5.5, critics and hard calls Opus 5.5 / Fable 5.1. Josh, 2026-11-11: the GPT column filled for Codex. The first
model ID in backticks in a row is the one a session gets (`tools/start_session.py` model_for).
Effort: hard-call and critic sessions run at high reasoning effort (Claude `--effort high`; Codex `model_reasoning_effort`);
building sessions at the default. GPT IDs are from OpenAI's Codex models page (11 Nov 2026: Astra the most capable,
Sol near-Astra for complex coding, Luna for focused high-volume tasks). If a teammate's plan refuses one on
`codex exec -m <id>`, put the model their plan offers in that cell.
Split runs: `tools/kickoff.sh --split` puts the builders on one agent CLI and the reviewers, critics and Producer on the
other when both Claude Code and Codex are installed (default `build=codex,review=claude,critic=claude,producer=claude`;
`--split build=claude,critic=codex` or `KICKOFF_SPLIT` to choose); each session takes its model from its own column.

| Role (`gates.json` key) | Tier |
|---|---|
| producer | Hard calls |
| technical-director | Hard calls |
| dev-lead | Hard calls (reviewer) |
| game-designer | Hard calls |
| gameplay-dev | Building |
| integrator | Building |
| art-director | Building |
| asset-specialist | Building |
| level-designer | Building |
| encounter-designer | Building |
| audio | Building |
| ui-ux | Building |
| story | Building |
| qa-build | Building |
| agent-ops | Building |

Any reviewer session, whatever its role, runs at the Hard calls tier; any blind critic session at the Critic tier. A change to this table or to the Dev Lead's
model re-runs the reviewer eval (`evals/reviewer/results.md`).
