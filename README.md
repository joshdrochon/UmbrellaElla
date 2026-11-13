# GameJam2026

**New here, or told to merge a PR and run the pipeline? Read [`START_HERE.md`](START_HERE.md) first.** It has
every step for Windows and Mac, from setup to your first run.

Umbrella Ella (working title): a 2D Unreal Engine 5.8.4 action game for the jam.

- **Agents start at** [`AGENTS.md`](AGENTS.md).
- Game, MVP and people: [`docs/jam-brief.md`](docs/jam-brief.md)
- Open decisions: [`docs/decisions.md`](docs/decisions.md)
- Pipeline audit (issue #11): [`docs/audit.md`](docs/audit.md)
- Sources: [`docs/references.md`](docs/references.md)

Checks: `python3 tools/pipeline_check.py`; a card session adds `python3 tools/affected_tests.py --run` (the tests for
the changed files, a 5-minute target). The full suite, `python3 -m unittest discover -s tests`, is CI's (no installs needed).

## Build modes
`tools/kickoff.sh` (Windows: `tools\kickoff.ps1`) follows `docs/build/MODE`:
- `direct`: no GitHub cards, PRs or reviews. Kickoff reads `HANDOFF.md`, resumes every unfinished area from its
  `area/<name>` branch with a Claude Code worker (brief: `docs/build/areas/<name>.md`), runs the local gates, merges
  each passing area into `main` and pushes. Use it to build fast, or to pick up the build where someone stopped.
- `cards`: the GitHub card flow (task cards, PRs, reviewers, CI). Use it when every change should be reviewed on GitHub.
No MODE file: kickoff asks once (Enter = `direct`) and saves the answer. Change it by editing the file, or pass
`--mode cards|direct` for one run. Both modes start every ready job whose files overlap no running job's (at most one
per CPU; `--parallel N` caps it); Unreal builds and tests share `UE_SLOTS` (default 2) engine slots. One area by hand:
`tools/area.sh <name>` (Windows: `tools\area.ps1 <name>`). Lead's handoff file shape: `docs/build/HANDOFF-template.md`.

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

Codex users get the same guardrails as Claude Code users: no local git hook checks gate paths; CI fails a card PR that
changes one unless the commit came through kickoff's tool route (trailer `GATE EDIT: by=kickoff`, read from git, not
from the PR body; `tools/check_pr.py` rule gate), and kickoff's merge gate runs that rule again. The Claude hook stays as an extra layer.
How to run the jam day to day: `pipeline/how-to-run-the-jam.md`. What the tools check and what people decide:
`pipeline/what-the-pipeline-controls.md`.

