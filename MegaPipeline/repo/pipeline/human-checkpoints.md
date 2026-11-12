# Human checkpoints

> GDD SH1.0 note (D-new-gdd-sh10): lines on this page that still describe the GDD 1.3 encounter (one owl bolt, the front shield, the 90 s survival timer, wear stages, the 1.3 QA-01..QA-28 tests) are history. The current design is `docs/gdd/GDD-SH1.0.md` and `docs/feature-manifest.json`, which win; the owning role re-files this page against the SH1.0 Rule IDs on its next card.


Agents own all build and setup work (Josh: "take the onus off the user, this stuff needs to be built out"). A person
acts only at the checkpoints below, and only to sign off: the agent prepares everything, and the person's step is
one command, one click, one answer or a physical act. Every point where a human must act, and who acts. "Who" is a seat in the People table of `docs/jam-brief.md`;
card 0.0 fills in the names. An agent that reaches one labels the issue `needs-human`, comments
`NEEDS HUMAN: <who/role> <what> <link> <YYYY-MM-DDTHH:MMZ>` (AGENTS.md section 4; the UTC time the label went on)
and stops that step. The Producer sweeps the queue every jam hour (`check_card.py --needs-human`;
`pipeline/how-to-run-the-jam.md`).

## Checkpoint kinds
A Day-0 card's person part is a Done-when line that starts `HUMAN <kind>:`, and column 3 of `pipeline/day0-cards.md`
names the kinds the card signs off (`<agent role> / <seat> (sign-off: <kinds>)`). `tools/check_card.py`
(`CHECKPOINT_KINDS`, `day0_owner_problems`) and `tools/pipeline_check.py` fail a person as Owner or reviewer, an
untagged person step, and any other kind. Everything else on a card is the owner agent's or kickoff's.
| Kind | The person's step | Why a person |
|---|---|---|
| `submission` | every upload (`butler push`), the jam form, closing G4 | Official Rules §17: a human entrant submits, never an AI agent |
| `secrets` | set an API key or token once per machine (environment or keychain, never a file) | a secret only a person holds |

No person on a Day-0 card does these any more; the tools do them, and the guardrails stay enforced by tools and CI:
- Gate patches: kickoff applies a session's `$JAM_OUTBOX/gate.patch` itself (`python3 tools/git_gate.py apply UE-<id> --auto`,
  `GATE EDIT: by=kickoff`). It refuses a patch with a path outside the card's lane, a change to a guardrail enforcer
  (`git_gate.py` GUARD_CORE: the hooks, `check_pr.py`, `kickoff.py`, `secrets_check.py`), or a loosened guardrail file
  (gates.json or `.claude/settings*.json`: a deny entry dropped, an allow entry added, `mcp_enabled` or
  `native_windows_shell` opened). CI's `check_pr.py` rule gate re-runs those checks, and kickoff's merge gate runs this
  checkout's rule gate too. A refused patch goes back to the builder; a loosening never goes through the pipeline.
- Repo settings: after cards 0.16 and 0.17 merge, kickoff sets the variables, branch protection and the Actions setting
  itself with fixed commands (`tools/kickoff.py` repo_settings) and posts the read-back.
- Machine work: a card that says `Runs on: the Windows packaging machine` is built by the kickoff running there, and
  one that says `Runs on: the Mac build machine` by a kickoff on the Mac. Every G1 card runs on the Mac; the Windows
  cards (0.3w, 0.6w, 0.4b, 0.6d) wait for that machine and never hold up G1 (`tools/kickoff.sh --until G1`).
- Audio: kickoff runs the audio critic sessions itself, and a sound the ElevenLabs API could not make (no key, an HTTP
  error, no credits left) becomes a tracked placeholder take; the run goes on (`tools/audio_check.py --placeholders`).
- `jam-start`: kickoff tags it when card 0.3 starts. People and Team hours: card 0.0 fills them from the repo's GitHub
  collaborators (`default (agent)`). Day-1 design rows: their owner agent decides them as `agent default` rows.

Art direction is not a sign-off checkpoint (Josh, 2026-11-10). The automated art gate decides: `python3 tools/art_check.py --gate`
on an in-engine capture (the numeric check against `pipeline/art/style.json`, every picture in
`pipeline/art/references.json` present, a calibrated judge, and the blind X/Y row against the key art). The Art
Director agent and the art loop (`tools/art_loop.py`) re-place or regenerate until it passes (no round cap, D-new-no-round-cap); a person
sees a piece only when it is stuck: 3 rounds in a row with the same gap and no better score (the art direction row below).
Changing `style.json` thresholds stays a guardrail.

## 2-hour grace default (approved by Josh)
If no human answers within 2 hours, `check_card.py --needs-human` prints `GRACE EXPIRED -> <role>` and the item goes
to a director session at the Hard calls tier (Fable 5.1, high effort; `pipeline/agent-ops/model-tiers.md`):
- Producer: scope, schedule, cut-list and approval calls.
- Technical Director: technical calls (asks to the TD seat).
- Producer for Richard: design calls in Richard's area.

