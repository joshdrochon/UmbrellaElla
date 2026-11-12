# Story critic calibration

The critic (`tools/story_critic_prompt.md`) is trusted only after it catches known-bad lines. The machine half
(`tools/story_check.py`) is tested the same way, in the unit tests.

`calibration.csv` holds 22 lines, each written to break one rubric row or to pass:
- `kind=none`: good lines. `story_check.py` passes them; the critic must answer every row `true`.
- `machine=yes`: `story_check.py --calibrate` must fail each one with its `kind` (deny, contradiction, banned, exclaim,
  caps, name, length, fact, ship, nar). `tests/test_story_check.py` runs it in CI.
- `machine=no`: only a reader catches these (a pun, an unclear tooltip, a promised mechanic, invented lore). The critic
  must answer the `rubric` row `false` for each.

## Run (before the first critic verdict of a session; void the session if it fails)
1. `python3 tools/story_check.py --calibrate` prints `story_check: calibrate PASS rows=<n>`.
2. A fresh Story session runs the critic prompt on `calibration.csv` (lines only; the `kind`, `machine`, `rubric` and
   `note` columns are removed and the rows shuffled, seed written in the PR).
3. Bar: every good row all `true`, every bad row `false` on its `rubric` row. 100%, no exceptions.
4. Paste the critic's verdict line and the bar result in the PR or card: `STORY_CALIBRATION: PASS rows=<n> seed=<n>`.

The calibration is valid only for one exact model id and the prompt and rubric versions at the top of the prompt.
Changing either, or the bible's Tone target, voids it. A row is never softened to let a critic pass; a mislabelled
row may be fixed with the reason in the commit message.
