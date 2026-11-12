# CLAUDE.md

@AGENTS.md

Claude Code specifics:
- Role subagents live in `.claude/agents/`. Each one only points at its card in `pipeline/roles/`; the card is the source of truth.
- Run `python3 tools/pipeline_check.py` and `python3 -m unittest discover -s tests` before opening a PR.
