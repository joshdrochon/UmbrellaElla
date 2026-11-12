# Spike card (answers one open row in `docs/decisions.md`)

Several open rows ask for a quick test before the team decides (D3, D4, D13).
A spike is a task card with these extra fields. It answers a question. It does not ship.
Title it `[UE-<n>] Spike D<n>: <question>` and paste the block under Unknowns. `check_card.py` fails a card titled
`Spike: ...` or `Spike D<n>: ...`, or any card with a `Decision row:` line, unless `Decision row` names a row,
`Decides it` reads "if ..., pick ..." and `Time box` is at most 60 min.

```
Decision row:  D<n>
Question:      <one sentence>
Variants:      <the 2-3 options being compared>
Setup:         <map/section, input device, build config, commit>
Measure:       <the number or observation that will be read>
Decides it:    <written BEFORE running: "if X, pick A; if Y, pick B">
Time box:      <at most 60 min>
Branch:        spike-D<n>-<short-name>
```

## Rules
- The branch `spike-*` is never merged. If the team keeps the idea, a normal card rebuilds it with tests and Done-when.
- Stop at the time box or at the first result that decides it.
- Compare like with like: same section, same device, same build. In a playtest A/B, alternate which version each player sees first.
- Post the result on the decision row's issue, even if it is inconclusive:
  `Question | Commit | Setup | Observed (numbers) | Not run | Recommendation: Keep / Revise / Cut / Retest`
- The human owner of the row decides from it. A spike never marks a row DECIDED.