The director adds a row to the Open decisions table of `docs/decisions.md` with Status
`DECIDED <date> (agent default after 2h grace; <role>; human may overturn)` and a link to the needs-human issue,
comments on the issue, removes the label, and work continues. If a human replies later, the human's answer wins and
the change gets its own decisions row (the grace row is marked `SUPERSEDED by D<n>`).

**Never a grace default.** These stay human-only however long they wait (`check_card.py` prints `HUMAN ONLY`;
`manifest_check.py` fails a grace row on them):
1. The final submission or any upload (Official Rules §17), and closing G4.
2. Physical work: Windows packaging and launch, playtests, the editor check of `.uasset`/`.umap` changes.
3. Changing guardrails: `gate_paths` in `pipeline/agent-ops/gates.json`, tools, tests, CI, hooks, role cards, model tiers.
4. Deleting someone else's work.
5. A P0 override or lifting a P0 rule: an `Overrides:` row needs `DECIDED <date> (Richard)`.
6. `approved_parameters` ranges: a grace default never changes them.
7. A hitbox or collider change (`hitbox_check.py fit` says `NEEDS HUMAN: Richard hitbox change request`): only Richard
   approves it (GDD 1.3 7C: "Never silently resize collisions to an atlas or damage mask").
8. Story canon: a PROPOSED or OPEN story bible row, the game title, the owl's name. Only Richard confirms it; the story
   agent writes proposals and waits (`pipeline/roles/story.md`). Until then the text stays `ship=no` (`tools/story_check.py`).

## What needs a human
| Kind | Examples |
|---|---|
| (a) Irreversible or external | an upload or submission, closing a gate |
| (b) Design or scope | GDD status, the P0 and cut lists, tuning outside the approved ranges (art is the automated art gate) |
| (c) Changing the guardrails | `tools/`, `tests/`, CI, role cards, agent settings (the gate paths below) |
| (d) Physical work | Windows packaging and launch, playtests |
| (e) Deleting someone else's work | any delete under `Content/` or `Source/`, a branch or file another card owns |

Everything else is reversible in-lane work with machine-checkable evidence. It needs no approval.

`tools/kickoff.sh` raises these items itself (label, `NEEDS HUMAN:` comment, one printed line) and keeps running the
other cards. It merges a card's PR itself (`gh pr merge --squash --match-head-commit`, one commit per card) once
every required CI check on the head is green, the reviewer agent's last verdict after the last push is approve, and
`tools/check_pr.py` passes on the head (its artship rule is the art ship gate); agent sessions still never push or
merge. A merge that fails is tried again, then asked (row below). It never closes a gate or uploads, even where a row
below allows a grace default: those wait for a human (or a director session a human starts). It closes a card whose
PR merged and a GitHub-only card its reviewer role approved itself (no ask), and before the jam start it runs the
pre-jam cards on the team repo (PRE-JAM mode).

