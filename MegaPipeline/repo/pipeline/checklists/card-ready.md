# Card readiness (Producer, before a card is labelled todo)

A card that fails a line is not ready. `pipeline/templates/task-card.md` lists the fields. Run `python3 tools/check_card.py` on the card first (empty fields, roles, lane, measurable Done-when); this list covers what the script can't.

- Full cards only for the next gate's MVP items. Later items stay one-line placeholders until the gate before them passes (D-new-port-11).
- Every Input path exists on `main` or is another open card's Output. No "as discussed" references.
- Rule cards pass `pipeline/checklists/design-review.md`. Asset cards have the brief from `pipeline/templates/asset-brief.md`.
- Every open decision whose test is due Day 0 or Day 1 has a spike card (`pipeline/templates/spike-card.md`). A card that depends on it waits for the result.
- Budget reads `<n> min agent + <n> min human`; agent over 120 min or human over 60 min means split (check_card enforces all three; D-new-human-cap). A Stretch card while an MVP card is open fails (`--lanes`; no override). Before labelling todo, `gh issue list --label task --state open --json number,title,body --limit 200 | python3 tools/check_card.py --hours --day N` exits 0 with this card included. It fails when a person's human budget is over 70% of their Team hours that day (D-new-reserve). That person gets no new card.
- Not too small: a card under 20 min agent + 10 min human in the same lane as another `todo` card for the same human is merged into that card. Each card costs one review session, and the review queue is capped at 3.
- Done-when and Out of scope say what must be true, not how to code it: no new class, function or member names unless `pipeline/unreal/gameplay-code.md` names them or they are test names.
- Before a card moves to `doing`: `gh issue list --label review --state open --json number,title,body | python3 tools/check_card.py --queue` exits 0 (at most 3 in review per human, D-new-port-3).
- `... | python3 tools/check_card.py --lanes` exits 0 with this card included: no shared lane glob, `.umap` or lock.
- Flipbook frame counts stay within the content caps in `docs/jam-brief.md`, or the card cites the decision row (check_card enforces).
- A stretch card names which open-vs-close decision it changes. One that changes none goes to the end of the stretch order.
- When a new GDD revision lands, run `tools/gdd_impact.py` (`docs/gdd/README.md`); every open card it lists is re-checked, and `check_card.py` fails a card whose Features changed since its `GDD revision`.
- Features are authorized in `docs/feature-manifest.json`, or the card is `Hook only` for an OPEN or PROPOSED ID (check_card enforces).
- Done-when has at least one blocked, negative or interrupted check besides the normal path (owl outside the firing lane: no shot; a hit during invulnerability does no damage).
- `Out of scope`, `Used by` and `Needs` are filled. If `Used by` names something in another lane, the follow-up card (usually Integrator) is filed now and its number is in `Used by` (check_card enforces). For an Asset Specialist card, that Integrator card is open with a Budget, so `--hours` counts its human time on the same day (`--hours` fails the asset card otherwise).
- A card that creates tests named in `pipeline/qa/test-map.md` has a Done-when line that writes its issue number and `merged` in that row (the file is row-scoped; `--lanes` ignores it).
- Any card that changes maps, `Config/**`, `*.Build.cs`, `*.Target.cs`, `.uproject` or assets loaded by path has a package + `SMOKE_OK` line in Done-when.
