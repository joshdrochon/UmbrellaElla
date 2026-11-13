# How to run the jam (for humans)



Agents follow `AGENTS.md` and own every card; you only sign off where
`pipeline/human-checkpoints.md` says.

## Start: one command, Claude Code or Codex
1. Type `tools/kickoff.sh` (Windows: `tools\kickoff.ps1`). It prints the version, checks every connection
   and starts your agent (asking if you have both); a problem prints what to type.
   API keys: once per machine (`python3 tools/keys.py status`). MCP servers stay off until the kickoff record.
2. Then it files the cards, runs each ready card in a fresh session, opens PRs, runs the reviewer and merges;
   it stops only for a human. `--agent codex` or `claude` picks the agent. First night: `--max-cards 5` stops after
   5 cards merge or block; rerun. `--until G1`: G1 cards only, then the Mac package.
3. Before Nov 12 the team repo runs only the pre-jam cards; a test repo with `--practice` runs all. `--dry-run`
   shows the plan.
4. Answer the needs-human queue (below), then run it again: it resumes. One card:
   `tools/start_session.sh <role> <card>`.

## Build modes
`docs/build/MODE`: `direct` (no cards or PRs) or `cards` (below). README explains.

## A/B test a build
`tools/kickoff.sh --prompt-file my-prompt.txt` records your prompt and adds it to every session; each run prints a
`RUN #<n>: ...` line. Record it: `python3 tools/journal.py run-outcome
--run <n> --outcome pass|fail`; `python3 tools/journal.py compare <a> <b>` diffs two runs.

## Another boss fight (encounter presets)
Fights are data in `pipeline/level/encounter.json` (Encounter Designer role); GDD 1.3 ships. A proposal such as
`OWL-FIGHT-RICKY` (`D-new-encounter-ricky`) loads only in workbench and practice builds; `python3
tools/encounter_check.py --presets --gdd 1.3` lists them.

## How a PR merges
kickoff squash-merges it (nobody clicks merge) once:
1. CI (`pipeline-checks`) is green and the card's reviewer role posted `approve` from a different session.
2. Evidence pastes real output per Done-when line; "Not run" lines name who runs them.
   Unit tests: `tools/affected_tests.py`; the full suite is CI's.
3. `tools/check_pr.py` passes on the head. A gate-path change is the agent's gate patch; kickoff applies it
   (`git_gate.py apply --auto`).
A `merge PR #N: ...` ask names the blocker: fix it and rerun kickoff, or label the card `cut` / `superseded`.
`tools\ue\daily.ps1` within 1 h: kickoff runs it (Windows, `native_windows_shell: allow`) or its owner posts `DAILY`.
`main` red: a revert PR opens itself; the integration owner merges it within 30 min.

## Clear the needs-human queue
Each jam hour the Producer runs:

    gh issue list --label needs-human --state open --json number,title,labels,comments \
      | python3 tools/check_card.py --needs-human

Each line reads `#<issue> <who>: <what> <link>`. If you are the named person or seat:
1. Do it (fix a blocked merge, decide the row, play the build, run the Windows step).
2. Reply on the issue: what you did, linked.
3. Remove the `needs-human` label; the next session picks it up.
An ask naming no one, or off the list, goes back to the agent.
`GRACE EXPIRED -> <role>` (2 h, no human answer): that director session decides it; a later human answer wins (`pipeline/human-checkpoints.md`).
Then `python3 tools/status_board.py --source gh` rewrites `Saved/status-board.md`; link it on the tracker.

## Close a gate (G1-G4)
1. The Producer posts the gate record on the tracker (its lines: `pipeline/templates/gate-record.md`).
2. On the packaging machine: `gh issue view <tracker #> --json comments | python3 tools/check_card.py --gate-record`
   exits 0.
3. The scope decision-maker posts the outcome (Pass, Pass with named exceptions with owner and hour, or Fail) and
   alone closes the gate.
4. Fail or 2 h late (`check_card.py --clock` prints `CUT FIRES`): cut the next cut-list item in `docs/jam-brief.md`.
5. G4 ends with the upload: `pipeline/checklists/submission.md`, run by the packaging and submission owner.
