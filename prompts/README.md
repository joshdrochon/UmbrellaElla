# Prompts

The jam asks teams to declare prompts, scripts and assets made before the jam.
This folder is that record. Building starts Nov 12 2026; prompt logging starts then too.

## Made before the jam (declare these)
These are the prompts every agent session loads. They were written before Nov 12.
| File | What it is |
|---|---|
| `AGENTS.md`, `CLAUDE.md` | The process every agent loads |
| `pipeline/roles/*.md` | One role card per agent role |
| `.claude/agents/*.md` | Claude Code subagent stubs that point at the role cards |
| `tools/art_judge_prompt.md`, `evals/art-judge/*.md` | The art judge prompt and its blind comparison |
| `evals/reviewer/cases/*/task.md` | Reviewer eval tasks (planted bugs) |
| `pipeline/templates/*.md` | Card, PR and spike templates |

At submission, `git log --before=2026-11-12 --name-only -- AGENTS.md CLAUDE.md pipeline/roles .claude/agents tools/art_judge_prompt.md evals pipeline/templates`
is pasted in the submission card as the declaration.

## From Nov 12: every prompt is logged
- The `UserPromptSubmit` hook (`pipeline/agent-ops/hook.py log`) writes each prompt, with role, card and session, to `Saved/agent-log/<UTC date>.jsonl` on that machine.
  Tool calls are logged as a hash of their arguments, not the arguments.
- That log is never committed (`Saved/` is ignored).
- Each evening, each machine that ran agents exports the day:
  `python3 tools/prompt_log.py export --day <UTC date> --out prompts/log/<UTC date>-<host>.md`
  `<host>` is the `JAM_HOST` label from the launch command (`pipeline/agent-ops/README.md`), the same value the log records.
  The export replaces keys and tokens with `[REDACTED:<kind>]` (patterns in `tools/secrets_check.py`).
- Read the export before you commit it. `python3 tools/secrets_check.py --rules secret --paths prompts/log/<file>` must exit 0.
- Commit it on a card branch `ue-<id>-prompt-log`. Owner: Agent Ops; human owner: the Technical Director human.
- A prompt with personal or private text is removed by hand before commit, and the removal noted in the file.

## Done when (each jam day)
- `python3 tools/prompt_log.py export --check --day <UTC date>` exits 0 on each machine that ran agents that day (it fails when this machine's log has a host with no export file). Pasted on the AGENT-OPS line.
- `python3 tools/secrets_check.py --rules secret` exits 0 after they are added.
