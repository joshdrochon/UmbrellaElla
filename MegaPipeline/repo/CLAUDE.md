# CLAUDE.md

@AGENTS.md

Claude Code specifics:
- Role subagents live in `.claude/agents/`. Each one only points at its card in `pipeline/roles/`; the card is the source of truth.
- Before a PR: `python3 tools/pipeline_check.py`, the card's Done-when commands and `python3 tools/affected_tests.py --run`
  (AGENTS.md section 8). The full unit suite runs in the pipeline repos' CI, never in a card session.
