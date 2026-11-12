# GDD revisions: how a new one lands (on demand)

Load this when a GDD revision arrives or you change `docs/feature-manifest.json`. Expect 1-4 revisions a day.

Files:
- `docs/gdd/GDD-<rev>.md`: one read-only snapshot per revision. Never edited after it merges.
- `docs/gdd/CURRENT`: one line, the snapshot agents read (now `GDD-1.3.md`).
- `docs/feature-manifest.json`: one record per feature ID, statuses copied from the GDD (source of truth #1).
- `docs/gdd/questions-<rev>.md`: open questions for the GDD authors.
- `docs/gdd/archive/`: superseded drafts. Never in any read order.

## A new revision (about 30 min, one PR, the integration owner)
1. Convert the PDF to `docs/gdd/GDD-<rev>.md`: same header table as `GDD-1.3.md` (revision, date, source commit), text below `---`.
2. Point `docs/gdd/CURRENT` at it. Pin it: add the line `python3 tools/manifest_check.py --pin docs/gdd/GDD-<rev>.md` prints to
   `gdd_snapshots` in `docs/feature-manifest.json`, and set `gdd_snapshot`. Old pins never change (CI compares them with the base branch).
3. Update `docs/feature-manifest.json`: new or removed IDs, status words exactly as the GDD prints them, `gdd_revision`.
   Never promote: only the design owner and the technical owner change a status or `implementation_authorized`.
4. Run, and paste both under `## GDD impact` in the PR (`check_pr.py` fails without it):
   `python3 tools/gdd_impact.py docs/gdd/GDD-<old>.md docs/gdd/GDD-<rev>.md`
   `git show origin/main:docs/feature-manifest.json > /tmp/old.json && python3 tools/gdd_impact.py /tmp/old.json docs/feature-manifest.json`
5. `python3 tools/gdd_select.py docs/gdd/GDD-<rev>.md --set-current --check`, `python3 tools/manifest_check.py` and
   `python3 tools/pipeline_check.py` print no problems. `gdd_select.py <rev> --check` lists what a revision still needs,
   one line each; `tools/kickoff.sh --gdd <rev>` tests a revision for one run without changing `CURRENT`.
6. Each "cited by" line is a card, test-map row, preset or doc line to re-check. Fix it in this PR or file a card for it.
   Open cards on the old revision stay valid unless one of their Features changed; `check_card.py` fails exactly those.
7. Move answered questions out of `questions-<old>.md` into a new `questions-<rev>.md`.

A status change (a sign-off) is a new revision too: the GDD's own change rule says "Future changes must increment the
document version and add dated revision notes", and `manifest_check.py` holds every status to the current snapshot.
Richard signs off by publishing the new PDF revision; then steps 1-7 run as above.
