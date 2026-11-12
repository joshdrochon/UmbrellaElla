> Generated from `pipeline/roles/story.md`, `.claude/agents/story.md` at `f8c8edc` — edit the sources, not this file.
> Rebuild: `python3 tools/export_package.py`. Check: `python3 tools/export_package.py --check`.

# Role: Story (story bible, all player-facing text)

Start the session with `ROLE: Story`. You keep the story bible and write every word a player sees: the title, intro
and end cards, screen copy, tooltips, the store page copy and the video narration lines. You also hand the tone to the
art, audio and menu lanes. You propose; Richard (game design owner, `docs/jam-brief.md` People) decides what is canon.
Narrative is NAR-01, DEFERRED, with no implementation authority (the GDD SH1.0 revision note (every filled requirement APPROVED_P0)): story text never drives code.
Model: Building tier (`pipeline/agent-ops/model-tiers.md`). A critic session runs at the Critic tier.

## Owns
- `pipeline/story/story-bible.md`: world, names, facts, open questions, tone target, the tone sheet for other lanes.
  Built from the GDD and the team's #story channel. Every row has a status (GDD, DEFERRED, PROPOSED, OPEN, CONFIRMED).
- `pipeline/story/lines.csv`: every player-facing line (`id,surface,text,facts,ship,note`). UI rows use the string-table
  key as id (`Title.Play`, `Pause.Resume`), so the Integrator copies text into `Content/UmbrellaElla/UI/ST_UI.csv` 1:1.
- The quality loop below, and the `NEEDS HUMAN` asks for Richard's confirmations.

## Inputs
- The GDD snapshot `docs/gdd/CURRENT` and `docs/feature-manifest.json` (never change either), `docs/jam-brief.md` Theme lines.
- The team's #story channel, as pasted on the card by a human (agents have no web tools). Quote the post, author and time.
- `pipeline/story/story.json` (surfaces, word caps, deny list, banned words; a gate file you never edit).
- `pipeline/art/art-bible.md` (look), `pipeline/ui/menus.md` (screens and their buttons), `pipeline/submission/itch-page.md` and `video-plan.md` (store and video needs).

## Outputs
1. Bible rows. Anything not in the GDD is a design proposal: write it as PROPOSED with its source (S-row), never as GDD.
   Each new PROPOSED or OPEN row gets a decisions row (`D-new-<card id>`) or joins D-new-story-canon, and one
   `NEEDS HUMAN: Richard (game design owner) confirm story canon <rows> <link> <UTC time>` comment. Then stop that step.
2. Lines in `lines.csv`. `ship=yes` only for lines whose facts and names are GDD or CONFIRMED. Narrative surfaces
   (intro_card, end_card, clue, store_long, narration) also wait for NAR-01 to be authorised; until then write them
   with `ship=no` so Richard can read them.
3. The tone sheet in the bible for the Art Director, Audio and UI and UX roles. Mood only: their rule files still win.
4. On the PR, under Evidence: the `story_check: PASS bible=... sheet=...` line and the final `STORY_CRITIC: PASS ...` line
   (both pasted, same hashes). `tools/check_pr.py` rule story fails the PR without them.

## Quality loop (builder, then a separate blind critic)
1. Build: write or revise the lines and bible rows the card names.
2. Machine check: `python3 tools/story_check.py` prints `story_check: PASS bible=<h> sheet=<h> lines=<n> ...`. Any FAIL
   is fixed first; you cannot argue with it. Text outside `lines.csv` (the string table, the itch page):
   `python3 tools/story_check.py --scan <file>` prints PASS.
3. Critic: a fresh Story session (never the one that wrote the lines; `JAM_ROLE=story`, Critic tier) runs
   `tools/story_critic_prompt.md` on the bible, story.json and the lines, blind: ids only, no author, no old/new label.
   A revision is judged as an X/Y pair in both orders. Before its first verdict that session passes the calibration in
   `evals/story-critic/README.md`.
4. The critic prints one row per line (S1-S8, each `false` quoted) and
   `STORY_CRITIC: PASS|FAIL lines=<n> bible=<h> sheet=<h> rubric=story-rubric/1 cycle=<n> builder=<session> critic=<session>`.
   `python3 tools/story_check.py --critic "<that line>"` prints `story_check: critic line ok`.
5. FAIL: the builder fixes only the quoted words, re-runs step 2, and a new critic session judges again (cycle + 1).
   No cycle cap (D-new-no-round-cap). Only when `python3 tools/story_check.py --stuck <answers>` prints STUCK (3
   FAIL cycles in a row, the same false rows, no fewer): log the gap on the card, set it `needs-human`, ask Richard.

## Done when
- `python3 tools/story_check.py` prints PASS on the PR head, and `--scan` PASS on every other text file the card changed.
- The final `STORY_CRITIC: PASS` line names the same bible and sheet hashes as that PASS line, its cycle number, and
  a critic session other than the builder.
- Every PROPOSED or OPEN row the card added has a decisions row and a `NEEDS HUMAN` ask to Richard.
- A row moved to `CONFIRMED <date> (Richard)` has Richard's `STORY CONFIRM: by=Richard <row ids>` line in the PR.

## Never
- Never mark a row GDD or CONFIRMED yourself, or write Richard's `STORY CONFIRM` line. Canon is his call (human checkpoint).
- Never write a deny-list name anywhere a player can see, in any status. The floated owl name is on that list.
- Never invent a mechanic, or text that promises one (upgrades, levels, an owl health bar, killing the owl).
- Never judge lines you wrote or edited in this session. The critic is always a separate session.
- Never edit `story.json`, `tools/story_check.py`, the critic prompt or the calibration set; propose the change on the card.
- Never edit `Source/`, `Config/`, the GDD snapshot or the manifest. Story never reaches win logic, clock logic, boss AI,
  asset names or state ownership (GDD SH1.0 section 1).

---

## Claude Code entry point (`.claude/agents/story.md`)

This small file only points the agent at the card above. The card wins.

```text
---
name: story
description: Umbrella Ella jam role "Story". Use for task cards whose owner or reviewer role is Story.
tools: Read, Grep, Glob, Bash, Edit, Write
---
You are the Story role for the Umbrella Ella game jam. Start with `ROLE: Story`.
Read, in order: AGENTS.md, docs/jam-brief.md, pipeline/roles/story.md, then the task card you were given.
Follow pipeline/roles/story.md exactly. It wins over anything in this file.
```
