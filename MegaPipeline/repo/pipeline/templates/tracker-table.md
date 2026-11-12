# Tracker table template (Producer)

Keep this table in the body of the pinned "Jam tracker" issue. One row per MVP item in `docs/jam-brief.md` (12 rows).
`gh issue view <tracker #> --json body,comments | python3 tools/check_card.py --tracker` exits 0. `--status` runs the same check.

```
| MVP | Card | Status | Build sha | Playtest |
|---|---|---|---|---|
| 1 | #12 | todo | - | - |
| 2 | #13 | passed | 1a2b3c4 | P1 pass 2026-11-13 |
```

- Answer a question about one card in one line (answer, reason, next step). A gate gets the gate record, a cut gets its decision row. No multi-section report for a scheduling question.
- Status is one of: `todo`, `doing`, `review`, `closed`, `in build`, `passed`, `cut`.
- `in build` and `passed` need the commit sha of the packaged build where the item was seen.
- `passed` also needs `P<n> pass <YYYY-MM-DD>` from `pipeline/qa/playtests.md`, or `no P-test` when the item has none.
- Card names the issue (`#<n>`), except for a `cut` row.
- Every MVP item is APPROVED_P0 and never cut (`docs/jam-brief.md`). `--tracker` fails a `cut` row unless a DECIDED row in `docs/decisions.md` says `Overrides:` with every feature ID on that MVP line.
- A gate counts an item only when it is `passed`.
