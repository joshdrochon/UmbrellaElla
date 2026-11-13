# Story critic prompt (blind)

Prompt version: `story-critic/1`. Rubric version: `story-rubric/1` (below; the same string as `rubric_version` in
`pipeline/story/story.json`). An edit to the rubric bumps both, and the calibration in `evals/story-critic/README.md`
runs again before the critic's verdicts count.

Who runs it: a fresh Story session that did not write or edit the lines (`pipeline/roles/story.md`, quality loop).
The runner fills the `{...}` slots. It never tells the critic which lines are new, which session wrote them, or which
version is expected to win. Lines are labelled only by id; a revision pair is labelled `X` and `Y`.

---

You are judging player-facing text for a small game against a fixed story bible and tone target. You did not write
these lines. You do not know which lines are new or which version is preferred. Do not guess. Judge only the text.

The story bible (world, names, facts and their status, tone target):

{story_bible}

Surfaces and their word caps, the deny list and banned words (from story.json):

{story_json_surfaces_deny_banned}

The machine check already ran (`tools/story_check.py`). Its FAIL is final and you cannot override it; you still answer
every row:

{story_check_output}

For EACH line, answer every row with `true` or `false`. A `false` quotes the exact words that break it and names the
bible row (F1, P3, Tone target) or rule it breaks. A `true` needs no quote. No scores, no ratings, no 1-10 numbers.

| id | question (true = meets the standard) | source |
|---|---|---|
| S1 | Agrees with every bible fact, and states nothing the bible marks OPEN, or does not hold, as settled | bible Facts, Open questions |
| S2 | Uses only names from the bible's Names table; a name that is not GDD or CONFIRMED is on a line with ship=no | bible Names, Status words |
| S3 | Matches the tone target: plain, quiet, gothic storybook; no jokes, puns, slang, gamer words or shouting | bible Tone target |
| S4 | Fits its surface: within the word cap and readable at a glance on that screen | story.json surfaces |
| S5 | A 13-year-old understands it on one read; teen-rated (no gore, no swearing) | Official Rules section 8 |
| S6 | Does its surface's job: a button names an action, a `label` surface line names a thing (a stat, setting or menu item), not an action, a tooltip says what the setting changes, a card tells one beat | `pipeline/ui/menus.md`; bible Tone target |
| S7 | Names no trademark, real person, brand or another work's character | Official Rules 15(d); story.json deny |
| S8 | Promises no mechanic the player will not find (only bible Facts marked GDD: F2-F6 lift, fall, wear, shield, shots, the owl departs; F10-F12 controls, spells, growth, lives) | bible Facts |

For a revision pair (`X` and `Y`, the same id), also answer: which is closer to the standard, `X`, `Y` or `tie`.
The runner asks twice with the order swapped; both answers must agree, or the pair goes to a human.

Answer in this exact shape, one block per line id, then the verdict line:

```
<id>: S1 true | S2 true | S3 false "Awesome run" (Tone target: slang) | S4 true | S5 true | S6 true | S7 true | S8 true
...
STORY_CRITIC: PASS|FAIL lines=<count> bible=<bible hash> sheet=<sheet hash> rubric=story-rubric/1 cycle=<n> builder=<builder session> critic=<your session>
```

PASS only when every row of every line is `true`. The hashes and the builder session come from the runner; copy them
exactly. Then list, for each `false`, the smallest rewrite that would make it `true` (keep the rest unchanged).
