# GameJam2026

**New here, or told to merge a PR and run the pipeline? Read [`START_HERE.md`](START_HERE.md) first.** It has
every step for Windows and Mac, from setup to your first run.

Umbrella Ella (working title): a 2D Unreal Engine 5.8.4 action game for the jam.

- **Agents start at** [`AGENTS.md`](AGENTS.md).
- Game, MVP and people: [`docs/jam-brief.md`](docs/jam-brief.md)
- Open decisions: [`docs/decisions.md`](docs/decisions.md)
- Pipeline audit (issue #11): [`docs/audit.md`](docs/audit.md)
- Sources: [`docs/references.md`](docs/references.md)

Checks: `python3 tools/pipeline_check.py` and `python3 -m unittest discover -s tests` (no installs needed).

## Install and run (Claude Code or Codex, same steps)
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