## Where they happen
| Checkpoint | Who acts | Source | Grace default |
|---|---|---|---|
| A card PR kickoff could not merge after its retry (`merge PR #N: ...` with the reason: a red or missing CI check, a `check_pr.py` problem, a conflict, branch protection): fix the cause, then run kickoff again | the card's `Human:` (the integration owner for cross-lane cards) | AGENTS.md §4; `tools/kickoff.py` merger | yes: Producer (not a gate-path PR, row below) |
| Merge a lane_guard revert PR within 30 min | integration owner | AGENTS.md §6; `tools/lane_guard.py` | yes: Technical Director |
| Add the `REVERT_TOKEN` secret so revert PRs run CI | TD human (repo admin) | `.github/workflows/main-red.yml` | no (3): CI |
| A gate patch the tool route refused MAX_FAILS times in a row (the card is labelled blocked). Gate paths: `tools/**`, `tests/**`, `.github/**`, `evals/` cases and results, `pipeline/roles/**`, `pipeline/agent-ops/**`, `pipeline/art/style.json`, `pipeline/audio/style.json`, `pipeline/audio/sound-events.json`, `pipeline/story/story.json`, `.claude/**`, `AGENTS.md`, `CLAUDE.md`, `.mcp.json`, `.gitattributes`, `.gitignore`. Normally nobody acts: kickoff applies the session's `$JAM_OUTBOX/gate.patch` with `python3 tools/git_gate.py apply UE-<id> --auto` (lane, guardrail enforcers, no loosening; `GATE EDIT: by=kickoff`) | the card's `Human:` (fix the card or the patch, remove `blocked`) | `pipeline/agent-ops/gates.json` `gate_paths`; `tools/git_gate.py` auto_problems | no (3) |
| `gh pr merge`, `gh release`, `gh api`, `gh secret`, `gh variable`, `gh ruleset`, `gh repo` edits; a push to `main`; a bulk delete under `Content/` or `Source/`, in an agent session (kickoff's own merge and its fixed repo-settings steps are not a session and do not ask) | whoever runs the session (the hook asks) | `gates.json` `ask_commands`, `protected_branches`, `delete_ask_paths` | no (3, 4): the hook asks whoever runs the session |
| Close G1-G4 (Pass, Pass with named exceptions, Fail) | scope decision-maker | `pipeline/roles/producer.md` Gates; `pipeline/templates/gate-record.md` | yes for G1-G3: Producer. no for G4 (1) |
| Decide an open row; a `DECIDED (Richard)` row with `Overrides:` | the row's Owner; Richard for P0, presets and GDD status | `docs/decisions.md` | yes for an open row: by its Owner (TD rows to Technical Director, Richard's to Producer for Richard, else Producer). no for `Overrides:` (5). Day-0 cards 0.0, 0.14 and 0.19 decide their rows themselves as `agent default` rows the team may override (no ask) |
| A new GDD revision, a P0 or cut-list change | Richard (game design owner); cuts: scope decision-maker | `docs/gdd/README.md`; `docs/jam-brief.md` | yes for a cut list with no P0: Producer. no for a GDD revision or a P0 (5), except card 0.0 recording the GDD SH1.0 import as printed (D-new-gdd-sh10: every Rule ID APPROVED_P0; an agent default the team may override) |
| Tuning outside a GDD SH1.0 start (section 9 ranges are blank, D-new-sh10-param-ranges) | Richard, by a DECIDED row | `pipeline/checklists/tuning.md` | no (6) |
| Art direction: no human approves a look (Josh, 10 Nov). The references in `pipeline/art/references.json` are the bar; the art loop's blind critic and the deterministic checks decide (`pipeline/art/art-bible.md`). A human acts only when a piece is stuck (3 rounds with no improvement) | Art Director human, with the first and latest image and the critic's gaps | `tools/art_loop.py`; `pipeline/roles/art-director.md` | yes: Producer |
| The audio mix by ear: the final listen after every piece closed its loop (`pipeline/audio/style-target.md` section 5); it is not the bar | audio owner | `pipeline/roles/audio.md` | no (2): needs ears |
| A stuck audio piece (`audio_loop.py verdict` prints `NEEDS HUMAN: Audio-owner ...` after 3 rounds with no improvement): listen to the files and answer with `audio_loop.py resume` | audio owner | `pipeline/audio/style-target.md` section 5 | no (2): needs ears |
| `daily.ps1` on the Windows packaging machine, each merge and each gate, while `gates.json` `native_windows_shell` is `block` (with `allow`, kickoff's QA and Build session runs it) | packaging machine owner | `pipeline/roles/qa-build.md` step 1 | no (2) |
| Start the gate zip on a second Windows machine (LAUNCH line) | launch machine owner | `pipeline/templates/gate-record.md` | no (2) |
| Playtests P1-P11 and the end-of-day 15-min play (one per gate on a real controller: the `GAMEPAD:` line; the automated `gamepad=ok` smoke, card 0.6e, does not replace it) | playtest lead and the human testers | `pipeline/qa/playtests.md` | no (2) |
| Every upload (`butler push`) and the jam form, final submission included, before the deadline | the Team Owner or the packaging and submission owner, a human entrant. Official Rules §17: never an AI agent; `hook.py` blocks `butler push` and `butler login` (`gates.json` `human_only_commands`) | `pipeline/checklists/submission.md` Upload; `docs/jam-rules.md` team rule 14 | no (1) |
| Set the audio API keys once per machine that runs kickoff (`ELEVENLABS_API_KEY`, `STABILITY_API_KEY`; art needs none: Blender), in the environment or the OS keychain, never a file | whoever runs `tools/kickoff.sh` on that machine | `tools/keys.py`; `tools/connections.py` names a missing key | no (3): a secret only a person holds; until then sounds fall back to placeholders |
| Turn on the MCP servers at kickoff: Unreal editor, GIMP, Aseprite, Blender (`mcp_enabled`, the kickoff record; both agents get them through `tools/kickoff.py`) | TD human, with the team's OK | `pipeline/agent-ops/editor-mcp.md`; `tools/mcp_config.py` | no (3) |
| Open and check each `.uasset`/`.umap` a PR changes (`EDITOR CHECK:` line) | the card's `Human:` | `tools/check_pr.py` rule editor | no (2) |
| Confirm story canon: a PROPOSED or OPEN row of `pipeline/story/story-bible.md`, the title, the owl's name (`STORY CONFIRM: by=Richard <row ids>` on the PR) | Richard (game design owner) | `pipeline/roles/story.md`; `docs/decisions.md` D-new-story-canon, D-new-owl-name; `tools/check_pr.py` rule story | no (8): a design call stays human |
| G4 content sign-off (`CONTENT ...` line: teen, trademarks, original, no extra software, English) | the Team Owner or the packaging and submission owner | `pipeline/checklists/submission.md` Content and rules | no (1) |
| Start an agent session (`tools/start_session.sh <role> <card>`) | whoever runs that machine | `pipeline/agent-ops/model-tiers.md` | no (2): a person at the machine |
| Answer an `--overrun` ask, a token-cap OK, a hard-stop exception | Producer human | `pipeline/roles/producer.md`; `pipeline/roles/agent-ops.md` | yes: Producer |
| The `HUMAN <kind>:` lines on Day-0 cards (column 3 `sign-off:` kinds; every card is agent-owned) | the card's `Human:` | `pipeline/day0-cards.md` | no for submission and secrets |
